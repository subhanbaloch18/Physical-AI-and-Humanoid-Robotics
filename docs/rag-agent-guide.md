# RAG Agent Guide

This guide provides information on how to use the RAG (Retrieval-Augmented Generation) agent that integrates OpenAI and Qdrant for contextual responses.

## Overview

The RAG Agent combines OpenAI's language model capabilities with Qdrant vector database to provide contextually-aware responses to user queries. The system retrieves relevant information from stored documents and generates responses based on both the retrieved context and the LLM's reasoning abilities.

## Architecture

The system consists of several key components:

- **API Layer**: FastAPI endpoints for handling user queries
- **Agent Layer**: RAG Agent that coordinates retrieval and generation
- **Retrieval Service**: Qdrant integration for context retrieval
- **Generation Service**: OpenAI integration for response generation
- **Authentication**: API key-based authentication

## API Usage

### Query Endpoint

Submit a query to the RAG agent:

```bash
curl -X POST "http://localhost:8000/v1/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "query": "What are the key concepts in machine learning?",
    "user_id": "optional-user-id",
    "metadata": {
      "source": "web_app",
      "priority": "high"
    }
  }'
```

### Response Format

The API returns a response in the following format:

```json
{
  "response_id": "resp_1703845234_12345",
  "query": "What are the key concepts in machine learning?",
  "answer": "The key concepts in machine learning include supervised learning, unsupervised learning, neural networks...",
  "sources": [
    {
      "chunk_id": "chunk_abc123",
      "content": "Machine learning is a field of artificial intelligence that uses algorithms to learn from data...",
      "source_url": "https://example.com/ml-intro#section-3",
      "document_title": "Introduction to Machine Learning",
      "section_id": "section-3",
      "similarity_score": 0.92
    }
  ],
  "confidence_score": 0.85,
  "processing_time": 2.45,
  "created_at": 1703845234
}
```

## Configuration

### Environment Variables

The application requires the following environment variables:

```env
OPENAI_API_KEY=your-openai-api-key
QDRANT_URL=your-qdrant-url
QDRANT_API_KEY=your-qdrant-api-key
QDRANT_COLLECTION_NAME=your-collection-name
API_KEY=your-api-key-for-authentication
TOP_K=5
SIMILARITY_THRESHOLD=0.5
```

### Settings

The application uses a settings model that can be customized:

- `top_k`: Number of context chunks to retrieve (default: 5)
- `similarity_threshold`: Minimum similarity score for relevance (default: 0.5)
- `max_tokens`: Maximum tokens for response generation (default: 1000)
- `temperature`: Creativity parameter for OpenAI (default: 0.7)

## Testing

### Unit Tests

Run unit tests for the core components:

```bash
pytest tests/unit/
```

### Integration Tests

Run integration tests to verify the complete flow:

```bash
pytest tests/integration/
```

### API Tests

Test the API endpoints:

```bash
pytest tests/api/
```

## Deployment

### Requirements

- Python 3.11+
- OpenAI API access
- Qdrant vector database access
- Dependencies from pyproject.toml

### Running the Application

Start the FastAPI application:

```bash
uvicorn backend.src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker (Optional)

To containerize the application:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/pyproject.toml .
RUN pip install poetry && poetry export -f requirements.txt --output requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "backend.src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Security

### Authentication

The API uses API key authentication. All requests must include the API key in the Authorization header:

```
Authorization: Bearer YOUR_API_KEY
```

### Rate Limiting

The system implements rate limiting to prevent abuse. Monitor your usage to ensure compliance with API limits.

## Troubleshooting

### Common Issues

1. **Qdrant Connection Issues**: Verify that the QDRANT_URL and QDRANT_API_KEY are correctly set
2. **OpenAI API Errors**: Check that the OPENAI_API_KEY is valid and has sufficient quota
3. **Authentication Failures**: Ensure the API_KEY is included in requests
4. **Empty Results**: Verify that documents are properly indexed in Qdrant

### Logs

Check the application logs for error details:

```
# Standard output
INFO:     Uvicorn running on http://0.0.0.0:8000

# Application logs
rag_agent.services.retrieval: INFO: Retrieved 3 context chunks for query: What is ML?
```

## Performance

### Optimization Tips

1. **Indexing**: Ensure documents are properly chunked and indexed in Qdrant
2. **Caching**: Implement caching for frequent queries
3. **Concurrent Requests**: The system can handle multiple concurrent requests
4. **Embedding Size**: Use appropriate embedding dimensions for your use case

### Monitoring

Monitor the following metrics:

- Query response time
- Context retrieval success rate
- API error rates
- Resource utilization

## Extending the System

### Adding New Document Types

To support new document types, extend the indexing process to convert them to embeddings and store them in Qdrant.

### Custom Prompts

Modify the system prompts in the RAG agent to customize response behavior for your specific use case.

### Additional Tools

The agent architecture supports adding additional tools for extended functionality beyond context retrieval.