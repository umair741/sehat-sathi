"""Direct RAG endpoints for testing retrieval and answer generation."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.health_info_agent import run_health_info
from app.rag.embeddings import embed_text
from app.services.vector_store import query_index

router = APIRouter(prefix="/health", tags=["health"])


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("/ask")
def ask(request: AskRequest):
    """Full RAG: embed -> retrieve from Pinecone -> Gemini answer with citations."""
    answer = run_health_info(request.question, top_k=request.top_k)
    return {"question": request.question, "answer": answer}


@router.post("/search")
def search(request: SearchRequest):
    """Retrieval only: return top-k chunks from Pinecone with similarity scores."""
    query_vec = embed_text(request.query)
    results = query_index(query_vec, top_k=request.top_k)
    return {"query": request.query, "results": results}
