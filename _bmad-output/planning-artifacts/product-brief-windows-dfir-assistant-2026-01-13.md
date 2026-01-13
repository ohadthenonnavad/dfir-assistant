---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: 
  - windows-internals-dfir-prd-v2.0.md
date: 2026-01-13
author: Ohad
status: complete
---

# Product Brief: Windows Internals DFIR Knowledge Assistant

## Executive Summary

The **Windows Internals DFIR Knowledge Assistant** is an AI-powered Senior DFIR Analyst designed to accelerate learning and investigation efficiency for junior Digital Forensics and Incident Response analysts. By combining expert knowledge from authoritative sources (Windows Internals, Art of Memory Forensics) with modern RAG technology, it delivers structured, educational guidance with exact Volatility 3 commands and correlation recommendations.

This air-gapped solution runs entirely locally on a single RTX 4090 workstation, ensuring complete data sovereignty for sensitive forensic investigations while providing expert-level guidance that would typically require senior analyst intervention.

**Key Value Proposition:** Transform junior DFIR analysts into effective investigators faster, reduce senior analyst interruptions, and ensure consistent, high-quality investigation guidance.

---

## Core Vision

### Problem Statement

Junior DFIR analysts (0-2 years experience) investigating Windows security incidents currently face significant barriers to effective investigation:

1. **Knowledge Fragmentation** - Must search through multiple 1000+ page technical books (Windows Internals, Art of Memory Forensics) to understand findings
2. **Senior Dependency** - Constantly interrupting senior analysts for guidance, pulling them away from complex investigations
3. **Tool Learning Curve** - Learning Volatility 3 commands through trial and error, wasting time and potentially corrupting evidence
4. **Contextual Understanding Gap** - Need to understand the "why" behind anomalies, not just the "what"

### Problem Impact

| Impact Area | Current State |
|-------------|---------------|
| **Investigation Time** | Hours spent searching documentation per finding |
| **Senior Analyst Time** | 20-40% of senior time spent answering basic questions |
| **Error Rate** | Wrong Volatility commands waste time or corrupt evidence |
| **Learning Speed** | Months to develop pattern recognition skills |
| **Consistency** | Investigation quality varies by analyst availability |

### Why Existing Solutions Fall Short

| Solution | Limitation |
|----------|------------|
| **ChatGPT/Cloud AI** | Cannot be used in air-gapped forensic environments; data sovereignty concerns |
| **Documentation** | Static, not contextual to specific findings; doesn't provide correlation guidance |
| **Senior Analyst Help** | Not scalable; inconsistent availability; pulls from complex work |
| **Training Programs** | Slow; theory-heavy; not available at moment of investigation |
| **Generic Search** | Returns noise; doesn't understand DFIR context; no structured responses |

### Proposed Solution

An AI assistant that acts as a **virtual Senior DFIR Analyst**, providing:

1. **Contextual Knowledge Q&A** - Answers about Windows internals, memory forensics, attack techniques, and tool usage with source citations
2. **Anomaly Explanation** - Structured analysis of suspicious findings with Legitimate vs Malicious comparison tables
3. **Procedural Guidance** - Step-by-step investigation procedures with exact, validated Volatility 3 commands
4. **Organization-Aware Responses** - Incorporates team SOPs, tools, and escalation procedures
5. **Multi-Turn Conversations** - Maintains investigation context across conversation turns

**Technical Implementation:**
- RAG pipeline with Contextual Retrieval and Instructor for structured outputs
- Qwen2.5 32B Instruct (quantized) running on Ollama
- Qdrant vector database with ~50K chunks from 30 DFIR books
- 100% local deployment - no cloud dependencies

### Key Differentiators

| Differentiator | Why It Matters |
|----------------|----------------|
| **Air-Gap Ready** | Works in classified/sensitive forensic environments |
| **Command Validation** | All Volatility commands verified against plugin list - no hallucination |
| **Structured Output** | Guaranteed response format with tables, commands, correlation steps |
| **Source Citations** | Every response traceable to authoritative sources |
| **Teaching-Oriented** | Explains "why" not just "what" - builds analyst skills |
| **Organization Context** | Adapts to team tools, SOPs, and workflows |

---

## Target Users

### Primary Users

#### 🎯 Junior DFIR Analyst ("Alex")
**Background:** 0-2 years experience, recently completed SANS FOR508 or equivalent, eager to learn

**Context:**
- Works on Windows-focused incidents under senior supervision
- Comfortable with basic Volatility usage but doesn't know all plugins
- Can identify obvious anomalies but struggles with edge cases
- Has the technical books but finds them overwhelming to navigate

**Pain Points:**
- "I found something suspicious but don't know what it means"
- "What Volatility command do I use for this?"
- "Is this normal or malicious?"
- "What should I check next?"

**Success Vision:**
- Confidently explains findings in reports
- Uses correct Volatility commands on first try
- Knows when to escalate vs. continue investigating
- Reduces time-to-first-finding by 30%

### Secondary Users

