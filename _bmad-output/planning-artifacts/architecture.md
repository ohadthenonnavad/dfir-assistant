---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
status: 'complete'
completedAt: '2026-01-15'
inputDocuments:
  - _bmad-output/planning-artifacts/prd-windows-dfir-assistant-v2.md
  - _bmad-output/planning-artifacts/product-brief-windows-dfir-assistant-2026-01-13.md
workflowType: 'architecture'
project_name: 'Windows Internals DFIR Knowledge Assistant'
user_name: 'Ohad'
date: '2026-01-15'
partyModeEnhanced: true
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
The system provides an AI-powered Senior DFIR Analyst assistant with 5 core features:

| ID | Feature | Priority | Architectural Complexity |
|----|---------|----------|-------------------------|
| FR-001 | Knowledge Q&A | P0 | Medium - Standard RAG |
| FR-002 | Anomaly Explanation | P0 | High - Structured output with tables |
| FR-003 | Procedural Guidance | P0 | High - Command validation required |
| FR-004 | Organization Context | P1 | Medium - Additional retrieval source |
| FR-005 | Multi-Turn | P1 | Medium - Session state management |

**Non-Functional Requirements:**

| Category | Requirement | Impact on Architecture |
|----------|-------------|----------------------|
| Performance | <10s first token, <30s full response | Streaming, optimized retrieval |
| Security | Air-gap, no telemetry | 100% local deployment |
| VRAM | 24GB max (RTX 4090) | Model size constrained |
| Reliability | 100% valid Volatility commands | Post-generation validation |
| Availability | Business hours, 5 min recovery | Simple restart, persistent data |

**Scale & Complexity (Refined via Party Mode):**
- Primary domain: AI/ML Application (Python RAG Pipeline)
- **Architectural complexity**: MEDIUM (proven patterns)
- **Quality complexity**: HIGH (100% command accuracy)
- **Operational complexity**: MEDIUM-HIGH (air-gap, VRAM constraints)
- Estimated architectural components: 8-10 major components
- Data volume: ~50K chunks from 30 books
- Concurrent users: 1 (MVP), 3-5 (future)

### Technical Constraints & Dependencies

| Constraint | Description | Mitigation |
|------------|-------------|------------|
| Air-Gap | No internet access | All components local, offline deps |
| 24GB VRAM | Single RTX 4090 | Qwen2.5 32B Q4 + nomic-embed |
| Single GPU | No parallelism | Sequential inference |
| PDF Complexity | Complex book layouts | marker-pdf + validation |
| Copyright | User-provided books | No content distribution |

**External Dependencies:**

| Dependency | Purpose | Risk Level | Air-Gap Consideration |
|------------|---------|------------|----------------------|
| Ollama | LLM serving | Low | Self-contained binary |
| Qdrant | Vector database | Low | Docker or standalone |
| marker-pdf | PDF extraction | Medium | **Offline pip install needed** |
| Instructor | Structured output | Low | **Ollama adapter required** |
| Gradio | UI framework | Low | Pip dependencies |

### Cross-Cutting Concerns Identified

1. **VRAM Management** (🔴 BLOCKING)
   - All components compete for GPU memory
   - 20GB estimated of 24GB available - **no headroom**
   - KV cache grows with context length
   - **MUST validate empirically before development**
   
2. **Command Validation** 
   - Every Volatility command must be validated against known plugin list
   - Critical for user trust
   
3. **Retrieval Quality** 
   - Confidence scoring needed
   - System must admit when it doesn't know
   - Trust > Utility > Experience
   
4. **Response Structuring** 
   - Consistent output format with Instructor/Pydantic models
   - Requires custom Ollama adapter (not standard OpenAI API)
   
5. **Audit Logging** 
   - All queries and responses logged for review
   
6. **Source Citations** 
   - Every response must cite source material

7. **Testability** (Added from Party Mode)
   - Mocking strategy for air-gap CI
   - End-to-end RAG pipeline testing
   - Component isolation for offline testing

### Missing Components Identified (Party Mode)

| Component | Description | Priority |
|-----------|-------------|----------|
| **Conversation State Manager** | Session tracking for multi-turn | P1 |
| **Dependency Management Strategy** | pip/uv/poetry + offline install | P0 |
| **Configuration Management** | Env vars, YAML, secrets handling | P0 |
| **Test Architecture** | Mocking strategy, integration tests | P1 |
| **Recovery Procedure** | Model reload after crash | P1 |

### Risk Assessment (Enhanced)

| Risk | Probability | Impact | Mitigation Status | Priority |
|------|-------------|--------|-------------------|----------|
| VRAM overflow | Medium | **Critical** | ⚠️ UNTESTED | **BLOCKING** |
| Command hallucination | High | High | ✅ Validation planned | P0 |
| Retrieval failure | Medium | Medium | ✅ Confidence scoring | P0 |
| PDF extraction errors | Medium | Medium | ⚠️ Needs validation | P1 |
| Offline dependency install | Medium | High | ⚠️ Not addressed | P0 |

### Priority Framework

Based on Party Mode discussion, architectural priorities should be:

1. **Trust** - Command validation, confidence scoring, "I don't know" responses
2. **Utility** - Retrieval quality, response accuracy  
3. **Experience** - Streaming, UI polish

---

_Project Context Analysis completed with Party Mode enhancements from Winston (Architect), Murat (Test Architect), Amelia (Developer), and John (PM)._

## Starter Template Evaluation

### Primary Technology Domain

**Python AI/ML Application** - RAG Pipeline with Local LLM

This project uses Python for a Retrieval-Augmented Generation system with specific requirements that don't fit standard starter templates:
- Air-gapped deployment (no pip install at runtime)
- Instructor for structured output (not standard LangChain/LlamaIndex)
- Custom command validation layer
- Gradio chat UI

### Starter Options Considered

