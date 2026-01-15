# Product Requirements Document (PRD)
# Windows Internals DFIR Knowledge Assistant

**Document Version:** 2.0
**Created By:** Omeriko ⚔️ (Cyber AI Systems Architect)
**Date:** 2026-01-13
**Status:** Updated with Critical Review & Research Scout Recommendations

---

## 1. Project Overview

### 1.1 Project Name
**Windows Internals DFIR Knowledge Assistant**

### 1.2 Problem Statement
Junior DFIR (Digital Forensics and Incident Response) researchers need expert-level guidance when investigating Windows-based security incidents. Currently, they must:
- Search through multiple heavy technical books (Windows Internals, Art of Memory Forensics)
- Ask senior analysts for help (pulls seniors away from complex work)
- Learn Volatility commands through trial and error
- Understand the "why" behind anomalies, not just the "what"

We need an AI-powered Senior DFIR Analyst that can teach while it guides, providing structured, expert-level responses with exact commands and correlation guidance.

### 1.3 Target Users
| User Type | Description | Primary Needs |
|-----------|-------------|---------------|
| **Junior DFIR Analysts** | 0-2 years experience, learning investigation techniques | Explanations, exact commands, step-by-step guidance |
| **Senior Analysts** | 5+ years, will review system outputs | Confidence in accuracy, ability to override |
| **SOC Team** | Triage analysts escalating to DFIR | Quick anomaly explanations during triage |

### 1.4 Success Metrics
| Metric | Target | How Measured |
|--------|--------|--------------|
| **Retrieval Accuracy** | >80% Recall@5 on test queries | Automated eval against golden dataset |
| **Response Quality** | >90% contain required elements (tables, commands, correlation) | Human review of sample responses |
| **Command Accuracy** | 100% valid Volatility commands | Automated validation against plugin list |
| **User Satisfaction** | >4.0/5.0 helpfulness rating | Post-response feedback collection |
| **Time Savings** | 30% reduction in time-to-first-finding | A/B comparison with control group |

---

## 2. Functional Requirements

### 2.1 Core Features

#### FR-001: Knowledge Q&A
**Priority:** P0 (Must Have)

The system must answer questions about:
- Windows internals concepts (processes, threads, memory, registry)
- Memory forensics techniques (VAD analysis, injection detection)
- Forensic artifacts (locations, significance, analysis methods)
- Attack techniques (rootkits, persistence mechanisms)
- Tool usage (Volatility 3 commands and output interpretation)

**Acceptance Criteria:**
- [ ] Responds to natural language questions
- [ ] Retrieves relevant chunks from knowledge base
- [ ] Generates structured, educational responses
- [ ] Cites source material when available

#### FR-002: Anomaly Explanation
**Priority:** P0 (Must Have)

When user reports finding an anomaly, the system must:
1. Explain what the anomaly means technically
2. Provide Legitimate vs Malicious comparison table
3. Give specific triage commands (Volatility 3)
4. Suggest correlation steps
5. Provide quick classification framework

**Acceptance Criteria:**
- [ ] Recognizes anomaly description patterns
- [ ] Generates structured anomaly response template
- [ ] Includes exact, validated Volatility commands
- [ ] Provides decision tree for severity classification

#### FR-003: Procedural Guidance
**Priority:** P0 (Must Have)

The system must provide step-by-step procedures for:
- Memory forensics investigations
- Registry analysis
- Process analysis
- Persistence mechanism detection
- IOC extraction

**Acceptance Criteria:**
- [ ] Numbered steps with exact commands
- [ ] Explanation of what each step accomplishes
- [ ] Expected output interpretation
- [ ] Next steps based on findings

#### FR-004: Organization-Aware Responses
**Priority:** P1 (Should Have)

The system must incorporate organization-specific context:
- Team's tools and versions (Volatility 3, internal tools)
- SOPs and investigation workflows
- Escalation procedures
- Common findings in their environment

**Acceptance Criteria:**
- [ ] Responses reference org-specific tools
- [ ] Includes escalation triggers (e.g., "escalate to senior if rootkit")
- [ ] Follows org investigation workflow
- [ ] Uses internal tool names and syntax

#### FR-005: Multi-Turn Conversations
**Priority:** P1 (Should Have)

