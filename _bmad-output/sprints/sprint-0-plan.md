# Sprint 0 Plan
# Windows Internals DFIR Knowledge Assistant

---
sprint: 0
name: "VRAM Validation & Project Setup"
status: 'planned'
createdAt: '2026-01-15'
startDate: '2026-01-15'
endDate: '2026-01-29'
sprintLength: '2 weeks'
velocity_target: 10
velocity_actual: null
---

## Sprint Goal

**Validate that the system can run on RTX 4090 with Qwen2.5 32B model and establish the project foundation.**

This is a **BLOCKING sprint** - no other work can proceed until VRAM validation passes.

---

## Sprint Backlog

### Stories Committed

| ID | Story | Points | Owner | Status |
|----|-------|--------|-------|--------|
| **STORY-000** | Project Initialization | 2 | Dev | 🔲 Not Started |
| **STORY-CR-001** | VRAM Usage Empirical Validation | 3 | Dev | 🔲 Not Started |
| **STORY-CR-002** | Fallback LLM Configuration | 3 | Dev | 🔲 Not Started |
| **STORY-CR-003** | VRAM Monitoring Integration | 2 | Dev | 🔲 Not Started |
| **TOTAL** | | **10** | | |

---

## Story Details

### STORY-000: Project Initialization (2 pts)

**Goal:** Initialize the project with uv and create the directory structure

**Tasks:**
- [ ] Run `uv init --name dfir-assistant --python 3.11`
- [ ] Add all dependencies to pyproject.toml
- [ ] Run `uv sync` to create lock file
- [ ] Create directory structure per architecture spec
- [ ] Create placeholder `__init__.py` files
- [ ] Verify `uv export` works for air-gap

**Acceptance Criteria:**
- [ ] `uv sync` succeeds without errors
- [ ] All directories from architecture.md exist
- [ ] `uv export --format requirements-txt` produces valid output

**Commands:**
```bash
# Initialize project
cd /Users/yalul/Code/Play
uv init --name dfir-assistant --python 3.11

# Add dependencies
uv add gradio qdrant-client instructor httpx marker-pdf pydantic pyyaml rich pynvml
uv add --dev pytest pytest-asyncio ruff mypy

# Create directory structure
mkdir -p src/dfir_assistant/{ingestion,retrieval,generation,validation,context,session,ui,pipeline}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p config/org_context
mkdir -p data/books
mkdir -p scripts/systemd
mkdir -p docs

# Create __init__.py files
touch src/dfir_assistant/__init__.py
touch src/dfir_assistant/{ingestion,retrieval,generation,validation,context,session,ui,pipeline}/__init__.py

# Verify
uv sync
uv export --format requirements-txt > requirements.txt
```

**Definition of Done:** Project structure matches architecture.md specification

---

### STORY-CR-001: VRAM Usage Empirical Validation (3 pts)

**Goal:** Validate that Qwen2.5 32B Q4 fits in 24GB VRAM under realistic conditions

**Tasks:**
- [ ] Ensure Ollama is installed and running
- [ ] Pull qwen2.5:32b-instruct-q4_K_M model
- [ ] Pull nomic-embed-text model
- [ ] Create `scripts/validate_vram.py`
- [ ] Run inference with 8K context and measure VRAM
- [ ] Run multi-turn conversation (5+ turns) and measure KV cache growth
- [ ] Document results in `docs/vram-validation-results.md`

**Acceptance Criteria:**
- [ ] VRAM usage documented with exact numbers
- [ ] Multi-turn KV cache growth measured
- [ ] Pass/Fail determination made
- [ ] If FAIL: trigger STORY-CR-002 fallback

**Script Template:**
```python
#!/usr/bin/env python3
"""VRAM Validation Script - Sprint 0 Blocker"""

import subprocess
import httpx
import time

def get_vram_usage() -> float:
    """Get current GPU VRAM usage in GB"""
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        capture_output=True, text=True
    )
    return float(result.stdout.strip()) / 1024

def test_inference(prompt: str, context_tokens: int = 8000) -> dict:
    """Run inference and measure VRAM"""
    # Generate test context
    context = "Windows process analysis: " * (context_tokens // 5)
    full_prompt = f"{context}\n\nQuestion: {prompt}"
    
    vram_before = get_vram_usage()
    
    response = httpx.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:32b-instruct-q4_K_M",
            "prompt": full_prompt,
            "stream": False
        },
        timeout=120.0
    )
    
    vram_after = get_vram_usage()
    
    return {
        "vram_before": vram_before,
        "vram_after": vram_after,
        "vram_peak": max(vram_before, vram_after),
        "response_length": len(response.json().get("response", ""))
    }

def main():
    print("=" * 60)
    print("VRAM VALIDATION - Sprint 0 BLOCKING")
    print("=" * 60)
    
    # Test 1: Single inference with 8K context
    print("\nTest 1: Single inference (8K context)...")
    result = test_inference("What is a VAD tree?", context_tokens=8000)
    print(f"  VRAM Peak: {result['vram_peak']:.2f} GB")
    
    # Test 2: Multi-turn conversation
    print("\nTest 2: Multi-turn conversation (5 turns)...")
    for i in range(5):
        result = test_inference(f"Follow-up question {i+1}", context_tokens=4000)
        print(f"  Turn {i+1} VRAM: {result['vram_peak']:.2f} GB")
    
    # Verdict
    print("\n" + "=" * 60)
    if result['vram_peak'] < 22.0:
        print("✅ PASS - VRAM within budget (< 22GB)")
        print("   Proceed to Sprint 1")
    else:
        print("❌ FAIL - VRAM exceeds budget")
        print("   Execute STORY-CR-002 (Fallback to 14B)")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

**Definition of Done:** VRAM validation results documented, pass/fail determined

---

### STORY-CR-002: Fallback LLM Configuration (3 pts)

**Goal:** Have a tested fallback model ready if 32B doesn't fit

**Tasks:**
- [ ] Pull qwen2.5:14b-instruct-q4_K_M model
- [ ] Run same validation tests with 14B
- [ ] Compare quality with sample prompts
- [ ] Document fallback procedure

**Acceptance Criteria:**
- [ ] 14B model tested and VRAM verified < 10GB
- [ ] Quality comparison documented
- [ ] config/settings.yaml supports model switching
- [ ] Fallback procedure documented

**Configuration:**
```yaml
# config/settings.yaml
llm:
  # Primary model (change if VRAM validation fails)
  model_name: "qwen2.5:32b-instruct-q4_K_M"
  
  # Fallback models (in priority order)
  fallback_models:
    - "qwen2.5:14b-instruct-q4_K_M"
    - "qwen2.5:7b-instruct-q8_0"
  
  # Ollama settings
  ollama_url: "http://localhost:11434"
  temperature: 0.1
  max_tokens: 4096
