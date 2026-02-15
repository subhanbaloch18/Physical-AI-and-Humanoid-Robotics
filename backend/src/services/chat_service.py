from typing import List, Dict, Any, Optional
import logging
import time
from datetime import datetime
from ..models.query import Query as QueryModel
from ..models.chunk import Chunk
from ..models.validation_result import ValidationResult
from .qdrant_service import QdrantService
from .openai_service import OpenAIService
from .retrieval_service import RetrievalService
from ..config.settings import settings


class ChatService:
    """
    Service class to handle chat-related operations for the RAG agent.
    Manages conversation context, processes queries with context awareness,
    and orchestrates the response generation process.
    """

    def __init__(self):
        """
        Initialize the chat service with required dependencies.
        """
        self.qdrant_service = QdrantService()
        self.openai_service = OpenAIService()
        self.retrieval_service = RetrievalService()
        self.logger = logging.getLogger(__name__)

    def process_query(
        self,
        query_text: str,
        session_id: Optional[str] = None,
        selected_text_context: Optional[Dict[str, Any]] = None,
        query_type: Optional[str] = None,
        query_mode: Optional[str] = None
    ) -> ValidationResult:
        """
        Process a user query by retrieving relevant context and generating a response.

        Args:
            query_text: The user's query text
            session_id: Optional session ID for maintaining conversation context
            selected_text_context: Optional context from selected text on the page
            query_type: Optional query type (factual, conceptual, procedural, mixed)
            query_mode: Optional query mode ('standard', 'full-book', 'contextual')

        Returns:
            ValidationResult containing the generated response and metadata
        """
        start_time = time.time()
        query_id = f"query_{int(time.time())}_{hash(query_text) % 10000}"

        self.logger.info(f"Processing query {query_id}: {query_text[:50]}...")

        try:
            # Prepare the query model
            query = QueryModel(
                query_text=query_text,
                query_type=query_type or "mixed",
                expected_topic=None,  # Will be inferred if possible
                created_at=datetime.utcnow()
            )

            # Retrieve context based on query mode
            context_chunks = self._retrieve_context_by_mode(
                query_text=query_text,
                selected_text_context=selected_text_context,
                query_mode=query_mode
            )

            # Generate response using OpenAI with the retrieved context
            response_data = self.openai_service.generate_response(
                query=query_text,
                context_chunks=context_chunks,
                system_prompt=self._get_system_prompt(query_type, selected_text_context, query_mode),
                query_mode=query_mode  # Pass query mode to influence response generation
            )

            # Calculate processing time
            processing_time = time.time() - start_time

            # Calculate confidence score based on similarity scores and context relevance
            confidence_score = self._calculate_confidence_score(
                response_data.get('similarity_scores', []),
                context_chunks
            )

            # Create and return the validation result
            result = ValidationResult(
                validation_id=f"val_{int(time.time())}_{hash(query_text) % 10000}",
                query=query,
                retrieved_chunks=context_chunks,
                similarity_scores=response_data.get('similarity_scores', []),
                metadata_accuracy=self._calculate_metadata_accuracy(context_chunks),
                relevance_score=response_data.get('relevance_score', 0.0),
                query_response_time=processing_time,
                status=response_data.get('status', 'success'),
                answer_text=response_data.get('answer', '')
            )

            self.logger.info(f"Query {query_id} processed successfully in {processing_time:.2f}s")
            return result

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Error processing query {query_id}: {str(e)}")

            # Return a failed validation result
            query = QueryModel(
                query_text=query_text,
                query_type=query_type or "mixed",
                expected_topic=None,
                created_at=datetime.utcnow()
            )

            return ValidationResult(
                validation_id=f"val_error_{int(time.time())}",
                query=query,
                retrieved_chunks=[],
                similarity_scores=[],
                metadata_accuracy=0.0,
                relevance_score=0.0,
                query_response_time=processing_time,
                status='failed'
            )

    def _retrieve_context_by_mode(
        self,
        query_text: str,
        selected_text_context: Optional[Dict[str, Any]] = None,
        query_mode: Optional[str] = None
    ) -> List[Chunk]:
        """
        Retrieve context based on the specified query mode.

        Args:
            query_text: The user's query
            selected_text_context: Optional context from selected text
            query_mode: The query mode ('standard', 'full-book', 'contextual')

        Returns:
            List of Chunk objects containing relevant context
        """
        # Determine the number of chunks to retrieve based on mode
        if query_mode == 'full-book':
            # For full-book queries, retrieve more context to synthesize information
            top_k = min(settings.top_k * 2, settings.max_chunks_for_full_book)
        else:
            top_k = settings.top_k

        # If selected text context is provided and we're not in full-book mode, prioritize it
        if selected_text_context and selected_text_context.get('content') and query_mode != 'full-book':
            # Create a chunk from the selected text
            selected_chunk = Chunk(
                chunk_id=f"selected_{int(time.time())}",
                content=selected_text_context['content'],
                source_url=selected_text_context.get('source_url', ''),
                section_id=selected_text_context.get('section_id', ''),
                document_title=selected_text_context.get('document_title', ''),
                similarity_score=1.0,  # High score since this was explicitly selected
                metadata=selected_text_context.get('metadata', {}),
                created_at=datetime.utcnow()
            )

            # If selected text is highly relevant to the query, return just that
            if self._is_selected_text_highly_relevant(query_text, selected_text_context['content']):
                return [selected_chunk]

            # Otherwise, combine with general context retrieval
            general_chunks = self.retrieval_service.retrieve_context(
                query_text=query_text,
                top_k=top_k - 1  # Leave room for selected text
            )

            # Combine selected text with general context
            return [selected_chunk] + general_chunks

        else:
            # For full-book mode or when no selected text, retrieve broader context
            if query_mode == 'full-book':
                # In full-book mode, we want to retrieve context that covers a broader range of the book
                # This might involve different retrieval strategies to get more diverse content
                chunks = self.retrieval_service.retrieve_context(
                    query_text=query_text,
                    top_k=top_k,
                    include_diverse_content=True  # This would be a new parameter
                )

                # For full-book queries, we might also want to include broader context
                # by retrieving chunks that are more diverse in terms of topics/sections
                return chunks
            else:
                # Standard retrieval
                return self.retrieval_service.retrieve_context(
                    query_text=query_text,
                    top_k=top_k
                )

    def _retrieve_context_with_selected_text(
        self,
        query_text: str,
        selected_text_context: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Retrieve context considering both the query and any selected text context (legacy method).

        Args:
            query_text: The user's query
            selected_text_context: Optional context from selected text

        Returns:
            List of Chunk objects containing relevant context
        """
        # This is now a wrapper that calls the new method with standard mode
        return self._retrieve_context_by_mode(
            query_text=query_text,
            selected_text_context=selected_text_context,
            query_mode='standard'
        )

    def _is_selected_text_highly_relevant(self, query: str, selected_text: str) -> bool:
        """
        Determine if the selected text is highly relevant to the query.

        Args:
            query: The user's query
            selected_text: The selected text content

        Returns:
            True if the selected text is highly relevant to the query
        """
        query_lower = query.lower()
        text_lower = selected_text.lower()

        # Check for keyword overlap
        query_words = set(query_lower.split())
        text_words = set(text_lower.split())

        # Calculate overlap ratio
        common_words = query_words.intersection(text_words)
        if len(common_words) == 0:
            return False

        overlap_ratio = len(common_words) / max(len(query_words), 1)
        return overlap_ratio > 0.3  # Consider highly relevant if >30% overlap

    def _get_system_prompt(self, query_type: Optional[str], selected_text_context: Optional[Dict[str, Any]], query_mode: Optional[str] = None) -> str:
        """
        Generate an appropriate system prompt based on query type, context, and mode.

        Args:
            query_type: The type of query (factual, conceptual, procedural, mixed)
            selected_text_context: Optional context from selected text
            query_mode: Optional query mode ('standard', 'full-book', 'contextual')

        Returns:
            Appropriate system prompt for the query
        """
        base_prompt = "You are a helpful AI assistant. Use the provided context to answer the user's question accurately."

        if selected_text_context and selected_text_context.get('content'):
            context_specific = f" The user has selected specific text on the page: '{selected_text_context['content'][:200]}...' Use this selected text as primary context when answering."
            base_prompt += context_specific

        # Add query mode instructions
        if query_mode == 'full-book':
            base_prompt += " For this full-book query, synthesize information across multiple sections of the book to provide comprehensive answers that may draw from various parts of the content."
        elif query_mode == 'contextual':
            base_prompt += " Use the provided context carefully, focusing on the specific context that's most relevant to the query."

        if query_type:
            if query_type == 'factual':
                base_prompt += " Provide specific facts and details from the context."
            elif query_type == 'conceptual':
                base_prompt += " Explain concepts and principles using the context."
            elif query_type == 'procedural':
                base_prompt += " Provide step-by-step instructions or processes based on the context."

        base_prompt += " If the context doesn't contain relevant information, acknowledge this limitation and provide the best answer you can based on general knowledge."

        return base_prompt

    def _calculate_confidence_score(
        self,
        similarity_scores: List[float],
        context_chunks: List[Chunk]
    ) -> float:
        """
        Calculate a confidence score based on similarity scores and context quality.

        Args:
            similarity_scores: List of similarity scores for retrieved chunks
            context_chunks: List of context chunks

        Returns:
            Confidence score between 0 and 1
        """
        if not similarity_scores:
            return 0.0

        # Calculate average similarity score
        avg_similarity = sum(similarity_scores) / len(similarity_scores)

        # Calculate context quality based on metadata completeness
        if context_chunks:
            valid_metadata_chunks = sum(1 for chunk in context_chunks if chunk.has_valid_source())
            metadata_quality = valid_metadata_chunks / len(context_chunks)
        else:
            metadata_quality = 0.0

        # Combine scores (weighted average)
        confidence = (0.7 * avg_similarity) + (0.3 * metadata_quality)

        return min(confidence, 1.0)  # Ensure it doesn't exceed 1.0

    def _calculate_metadata_accuracy(self, chunks: List[Chunk]) -> float:
        """
        Calculate the percentage of chunks with valid metadata.

        Args:
            chunks: List of context chunks

        Returns:
            Metadata accuracy score between 0 and 1
        """
        if not chunks:
            return 0.0

        valid_chunks = sum(1 for chunk in chunks if chunk.has_valid_source())
        return valid_chunks / len(chunks)

    def create_session(self) -> Dict[str, Any]:
        """
        Create a new chat session.

        Returns:
            Dictionary with session information
        """
        session_id = f"sess_{int(time.time())}_{hash(str(time.time())) % 10000}"

        session_info = {
            "session_id": session_id,
            "created_at": time.time(),
            "status": "active",
            "message_count": 0
        }

        self.logger.info(f"Created new session: {session_id}")
        return session_info

    def validate_session(self, session_id: str) -> bool:
        """
        Validate if a session is still active.

        Args:
            session_id: The session ID to validate

        Returns:
            True if the session is valid, False otherwise
        """
        # In a real implementation, this would check against a database or cache
        # For now, we'll just validate the format
        if not session_id or not isinstance(session_id, str):
            return False

        # Basic validation: session ID should start with 'sess_'
        return session_id.startswith('sess_')

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get the message history for a session.

        Args:
            session_id: The session ID

        Returns:
            List of messages in the session
        """
        # In a real implementation, this would fetch from a database or cache
        # For now, return an empty list
        self.logger.warning(f"Session history requested for {session_id}, but no persistence implemented")
        return []

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session.

        Args:
            session_id: The session ID to delete

        Returns:
            True if the session was deleted successfully, False otherwise
        """
        # In a real implementation, this would remove from a database or cache
        # For now, just log and return True
        self.logger.info(f"Session {session_id} marked for deletion")
        return True

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about the chat agent configuration.

        Returns:
            Dictionary with agent configuration information
        """
        return {
            "model": settings.openai_model,
            "top_k": settings.top_k,
            "similarity_threshold": settings.similarity_threshold,
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature
        }

    def validate_connection(self) -> bool:
        """
        Validate the connection to all required services.

        Returns:
            True if all connections are successful, False otherwise
        """
        try:
            # Check Qdrant connection
            qdrant_ok = self.qdrant_service.validate_connection()

            # Check OpenAI service (no external connection needed)
            openai_ok = True  # OpenAI service doesn't require separate connection validation

            return qdrant_ok and openai_ok
        except Exception as e:
            self.logger.error(f"Connection validation failed: {str(e)}")
            return False

    def get_service_health(self) -> Dict[str, Any]:
        """
        Get detailed health information about the service and its dependencies.

        Returns:
            Dictionary with detailed health information
        """
        qdrant_ok = self.qdrant_service.validate_connection()

        return {
            "status": "healthy" if qdrant_ok else "unhealthy",
            "timestamp": time.time(),
            "services": {
                "qdrant": "connected" if qdrant_ok else "disconnected",
                "openai": "ready",  # Always ready since it's called on demand
            },
            "performance": {
                "avg_response_time": getattr(self, '_avg_response_time', 0.0),
                "requests_per_minute": getattr(self, '_requests_per_minute', 0)
            }
        }

    def get_query_statistics(self, query: str) -> Dict[str, Any]:
        """
        Get statistics about a query (for analysis and improvement).

        Args:
            query: The query to analyze

        Returns:
            Dictionary with query statistics
        """
        # Analyze query characteristics
        words = query.split()
        char_count = len(query)
        word_count = len(words)

        # Detect query type
        query_type = self._detect_query_type(query)

        return {
            "character_count": char_count,
            "word_count": word_count,
            "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
            "query_type": query_type,
            "has_question_mark": "?" in query,
            "starts_with_wh_word": query.lower().startswith(("what", "when", "where", "who", "why", "how", "which", "whose"))
        }

    def _detect_query_type(self, query: str) -> str:
        """
        Detect the likely type of query based on its content.

        Args:
            query: The query text

        Returns:
            Detected query type (factual, conceptual, procedural, mixed)
        """
        query_lower = query.lower()

        # Factual indicators
        factual_indicators = [
            "what is", "what are", "when", "where", "who", "how many", "define",
            "explain", "name", "list", "identify", "state", "enumerate"
        ]

        # Conceptual indicators
        conceptual_indicators = [
            "why", "how does", "what causes", "what means", "what implies",
            "what represents", "what constitutes", "what defines", "what characterizes",
            "what distinguishes", "what differentiates", "what is the principle"
        ]

        # Procedural indicators
        procedural_indicators = [
            "how to", "how do", "steps to", "process for", "procedure for",
            "method for", "way to", "technique for", "approach for", "implement",
            "create", "build", "develop", "design", "construct", "execute"
        ]

        # Count matches for each type
        factual_matches = sum(1 for indicator in factual_indicators if indicator in query_lower)
        conceptual_matches = sum(1 for indicator in conceptual_indicators if indicator in query_lower)
        procedural_matches = sum(1 for indicator in procedural_indicators if indicator in query_lower)

        # Determine the most likely type
        max_matches = max(factual_matches, conceptual_matches, procedural_matches)

        if max_matches == 0:
            return "mixed"
        elif max_matches == factual_matches:
            return "factual"
        elif max_matches == conceptual_matches:
            return "conceptual"
        else:
            return "procedural"