The system must maintain context across conversation turns:
- Follow-up questions reference previous context
- Investigation session state (what's been analyzed)
- Clarification without repeating information

**Acceptance Criteria:**
- [ ] Understands "what about X?" follow-ups
- [ ] Tracks what's already been covered
- [ ] Summarizes current investigation state on request

### 2.2 Data Requirements

#### DR-001: Knowledge Base Sources
| Source Type | Examples | Priority |
|-------------|----------|----------|
| **Technical Books** | Windows Internals 7th Ed, Art of Memory Forensics | P0 |
| **Tool Documentation** | Volatility 3 plugin reference | P0 |
| **Organization Docs** | SOPs, playbooks, tool guides | P1 |
| **Threat Intelligence** | MITRE ATT&CK Windows techniques | P1 |

#### DR-002: Data Format Requirements
- PDF books (10-100MB each, complex layouts)
- Markdown documentation
- YAML/JSON configuration files
- Text-based command references

### 2.3 Integration Points

#### INT-001: Ollama/LLM Serving
- **Interface:** HTTP API
- **Model:** Qwen2.5 32B (quantized)
- **Protocol:** Ollama-compatible API

#### INT-002: Vector Database
- **Interface:** REST API / Python client
- **Database:** Qdrant
- **Operations:** Index, search, filter

#### INT-003: User Interface
- **Framework:** Gradio
- **Features:** Chat interface, file upload (for context)
- **Deployment:** Local web server

### 2.4 Output Requirements

All responses must include (as applicable):

| Element | When Required | Format |
|---------|---------------|--------|
| Technical Explanation | Always | Markdown paragraphs |
| Legitimate vs Malicious Table | Anomaly queries | Markdown table |
| Triage Commands | Investigation queries | Code blocks with exact syntax |
| Correlation Guidance | Anomaly/procedure queries | Numbered list |
| Quick Classification | Anomaly queries | IF/THEN decision tree |
| Source Citations | When retrieving from books | Book name + chapter |

---

## 3. Non-Functional Requirements

### 3.1 Performance

| Metric | Requirement | Notes |
|--------|-------------|-------|
| **Response Latency** | <10 seconds for first token | Qwen2.5 32B Q4 inference |
| **Full Response Time** | <30 seconds typical | Streaming preferred |
| **Embedding Latency** | <500ms per query | nomic-embed-text |
| **Retrieval Latency** | <200ms | Qdrant search |

### 3.2 Security

| Requirement | Details |
|-------------|---------|
| **Air-Gap Deployment** | All components run locally, no internet required |
| **Data Residency** | All data stays on local system |
| **No Telemetry** | No data sent to external services |
| **Audit Logging** | Log queries and responses for review |

### 3.3 Scalability

| Scenario | Requirement |
|----------|-------------|
| **Concurrent Users** | Single user (MVP); plan for 3-5 |
| **Knowledge Base Size** | ~50K chunks from 30 books |
| **Conversation Length** | Support 20+ turn conversations |

### 3.4 Availability

| Requirement | Target |
|-------------|--------|
| **Uptime** | Business hours availability (not 24/7) |
| **Recovery** | Restart within 5 minutes |
| **Data Persistence** | Survive system restart |

---

## 4. AI/ML Specifications (From Omeriko Design)

### 4.1 Model Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     RAG PIPELINE v2.0                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Query → [Embedding] → [Hybrid Search] → [Rerank] →         │
│       → [Context Build] → [LLM + Instructor] → Response     │
│                                                              │
│  Key Enhancements:                                           │
│  ✅ Contextual Retrieval - Source context prepended         │
│  ✅ Instructor - Structured output generation                │
│  ✅ Command Validation - Post-generation safety              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Model Selection

| Component | Model | Rationale |
|-----------|-------|-----------|
| **LLM** | Qwen2.5 32B Instruct Q4 | Best reasoning + structured output at size |
| **Embedding** | nomic-embed-text | 8K context, efficient, good retrieval |
| **Reranker** | BGE-reranker-base (optional) | Cross-encoder for improved ranking |
| **Structured Output** | Instructor library | Pydantic-based output validation |

### 4.3 Sweet Spot Techniques (Research Scout Recommendations)

Based on the Research Scout analysis, these high-value, low-effort techniques are **required for Phase 1**:

#### 4.3.1 Contextual Retrieval (Anthropic)

**What:** Prepend source context to each chunk before embedding.

**Why:** 20-67% improvement in retrieval quality with minimal effort.

**Implementation:**
```
Before embedding:
  "The VAD tree is organized as a balanced binary tree..."

After contextual prepend:
  "Source: The Art of Memory Forensics
   Chapter: Chapter 5 - Windows Memory Forensics
   Section: Virtual Address Descriptors
   ---
   The VAD tree is organized as a balanced binary tree..."
```

**Reference:** [Anthropic Contextual Retrieval Blog](https://www.anthropic.com/news/contextual-retrieval)

#### 4.3.2 Instructor (Structured Output)

**What:** Use Instructor library with Pydantic models to guarantee structured LLM output.

**Why:** Ensures responses match required templates (tables, commands, etc.) without hallucination.

**Implementation:**
```python
from instructor import from_openai
from pydantic import BaseModel

class AnomalyResponse(BaseModel):
    title: str
    technical_explanation: str
    legitimate_scenarios: list[str]
    malicious_scenarios: list[str]
    triage_steps: list[TriageStep]
    correlation_guidance: list[str]

# Guaranteed to return valid AnomalyResponse
response = client.chat.completions.create(
    model="qwen2.5:32b",
    response_model=AnomalyResponse,
    messages=[...]
)
```

**Reference:** [Instructor GitHub](https://github.com/jxnl/instructor)

### 4.4 Training Requirements

**No training required for MVP** - using pre-trained models with RAG.

Future consideration: QLoRA fine-tuning for domain adaptation (see Research Scout report).

### 4.5 Inference Requirements

| Resource | Requirement |
|----------|-------------|
| **GPU** | RTX 4090 (24GB VRAM) |
| **VRAM Usage** | ~20GB (18GB LLM + 2GB embedding/overhead) |
| **System RAM** | 32GB minimum |
| **Storage** | 50GB for models, 10GB for index |

### 4.6 RAG/Knowledge Base Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Vector DB** | Qdrant (single collection) | Metadata filtering for source types |
| **Chunk Size** | 800-1200 tokens | Hierarchical by section |
| **Overlap** | 100-200 tokens | Preserve continuity |
| **Embedding Dim** | 768 | nomic-embed-text |
| **Search Top-K** | 10-15 before rerank | 5 final context chunks |
| **Contextual Retrieval** | Required | Prepend source metadata |
| **Structured Output** | Required | Via Instructor library |

---

## 5. Constraints & Assumptions

### 5.1 Technical Constraints

| Constraint | Impact |
|------------|--------|
| **Air-Gap Deployment** | All models must run locally; no cloud services |
| **24GB VRAM Limit** | Limits model size to ~32B quantized |
| **Single GPU** | No model parallelism; batch size limited |
| **PDF Complexity** | Windows Internals has complex layouts, code, tables |

### 5.2 Dependencies

| Dependency | Type | Risk |
|------------|------|------|
| **Ollama** | LLM serving | Low - stable, well-documented |
| **Qdrant** | Vector DB | Low - supports local deployment |
| **marker-pdf** | PDF extraction | Medium - complex PDFs may need tuning |
| **Book PDFs** | Data source | User must provide legally-obtained copies |

### 5.3 Assumptions

1. **User has the books**: System indexes user-provided PDFs; we don't distribute copyrighted content
2. **User knows basic forensics**: Not teaching "what is forensics" - teaching Windows specifics
3. **Single language**: English only for MVP
4. **Volatility 3**: User's team uses Volatility 3 (not 2)
5. **Junior analyst queries**: Not designed for senior-level edge cases

---

## 6. Out of Scope

The following are explicitly **NOT** included in this project:

| Excluded | Reason |
|----------|--------|
| **Automated analysis** | Not running Volatility automatically on dumps |
| **Live system analysis** | Not connecting to live endpoints |
| **Malware classification** | Not a malware classifier/detector |
| **Threat hunting** | Not proactively searching for threats |
| **Multi-language support** | English only |
| **Cloud deployment** | Air-gapped only |
| **Mobile device forensics** | Windows only |
| **Network forensics** | Memory and disk forensics only |
| **Report generation** | Guidance only, not full reports |

---

## 7. User Stories

### US-001: Anomaly Explanation
**As a** junior DFIR analyst  
**I want to** get an explanation of a suspicious finding  
**So that** I understand what it means and how to investigate further

**Example:**
> "I found a VAD with RW protection that has no DLL reference. What does this mean?"

### US-002: Command Lookup
**As a** junior DFIR analyst  
**I want to** know the exact Volatility command for a task  
**So that** I don't waste time searching documentation

**Example:**
> "What Volatility command shows processes with hidden DLLs?"

### US-003: Concept Learning
**As a** junior DFIR analyst  
**I want to** understand a Windows concept deeply  
**So that** I can recognize related issues in future investigations

**Example:**
> "Explain how Windows handles process creation at the kernel level"

### US-004: Investigation Procedure
**As a** junior DFIR analyst  
**I want to** get a step-by-step procedure for an investigation type  
**So that** I don't miss important steps

**Example:**
> "Walk me through memory forensics for credential theft"

---

## 8. Acceptance Criteria Summary

### MVP (Phase 1-2)
- [ ] Process Windows Internals + Art of Memory Forensics PDFs
- [ ] Basic RAG Q&A with structured responses
- [ ] Volatility 3 command accuracy validated
- [ ] Gradio chat interface functional
- [ ] Runs on RTX 4090 within VRAM budget

### Full Release (Phase 3-6)
- [ ] All 30 books processed
- [ ] Organization context integrated
- [ ] Response templates implemented
- [ ] Evaluation dataset validated (>80% retrieval accuracy)
- [ ] Multi-turn conversation support
- [ ] User feedback collection

---

## 9. BMM Epics & Stories (From Critical Review)

The following epics and stories are derived from the Critical Review analysis. They represent risk mitigations and quality gates that MUST be implemented.

### EPIC-001: VRAM Validation & Fallback Planning
**Source:** Critical Review - VRAM fragility risk (🔴 CRITICAL)

**Problem:** The architecture depends on Qwen2.5 32B Q4 fitting in 24GB VRAM alongside embedding model and KV cache. This assumption is unvalidated.

| Story ID | Story | Acceptance Criteria | Owner |
|----------|-------|---------------------|-------|
| CR-001 | As a developer, I need to validate VRAM usage empirically before building features | - Run Qwen2.5 32B Q4 inference with 8K context<br>- Measure with nomic-embed loaded simultaneously<br>- Document actual VRAM under realistic multi-turn | Ravi |
| CR-002 | As a developer, I need a fallback LLM option ready | - Qwen2.5 14B tested as backup<br>- Prompts work with either model<br>- Quality delta quantified | Ravi |
| CR-003 | As a developer, I need VRAM monitoring in the application | - Log VRAM usage per query<br>- Alert when approaching 22GB<br>- Graceful degradation if limit hit | Ravi |

---

### EPIC-002: Command Validation Safety Layer
**Source:** Critical Review - Command hallucination risk (🔴 CRITICAL)

**Problem:** LLMs can generate plausible-looking but invalid Volatility commands. Junior analysts won't know the difference. Wrong commands waste time or corrupt evidence.

| Story ID | Story | Acceptance Criteria | Owner |
|----------|-------|---------------------|-------|
| CR-004 | As a developer, I need a Volatility 3 plugin validation list | - Complete list of valid `windows.*` plugins<br>- Valid command syntax patterns<br>- Machine-readable format JSON | Ravi |
| CR-005 | As a developer, I need post-generation command validation | - Extract all code blocks from responses<br>- Validate against known plugin list<br>- Flag invalid commands with warning | Ravi |
| CR-006 | As a user, I want to see warnings when commands are unverified | - Visual warning indicator<br>- Suggest closest valid command<br>- Log for quality review | Ravi |

---

### EPIC-003: Evaluation Framework
**Source:** Critical Review - No evaluation plan (🔴 CRITICAL)

**Problem:** No concrete plan to prove the system actually helps analysts. "Validate output quality" is too vague.

| Story ID | Story | Acceptance Criteria | Owner |
|----------|-------|---------------------|-------|
| CR-007 | As a developer, I need a golden Q&A test dataset | - 30+ Q&As with expected responses<br>- Covers all query types: concept, anomaly, procedure, tool<br>- Human-reviewed for accuracy | Ravi + Dana |
| CR-008 | As a developer, I need retrieval quality metrics | - Recall@5 measurement<br>- Precision@5 measurement<br>- Target: >80% recall | Dana |
| CR-009 | As a developer, I need response quality metrics | - Check for required elements: tables, commands<br>- Command validity rate<br>- Human evaluation rubric | Ravi |
| CR-010 | As a developer, I need regression testing on model/prompt changes | - Golden set re-run after changes<br>- Automated comparison<br>- Block deploy if quality drops | Ravi |

---

### EPIC-004: Organization Context Maintenance
**Source:** Critical Review - Stale advice risk (🟡 HIGH)

**Problem:** Org context needs constant updates. The system will give confidently wrong advice if context is stale.

| Story ID | Story | Acceptance Criteria | Owner |
|----------|-------|---------------------|-------|
| CR-011 | As a team lead, I need ownership assigned for each org context doc | - Owner field in each YAML file<br>- Review cadence defined<br>- Reminder system | Product Owner |
| CR-012 | As a user, I want to see when org context was last verified | - Display last_updated in responses<br>- Warning if >30 days old<br>- Easy update path | Ravi |
| CR-013 | As a team lead, I need user feedback to flag stale context | - "Was this command correct?" button<br>- Track flagged org context docs<br>- Review queue | Ravi |

---

### EPIC-005: Retrieval Failure Handling
**Source:** Critical Review - Poor user experience (🟡 HIGH)

**Problem:** No handling when retrieved context doesn't contain the answer. Novel questions, typos, and multi-topic queries fail silently.

| Story ID | Story | Acceptance Criteria | Owner |
|----------|-------|---------------------|-------|
| CR-014 | As a developer, I need confidence scoring on retrieval | - Score based on top-K similarity<br>- Thresholds for high/medium/low<br>- API returns confidence level | Ravi |
| CR-015 | As a user, I want the system to admit when it doesn't know | - "I don't have specific information" response<br>- Suggest related topics that ARE covered<br>- Never hallucinate an answer | Ravi |
| CR-016 | As a developer, I need to log queries with poor retrieval | - Log query + retrieval scores<br>- Weekly review for corpus gaps<br>- Prioritized content additions | Ravi + Dana |

---

### EPIC-006: PDF Processing Quality
**Source:** Critical Review - Garbage in, garbage out (🟡 HIGH)

**Problem:** Windows Internals has complex layouts, code blocks, tables. marker-pdf is good but not magic.

| Story ID | Story | Acceptance Criteria | Owner |
|----------|-------|---------------------|-------|
| CR-017 | As a developer, I need to validate marker-pdf on actual books | - Process 3 sample chapters<br>- Compare to original: code blocks, tables, formatting<br>- Document limitations | Dana |
| CR-018 | As a developer, I need fallback extraction methods | - Test alternatives: PyMuPDF, LlamaParse<br>- Hybrid approach if needed<br>- Document which works for which book type | Dana |
| CR-019 | As a developer, I need chunk quality validation | - Spot-check 50 random chunks per book<br>- Check: complete sentences, code intact, no garbage<br>- Quality score > 90% | Dana |

---

### EPIC-007: Single Collection Architecture
**Source:** Critical Review - Complexity vs benefit (🟢 MEDIUM)

**Problem:** Original design had 4 collections. CR recommends starting simple and proving complexity is needed.

| Story ID | Story | Acceptance Criteria | Owner |
|----------|-------|---------------------|-------|
| CR-020 | As a developer, I need a single unified collection with rich metadata | - One Qdrant collection<br>- source_type filtering<br>- All metadata queryable | Ravi |
| CR-021 | As a developer, I need to benchmark multi-collection IF retrieval quality is poor | - Only if single collection < 80% recall<br>- A/B test single vs multi<br>- Document difference | Ravi |

---

## 10. Implementation Epics & Stories (Feature Development)

### EPIC-100: Data Ingestion Pipeline
**Owner:** Dana (Data Engineer)

| Story ID | Story | Acceptance Criteria | Points |
|----------|-------|---------------------|--------|
| FD-001 | As a developer, I need to process PDF books to markdown | - marker-pdf integration<br>- Code blocks preserved<br>- Tables extracted | 5 |
| FD-002 | As a developer, I need hierarchical chunking by section | - 800-1200 token target<br>- 100-200 token overlap<br>- Section boundaries respected | 5 |
| FD-003 | As a developer, I need contextual retrieval prepending | - Source metadata in each chunk<br>- Format per spec<br>- Applied before embedding | 3 |
| FD-004 | As a developer, I need embedding generation | - nomic-embed-text via Ollama<br>- Batch processing<br>- Save to disk | 3 |
| FD-005 | As a developer, I need Qdrant index building | - Single collection schema<br>- All metadata indexed<br>- Verification queries pass | 5 |

---

### EPIC-101: RAG Pipeline
**Owner:** Ravi (RAG Developer)

| Story ID | Story | Acceptance Criteria | Points |
|----------|-------|---------------------|--------|
| FD-010 | As a developer, I need query embedding generation | - nomic-embed-text for queries<br>- <500ms latency<br>- Same model as indexing | 2 |
| FD-011 | As a developer, I need hybrid search vector + BM25 | - Alpha parameter tunable<br>- Metadata filtering<br>- Top-K configurable | 5 |
| FD-012 | As a developer, I need reranking with BGE-reranker | - Cross-encoder reranking<br>- Top 5 from top 15<br>- Optional (can disable) | 3 |
| FD-013 | As a developer, I need context building for LLM | - Concatenate chunks<br>- Respect context window<br>- Include source citations | 3 |

---

### EPIC-102: Response Generation
**Owner:** Ravi (RAG Developer)

| Story ID | Story | Acceptance Criteria | Points |
|----------|-------|---------------------|--------|
| FD-020 | As a developer, I need LLM client with Ollama | - Qwen2.5 32B Q4 integration<br>- Streaming support<br>- Temperature configurable | 3 |
| FD-021 | As a developer, I need Instructor integration | - Pydantic response models<br>- Retry on validation failure<br>- Works with Ollama | 5 |
| FD-022 | As a developer, I need query intent classification | - Detect: concept, anomaly, procedure, tool_command<br>- Select appropriate template<br>- Extract entities | 5 |
| FD-023 | As a developer, I need AnomalyResponse template | - All required fields<br>- Legitimate vs Malicious table<br>- Triage commands | 5 |
| FD-024 | As a developer, I need ConceptResponse template | - Technical explanation<br>- Attacker abuse section<br>- Key artifacts table | 3 |
| FD-025 | As a developer, I need ProcedureResponse template | - Numbered steps<br>- Exact commands<br>- Expected outputs | 3 |

---

### EPIC-103: User Interface
**Owner:** Ravi (RAG Developer)

| Story ID | Story | Acceptance Criteria | Points |
|----------|-------|---------------------|--------|
| FD-030 | As a user, I need a chat interface | - Gradio chat component<br>- Message history<br>- Clear conversation | 3 |
| FD-031 | As a user, I need streaming responses | - Token-by-token display<br>- Smooth UX<br>- Stop generation button | 3 |
| FD-032 | As a user, I need to see source citations | - Collapsible sources<br>- Book + chapter + section<br>- Link to chunk text | 3 |
| FD-033 | As a user, I need response feedback | - Thumbs up/down<br>- "Command worked" checkbox<br>- Free-text feedback | 2 |

---

## 11. Story Point Summary

| Epic | Total Points | Owner |
|------|-------------|-------|
| EPIC-001: VRAM Validation | 8 | Ravi |
| EPIC-002: Command Validation | 8 | Ravi |
| EPIC-003: Evaluation Framework | 13 | Ravi + Dana |
| EPIC-004: Org Context Maintenance | 5 | Ravi + PO |
| EPIC-005: Retrieval Failure Handling | 8 | Ravi |
| EPIC-006: PDF Processing Quality | 8 | Dana |
| EPIC-007: Single Collection | 5 | Ravi |
| **Critical Review Total** | **55** | |
| EPIC-100: Data Ingestion | 21 | Dana |
| EPIC-101: RAG Pipeline | 13 | Ravi |
| EPIC-102: Response Generation | 24 | Ravi |
| EPIC-103: User Interface | 11 | Ravi |
| **Feature Development Total** | **69** | |
| **GRAND TOTAL** | **124** | |

---

## 12. Document Handoff

This PRD v2.0 is ready for implementation.

**Key Updates in v2.0:**
- Added Sweet Spot techniques: Contextual Retrieval, Instructor from Research Scout
- Added BMM Epics & Stories from Critical Review recommendations
- Added Feature Development Epics & Stories
- Story point estimates included

**Next Steps:**
```
@ravi Begin with EPIC-001 (VRAM Validation) before any feature work
@dana Begin with CR-017 (PDF Processing Validation) in parallel
```

**Related Documents:**
| Document | Location |
|----------|----------|
| Implementation Architecture | docs/implementation-architecture.md |
| System Architecture | plans/windows-internals-assistant-architecture.md |
| Critical Review | plans/critical-review-report.md |
| Research Scout | plans/research-scout-report.md |
| Review Summary | plans/review-summary.md |
| Team Workflow | _bmad/agents/TEAM_WORKFLOW.md |
| Eval Generator | src/eval_generator/ |

---

*PRD v2.0 generated by Omeriko ⚔️ - Cyber AI Systems Architect*
*Updated with Critical Review & Research Scout recommendations*