```

**Definition of Done:** Fallback model tested and documented

---

### STORY-CR-003: VRAM Monitoring Integration (2 pts)

**Goal:** Add runtime VRAM monitoring to detect memory pressure

**Tasks:**
- [ ] Create `src/dfir_assistant/validation/vram_monitor.py`
- [ ] Implement VRAM query using pynvml
- [ ] Add threshold-based warnings
- [ ] Create graceful degradation response

**Acceptance Criteria:**
- [ ] `VRAMMonitor` class implemented
- [ ] Logs VRAM at INFO level per query
- [ ] Warns at 22GB, errors at 23GB
- [ ] Returns friendly error on memory pressure

**Implementation:**
```python
# src/dfir_assistant/validation/vram_monitor.py
import logging
from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo

logger = logging.getLogger(__name__)

class VRAMMonitor:
    WARNING_THRESHOLD_GB = 22.0
    CRITICAL_THRESHOLD_GB = 23.0
    
    def __init__(self):
        nvmlInit()
        self.handle = nvmlDeviceGetHandleByIndex(0)
    
    def get_usage_gb(self) -> float:
        info = nvmlDeviceGetMemoryInfo(self.handle)
        return info.used / (1024 ** 3)
    
    def check_health(self) -> tuple[bool, str | None]:
        usage = self.get_usage_gb()
        logger.info(f"VRAM usage: {usage:.2f} GB")
        
        if usage >= self.CRITICAL_THRESHOLD_GB:
            return False, "🔴 Critical VRAM pressure - service may be unstable"
        elif usage >= self.WARNING_THRESHOLD_GB:
            return True, "⚠️ High VRAM usage - monitoring closely"
        return True, None
```

**Definition of Done:** VRAM monitoring implemented and tested

---

## Sprint Ceremonies

### Sprint Planning (Day 1)
- **Date:** 2026-01-15
- **Attendees:** Dev Lead
- **Outcome:** Sprint backlog committed (10 points)

### Daily Standups
- **Schedule:** Daily at 09:00 IST (async for solo dev)
- **Format:** Update sprint board, note blockers

### Sprint Review (Day 10)
- **Date:** 2026-01-29
- **Demo:** VRAM validation results, project structure
- **Outcome:** Go/No-Go for Sprint 1

### Sprint Retrospective (Day 10)
- **Date:** 2026-01-29
- **Focus:** Process improvements for subsequent sprints

---

## Definition of Done (Sprint Level)

- [ ] All stories in "Done" column
- [ ] VRAM validation PASS or documented fallback
- [ ] Project structure matches architecture.md
- [ ] `uv sync` succeeds
- [ ] Documentation updated
- [ ] Ready for Sprint 1 kickoff

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| VRAM validation fails | Medium | High | CR-002 fallback ready |
| Ollama not installed | Low | Medium | Installation docs provided |
| Network issues pulling models | Low | Medium | Can use pre-cached models |

---

## Sprint Outcome

**Status:** 🔲 PLANNED

| Metric | Target | Actual |
|--------|--------|--------|
| Stories Completed | 4/4 | - |
| Points Completed | 10 | - |
| VRAM Validation | PASS | - |
| Sprint Goal Met | Yes | - |

---

## Next Sprint Preview

**Sprint 1: Foundation & Quality** (34 points)
- EPIC-006: PDF Processing Quality
- EPIC-007: Single Collection Architecture  
- EPIC-002: Command Validation
- EPIC-003: Evaluation Framework

Sprint 1 can only begin after Sprint 0 VRAM validation PASSES.

---

*Sprint 0 Plan created by Scrum Master Agent*
*Ready for implementation*
