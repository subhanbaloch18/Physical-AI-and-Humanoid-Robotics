from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Chunk:
    """Model representing a text chunk retrieved from the vector database."""

    chunk_id: str
    content: str
    source_url: str = ""
    section_id: str = ""
    document_title: str = ""
    similarity_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def has_valid_source(self) -> bool:
        """Check if the chunk has valid source metadata."""
        return bool(self.source_url and self.document_title)

    def to_dict(self):
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "source_url": self.source_url,
            "section_id": self.section_id,
            "document_title": self.document_title,
            "similarity_score": self.similarity_score,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