| Option | Fit | Reason |
|--------|-----|--------|
| LangChain Templates | ❌ Poor | Too abstracted, doesn't support Instructor well |
| LlamaIndex Starter | ❌ Poor | Opinionated retrieval doesn't fit hybrid search needs |
| Poetry + src layout | ✅ Good | Standard Python project structure |
| **uv + src layout** | ✅ Best | Modern, fast, excellent lock files for air-gap |

### Selected Approach: Custom Structure with uv

**Rationale:**
- `uv` provides fast, reproducible dependency management
- Lock files enable offline dependency installation
- No framework abstractions - full control over RAG pipeline
- Standard Python src layout for maintainability

**Initialization Commands:**

```bash
# Create project structure
mkdir -p windows-dfir-assistant
cd windows-dfir-assistant

# Initialize with uv
uv init --name dfir-assistant --python 3.11

# Create src layout
mkdir -p src/dfir_assistant/{ingestion,retrieval,generation,ui,validation}
touch src/dfir_assistant/__init__.py
mkdir -p tests/{unit,integration}
mkdir -p data/{books,chunks,vectors}
mkdir -p config
```

### Project Structure Established

```
windows-dfir-assistant/
├── pyproject.toml           # Project config with uv
├── uv.lock                   # Locked dependencies (critical for air-gap)
├── src/
│   └── dfir_assistant/
│       ├── __init__.py
│       ├── ingestion/       # PDF processing, chunking
│       ├── retrieval/       # Qdrant search, hybrid search
│       ├── generation/      # LLM client, Instructor models
│       ├── validation/      # Command validation, confidence scoring
│       └── ui/              # Gradio interface
├── tests/
│   ├── unit/
│   └── integration/
├── data/
│   ├── books/               # Source PDFs (user-provided)
│   ├── chunks/              # Processed chunks
│   └── vectors/             # Qdrant data directory
├── config/
│   ├── org_context/         # Organization-specific YAML
│   └── volatility_plugins.json  # Valid command list
└── scripts/
    ├── ingest.py            # Data ingestion script
    └── export_deps.sh       # Air-gap dependency export
```

### Architectural Decisions Established by Structure

**Language & Runtime:**
- Python 3.11+ (required for modern typing features)
- uv for dependency management
- pyproject.toml for configuration

**Package Layout:**
- src/ layout for clean imports
- Domain-driven module structure
- Separate data directories for air-gap portability

**Testing Framework:**
- pytest (standard, well-supported)
- tests/ with unit/integration separation
- Fixtures for Ollama/Qdrant mocking

**Development Experience:**
- uv for fast dependency resolution
- Lock file for reproducible installs
- Scripts for common operations

**Air-Gap Considerations:**
- `uv export` for offline wheel bundles
- Data directory structure for portable transfer
- No runtime internet dependencies

### Core Dependencies (pyproject.toml)

```toml
[project]
name = "dfir-assistant"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "gradio>=4.0.0",
    "qdrant-client>=1.7.0",
    "instructor>=1.0.0",
    "httpx>=0.25.0",           # For Ollama API
    "marker-pdf>=0.1.0",       # PDF extraction
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "rich>=13.0.0",            # CLI output
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.1.0",
]
```

**Note:** First implementation story should be EPIC-001 (VRAM Validation), but project initialization is Sprint 0 prerequisite.

---

_Starter Template Evaluation completed. Custom Python structure with uv selected for air-gap compatibility and RAG pipeline control._

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
1. VRAM Allocation Strategy - Conservative approach
2. Hybrid Search Configuration - Adaptive weighting
3. Error Handling Standards - Explicit uncertainty

**Important Decisions (Shape Architecture):**
4. Chunking Strategy - Hybrid with semantic boundaries
5. Configuration Management - Pydantic Settings

**Deferred Decisions (Post-MVP):**
- Multi-user session management
- Horizontal scaling strategy
- Alternative model support

### Decision 1: VRAM Allocation Strategy

| Attribute | Value |
|-----------|-------|
| **Decision** | Conservative (Option A) |
| **Rationale** | 24GB VRAM with ~20GB projected usage leaves no margin. Unpredictable KV cache growth and model loading spikes require headroom. |
| **Implementation** | Load embedding model to CPU, Qdrant indexes to CPU memory |
| **Trade-off** | ~50-100ms additional latency per query (negligible vs. 10s+ total response time) |
| **Affects** | EPIC-001 (VRAM Validation), All inference components |
| **Party Mode Consensus** | Unanimous - reliability over performance for P0 |

**VRAM Budget (Conservative):**

| Component | VRAM | Location |
|-----------|------|----------|
| Qwen2.5 32B Q4_K_M | 18-20GB | GPU |
| nomic-embed-text | 0 | CPU |
| Qdrant indexes | 0 | System RAM |
| System overhead | 2-4GB | GPU |
| **Available Headroom** | **2-4GB** | Buffer |

### Decision 2: Chunking Strategy

| Attribute | Value |
|-----------|-------|
| **Decision** | Hybrid chunking with semantic boundaries |
| **Rationale** | Technical content requires respecting code blocks, tables, and command sequences |
| **Implementation** | RecursiveCharacterTextSplitter with DFIR-tuned separators |
| **Affects** | EPIC-002 (Data Ingestion), Retrieval quality |

**Chunking Configuration:**

```python
separators = [
    "\n## ",      # H2 headers (chapter sections)
    "\n### ",     # H3 headers (subsections)
    "\n```",      # Code block boundaries (CRITICAL - never split)
    "\n\n",       # Paragraph breaks
    "\n",         # Line breaks
    " "           # Word boundaries (last resort)
]

chunk_size = 512  # tokens
chunk_overlap = 100  # tokens
```

**Semantic Integrity Rules:**
- ✅ Never split code blocks
- ✅ Never split tables
- ✅ Never split command sequences
- ✅ Prefer splitting at section boundaries

### Decision 3: Hybrid Search Configuration

| Attribute | Value |
|-----------|-------|
| **Decision** | Adaptive weighting based on query analysis |
| **Rationale** | DFIR queries mix exact commands with conceptual questions |
| **Implementation** | Query classifier determines weight distribution |
| **Affects** | EPIC-003 (Retrieval), Response relevance |
| **Party Mode Enhancement** | John's adaptive weighting proposal |

**Adaptive Search Weights:**

| Query Type | Dense Weight | Sparse Weight | Trigger |
|------------|--------------|---------------|---------|
| Command-focused | 0.3 | 0.7 | Contains known commands (pslist, malfind, etc.) |
| Conceptual | 0.5 | 0.5 | General questions |
| Mixed | 0.4 | 0.6 | Default fallback |

**Query Classifier Implementation:**

```python
KNOWN_COMMANDS = ["pslist", "pstree", "malfind", "handles", ...]

