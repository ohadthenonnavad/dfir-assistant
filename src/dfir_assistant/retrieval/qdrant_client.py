"""Qdrant vector database client and collection management.

This module provides a unified interface for Qdrant operations including
collection setup, document storage, and vector search.
"""

import logging
from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from dfir_assistant.config import get_settings
from dfir_assistant.ingestion.models import Chunk

logger = logging.getLogger(__name__)


@dataclass
class QdrantConfig:
    """Configuration for Qdrant connection and collection."""
    
    url: str = "http://localhost:6333"
    collection_name: str = "dfir_books"
    embedding_dim: int = 768  # nomic-embed-text dimension
    
    # Collection settings
    distance: str = "Cosine"
    on_disk: bool = False  # Keep in memory for performance
    
    # Indexing settings
    hnsw_m: int = 16
    hnsw_ef_construct: int = 100


class DFIRQdrantClient:
    """Qdrant client optimized for DFIR knowledge base.
    
    Features:
    - Single collection with rich metadata filtering
    - Batch operations for efficient ingestion
    - Hybrid search support (dense + sparse)
    """
    
    # Metadata payload schema
    PAYLOAD_SCHEMA = {
        "source_type": qmodels.PayloadSchemaType.KEYWORD,
        "book_title": qmodels.PayloadSchemaType.KEYWORD,
        "chapter": qmodels.PayloadSchemaType.KEYWORD,
        "section": qmodels.PayloadSchemaType.KEYWORD,
        "page": qmodels.PayloadSchemaType.INTEGER,
        "chunk_index": qmodels.PayloadSchemaType.INTEGER,
    }
    
    def __init__(self, config: QdrantConfig | None = None):
        """Initialize Qdrant client.
        
        Args:
            config: QdrantConfig instance, uses settings if None
        """
        if config is None:
            settings = get_settings()
            config = QdrantConfig(
                url=settings.qdrant_url,
                collection_name=settings.collection_name,
            )
        
        self.config = config
        self._client: QdrantClient | None = None
    
    @property
    def client(self) -> QdrantClient:
        """Get or create Qdrant client connection."""
        if self._client is None:
            self._client = QdrantClient(url=self.config.url)
            logger.info(f"Connected to Qdrant at {self.config.url}")
        return self._client
    
    def health_check(self) -> bool:
        """Check if Qdrant is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
    
    def collection_exists(self) -> bool:
        """Check if the DFIR collection exists.
        
        Returns:
            True if collection exists
        """
        try:
            collections = self.client.get_collections().collections
            return any(c.name == self.config.collection_name for c in collections)
        except Exception as e:
            logger.error(f"Error checking collection: {e}")
            return False
    
    def create_collection(self, recreate: bool = False) -> bool:
        """Create the DFIR knowledge collection.
        
        Args:
            recreate: If True, delete existing collection first
            
        Returns:
            True if collection created successfully
        """
        if self.collection_exists():
            if recreate:
                logger.warning(f"Deleting existing collection: {self.config.collection_name}")
                self.client.delete_collection(self.config.collection_name)
            else:
                logger.info(f"Collection {self.config.collection_name} already exists")
                return True
        
        try:
            # Create collection with vector configuration
            self.client.create_collection(
                collection_name=self.config.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self.config.embedding_dim,
                    distance=qmodels.Distance.COSINE,
                    on_disk=self.config.on_disk,
                ),
                hnsw_config=qmodels.HnswConfigDiff(
                    m=self.config.hnsw_m,
                    ef_construct=self.config.hnsw_ef_construct,
                ),
                optimizers_config=qmodels.OptimizersConfigDiff(
                    indexing_threshold=20000,  # Start indexing after 20k points
                ),
            )
            
            # Create payload indexes for filtering
            for field_name, field_type in self.PAYLOAD_SCHEMA.items():
                self.client.create_payload_index(
                    collection_name=self.config.collection_name,
                    field_name=field_name,
                    field_schema=field_type,
                )
            
            logger.info(f"Created collection: {self.config.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False
    
    def get_collection_info(self) -> dict[str, Any]:
        """Get collection information and statistics.
        
        Returns:
            Dictionary with collection info
        """
        try:
            info = self.client.get_collection(self.config.collection_name)
            return {
                "name": self.config.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": info.status.value,
                "optimizer_status": info.optimizer_status.status.value,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {"error": str(e)}
    
    def upsert_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        batch_size: int = 100,
    ) -> int:
        """Upsert chunks with embeddings to collection.
        
        Args:
            chunks: List of Chunk objects
            embeddings: List of embedding vectors
            batch_size: Number of points per batch
            
        Returns:
            Number of points upserted
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunks and embeddings count mismatch: {len(chunks)} vs {len(embeddings)}"
            )
        
        total_upserted = 0
        
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]
            
            points = []
            for chunk, embedding in zip(batch_chunks, batch_embeddings):
                point = qmodels.PointStruct(
                    id=chunk.chunk_id,
                    vector=embedding,
                    payload={
                        "content": chunk.content,
                        "contextual_prefix": chunk.contextual_prefix,
                        "source_type": chunk.source_type,
                        "book_title": chunk.book_title,
                        "chapter": chunk.chapter,
                        "section": chunk.section,
                        "page": chunk.page,
                        "chunk_index": chunk.chunk_index,
                    },
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=self.config.collection_name,
                points=points,
            )
            
            total_upserted += len(points)
            logger.debug(f"Upserted batch {i // batch_size + 1}: {len(points)} points")
        
        logger.info(f"Total upserted: {total_upserted} points")
        return total_upserted
    
    def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
        filter_source_type: str | None = None,
        filter_book_title: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            query_vector: Query embedding vector
            limit: Maximum results to return
            score_threshold: Minimum similarity score
            filter_source_type: Filter by source type
            filter_book_title: Filter by book title
            
        Returns:
            List of search results with payload and score
        """
        # Build filter conditions
        must_conditions = []
        
        if filter_source_type:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="source_type",
                    match=qmodels.MatchValue(value=filter_source_type),
                )
            )
        
        if filter_book_title:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="book_title",
                    match=qmodels.MatchValue(value=filter_book_title),
                )
            )
        
        query_filter = None
        if must_conditions:
            query_filter = qmodels.Filter(must=must_conditions)
        
        results = self.client.search(
            collection_name=self.config.collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
            with_payload=True,
        )
        
        return [
            {
                "id": r.id,
                "score": r.score,
                "content": r.payload.get("content", ""),
                "contextual_prefix": r.payload.get("contextual_prefix", ""),
                "source_type": r.payload.get("source_type"),
                "book_title": r.payload.get("book_title"),
                "chapter": r.payload.get("chapter"),
                "section": r.payload.get("section"),
                "page": r.payload.get("page"),
            }
            for r in results
        ]
    
    def delete_by_book(self, book_title: str) -> int:
        """Delete all chunks for a specific book.
        
        Args:
            book_title: Title of book to delete
            
        Returns:
            Number of points deleted
        """
        try:
            # Get count before deletion
            count_before = self.client.count(
                collection_name=self.config.collection_name,
                count_filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="book_title",
                            match=qmodels.MatchValue(value=book_title),
                        )
                    ]
                ),
            ).count
            
            # Delete by filter
            self.client.delete(
                collection_name=self.config.collection_name,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="book_title",
                                match=qmodels.MatchValue(value=book_title),
                            )
                        ]
                    )
                ),
            )
            
            logger.info(f"Deleted {count_before} points for book: {book_title}")
            return count_before
            
        except Exception as e:
            logger.error(f"Error deleting book {book_title}: {e}")
            return 0


# Module-level client instance
_client: DFIRQdrantClient | None = None


def get_qdrant_client() -> DFIRQdrantClient:
    """Get or create the global Qdrant client instance."""
    global _client
    if _client is None:
        _client = DFIRQdrantClient()
    return _client
