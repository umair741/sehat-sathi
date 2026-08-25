from app.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from app.models.schemas import TriageResult

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=settings.google_api_key,
)

structured_llm = llm.with_structured_output(TriageResult)

TRIAGE_SYSTEM_PROMPT = """You are a medical triage assistant.
Classify the user's symptom description into: emergency, moderate, or mild.
Be conservative — when in doubt, escalate severity.
Give a short, clear reasoning for your classification."""


def run_triage(query: str) -> TriageResult:
    full_prompt = f"{TRIAGE_SYSTEM_PROMPT}\n\nSymptom: {query}"
    result = structured_llm.invoke(full_prompt)
    return result


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