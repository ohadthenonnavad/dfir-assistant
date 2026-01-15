---
project_name: 'Windows Internals DFIR Knowledge Assistant'
user_name: 'Ohad'
date: '2026-01-15'
sections_completed: ['technology_stack', 'critical_rules', 'patterns', 'testing', 'anti_patterns']
existing_patterns_found: 12
---

# Project Context for AI Agents

_Critical rules and patterns for implementing the Windows Internals DFIR Knowledge Assistant. Read this before writing any code._

---

## Technology Stack & Versions

| Component | Version | Notes |
|-----------|---------|-------|
| **Python** | 3.11+ | Required for modern typing |
| **uv** | latest | Package manager (NOT pip) |
| **Pydantic** | 2.x | Data validation, settings |
| **Gradio** | 4.x | Web UI framework |
| **Ollama** | latest | LLM serving (HTTP API) |
| **Qdrant** | latest | Vector database |
| **Instructor** | 1.x | Structured LLM output |
| **pytest** | 7.x | Testing framework |
| **ruff** | 0.1.x | Linting (replaces black, isort, flake8) |
| **httpx** | 0.25+ | Async HTTP client |
| **marker-pdf** | latest | PDF extraction |

**Package Management:**
```bash
# ALWAYS use uv, never pip directly
uv add <package>        # Add dependency
uv sync                 # Install from lock
uv run pytest           # Run with env
```

---

## Critical Implementation Rules

### 1. Naming Conventions (PEP 8)

```python
# ✅ CORRECT
def get_search_results() -> list[SearchResult]:  # snake_case functions
class ChunkProcessor:                             # PascalCase classes
MAX_CHUNK_SIZE = 1024                             # UPPER_SNAKE constants
chunk_ids: list[str]                              # snake_case variables

# ❌ WRONG
def getSearchResults():    # No camelCase
class chunk_processor:     # No lowercase classes
maxChunkSize = 1024        # No camelCase variables
```

### 2. Module Structure

Every domain module has this structure:
```
src/dfir_assistant/{domain}/
├── __init__.py          # Public exports only
├── {feature}.py         # Implementation
└── models.py            # Pydantic models for this domain
```

**Import rules:**
- Import from `__init__.py` exports, not internal modules
- No circular imports - dependency flows inward
- Use relative imports within same domain

### 3. Pydantic Models

```python
from pydantic import BaseModel, Field

# ✅ All response data uses Pydantic
class SearchResult(BaseModel):
    chunk_id: str
    content: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    source: SourceCitation

# ✅ Use ResponseWrapper for user-facing responses
class ResponseWrapper(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: str | None = None
    confidence: float | None = None
    disclaimer: str | None = None
    sources: list[SourceCitation] = []
```

### 4. Async Patterns

```python
# ✅ ASYNC for I/O operations (Ollama, Qdrant, HTTP)
async def search_chunks(query: str) -> list[SearchResult]:
    embeddings = await embedder.embed_async(query)
    return await qdrant.search_async(embeddings)

# ✅ SYNC for CPU-bound work (chunking, validation)
def validate_commands(commands: list[str]) -> list[ValidationResult]:
    return [validator.validate(cmd) for cmd in commands]

# ❌ NEVER mix asyncio with threading
```

### 5. Error Handling (Explicit Uncertainty)

```python
# ✅ Custom exception hierarchy
class DFIRError(Exception): pass
class RetrievalError(DFIRError): pass
class GenerationError(DFIRError): pass
class ValidationError(DFIRError): pass
class VRAMError(DFIRError): pass

# ✅ User-friendly error wrapping
try:
    result = await pipeline.process(query)
    return ResponseWrapper(success=True, data=result)
except RetrievalError:
    return ResponseWrapper(
        success=False,
        error="I couldn't find relevant information for this query.",
        disclaimer="❓ No matching content in knowledge base."
    )

# ❌ NEVER expose raw exceptions to users
except Exception as e:
    return str(e)  # WRONG!
```

### 6. Command Validation (CRITICAL)

