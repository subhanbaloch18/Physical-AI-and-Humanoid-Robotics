"""
Lightweight RAG backend server.
Uses only http.server + requests (no FastAPI/pydantic needed).
Compatible with Python 3.15 alpha.
Supports Groq (free) and OpenAI as LLM providers.
"""

import json
import os
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from dotenv import load_dotenv
import requests

# Load .env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

# Config
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION_NAME", "rag_embedding")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

# LLM Provider config (Groq or OpenAI)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

# Pick the right base URL and API key based on provider
if LLM_PROVIDER == "groq":
    LLM_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
    LLM_API_KEY = GROQ_API_KEY
else:
    LLM_BASE_URL = "https://api.openai.com/v1/chat/completions"
    LLM_API_KEY = OPENAI_API_KEY

TOP_K = int(os.getenv("TOP_K", "5"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def embed_query(query: str) -> list:
    """Generate embedding using Cohere API via HTTP."""
    try:
        resp = requests.post(
            "https://api.cohere.ai/v1/embed",
            headers={
                "Authorization": f"Bearer {COHERE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "texts": [query],
                "model": "embed-english-v3.0",
                "input_type": "search_query",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["embeddings"][0]
    except Exception as e:
        logger.error(f"Cohere embedding error: {e}")
        return []


def search_qdrant(query_vector: list, top_k: int = TOP_K) -> list:
    """Search Qdrant vector database via HTTP."""
    try:
        resp = requests.post(
            f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/search",
            headers={
                "api-key": QDRANT_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "vector": query_vector,
                "limit": top_k,
                "score_threshold": SIMILARITY_THRESHOLD,
                "with_payload": True,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("result", [])
        logger.info(f"Qdrant returned {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Qdrant search error: {e}")
        return []


def generate_llm_response(query: str, context_chunks: list, query_type: str = "mixed", query_mode: str = "standard") -> dict:
    """Generate response using Groq or OpenAI API (OpenAI-compatible format)."""
    # Build context text
    context_parts = []
    for i, chunk in enumerate(context_chunks):
        payload = chunk.get("payload", {})
        title = payload.get("title", f"Source {i+1}")
        text = payload.get("text", "")
        context_parts.append(f"[Source {i+1}: {title}]\n{text}")

    context_text = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant context found."

    # Build system prompt
    system_prompt = "You are a helpful AI assistant for a book on Physical AI and Humanoid Robotics. Use the provided context to answer the user's question accurately."

    if query_mode == "full-book":
        system_prompt += " Synthesize information across multiple sections to provide comprehensive answers."
    elif query_mode == "contextual":
        system_prompt += " Focus on the specific context that's most relevant to the query."

    if query_type == "factual":
        system_prompt += " Provide specific facts and details from the context."
    elif query_type == "conceptual":
        system_prompt += " Explain concepts and principles using the context."
    elif query_type == "procedural":
        system_prompt += " Provide step-by-step instructions based on the context."

    system_prompt += " If the context doesn't contain relevant information, acknowledge this and provide the best answer you can."

    try:
        resp = requests.post(
            LLM_BASE_URL,
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Context from documentation:\n\n{context_text}\n\nUser Question: {query}\n\nPlease answer based on the provided context.",
                    },
                ],
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        answer = data["choices"][0]["message"]["content"]
        return {"answer": answer, "status": "success"}
    except requests.exceptions.HTTPError as e:
        error_body = ""
        try:
            error_body = e.response.json().get("error", {}).get("message", str(e))
        except Exception:
            error_body = str(e)
        logger.error(f"LLM API error ({LLM_PROVIDER}): {error_body}")
        return {"answer": f"LLM API error: {error_body}", "status": "failed"}
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return {"answer": f"Error generating response: {str(e)}", "status": "failed"}


class RAGHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the RAG API."""

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            self._send_json({"status": "running", "message": "RAG Agent API", "provider": LLM_PROVIDER, "model": LLM_MODEL})
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        if self.path != "/v1/query":
            self._send_json({"error": "Not found"}, 404)
            return

        start_time = time.time()

        try:
            # Read request body
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length)) if content_length > 0 else {}

            query = body.get("query", "").strip()
            if not query:
                self._send_json({"error": "Query is required"}, 400)
                return

            query_type = body.get("query_type", "mixed")
            query_mode = body.get("query_mode", "standard")

            logger.info(f"Processing query: {query[:80]}... (type={query_type}, mode={query_mode})")

            # Step 1: Embed query with Cohere
            query_embedding = embed_query(query)
            if not query_embedding:
                self._send_json({
                    "answer": "Sorry, I couldn't process your query. The embedding service is unavailable.",
                    "sources": [],
                    "confidence_score": 0,
                    "processing_time": time.time() - start_time,
                }, 200)
                return

            # Step 2: Search Qdrant
            top_k = TOP_K * 2 if query_mode == "full-book" else TOP_K
            qdrant_results = search_qdrant(query_embedding, top_k=top_k)

            # Step 3: Generate response with LLM (Groq/OpenAI)
            response_data = generate_llm_response(query, qdrant_results, query_type, query_mode)

            # Build sources
            sources = []
            for i, result in enumerate(qdrant_results[:5]):
                payload = result.get("payload", {})
                sources.append({
                    "chunk_id": str(result.get("id", i)),
                    "content": payload.get("text", "")[:200],
                    "source_url": payload.get("url", ""),
                    "document_title": payload.get("title", f"Source {i+1}"),
                    "section_id": payload.get("section", ""),
                    "similarity_score": result.get("score", 0),
                })

            # Calculate confidence
            scores = [r.get("score", 0) for r in qdrant_results]
            confidence = sum(scores) / len(scores) if scores else 0

            processing_time = time.time() - start_time
            logger.info(f"Query processed in {processing_time:.2f}s with {len(sources)} sources")

            self._send_json({
                "answer": response_data["answer"],
                "sources": sources,
                "confidence_score": confidence,
                "processing_time": processing_time,
                "created_at": int(time.time()),
            })

        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
        except Exception as e:
            logger.error(f"Request error: {e}")
            self._send_json({
                "answer": f"Server error: {str(e)}",
                "sources": [],
                "confidence_score": 0,
                "processing_time": time.time() - start_time,
            }, 200)

    def log_message(self, format, *args):
        """Suppress default HTTP logging (we use our own logger)."""
        pass


def main():
    port = 8000
    server = HTTPServer(("0.0.0.0", port), RAGHandler)
    logger.info(f"RAG Backend server running on http://localhost:{port}")
    logger.info(f"LLM Provider: {LLM_PROVIDER.upper()}")
    logger.info(f"LLM Model: {LLM_MODEL}")
    logger.info(f"LLM API Key: {'SET' if LLM_API_KEY else 'NOT SET!'}")
    logger.info(f"Qdrant URL: {QDRANT_URL[:50]}...")
    logger.info(f"Collection: {QDRANT_COLLECTION}")
    logger.info(f"Cohere Key: {'SET' if COHERE_API_KEY else 'NOT SET!'}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
        server.server_close()


if __name__ == "__main__":
    main()
