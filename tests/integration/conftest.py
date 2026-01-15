"""Integration test fixtures."""

import pytest


@pytest.fixture
def ollama_available():
    """Check if Ollama is available for integration tests."""
    import httpx
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture
def qdrant_available():
    """Check if Qdrant is available for integration tests."""
    import httpx
    try:
        response = httpx.get("http://localhost:6333/collections", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False