def get_search_weights(query: str) -> tuple[float, float]:
    query_lower = query.lower()
    if any(cmd in query_lower for cmd in KNOWN_COMMANDS):
        return (0.3, 0.7)  # Command-focused
    elif any(word in query_lower for word in ["how", "why", "what", "explain"]):
        return (0.5, 0.5)  # Conceptual
    return (0.4, 0.6)  # Default
```

### Decision 4: Configuration Management

| Attribute | Value |
|-----------|-------|
| **Decision** | Pydantic Settings with YAML override |
| **Rationale** | Type-safe defaults, environment variable support, user-editable YAML |
| **Implementation** | BaseSettings with env_file and yaml_file support |
| **Affects** | All components, Testing, Deployment |
| **Party Mode Consensus** | Unanimous - testing-friendly configuration |

**Configuration Structure:**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Ollama Configuration
    ollama_url: str = "http://localhost:11434"
    model_name: str = "qwen2.5:32b-instruct-q4_K_M"
    embedding_model: str = "nomic-embed-text"
    
    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    collection_name: str = "dfir_knowledge"
    
    # Search Configuration
    search_dense_weight: float = 0.4
    search_sparse_weight: float = 0.6
    top_k: int = 10
    rerank_top_k: int = 5
    
    # Chunking Configuration
    chunk_size: int = 512
    chunk_overlap: int = 100
    
    # Confidence Thresholds
    min_confidence: float = 0.5
    warn_confidence: float = 0.7
    
    class Config:
        env_file = ".env"
        env_prefix = "DFIR_"

# Load from YAML with env override
def load_settings() -> Settings:
    yaml_config = load_yaml("config/settings.yaml")
    return Settings(**yaml_config)
```

### Decision 5: Error Handling Standards

| Attribute | Value |
|-----------|-------|
| **Decision** | Explicit uncertainty |
| **Rationale** | Aligns with Trust > Utility > Experience priority framework |
| **Implementation** | Confidence scoring with explicit disclaimers |
| **Affects** | EPIC-004 (Generation), User trust |
| **Party Mode Consensus** | Unanimous - testable and trust-building |

**Error Response Patterns:**

| Scenario | Response Pattern |
|----------|------------------|
| Low confidence (< 0.5) | "⚠️ I'm not confident about this answer. Please verify independently." |
| No relevant chunks | "❓ I couldn't find relevant information in the knowledge base for this query." |
| Command validation failed | "🚨 The generated command could not be validated. Please check the Volatility documentation." |
| Ollama unavailable | "🔴 LLM service unavailable. Please ensure Ollama is running." |
| VRAM overflow | "⚠️ Memory pressure detected. Restarting inference service..." |

**Uncertainty Model:**

```python
class ResponseConfidence(BaseModel):
    retrieval_score: float  # 0-1: chunk relevance
    generation_score: float  # 0-1: model confidence
    validation_score: float  # 0-1: command validity
    overall: float  # weighted average
    
    @property
    def disclaimer(self) -> str | None:
        if self.overall < 0.5:
            return "⚠️ Low confidence - please verify this response"
        if self.validation_score < 0.8:
            return "⚠️ Commands should be verified before execution"
        return None
```

### Decision Impact Analysis

**Implementation Sequence:**
1. Project setup with uv + Pydantic Settings
2. VRAM validation (EPIC-001) - BLOCKING
3. Configuration management infrastructure
4. Error handling framework
5. Chunking pipeline
6. Hybrid search implementation

**Cross-Component Dependencies:**

```
Settings ──────────┬──────────────────────────────────────┐
                   │                                      │
                   ▼                                      ▼
        ┌─────────────────┐                    ┌────────────────┐
        │ VRAM Manager    │                    │ Query Analyzer │
        └────────┬────────┘                    └───────┬────────┘
                 │                                     │
                 ▼                                     ▼
        ┌─────────────────┐                    ┌────────────────┐
        │ Ollama Client   │                    │ Search Weights │
        └────────┬────────┘                    └───────┬────────┘
                 │                                     │
                 └─────────────────┬───────────────────┘
                                   ▼
                         ┌─────────────────┐
                         │ Error Handler   │
                         │ (Explicit)      │
                         └─────────────────┘
```

---

_Core Architectural Decisions completed with Party Mode enhancements from Winston (Architect), Murat (Test Architect), Amelia (Developer), and John (PM)._

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** 12 areas where AI agents could make different choices

### Naming Patterns

#### Python Code Naming (PEP 8 Compliance)

| Element | Convention | Example | Anti-Pattern |
|---------|------------|---------|--------------|
| **Modules** | snake_case | `retrieval_engine.py` | `RetrievalEngine.py` |
| **Classes** | PascalCase | `class ChunkProcessor:` | `class chunk_processor:` |
| **Functions** | snake_case | `def get_embeddings():` | `def getEmbeddings():` |
| **Variables** | snake_case | `chunk_size = 512` | `chunkSize = 512` |
| **Constants** | UPPER_SNAKE | `MAX_CHUNK_SIZE = 1024` | `maxChunkSize = 1024` |
| **Private** | _leading_underscore | `def _internal_method():` | `def internalMethod():` |

#### Pydantic Models

| Element | Convention | Example |
|---------|------------|---------|
| **Model Classes** | PascalCase + suffix | `QueryRequest`, `ResponseModel` |
| **Fields** | snake_case | `chunk_ids: list[str]` |
| **Validators** | snake_case with verb | `@validator validate_confidence()` |