```python
# ✅ ALWAYS validate Volatility commands before returning
class ValidatedCommand(BaseModel):
    command: str
    plugin: str
    arguments: list[str]
    is_valid: bool
    validation_note: str | None = None

# ✅ Accept BOTH Volatility 2 and 3 syntax
KNOWN_COMMANDS = {
    "pslist": ["windows.pslist", "pslist"],     # Vol3, Vol2
    "malfind": ["windows.malfind", "malfind"],
    "handles": ["windows.handles", "handles"],
}

# ✅ Add disclaimer if command cannot be validated
if not validated:
    response.disclaimer = "⚠️ Command could not be validated. Please verify before execution."
```

### 7. Confidence Scoring

```python
# ✅ Every response has confidence scoring
class ResponseConfidence(BaseModel):
    retrieval_score: float   # 0-1: chunk relevance
    generation_score: float  # 0-1: model confidence  
    validation_score: float  # 0-1: command validity
    overall: float           # weighted average

    @property
    def disclaimer(self) -> str | None:
        if self.overall < 0.5:
            return "⚠️ Low confidence - please verify this response"
        return None
```

### 8. Configuration (Pydantic Settings)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ✅ Use typed settings with defaults
    ollama_url: str = "http://localhost:11434"
    model_name: str = "qwen2.5:32b-instruct-q4_K_M"
    search_dense_weight: float = 0.4
    
    class Config:
        env_file = ".env"
        env_prefix = "DFIR_"

# ✅ Load once at startup
settings = Settings()
```

---

## Search Weights (Adaptive)

```python
# ✅ Query-aware search weighting
def get_search_weights(query: str) -> tuple[float, float]:
    query_lower = query.lower()
    
    # Command-focused: boost sparse (keyword) search
    if any(cmd in query_lower for cmd in KNOWN_COMMANDS):
        return (0.3, 0.7)  # dense, sparse
    
    # Conceptual: balanced
    if any(word in query_lower for word in ["how", "why", "what", "explain"]):
        return (0.5, 0.5)
    
    # Default
    return (0.4, 0.6)
```

---

## Testing Rules

### Test Structure
```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Fast, mocked tests
│   └── {domain}/
│       └── test_{module}.py # Mirrors src/ structure
└── integration/             # Requires services
    └── test_{feature}.py
```

### Test Naming
```python
# ✅ Test files mirror source
# src/dfir_assistant/retrieval/embedder.py
# tests/unit/retrieval/test_embedder.py

# ✅ Descriptive test names
def test_validate_command_returns_invalid_for_unknown_plugin():
    ...

def test_search_weights_boost_sparse_when_command_in_query():
    ...
```

### Mocking
```python
# ✅ Mock external services in unit tests
@pytest.fixture
def mock_ollama_response():
    return {"response": "Test response", "done": True}

# ✅ Mark integration tests
@pytest.mark.integration
async def test_ollama_client_real_connection():
    ...
```

---

## Air-Gap Considerations

1. **No runtime internet** - All dependencies pre-installed via `uv.lock`
2. **No telemetry** - Disable any analytics in dependencies
3. **Local services only** - Ollama, Qdrant on localhost/server
4. **No external API calls** - No OpenAI, no cloud services

```python
# ✅ Check for offline operation
if settings.air_gap_mode:
    assert "localhost" in settings.ollama_url
    assert "localhost" in settings.qdrant_url
```

---

## Anti-Patterns to Avoid

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Use `pip install` | Use `uv add` or `uv sync` |
| Return raw exceptions | Wrap in ResponseWrapper |
| Use camelCase functions | Use snake_case (PEP 8) |
| Mix async/threading | Choose one per operation |
| Skip command validation | Always validate before return |
| Hardcode model names | Use Settings class |
| Trust LLM output blindly | Add confidence scoring |
| Split code blocks in chunks | Use semantic chunking |

---

## Quick Reference

### File Locations
| Purpose | Path |
|---------|------|
| Main entry | `src/dfir_assistant/main.py` |
| Settings | `src/dfir_assistant/config.py` |
| Shared models | `src/dfir_assistant/models.py` |
| Domain models | `src/dfir_assistant/{domain}/models.py` |
| Config files | `config/settings.yaml` |
| Test fixtures | `tests/fixtures/` |

### Key Patterns
| Pattern | Where |
|---------|-------|
| ResponseWrapper | All user-facing responses |
| ValidatedCommand | All Volatility commands |
| Pydantic Settings | Configuration loading |
| Async I/O | Ollama, Qdrant calls |
| Confidence scoring | All RAG responses |

---

_This context file ensures consistent implementation across all AI agents. Refer to `architecture.md` for full architectural details._
