"""Domain models for retrieval."""

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """A search query with analyzed weights."""
    
    query: str
    dense_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    sparse_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    top_k: int = Field(default=15, ge=1)
    filters: dict[str, str] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """A search result with chunk and score."""
    
    chunk_id: str
    content: str
    score: float
    book_title: str
    chapter: str | None = None
    section: str | None = None
    page: int | None = None
    contextual_prefix: str = ""
