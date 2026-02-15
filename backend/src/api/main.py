"""FastAPI application for the RAG Agent backend (local development)."""

import logging
import time
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..services.chat_service import ChatService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RAG Agent API",
    description="RAG Agent with OpenAI and Qdrant integration",
    version="1.0.0",
)

# CORS - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chat service
chat_service = ChatService()


class QueryRequest(BaseModel):
    """Request model for queries."""
    query: str = Field(..., min_length=1, max_length=2000)
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    selected_text_context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    query_type: Optional[str] = "mixed"
    query_mode: Optional[str] = "standard"


@app.get("/")
async def root():
    return {"message": "RAG Agent API", "status": "running"}


@app.get("/health")
async def health():
    health_info = chat_service.get_service_health()
    return health_info


@app.post("/v1/query")
async def query(request: QueryRequest):
    """Process a user query through the RAG pipeline."""
    start_time = time.time()

    try:
        result = chat_service.process_query(
            query_text=request.query,
            session_id=request.session_id,
            selected_text_context=request.selected_text_context,
            query_type=request.query_type,
            query_mode=request.query_mode,
        )

        processing_time = time.time() - start_time

        # Build sources from retrieved chunks
        sources = []
        for chunk in result.retrieved_chunks:
            sources.append({
                "chunk_id": chunk.chunk_id,
                "content": chunk.content[:200],
                "source_url": chunk.source_url,
                "document_title": chunk.document_title,
                "section_id": chunk.section_id,
                "similarity_score": chunk.similarity_score,
            })

        return {
            "response_id": result.validation_id,
            "query": request.query,
            "answer": result.answer_text if result.answer_text else "No response generated.",
            "sources": sources,
            "confidence_score": result.relevance_score,
            "processing_time": processing_time,
            "created_at": int(time.time()),
        }

    except Exception as e:
        logger.error(f"Query processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/agent/info")
async def agent_info():
    """Get agent configuration information."""
    return chat_service.get_agent_info()
