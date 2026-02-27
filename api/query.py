"""
Vercel Serverless Function for RAG Query API.

This function handles POST requests to /api/query and performs:
1. Embeds the user query using Cohere
2. Searches Pinecone vector database for relevant context
3. Generates a response using Groq (or OpenAI) with the retrieved context
"""

import json
import os
import time
from http.server import BaseHTTPRequestHandler

import requests as http_requests


# Config
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")
PINECONE_HOST = os.environ.get("PINECONE_HOST", "").rstrip("/")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY", "")

# LLM Provider (Groq or OpenAI)
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq").lower()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")

if LLM_PROVIDER == "groq":
    LLM_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
    LLM_API_KEY = GROQ_API_KEY
else:
    LLM_BASE_URL = "https://api.openai.com/v1/chat/completions"
    LLM_API_KEY = OPENAI_API_KEY

TOP_K = int(os.environ.get("TOP_K", "8"))
SIMILARITY_THRESHOLD = float(os.environ.get("SIMILARITY_THRESHOLD", "0.25"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "1000"))
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.7"))


def get_system_prompt(query_type=None, selected_text=None, query_mode=None):
    """Generate system prompt based on query parameters."""
    prompt = (
        "You are a helpful AI assistant for a documentation site about Physical AI "
        "and Humanoid Robotics. Use the provided context to answer the user's question "
        "accurately and concisely."
    )

    if selected_text:
        prompt += (
            f" The user has selected specific text: '{selected_text[:200]}...' "
            "Use this as primary context."
        )

    if query_mode == "full-book":
        prompt += (
            " Synthesize information across multiple sections to provide "
            "comprehensive answers."
        )

    if query_type == "factual":
        prompt += " Provide specific facts and details from the context."
    elif query_type == "conceptual":
        prompt += " Explain concepts and principles using the context."
    elif query_type == "procedural":
        prompt += " Provide step-by-step instructions based on the context."

    prompt += (
        " If the context doesn't contain relevant information, acknowledge this "
        "and provide the best answer based on general knowledge. Always be helpful."
    )

    return prompt


def embed_query(query_text):
    """Generate embedding for the query using Cohere HTTP API."""
    resp = http_requests.post(
        "https://api.cohere.ai/v1/embed",
        headers={
            "Authorization": f"Bearer {COHERE_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "texts": [query_text],
            "model": "embed-english-v3.0",
            "input_type": "search_query",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"][0]


def search_pinecone(query_embedding, top_k=None):
    """Search Pinecone for relevant context chunks via HTTP."""
    k = top_k or TOP_K
    resp = http_requests.post(
        f"{PINECONE_HOST}/query",
        headers={
            "Api-Key": PINECONE_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "vector": query_embedding,
            "topK": k,
            "includeMetadata": True,
            "namespace": "",
        },
        timeout=30,
    )
    resp.raise_for_status()
    matches = resp.json().get("matches", [])
    # Apply similarity threshold (Pinecone doesn't filter server-side)
    return [m for m in matches if m.get("score", 0) >= SIMILARITY_THRESHOLD]


def generate_response(query, context_chunks, system_prompt):
    """Generate a response using Groq/OpenAI via HTTP."""
    context_parts = []
    for i, chunk in enumerate(context_chunks):
        payload = chunk.get("metadata", {})
        title = payload.get("title", "Unknown")
        text = payload.get("text", "")
        context_parts.append(f"[Source {i + 1}: {title}]\n{text}")

    context_text = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant context found."

    resp = http_requests.post(
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
                    "content": (
                        f"Context from documentation:\n\n{context_text}\n\n"
                        f"User Question: {query}\n\n"
                        "Please answer based on the provided context."
                    ),
                },
            ],
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        start_time = time.time()

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}

            query = data.get("query", "").strip()
            if not query:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Query is required"}).encode())
                return

            query_type = data.get("query_type", "mixed")
            query_mode = data.get("query_mode", "standard")
            selected_text_context = data.get("selected_text_context")
            selected_text = None
            if selected_text_context and isinstance(selected_text_context, dict):
                selected_text = selected_text_context.get("content", "")

            top_k = TOP_K
            if query_mode == "full-book":
                top_k = min(TOP_K * 2, 15)

            # RAG Pipeline
            query_embedding = embed_query(query)
            search_results = search_pinecone(query_embedding, top_k=top_k)
            system_prompt = get_system_prompt(query_type, selected_text, query_mode)
            answer = generate_response(query, search_results, system_prompt)

            # Build sources (Pinecone uses "metadata" instead of "payload")
            sources = []
            similarity_scores = []
            for result in search_results:
                payload = result.get("metadata", {})
                sources.append({
                    "chunk_id": str(result.get("id", "")),
                    "content": payload.get("text", "")[:200],
                    "source_url": payload.get("url", ""),
                    "document_title": payload.get("title", "Unknown"),
                    "section_id": payload.get("section", ""),
                    "similarity_score": round(result.get("score", 0), 4),
                })
                similarity_scores.append(result.get("score", 0))

            avg_similarity = (
                sum(similarity_scores) / len(similarity_scores)
                if similarity_scores
                else 0
            )
            confidence_score = round(min(avg_similarity * 1.1, 1.0), 4)
            processing_time = round(time.time() - start_time, 3)

            response_data = {
                "response_id": f"resp_{int(time.time())}_{hash(query) % 10000}",
                "query": query,
                "answer": answer,
                "sources": sources,
                "confidence_score": confidence_score,
                "processing_time": processing_time,
                "created_at": int(time.time()),
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        except Exception as e:
            processing_time = round(time.time() - start_time, 3)
            error_response = {
                "error": str(e),
                "detail": f"Failed to process query: {str(e)}",
                "processing_time": processing_time,
            }

            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "healthy",
            "service": "RAG Query API",
            "provider": LLM_PROVIDER,
            "model": LLM_MODEL,
            "timestamp": int(time.time()),
        }).encode())