#### File Naming

| Type | Convention | Example |
|------|------------|---------|
| **Modules** | snake_case.py | `hybrid_search.py` |
| **Tests** | test_*.py | `test_hybrid_search.py` |
| **Configs** | lowercase + ext | `settings.yaml`, `.env` |
| **Scripts** | verb_noun.py | `ingest_books.py` |

### Structure Patterns

#### Module Organization

```
src/dfir_assistant/
├── __init__.py              # Package exports
├── main.py                  # Application entry point
├── config.py                # Pydantic Settings class
│
├── ingestion/               # Data ingestion domain
│   ├── __init__.py
│   ├── pdf_extractor.py     # marker-pdf wrapper
│   ├── chunker.py           # Text chunking logic
│   └── models.py            # Domain models (Chunk, Document)
│
├── retrieval/               # Search domain
│   ├── __init__.py
│   ├── embedder.py          # Embedding generation
│   ├── hybrid_search.py     # Qdrant hybrid search
│   ├── reranker.py          # Result reranking
│   └── models.py            # SearchResult, SearchQuery
│
├── generation/              # LLM generation domain
│   ├── __init__.py
│   ├── ollama_client.py     # Ollama HTTP client
│   ├── instructor_adapter.py # Instructor integration
│   ├── prompts.py           # Prompt templates
│   └── models.py            # Response models
│
├── validation/              # Trust layer
│   ├── __init__.py
│   ├── command_validator.py # Volatility command validation
│   ├── confidence_scorer.py # Confidence calculation
│   └── models.py            # ValidationResult, Confidence
│
└── ui/                      # Presentation layer
    ├── __init__.py
    ├── gradio_app.py        # Gradio interface
    ├── formatters.py        # Response formatting
    └── models.py            # UI state models
```

**Rules:**
- ✅ Each domain has its own `models.py` for domain-specific Pydantic models
- ✅ Shared models go in `src/dfir_assistant/models.py` (if needed)
- ✅ No circular imports - dependency flows inward
- ✅ `__init__.py` exports public API only

#### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Fast, isolated tests
│   ├── ingestion/
│   │   └── test_chunker.py
│   ├── retrieval/
│   │   └── test_hybrid_search.py
│   └── validation/
│       └── test_command_validator.py
│
└── integration/             # Tests requiring services
    ├── conftest.py          # Integration fixtures (mocked Ollama)
    ├── test_rag_pipeline.py # End-to-end RAG tests
    └── test_ollama_client.py # Ollama integration
```

**Rules:**
- ✅ Test files mirror source structure
- ✅ Fixtures in `conftest.py` at appropriate level
- ✅ Integration tests use `pytest.mark.integration`
- ✅ Mock external services (Ollama, Qdrant) in unit tests

### Format Patterns

#### Pydantic Response Models

**Standard Response Wrapper:**
```python
from pydantic import BaseModel
from typing import TypeVar, Generic

T = TypeVar('T')

class ResponseWrapper(BaseModel, Generic[T]):
    """Standard wrapper for all responses."""
    success: bool
    data: T | None = None
    error: str | None = None
    confidence: float | None = None
    disclaimer: str | None = None
    sources: list[SourceCitation] = []

class SourceCitation(BaseModel):
    """Source attribution for RAG responses."""
    book_title: str
    chapter: str | None
    page: int | None
    chunk_id: str
    relevance_score: float
```

**Domain Response Models:**
```python
class DFIRResponse(BaseModel):
    """Domain-specific response with validation."""
    answer: str
    commands: list[ValidatedCommand] = []
    tables: list[FormattedTable] = []
    confidence: ResponseConfidence
    
class ValidatedCommand(BaseModel):
    """A validated Volatility command."""
    command: str
    plugin: str
    arguments: list[str]
    is_valid: bool
    validation_note: str | None = None
```

#### Logging Format

**Standard Log Format:**
```python
import logging

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log levels by category:
# DEBUG: Internal state, chunk contents, embeddings
# INFO: User queries, response generation, search results
# WARNING: Low confidence, validation failures, retries
# ERROR: Exceptions, service failures, VRAM issues
```

### Communication Patterns

#### Gradio State Management

**Session State Pattern:**
```python
from dataclasses import dataclass, field

@dataclass
class SessionState:
    """Immutable session state for Gradio."""
    session_id: str
    conversation_history: list[tuple[str, str]] = field(default_factory=list)
    context_chunks: list[str] = field(default_factory=list)
    last_confidence: float = 0.0
    
    def with_message(self, user: str, assistant: str) -> "SessionState":
        """Return new state with added message (immutable)."""
        return SessionState(
            session_id=self.session_id,
            conversation_history=[*self.conversation_history, (user, assistant)],
            context_chunks=self.context_chunks,
            last_confidence=self.last_confidence,
        )
```

**Rules:**
- ✅ State is immutable - always create new instances
- ✅ Session ID generated at conversation start
- ✅ Conversation history limited to last N turns (configurable)

### Process Patterns

#### Error Handling (Explicit Uncertainty)

**Exception Hierarchy:**
```python
class DFIRError(Exception):
    """Base exception for all DFIR Assistant errors."""
    pass

class RetrievalError(DFIRError):
    """Failed to retrieve relevant context."""
    pass

class GenerationError(DFIRError):
    """LLM generation failed."""
    pass

class ValidationError(DFIRError):
    """Command or response validation failed."""
    pass

class VRAMError(DFIRError):
    """VRAM resource exhaustion."""
    pass
```

**Error Handling Pattern:**
```python
async def handle_query(query: str) -> ResponseWrapper[DFIRResponse]:
    try:
        result = await pipeline.process(query)
        return ResponseWrapper(success=True, data=result)
    except RetrievalError as e:
        return ResponseWrapper(
            success=False,
            error="I couldn't find relevant information for this query.",
            disclaimer="❓ No matching content in knowledge base."
        )
    except ValidationError as e:
        return ResponseWrapper(
            success=True,
            data=result,
            disclaimer="⚠️ Some commands could not be validated."
        )
    except VRAMError as e:
        logger.error(f"VRAM overflow: {e}")
        return ResponseWrapper(
            success=False,
            error="System memory issue. Please wait and try again.",
            disclaimer="🔴 Service restarting..."
        )
