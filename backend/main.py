import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import cohere
from qdrant_client import QdrantClient
from qdrant_client.http import models
import os
from dotenv import load_dotenv
import time
import re
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Initialize Cohere client
cohere_api_key = os.getenv("COHERE_API_KEY")
cohere_client = cohere.Client(cohere_api_key)

# Initialize Qdrant client
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key,
)


def get_all_urls(base_url: str, max_pages: int = 100) -> List[str]:
    """
    Crawl the website and extract all unique URLs

    Args:
        base_url: The base URL to start crawling from
        max_pages: Maximum number of pages to crawl

    Returns:
        List of unique URLs found on the website
    """
    urls = set()
    visited = set()
    to_visit = [base_url]

    while to_visit and len(urls) < max_pages:
        current_url = to_visit.pop(0)

        if current_url in visited:
            continue

        visited.add(current_url)

        try:
            # Check if URL is valid and belongs to the same domain
            parsed_base = urlparse(base_url)
            parsed_current = urlparse(current_url)

            if parsed_current.netloc != parsed_base.netloc:
                continue

            response = requests.get(current_url, timeout=10)
            response.raise_for_status()

            # Add the current URL to the set
            urls.add(current_url)

            # Parse HTML to find more links
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all links on the page
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(current_url, href)

                # Only add URLs from the same domain and not already visited
                parsed_href = urlparse(full_url)
                if (parsed_href.netloc == parsed_base.netloc and
                    full_url not in visited and
                    full_url not in to_visit):
                    to_visit.append(full_url)

        except requests.RequestException as e:
            print(f"Error crawling {current_url}: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error crawling {current_url}: {e}")
            continue

    return list(urls)


def extract_text_from_url(url: str) -> Dict[str, Any]:
    """
    Extract clean text content from a given URL

    Args:
        url: The URL to extract text from

    Returns:
        Dictionary containing the extracted text, title, and metadata
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Try to find the main content area
        # Common selectors for Docusaurus content areas
        content_selectors = [
            'main',  # Main content area
            '.main-wrapper',  # Docusaurus main wrapper
            '.container',  # Container
            '.theme-doc-markdown',  # Docusaurus markdown content
            '.markdown',  # Markdown content
            'article',  # Article content
            '.post',  # Post content
            '.content',  # Generic content area
        ]

        text_content = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    text_content += element.get_text(separator=' ', strip=True) + "\n\n"
                break

        # If no specific content area found, get all text
        if not text_content.strip():
            text_content = soup.get_text(separator=' ', strip=True)

        # Clean up the text
        text_content = re.sub(r'\s+', ' ', text_content).strip()

        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else "No Title"

        return {
            "url": url,
            "title": title,
            "text": text_content,
            "content_length": len(text_content)
        }
    except Exception as e:
        print(f"Error extracting text from {url}: {e}")
        return {
            "url": url,
            "title": "Error",
            "text": "",
            "content_length": 0
        }


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks

    Args:
        text: The text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Overlap between chunks in characters

    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # If this is the last chunk, include the remainder
        if end >= len(text):
            end = len(text)
        else:
            # Try to break at sentence boundary if possible
            # Look for sentence endings near the end
            chunk = text[start:end]
            last_sentence_end = max(
                chunk.rfind('.'),
                chunk.rfind('!'),
                chunk.rfind('?'),
                chunk.rfind('\n')
            )

            if last_sentence_end > chunk_size // 2:  # Only break if it's not too early
                end = start + last_sentence_end + 1

        chunks.append(text[start:end])

        # Move start position, considering overlap
        start = end - overlap if end < len(text) else end

        # Prevent infinite loops
        if start >= len(text):
            break

    # Filter out empty chunks
    chunks = [chunk for chunk in chunks if chunk.strip()]

    return chunks


def embed(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using Cohere

    Args:
        texts: List of texts to embed

    Returns:
        List of embedding vectors
    """
    if not texts:
        return []

    try:
        response = cohere_client.embed(
            texts=texts,
            model='embed-english-v3.0',  # Using the English v3 model
            input_type='search_document'  # Specify the input type for better embeddings
        )

        return [embedding for embedding in response.embeddings]
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return [[] for _ in texts]  # Return empty embeddings in case of error


