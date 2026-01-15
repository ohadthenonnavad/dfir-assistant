"""Domain models for pipeline orchestration."""

from pydantic import BaseModel, Field
from dfir_assistant.models import ResponseConfidence, SourceCitation


class PipelineConfig(BaseModel):
    """Configuration for RAG pipeline."""
    
    enable_reranking: bool = True
    enable_streaming: bool = True
    max_context_chunks: int = 5
    context_token_budget: int = 4000


class PipelineResult(BaseModel):
    """Result from RAG pipeline execution."""
    
    query: str
    response: str
    confidence: ResponseConfidence
    sources: list[SourceCitation] = Field(default_factory=list)
    latency_ms: float = 0.0
