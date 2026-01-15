"""Contextual Retrieval Prepending for enhanced embedding quality.

This module implements the Anthropic Contextual Retrieval technique,
prepending source context to each chunk before embedding to improve
retrieval accuracy.
"""

import logging
from dataclasses import dataclass
from typing import Iterator

from dfir_assistant.ingestion.models import Chunk

logger = logging.getLogger(__name__)


@dataclass
class ContextualConfig:
    """Configuration for contextual preprocessing."""
    
    include_source: bool = True
    include_chapter: bool = True
    include_section: bool = True
    include_page: bool = False
    separator: str = "---"
    max_context_length: int = 200  # chars


class ContextualPreprocessor:
    """Prepends source context to chunks for enhanced embedding.
    
    Based on Anthropic's Contextual Retrieval technique:
    https://www.anthropic.com/news/contextual-retrieval
    
    The contextual prefix helps embeddings capture document-level
    context, improving retrieval for ambiguous or context-dependent
    queries.
    """
    
    def __init__(self, config: ContextualConfig | None = None):
        """Initialize preprocessor with configuration.
        
        Args:
            config: ContextualConfig instance, uses defaults if None
        """
        self.config = config or ContextualConfig()
    
    def build_contextual_prefix(
        self,
        source: str | None = None,
        chapter: str | None = None,
        section: str | None = None,
        page: int | None = None,
        source_type: str = "book",
    ) -> str:
        """Build contextual prefix string.
        
        Args:
            source: Source document title
            chapter: Chapter name
            section: Section name
            page: Page number
            source_type: Type of source (book, doc, org)
            
        Returns:
            Formatted contextual prefix string
        """
        parts = []
        
        if self.config.include_source and source:
            source_label = self._get_source_label(source_type)
            parts.append(f"{source_label}: {source}")
        
        if self.config.include_chapter and chapter:
            parts.append(f"Chapter: {chapter}")
        
        if self.config.include_section and section:
            parts.append(f"Section: {section}")
        
        if self.config.include_page and page:
            parts.append(f"Page: {page}")
        
        if not parts:
            return ""
        
        prefix = "\n".join(parts)
        
        # Truncate if too long
        if len(prefix) > self.config.max_context_length:
            prefix = prefix[:self.config.max_context_length - 3] + "..."
        
        return f"{prefix}\n{self.config.separator}\n"
    
    def _get_source_label(self, source_type: str) -> str:
        """Get appropriate label for source type."""
        labels = {
            "book": "Source",
            "doc": "Document",
            "org": "Organization Knowledge",
            "procedure": "Procedure",
        }
        return labels.get(source_type, "Source")
    
    def preprocess_chunk(self, chunk: Chunk) -> Chunk:
        """Add contextual prefix to a chunk if not already present.
        
        Args:
            chunk: Chunk to preprocess
            
        Returns:
            New Chunk with contextual_prefix set
        """
        if chunk.contextual_prefix:
            # Already has prefix, return as-is
            return chunk
        
        prefix = self.build_contextual_prefix(
            source=chunk.book_title,
            chapter=chunk.chapter,
            section=chunk.section,
            page=chunk.page,
            source_type=chunk.source_type,
        )
        
        # Create new chunk with prefix (immutable pattern)
        return Chunk(
            chunk_id=chunk.chunk_id,
            content=chunk.content,
            contextual_prefix=prefix,
            source_type=chunk.source_type,
            book_title=chunk.book_title,
            chapter=chunk.chapter,
            section=chunk.section,
            page=chunk.page,
            chunk_index=chunk.chunk_index,
        )
    
    def preprocess_chunks(self, chunks: Iterator[Chunk]) -> Iterator[Chunk]:
        """Preprocess multiple chunks with contextual prefixes.
        
        Args:
            chunks: Iterator of chunks to preprocess
            
        Yields:
            Preprocessed chunks with contextual prefixes
        """
        for chunk in chunks:
            yield self.preprocess_chunk(chunk)
    
    def get_text_for_embedding(self, chunk: Chunk) -> str:
        """Get the full text to embed including contextual prefix.
        
        Args:
            chunk: Chunk to get embedding text for
            
        Returns:
            Concatenated contextual_prefix + content
        """
        prefix = chunk.contextual_prefix or self.build_contextual_prefix(
            source=chunk.book_title,
            chapter=chunk.chapter,
            section=chunk.section,
            page=chunk.page,
            source_type=chunk.source_type,
        )
        
        return f"{prefix}{chunk.content}"


class BatchPreprocessor:
    """Batch preprocessing for large document collections."""
    
    def __init__(self, preprocessor: ContextualPreprocessor | None = None):
        """Initialize batch preprocessor.
        
        Args:
            preprocessor: ContextualPreprocessor instance
        """
        self.preprocessor = preprocessor or ContextualPreprocessor()
        self._stats = {
            "total_processed": 0,
            "with_existing_prefix": 0,
            "prefix_added": 0,
        }
    
    def process_batch(
        self,
        chunks: list[Chunk],
        update_stats: bool = True,
    ) -> list[Chunk]:
        """Process a batch of chunks.
        
        Args:
            chunks: List of chunks to process
            update_stats: Whether to update processing statistics
            
        Returns:
            List of preprocessed chunks
        """
        processed = []
        
        for chunk in chunks:
            had_prefix = bool(chunk.contextual_prefix)
            processed_chunk = self.preprocessor.preprocess_chunk(chunk)
            processed.append(processed_chunk)
            
            if update_stats:
                self._stats["total_processed"] += 1
                if had_prefix:
                    self._stats["with_existing_prefix"] += 1
                else:
                    self._stats["prefix_added"] += 1
        
        return processed
    
    def get_embedding_texts(self, chunks: list[Chunk]) -> list[str]:
        """Get embedding texts for a batch of chunks.
        
        Args:
            chunks: List of chunks
            
        Returns:
            List of texts ready for embedding
        """
        return [
            self.preprocessor.get_text_for_embedding(chunk)
            for chunk in chunks
        ]
    
    @property
    def stats(self) -> dict:
        """Get processing statistics."""
        return self._stats.copy()
    
    def reset_stats(self):
        """Reset processing statistics."""
        self._stats = {
            "total_processed": 0,
            "with_existing_prefix": 0,
            "prefix_added": 0,
        }


def get_preprocessor(config: ContextualConfig | None = None) -> ContextualPreprocessor:
    """Get configured preprocessor instance."""
    return ContextualPreprocessor(config)


def get_batch_preprocessor() -> BatchPreprocessor:
    """Get batch preprocessor instance."""
    return BatchPreprocessor()
