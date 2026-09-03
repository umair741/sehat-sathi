

import hashlib
import time

from huggingface_hub import InferenceClient

from app.config import settings
from app.rag.ingest import PDF_PATH, load_pdf, chunking, extract_page_sources, attach_metadata
from app.services.vector_store import get_or_create_index, upsert_chunks

HF_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
HASH_RECORD_ID = "ingestion-source-hash"

_client: InferenceClient | None = None


def _get_client() -> InferenceClient:
    """Lazy-init the HF InferenceClient using the user's HF token."""
    global _client
    if _client is None:
        _client = InferenceClient(api_key=settings.hf_token)
    return _client


def embed_text(text: str) -> list[float]:
    """Embed a single string via HF Inference API. Used at query time."""
    return embed_texts([text])[0]


def embed_texts(texts: list[str], max_retries: int = 3) -> list[list[float]]:
    """Embed a batch of strings via HF Inference API with retry on transient errors."""
    client = _get_client()

    for attempt in range(max_retries):
        try:
            result = client.feature_extraction(texts, model=HF_MODEL)
            # HF returns numpy arrays — convert to plain lists for Pinecone JSON
            if hasattr(result, "tolist"):
                result = result.tolist()
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"HF Inference API failed after {max_retries} attempts: {e}") from e
            wait = 2 ** attempt
            print(f"HF API error, retrying in {wait}s: {e}")
            time.sleep(wait)


def get_chunks_from_ingest(path: str = PDF_PATH) -> list:
    """Runs load PDF -> chunk -> attach metadata, returns ready-to-embed chunks."""
    docs = load_pdf(path)
    page_sources = extract_page_sources(docs)
    chunks = chunking(docs)
    chunks = attach_metadata(chunks, page_sources)
    return chunks


def compute_file_hash(path: str = PDF_PATH) -> str:
    """Returns a SHA-256 hash of the PDF file's raw bytes."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def get_stored_hash() -> str | None:
    """Fetches the previously stored content hash from Pinecone, if any."""
    index = get_or_create_index()
    result = index.fetch(ids=[HASH_RECORD_ID])
    vectors = result.get("vectors", {}) if hasattr(result, "get") else result.vectors
    record = vectors.get(HASH_RECORD_ID) if vectors else None
    if record is None:
        return None
    metadata = record.get("metadata", {}) if hasattr(record, "get") else record.metadata
    return metadata.get("content_hash")


def store_hash(content_hash: str) -> None:
    """Stores the current content hash in Pinecone under a fixed record id."""
    index = get_or_create_index()
    dummy_vector = embed_text("sehat sathi ingestion hash record")
    index.upsert(vectors=[{
        "id": HASH_RECORD_ID,
        "values": dummy_vector,
        "metadata": {"content_hash": content_hash, "type": "hash_record"},
    }])


def run_embedding_pipeline(force: bool = False, batch_size: int = 20) -> None:
    current_hash = compute_file_hash()
    stored_hash = get_stored_hash()

    if not force and stored_hash == current_hash:
        print("Source PDF unchanged (hash matches). Skipping embedding.")
        return

    if stored_hash is None:
        print("No previous ingestion found. Embedding for the first time...")
    elif force:
        print("Force re-embed requested...")
    else:
        print("Source PDF has changed since last ingestion. Re-embedding...")

    chunks = get_chunks_from_ingest()
    print(f"Embedding {len(chunks)} chunks via HF Inference API...")

    total = upsert_chunks(chunks, embed_fn=embed_texts, batch_size=batch_size)

    store_hash(current_hash)
    print(f"Done. {total} vectors stored in Pinecone. Content hash recorded.")


if __name__ == "__main__":
    run_embedding_pipeline()