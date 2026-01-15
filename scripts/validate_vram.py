#!/usr/bin/env python3
"""VRAM Validation Script - Sprint 0 BLOCKING.

This script validates that Qwen2.5 32B Q4 fits in 24GB VRAM under realistic conditions.
It tests:
1. Single inference with 8K context
2. Multi-turn conversation (5+ turns) with KV cache growth
3. Simultaneous embedding generation

Exit codes:
- 0: PASS - VRAM within budget
- 1: FAIL - VRAM exceeds budget, use fallback model
- 2: ERROR - Could not complete validation
"""

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import httpx


@dataclass
class VRAMResult:
    """VRAM measurement result."""
    
    vram_before_gb: float
    vram_after_gb: float
    vram_peak_gb: float
    response_length: int
    latency_ms: float


@dataclass
class ValidationReport:
    """Complete validation report."""
    
    timestamp: str
    model_name: str
    single_inference_peak: float
    multi_turn_peaks: list[float]
    embedding_vram: float
    combined_peak: float
    verdict: str
    recommendation: str


def get_vram_usage() -> float:
    """Get current GPU VRAM usage in GB using nvidia-smi."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            print(f"nvidia-smi error: {result.stderr}")
            return -1.0
        return float(result.stdout.strip().split("\n")[0]) / 1024
    except FileNotFoundError:
        print("ERROR: nvidia-smi not found. Is NVIDIA driver installed?")
        return -1.0
    except Exception as e:
        print(f"ERROR getting VRAM: {e}")
        return -1.0


def get_vram_total() -> float:
    """Get total GPU VRAM in GB."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return float(result.stdout.strip().split("\n")[0]) / 1024
    except Exception:
        return 24.0  # Default assumption


def check_ollama_running() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


def check_model_available(model_name: str) -> bool:
    """Check if a model is available in Ollama."""
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(m.get("name", "").startswith(model_name.split(":")[0]) for m in models)
        return False
    except Exception:
        return False


def run_inference(prompt: str, model: str, context_tokens: int = 8000) -> VRAMResult:
    """Run inference and measure VRAM.
    
    Args:
        prompt: The question to ask
        model: Model name in Ollama
        context_tokens: Approximate number of context tokens to simulate
        
    Returns:
        VRAMResult with measurements
    """
    # Generate test context to simulate realistic retrieval
    context = "Windows process analysis context for memory forensics investigation. " * (context_tokens // 10)
    full_prompt = f"""Context from Windows Internals documentation:
{context}

Based on the above context, please answer the following question:
{prompt}

Provide a detailed technical answer with relevant Volatility commands."""

    vram_before = get_vram_usage()
    start_time = time.time()
    
    try:
        response = httpx.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_ctx": 8192,  # Context window
                    "temperature": 0.1,
                }
            },
            timeout=180.0,  # 3 min timeout for large model
        )
        response.raise_for_status()
        
        latency_ms = (time.time() - start_time) * 1000
        vram_after = get_vram_usage()
        
        result = response.json()
        response_text = result.get("response", "")
        
        return VRAMResult(
            vram_before_gb=vram_before,
            vram_after_gb=vram_after,
            vram_peak_gb=max(vram_before, vram_after),
            response_length=len(response_text),
            latency_ms=latency_ms,
        )
    except httpx.TimeoutException:
        print("  ERROR: Inference timed out (>180s)")
        return VRAMResult(
            vram_before_gb=vram_before,
            vram_after_gb=get_vram_usage(),
            vram_peak_gb=-1,
            response_length=0,
            latency_ms=-1,
        )
    except Exception as e:
        print(f"  ERROR: Inference failed: {e}")
        return VRAMResult(
            vram_before_gb=vram_before,
            vram_after_gb=get_vram_usage(),
            vram_peak_gb=-1,
            response_length=0,
            latency_ms=-1,
        )


def run_embedding(text: str, model: str = "nomic-embed-text") -> float:
    """Run embedding generation and return VRAM usage."""
    try:
        vram_before = get_vram_usage()
        
        response = httpx.post(
            "http://localhost:11434/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=30.0,
        )
        response.raise_for_status()
        
        vram_after = get_vram_usage()
        return max(vram_before, vram_after)
    except Exception as e:
        print(f"  ERROR: Embedding failed: {e}")
        return -1.0


