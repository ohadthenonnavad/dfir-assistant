"""PDF to Markdown extraction using marker-pdf with fallback to PyMuPDF.

This module provides PDF extraction capabilities optimized for technical
documentation like Windows Internals and memory forensics books.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from dfir_assistant.ingestion.models import Document, ExtractedContent

logger = logging.getLogger(__name__)


class PDFExtractor(Protocol):
    """Protocol for PDF extraction implementations."""
    
    def extract(self, pdf_path: Path) -> ExtractedContent:
        """Extract content from PDF to markdown."""
        ...
    
    @property
    def name(self) -> str:
        """Extractor name for logging."""
        ...


@dataclass
class ExtractionResult:
    """Result of PDF extraction with quality metrics."""
    
    content: ExtractedContent
    extractor_used: str
    code_blocks_found: int
    tables_found: int
    quality_score: float  # 0.0-1.0


class MarkerPDFExtractor:
    """PDF extraction using marker-pdf library.
    
    marker-pdf provides high-quality extraction with:
    - Code block preservation
    - Table detection
    - Layout analysis
    """
    
    @property
    def name(self) -> str:
        return "marker-pdf"
    
    def extract(self, pdf_path: Path) -> ExtractedContent:
        """Extract PDF content using marker-pdf.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ExtractedContent with markdown and metadata
            
        Raises:
            ImportError: If marker-pdf is not installed
            ValueError: If extraction fails
        """
        try:
            from marker.converters.pdf import PdfConverter
            from marker.models import create_model_dict
        except ImportError:
            raise ImportError(
                "marker-pdf not installed. Install with: pip install marker-pdf"
            )
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise ValueError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Extracting {pdf_path.name} with marker-pdf...")
        
        # Create converter with models
        models = create_model_dict()
        converter = PdfConverter(artifact_dict=models)
        
        # Convert PDF to markdown
        rendered = converter(str(pdf_path))
        markdown_content = rendered.markdown
        
        # Build page markers (approximate based on content length)
        # marker-pdf doesn't preserve exact page numbers, so we estimate
        page_markers = self._estimate_page_markers(markdown_content)
        
        document = Document(
            title=pdf_path.stem,
            file_path=str(pdf_path),
            total_pages=len(page_markers),
            chapters=self._detect_chapters(markdown_content),
        )
        
        return ExtractedContent(
            document=document,
            markdown_content=markdown_content,
            page_markers=page_markers,
        )
    
    def _estimate_page_markers(self, content: str, chars_per_page: int = 3000) -> dict[int, int]:
        """Estimate page positions based on character count."""
        markers = {}
        page = 1
        for pos in range(0, len(content), chars_per_page):
            markers[page] = pos
            page += 1
        return markers
    
    def _detect_chapters(self, content: str) -> list[str]:
        """Detect chapter titles from markdown headers."""
        import re
        chapters = []
        for match in re.finditer(r'^#\s+(.+?)$', content, re.MULTILINE):
            title = match.group(1).strip()
            if len(title) < 100:  # Reasonable chapter title length
                chapters.append(title)
        return chapters[:50]  # Limit to first 50


class PyMuPDFExtractor:
    """Fallback PDF extraction using PyMuPDF.
    
    PyMuPDF (fitz) provides basic text extraction when marker-pdf fails.
    Quality may be lower for complex layouts.
    """
    
    @property
    def name(self) -> str:
        return "PyMuPDF"
    
    def extract(self, pdf_path: Path) -> ExtractedContent:
        """Extract PDF content using PyMuPDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ExtractedContent with text content
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PyMuPDF not installed. Install with: pip install pymupdf"
            )
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise ValueError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Extracting {pdf_path.name} with PyMuPDF...")
        
        doc = fitz.open(str(pdf_path))
        
        markdown_parts = []
        page_markers = {}
        chapters = []
        
        current_pos = 0
        for page_num, page in enumerate(doc, 1):
            page_markers[page_num] = current_pos
            
            # Extract text blocks
            text = page.get_text("text")
            
            # Basic markdown conversion
            # Detect headers (usually larger font, but we use heuristics)
            lines = text.split('\n')
            for line in lines:
                stripped = line.strip()
                if stripped:
                    # Detect chapter headers (ALL CAPS or "Chapter" prefix)
                    if (stripped.isupper() and len(stripped) > 5 and len(stripped) < 80) or \
                       stripped.lower().startswith("chapter"):
                        markdown_parts.append(f"\n# {stripped}\n")
                        chapters.append(stripped)
                    else:
                        markdown_parts.append(stripped)
            
            markdown_parts.append("\n\n---\n\n")  # Page separator
            current_pos = len('\n'.join(markdown_parts))
        
        doc.close()
        
        markdown_content = '\n'.join(markdown_parts)
        
        document = Document(
            title=pdf_path.stem,
            file_path=str(pdf_path),
            total_pages=len(page_markers),
            chapters=chapters[:50],
        )
        
        return ExtractedContent(
            document=document,
            markdown_content=markdown_content,
            page_markers=page_markers,
        )


