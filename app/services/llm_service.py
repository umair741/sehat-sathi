"""Shared Gemini LLM client for Sehat Sathi agents."""

from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

_llm: ChatGoogleGenerativeAI | None = None

def get_llm() -> ChatGoogleGenerativeAI:
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=settings.google_api_key,
        )
    return _llm