# Sehat Sathi — AI Health Assistant for Pakistan

An AI-powered health assistant that works in **Urdu, Roman Urdu, and English** — built for the 220+ million people in Pakistan who lack easy access to reliable healthcare guidance.

> **Vision**: Healthcare for everyone — in their own language, at any time, for free.

## Live Demo

| | URL |
|---|---|
| Frontend | https://sehat-sathi-peach.vercel.app |
| Backend API | https://sehat-sathi-production-32ce.up.railway.app |
| API Docs | https://sehat-sathi-production-32ce.up.railway.app/docs |

## Architecture

A **supervisor-based multi-agent system** built with LangGraph:

```
User Query (Urdu / Roman Urdu / English)
    │
    ▼
┌──────────────┐
│  Supervisor   │  ← Groq LLM classifies intent (structured output)
└──────┬───────┘
       │
       ├── "triage"       → Triage Agent (symptom → emergency/moderate/mild)
       ├── "health_info"  → RAG Agent (Pinecone retrieval + cited answer)
       ├── "booking"      → Booking Agent (in development)
       └── "general"      → Greetings / chitchat / unclear input
```

### Graph Flow (LangGraph)

```
START → supervisor → conditional routing:
    ├── triage       → severity classification → END
    ├── health_info  → embed → Pinecone search → cited answer → END
    ├── booking      → placeholder ("coming soon")            → END
    └── general      → greeting response                       → END
```

## Features

### Multi-Agent Routing ✅
- Supervisor agent routes every query to the right agent using structured LLM output
- Few-shot prompted for 4 routes: `triage`, `health_info`, `booking`, `general`
- Vague/off-topic input safely falls back to `general` (no false triage routing)

### Symptom Triage ✅
- Classifies symptoms into `emergency` / `moderate` / `mild` with a severity rubric
- Red-flag based escalation: only explicit red-flag symptoms trigger `emergency` (1122 alert)
- Guardrails against false emergencies — unclear input gets a friendly follow-up question, never an alarm
- Patient-facing responses in Roman Urdu (no internal English reasoning leaked to users)

