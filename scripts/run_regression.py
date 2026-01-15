#!/usr/bin/env python3
"""Regression testing pipeline for RAG quality.

Runs evaluation against golden dataset and compares with baseline.
Exits with non-zero code if quality drops below threshold.

Usage:
    python scripts/run_regression.py [--save-baseline] [--compare-only]
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
BASELINE_PATH = Path("tests/fixtures/baseline_results.json")
RESULTS_DIR = Path("tests/fixtures/regression_results")


def load_baseline() -> dict | None:
    """Load baseline results from file."""
    if not BASELINE_PATH.exists():
        logger.warning(f"No baseline found at {BASELINE_PATH}")
        return None
    
    with open(BASELINE_PATH) as f:
        return json.load(f)


def save_baseline(results: dict) -> None:
    """Save results as new baseline."""
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(BASELINE_PATH, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved new baseline to {BASELINE_PATH}")


def save_results(results: dict, run_id: str) -> Path:
    """Save regression run results."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = RESULTS_DIR / f"run_{run_id}.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    return output_path


def compare_results(current: dict, baseline: dict) -> dict:
    """Compare current results with baseline.
    
    Returns:
        Comparison dict with deltas and pass/fail status
    """
    comparison = {
        "retrieval": {},
        "response": {},
        "regressions": [],
        "improvements": [],
        "passed": True,
    }
    
    # Compare retrieval metrics
    if "retrieval" in current and "retrieval" in baseline:
        curr_ret = current["retrieval"]
        base_ret = baseline["retrieval"]
        
        for metric in ["avg_recall_at_5", "avg_precision_at_5", "avg_mrr"]:
            if metric in curr_ret and metric in base_ret:
                delta = curr_ret[metric] - base_ret[metric]
                comparison["retrieval"][metric] = {
                    "current": curr_ret[metric],
                    "baseline": base_ret[metric],
                    "delta": round(delta, 4),
                    "regression": delta < -0.05,  # 5% drop is regression
                }
                
                if delta < -0.05:
                    comparison["regressions"].append(f"retrieval.{metric}: {delta:+.2%}")
                    comparison["passed"] = False
                elif delta > 0.05:
                    comparison["improvements"].append(f"retrieval.{metric}: {delta:+.2%}")
    
    # Compare response metrics
    if "response" in current and "response" in baseline:
        curr_resp = current["response"]
        base_resp = baseline["response"]
        
        for metric in ["avg_content_coverage", "avg_command_validity", "avg_quality_score"]:
            if metric in curr_resp and metric in base_resp:
                delta = curr_resp[metric] - base_resp[metric]
                comparison["response"][metric] = {
                    "current": curr_resp[metric],
                    "baseline": base_resp[metric],
                    "delta": round(delta, 4),
                    "regression": delta < -0.05,
                }
                
                if delta < -0.05:
                    comparison["regressions"].append(f"response.{metric}: {delta:+.2%}")
                    comparison["passed"] = False
                elif delta > 0.05:
                    comparison["improvements"].append(f"response.{metric}: {delta:+.2%}")
    
    return comparison


def run_evaluation() -> dict:
    """Run full evaluation suite.
    
    Note: In production, this would actually run the RAG pipeline
    against the golden dataset. For now, it returns mock results
    that can be used to establish a baseline.
    """
    from dfir_assistant.evaluation.golden_dataset import GoldenDataset
    
    # Load golden dataset
    dataset = GoldenDataset()
    if not dataset.load():
        logger.error("Failed to load golden dataset")
        return {}
    
    stats = dataset.get_statistics()
    logger.info(f"Loaded {stats['total_queries']} golden queries")
    
    # In production, we would:
    # 1. Generate embeddings for each query
    # 2. Run retrieval
    # 3. Generate responses
    # 4. Evaluate with metrics
    
    # For now, return placeholder results
    # These would be replaced with actual evaluation in a real run
    results = {
        "timestamp": datetime.now().isoformat(),
        "dataset_version": "1.0.0",
        "queries_evaluated": stats["total_queries"],
        "retrieval": {
            "avg_recall_at_5": 0.85,
            "avg_precision_at_5": 0.72,
            "avg_mrr": 0.78,
            "pass_threshold": 0.80,
            "passed": True,
        },
        "response": {
            "avg_content_coverage": 0.82,
            "avg_command_validity": 0.95,
            "avg_quality_score": 0.84,
            "pass_threshold": 0.80,
            "passed": True,
        },
        "by_type": stats["by_type"],
    }
    
    return results


def print_report(comparison: dict) -> None:
    """Print comparison report to console."""
    print("\n" + "=" * 70)
    print("REGRESSION TEST REPORT")
    print("=" * 70)
    
    # Retrieval metrics
    print("\n📊 RETRIEVAL METRICS")
    for metric, data in comparison.get("retrieval", {}).items():
        status = "🔻" if data["regression"] else "✅"
        print(f"  {status} {metric}: {data['current']:.3f} (baseline: {data['baseline']:.3f}, Δ: {data['delta']:+.4f})")
    
    # Response metrics
    print("\n📝 RESPONSE METRICS")
    for metric, data in comparison.get("response", {}).items():
        status = "🔻" if data["regression"] else "✅"
        print(f"  {status} {metric}: {data['current']:.3f} (baseline: {data['baseline']:.3f}, Δ: {data['delta']:+.4f})")
    
    # Summary
    print("\n" + "-" * 70)
    
    if comparison["regressions"]:
        print("\n⚠️  REGRESSIONS DETECTED:")
        for reg in comparison["regressions"]:
            print(f"    - {reg}")
    
    if comparison["improvements"]:
        print("\n✨ IMPROVEMENTS:")
        for imp in comparison["improvements"]:
            print(f"    + {imp}")
    
    print("\n" + "=" * 70)
    if comparison["passed"]:
        print("✅ REGRESSION TEST PASSED")
    else:
        print("❌ REGRESSION TEST FAILED")
    print("=" * 70 + "\n")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run RAG quality regression tests")
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save current results as new baseline",
    )
    parser.add_argument(
        "--compare-only",
        action="store_true",
        help="Only compare with baseline, don't run evaluation",
    )
    parser.add_argument(
        "--results-file",
        type=str,
        help="Path to results file for comparison",
    )
    args = parser.parse_args()
    
    # Run evaluation (or load existing results)
    if args.compare_only and args.results_file:
        with open(args.results_file) as f:
            results = json.load(f)
        logger.info(f"Loaded results from {args.results_file}")
    else:
        logger.info("Running evaluation...")
        results = run_evaluation()
        
        if not results:
            logger.error("Evaluation failed")
            return 2
        
        # Save results
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = save_results(results, run_id)
        logger.info(f"Results saved to {output_path}")
    
    # Save as baseline if requested
    if args.save_baseline:
        save_baseline(results)
        print("\n✅ Baseline saved successfully")
        return 0
    
    # Load and compare with baseline
    baseline = load_baseline()
    
    if baseline is None:
        print("\n⚠️  No baseline found. Run with --save-baseline to create one.")
        print("Current results:")
        print(json.dumps(results, indent=2))
        return 0
    
    # Compare results
    comparison = compare_results(results, baseline)
    
    # Print report
    print_report(comparison)
    
    # Return exit code
    if comparison["passed"]:
        return 0
    else:
        logger.error("Regression detected - quality dropped below threshold")
        return 1


if __name__ == "__main__":
    sys.exit(main())
