"""Response formatters for Gradio UI.

Provides formatting utilities for displaying responses with
validation indicators, source citations, and warnings.
"""

import re
from dataclasses import dataclass

from dfir_assistant.models import ValidatedCommand, SourceCitation, ResponseConfidence


@dataclass
class FormattedResponse:
    """A formatted response ready for UI display."""
    
    content: str
    command_warnings: list[str]
    confidence_indicator: str
    sources_html: str


class ResponseFormatter:
    """Formats RAG responses for Gradio display.
    
    Features:
    - Command validation indicators (✅/⚠️)
    - Confidence level display
    - Collapsible source citations
    - Markdown table formatting
    """
    
    # Confidence level indicators
    CONFIDENCE_INDICATORS = {
        "high": "🟢 High Confidence",
        "medium": "🟡 Medium Confidence", 
        "low": "🔴 Low Confidence",
    }
    
    def format_response(
        self,
        response_text: str,
        validated_commands: list[ValidatedCommand] | None = None,
        confidence: ResponseConfidence | None = None,
        sources: list[SourceCitation] | None = None,
    ) -> FormattedResponse:
        """Format a response for UI display.
        
        Args:
            response_text: Raw response text
            validated_commands: List of validated commands
            confidence: Response confidence scores
            sources: Source citations
            
        Returns:
            FormattedResponse with all formatting applied
        """
        content = response_text
        warnings = []
        
        # Add command validation indicators
        if validated_commands:
            content, warnings = self._add_command_indicators(content, validated_commands)
        
        # Format confidence indicator
        confidence_indicator = self._format_confidence(confidence)
        
        # Format sources
        sources_html = self._format_sources(sources) if sources else ""
        
        return FormattedResponse(
            content=content,
            command_warnings=warnings,
            confidence_indicator=confidence_indicator,
            sources_html=sources_html,
        )
    
    def _add_command_indicators(
        self,
        content: str,
        commands: list[ValidatedCommand],
    ) -> tuple[str, list[str]]:
        """Add validation indicators to commands in content.
        
        Returns:
            Tuple of (modified_content, warnings_list)
        """
        warnings = []
        
        # Build warning section for invalid commands
        invalid_commands = [c for c in commands if not c.is_valid]
        
        if invalid_commands:
            warnings.append("---")
            warnings.append("⚠️ **Command Validation Warnings:**")
            for cmd in invalid_commands:
                warning = f"- `{cmd.plugin}`: {cmd.validation_note or 'Unknown plugin'}"
                warnings.append(warning)
        
        # Add validation summary
        valid_count = sum(1 for c in commands if c.is_valid)
        total = len(commands)
        
        if total > 0:
            if valid_count == total:
                content += f"\n\n✅ *All {total} Volatility commands verified*"
            else:
                content += f"\n\n⚠️ *{valid_count}/{total} commands verified*"
        
        return content, warnings
    
    def _format_confidence(self, confidence: ResponseConfidence | None) -> str:
        """Format confidence indicator."""
        if confidence is None:
            return ""
        
        overall = confidence.overall
        
        if overall >= 0.7:
            indicator = self.CONFIDENCE_INDICATORS["high"]
        elif overall >= 0.5:
            indicator = self.CONFIDENCE_INDICATORS["medium"]
        else:
            indicator = self.CONFIDENCE_INDICATORS["low"]
        
        disclaimer = confidence.disclaimer
        
        if disclaimer:
            return f"{indicator}\n\n{disclaimer}"
        
        return indicator
    
    def _format_sources(self, sources: list[SourceCitation]) -> str:
        """Format source citations as HTML/Markdown."""
        if not sources:
            return ""
        
        lines = ["<details>", "<summary>📚 Sources</summary>", ""]
        
        for i, source in enumerate(sources, 1):
            relevance_pct = int(source.relevance_score * 100)
            location = f"Chapter: {source.chapter}" if source.chapter else ""
            if source.section:
                location += f", Section: {source.section}"
            if source.page:
                location += f", Page {source.page}"
            
            lines.append(f"**{i}. {source.book_title}** ({relevance_pct}% relevant)")
            if location:
                lines.append(f"   {location}")
            lines.append("")
        
        lines.append("</details>")
        
        return "\n".join(lines)
    
    def format_command_warning_box(self, command: ValidatedCommand) -> str:
        """Format a single command warning as a styled box."""
        if command.is_valid:
            return f"""
<div style="padding: 10px; background-color: #d4edda; border-radius: 5px; margin: 5px 0;">
✅ <code>{command.command}</code>
<br><small>Valid {command.version} plugin: {command.plugin}</small>
</div>
"""
        else:
            suggestion = ""
            if command.validation_note:
                suggestion = f"<br><small>{command.validation_note}</small>"
            
            return f"""
<div style="padding: 10px; background-color: #fff3cd; border-radius: 5px; margin: 5px 0;">
⚠️ <code>{command.command}</code>
<br><small>Unverified plugin: {command.plugin}</small>
{suggestion}
</div>
"""
    
    def format_low_confidence_warning(self) -> str:
        """Format warning message for low confidence responses."""
        return """
<div style="padding: 15px; background-color: #f8d7da; border-radius: 5px; margin: 10px 0; border-left: 4px solid #dc3545;">
⚠️ <strong>Low Confidence Response</strong>
<p>This response may not be fully accurate. The system couldn't find highly relevant information in the knowledge base for your query.</p>
<p><strong>Recommendations:</strong></p>
<ul>
<li>Verify the information independently</li>
<li>Rephrase your question with more specific terms</li>
<li>Check the Volatility documentation directly</li>
</ul>
</div>
"""
    
    def format_error_response(self, error_type: str, message: str) -> str:
        """Format error response for display."""
        icons = {
            "retrieval": "🔍",
            "generation": "🤖",
            "validation": "⚠️",
            "vram": "💾",
            "connection": "🔌",
        }
        
        icon = icons.get(error_type, "❌")
        
        return f"""
<div style="padding: 15px; background-color: #f8d7da; border-radius: 5px; margin: 10px 0;">
{icon} <strong>Error: {error_type.title()}</strong>
<p>{message}</p>
</div>
"""


def format_validated_response(
    response: str,
    commands: list[ValidatedCommand],
    confidence: ResponseConfidence | None = None,
) -> str:
    """Convenience function to format a validated response."""
    formatter = ResponseFormatter()
    result = formatter.format_response(
        response_text=response,
        validated_commands=commands,
        confidence=confidence,
    )
    
    output = result.content
    
    if result.confidence_indicator:
        output = f"{result.confidence_indicator}\n\n---\n\n{output}"
    
    if result.command_warnings:
        output += "\n\n" + "\n".join(result.command_warnings)
    
    return output
