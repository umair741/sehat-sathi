# Sehat Sathi — Progress So Far

## What's built

### Triage Agent
- Uses Gemini (`gemini-1.5-flash`) via `langchain-google-genai`
- Structured output via Pydantic (`TriageResult`: `severity` + `reasoning`)
- Severity classified as `emergency` / `moderate` / `mild`
- System prompt loaded from `prompts.json` (kept at project root)
- Tested with Roman Urdu symptom inputs — correctly classified emergency,
  moderate, and mild cases with clear reasoning
- Confirmed to handle pure Urdu script as well (Gemini is multilingual by
  default, no separate translation needed)

### LangGraph wiring
- Shared state schema defined (`SehatSathiState`) — holds query, severity,
  reasoning, health_response, needs_booking, booking_confirmation
- Triage node wrapped and connected in a `StateGraph` (entry point → triage → END)
- Verified working end-to-end via `graph.invoke()`, returns full populated state

### Config / environment setup
- API keys managed via `.env` (not committed) + `.env.example` (committed, empty)
- `pydantic-settings` loads `.env` automatically, no manual `load_dotenv()` calls

### FastAPI
- Basic `/chat` endpoint stubbed, wraps the triage function for local testing

### Version control
- Git repo initialized, `.gitignore` excludes `venv/` and `.env`
- Pushed to GitHub with incremental commits

## Not built yet

- Health Info Agent (RAG)
- Booking Agent
- Full graph integration (only triage node connected so far)
- Deployment
- Frontend/demo interface