```

#### Async Patterns

**Rules:**
- ✅ Use `async/await` for I/O operations (Ollama, Qdrant)
- ✅ CPU-bound work (chunking, validation) stays sync
- ✅ Gradio handlers are async
- ✅ No mixing `asyncio` with `threading`

### Enforcement Guidelines

**All AI Agents MUST:**
1. Follow PEP 8 naming conventions (snake_case functions, PascalCase classes)
2. Use the standard `ResponseWrapper` for all user-facing responses
3. Place domain models in `{domain}/models.py`
4. Write tests in mirrored structure under `tests/unit/`
5. Use the exception hierarchy for error handling
6. Never return raw exceptions to users - always wrap with user-friendly messages
7. Log at appropriate levels (INFO for queries, WARNING for validation failures)

**Pattern Verification:**
- Run `ruff check` before commits
- Type checking with `mypy --strict`
- Test coverage minimum: 80% for validation/, 70% for others

---

_Implementation Patterns completed. Consistent naming, structure, format, and process patterns established for AI agent coordination._

## Project Structure & Boundaries

### Deployment Model: Centralized Server

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     AIR-GAPPED SERVER (RTX 4090)                        │
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────────────┐   │
│  │     Ollama      │  │     Qdrant      │  │    DFIR Assistant     │   │
│  │  (systemd svc)  │  │  (Docker/svc)   │  │    (Gradio app)       │   │
│  │   port: 11434   │  │   port: 6333    │  │    port: 7860         │   │
│  │                 │  │                 │  │                       │   │
│  │ Models:         │  │ Collections:    │  │ - Python web server   │   │
│  │ - qwen2.5:32b   │  │ - dfir_books    │  │ - Connects to Ollama  │   │
│  │ - nomic-embed   │  │                 │  │ - Connects to Qdrant  │   │
│  └─────────────────┘  └─────────────────┘  └───────────────────────┘   │
│                                                                         │
│  Server Storage:                                                        │
│  ~/.ollama/models/          - LLM models                                │
│  /var/lib/qdrant/           - Vector database                           │
│  /opt/dfir-assistant/data/  - PDF books, configs                        │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                    Internal network only (air-gapped)
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
     ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
     │ Analyst │         │ Analyst │         │ Analyst │
     │ Browser │         │ Browser │         │ Browser │
     │ http://server:7860 │         │         │
     └─────────┘         └─────────┘         └─────────┘
```

**Key Characteristics:**
- **Single server** hosts all services (Ollama, Qdrant, DFIR Assistant)
- **Shared Qdrant** = One vector database for all users
- **Shared Ollama** = One LLM service for all users
- **Multi-user** = Analysts access via browser
- **No client installation** = Pure web application

### Complete Project Directory Structure

```
windows-dfir-assistant/
├── README.md                        # Project documentation
├── pyproject.toml                   # uv project configuration
├── uv.lock                          # Locked dependencies (air-gap critical)
├── .env.example                     # Environment variable template
├── .gitignore                       # Git ignore rules
├── .python-version                  # Python version (3.11)
│
├── config/                          # Configuration files
│   ├── settings.yaml                # Main application settings
│   ├── org_context/                 # Organization-specific context
│   │   └── example_org.yaml         # Example org context template
│   └── volatility_plugins.json      # Valid Volatility command list
│
├── data/                            # Server-side data (git-ignored)
│   └── books/                       # Source PDFs for ingestion
│       └── .gitkeep
│
├── src/
│   └── dfir_assistant/
│       ├── __init__.py              # Package version and exports
│       ├── main.py                  # Application entry point
│       ├── config.py                # Pydantic Settings (env + YAML)
│       ├── models.py                # Shared Pydantic models
│       │
│       ├── ingestion/               # EPIC-002: Data Ingestion
│       │   ├── __init__.py
│       │   ├── pdf_extractor.py     # marker-pdf wrapper
│       │   ├── chunker.py           # Hybrid chunking implementation
│       │   ├── preprocessor.py      # Text cleaning, normalization
│       │   └── models.py            # Document, Chunk, ExtractedContent
│       │
│       ├── retrieval/               # EPIC-003: Retrieval System
│       │   ├── __init__.py
│       │   ├── embedder.py          # Ollama embedding client
│       │   ├── qdrant_client.py     # Qdrant connection manager
│       │   ├── hybrid_search.py     # Hybrid search orchestration
│       │   ├── query_analyzer.py    # Query classification for weights
│       │   ├── reranker.py          # Result reranking logic
│       │   └── models.py            # SearchQuery, SearchResult
│       │
│       ├── generation/              # EPIC-004: Response Generation
│       │   ├── __init__.py
│       │   ├── ollama_client.py     # Ollama HTTP client (shared svc)
│       │   ├── instructor_adapter.py # Instructor + Pydantic integration
│       │   ├── prompts.py           # Prompt templates
│       │   ├── response_builder.py  # Response assembly with citations
│       │   └── models.py            # DFIRResponse, FormattedTable
│       │
│       ├── validation/              # EPIC-005: Command Validation
│       │   ├── __init__.py
│       │   ├── command_validator.py # Volatility command validation
│       │   ├── confidence_scorer.py # Multi-factor confidence
│       │   ├── plugin_registry.py   # Valid plugin loading
│       │   └── models.py            # ValidatedCommand, Confidence
│       │
│       ├── context/                 # EPIC-006: Organization Context
│       │   ├── __init__.py
│       │   ├── org_loader.py        # YAML org context loading
│       │   ├── context_injector.py  # Context injection into prompts
│       │   └── models.py            # OrgContext, ToolInventory
│       │
│       ├── session/                 # EPIC-007: Multi-Turn
│       │   ├── __init__.py
│       │   ├── state_manager.py     # Per-user session state
│       │   ├── history_builder.py   # Conversation history formatting
│       │   └── models.py            # SessionState, ConversationTurn
│       │
│       ├── ui/                      # EPIC-008: Chat Interface
│       │   ├── __init__.py
│       │   ├── gradio_app.py        # Gradio web interface
│       │   ├── formatters.py        # Response formatting (MD tables)
│       │   ├── components.py        # Custom UI components
│       │   └── models.py            # UIState, DisplayConfig
│       │
│       └── pipeline/                # RAG Pipeline Orchestration
│           ├── __init__.py
│           ├── rag_pipeline.py      # Main pipeline orchestrator
│           ├── streaming.py         # Streaming response handler
│           └── models.py            # PipelineConfig, PipelineResult
│
├── scripts/                         # Server administration scripts
│   ├── ingest.py                    # Data ingestion CLI
│   ├── validate_vram.py             # EPIC-001: VRAM validation
│   ├── export_deps.sh               # Air-gap dependency export
│   ├── setup_qdrant.py              # Qdrant collection setup
│   ├── benchmark.py                 # EPIC-010: Performance benchmarks
│   └── systemd/                     # Service files for deployment
│       ├── dfir-assistant.service   # Systemd service file
│       └── dfir-assistant.env       # Environment for service
│
├── tests/
│   ├── conftest.py                  # Global fixtures
│   ├── fixtures/                    # Test data fixtures
│   │   ├── sample_chunks.json
│   │   ├── sample_queries.json
│   │   └── mock_ollama_responses.json
│   │
│   ├── unit/                        # Unit tests (mocked dependencies)
│   │   ├── ingestion/
│   │   ├── retrieval/
│   │   ├── validation/
│   │   └── generation/
│   │
│   └── integration/                 # Integration tests
│       ├── conftest.py
│       ├── test_rag_pipeline.py
│       ├── test_ollama_client.py
│       └── test_qdrant_search.py
│
└── docs/                            # Documentation
    ├── architecture.md
    ├── deployment.md                # Server deployment guide
    ├── admin-guide.md               # Server administration
    └── user-guide.md                # End-user documentation
```

