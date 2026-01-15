# User Stories Document
# Windows Internals DFIR Knowledge Assistant

---
workflowStep: 3
status: 'stories-created'
createdAt: '2026-01-15'
totalStories: 39
totalPoints: 129
sourceDocument: epics.md
---

## Story Format Reference

Each story follows this structure:
```
STORY-XXX: [Title]
As a [role], I want [goal] so that [benefit]

Acceptance Criteria:
- [ ] Given [context], when [action], then [expected result]

Technical Notes:
- Implementation details
- Architecture references

Dependencies: [story IDs]
Points: [estimate]
```

---

# SPRINT 0: BLOCKING VALIDATION

## EPIC-001: VRAM Validation & Fallback Planning (8 pts)
**Owner:** Ravi (RAG Developer)
**Sprint:** 0
**Status:** 🔴 BLOCKING - Must pass before all other work

---

### STORY-000: Project Initialization
**As a** developer
**I want** the project structure initialized with uv
**So that** I can begin development with proper dependencies

**Acceptance Criteria:**
- [ ] Given an empty directory, when running `uv init --name dfir-assistant --python 3.11`, then project is created with pyproject.toml
- [ ] Given pyproject.toml, when adding all dependencies from architecture spec, then `uv sync` succeeds
- [ ] Given initialized project, when running `uv export --format requirements-txt`, then dependencies export for air-gap
- [ ] Given project structure, when comparing to architecture.md spec, then all directories exist

**Technical Notes:**
- Follow exact directory structure from [`architecture.md`](_bmad-output/planning-artifacts/architecture.md:186)
- Use Python 3.11 (required for modern typing)
- Dependencies: gradio>=4.0.0, qdrant-client>=1.7.0, instructor>=1.0.0, httpx>=0.25.0, marker-pdf>=0.1.0, pydantic>=2.0.0

**Dependencies:** None
**Points:** 2

---

### STORY-CR-001: VRAM Usage Empirical Validation
**As a** developer
**I want** to validate actual VRAM usage under realistic conditions
**So that** I know the 32B model fits before building features

**Acceptance Criteria:**
- [ ] Given Ollama running with qwen2.5:32b-instruct-q4_K_M loaded, when measuring VRAM, then usage is documented
- [ ] Given 8K context length input, when running inference, then VRAM usage stays under 22GB
- [ ] Given nomic-embed-text loaded simultaneously, when running embedding + inference, then total VRAM documented
- [ ] Given multi-turn conversation (5+ turns), when measuring KV cache growth, then max VRAM documented
- [ ] Given all measurements, when VRAM > 22GB, then fallback to 14B model is triggered

**Technical Notes:**
- Use `nvidia-smi` for VRAM monitoring
- Create `scripts/validate_vram.py` for automated testing
- Document results in `docs/vram-validation-results.md`
- Conservative VRAM budget: 20GB model + 2-4GB overhead

**Dependencies:** STORY-000
**Points:** 3

---

### STORY-CR-002: Fallback LLM Configuration
**As a** developer
**I want** a tested fallback LLM option ready
**So that** the system works even if 32B model doesn't fit

**Acceptance Criteria:**
- [ ] Given qwen2.5:14b-instruct-q4_K_M pulled in Ollama, when running same test prompts, then responses are coherent
- [ ] Given config/settings.yaml, when changing model_name, then system uses new model without code changes
- [ ] Given 14B model, when running VRAM test, then usage is under 10GB
- [ ] Given both 32B and 14B results, when comparing quality, then delta is documented

**Technical Notes:**
- Fallback chain: 32B Q4 → 14B Q4 → 7B Q8
- All prompts must work with any model in chain
- Quality delta acceptable if retrieval quality compensates

**Dependencies:** STORY-CR-001
**Points:** 3

---

### STORY-CR-003: VRAM Monitoring Integration
**As a** developer
**I want** runtime VRAM monitoring in the application
**So that** I can detect and respond to memory pressure

**Acceptance Criteria:**
- [ ] Given application running, when querying VRAM usage, then current usage returned in MB
- [ ] Given VRAM > 22GB, when threshold exceeded, then WARNING logged
- [ ] Given VRAM > 23GB, when critical threshold exceeded, then graceful degradation triggered
- [ ] Given graceful degradation, when triggered, then user receives friendly error message

**Technical Notes:**
- Use `pynvml` library for GPU monitoring
- Log VRAM at each query (INFO level)
- Create `src/dfir_assistant/validation/vram_monitor.py`

**Dependencies:** STORY-CR-001
**Points:** 2

---

# SPRINT 1: FOUNDATION & QUALITY

## EPIC-006: PDF Processing Quality (8 pts)
**Owner:** Dana (Data Engineer)
**Sprint:** 1
**Status:** Foundation - Data quality validation

---

### STORY-CR-017: marker-pdf Validation on Actual Books
**As a** developer
**I want** to validate marker-pdf extraction quality on Windows Internals
**So that** I know the extraction pipeline produces usable content

