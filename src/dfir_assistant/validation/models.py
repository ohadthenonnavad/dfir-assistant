"""Domain models for validation."""

from pydantic import BaseModel, Field


class Confidence(BaseModel):
    """Confidence scoring for responses."""
    
    retrieval_confidence: float = Field(ge=0.0, le=1.0)
    generation_confidence: float = Field(ge=0.0, le=1.0)
    validation_confidence: float = Field(ge=0.0, le=1.0)
    overall: float = Field(ge=0.0, le=1.0)
    
    @property
    def level(self) -> str:
        """Get confidence level as string."""
        if self.overall >= 0.7:
            return "HIGH"
        elif self.overall >= 0.5:
            return "MEDIUM"
        return "LOW"


class ValidationResult(BaseModel):
    """Result of command validation."""
    
    command: str
    is_valid: bool
    plugin_name: str | None = None
    suggested_correction: str | None = None
    validation_message: str = ""
    version: str = "vol3"
