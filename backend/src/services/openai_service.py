import logging
from typing import List, Dict, Any
from openai import OpenAI
from ..config.settings import settings
from ..models.chunk import Chunk


class OpenAIService:
    """Service for interacting with OpenAI API."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    def generate_response(
        self,
        query: str,
        context_chunks: List[Chunk],
        system_prompt: str,
        query_mode: str = None,
    ) -> Dict[str, Any]:
        """Generate a response using OpenAI with the retrieved context."""
        try:
            # Build context text
            context_parts = []
            for i, chunk in enumerate(context_chunks):
                context_parts.append(
                    f"[Source {i + 1}: {chunk.document_title}]\n{chunk.content}"
                )

            context_text = (
                "\n\n---\n\n".join(context_parts)
                if context_parts
                else "No relevant context found."
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Context from documentation:\n\n{context_text}\n\n"
                        f"User Question: {query}\n\n"
                        "Please answer based on the provided context."
                    ),
                },
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
            )

            answer = response.choices[0].message.content
            similarity_scores = [c.similarity_score for c in context_chunks]

            return {
                "answer": answer,
                "similarity_scores": similarity_scores,
                "relevance_score": (
                    sum(similarity_scores) / len(similarity_scores)
                    if similarity_scores
                    else 0.0
                ),
                "status": "success",
            }

        except Exception as e:
            self.logger.error(f"OpenAI generation error: {e}")
            return {
                "answer": f"Error generating response: {str(e)}",
                "similarity_scores": [],
                "relevance_score": 0.0,
                "status": "failed",
            }