**Acceptance Criteria:**
- [ ] Given Windows Internals PDF Chapter 5, when extracting with marker-pdf, then markdown output is readable
- [ ] Given extracted markdown, when checking code blocks, then 95%+ are properly formatted
- [ ] Given extracted markdown, when checking tables, then 90%+ are properly formatted
- [ ] Given Art of Memory Forensics PDF, when extracting sample chapter, then quality is documented
- [ ] Given quality assessment, when creating report, then limitations are documented

**Technical Notes:**
- Test with 3 diverse chapters: text-heavy, code-heavy, table-heavy
- Create `scripts/validate_pdf_extraction.py`
- Output quality report to `docs/pdf-extraction-quality.md`

**Dependencies:** STORY-000
**Points:** 3

---

### STORY-CR-018: Fallback PDF Extraction Methods
**As a** developer
**I want** alternative extraction methods tested
**So that** I have options if marker-pdf fails on specific content

**Acceptance Criteria:**
- [ ] Given PyMuPDF, when extracting same test chapters, then quality compared to marker-pdf
- [ ] Given LlamaParse (if available), when extracting, then quality compared
- [ ] Given comparison results, when marker-pdf fails, then fallback method identified
- [ ] Given hybrid approach, when combining methods, then best results documented

**Technical Notes:**
- PyMuPDF: `pip install pymupdf`
- Compare: code block preservation, table extraction, layout handling
- May need different extractors for different book types

**Dependencies:** STORY-CR-017
**Points:** 3

---

### STORY-CR-019: Chunk Quality Validation
**As a** developer
**I want** automated chunk quality validation
**So that** I can ensure ingested content is usable

**Acceptance Criteria:**
- [ ] Given 50 random chunks per book, when spot-checking, then quality score > 90%
- [ ] Given chunk, when checking for complete sentences, then incomplete chunks flagged
- [ ] Given chunk with code, when checking code integrity, then split code blocks flagged
- [ ] Given chunk, when checking for garbage characters, then cleanup applied

**Technical Notes:**
- Create `src/dfir_assistant/ingestion/chunk_validator.py`
- Quality metrics: sentence completeness, code integrity, no garbage
- Output validation report for each ingestion run

**Dependencies:** STORY-CR-017
**Points:** 2

---

## EPIC-007: Single Collection Architecture (5 pts)
**Owner:** Ravi (RAG Developer)
**Sprint:** 1
**Status:** Foundation - Schema design

---

### STORY-CR-020: Unified Qdrant Collection Schema
**As a** developer
**I want** a single Qdrant collection with rich metadata
**So that** retrieval is simple and filtering is flexible

**Acceptance Criteria:**
- [ ] Given collection schema, when designed, then includes: source_type, book_title, chapter, section, page
- [ ] Given schema, when source_type filter applied, then only matching sources returned
- [ ] Given metadata, when querying, then all fields are indexed and queryable
- [ ] Given collection, when storing 50K chunks, then performance is acceptable (<200ms search)

**Technical Notes:**
- Collection name: `dfir_books`
- Metadata schema:
  ```python
  {
    "source_type": "book|doc|org",
    "book_title": str,
    "chapter": str | None,
    "section": str | None,
    "page": int | None,
    "chunk_index": int,
    "contextual_prefix": str
  }
  ```
- Create `scripts/setup_qdrant.py` for collection initialization

**Dependencies:** STORY-000
**Points:** 3

---

### STORY-CR-021: Multi-Collection Benchmark (Conditional)
**As a** developer
**I want** to benchmark multi-collection IF single collection recall < 80%
**So that** I can prove complexity is justified

**Acceptance Criteria:**
- [ ] Given single collection recall measured, when < 80%, then multi-collection test triggered
- [ ] Given multi-collection setup, when A/B testing, then results compared
- [ ] Given comparison, when multi-collection wins by >5%, then architecture updated
- [ ] Given comparison results, when documented, then decision is justified

**Technical Notes:**
- Only execute this story if EPIC-003 evaluation shows poor recall
- Multi-collection design: books, commands, org_context, procedures
- Default: stay with single collection (simpler)

**Dependencies:** STORY-CR-020, EPIC-003 completion
**Points:** 2 (conditional)

---

## EPIC-003: Evaluation Framework (13 pts)
**Owner:** Ravi + Dana
**Sprint:** 1
**Status:** Foundation - Test infrastructure

---

### STORY-CR-007: Golden Q&A Test Dataset
**As a** developer
**I want** a curated test dataset with expected responses
**So that** I can measure system quality objectively

**Acceptance Criteria:**
- [ ] Given dataset, when created, then contains 30+ Q&A pairs
- [ ] Given Q&A pairs, when categorized, then covers: concept (10), anomaly (10), procedure (5), tool_command (5)
- [ ] Given each Q&A, when reviewed, then expected response is human-verified accurate
- [ ] Given dataset, when formatted, then machine-readable JSON with query + expected_chunks + expected_response

**Technical Notes:**
- Create `tests/fixtures/golden_qa_dataset.json`
- Format:
  ```json
  {
    "queries": [
      {
        "id": "Q001",
        "type": "concept",
        "query": "What is a VAD tree?",
        "expected_chunks": ["vad_tree_explanation_chunk"],
        "expected_response_contains": ["binary tree", "virtual address"]
      }
    ]
  }
  ```
