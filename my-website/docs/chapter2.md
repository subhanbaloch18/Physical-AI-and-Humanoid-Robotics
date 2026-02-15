---
sidebar_position: 3
sidebar_label: "Chapter 2: Setting Up Your Environment"
---

# Chapter 2: Setting Up Your Environment

## Overview

Before diving into AI-driven content generation, you need a properly configured development environment. This chapter walks you through installing and configuring all the tools, frameworks, and services required for the AI authorship pipeline.

---

## Prerequisites

Before starting, ensure you have:

| Requirement | Minimum Version | Purpose |
|-------------|----------------|---------|
| **Node.js** | v18+ | Running Docusaurus and frontend tools |
| **Python** | 3.10+ | Backend services and AI pipeline |
| **Git** | 2.30+ | Version control |
| **npm or yarn** | Latest | Package management |

---

## Step 1: Project Structure Setup

Create the project directory structure:

```bash
mkdir physical-ai-book && cd physical-ai-book
```

The recommended project structure:

```
physical-ai-book/
├── my-website/          # Docusaurus frontend
│   ├── docs/            # Markdown documentation
│   ├── src/             # React components
│   │   ├── components/  # Reusable components (ChatBot, etc.)
│   │   ├── css/         # Global styles
│   │   └── pages/       # Custom pages
│   ├── static/          # Static assets
│   └── docusaurus.config.js
├── backend/             # Python backend
│   ├── src/
│   │   ├── api/         # FastAPI routes
│   │   ├── config/      # Configuration management
│   │   ├── models/      # Data models
│   │   └── services/    # Business logic
│   ├── main.py          # Entry point
│   └── .env             # Environment variables
├── api/                 # Vercel serverless functions
│   ├── query.py         # RAG query endpoint
│   └── requirements.txt
└── vercel.json          # Deployment config
```

---

## Step 2: Frontend Setup (Docusaurus)

### Initialize Docusaurus

```bash
npx create-docusaurus@latest my-website classic
cd my-website
npm install
```

### Configure Docusaurus

Edit `docusaurus.config.js` with your project settings:

- **Site metadata**: Title, tagline, URL
- **Navbar**: Navigation links for docs, chapters, and RAG chat
- **Footer**: Quick links and copyright
- **Theme**: Custom CSS with your color palette

### Install Additional Dependencies

```bash
npm install react@19 react-dom@19
```

---

## Step 3: Backend Setup (Python FastAPI)

### Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows
```

### Install Python Dependencies

```bash
pip install fastapi uvicorn python-dotenv
pip install cohere openai qdrant-client
pip install pydantic aiohttp
```

### Environment Variables

Create a `.env` file in the backend directory:

```env
# API Keys
OPENAI_API_KEY=your-openai-api-key
COHERE_API_KEY=your-cohere-api-key

# Qdrant Configuration
QDRANT_URL=your-qdrant-cloud-url
QDRANT_API_KEY=your-qdrant-api-key
QDRANT_COLLECTION_NAME=book_embeddings

# Model Configuration
OPENAI_MODEL=gpt-4
COHERE_EMBED_MODEL=embed-english-v3.0
EMBEDDING_DIMENSION=1024
TOP_K=5
SIMILARITY_THRESHOLD=0.7
MAX_TOKENS=2048
TEMPERATURE=0.7
```

:::caution Important
Never commit your `.env` file to version control. Add it to `.gitignore` to protect your API keys.
:::

---

## Step 4: Vector Database Setup (Qdrant)

### Option A: Qdrant Cloud (Recommended)

1. Sign up at [cloud.qdrant.io](https://cloud.qdrant.io)
2. Create a new cluster (free tier available)
3. Note your cluster URL and API key
4. Create a collection with 1024-dimensional vectors

### Option B: Local Qdrant

```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

### Verify Connection

```python
from qdrant_client import QdrantClient

client = QdrantClient(
    url="your-qdrant-url",
    api_key="your-api-key"
)

# Check connection
collections = client.get_collections()
print(f"Connected! Collections: {collections}")
```

---

## Step 5: AI Service Configuration

### OpenAI Setup

1. Create an account at [platform.openai.com](https://platform.openai.com)
2. Generate an API key
3. Add to your `.env` file

### Cohere Setup

1. Sign up at [dashboard.cohere.com](https://dashboard.cohere.com)
2. Generate an API key
3. Add to your `.env` file

### Testing the Services

```python
import cohere
import openai

# Test Cohere embeddings
co = cohere.Client("your-cohere-key")
response = co.embed(
    texts=["Test embedding"],
    model="embed-english-v3.0",
    input_type="search_document"
)
print(f"Embedding dimension: {len(response.embeddings[0])}")

# Test OpenAI generation
client = openai.OpenAI(api_key="your-openai-key")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(f"Response: {response.choices[0].message.content}")
```

---

## Step 6: Deployment Configuration (Vercel)

### Install Vercel CLI

```bash
npm i -g vercel
```

### Configure `vercel.json`

```json
{
  "buildCommand": "cd my-website && npm install && npm run build",
  "outputDirectory": "my-website/build",
  "functions": {
    "api/*.py": {
      "runtime": "@vercel/python@4.5.0",
      "maxDuration": 60
    }
  }
}
```

### Set Environment Variables on Vercel

```bash
vercel env add OPENAI_API_KEY
vercel env add COHERE_API_KEY
vercel env add QDRANT_URL
vercel env add QDRANT_API_KEY
```

---

## Step 7: Running Locally

### Start the Backend

```bash
cd backend
source venv/bin/activate
uvicorn src.api.main:app --reload --port 8000
```

### Start the Frontend

```bash
cd my-website
npm start
```

Your site should now be running at `http://localhost:3000` with the backend API at `http://localhost:8000`.

---

## Environment Checklist

| Component | Status Check | Command |
|-----------|-------------|---------|
| Node.js | Version 18+ | `node --version` |
| Python | Version 3.10+ | `python --version` |
| Docusaurus | Builds successfully | `npm run build` |
| FastAPI | Starts without errors | `uvicorn src.api.main:app` |
| Qdrant | Connection verified | Python test script |
| OpenAI | API key valid | Test generation call |
| Cohere | API key valid | Test embedding call |

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ERR_MODULE_NOT_FOUND` | Delete `node_modules` and run `npm install` |
| Python import errors | Ensure virtual environment is activated |
| Qdrant connection timeout | Check URL and API key in `.env` |
| CORS errors in browser | Verify CORS middleware is configured in FastAPI |
| Vercel build fails | Check `vercel.json` paths match your structure |

---

## Summary

You now have a complete development environment with:

- A Docusaurus frontend for professional documentation
- A Python FastAPI backend for the RAG pipeline
- Qdrant vector database for semantic search
- OpenAI and Cohere APIs for generation and embeddings
- Vercel deployment configuration for production

> **Next**: In Chapter 3, we'll explore the specification-driven approach to AI content generation.
