# Sehat Sathi — AI Health Assistant for Pakistan

An AI-powered health triage and guidance system that works in **Urdu, Roman Urdu, and English**. Built for the 300+ million people who lack easy access to healthcare.

## Architecture

```
User Query (Urdu / Roman Urdu / English)
    │
    ▼
┌──────────────┐
│  Supervisor   │  ← Gemini classifies intent
└──────┬───────┘
       │
       ├── "triage"       → Triage Agent (symptom → severity)
       ├── "health_info"  → Health Info Agent (RAG — coming soon)
       ├── "booking"      → Booking Agent (Google Calendar — coming soon)
       └── "general"      → Direct reply (greetings, chitchat)
```

### Graph Flow (LangGraph)

```
START → supervisor → conditional routing:
    │
    ├── triage       → classifies severity (emergency / moderate / mild) → END
    ├── health_info  → answers health questions with citations         → END
    ├── booking      → books appointment in Google Calendar            → END
    └── general      → responds with greeting                          → END
```

## What's Built

### Supervisor Agent ✅
- Routes user queries to the correct agent using Gemini structured output
- Handles 4 routes: `triage`, `health_info`, `booking`, `general`
- Tested with Urdu, Roman Urdu, and English — all route correctly
- Prompt stored in `prompts.json`

### Triage Agent ✅
- Classifies symptoms into `emergency` / `moderate` / `mild`
- Structured output via Pydantic (`TriageResult`: severity + reasoning)
- Works with pure Urdu script and Roman Urdu
- Conservative approach — escalates when in doubt

### LangGraph Full Wiring ✅
- Shared state schema (`SehatSathiState`) with `route_to` field
- Supervisor as entry point with conditional edges to all agents
- Health info and booking nodes have placeholders (ready for real logic)
- General node returns Urdu greeting

### RAG Pipeline (Partial) ⚠️
- File loading via LangChain `DirectoryLoader` — working
- Chunking via `RecursiveCharacterTextSplitter` with paragraph-first splitting — working
- Embedding + Pinecone storage — not yet connected
- Answer generation — not yet connected

### Config / Environment ✅
- API keys managed via `.env` + `pydantic-settings`
- Supports: Google API, Pinecone, Supabase, Groq, Google Calendar

### Prompts ✅
- All agent prompts centralized in `prompts.json` (triage, supervisor)
- Easy to edit without touching code

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Gemini 1.5 Flash (`langchain-google-genai`) |
| Orchestration | LangGraph (`StateGraph` with conditional edges) |
| Embeddings | Gemini `text-embedding-004` (768 dim) |
| Vector DB | Pinecone (cosine similarity) |
| Database | Supabase |
| Calendar | Google Calendar API |
| API | FastAPI + Uvicorn |
| Config | `pydantic-settings` + `.env` |
| Deployment | Docker (3.11-slim) |

## What's Remaining

| Priority | Task | Status |
|----------|------|--------|
| 🔴 High | **Health Info Agent** — connect RAG embedding + Pinecone + answer generation | Placeholder exists |
| 🔴 High | **Booking Agent** — extract date/time from message, create Google Calendar event | Placeholder exists |
| 🔴 High | **FastAPI `/chat` endpoint** — wire the full graph to the API | Stub only |
| 🟡 Medium | **Health data** — populate `data/health_docs/` with real health content | Empty |
| 🟡 Medium | **Supabase integration** — chat history, user sessions | Not started |
| 🟡 Medium | **Frontend** — simple chat UI (Streamlit or HTML) | Not started |
| 🟢 Low | **Emergency detection** — auto-detect red flags, push "Call 1122" | Not started |
| 🟢 Low | **Deployment** — Docker Compose + hosting | Dockerfile exists |

## File Structure

```
app/
├── agents/
│   ├── supervisor.py      ✅ Routes queries to correct agent
│   ├── triage_agent.py    ✅ Classifies symptom severity
│   ├── booking_agent.py   ⬜ Placeholder — Google Calendar booking
│   ├── health_info_agent.py ⬜ Placeholder — RAG health Q&A
│   ├── graph.py           ✅ Full LangGraph with conditional routing
│   └── state.py           ✅ Shared state schema
├── api/routes/
│   ├── chat.py            ⬜ Stub
│   ├── booking.py         ⬜ Stub
│   └── health.py          ⬜ Stub
├── rag/
│   ├── ingest.py          ⚠️ Load + chunk done, embed + store pending
│   └── prompts.py         ✅ Health Q&A prompt templates
├── services/
│   ├── calendar_service.py ⬜ Empty
│   ├── db_service.py       ⬜ Empty
│   ├── llm_service.py      ⬜ Empty
│   └── vector_store.py     ⬜ Empty
├── models/
│   ├── schemas.py          ✅ TriageResult, RoutingResult, TriageRequest
│   └── db_models.py        ⬜ Empty
├── config.py               ✅ All env vars configured
└── main.py                 ⬜ FastAPI app stub
```

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Test supervisor routing
python -m app.agents.supervisor

# Test full graph
python -m app.agents.graph

# Test RAG loading
python -m app.rag.ingest
```
