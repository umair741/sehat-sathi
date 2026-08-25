from pydantic import BaseModel
from typing import Literal, Optional


class TriageResult(BaseModel):
    severity: Literal["emergency", "moderate", "mild"]
    reasoning: str


class TriageRequest(BaseModel):
    query: str
    history: Optional[str] = None