- Collaborate with DFIR SME for accuracy review

**Dependencies:** STORY-000
**Points:** 5

---

### STORY-CR-008: Retrieval Quality Metrics
**As a** developer
**I want** automated retrieval quality measurement
**So that** I can track Recall@5 and Precision@5

**Acceptance Criteria:**
- [ ] Given golden dataset query, when searching, then expected chunks tracked
- [ ] Given search results, when calculating Recall@5, then metric reported
- [ ] Given search results, when calculating Precision@5, then metric reported
- [ ] Given metrics, when Recall@5 < 80%, then WARNING logged
- [ ] Given batch run, when processing all golden queries, then aggregate metrics reported

**Technical Notes:**
- Create `src/dfir_assistant/evaluation/retrieval_metrics.py`
- Target: Recall@5 > 80%
- Run as part of CI pipeline

**Dependencies:** STORY-CR-007, STORY-CR-020
**Points:** 3

---

### STORY-CR-009: Response Quality Metrics
**As a** developer
**I want** automated response quality checking
**So that** I can ensure responses meet format requirements

**Acceptance Criteria:**
- [ ] Given response, when checking for required elements, then presence/absence reported
- [ ] Given anomaly response, when checking, then table + commands + correlation present
- [ ] Given any response with commands, when validating, then command validity rate reported
- [ ] Given batch run, when processing golden queries, then quality score reported

**Technical Notes:**
- Create `src/dfir_assistant/evaluation/response_metrics.py`
- Check for: tables (markdown), code blocks, required sections
- Integrate with command validator from EPIC-002

**Dependencies:** STORY-CR-007, EPIC-002
**Points:** 3

---

### STORY-CR-010: Regression Testing Pipeline
**As a** developer
**I want** automated regression testing on model/prompt changes
**So that** quality doesn't silently degrade

**Acceptance Criteria:**
- [ ] Given golden dataset, when running full evaluation, then results saved to file
- [ ] Given new run, when comparing to baseline, then delta reported
- [ ] Given quality drop > 5%, when detected, then pipeline fails
- [ ] Given CI integration, when PR submitted, then regression test runs

**Technical Notes:**
- Create `scripts/run_regression.py`
- Store baseline in `tests/fixtures/baseline_results.json`
- Can run in air-gap CI with mocked Ollama responses

**Dependencies:** STORY-CR-008, STORY-CR-009
**Points:** 2

---

## EPIC-002: Command Validation Safety Layer (8 pts)
**Owner:** Ravi (RAG Developer)
**Sprint:** 1
**Status:** Foundation - Safety critical

---

### STORY-CR-004: Volatility Plugin Registry
**As a** developer
**I want** a complete list of valid Volatility 3 plugins
**So that** I can validate generated commands

**Acceptance Criteria:**
- [ ] Given Volatility 3 documentation, when extracted, then all `windows.*` plugins listed
- [ ] Given each plugin, when documented, then valid syntax pattern included
- [ ] Given registry, when formatted, then machine-readable JSON
- [ ] Given Vol2 commands, when included, then marked with version compatibility

**Technical Notes:**
- Create `config/volatility_plugins.json`
- Format:
  ```json
  {
    "plugins": {
      "windows.pslist": {
        "version": ["vol3"],
        "syntax": "vol -f <memory_dump> windows.pslist [--pid PID]",
        "description": "List processes"
      },
      "pslist": {
        "version": ["vol2"],
        "syntax": "vol.py -f <memory_dump> pslist",
        "description": "List processes (Vol2)"
      }
    }
  }
  ```
- Include both Vol2 and Vol3 for compatibility

**Dependencies:** STORY-000
**Points:** 3

---

### STORY-CR-005: Post-Generation Command Validation
**As a** developer
**I want** all generated commands validated before display
**So that** users never see invalid commands

**Acceptance Criteria:**
- [ ] Given LLM response, when parsing, then all code blocks extracted
- [ ] Given code block, when containing Volatility command, then validated against registry
- [ ] Given valid command, when displayed, then shown with ✅ indicator
- [ ] Given invalid command, when detected, then flagged with ⚠️ and closest match suggested
- [ ] Given validation results, when logged, then command validity rate tracked

**Technical Notes:**
- Create `src/dfir_assistant/validation/command_validator.py`
- Extract commands using regex: `vol\.py|vol -f|volatility`
- Validate plugin name against registry
- Use fuzzy matching for suggestions (Levenshtein distance)

**Dependencies:** STORY-CR-004
**Points:** 3

---

### STORY-CR-006: User Warning Display for Unverified Commands
**As a** user
**I want** clear warnings when commands couldn't be verified
**So that** I know to double-check before running

**Acceptance Criteria:**
- [ ] Given unverified command, when displayed, then ⚠️ icon shown
- [ ] Given warning, when clicked/hovered, then explanation shown: "Command not in verified list"
- [ ] Given unverified command, when similar valid command exists, then suggestion shown
- [ ] Given response with mixed validity, when displayed, then each command marked individually

**Technical Notes:**
- Integrate with Gradio UI (EPIC-103)
- Warning styles defined in `src/dfir_assistant/ui/formatters.py`
- Log unverified commands for registry expansion

