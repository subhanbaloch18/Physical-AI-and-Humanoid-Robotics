from dataclasses import dataclass, field
from typing import List
from .query import Query
from .chunk import Chunk


@dataclass
class ValidationResult:
    """Model representing the result of a query validation/processing."""

    validation_id: str
    query: Query
    retrieved_chunks: List[Chunk] = field(default_factory=list)
    similarity_scores: List[float] = field(default_factory=list)
    metadata_accuracy: float = 0.0
    relevance_score: float = 0.0
    query_response_time: float = 0.0
    status: str = "pending"
    answer_text: str = ""

    def is_successful(self) -> bool:
        return self.status == "success"

    def to_dict(self):
        return {
            "validation_id": self.validation_id,
            "query": self.query.to_dict(),
            "retrieved_chunks": [c.to_dict() for c in self.retrieved_chunks],
            "similarity_scores": self.similarity_scores,
            "metadata_accuracy": self.metadata_accuracy,
            "relevance_score": self.relevance_score,
            "query_response_time": self.query_response_time,
            "status": self.status,
        }