### RAG Health Info Agent ✅
- **Ingestion**: health knowledge-base PDF → 500-char paragraph-first chunks (`app/rag/ingest.py`)
- **Embeddings**: HuggingFace Inference API, `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- **Vector DB**: Pinecone (cosine similarity, content-hash change detection)
- **Retrieval**: query embedding → top-k semantic search with metadata (page, source)
- **Generation**: retrieved chunks + Groq LLM → **cited answer** ([1], [2]…) + medical disclaimer
- Answers in the same language the user asked (Urdu / Roman Urdu / English)

### Multi-turn Conversation Memory ✅
- Conversation history threads through every agent via shared LangGraph state
- History persists in Supabase, so context survives across sessions and devices

### Authentication & Persistence ✅
- Supabase Auth (email/password + Google OAuth) with JWT verification middleware
- `/chat` is dual-mode: authenticated chats persist user + bot messages; anonymous chats still work
- Conversation + message storage in Supabase with Row-Level Security

### Frontend ✅
- Landing page (`index.html`), auth page (`auth.html`), full chat UI (`chat.html`)
- Session list with conversation history, suggestions, typing indicator, severity badges
- Emergency responses show a "📞 Call 1122 (Rescue) immediately" alert box
- Responsive design (mobile/tablet/desktop), Plus Jakarta Sans, blue & white theme

### Emergency Red Flags ✅
- Keyword-based emergency detection utility (`app/utils/red_flags.py`)

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq (`openai/gpt-oss-120b`) via `langchain-groq` |
| Orchestration | LangGraph (`StateGraph` with conditional edges) |
| Embeddings | HuggingFace Inference API — `all-MiniLM-L6-v2` (384 dim) |
| Vector DB | Pinecone (cosine similarity) |
| Database + Auth | Supabase (Postgres, RLS, JWT) |
| API | FastAPI + Uvicorn |
| Frontend | Vanilla HTML/CSS/JS (no framework) |
| Config | `pydantic-settings` + `.env` |
| Deployment | Railway (backend) + Vercel (frontend) + Docker |

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Status check |
| GET | `/health` | Health check |
| POST | `/chat` | Main endpoint — supervisor routing + agent response (`message`, optional `session_id`) |
| POST | `/health/ask` | Direct RAG — retrieve + cited answer (`question`, optional `top_k`) |
| POST | `/health/search` | Retrieval only — chunks + similarity scores (`query`, optional `top_k`) |
| GET | `/auth/me` | Current user (Bearer token) |
| GET | `/auth/conversations` | User's conversations (Bearer token) |
| GET | `/auth/conversations/{id}/messages` | Messages of a conversation (Bearer token) |

## Project Structure

```
app/
├── agents/
│   ├── supervisor.py        ✅ Routes queries to correct agent
│   ├── triage_agent.py      ✅ Classifies symptom severity
│   ├── health_info_agent.py ✅ RAG: retrieve + cited answer
│   ├── booking_agent.py     ⬜ Placeholder (calendar integration planned)
│   ├── graph.py             ✅ Full LangGraph with conditional routing
│   └── state.py             ✅ Shared state schema (incl. conversation history)
├── api/
│   ├── deps.py              ✅ JWT middleware (strict + optional variants)
│   └── routes/
│       ├── auth.py          ✅ /auth/me + conversation history endpoints
│       ├── chat.py          ✅ Async /chat with persistence + history wiring
│       ├── health.py        ✅ Direct RAG: /health/ask + /health/search
│       └── booking.py       ⬜ Stub
├── rag/
│   ├── ingest.py            ✅ PDF load + paragraph-first chunking
│   ├── embeddings.py        ✅ HF Inference API embeddings + ingestion pipeline
│   └── test_embedding.py    ✅ Embedding smoke test
├── services/
│   ├── db_service.py        ✅ Supabase client + conversation/message CRUD
│   ├── llm_service.py       ✅ Shared Groq LLM singleton
│   ├── vector_store.py      ✅ Pinecone create/upsert/query
│   └── calendar_service.py  ⬜ Google Calendar (planned)
├── models/
│   ├── schemas.py           ✅ TriageResult, RoutingResult, request/response models
│   └── db_models.py         ✅ DB entity models
├── core/                    ✅ Logging, security, custom exceptions
├── utils/red_flags.py       ✅ Emergency keyword detection
├── config.py                ✅ All env vars configured
└── main.py                  ✅ FastAPI app + CORS + routers
frontend/
├── index.html               ✅ Landing page
├── auth.html + auth.js      ✅ Login/Signup + Google OAuth
├── chat.html + chat.js      ✅ Chat UI + Supabase session + history
├── style.css                ✅ Responsive design system
└── script.js                ✅ Scroll reveal + smooth scroll
prompts.json                 ✅ Centralized agent prompts (few-shot + rubric)
data/health_docs/            ✅ Health knowledge base (PDF + markdown)
scripts/
├── supabase_schema.sql      ✅ Tables + RLS policies
├── create_supabase_tables.py ✅ Schema provisioning script
└── seed_vector_db.py        ✅ Vector DB seeding
tests/                       ✅ pytest suite (chat, triage, booking, RAG)
```

## How to Run (Local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy .env.example → .env and add keys:
#    GROQ_API_KEY, HF_TOKEN, PINECONE_API_KEY, PINECONE_INDEX_NAME,
#    SUPABASE_URL, SUPABASE_KEY, SUPABASE_ANON_KEY

# 3. Create Supabase tables (one-time): run scripts/supabase_schema.sql in SQL Editor

# 4. Ingest health docs into Pinecone (one-time)
python -m app.rag.embeddings

# 5. Start API
uvicorn app.main:app --reload
# Docs: http://localhost:8000/docs

# 6. Open the frontend (static — open in browser or use Live Server)
#    Landing: frontend/index.html   Chat: frontend/chat.html
```

## Docker

```bash
docker-compose up --build
# Check: curl http://localhost:8000/health
```

## Demo Queries

| Input | Expected Flow |
|---|---|
| `"seene me dard hai aur saans nahi aa rahi"` | triage → `emergency` → "Call 1122" alert |
| `"bukhar hai 3 din se"` | triage → `moderate` → doctor visit advice |
| `"diabetes kya hai?"` | health_info → RAG cited answer |
| `"malaria se kaise bache?"` | health_info → RAG cited answer |
| `"doctor ka appointment chahiye"` | booking → placeholder (in development) |
| `"hello"` | general → greeting |

## Roadmap

| Priority | Task | Status |
|---|---|---|
| 🔴 High | Booking Agent — calendar integration, slot selection, booking ID | Planned |
| 🟡 Medium | Streaming responses (SSE) + embedding caching | Planned |
| 🟡 Medium | Multilingual embedding model for better cross-lingual retrieval | Planned |
| 🟢 Low | Hybrid search (keyword + semantic) | Not started |
| 🟢 Low | Eval harness with golden routing/severity dataset | Not started |

## Known Limitations

- Booking agent is a placeholder — calendar integration in development
- HF Inference API embedding adds 3–8s latency per query (local/multilingual embeddings planned)
- No response streaming yet
