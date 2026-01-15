"""Domain models for UI."""

from pydantic import BaseModel


class DisplayConfig(BaseModel):
    """Configuration for UI display."""
    
    show_sources: bool = True
    show_confidence: bool = True
    show_commands_validation: bool = True
    max_history_display: int = 10


class UIState(BaseModel):
    """UI component state."""
    
    is_loading: bool = False
    error_message: str | None = None
    last_query: str = ""
