"""Golden Q&A dataset loader and query management."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)


@dataclass
class GoldenQuery:
    """A single golden Q&A test case."""
    
    id: str
    type: str  # concept, anomaly, procedure, tool_command
    query: str
    expected_chunks: list[str]
    expected_response_contains: list[str]
    expected_table: bool = False
    expected_commands: list[str] | None = None
    difficulty: str = "medium"


class GoldenDataset:
    """Loader and accessor for golden Q&A test dataset.
    
    Provides test cases for evaluating retrieval and response quality.
    """
    
    def __init__(self, dataset_path: Path | str | None = None):
        """Initialize dataset loader.
        
        Args:
            dataset_path: Path to golden_qa_dataset.json
        """
        if dataset_path is None:
            dataset_path = Path("tests/fixtures/golden_qa_dataset.json")
        
        self.dataset_path = Path(dataset_path)
        self._queries: list[GoldenQuery] = []
        self._metadata: dict = {}
        self._loaded = False
    
    def load(self) -> bool:
        """Load dataset from JSON file.
        
        Returns:
            True if loaded successfully
        """
        if not self.dataset_path.exists():
            logger.error(f"Dataset not found: {self.dataset_path}")
            return False
        
        try:
            with open(self.dataset_path) as f:
                data = json.load(f)
            
            self._metadata = data.get("metadata", {})
            
            for query_data in data.get("queries", []):
                query = GoldenQuery(
                    id=query_data["id"],
                    type=query_data["type"],
                    query=query_data["query"],
                    expected_chunks=query_data.get("expected_chunks", []),
                    expected_response_contains=query_data.get("expected_response_contains", []),
                    expected_table=query_data.get("expected_table", False),
                    expected_commands=query_data.get("expected_commands"),
                    difficulty=query_data.get("difficulty", "medium"),
                )
                self._queries.append(query)
            
            self._loaded = True
            logger.info(f"Loaded {len(self._queries)} golden queries")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            return False
    
    @property
    def queries(self) -> list[GoldenQuery]:
        """Get all loaded queries."""
        if not self._loaded:
            self.load()
        return self._queries
    
    @property
    def metadata(self) -> dict:
        """Get dataset metadata."""
        if not self._loaded:
            self.load()
        return self._metadata
    
    def get_by_type(self, query_type: str) -> list[GoldenQuery]:
        """Get queries by type.
        
        Args:
            query_type: One of concept, anomaly, procedure, tool_command
        """
        return [q for q in self.queries if q.type == query_type]
    
    def get_by_difficulty(self, difficulty: str) -> list[GoldenQuery]:
        """Get queries by difficulty level."""
        return [q for q in self.queries if q.difficulty == difficulty]
    
    def get_by_id(self, query_id: str) -> GoldenQuery | None:
        """Get a specific query by ID."""
        for q in self.queries:
            if q.id == query_id:
                return q
        return None
    
    def iterate_queries(self) -> Iterator[GoldenQuery]:
        """Iterate over all queries."""
        yield from self.queries
    
    def get_statistics(self) -> dict:
        """Get dataset statistics."""
        return {
            "total_queries": len(self.queries),
            "by_type": {
                "concept": len(self.get_by_type("concept")),
                "anomaly": len(self.get_by_type("anomaly")),
                "procedure": len(self.get_by_type("procedure")),
                "tool_command": len(self.get_by_type("tool_command")),
            },
            "by_difficulty": {
                "easy": len(self.get_by_difficulty("easy")),
                "medium": len(self.get_by_difficulty("medium")),
                "hard": len(self.get_by_difficulty("hard")),
            },
        }
