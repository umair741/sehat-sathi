import json
import os

from app.config import settings
from app.models.schemas import TriageResult
from app.agents.state import SehatSathiState
from app.services.llm_service import get_llm


_prompts_path = os.path.join(os.path.dirname(__file__), "..", "..", "prompts.json")
with open(_prompts_path, "r", encoding="utf-8") as f:
    _prompts = json.load(f)

TRIAGE_SYSTEM_PROMPT = _prompts["triage"]["system_prompt"]

llm = get_llm()

structured_llm = llm.with_structured_output(TriageResult, method="json_mode")


def run_triage(query: str, history: str | None = None) -> TriageResult:
    context = ""
    if history:
        context = f"\n\nConversation history:\n{history}"
    full_prompt = f"{TRIAGE_SYSTEM_PROMPT}{context}\n\nSymptom: {query}"
    result = structured_llm.invoke(full_prompt)
    return result


def triage_node(state: SehatSathiState) -> SehatSathiState:
    result = run_triage(state["query"], state.get("history"))
    state["severity"] = result.severity
    state["reasoning"] = result.reasoning
    return state


if __name__ == "__main__":
    test_cases = [
     "مجھے بخار ہے اور جسم میں درد ہے",
    "چھاتی میں شدید درد ہو رہا ہے",
    ]
    for query in test_cases:
        result = run_triage(query)
        print(f"Query: {query}")
        print(f"Severity: {result.severity}")
        print(f"Reasoning: {result.reasoning}")
        print("---")