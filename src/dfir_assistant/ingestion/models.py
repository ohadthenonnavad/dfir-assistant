"""Domain models for ingestion."""

from pydantic import BaseModel, Field


class Document(BaseModel):
    """A source document (PDF book)."""
    
    title: str
    file_path: str
    total_pages: int = 0
    chapters: list[str] = Field(default_factory=list)


class ExtractedContent(BaseModel):
    """Content extracted from PDF."""
    
    document: Document
    markdown_content: str
    page_markers: dict[int, int] = Field(
        default_factory=dict,
        description="Mapping of page numbers to character positions"
    )


class Chunk(BaseModel):
    """A text chunk ready for embedding."""
    
    chunk_id: str
    content: str
    contextual_prefix: str = ""
    source_type: str = "book"
    book_title: str
    chapter: str | None = None
    section: str | None = None
    page: int | None = None
    chunk_index: int = 0
