import json
import os

from app.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from app.models.schemas import TriageResult
from app.agents.state import SehatSathiState


prompts_path = os.path.join(os.path.dirname(__file__), "..", "..", "prompts.json")
with open(_prompts_path, "r", encoding="utf-8") as f:
    _prompts = json.load(f)

TRIAGE_SYSTEM_PROMPT = _prompts["triage"]["system_prompt"]

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=settings.google_api_key,
)

structured_llm = llm.with_structured_output(TriageResult)


def run_triage(query: str) -> TriageResult:
    full_prompt = f"{TRIAGE_SYSTEM_PROMPT}\n\nSymptom: {query}"
    result = structured_llm.invoke(full_prompt)
    return result


def triage_node(state: SehatSathiState) -> SehatSathiState:
    result = run_triage(state["query"])
    state["severity"] = result.severity
    state["reasoning"] = result.reasoning
    return state


if __name__ == "__main__":
    test_cases = [
        "seenay mein bohot takleef ho rahi hai, saans nahi aa rahi",
        "halka sar dard hai",
        "3 din se ulti ho rahi hai aur kamzori bhi hai",
        "dil ghabra raha hai aur pasina aa raha hai",
    ]
    for query in test_cases:
        result = run_triage(query)
        print(f"Query: {query}")
        print(f"Severity: {result.severity}")
        print(f"Reasoning: {result.reasoning}")
        print("---")