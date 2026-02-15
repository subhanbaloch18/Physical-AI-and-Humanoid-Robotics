import logging
from typing import List
import cohere
from ..config.settings import settings
from ..models.chunk import Chunk
from .qdrant_service import QdrantService


class RetrievalService:
    """Service for retrieving relevant context from the vector database."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cohere_client = cohere.Client(settings.cohere_api_key)
        self.qdrant_service = QdrantService()

    def embed_query(self, query_text: str) -> List[float]:
        """Generate embedding for a query using Cohere."""
        try:
            response = self.cohere_client.embed(
                texts=[query_text],
                model="embed-english-v3.0",
                input_type="search_query",
            )
            return response.embeddings[0]
        except Exception as e:
            self.logger.error(f"Embedding error: {e}")
            return []

    def retrieve_context(
        self,
        query_text: str,
        top_k: int = None,
        include_diverse_content: bool = False,
    ) -> List[Chunk]:
        """Retrieve relevant context chunks for a query."""
        k = top_k or settings.top_k

        # Generate query embedding
        query_embedding = self.embed_query(query_text)
        if not query_embedding:
            return []

        # Search Qdrant
        chunks = self.qdrant_service.search(query_embedding, top_k=k)

        self.logger.info(
            f"Retrieved {len(chunks)} context chunks for query: {query_text[:50]}..."
        )
        return chunks
