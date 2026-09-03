"""Shared LLM client for Sehat Sathi agents (Groq)."""

from langchain_groq import ChatGroq
from app.config import settings

_llm: ChatGroq | None = None

def get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="openai/gpt-oss-120b",
            groq_api_key=settings.groq_api_key,
        )
    return _llm