**Dependencies:** STORY-CR-005
**Points:** 2

---

# SPRINT 2: DATA INGESTION

## EPIC-100: Data Ingestion Pipeline (21 pts)
**Owner:** Dana (Data Engineer)
**Sprint:** 2
**Status:** Core - Data foundation

---

### STORY-FD-001: PDF to Markdown Extraction
**As a** developer
**I want** to convert PDF books to clean markdown
**So that** content can be chunked and indexed

**Acceptance Criteria:**
- [ ] Given PDF file path, when processing, then markdown file output
- [ ] Given code blocks in PDF, when extracted, then wrapped in ``` markers
- [ ] Given tables in PDF, when extracted, then converted to markdown tables
- [ ] Given batch of PDFs, when processing, then progress reported and errors logged
- [ ] Given extraction, when complete, then source metadata preserved (filename, page numbers)

**Technical Notes:**
- Use marker-pdf with fallback to PyMuPDF where needed
- Create `src/dfir_assistant/ingestion/pdf_extractor.py`
- Output to `data/extracted/{book_name}/`
- Handle 10-100MB files efficiently

**Dependencies:** STORY-CR-017, STORY-CR-018
**Points:** 5

---

### STORY-FD-002: Hierarchical Chunking
**As a** developer
**I want** semantic-aware chunking that respects content boundaries
**So that** chunks are coherent and useful for retrieval

**Acceptance Criteria:**
- [ ] Given markdown content, when chunking, then target 512 tokens with 100 overlap
- [ ] Given H2/H3 headers, when encountered, then used as chunk boundaries
- [ ] Given code block, when encountered, then NEVER split mid-block
- [ ] Given table, when encountered, then kept intact in single chunk
- [ ] Given command sequence, when encountered, then kept intact

**Technical Notes:**
- Create `src/dfir_assistant/ingestion/chunker.py`
- Use separators from architecture: `["\n## ", "\n### ", "\n```", "\n\n", "\n", " "]`
- Preserve section context in chunk metadata

**Dependencies:** STORY-FD-001
**Points:** 5

---

### STORY-FD-003: Contextual Retrieval Prepending
**As a** developer
**I want** source context prepended to each chunk
**So that** embeddings capture document context

**Acceptance Criteria:**
- [ ] Given chunk, when prepending context, then format matches spec
- [ ] Given context, when added, then includes: source, chapter, section
- [ ] Given prepended chunk, when embedded, then embedding quality maintained
- [ ] Given original vs prepended, when compared, then retrieval improvement measurable

**Technical Notes:**
- Format per architecture:
  ```
  Source: [Book Title]
  Chapter: [Chapter Name]
  Section: [Section Name]
  ---
  [Chunk content]
  ```
- Create `src/dfir_assistant/ingestion/preprocessor.py`
- Based on Anthropic Contextual Retrieval technique

**Dependencies:** STORY-FD-002
**Points:** 3

---

### STORY-FD-004: Embedding Generation
**As a** developer
**I want** embeddings generated for all chunks
**So that** vector search is possible

**Acceptance Criteria:**
- [ ] Given chunk text, when embedding, then 768-dim vector returned
- [ ] Given batch of chunks, when processing, then embeddings generated in batches
- [ ] Given nomic-embed-text, when used via Ollama, then <500ms per embedding
- [ ] Given large corpus, when processing, then progress logged and checkpointing works

**Technical Notes:**
- Create `src/dfir_assistant/retrieval/embedder.py`
- Use Ollama API: `POST /api/embeddings`
- Batch size: 32 chunks per request
- Save embeddings to disk for restart recovery

**Dependencies:** STORY-FD-003
**Points:** 3

---

### STORY-FD-005: Qdrant Index Building
**As a** developer
**I want** all chunks indexed in Qdrant
**So that** vector search works at scale

**Acceptance Criteria:**
- [ ] Given collection schema from CR-020, when upserting chunks, then all metadata preserved
- [ ] Given 50K chunks, when indexed, then completes in <1 hour
- [ ] Given indexed collection, when searching, then <200ms response
- [ ] Given re-ingestion, when running, then duplicates detected and handled

**Technical Notes:**
- Use batch upsert (100 points per batch)
- Create unique chunk IDs: `{book_name}_{chapter}_{chunk_index}`
- Verify index health after ingestion
- Create `scripts/ingest.py` CLI

**Dependencies:** STORY-FD-004, STORY-CR-020
**Points:** 5

---

# SPRINT 3: RETRIEVAL SYSTEM

## EPIC-101: RAG Pipeline (13 pts)
**Owner:** Ravi (RAG Developer)
**Sprint:** 3
**Status:** Core - Search functionality

---

### STORY-FD-010: Query Embedding Generation
**As a** developer
**I want** user queries embedded using same model
**So that** semantic similarity works correctly

**Acceptance Criteria:**
- [ ] Given user query, when embedding, then same nomic-embed-text used
- [ ] Given embedding, when generated, then <500ms latency
- [ ] Given query, when preprocessed, then same normalization as chunks

**Technical Notes:**
- Reuse `src/dfir_assistant/retrieval/embedder.py`
- Ensure consistent preprocessing (lowercasing, etc.)
- Cache recent query embeddings (LRU cache)

**Dependencies:** STORY-FD-004
**Points:** 2

---

### STORY-FD-011: Hybrid Search Implementation
**As a** developer
**I want** hybrid search combining vector and BM25
**So that** both semantic and keyword matches work

**Acceptance Criteria:**
- [ ] Given query, when searching, then both dense and sparse scores computed
- [ ] Given search weights, when applying, then results combined correctly
- [ ] Given query with command keywords, when detected, then sparse weight increased (0.7)
- [ ] Given conceptual query, when detected, then balanced weights (0.5/0.5)
- [ ] Given top-K=15, when returning, then 15 candidates ready for reranking

**Technical Notes:**
- Create `src/dfir_assistant/retrieval/hybrid_search.py`
- Create `src/dfir_assistant/retrieval/query_analyzer.py` for weight selection
- Qdrant sparse vectors or external BM25 index
- Adaptive weights from architecture decision

**Dependencies:** STORY-FD-010, STORY-FD-005
**Points:** 5

---

### STORY-FD-012: Result Reranking
**As a** developer
**I want** cross-encoder reranking of search results
**So that** top-5 results are highest quality

**Acceptance Criteria:**
- [ ] Given 15 candidates, when reranking, then top-5 selected
- [ ] Given reranker, when optional, then can be disabled via config
- [ ] Given reranking, when applied, then relevance improvement measurable
- [ ] Given latency budget, when reranking, then <500ms total

**Technical Notes:**
- Optional BGE-reranker-base (can disable for speed)
- Create `src/dfir_assistant/retrieval/reranker.py`
- Fall back to vector similarity if reranker unavailable

**Dependencies:** STORY-FD-011
**Points:** 3

---

### STORY-FD-013: Context Building for LLM
**As a** developer
**I want** retrieved chunks assembled into LLM context
**So that** generation has all needed information

**Acceptance Criteria:**
- [ ] Given top-5 chunks, when building context, then concatenated with separators
- [ ] Given context length, when exceeding budget, then lowest-ranked chunks trimmed
- [ ] Given source metadata, when building, then citations prepared
- [ ] Given context, when formatted, then matches prompt template expectations

**Technical Notes:**
- Create `src/dfir_assistant/retrieval/context_builder.py`
- Context budget: 4K tokens (leaving room for query + response)
- Format with chunk boundaries: `--- Source: [title] ---`

**Dependencies:** STORY-FD-012
**Points:** 3

---

## EPIC-005: Retrieval Failure Handling (8 pts)
**Owner:** Ravi (RAG Developer)
**Sprint:** 3
**Status:** Core - Trust layer

---

### STORY-CR-014: Retrieval Confidence Scoring
**As a** developer
**I want** confidence scores for retrieval results
**So that** I can flag low-confidence responses

**Acceptance Criteria:**
- [ ] Given search results, when scoring, then confidence 0.0-1.0 computed
- [ ] Given top-K similarity scores, when averaging, then retrieval confidence derived
- [ ] Given confidence < 0.5, when detected, then marked as LOW
- [ ] Given confidence 0.5-0.7, when detected, then marked as MEDIUM
- [ ] Given confidence > 0.7, when detected, then marked as HIGH

**Technical Notes:**
- Create `src/dfir_assistant/validation/confidence_scorer.py`
- Confidence formula: `avg(top_5_scores) * coverage_factor`
- Coverage factor: how many chunks from different sources

**Dependencies:** STORY-FD-011
**Points:** 3

---

### STORY-CR-015: "I Don't Know" Response Generation
**As a** developer
**I want** the system to admit uncertainty
**So that** users trust accurate responses more

**Acceptance Criteria:**
- [ ] Given confidence < 0.5, when generating, then "I don't have specific information" response
- [ ] Given no relevant chunks, when detected, then suggest related topics
- [ ] Given low confidence response, when displayed, then ❓ indicator shown
- [ ] Given admission, when delivered, then NEVER hallucinate an answer instead

**Technical Notes:**
- Trust > Utility > Experience priority
- Create response templates in `src/dfir_assistant/generation/prompts.py`
- Log low-confidence queries for corpus improvement

**Dependencies:** STORY-CR-014
**Points:** 3

---

### STORY-CR-016: Poor Retrieval Logging
**As a** developer
**I want** queries with poor retrieval logged
**So that** I can identify corpus gaps

**Acceptance Criteria:**
- [ ] Given query with confidence < 0.5, when logged, then query + scores saved
- [ ] Given log file, when reviewed weekly, then corpus gaps identified
- [ ] Given identified gaps, when addressed, then content additions prioritized
- [ ] Given log aggregation, when running, then common failure patterns surfaced

**Technical Notes:**
- Log to `logs/poor_retrieval.jsonl`
- Include: timestamp, query, confidence, top_chunk_scores
- Weekly review process documented in admin guide

**Dependencies:** STORY-CR-014
**Points:** 2

---

# SPRINT 4: RESPONSE GENERATION

## EPIC-102: Response Generation (24 pts)
**Owner:** Ravi (RAG Developer)
**Sprint:** 4
**Status:** Core - LLM integration

---

### STORY-FD-020: Ollama Client Implementation
**As a** developer
**I want** a robust Ollama HTTP client
**So that** LLM inference is reliable

**Acceptance Criteria:**
- [ ] Given Ollama URL, when connecting, then health check succeeds
- [ ] Given prompt, when generating, then streaming response returned
- [ ] Given connection failure, when detected, then retry with backoff
- [ ] Given temperature setting, when configured, then applied to generation
- [ ] Given model name, when configurable, then supports fallback chain

**Technical Notes:**
- Create `src/dfir_assistant/generation/ollama_client.py`
- Use httpx for async HTTP
- Streaming via Server-Sent Events
- Retry: 3 attempts with exponential backoff

**Dependencies:** STORY-CR-001 (VRAM validation passed)
**Points:** 3

---

### STORY-FD-021: Instructor Integration
**As a** developer
**I want** Instructor library for structured output
**So that** responses match Pydantic models

**Acceptance Criteria:**
- [ ] Given Ollama client, when wrapped with Instructor, then Pydantic validation works
- [ ] Given response model, when generating, then output matches schema
- [ ] Given validation failure, when detected, then retry with error feedback
- [ ] Given complex nested model, when used, then all fields populated correctly

**Technical Notes:**
- Create `src/dfir_assistant/generation/instructor_adapter.py`
- Use instructor's `patch` or custom Ollama adapter
- May need custom implementation if standard adapter doesn't support Ollama
- Test early - this is identified risk from architecture

**Dependencies:** STORY-FD-020
**Points:** 5

---

### STORY-FD-022: Query Intent Classification
**As a** developer
**I want** user queries classified by intent
**So that** appropriate response templates are selected

**Acceptance Criteria:**
- [ ] Given query, when classifying, then one of: concept, anomaly, procedure, tool_command
- [ ] Given classification, when determined, then appropriate Pydantic model selected
- [ ] Given ambiguous query, when detected, then default to concept response
- [ ] Given entity extraction, when running, then key entities identified (process names, commands)

**Technical Notes:**
- Create `src/dfir_assistant/generation/intent_classifier.py`
- Use keyword matching + simple rules (LLM classification optional)
- Anomaly triggers: "found", "suspicious", "weird", anomaly terms
- Command triggers: Volatility command names

**Dependencies:** STORY-FD-021
**Points:** 5

---

### STORY-FD-023: AnomalyResponse Template
**As a** developer
**I want** structured anomaly explanation responses
**So that** users get consistent, complete guidance

**Acceptance Criteria:**
- [ ] Given anomaly query, when generating, then all fields populated:
  - title, technical_explanation
  - legitimate_scenarios (list), malicious_scenarios (list)
  - triage_steps (numbered with commands)
  - correlation_guidance (list)
  - quick_classification (decision tree)
- [ ] Given triage_steps, when containing commands, then validated
- [ ] Given Legitimate vs Malicious, when formatted, then markdown table output

**Technical Notes:**
- Create `src/dfir_assistant/generation/models.py` with AnomalyResponse
- Template in `src/dfir_assistant/generation/prompts.py`
- Include example in prompt for few-shot learning

**Dependencies:** STORY-FD-022
**Points:** 5

---

### STORY-FD-024: ConceptResponse Template
**As a** developer
**I want** structured concept explanation responses
**So that** educational content is consistent

**Acceptance Criteria:**
- [ ] Given concept query, when generating, then fields populated:
  - concept_name, technical_explanation
  - windows_implementation (how Windows does it)
  - attacker_abuse (how attackers exploit it)
  - key_artifacts (table: artifact, location, significance)
  - related_commands (validated Volatility commands)
- [ ] Given key_artifacts, when formatted, then markdown table output

**Technical Notes:**
- Create ConceptResponse model in models.py
- Focus on educational value (teaching junior analysts)
- Include Windows Internals references where applicable

**Dependencies:** STORY-FD-022
**Points:** 3

---

### STORY-FD-025: ProcedureResponse Template
**As a** developer
**I want** structured procedural guidance responses
**So that** step-by-step instructions are clear

**Acceptance Criteria:**
- [ ] Given procedure query, when generating, then fields populated:
  - procedure_name, overview
  - prerequisites (what's needed before starting)
  - steps (numbered list with commands and explanations)
  - expected_outputs (what to look for)
  - next_steps_by_finding (if X then Y decision tree)
- [ ] Given each step, when containing command, then validated
- [ ] Given procedure, when formatted, then numbered list with code blocks

**Technical Notes:**
- Create ProcedureResponse model in models.py
- Each step: number, description, command (optional), expected_output
- Include common pitfalls section

**Dependencies:** STORY-FD-022
**Points:** 3

---

## EPIC-004: Organization Context Maintenance (5 pts)
**Owner:** Ravi + Product Owner
**Sprint:** 4
**Status:** Enhancement - Personalization

---

### STORY-CR-011: Org Context Ownership Assignment
**As a** team lead
**I want** ownership assigned to each org context document
**So that** context stays current

**Acceptance Criteria:**
- [ ] Given org context YAML, when structured, then includes owner field
- [ ] Given owner field, when documented, then review cadence defined
- [ ] Given review cadence, when approaching, then reminder logged
- [ ] Given all org docs, when listed, then owners visible in dashboard

**Technical Notes:**
- Template in `config/org_context/template.yaml`:
  ```yaml
  metadata:
    owner: "team_lead@company.com"
    last_updated: "2026-01-15"
    review_cadence_days: 30
  ```
- Create admin script to check stale docs

**Dependencies:** STORY-000
**Points:** 2

---

### STORY-CR-012: Context Freshness Display
**As a** user
**I want** to see when org context was last verified
**So that** I know if guidance might be stale

**Acceptance Criteria:**
- [ ] Given response using org context, when displayed, then last_updated shown
- [ ] Given last_updated > 30 days, when detected, then ⚠️ warning shown
- [ ] Given stale context, when displayed, then "This guidance may be outdated" message

**Technical Notes:**
- Pass metadata through response pipeline
- Display in Gradio UI near response
- Threshold configurable in settings

**Dependencies:** STORY-CR-011, EPIC-103 started
**Points:** 2

---

### STORY-CR-013: User Feedback for Stale Context
**As a** user
**I want** to flag when org context seems wrong
**So that** the team can update it

**Acceptance Criteria:**
- [ ] Given response, when "Report outdated info" clicked, then feedback captured
- [ ] Given feedback, when submitted, then logged with query + response + user note
- [ ] Given logged feedback, when reviewed, then actionable queue created
- [ ] Given review queue, when processed, then org docs updated

**Technical Notes:**
- Add feedback button to UI (EPIC-103)
- Log to `logs/feedback.jsonl`
- Weekly review process in admin guide

**Dependencies:** STORY-CR-012, EPIC-103
**Points:** 1

---

# SPRINT 5: USER INTERFACE

## EPIC-103: User Interface (11 pts)
**Owner:** Ravi (RAG Developer)
**Sprint:** 5
**Status:** Enhancement - Presentation layer

---

### STORY-FD-030: Gradio Chat Interface
**As a** user
**I want** a chat interface to interact with the assistant
**So that** I can ask questions naturally

**Acceptance Criteria:**
- [ ] Given Gradio app, when launched, then chat interface displayed
- [ ] Given user message, when submitted, then response generated and displayed
- [ ] Given conversation, when continuing, then history maintained
- [ ] Given clear button, when clicked, then conversation reset
- [ ] Given multiple users, when connecting, then sessions isolated

**Technical Notes:**
- Create `src/dfir_assistant/ui/gradio_app.py`
- Use Gradio ChatInterface component
- Session state via Gradio State
- Launch on configurable port (default 7860)

**Dependencies:** EPIC-102 complete
**Points:** 3

---

### STORY-FD-031: Streaming Response Display
**As a** user
**I want** responses to stream token-by-token
**So that** I see progress during generation

**Acceptance Criteria:**
- [ ] Given generation starting, when tokens arrive, then displayed incrementally
- [ ] Given streaming, when displayed, then smooth visual experience
- [ ] Given stop button, when clicked, then generation halted
- [ ] Given complete response, when finished, then final formatting applied

**Technical Notes:**
- Create `src/dfir_assistant/pipeline/streaming.py`
- Use Gradio's streaming callback
- Apply markdown formatting after streaming complete

**Dependencies:** STORY-FD-030
**Points:** 3

---

### STORY-FD-032: Source Citation Display
**As a** user
**I want** to see sources for each response
**So that** I can verify information and learn more

**Acceptance Criteria:**
- [ ] Given response with sources, when displayed, then collapsible "Sources" section
- [ ] Given each source, when listed, then shows: book title, chapter, section
- [ ] Given source, when clicked, then chunk text shown
- [ ] Given relevance score, when displayed, then shows how relevant each source was

**Technical Notes:**
- Create `src/dfir_assistant/ui/components.py` for SourcePanel
- Use Gradio Accordion for collapsible section
- Include relevance score as percentage

**Dependencies:** STORY-FD-030
**Points:** 3

---

### STORY-FD-033: Response Feedback Collection
**As a** user
**I want** to provide feedback on responses
**So that** the system can be improved

**Acceptance Criteria:**
- [ ] Given response, when displayed, then thumbs up/down buttons visible
- [ ] Given thumbs down, when clicked, then optional text feedback collected
- [ ] Given "Command worked" checkbox, when checked, then positive signal logged
- [ ] Given all feedback, when logged, then includes query + response + rating + timestamp

**Technical Notes:**
- Create feedback panel in UI
- Log to `logs/feedback.jsonl`
- Aggregate for weekly quality review
- Calculate user satisfaction metric

**Dependencies:** STORY-FD-030
**Points:** 2

---

### STORY-104: Deployment Configuration (NEW)
**As a** system administrator
**I want** systemd service configuration
**So that** the application runs reliably on the server

**Acceptance Criteria:**
- [ ] Given systemd service file, when created, then app starts on boot
- [ ] Given service, when crashed, then automatic restart within 30 seconds
- [ ] Given deployment guide, when written, then step-by-step instructions complete
- [ ] Given server restart, when tested, then all services recover

**Technical Notes:**
- Create `scripts/systemd/dfir-assistant.service`
- Create `scripts/systemd/dfir-assistant.env`
- Write `docs/deployment.md` with full instructions
- Test full restart scenario

**Dependencies:** STORY-FD-030
**Points:** 3

---

# STORY SUMMARY

## All Stories by Sprint

### Sprint 0 (BLOCKING)
| Story ID | Title | Points | Status |
|----------|-------|--------|--------|
| STORY-000 | Project Initialization | 2 | Not Started |
| STORY-CR-001 | VRAM Usage Empirical Validation | 3 | Not Started |
| STORY-CR-002 | Fallback LLM Configuration | 3 | Not Started |
| STORY-CR-003 | VRAM Monitoring Integration | 2 | Not Started |
| **Sprint 0 Total** | | **10** | |

### Sprint 1 (Foundation)
| Story ID | Title | Points | Status |
|----------|-------|--------|--------|
| STORY-CR-017 | marker-pdf Validation | 3 | Not Started |
| STORY-CR-018 | Fallback PDF Extraction | 3 | Not Started |
| STORY-CR-019 | Chunk Quality Validation | 2 | Not Started |
| STORY-CR-020 | Unified Qdrant Collection | 3 | Not Started |
| STORY-CR-021 | Multi-Collection Benchmark | 2 | Conditional |
| STORY-CR-007 | Golden Q&A Test Dataset | 5 | Not Started |
| STORY-CR-008 | Retrieval Quality Metrics | 3 | Not Started |
| STORY-CR-009 | Response Quality Metrics | 3 | Not Started |
| STORY-CR-010 | Regression Testing Pipeline | 2 | Not Started |
| STORY-CR-004 | Volatility Plugin Registry | 3 | Not Started |
| STORY-CR-005 | Post-Generation Command Validation | 3 | Not Started |
| STORY-CR-006 | User Warning Display | 2 | Not Started |
| **Sprint 1 Total** | | **34** | |

### Sprint 2 (Data Ingestion)
| Story ID | Title | Points | Status |
|----------|-------|--------|--------|
| STORY-FD-001 | PDF to Markdown Extraction | 5 | Not Started |
| STORY-FD-002 | Hierarchical Chunking | 5 | Not Started |
| STORY-FD-003 | Contextual Retrieval Prepending | 3 | Not Started |
| STORY-FD-004 | Embedding Generation | 3 | Not Started |
| STORY-FD-005 | Qdrant Index Building | 5 | Not Started |
| **Sprint 2 Total** | | **21** | |

### Sprint 3 (Retrieval)
| Story ID | Title | Points | Status |
|----------|-------|--------|--------|
| STORY-FD-010 | Query Embedding Generation | 2 | Not Started |
| STORY-FD-011 | Hybrid Search Implementation | 5 | Not Started |
| STORY-FD-012 | Result Reranking | 3 | Not Started |
| STORY-FD-013 | Context Building for LLM | 3 | Not Started |
| STORY-CR-014 | Retrieval Confidence Scoring | 3 | Not Started |
| STORY-CR-015 | "I Don't Know" Response | 3 | Not Started |
| STORY-CR-016 | Poor Retrieval Logging | 2 | Not Started |
| **Sprint 3 Total** | | **21** | |

### Sprint 4 (Generation)
| Story ID | Title | Points | Status |
|----------|-------|--------|--------|
| STORY-FD-020 | Ollama Client Implementation | 3 | Not Started |
| STORY-FD-021 | Instructor Integration | 5 | Not Started |
| STORY-FD-022 | Query Intent Classification | 5 | Not Started |
| STORY-FD-023 | AnomalyResponse Template | 5 | Not Started |
| STORY-FD-024 | ConceptResponse Template | 3 | Not Started |
| STORY-FD-025 | ProcedureResponse Template | 3 | Not Started |
| STORY-CR-011 | Org Context Ownership | 2 | Not Started |
| STORY-CR-012 | Context Freshness Display | 2 | Not Started |
| STORY-CR-013 | User Feedback for Stale Context | 1 | Not Started |
| **Sprint 4 Total** | | **29** | |

### Sprint 5 (UI)
| Story ID | Title | Points | Status |
|----------|-------|--------|--------|
| STORY-FD-030 | Gradio Chat Interface | 3 | Not Started |
| STORY-FD-031 | Streaming Response Display | 3 | Not Started |
| STORY-FD-032 | Source Citation Display | 3 | Not Started |
| STORY-FD-033 | Response Feedback Collection | 2 | Not Started |
| STORY-104 | Deployment Configuration | 3 | Not Started |
| **Sprint 5 Total** | | **14** | |

---

## Grand Total

| Metric | Value |
|--------|-------|
| **Total Stories** | 39 |
| **Total Points** | 129 |
| **Sprints** | 6 (including Sprint 0) |
| **Avg Points/Sprint** | ~21.5 |
| **Estimated Duration** | 12 weeks |

---

*Stories document completed. All 39 stories have detailed acceptance criteria, technical notes, and dependencies defined.*
