"""Pinecone vector store operations for Sehat Sathi RAG."""

from pinecone import Pinecone, ServerlessSpec
from app.config import settings

EMBEDDING_DIM = 384

_pc: Pinecone | None = None


def _get_pinecone() -> Pinecone:
    """Lazy-initialize the Pinecone client (singleton)."""
    global _pc
    if _pc is None:
        _pc = Pinecone(api_key=settings.pinecone_api_key)
    return _pc


def get_or_create_index():
    """Return the Pinecone index, creating it (384-d, cosine) if it doesn't exist."""
    pc = _get_pinecone()
    index_name = settings.pinecone_index_name

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"Created Pinecone index: {index_name}")

    return pc.Index(index_name)


def upsert_chunks(chunks: list, embed_fn, batch_size: int = 20) -> int:
    """Embed chunks in batches via *embed_fn* and upsert vectors to Pinecone.

    Returns the total number of vectors upserted.
    """
    index = get_or_create_index()
    total = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [chunk.page_content for chunk in batch]
        embeddings = embed_fn(texts)

        vectors = []
        for j, chunk in enumerate(batch):
            chunk_id = f"chunk-{i + j}"
            vectors.append({
                "id": chunk_id,
                "values": embeddings[j],
                "metadata": {
                    "text": chunk.page_content,
                    "page": chunk.metadata.get("page", 0),
                    "source_file": chunk.metadata.get("source_file", ""),
                    "verified_source": chunk.metadata.get("verified_source", ""),
                },
            })

        index.upsert(vectors=vectors)
        total += len(vectors)
        print(f"  Upserted batch {i // batch_size + 1}: {len(vectors)} vectors")

    return total


def query_index(query_embedding: list[float], top_k: int = 5) -> list[dict]:
    """Search Pinecone for the top-k chunks most similar to *query_embedding*.

    Returns a list of dicts with keys: text, page, source_file, verified_source, score.
    """
    index = get_or_create_index()
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
    )

    matches = []
    for match in results.matches:
        matches.append({
            "text": match.metadata.get("text", ""),
            "page": match.metadata.get("page", 0),
            "source_file": match.metadata.get("source_file", ""),
            "verified_source": match.metadata.get("verified_source", ""),
            "score": match.score,
        })

    return matches