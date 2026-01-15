"""Shared Pydantic models used across multiple domains."""

from pydantic import BaseModel, Field
from typing import Generic, TypeVar

T = TypeVar("T")


class SourceCitation(BaseModel):
    """Source attribution for RAG responses."""
    
    book_title: str
    chapter: str | None = None
    section: str | None = None
    page: int | None = None
    chunk_id: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class ResponseConfidence(BaseModel):
    """Multi-factor confidence scoring."""
    
    retrieval_score: float = Field(ge=0.0, le=1.0, description="Chunk relevance")
    generation_score: float = Field(ge=0.0, le=1.0, description="Model confidence")
    validation_score: float = Field(ge=0.0, le=1.0, description="Command validity")
    overall: float = Field(ge=0.0, le=1.0, description="Weighted average")
    
    @property
    def disclaimer(self) -> str | None:
        """Get appropriate disclaimer based on confidence level."""
        if self.overall < 0.5:
            return "⚠️ Low confidence - please verify this response"
        if self.validation_score < 0.8:
            return "⚠️ Commands should be verified before execution"
        return None


class ResponseWrapper(BaseModel, Generic[T]):
    """Standard wrapper for all user-facing responses."""
    
    success: bool
    data: T | None = None
    error: str | None = None
    confidence: ResponseConfidence | None = None
    disclaimer: str | None = None
    sources: list[SourceCitation] = Field(default_factory=list)


class ValidatedCommand(BaseModel):
    """A validated Volatility command."""
    
    command: str
    plugin: str
    arguments: list[str] = Field(default_factory=list)
    is_valid: bool
    validation_note: str | None = None
    version: str = Field(default="vol3", description="vol2 or vol3")
