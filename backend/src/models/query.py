from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Query:
    """Model representing a user query."""

    query_text: str
    query_type: str = "mixed"
    expected_topic: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        return {
            "query_text": self.query_text,
            "query_type": self.query_type,
            "expected_topic": self.expected_topic,
            "created_at": self.created_at.isoformat(),
        }
