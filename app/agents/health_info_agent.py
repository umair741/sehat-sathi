
import json
import os
from app.agents.state import SehatSathiState
from app.rag.embeddings import embed_text
from app.services.vector_store import query_index
from app.services.llm_service import get_llm

_prompts_path = os.path.join(os.path.dirname(__file__), "..", "..", "prompts.json")
with open(_prompts_path, "r", encoding="utf-8") as f:
    _prompts = json.load(f)

HEALTH_INFO_PROMPT = _prompts["health_info"]["system_prompt"]

llm = get_llm()


def _build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a numbered context string with source labels."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("verified_source") or chunk.get("source_file", "unknown")
        parts.append(f"[{i}] (Source: {source})\n{chunk['text']}")
    return "\n\n".join(parts)


def run_health_info(query: str, top_k: int = 5) -> str:
    """Retrieve relevant health docs from Pinecone and generate a cited answer via Gemini."""
    # 1. Embed the query
    query_vec = embed_text(query)

    # 2. Search Pinecone
    results = query_index(query_vec, top_k=top_k)

    if not results:
        return (
            "I couldn't find relevant health information for your question. "
            "Please consult a doctor or rephrase your question."
        )

    # 3. Build context from retrieved chunks
    context = _build_context(results)

    # 4. Generate answer with Gemini
    prompt = (
        f"{HEALTH_INFO_PROMPT}\n\n"
        f"Context:\n{context}\n\n"
        f"User question: {query}\n\n"
        f"Answer:"
    )
    response = llm.invoke(prompt)
    
    # Handle both string and list content formats
    content = response.content
    if isinstance(content, list):
        # Extract text from content blocks
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif hasattr(block, "text"):
                text_parts.append(block.text)
        return "\n".join(text_parts)
    
    return content


def health_info_node(state: SehatSathiState) -> SehatSathiState:
    """LangGraph node: run RAG pipeline and store the answer in state."""
    response = run_health_info(state["query"])
    state["health_response"] = response
    return state