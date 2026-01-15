"""Volatility command validation for post-generation safety.

This module validates all Volatility commands in generated responses
to ensure they are syntactically correct and use valid plugins.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from difflib import get_close_matches
from pathlib import Path

from dfir_assistant.models import ValidatedCommand
from dfir_assistant.validation.models import ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """Information about a Volatility plugin."""
    
    name: str
    versions: list[str]  # ["vol2", "vol3"]
    syntax: str
    description: str
    aliases: list[str] = field(default_factory=list)
    vol3_equivalent: str | None = None


class PluginRegistry:
    """Registry of valid Volatility plugins.
    
    Loads plugin definitions from JSON configuration file.
    """
    
    def __init__(self, config_path: Path | str | None = None):
        """Initialize plugin registry.
        
        Args:
            config_path: Path to volatility_plugins.json
        """
        if config_path is None:
            config_path = Path("config/volatility_plugins.json")
        
        self.config_path = Path(config_path)
        self._plugins: dict[str, PluginInfo] = {}
        self._aliases: dict[str, str] = {}  # alias -> canonical name
        self._loaded = False
    
    def load(self) -> bool:
        """Load plugins from configuration file.
        
        Returns:
            True if loaded successfully
        """
        if not self.config_path.exists():
            logger.warning(f"Plugin config not found: {self.config_path}")
            return False
        
        try:
            with open(self.config_path) as f:
                data = json.load(f)
            
            plugins_data = data.get("plugins", {})
            
            for name, info in plugins_data.items():
                plugin = PluginInfo(
                    name=name,
                    versions=info.get("version", ["vol3"]),
                    syntax=info.get("syntax", ""),
                    description=info.get("description", ""),
                    aliases=info.get("aliases", []),
                    vol3_equivalent=info.get("vol3_equivalent"),
                )
                self._plugins[name] = plugin
                
                # Build alias lookup
                for alias in plugin.aliases:
                    self._aliases[alias.lower()] = name
            
            self._loaded = True
            logger.info(f"Loaded {len(self._plugins)} plugins from registry")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plugin registry: {e}")
            return False
    
    @property
    def plugins(self) -> dict[str, PluginInfo]:
        """Get all loaded plugins."""
        if not self._loaded:
            self.load()
        return self._plugins
    
    def get_plugin(self, name: str) -> PluginInfo | None:
        """Get plugin by name or alias.
        
        Args:
            name: Plugin name or alias
            
        Returns:
            PluginInfo if found, None otherwise
        """
        if not self._loaded:
            self.load()
        
        # Try exact match
        if name in self._plugins:
            return self._plugins[name]
        
        # Try alias lookup
        canonical = self._aliases.get(name.lower())
        if canonical:
            return self._plugins.get(canonical)
        
        # Try case-insensitive search
        name_lower = name.lower()
        for plugin_name, plugin in self._plugins.items():
            if plugin_name.lower() == name_lower:
                return plugin
        
        return None
    
    def is_valid_plugin(self, name: str) -> bool:
        """Check if plugin name is valid.
        
        Args:
            name: Plugin name to check
            
        Returns:
            True if valid plugin
        """
        return self.get_plugin(name) is not None
    
    def get_similar_plugins(self, name: str, n: int = 3) -> list[str]:
        """Get similar plugin names for suggestions.
        
        Args:
            name: Invalid plugin name
            n: Number of suggestions
            
        Returns:
            List of similar valid plugin names
        """
        if not self._loaded:
            self.load()
        
        all_names = list(self._plugins.keys()) + list(self._aliases.keys())
        matches = get_close_matches(name.lower(), [n.lower() for n in all_names], n=n, cutoff=0.5)
        
        # Map back to original case
        result = []
        for match in matches:
            for original in all_names:
                if original.lower() == match:
                    result.append(original)
                    break
        
        return result
    
    def get_all_plugin_names(self) -> list[str]:
        """Get all valid plugin names and aliases."""
        if not self._loaded:
            self.load()
        return list(self._plugins.keys()) + list(self._aliases.keys())


class CommandValidator:
    """Validates Volatility commands in generated responses.
    
    Features:
    - Plugin name validation
    - Syntax pattern matching
    - Suggestion for invalid commands
    - Version awareness (Vol2 vs Vol3)
    """
    
    # Patterns to extract Volatility commands
    COMMAND_PATTERNS = [
        # Vol3: vol -f <file> <plugin>
        re.compile(r'vol(?:atility)?\s+-f\s+[<"\']?[\w./\\-]+[>"\']?\s+(windows\.\w+|\w+)', re.IGNORECASE),
        # Vol3: vol <plugin> -f <file>
        re.compile(r'vol(?:atility)?\s+(windows\.\w+|\w+)\s+-f', re.IGNORECASE),
        # Vol2: vol.py -f <file> <plugin>
        re.compile(r'vol\.py\s+-f\s+[<"\']?[\w./\\-]+[>"\']?\s+(\w+)', re.IGNORECASE),
        # Vol2: volatility -f <file> <plugin>
        re.compile(r'volatility\s+-f\s+[<"\']?[\w./\\-]+[>"\']?\s+(\w+)', re.IGNORECASE),
        # Generic: python vol.py ...
        re.compile(r'python\s+vol\.py\s+.*?(\w+)\s*(?:\n|$)', re.IGNORECASE),
    ]
    
    # Pattern to extract code blocks
    CODE_BLOCK_PATTERN = re.compile(r'```(?:\w+)?\n(.*?)```', re.DOTALL)
    INLINE_CODE_PATTERN = re.compile(r'`([^`]+)`')
    
    def __init__(self, registry: PluginRegistry | None = None):
        """Initialize command validator.
        
        Args:
            registry: PluginRegistry instance
        """
        self.registry = registry or PluginRegistry()
    
    def extract_commands(self, text: str) -> list[tuple[str, str]]:
        """Extract Volatility commands from text.
        
        Args:
            text: Text containing potential commands
            
        Returns:
            List of (full_command, plugin_name) tuples
        """
        commands = []
        
        # Extract from code blocks first
        code_blocks = self.CODE_BLOCK_PATTERN.findall(text)
        
        # Also check inline code
        inline_codes = self.INLINE_CODE_PATTERN.findall(text)
        
        # Process all code segments
        all_code = code_blocks + inline_codes + [text]
        
        for code in all_code:
            for pattern in self.COMMAND_PATTERNS:
                for match in pattern.finditer(code):
                    full_match = match.group(0)
                    plugin_name = match.group(1)
                    
                    if (full_match, plugin_name) not in commands:
                        commands.append((full_match, plugin_name))
        
        return commands
    
    def validate_command(self, command: str, plugin_name: str) -> ValidationResult:
        """Validate a single Volatility command.
        
        Args:
            command: Full command string
            plugin_name: Extracted plugin name
            
        Returns:
            ValidationResult with validation status
        """
        plugin = self.registry.get_plugin(plugin_name)
        
        if plugin:
            # Determine version from command
            version = "vol3" if "windows." in plugin_name or "vol -f" in command.lower() else "vol2"
            
            return ValidationResult(
                command=command,
                is_valid=True,
                plugin_name=plugin.name,
                validation_message=f"Valid {version} plugin: {plugin.description}",
                version=version,
            )
        else:
            # Invalid plugin - get suggestions
            suggestions = self.registry.get_similar_plugins(plugin_name)
            suggestion_text = ""
            if suggestions:
                suggestion_text = f"Did you mean: {', '.join(suggestions)}?"
            
            return ValidationResult(
                command=command,
                is_valid=False,
                plugin_name=plugin_name,
                suggested_correction=suggestions[0] if suggestions else None,
                validation_message=f"Unknown plugin: {plugin_name}. {suggestion_text}",
                version="unknown",
            )
    
    def validate_response(self, response_text: str) -> list[ValidatedCommand]:
        """Validate all Volatility commands in a response.
        
        Args:
            response_text: Full response text
            
        Returns:
            List of ValidatedCommand objects
        """
        commands = self.extract_commands(response_text)
        validated = []
        
        for full_command, plugin_name in commands:
            result = self.validate_command(full_command, plugin_name)
            
            validated.append(ValidatedCommand(
                command=result.command,
                plugin=result.plugin_name or plugin_name,
                arguments=[],  # TODO: Parse arguments
                is_valid=result.is_valid,
                validation_note=result.validation_message,
                version=result.version,
            ))
        
        return validated
    
    def get_validation_summary(self, commands: list[ValidatedCommand]) -> dict:
        """Get validation summary for a list of commands.
        
        Args:
            commands: List of validated commands
            
        Returns:
            Summary dictionary
        """
        total = len(commands)
        valid = sum(1 for c in commands if c.is_valid)
        invalid = total - valid
        
        return {
            "total_commands": total,
            "valid_commands": valid,
            "invalid_commands": invalid,
            "validity_rate": round(valid / total * 100, 1) if total > 0 else 100.0,
            "all_valid": invalid == 0,
            "invalid_details": [
                {"command": c.command, "plugin": c.plugin, "note": c.validation_note}
                for c in commands if not c.is_valid
            ],
        }
    
    def format_validated_response(self, response_text: str) -> tuple[str, list[ValidatedCommand]]:
        """Format response with validation indicators.
        
        Args:
            response_text: Original response text
            
        Returns:
            Tuple of (formatted_text, validated_commands)
        """
        validated = self.validate_response(response_text)
        formatted = response_text
        
        # Add indicators to commands in the response
        for cmd in validated:
            if cmd.is_valid:
                indicator = "✅"
            else:
                indicator = "⚠️"
            
            # Find and annotate the command in text
            # Be careful not to break markdown code blocks
            # For now, we'll append validation status after code blocks
        
        # Append validation summary if there are invalid commands
        invalid = [c for c in validated if not c.is_valid]
        if invalid:
            formatted += "\n\n---\n⚠️ **Command Validation Warnings:**\n"
            for cmd in invalid:
                formatted += f"- `{cmd.plugin}`: {cmd.validation_note}\n"
        
        return formatted, validated


# Module-level instances
_registry: PluginRegistry | None = None
_validator: CommandValidator | None = None


def get_plugin_registry() -> PluginRegistry:
    """Get or create the global plugin registry."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        _registry.load()
    return _registry


def get_command_validator() -> CommandValidator:
    """Get or create the global command validator."""
    global _validator
    if _validator is None:
        _validator = CommandValidator(get_plugin_registry())
    return _validator


def validate_commands_in_text(text: str) -> list[ValidatedCommand]:
    """Convenience function to validate commands in text."""
    return get_command_validator().validate_response(text)