### Architectural Boundaries

#### Service Boundaries (All on Same Server)

| Service | Port | Managed By | Data Location |
|---------|------|------------|---------------|
| **Ollama** | 11434 | systemd | `~/.ollama/models/` |
| **Qdrant** | 6333 | Docker/systemd | `/var/lib/qdrant/` |
| **DFIR Assistant** | 7860 | systemd | `/opt/dfir-assistant/` |

#### API Boundaries

**External (User-Facing):**
| Endpoint | Handler | Access |
|----------|---------|--------|
| `http://server:7860/` | Gradio web UI | Internal network |
| `http://server:7860/api/predict` | Gradio API | Internal network |

**Internal (Service-to-Service):**
| From | To | Protocol |
|------|-----|----------|
| DFIR Assistant | Ollama | HTTP (localhost:11434) |
| DFIR Assistant | Qdrant | HTTP (localhost:6333) |

#### Data Boundaries

| Data Type | Location | Persistence | Shared? |
|-----------|----------|-------------|---------|
| LLM Models | `~/.ollama/models/` | Ollama managed | Yes |
| Vector Index | `/var/lib/qdrant/` | Qdrant managed | Yes (all users) |
| PDF Books | `/opt/dfir-assistant/data/books/` | File system | Yes (single source) |
| Config | `/opt/dfir-assistant/config/` | File system | Yes |
| User Sessions | In-memory (Gradio) | Ephemeral | No (per-user) |
| Audit Logs | `/var/log/dfir-assistant/` | Append-only | N/A |

### Requirements to Structure Mapping

#### Epic → Directory Mapping

| Epic | Primary Location | Supporting Files |
|------|------------------|------------------|
| **EPIC-001: VRAM Validation** | `scripts/validate_vram.py` | `config/settings.yaml` |
| **EPIC-002: Data Ingestion** | `src/dfir_assistant/ingestion/` | `scripts/ingest.py` |
| **EPIC-003: Retrieval** | `src/dfir_assistant/retrieval/` | `scripts/setup_qdrant.py` |
| **EPIC-004: Generation** | `src/dfir_assistant/generation/` | - |
| **EPIC-005: Validation** | `src/dfir_assistant/validation/` | `config/volatility_plugins.json` |
| **EPIC-006: Org Context** | `src/dfir_assistant/context/` | `config/org_context/` |
| **EPIC-007: Multi-Turn** | `src/dfir_assistant/session/` | - |
| **EPIC-008: Chat UI** | `src/dfir_assistant/ui/` | - |
| **EPIC-009: Testing** | `tests/` | `tests/fixtures/` |
| **EPIC-010: Evaluation** | `scripts/benchmark.py` | - |
| **EPIC-011: Critical Review** | All validation code | - |

### Integration Points

#### Internal Communication Flow

```
[User Browser] ──HTTP──▶ [Gradio :7860]
                              │
                    create/get session
                              │
                              ▼
                    [Session Manager]
                              │
                              ▼
                    [RAG Pipeline]
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
[Query Analyzer]      [Hybrid Search]        [Response Builder]
        │                     │                     │
        │          ┌──────────┴──────────┐         │
        │          │                     │         │
        │          ▼                     ▼         │
        │    [Qdrant :6333]      [Ollama :11434]   │
        │    (vector search)     (embeddings)      │
        │                                          │
        └──────────────────────────────────────────┘
                              │
                              ▼
                    [Command Validator]
                              │
                              ▼
                    [Confidence Scorer]
                              │
                              ▼
                    [Response + Disclaimer]
```

#### External Service Dependencies

| Service | Connection | Health Check |
|---------|------------|--------------|
| Ollama | `http://localhost:11434/api/tags` | `GET /api/tags` |
| Qdrant | `http://localhost:6333/collections` | `GET /collections` |

### Server Deployment Layout

