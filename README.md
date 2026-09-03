# Sehat Sathi — AI Health Assistant for Pakistan

An AI-powered health triage and guidance system that works in **Urdu, Roman Urdu, and English**. Built for the 220+ million people in Pakistan who lack easy access to healthcare.

> **Vision**: Healthcare for everyone — in their own language, at any time, for free.

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
       ├── "booking"      → Booking Agent (in development)
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

### Frontend ✅ (Complete UI)
- **Landing page** (`frontend/index.html`) — problem-first design with mission, features, health topics, emergency guide
- **Chat page** (`frontend/chat.html`) — full chat UI with session memory (localStorage), suggestions, typing indicator, severity badges
- **Design** (`frontend/style.css`) — blue & white theme, Plus Jakarta Sans font, responsive (mobile/tablet/desktop)
- **JS** — `script.js` (scroll reveal, smooth scroll), `chat.js` (chat logic, session management, API calls)
- **Multilingual UI** — English + Roman Urdu copy throughout

### Emergency Red Flags ✅
- Keyword-based emergency detection utility (`app/utils/red_flags.py`)
- Emergency responses show "Call 1122" alert box in chat

### API ✅
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Status check |
| GET | `/health` | Health check |
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
| Database | Supabase (not connected yet — planned) |
| API | FastAPI + Uvicorn |
| Frontend | Vanilla HTML/CSS/JS (Plus Jakarta Sans, responsive, no framework) |
| Config | `pydantic-settings` + `.env` |
| Deployment | Docker (3.11-slim) |

## What's Remaining

| Priority | Task | Status |
|----------|------|--------|
| 🔴 High | **Booking Agent** — LLM multi-step conversation, doctor + slot selection, booking ID | Planned |
| 🔴 High | **Auth / Login** — Supabase Auth (email/password) + login page | Planned |
| 🟡 Medium | **Supabase integration** — persistent conversations, bookings, user sessions | Planned |
| 🟡 Medium | **Speed optimization** — local embeddings (replace HF API), response caching, streaming | Planned |
| 🟢 Low | **Hybrid search** — keyword + semantic retrieval | Not started |
| 🟢 Low | **Deployment** — Docker Compose + hosting | Dockerfile exists |

## File Structure

```
app/
├── agents/
│   ├── supervisor.py        ✅ Routes queries to correct agent
│   ├── triage_agent.py      ✅ Classifies symptom severity
│   ├── health_info_agent.py ✅ RAG: retrieve + Gemini cited answer
│   ├── booking_agent.py     ⬜ Empty — LLM multi-step booking (planned)
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
│   ├── calendar_service.py  ⬜ Empty — slot management (planned)
│   └── db_service.py        ⬜ Empty — Supabase client (planned)
├── models/
│   └── schemas.py           ✅ TriageResult, RoutingResult, TriageRequest
├── utils/
│   └── red_flags.py         ✅ Emergency keyword detection
├── config.py                ✅ All env vars configured
└── main.py                  ✅ FastAPI app + CORS + routers
frontend/
├── index.html               ✅ Landing page (mission, features, topics)
├── chat.html                ✅ Chat UI (sessions, suggestions, badges)
├── style.css                ✅ Blue & white responsive design system
├── script.js                ✅ Scroll reveal + smooth scroll
└── chat.js                  ✅ Chat logic + localStorage session memory
tests/
├── test_api_chat.py         ✅ API endpoint tests
├── test_booking_agent.py    ⬜ Booking agent tests (planned)
├── test_rag_retriever.py    ✅ Embed query → Pinecone search
└── test_triage_agent.py     ✅ Triage severity tests
scripts/
└── seed_vector_db.py        ✅ Seed vector database
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

# 7. Open frontend
# Landing page:   frontend/index.html  (browser mein kholo)
# Chat page:      frontend/chat.html   (API running honi chahiye)
```

> **Note**: Frontend static files hain — kisi server ki zaroorat nahi, browser mein directly kholo. Chat API `http://127.0.0.1:8000` pe running honi chahiye (CORS enabled).

## Docker Setup (Friend / Deployment)

Docker se chalanay ke liye — koi Python install karne ki zaroorat nahi:

```bash
# 1. Copy .env.example → .env aur apni API keys daalo (GOOGLE_API_KEY, HF_TOKEN, PINECONE_API_KEY zaroori)
# 2. Build + run
docker-compose up --build

# 3. Check
curl http://localhost:8000/health
# → {"status": "ok", "service": "Sehat Sathi"}
```

### Docker Details
- **Python 3.11.9-slim** — local dev venv (3.11.9) se exact match
- **Healthcheck** — `/health` pe automatic status check
- **Volume** — `./data` mount hota hai (health docs ke liye)
- **Secrets safe** — `.dockerignore` se `.env` image mein bake nahi hota

### Manual Docker (without compose)
```bash
docker build -t sehat-sathi .
docker run -p 8000:8000 --env-file .env -v $(pwd)/data:/app/data sehat-sathi
```

## Demo Queries

| Input | Expected Flow |
|-------|---------------|
| `"seene me dard hai aur saans nahi aa rahi"` | triage → EMERGENCY → "Call 1122" |
| `"diabetes kya hai?"` | health_info → RAG cited answer |
| `"malaria se kaise bache?"` | health_info → RAG cited answer |
| `"doctor ka appointment chahiye"` | booking → placeholder (in development) |
| `"hello"` | general → Urdu greeting |

## Known Issues / Fixes

- **Gemini content format**: `response.content` kabhi list return karta hai (content blocks) — `health_info_agent.py` dono formats handle karta hai (string + list)
- **HF API latency**: Query embedding ke liye free HF Inference API 3-8 sec leti hai — local embeddings planned
- **No auth**: API open hai — Supabase Auth planned
- **Conversations in localStorage only**: Server restart pe data nahi bachta — Supabase integration planned