#### 👨‍💼 Senior DFIR Analyst (Reviewer)
**Role:** Reviews junior analyst work, provides oversight

**Needs:**
- Confidence that AI guidance is accurate
- Ability to override or correct AI responses
- Audit trail of what guidance was given
- Time savings from fewer basic questions

#### 🔍 SOC Triage Analyst
**Role:** Escalates potential incidents to DFIR team

**Needs:**
- Quick anomaly explanations during triage
- Help deciding when to escalate
- Basic memory forensics understanding

### User Journey

```
Discovery → Onboarding → Core Usage → Value Realization → Mastery
```

1. **Discovery:** Junior analyst encounters unfamiliar finding in investigation
2. **Onboarding:** Opens local web interface, describes finding in natural language
3. **Core Usage:** Receives structured explanation with commands and next steps
4. **Value Realization:** Commands work, finding makes sense, investigation progresses
5. **Mastery:** Over time, builds pattern recognition; needs assistant less for basic queries

---

## Success Metrics

### User Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Time-to-First-Finding** | 30% reduction | A/B comparison with control group |
| **Correct Command Usage** | >90% first-try success | Post-response "command worked" feedback |
| **User Satisfaction** | >4.0/5.0 | Post-response helpfulness rating |
| **Senior Interruption Reduction** | 40% fewer basic questions | Senior analyst time tracking |
| **Investigation Confidence** | Qualitative improvement | Monthly survey |

### Business Objectives

| Objective | Timeline | Success Indicator |
|-----------|----------|-------------------|
| **MVP Deployment** | Phase 1-2 | System functional with 2 core books |
| **Team Adoption** | Phase 3 | 80% of junior analysts using regularly |
| **Quality Validation** | Phase 4 | >80% retrieval accuracy on golden dataset |
| **Knowledge Expansion** | Phase 5-6 | All 30 books processed and validated |

### Key Performance Indicators

| KPI | Target | How Measured |
|-----|--------|--------------|
| **Retrieval Accuracy** | >80% Recall@5 | Automated eval against golden dataset |
| **Response Quality** | >90% contain required elements | Human review of sample responses |
| **Command Accuracy** | 100% valid Volatility commands | Automated validation against plugin list |
| **Response Latency** | <10s first token | System monitoring |
| **VRAM Utilization** | <22GB peak | Runtime monitoring |

---

## Scope

### MVP Scope (Phase 1-2)

| Feature | Description |
|---------|-------------|
| ✅ **Core Books** | Windows Internals 7th Ed + Art of Memory Forensics processed |
| ✅ **Basic RAG Q&A** | Natural language questions with structured responses |
| ✅ **Volatility Commands** | Validated V3 commands in code blocks |
| ✅ **Gradio Interface** | Simple chat UI with streaming |
| ✅ **Single User** | Runs on RTX 4090 workstation |

### Full Release Scope (Phase 3-6)

| Feature | Description |
|---------|-------------|
| 📋 **All 30 Books** | Full DFIR library processed |
| 📋 **Organization Context** | Team SOPs and tool configurations |
| 📋 **Response Templates** | Anomaly, Concept, Procedure templates |
| 📋 **Multi-Turn** | Conversation context tracking |
| 📋 **User Feedback** | Thumbs up/down, command validation |
| 📋 **Evaluation Suite** | Automated quality regression testing |

### Out of Scope

| Excluded | Rationale |
|----------|-----------|
| ❌ Automated analysis | Not running Volatility on dumps automatically |
| ❌ Live system analysis | No endpoint connection |
| ❌ Malware classification | Not a malware detector |
| ❌ Threat hunting | Reactive guidance, not proactive hunting |
| ❌ Multi-language | English only |
| ❌ Cloud deployment | Air-gapped only |
| ❌ Mobile forensics | Windows memory only |
| ❌ Report generation | Guidance only, not full reports |

---

## Technical Constraints

| Constraint | Impact |
|------------|--------|
| **Air-Gap Deployment** | All models must run locally; no cloud APIs |
| **24GB VRAM Limit** | Constrains model size to ~32B quantized |
| **Single GPU** | No model parallelism; sequential inference |
| **PDF Complexity** | Complex layouts require quality extraction validation |

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| **VRAM Fragility** | 🔴 Critical | Empirical validation + 14B fallback ready |
| **Command Hallucination** | 🔴 Critical | Post-generation validation against plugin list |
| **Stale Org Context** | 🟡 High | Ownership + review cadence + freshness warnings |
| **Poor Retrieval** | 🟡 High | Confidence scoring + "I don't know" responses |
| **PDF Extraction Quality** | 🟡 High | Manual chunk validation + fallback extractors |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| PRD v2.0 | Full requirements with epics and stories |
| Implementation Architecture | Technical design |
| Critical Review Report | Risk analysis and mitigations |
| Research Scout Report | Technology recommendations |

---

*Product Brief generated from PRD v2.0*
*Project: Windows Internals DFIR Knowledge Assistant*
*Author: Ohad | Date: 2026-01-13*