class HybridPDFExtractor:
    """Hybrid extractor that tries marker-pdf first, falls back to PyMuPDF.
    
    This is the recommended extractor for production use.
    """
    
    def __init__(self):
        self.primary = MarkerPDFExtractor()
        self.fallback = PyMuPDFExtractor()
        self._last_extractor_used: str = ""
    
    @property
    def name(self) -> str:
        return "hybrid"
    
    @property
    def last_extractor_used(self) -> str:
        return self._last_extractor_used
    
    def extract(self, pdf_path: Path) -> ExtractedContent:
        """Extract PDF using best available method.
        
        Tries marker-pdf first, falls back to PyMuPDF on failure.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            ExtractedContent from successful extractor
        """
        try:
            result = self.primary.extract(pdf_path)
            self._last_extractor_used = self.primary.name
            logger.info(f"Successfully extracted with {self.primary.name}")
            return result
        except Exception as e:
            logger.warning(f"Primary extractor ({self.primary.name}) failed: {e}")
            logger.info(f"Falling back to {self.fallback.name}")
            
            result = self.fallback.extract(pdf_path)
            self._last_extractor_used = self.fallback.name
            return result
    
    def extract_with_quality(self, pdf_path: Path) -> ExtractionResult:
        """Extract PDF and calculate quality metrics.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            ExtractionResult with content and quality metrics
        """
        content = self.extract(pdf_path)
        
        # Calculate quality metrics
        code_blocks = content.markdown_content.count("```")
        tables = content.markdown_content.count("|---|")  # Markdown table separator
        
        # Quality heuristics
        has_structure = len(content.document.chapters) > 0
        has_code = code_blocks > 0
        has_tables = tables > 0
        content_length = len(content.markdown_content)
        
        # Score calculation (simple heuristic)
        score = 0.5  # Base score
        if has_structure:
            score += 0.2
        if has_code:
            score += 0.15
        if has_tables:
            score += 0.15
        if content_length > 10000:
            score = min(score, 1.0)
        
        return ExtractionResult(
            content=content,
            extractor_used=self._last_extractor_used,
            code_blocks_found=code_blocks // 2,  # Pairs of ```
            tables_found=tables,
            quality_score=score,
        )


def get_extractor(extractor_type: str = "hybrid") -> PDFExtractor:
    """Get PDF extractor by type.
    
    Args:
        extractor_type: One of "hybrid", "marker", "pymupdf"
        
    Returns:
        PDFExtractor instance
    """
    extractors = {
        "hybrid": HybridPDFExtractor,
        "marker": MarkerPDFExtractor,
        "pymupdf": PyMuPDFExtractor,
    }
    
    if extractor_type not in extractors:
        raise ValueError(f"Unknown extractor type: {extractor_type}")
    
    return extractors[extractor_type]()
