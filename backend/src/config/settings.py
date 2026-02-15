import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend directory regardless of working directory
_backend_dir = Path(__file__).resolve().parent.parent.parent
_env_path = _backend_dir / ".env"
load_dotenv(_env_path)


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL", "")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
        self.qdrant_collection_name = os.getenv("QDRANT_COLLECTION_NAME", "rag_embedding")
        self.cohere_api_key = os.getenv("COHERE_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.api_key = os.getenv("API_KEY", "")
        self.top_k = int(os.getenv("TOP_K", "5"))
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        self.max_chunks_for_full_book = int(os.getenv("MAX_CHUNKS_FULL_BOOK", "15"))
        self.target_url = os.getenv("TARGET_URL", "")


settings = Settings()
