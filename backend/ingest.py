"""
Ingest book chapters into Qdrant vector database.
Reads all markdown files from docs/, chunks them, embeds with Cohere,
and uploads to Qdrant.
"""

import json
import os
import re
import time
import uuid
import hashlib
from pathlib import Path
from dotenv import load_dotenv
import requests

# Load .env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_HOST = os.getenv("PINECONE_HOST", "").rstrip("/")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

DOCS_DIR = Path(__file__).resolve().parent.parent / "my-website" / "docs"
CHUNK_SIZE = 500  # words per chunk
CHUNK_OVERLAP = 50  # overlapping words
EMBEDDING_DIM = 1024  # Cohere embed-english-v3.0 dimension
BATCH_SIZE = 96  # Cohere max batch size


def parse_markdown(file_path: Path) -> dict:
    """Parse a markdown file, extract frontmatter and content."""
    text = file_path.read_text(encoding="utf-8")

    # Extract frontmatter
    title = file_path.stem
    sidebar_position = 0
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            frontmatter = text[3:end].strip()
            for line in frontmatter.split("\n"):
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("sidebar_position:"):
                    sidebar_position = int(line.split(":", 1)[1].strip())
            text = text[end + 3:].strip()

    # Clean markdown - remove HTML tags but keep text
    text = re.sub(r'<[^>]+>', '', text)
    # Remove image references
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Convert links to just text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    return {
        "title": title,
        "content": text,
        "file_name": file_path.name,
        "sidebar_position": sidebar_position,
    }


def chunk_text(text: str, title: str, file_name: str, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> list:
    """Split text into overlapping chunks by section headers."""
    chunks = []

    # Split by headers (## or ###)
    sections = re.split(r'\n(#{2,3}\s+.+)', text)

    current_section = "Introduction"
    current_text = ""

    for part in sections:
        if re.match(r'^#{2,3}\s+', part):
            # This is a header - save previous section if it has content
            if current_text.strip():
                section_chunks = split_by_words(current_text.strip(), title, file_name, current_section, chunk_size, overlap)
                chunks.extend(section_chunks)
            current_section = part.strip('#').strip()
            current_text = ""
        else:
            current_text += part

    # Don't forget the last section
    if current_text.strip():
        section_chunks = split_by_words(current_text.strip(), title, file_name, current_section, chunk_size, overlap)
        chunks.extend(section_chunks)

    return chunks


def split_by_words(text: str, title: str, file_name: str, section: str, chunk_size: int, overlap: int) -> list:
    """Split text into word-based chunks with overlap."""
    words = text.split()
    chunks = []

    if len(words) <= chunk_size:
        chunks.append({
            "text": text,
            "title": title,
            "file_name": file_name,
            "section": section,
            "chunk_index": 0,
        })
        return chunks

    i = 0
    idx = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)
        chunks.append({
            "text": chunk_text,
            "title": title,
            "file_name": file_name,
            "section": section,
            "chunk_index": idx,
        })
        i += chunk_size - overlap
        idx += 1

    return chunks


def embed_texts(texts: list) -> list:
    """Embed a batch of texts using Cohere API."""
    resp = requests.post(
        "https://api.cohere.ai/v1/embed",
        headers={
            "Authorization": f"Bearer {COHERE_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "texts": texts,
            "model": "embed-english-v3.0",
            "input_type": "search_document",
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"]


def validate_pinecone():
    """Validate connection to Pinecone index."""
    resp = requests.get(
        f"{PINECONE_HOST}/describe_index_stats",
        headers={"Api-Key": PINECONE_API_KEY},
        timeout=10,
    )
    resp.raise_for_status()
    stats = resp.json()
    total = stats.get("totalVectorCount", 0)
    print(f"Pinecone index reachable. Current vector count: {total}")
    return True


def upload_to_pinecone(chunks: list, embeddings: list):
    """Upload embedded chunks to Pinecone."""
    vectors = []
    for chunk, embedding in zip(chunks, embeddings):
        # Generate a deterministic ID from content
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["text"][:200]))
        vectors.append({
            "id": point_id,
            "values": embedding,
            "metadata": {
                "text": chunk["text"],
                "title": chunk["title"],
                "section": chunk["section"],
                "file_name": chunk["file_name"],
                "chunk_index": chunk["chunk_index"],
                "url": f"/docs/{chunk['file_name'].replace('.md', '')}",
            }
        })

    # Upload in batches of 100
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        resp = requests.post(
            f"{PINECONE_HOST}/vectors/upsert",
            headers={
                "Api-Key": PINECONE_API_KEY,
                "Content-Type": "application/json",
            },
            json={"vectors": batch, "namespace": ""},
            timeout=30,
        )
        resp.raise_for_status()
        print(f"  Uploaded batch {i // batch_size + 1} ({len(batch)} vectors)")


def main():
    print("=" * 60)
    print("RAG Book Ingestion Pipeline")
    print("=" * 60)

    # Check config
    if not PINECONE_API_KEY:
        print("ERROR: PINECONE_API_KEY not set!")
        return
    if not PINECONE_HOST:
        print("ERROR: PINECONE_HOST not set!")
        return
    if not COHERE_API_KEY:
        print("ERROR: COHERE_API_KEY not set!")
        return

    print(f"Pinecone Host: {PINECONE_HOST[:60]}...")
    print(f"Docs dir: {DOCS_DIR}")
    print()

    # Step 1: Validate Pinecone connection
    print("[1/4] Checking Pinecone index...")
    try:
        validate_pinecone()
    except Exception as e:
        print(f"ERROR connecting to Pinecone: {e}")
        print("Make sure your Pinecone index is created at https://app.pinecone.io")
        return

    # Step 2: Parse all markdown files
    print("\n[2/4] Parsing markdown files...")
    md_files = sorted(DOCS_DIR.glob("*.md"))
    all_chunks = []

    for md_file in md_files:
        doc = parse_markdown(md_file)
        chunks = chunk_text(doc["content"], doc["title"], doc["file_name"])
        all_chunks.extend(chunks)
        print(f"  {md_file.name}: {len(chunks)} chunks")

    print(f"\nTotal chunks: {len(all_chunks)}")

    if not all_chunks:
        print("No chunks to process!")
        return

    # Step 3: Embed all chunks with Cohere
    print("\n[3/4] Embedding chunks with Cohere...")
    all_embeddings = []
    texts = [c["text"] for c in all_chunks]

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        print(f"  Embedding batch {i // BATCH_SIZE + 1}/{(len(texts) + BATCH_SIZE - 1) // BATCH_SIZE} ({len(batch)} texts)...")
        embeddings = embed_texts(batch)
        all_embeddings.extend(embeddings)
        time.sleep(0.5)  # Rate limit courtesy

    print(f"  Generated {len(all_embeddings)} embeddings")

    # Step 4: Upload to Pinecone
    print("\n[4/4] Uploading to Pinecone...")
    upload_to_pinecone(all_chunks, all_embeddings)

    print(f"\nDone! Ingested {len(all_chunks)} chunks into Pinecone.")
    print("Your RAG agent should now be able to answer questions about the book!")


if __name__ == "__main__":
    main()
