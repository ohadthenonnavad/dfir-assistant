"""Global pytest fixtures."""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for testing."""
    client = MagicMock()
    client.generate.return_value = {
        "response": "Test response",
        "done": True,
    }
    client.embeddings.return_value = {
        "embedding": [0.1] * 768,
    }
    return client


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing."""
    client = MagicMock()
    client.search.return_value = []
    return client


@pytest.fixture
def sample_chunk():
    """Sample chunk for testing."""
    from dfir_assistant.ingestion.models import Chunk
    return Chunk(
        chunk_id="test_chunk_001",
        content="A VAD (Virtual Address Descriptor) tree is a binary tree structure...",
        contextual_prefix="Source: Windows Internals\nChapter: Memory Management\n---\n",
        source_type="book",
        book_title="Windows Internals",
        chapter="Memory Management",
        section="VAD Trees",
        page=123,
        chunk_index=1,
    )
