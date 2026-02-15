import logging
from typing import List
from qdrant_client import QdrantClient
from ..config.settings import settings
from ..models.chunk import Chunk


class QdrantService:
    """Service for interacting with Qdrant vector database."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
        self.collection_name = settings.qdrant_collection_name

    def search(self, query_vector: List[float], top_k: int = None) -> List[Chunk]:
        """Search for similar chunks in Qdrant."""
        k = top_k or settings.top_k
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=k,
                score_threshold=settings.similarity_threshold,
            )

            chunks = []
            for result in results:
                chunk = Chunk(
                    chunk_id=str(result.id),
                    content=result.payload.get("text", ""),
                    source_url=result.payload.get("url", ""),
                    section_id=result.payload.get("section", ""),
                    document_title=result.payload.get("title", "Unknown"),
                    similarity_score=result.score,
                    metadata=result.payload,
                )
                chunks.append(chunk)

            self.logger.info(f"Retrieved {len(chunks)} chunks from Qdrant")
            return chunks

        except Exception as e:
            self.logger.error(f"Qdrant search error: {e}")
            return []

    def validate_connection(self) -> bool:
        """Validate connection to Qdrant."""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            self.logger.error(f"Qdrant connection failed: {e}")
            return False
