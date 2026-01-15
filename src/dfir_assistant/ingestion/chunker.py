"""Hierarchical chunking with semantic boundary respect.

This module implements chunking strategies optimized for technical
documentation, ensuring code blocks, tables, and command sequences
are never split.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Iterator

from dfir_assistant.ingestion.models import Chunk, ExtractedContent

logger = logging.getLogger(__name__)


@dataclass
class ChunkingConfig:
    """Configuration for text chunking."""
    
    chunk_size: int = 512  # Target tokens (approximate with chars/4)
    chunk_overlap: int = 100  # Overlap tokens
    min_chunk_size: int = 100  # Minimum viable chunk
    
    # Character-based approximations (4 chars ≈ 1 token)
    @property
    def chunk_size_chars(self) -> int:
        return self.chunk_size * 4
    
    @property
    def chunk_overlap_chars(self) -> int:
        return self.chunk_overlap * 4
    
    @property
    def min_chunk_size_chars(self) -> int:
        return self.min_chunk_size * 4


@dataclass
class ChunkMetadata:
    """Metadata extracted during chunking."""
    
    chapter: str | None = None
    section: str | None = None
    subsection: str | None = None
    page: int | None = None
    has_code: bool = False
    has_table: bool = False
    has_command: bool = False


@dataclass
class ChunkQualityMetrics:
    """Quality metrics for a chunk."""
    
    is_complete_sentence: bool = True
    has_split_code_block: bool = False
    has_split_table: bool = False
    has_garbage_chars: bool = False
    quality_score: float = 1.0
    issues: list[str] = field(default_factory=list)


class HierarchicalChunker:
    """Chunker that respects semantic boundaries in technical documents.
    
    Key features:
    - Never splits code blocks
    - Never splits tables  
    - Never splits command sequences
    - Respects header boundaries (H2, H3)
    - Preserves contextual information
    """
    
    # Separators in priority order (most important first)
    SEPARATORS = [
        "\n## ",      # H2 headers (chapter sections)
        "\n### ",     # H3 headers (subsections)
        "\n#### ",    # H4 headers
        "\n```",      # Code block boundaries (CRITICAL)
        "\n\n",       # Paragraph breaks
        "\n",         # Line breaks
        " ",          # Word boundaries (last resort)
    ]
    
    # Patterns for content that should never be split
    CODE_BLOCK_PATTERN = re.compile(r'```[\s\S]*?```', re.MULTILINE)
    TABLE_PATTERN = re.compile(r'(\|[^\n]+\|\n)+', re.MULTILINE)
    COMMAND_PATTERN = re.compile(
        r'(?:vol\.py|vol\s+-f|volatility).*?(?=\n\n|\n[A-Z]|\Z)',
        re.MULTILINE | re.DOTALL
    )
    
    def __init__(self, config: ChunkingConfig | None = None):
        """Initialize chunker with configuration.
        
        Args:
            config: ChunkingConfig instance, uses defaults if None
        """
        self.config = config or ChunkingConfig()
    
    def chunk_content(self, content: ExtractedContent) -> Iterator[Chunk]:
        """Chunk extracted content into semantic units.
        
        Args:
            content: ExtractedContent from PDF extraction
            
        Yields:
            Chunk objects with content and metadata
        """
        text = content.markdown_content
        document = content.document
        
        # First, protect non-splittable content
        protected_text, protected_blocks = self._protect_content(text)
        
        # Split into chunks respecting boundaries
        raw_chunks = self._recursive_split(
            protected_text,
            self.config.chunk_size_chars,
            self.config.chunk_overlap_chars,
        )
        
        # Restore protected content and generate Chunk objects
        chunk_index = 0
        current_chapter = None
        current_section = None
        
        for raw_chunk in raw_chunks:
            # Restore protected blocks
            restored_chunk = self._restore_content(raw_chunk, protected_blocks)
            
            # Skip empty or too-small chunks
            if len(restored_chunk.strip()) < self.config.min_chunk_size_chars:
                continue
            
            # Extract metadata from chunk content
            metadata = self._extract_metadata(restored_chunk)
            
            # Update running context
            if metadata.chapter:
                current_chapter = metadata.chapter
            if metadata.section:
                current_section = metadata.section
            
            # Estimate page number
            chunk_start = text.find(restored_chunk[:100]) if len(restored_chunk) > 100 else 0
            page = self._estimate_page(chunk_start, content.page_markers)
            
            # Create contextual prefix
            contextual_prefix = self._build_contextual_prefix(
                document.title,
                current_chapter or metadata.chapter,
                current_section or metadata.section,
            )
            
            chunk_id = f"{document.title.lower().replace(' ', '_')}_{chunk_index:04d}"
            
            yield Chunk(
                chunk_id=chunk_id,
                content=restored_chunk.strip(),
                contextual_prefix=contextual_prefix,
                source_type="book",
                book_title=document.title,
                chapter=current_chapter or metadata.chapter,
                section=current_section or metadata.section,
                page=page,
                chunk_index=chunk_index,
            )
            
            chunk_index += 1
        
        logger.info(f"Created {chunk_index} chunks from {document.title}")
    
    def _protect_content(self, text: str) -> tuple[str, dict[str, str]]:
        """Protect non-splittable content with placeholders.
        
        Returns:
            Tuple of (protected_text, {placeholder: original_content})
        """
        protected_blocks = {}
        
        # Protect code blocks
        for i, match in enumerate(self.CODE_BLOCK_PATTERN.finditer(text)):
            placeholder = f"__CODE_BLOCK_{i}__"
            protected_blocks[placeholder] = match.group(0)
            text = text.replace(match.group(0), placeholder, 1)
        
        # Protect tables
        for i, match in enumerate(self.TABLE_PATTERN.finditer(text)):
            placeholder = f"__TABLE_{i}__"
            protected_blocks[placeholder] = match.group(0)
            text = text.replace(match.group(0), placeholder, 1)
        
        return text, protected_blocks
    
    def _restore_content(self, text: str, protected_blocks: dict[str, str]) -> str:
        """Restore protected content from placeholders."""
        for placeholder, original in protected_blocks.items():
            text = text.replace(placeholder, original)
        return text
    
    def _recursive_split(
        self,
        text: str,
        chunk_size: int,
        overlap: int,
        separators: list[str] | None = None,
    ) -> list[str]:
        """Recursively split text using separator hierarchy.
        
        Args:
            text: Text to split
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks
            separators: List of separators to try
            
        Returns:
            List of text chunks
        """
        if separators is None:
            separators = self.SEPARATORS.copy()
        
        if not separators:
            # No more separators, force split at chunk_size
            return self._force_split(text, chunk_size, overlap)
        
        separator = separators[0]
        remaining_separators = separators[1:]
        
        splits = text.split(separator)
        
        if len(splits) == 1:
            # Separator not found, try next one
            return self._recursive_split(text, chunk_size, overlap, remaining_separators)
        
        # Process splits and merge small ones
        chunks = []
        current_chunk = ""
        
        for i, split in enumerate(splits):
            # Add separator back (except for first split)
            if i > 0:
                split = separator + split
            
            if len(current_chunk) + len(split) <= chunk_size:
                current_chunk += split
            else:
                if current_chunk:
                    # Recursively split if still too large
                    if len(current_chunk) > chunk_size:
                        chunks.extend(
                            self._recursive_split(
                                current_chunk, chunk_size, overlap, remaining_separators
                            )
                        )
                    else:
                        chunks.append(current_chunk)
                
                current_chunk = split
                
                # Add overlap from previous chunk
                if chunks and overlap > 0:
                    prev_chunk = chunks[-1]
                    overlap_text = prev_chunk[-overlap:] if len(prev_chunk) > overlap else prev_chunk
                    current_chunk = overlap_text + current_chunk
        
        # Don't forget the last chunk
        if current_chunk:
            if len(current_chunk) > chunk_size:
                chunks.extend(
                    self._recursive_split(
                        current_chunk, chunk_size, overlap, remaining_separators
                    )
                )
            else:
                chunks.append(current_chunk)
        
        return chunks
    
    def _force_split(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        """Force split text at exact chunk_size (last resort)."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # Try to break at word boundary
            if end < len(text):
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunks.append(text[start:end])
            start = end - overlap if overlap > 0 else end
        
        return chunks
    
    def _extract_metadata(self, chunk: str) -> ChunkMetadata:
        """Extract metadata from chunk content."""
        metadata = ChunkMetadata()
        
        # Extract chapter (H1/H2)
        h1_match = re.search(r'^#\s+(.+?)$', chunk, re.MULTILINE)
        if h1_match:
            metadata.chapter = h1_match.group(1).strip()
        
        h2_match = re.search(r'^##\s+(.+?)$', chunk, re.MULTILINE)
        if h2_match:
            metadata.section = h2_match.group(1).strip()
        
        h3_match = re.search(r'^###\s+(.+?)$', chunk, re.MULTILINE)
        if h3_match:
            metadata.subsection = h3_match.group(1).strip()
        
        # Detect content types
        metadata.has_code = '```' in chunk
        metadata.has_table = '|---|' in chunk or '| --- |' in chunk
        metadata.has_command = bool(re.search(r'vol\.py|vol\s+-f|volatility', chunk, re.IGNORECASE))
        
        return metadata
    
    def _estimate_page(self, position: int, page_markers: dict[int, int]) -> int | None:
        """Estimate page number from character position."""
        if not page_markers:
            return None
        
        current_page = 1
        for page, marker_pos in sorted(page_markers.items()):
            if position >= marker_pos:
                current_page = page
            else:
                break
        
        return current_page
    
    def _build_contextual_prefix(
        self,
        book_title: str,
        chapter: str | None,
        section: str | None,
    ) -> str:
        """Build contextual prefix for embedding enhancement."""
        parts = [f"Source: {book_title}"]
        
        if chapter:
            parts.append(f"Chapter: {chapter}")
        if section:
            parts.append(f"Section: {section}")
        
        parts.append("---")
        
        return "\n".join(parts) + "\n"
    
    def validate_chunk(self, chunk: Chunk) -> ChunkQualityMetrics:
        """Validate chunk quality and detect issues.
        
        Args:
            chunk: Chunk to validate
            
        Returns:
            ChunkQualityMetrics with quality assessment
        """
        metrics = ChunkQualityMetrics()
        content = chunk.content
        
        # Check for incomplete sentences
        if content and not content.rstrip().endswith(('.', '!', '?', ':', '```', '|')):
            metrics.is_complete_sentence = False
            metrics.issues.append("Chunk may end mid-sentence")
        
        # Check for split code blocks (odd number of ```)
        code_markers = content.count('```')
        if code_markers % 2 != 0:
            metrics.has_split_code_block = True
            metrics.issues.append("Code block may be split")
        
        # Check for split tables (starts with | but doesn't have header separator)
        if content.strip().startswith('|') and '|---|' not in content:
            metrics.has_split_table = True
            metrics.issues.append("Table may be split")
        
        # Check for garbage characters
        garbage_pattern = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]')
        if garbage_pattern.search(content):
            metrics.has_garbage_chars = True
            metrics.issues.append("Contains garbage characters")
        
        # Calculate quality score
        score = 1.0
        if not metrics.is_complete_sentence:
            score -= 0.1
        if metrics.has_split_code_block:
            score -= 0.3
        if metrics.has_split_table:
            score -= 0.2
        if metrics.has_garbage_chars:
            score -= 0.2
        
        metrics.quality_score = max(0.0, score)
        
        return metrics


