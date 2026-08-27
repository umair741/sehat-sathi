from fastapi import FastAPI
from pydantic import BaseModel

from app.agents.triage_agent import run_triage

app = FastAPI(title="Sehat Sathi - Triage Demo")


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def root():
    return {"status": "Sehat Sathi API running"}


@app.post("/chat")
def chat(request: ChatRequest):
    result = run_triage(request.message)
    return {
        "severity": result.severity,
        "reasoning": result.reasoning,
    }