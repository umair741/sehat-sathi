import json
import os
from app.config import settings
from app.models.schemas import RoutingResult
from app.agents.state import SehatSathiState
from app.services.llm_service import get_llm


_prompts_path = os.path.join(os.path.dirname(__file__), "..", "..", "prompts.json")
with open(_prompts_path, "r", encoding="utf-8") as f:
    _prompts = json.load(f)

SUPERVISOR_PROMPT = _prompts["supervisor"]["system_prompt"]


llm = get_llm()
structured_llm = llm.with_structured_output(RoutingResult)


def run_supervisor(query: str) -> RoutingResult:
    prompt = f"{SUPERVISOR_PROMPT}\n\nUser message: {query}"
    return structured_llm.invoke(prompt)


def supervisor_node(state: SehatSathiState) -> SehatSathiState:
    result = run_supervisor(state["query"])
    state["route_to"] = result.route
    state["reasoning"] = result.reasoning
    print(f"Supervisor routed to: {result.route} ({result.reasoning})")
    return state


if __name__ == "__main__":
    test_cases = [
        "مجھے بخار ہے اور جسم میں درد ہے",
        "diabetes kya hai?",
        "doctor ka appointment chahiye",
        "hello kaise ho?",
        "seene me dard hai aur saans nahi aa rahi",
        "malaria se kaise bache?",
    ]
    for query in test_cases:
        result = run_supervisor(query)
        print(f"Query: {query}")
        print(f"Route: {result.route}")
        print(f"Reason: {result.reasoning}")
        print("---")