def create_collection(collection_name: str = "rag_embedding"):
    """
    Create a collection in Qdrant Cloud for storing embeddings

    Args:
        collection_name: Name of the collection to create
    """
    try:
        # Check if collection already exists
        collections = qdrant_client.get_collections()
        collection_names = [collection.name for collection in collections.collections]

        if collection_name in collection_names:
            print(f"Collection '{collection_name}' already exists, recreating...")
            qdrant_client.delete_collection(collection_name)

        # Create the collection
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=1024,  # Cohere embed-english-v3.0 produces 1024-dim vectors
                distance=models.Distance.COSINE
            )
        )

        print(f"Collection '{collection_name}' created successfully.")
    except Exception as e:
        print(f"Error creating collection: {e}")
        # Try with a smaller vector size if 1024 fails
        try:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=512,  # Alternative size
                    distance=models.Distance.COSINE
                )
            )
            print(f"Collection '{collection_name}' created with 512-dim vectors.")
        except Exception as e2:
            print(f"Error creating collection with alternative size: {e2}")


def save_chunk_to_qdrant(text: str, embedding: List[float], metadata: Dict[str, Any], collection_name: str = "rag_embedding"):
    """
    Save a text chunk with its embedding to Qdrant Cloud

    Args:
        text: The text content
        embedding: The embedding vector
        metadata: Additional metadata to store with the vector
        collection_name: Name of the collection to save to
    """
    try:
        # Create a unique ID for this record
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()

        # Prepare the record
        record = models.PointStruct(
            id=text_hash,
            vector=embedding,
            payload={
                "text": text,
                "url": metadata.get("url", ""),
                "title": metadata.get("title", ""),
                "section": metadata.get("section", ""),
                "created_at": time.time(),
                **metadata  # Include any additional metadata
            }
        )

        # Upsert the record
        qdrant_client.upsert(
            collection_name=collection_name,
            points=[record]
        )

        print(f"Saved chunk to Qdrant: {text_hash[:8]}...")
    except Exception as e:
        print(f"Error saving to Qdrant: {e}")


def main():
    """
    Main function to execute the complete RAG pipeline
    """
    print("Starting RAG Content Embeddings Pipeline...")

    # Get the target URL from environment or use default
    target_url = os.getenv("TARGET_URL", "https://physical-ai-and-humanoid-robotics-gamma.vercel.app/")

    print(f"Crawling website: {target_url}")

    # Step 1: Get all URLs from the website
    urls = get_all_urls(target_url)
    print(f"Found {len(urls)} URLs")

    # Step 2: Create the Qdrant collection
    create_collection("rag_embedding")

    # Step 3: Process each URL
    processed_count = 0
    for url in urls:
        print(f"Processing: {url}")

        # Extract text from the URL
        content_data = extract_text_from_url(url)

        if not content_data["text"].strip():
            print(f"  No content found, skipping...")
            continue

        # Chunk the text
        chunks = chunk_text(content_data["text"])
        print(f"  Created {len(chunks)} chunks")

        # Process each chunk
        for i, chunk in enumerate(chunks):
            if chunk.strip():  # Only process non-empty chunks
                # Generate embedding
                embeddings = embed([chunk])

                if embeddings and embeddings[0]:  # Check if embedding was generated successfully
                    # Prepare metadata
                    chunk_metadata = {
                        "url": content_data["url"],
                        "title": content_data["title"],
                        "section": f"chunk_{i}",
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }

                    # Save to Qdrant
                    save_chunk_to_qdrant(
                        text=chunk,
                        embedding=embeddings[0],
                        metadata=chunk_metadata,
                        collection_name="rag_embedding"
                    )

        processed_count += 1

        # Add a small delay to respect rate limits
        time.sleep(0.1)

    print(f"Pipeline completed! Processed {processed_count} URLs")

    # Step 4: Validate ingestion with a test similarity query
    print("\nValidating ingestion with test similarity query...")

    try:
        # Simple test: try to get 3 closest vectors to a sample query
        sample_embedding = embed(["test query for validation"])

        if sample_embedding and sample_embedding[0]:
            search_results = qdrant_client.search(
                collection_name="rag_embedding",
                query_vector=sample_embedding[0],
                limit=3
            )

            print(f"Found {len(search_results)} similar chunks in the database")
            if search_results:
                print("Sample result titles:")
                for i, result in enumerate(search_results[:2]):  # Show first 2 results
                    title = result.payload.get("title", "No Title")
                    print(f"  {i+1}. {title}")
        else:
            print("Could not generate test embedding for validation")

    except Exception as e:
        print(f"Error during validation: {e}")

    print("\nRAG pipeline execution completed!")


if __name__ == "__main__":
    main()