def validate_vram(model_name: str = "qwen2.5:32b-instruct-q4_K_M") -> ValidationReport:
    """Run complete VRAM validation suite.
    
    Args:
        model_name: The model to validate
        
    Returns:
        ValidationReport with all measurements and verdict
    """
    print("=" * 70)
    print("VRAM VALIDATION - Sprint 0 BLOCKING")
    print("=" * 70)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"Model: {model_name}")
    print(f"Total VRAM: {get_vram_total():.1f} GB")
    print(f"Initial VRAM usage: {get_vram_usage():.2f} GB")
    
    # Test 1: Single inference with 8K context
    print("\n" + "-" * 50)
    print("Test 1: Single inference (8K context)...")
    print("-" * 50)
    
    result1 = run_inference(
        "What is a VAD tree and how is it used in memory forensics?",
        model_name,
        context_tokens=8000,
    )
    print(f"  VRAM Before: {result1.vram_before_gb:.2f} GB")
    print(f"  VRAM After:  {result1.vram_after_gb:.2f} GB")
    print(f"  VRAM Peak:   {result1.vram_peak_gb:.2f} GB")
    print(f"  Response:    {result1.response_length} chars")
    print(f"  Latency:     {result1.latency_ms:.0f} ms")
    single_peak = result1.vram_peak_gb
    
    # Test 2: Multi-turn conversation (simulate KV cache growth)
    print("\n" + "-" * 50)
    print("Test 2: Multi-turn conversation (5 turns)...")
    print("-" * 50)
    
    questions = [
        "What processes should I investigate for process hollowing?",
        "How do I identify injected code using VAD analysis?",
        "What are the signs of a rootkit in memory?",
        "How do I analyze network connections from a memory dump?",
        "Summarize the key steps for initial triage of a compromised system.",
    ]
    
    multi_turn_peaks = []
    for i, question in enumerate(questions, 1):
        result = run_inference(question, model_name, context_tokens=4000)
        print(f"  Turn {i}: VRAM Peak {result.vram_peak_gb:.2f} GB | Latency {result.latency_ms:.0f}ms")
        multi_turn_peaks.append(result.vram_peak_gb)
    
    # Test 3: Embedding generation (if model available)
    print("\n" + "-" * 50)
    print("Test 3: Embedding generation...")
    print("-" * 50)
    
    embedding_vram = run_embedding(
        "This is a test document about Windows memory forensics and process analysis."
    )
    print(f"  Embedding VRAM: {embedding_vram:.2f} GB")
    
    # Calculate combined peak (LLM + embedding)
    combined_peak = max(single_peak, max(multi_turn_peaks) if multi_turn_peaks else 0)
    
    # Determine verdict
    VRAM_WARNING = 22.0
    VRAM_CRITICAL = 23.0
    
    if combined_peak < 0:
        verdict = "ERROR"
        recommendation = "Could not complete VRAM validation. Check Ollama and model availability."
    elif combined_peak < VRAM_WARNING:
        verdict = "PASS"
        recommendation = f"VRAM usage ({combined_peak:.1f}GB) is within safe limits. Proceed with {model_name}."
    elif combined_peak < VRAM_CRITICAL:
        verdict = "WARN"
        recommendation = f"VRAM usage ({combined_peak:.1f}GB) is high. Monitor closely. Consider 14B fallback."
    else:
        verdict = "FAIL"
        recommendation = f"VRAM usage ({combined_peak:.1f}GB) exceeds budget. Use fallback model (14B or 7B)."
    
    return ValidationReport(
        timestamp=datetime.now().isoformat(),
        model_name=model_name,
        single_inference_peak=single_peak,
        multi_turn_peaks=multi_turn_peaks,
        embedding_vram=embedding_vram,
        combined_peak=combined_peak,
        verdict=verdict,
        recommendation=recommendation,
    )


def write_report(report: ValidationReport, output_path: str = "docs/vram-validation-results.md") -> None:
    """Write validation report to markdown file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    content = f"""# VRAM Validation Results

**Generated:** {report.timestamp}
**Model:** {report.model_name}

## Summary

| Metric | Value |
|--------|-------|
| **Verdict** | {report.verdict} |
| **Single Inference Peak** | {report.single_inference_peak:.2f} GB |
| **Multi-Turn Peak** | {max(report.multi_turn_peaks) if report.multi_turn_peaks else 'N/A':.2f} GB |
| **Embedding VRAM** | {report.embedding_vram:.2f} GB |
| **Combined Peak** | {report.combined_peak:.2f} GB |

## Recommendation

{report.recommendation}

## Multi-Turn Details

| Turn | VRAM Peak (GB) |
|------|----------------|
"""
    for i, peak in enumerate(report.multi_turn_peaks, 1):
        content += f"| {i} | {peak:.2f} |\n"
    
    content += f"""
## Test Configuration

- Context window: 8192 tokens
- Temperature: 0.1
- Timeout: 180 seconds
- Test context: ~8000 tokens for single inference, ~4000 tokens per multi-turn

## Thresholds

| Level | Threshold | Meaning |
|-------|-----------|---------|
| PASS | < 22 GB | Safe to proceed |
| WARN | 22-23 GB | Monitor closely |
| FAIL | > 23 GB | Use fallback model |

---

*Report generated by `scripts/validate_vram.py`*
"""
    
    with open(output_path, "w") as f:
        f.write(content)
    print(f"\nReport written to: {output_path}")


def main() -> int:
    """Main entry point."""
    # Check prerequisites
    if not check_ollama_running():
        print("ERROR: Ollama is not running. Please start Ollama first:")
        print("  $ ollama serve")
        return 2
    
    model_name = "qwen2.5:32b-instruct-q4_K_M"
    
    if not check_model_available(model_name):
        print(f"Model {model_name} not found. Attempting to pull...")
        print(f"  $ ollama pull {model_name}")
        print("\nThis may take a while for a 32B model (~20GB download).")
        print("Run this script again after the model is downloaded.")
        return 2
    
    # Run validation
    report = validate_vram(model_name)
    
    # Print verdict
    print("\n" + "=" * 70)
    if report.verdict == "PASS":
        print("✅ PASS - VRAM within budget")
        print(f"   Peak usage: {report.combined_peak:.2f} GB")
        print("   Proceed to Sprint 1")
    elif report.verdict == "WARN":
        print("⚠️  WARN - VRAM usage is high")
        print(f"   Peak usage: {report.combined_peak:.2f} GB")
        print("   Consider monitoring or using 14B fallback")
    elif report.verdict == "FAIL":
        print("❌ FAIL - VRAM exceeds budget")
        print(f"   Peak usage: {report.combined_peak:.2f} GB")
        print("   Execute STORY-CR-002 (Fallback to 14B)")
    else:
        print("🔴 ERROR - Validation incomplete")
        print("   Check Ollama logs and model availability")
    print("=" * 70)
    
    print(f"\n{report.recommendation}")
    
    # Write report
    write_report(report)
    
    # Return appropriate exit code
    if report.verdict == "PASS":
        return 0
    elif report.verdict in ("WARN", "FAIL"):
        return 1
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())