```
/opt/dfir-assistant/              # Application root
├── venv/                         # Python virtual environment
├── src/                          # Application source
├── config/                       # Configuration
├── data/books/                   # PDF source files
├── logs/                         # Application logs
└── scripts/systemd/              # Service files

/var/lib/qdrant/                  # Qdrant data (Docker volume)
├── collections/
│   └── dfir_books/               # Our vector collection

~/.ollama/                        # Ollama home
├── models/
│   ├── qwen2.5:32b-instruct-q4_K_M
│   └── nomic-embed-text

/var/log/dfir-assistant/          # Audit and application logs
├── audit.log                     # Query/response audit trail
├── app.log                       # Application logs
└── error.log                     # Error logs
```

### Development vs Production Structure

| Aspect | Development | Production |
|--------|-------------|------------|
| **Python env** | `uv sync` local | `/opt/dfir-assistant/venv/` |
| **Config** | `.env` / `config/settings.yaml` | Systemd environment file |
| **Ollama** | Local install | Systemd service |
| **Qdrant** | Docker | Docker or systemd |
| **Gradio** | `uv run python -m dfir_assistant.main` | Systemd service |
| **Logs** | Console | `/var/log/dfir-assistant/` |

### Multi-User Considerations

**Shared Resources (Thread-Safe Required):**
- Qdrant client → Connection pooling
- Ollama client → HTTP client pooling
- Config loading → Read-only, load once

**Per-User Resources:**
- Session state → Gradio session management
- Conversation history → In-memory per session
- Query context → Per-request

**Concurrency Model:**
```python
# Gradio handles concurrent users automatically
# Each request gets its own async context
# Session state is per-user (Gradio State component)
```

---

_Project Structure completed. Server-centric deployment with shared Qdrant and Ollama services._

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:** PASS
All technology choices work together. Python 3.11 + uv + Pydantic 2.x + Gradio 4.x + Qdrant + Ollama form a coherent stack. Instructor's custom Ollama adapter is noted and requires dedicated validation.

**Pattern Consistency:** PASS
All patterns (naming, structure, communication) align with Python/Pydantic best practices. PEP 8 enforced via ruff, async patterns consistent, error handling standardized.

**Structure Alignment:** PASS
Project structure directly supports all architectural decisions. Domain modules map 1:1 with epics. Server deployment layout is clear.

### Requirements Coverage Validation ✅

**Epic Coverage:** 11/11 epics have full architectural support
- Each epic maps to specific directories and files
- Cross-epic dependencies handled via Python imports
- Shared models in root models.py when needed

**Functional Requirements Coverage:** PASS
All 5 core features (Q&A, Anomaly, Procedural, Org Context, Multi-Turn) have dedicated modules.

**Non-Functional Requirements Coverage:** PASS
| NFR | Architectural Support | Status |
|-----|----------------------|--------|
| Performance | Streaming, GPU LLM | ✅ |
| Security | Air-gap, local-only | ✅ |
| VRAM | Conservative allocation | ✅ |
| Reliability | Command validation | ✅ |
| Availability | Systemd service | ✅ |
| Multi-user | Shared services | ✅ |

### Implementation Readiness Validation ✅

**Decision Completeness:** PASS
All critical decisions documented with rationale. Party Mode enhancements added adaptive search weights.

**Structure Completeness:** PASS
Complete directory tree with 50+ files defined. All integration points mapped.

**Pattern Completeness:** PASS
Naming, structure, format, communication, and process patterns all documented with examples.

### Gap Analysis Results (Enhanced via Party Mode)

| Priority | Count | Status |
|----------|-------|--------|
| 🔴 Critical | 0 | ✅ None |
| 🟡 Important | 7 | Documented for Sprint 0 |
| ⚪ Nice-to-Have | 3 | Deferred to post-MVP |

**Important Gaps (Party Mode Enhanced):**

| Gap | Source | Resolution |
|-----|--------|------------|
| Instructor/Ollama adapter validation | Winston | Add story to EPIC-004 |
| VRAM monitoring in CI | Murat | Add regression test job |
| Volatility version compatibility | Murat | Document Vol2/Vol3 plugin matrix |
| Air-gap export script details | Amelia | Expand export_deps.sh |
| Session persistence clarification | Amelia | Browser-session based (ephemeral) |
| VRAM fallback models | Winston/John | Document backup models |
| Evaluation dataset creation | John | Sprint 0 task |

### VRAM Fallback Strategy (Party Mode Addition)

**Model Fallback Chain:**
| Priority | Model | VRAM | Capability |
|----------|-------|------|------------|
| Primary | Qwen2.5 32B Q4_K_M | 18-20GB | Full capability |
| Fallback 1 | Qwen2.5 14B Q4_K_M | ~8GB | Reduced, viable |
| Fallback 2 | Qwen2.5 7B Q8_K | ~8GB | Minimum viable |

**Note:** Architecture remains unchanged for fallbacks - only `config/settings.yaml` model_name changes.

### Volatility Compatibility Matrix (Party Mode Addition)

| Plugin Category | Vol2 | Vol3 | Validation |
|-----------------|------|------|------------|
| Process listing | pslist, psscan | windows.pslist | Both in registry |
| Memory maps | vadinfo, vaddump | windows.vadinfo | Both in registry |
| Malware scan | malfind | windows.malfind | Both in registry |
| Network | netscan, connections | windows.netscan | Both in registry |

**Validation Rule:** Accept both Vol2 and Vol3 syntax, note version in response.

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped
- [x] Party Mode enhancements incorporated

**✅ Architectural Decisions**
- [x] Critical decisions documented (5 decisions)
- [x] Technology stack specified
- [x] Adaptive search weights (Party Mode)
- [x] VRAM conservative strategy
- [x] Error handling: explicit uncertainty
- [x] Fallback models documented (Party Mode)

**✅ Implementation Patterns**
- [x] PEP 8 naming conventions
- [x] Domain-driven module structure
- [x] ResponseWrapper standard
- [x] Exception hierarchy
- [x] Async patterns for I/O

**✅ Project Structure**
- [x] Complete directory structure
- [x] Server deployment layout
- [x] Epic → directory mapping
- [x] Integration points diagrammed

