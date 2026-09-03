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
       ├── "health_info"  → Health Info Agent (RAG with citations) ✅
       ├── "booking"      → Booking Agent (Google Calendar — coming soon)
       └── "general"      → Direct reply (greetings, chitchat)
```

### Graph Flow (LangGraph)

```
START → supervisor → conditional routing:
    │
    ├── triage       → classifies severity (emergency / moderate / mild) → END
    ├── health_info  → RAG: embed → Pinecone search → Gemini cited answer → END
    ├── booking      → placeholder ("coming soon")                        → END
    └── general      → responds with greeting                             → END
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
- Shared state schema (`SehatSathiState`)
- Supervisor as entry point with conditional edges to all agents
- Health info node wired to real RAG agent
- Booking node placeholder ("coming soon")
- General node returns Urdu greeting

### RAG Pipeline ✅ (End-to-End Working)
- **Ingestion**: PDF → chunks (500 chars, paragraph-first splitting) — `app/rag/ingest.py`
- **Embedding**: HuggingFace Inference API via `HF_TOKEN` (`sentence-transformers/all-MiniLM-L6-v2`, 384-dim) — `app/rag/embeddings.py`
- **Storage**: Pinecone upsert with metadata (page, source) + content-hash change detection — `app/services/vector_store.py`
- **Retrieval**: Query embedding → Pinecone top-k search with similarity scores
- **Answer Generation**: Retrieved chunks + Gemini → cited answer with disclaimer — `app/agents/health_info_agent.py`
- **Verified**: 81 vectors stored, "diabetes kya hai?" returns relevant WHO/MedlinePlus chunks (scores 0.58 / 0.42 / 0.41)

### API ✅
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Status check |
| GET | `/chat/health` | Health check |
| POST | `/chat` | Main endpoint — supervisor routing + agent response (`message`, optional `session_id`) |
| POST | `/health/ask` | Direct RAG — retrieve + cited answer (`question`, optional `top_k`) |
| POST | `/health/search` | Retrieval only — chunks + similarity scores (`query`, optional `top_k`) |

### Config / Environment ✅
- API keys managed via `.env` + `pydantic-settings`
- Supports: Google API, HuggingFace token, Pinecone, Supabase, Groq, Google Calendar

### Prompts ✅
- All agent prompts centralized in `prompts.json` (triage, supervisor, health_info)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Gemini (`langchain-google-genai`) |
| Orchestration | LangGraph (`StateGraph` with conditional edges) |
| Embeddings | HuggingFace Inference API — `all-MiniLM-L6-v2` (384 dim) |
| Vector DB | Pinecone (cosine similarity) |
| Database | Supabase (not connected yet) |
| Calendar | Google Calendar API (not built yet) |
| API | FastAPI + Uvicorn |
| Config | `pydantic-settings` + `.env` |
| Deployment | Docker (3.11-slim) |

## What's Remaining

| Priority | Task | Status |
|----------|------|--------|
| 🔴 High | **Booking Agent** — extract date/time, create Google Calendar event | Placeholder |
| 🔴 High | **Calendar Service** — Google Calendar API wrapper | Empty |
| 🟡 Medium | **Supabase integration** — chat history, user sessions | Not started |
| 🟡 Medium | **Frontend** — chat UI (Streamlit or HTML) | Not started |
| 🟢 Low | **Emergency red flags** — keyword detection, instant "Call 1122" | Not started |
| 🟢 Low | **Hybrid search** — keyword + semantic retrieval | Not started |
| 🟢 Low | **Deployment** — Docker Compose + hosting | Dockerfile exists |

## File Structure

```
app/
├── agents/
│   ├── supervisor.py        ✅ Routes queries to correct agent
│   ├── triage_agent.py      ✅ Classifies symptom severity
│   ├── health_info_agent.py ✅ RAG: retrieve + Gemini cited answer
│   ├── booking_agent.py     ⬜ Empty — Google Calendar booking
│   ├── graph.py             ✅ Full LangGraph with conditional routing
│   └── state.py             ✅ Shared state schema
├── api/routes/
│   ├── chat.py              ✅ Async /chat + /chat/health
│   ├── health.py            ✅ Direct RAG: /health/ask + /health/search
│   └── booking.py           ⬜ Stub — references missing calendar service
├── rag/
│   ├── __init__.py          ✅ Package init
│   ├── ingest.py            ✅ PDF load + paragraph-first chunking
│   ├── embeddings.py        ✅ HF Inference API embeddings (384-dim)
│   └── test_embedding.py    ✅ Quick embedding smoke test
├── services/
│   ├── vector_store.py      ✅ Pinecone create/upsert/query
│   ├── llm_service.py       ✅ Shared Gemini singleton
│   ├── calendar_service.py  ⬜ Empty
│   └── db_service.py        ⬜ Empty
├── models/
│   └── schemas.py           ✅ TriageResult, RoutingResult, TriageRequest
├── config.py                ✅ All env vars configured
└── main.py                  ✅ FastAPI app + CORS + routers
tests/
└── test_rag_retriever.py    ✅ Embed query → Pinecone search → print results
scripts/
└── seed_vector_db.py        ⬜ Empty
```

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# 1. Ingest health docs into Pinecone (one-time)
python -m app.rag.embeddings

# 2. Test retriever (embed query → search Pinecone)
python -m tests.test_rag_retriever

# 3. Test supervisor routing
python -m app.agents.supervisor

# 4. Test triage severity
python -m app.agents.triage_agent

# 5. Test full graph (all agents end-to-end)
python -m app.agents.graph

# 6. Start API
uvicorn app.main:app --reload
# Docs: http://localhost:8000/docs
```

## Demo Queries

| Input | Expected Flow |
|-------|---------------|
| `"seene me dard hai aur saans nahi aa rahi"` | triage → EMERGENCY → "Call 1122" |
| `"diabetes kya hai?"` | health_info → RAG cited answer |
| `"malaria se kaise bache?"` | health_info → RAG cited answer |
| `"doctor ka appointment chahiye"` | booking → placeholder |
| `"hello"` | general → Urdu greeting |
