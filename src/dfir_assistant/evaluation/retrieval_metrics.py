"""Retrieval quality metrics for RAG evaluation.

Implements Recall@K and Precision@K metrics for measuring
retrieval effectiveness against golden dataset.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from dfir_assistant.evaluation.golden_dataset import GoldenQuery

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Result of a single retrieval evaluation."""
    
    query_id: str
    query_text: str
    expected_chunks: list[str]
    retrieved_chunk_ids: list[str]
    retrieved_scores: list[float]
    recall_at_5: float
    precision_at_5: float
    mrr: float  # Mean Reciprocal Rank
    hits: list[str] = field(default_factory=list)
    misses: list[str] = field(default_factory=list)


@dataclass
class RetrievalReport:
    """Aggregated retrieval evaluation report."""
    
    total_queries: int
    avg_recall_at_5: float
    avg_precision_at_5: float
    avg_mrr: float
    queries_above_threshold: int
    threshold: float
    passed: bool
    results: list[RetrievalResult]
    
    def to_dict(self) -> dict:
        return {
            "total_queries": self.total_queries,
            "avg_recall_at_5": round(self.avg_recall_at_5, 3),
            "avg_precision_at_5": round(self.avg_precision_at_5, 3),
            "avg_mrr": round(self.avg_mrr, 3),
            "queries_above_threshold": self.queries_above_threshold,
            "pass_rate": round(self.queries_above_threshold / self.total_queries * 100, 1),
            "threshold": self.threshold,
            "passed": self.passed,
        }


class RetrievalEvaluator:
    """Evaluates retrieval quality against golden dataset.
    
    Metrics:
    - Recall@K: Fraction of expected chunks found in top K results
    - Precision@K: Fraction of top K results that are relevant
    - MRR: Mean Reciprocal Rank of first relevant result
    """
    
    def __init__(self, pass_threshold: float = 0.8, k: int = 5):
        """Initialize evaluator.
        
        Args:
            pass_threshold: Minimum recall to pass (default 0.8 = 80%)
            k: Number of results to consider
        """
        self.pass_threshold = pass_threshold
        self.k = k
    
    def evaluate_single(
        self,
        query: GoldenQuery,
        retrieved_chunks: list[dict[str, Any]],
    ) -> RetrievalResult:
        """Evaluate retrieval for a single query.
        
        Args:
            query: Golden query with expected chunks
            retrieved_chunks: List of retrieved chunk dicts with 'id' and 'score'
            
        Returns:
            RetrievalResult with metrics
        """
        expected = set(query.expected_chunks)
        
        # Get top K retrieved IDs
        top_k = retrieved_chunks[:self.k]
        retrieved_ids = [c.get("id", c.get("chunk_id", "")) for c in top_k]
        retrieved_scores = [c.get("score", 0.0) for c in top_k]
        
        # Calculate hits and misses (fuzzy matching on chunk ID)
        hits = []
        for expected_chunk in expected:
            for retrieved_id in retrieved_ids:
                if expected_chunk.lower() in retrieved_id.lower():
                    hits.append(expected_chunk)
                    break
        
        misses = list(expected - set(hits))
        
        # Recall@K: what fraction of expected chunks did we find?
        recall = len(hits) / len(expected) if expected else 1.0
        
        # Precision@K: what fraction of retrieved are relevant?
        relevant_count = len(hits)
        precision = relevant_count / len(top_k) if top_k else 0.0
        
        # MRR: reciprocal rank of first relevant result
        mrr = 0.0
        for i, retrieved_id in enumerate(retrieved_ids):
            for expected_chunk in expected:
                if expected_chunk.lower() in retrieved_id.lower():
                    mrr = 1.0 / (i + 1)
                    break
            if mrr > 0:
                break
        
        return RetrievalResult(
            query_id=query.id,
            query_text=query.query,
            expected_chunks=list(expected),
            retrieved_chunk_ids=retrieved_ids,
            retrieved_scores=retrieved_scores,
            recall_at_5=recall,
            precision_at_5=precision,
            mrr=mrr,
            hits=hits,
            misses=misses,
        )
    
    def evaluate_batch(
        self,
        queries: list[GoldenQuery],
        results_map: dict[str, list[dict[str, Any]]],
    ) -> RetrievalReport:
        """Evaluate retrieval for multiple queries.
        
        Args:
            queries: List of golden queries
            results_map: Map of query_id -> retrieved chunks
            
        Returns:
            RetrievalReport with aggregated metrics
        """
        results = []
        
        for query in queries:
            retrieved = results_map.get(query.id, [])
            result = self.evaluate_single(query, retrieved)
            results.append(result)
        
        # Aggregate metrics
        total = len(results)
        avg_recall = sum(r.recall_at_5 for r in results) / total if total > 0 else 0
        avg_precision = sum(r.precision_at_5 for r in results) / total if total > 0 else 0
        avg_mrr = sum(r.mrr for r in results) / total if total > 0 else 0
        above_threshold = sum(1 for r in results if r.recall_at_5 >= self.pass_threshold)
        
        passed = avg_recall >= self.pass_threshold
        
        return RetrievalReport(
            total_queries=total,
            avg_recall_at_5=avg_recall,
            avg_precision_at_5=avg_precision,
            avg_mrr=avg_mrr,
            queries_above_threshold=above_threshold,
            threshold=self.pass_threshold,
            passed=passed,
            results=results,
        )
    
    def log_warning_if_low(self, result: RetrievalResult) -> None:
        """Log warning if retrieval quality is low."""
        if result.recall_at_5 < self.pass_threshold:
            logger.warning(
                f"Low retrieval quality for {result.query_id}: "
                f"Recall@5={result.recall_at_5:.2f} "
                f"(threshold={self.pass_threshold})"
            )
            if result.misses:
                logger.warning(f"  Missing chunks: {result.misses}")


def calculate_recall_at_k(expected: set[str], retrieved: list[str], k: int = 5) -> float:
    """Calculate Recall@K metric.
    
    Args:
        expected: Set of expected chunk identifiers
        retrieved: List of retrieved chunk IDs (ranked)
        k: Number of top results to consider
        
    Returns:
        Recall score (0.0 to 1.0)
    """
    if not expected:
        return 1.0
    
    top_k = set(retrieved[:k])
    hits = len(expected.intersection(top_k))
    return hits / len(expected)


def calculate_precision_at_k(expected: set[str], retrieved: list[str], k: int = 5) -> float:
    """Calculate Precision@K metric.
    
    Args:
        expected: Set of expected chunk identifiers
        retrieved: List of retrieved chunk IDs (ranked)
        k: Number of top results to consider
        
    Returns:
        Precision score (0.0 to 1.0)
    """
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    
    hits = len(set(top_k).intersection(expected))
    return hits / len(top_k)