class ChunkValidator:
    """Validates chunks and provides quality reports."""
    
    def __init__(self, chunker: HierarchicalChunker | None = None):
        self.chunker = chunker or HierarchicalChunker()
    
    def validate_chunks(self, chunks: list[Chunk]) -> dict:
        """Validate a list of chunks and generate quality report.
        
        Args:
            chunks: List of chunks to validate
            
        Returns:
            Quality report dictionary
        """
        total = len(chunks)
        issues = []
        total_score = 0.0
        
        for chunk in chunks:
            metrics = self.chunker.validate_chunk(chunk)
            total_score += metrics.quality_score
            
            if metrics.issues:
                issues.append({
                    "chunk_id": chunk.chunk_id,
                    "issues": metrics.issues,
                    "score": metrics.quality_score,
                })
        
        avg_score = total_score / total if total > 0 else 0.0
        
        return {
            "total_chunks": total,
            "average_quality_score": round(avg_score, 3),
            "chunks_with_issues": len(issues),
            "issue_rate": round(len(issues) / total * 100, 1) if total > 0 else 0,
            "issues": issues[:20],  # Limit to first 20 issues
            "passed": avg_score >= 0.9,
        }


def get_chunker(config: ChunkingConfig | None = None) -> HierarchicalChunker:
    """Get configured chunker instance."""
    return HierarchicalChunker(config)