**✅ Testing Strategy (Party Mode Enhanced)**
- [x] Unit test structure
- [x] Integration test structure
- [x] Mock Ollama responses (happy + error paths)
- [x] VRAM regression monitoring planned
- [x] Volatility version compatibility tests planned

### Architecture Readiness Assessment

**Overall Status:** ✅ READY FOR IMPLEMENTATION

**Confidence Level:** HIGH
- All validation checks passed
- Party Mode team review incorporated
- Fallback strategies documented
- Testing gaps identified and planned

**Key Strengths:**
1. **Trust-first design** - Command validation, confidence scoring, explicit uncertainty
2. **Air-gap optimized** - uv lock files, server-centric deployment
3. **Multi-user ready** - Shared Qdrant/Ollama, per-user sessions
4. **Testable** - Mocking strategy, comprehensive test structure
5. **Adaptive search** - Query-aware weight distribution
6. **Resilient** - VRAM fallback chain, error recovery patterns

**Areas for Future Enhancement:**
1. Prometheus/Grafana metrics (post-MVP)
2. Model A/B testing capability
3. Admin CLI for server management
4. Multi-GPU support for scale
5. Persistent conversation history (database-backed)

### Implementation Handoff

**AI Agent Guidelines:**
1. Follow all architectural decisions exactly as documented
2. Use implementation patterns consistently across all components
3. Respect project structure and domain boundaries
4. Refer to this document for all architectural questions
5. Validate commands against plugin_registry (both Vol2 and Vol3 syntax)
6. Test Instructor/Ollama adapter early in EPIC-004

**Sprint 0 Prerequisites:**
```bash
# 1. Project initialization
uv init --name dfir-assistant --python 3.11
uv sync

# 2. VRAM Validation (BLOCKING)
python scripts/validate_vram.py

# 3. Evaluation dataset creation
# Create sample queries + expected outputs for benchmark
```

**First Epic Priority:**
⚠️ EPIC-001 (VRAM Validation) must complete successfully before other epics can proceed.

**Fallback Procedure:**
If VRAM validation fails with 32B model:
1. Update `config/settings.yaml` → `model_name: qwen2.5:14b-instruct-q4_K_M`
2. Re-run VRAM validation
3. Proceed with reduced capability (document in release notes)

---

_Architecture Validation completed with Party Mode enhancements from Winston (Architect), Murat (Test Architect), Amelia (Developer), and John (PM). HIGH confidence for implementation._

## Architecture Completion Summary

### Workflow Completion

**Architecture Decision Workflow:** COMPLETED ✅
**Total Steps Completed:** 8
**Date Completed:** 2026-01-15
**Document Location:** `_bmad-output/planning-artifacts/architecture.md`

### Final Architecture Deliverables

**📋 Complete Architecture Document**
- All architectural decisions documented with specific versions
- Implementation patterns ensuring AI agent consistency
- Complete project structure with all files and directories
- Requirements to architecture mapping
- Validation confirming coherence and completeness

**🏗️ Implementation Ready Foundation**
- 5 core architectural decisions made
- 12 implementation patterns defined
- 11 architectural components specified (mapped to epics)
- All functional and non-functional requirements fully supported

**📚 AI Agent Implementation Guide**
- Technology stack: Python 3.11, uv, Pydantic 2.x, Gradio 4.x, Ollama, Qdrant
- Consistency rules that prevent implementation conflicts
- Project structure with clear domain boundaries
- Integration patterns and communication standards

### Implementation Handoff

**For AI Agents:**
This architecture document is your complete guide for implementing the Windows Internals DFIR Knowledge Assistant. Follow all decisions, patterns, and structures exactly as documented.

**First Implementation Priority:**
```bash
# Sprint 0: Project Setup
uv init --name dfir-assistant --python 3.11
uv sync

# BLOCKING: VRAM Validation (EPIC-001)
uv run python scripts/validate_vram.py
```

**Development Sequence:**
1. Initialize project using uv (Sprint 0)
2. Validate VRAM with 32B model (BLOCKING)
3. Set up Ollama and Qdrant services on server
4. Implement data ingestion pipeline (EPIC-002)
5. Implement retrieval system (EPIC-003)
6. Implement generation with Instructor validation (EPIC-004)
7. Implement command validation (EPIC-005)
8. Continue with remaining epics following dependencies

### Quality Assurance Checklist

**✅ Architecture Coherence**
- [x] All decisions work together without conflicts
- [x] Technology choices are compatible
- [x] Patterns support the architectural decisions
- [x] Structure aligns with all choices

**✅ Requirements Coverage**
- [x] All 11 epics architecturally supported
- [x] All non-functional requirements addressed
- [x] Cross-cutting concerns handled
- [x] Integration points defined

**✅ Implementation Readiness**
- [x] Decisions are specific and actionable
- [x] Patterns prevent agent conflicts
- [x] Structure is complete and unambiguous
- [x] Examples provided for clarity
- [x] VRAM fallback chain documented
- [x] Volatility version compatibility addressed

### Project Success Factors

**🎯 Clear Decision Framework**
Every technology choice was made collaboratively with Party Mode team reviews, ensuring all perspectives are represented.

**🔧 Consistency Guarantee**
Implementation patterns and rules ensure multiple AI agents produce compatible, consistent code.

**📋 Complete Coverage**
All project requirements mapped from business needs to technical implementation with epic → directory mappings.

**🏗️ Solid Foundation**
Custom Python project structure with uv provides modern, air-gap compatible foundation.

**🛡️ Trust-First Design**
Command validation, confidence scoring, and explicit uncertainty prioritize user trust over performance.

---

**Architecture Status:** READY FOR IMPLEMENTATION ✅

**Next Phase:** Begin Sprint 0 (Project Setup) → EPIC-001 (VRAM Validation) → Implementation

**Document Maintenance:** Update this architecture when major technical decisions are made during implementation.

---

_Architecture workflow completed. Document created through 8 collaborative steps with 3 Party Mode team review sessions. HIGH confidence for implementation._
