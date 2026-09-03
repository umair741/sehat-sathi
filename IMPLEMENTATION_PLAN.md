# Sehat Sathi — Implementation Plan

> **Target:** Hackathon submission — working product for Pakistan healthcare

---

## Architecture Overview

```
User Query (Urdu / Roman Urdu / English)
    │
    ▼
[Supervisor] ← Gemini classifies intent
    │
    ├── "triage"      → Triage Agent     → severity (emergency/moderate/mild)
    ├── "health_info" → Health Info Agent → RAG answer with citations
    ├── "booking"     → Booking Agent    → Google Calendar appointment
    └── "general"     → Direct reply
    │
    ▼
  [END] → API Response
```

---

## ✅ Completed

| # | Component | Status | Files |
|---|-----------|--------|-------|
| 1 | **Supervisor Agent** | ✅ Done, tested | `app/agents/supervisor.py` |
| 2 | **Triage Agent** | ✅ Done, tested | `app/agents/triage_agent.py` |
| 3 | **LangGraph Wiring** | ✅ Full graph with conditional routing | `app/agents/graph.py` |
| 4 | **State Schema** | ✅ All fields defined | `app/agents/state.py` |
| 5 | **Pydantic Schemas** | ✅ TriageResult, RoutingResult | `app/models/schemas.py` |
| 6 | **Prompts** | ✅ Triage + Supervisor in JSON | `prompts.json` |
| 7 | **Chat API** | ✅ Async endpoint with session support | `app/api/routes/chat.py` |
| 8 | **FastAPI App** | ✅ CORS + router included | `app/main.py` |
| 9 | **RAG Loading** | ✅ LangChain DirectoryLoader | `app/rag/ingest.py` |
| 10 | **RAG Chunking** | ✅ Paragraph-first splitter | `app/rag/ingest.py` |
| 11 | **RAG Prompts** | ✅ Health Q&A templates | `app/rag/prompts.py` |
| 12 | **Config** | ✅ All env vars setup | `app/config.py` |
| 13 | **Docker** | ✅ Dockerfile + docker-compose | Root files |

---

## 🔴 Remaining — High Priority

### 1. Health Info Agent (RAG)
**Goal:** Answer health questions using retrieved documents with citations

**Steps:**
- [ ] Add health data files to `data/health_docs/` (source: MedlinePlus API or NHS)
- [ ] Connect Gemini embeddings to `ingest.py`
- [ ] Connect Pinecone upsert to `ingest.py`
- [ ] Build `health_info_agent.py` — retrieve + generate answer
- [ ] Replace placeholder in `graph.py` with real node
- [ ] Add `health_info` prompt to `prompts.json`
- [ ] Test end-to-end: "diabetes kya hai?" → cited answer

**Files to modify:**
- `app/agents/health_info_agent.py`
- `app/agents/graph.py`
- `app/rag/ingest.py` (add embed + store)
- `prompts.json`

---

### 2. Booking Agent (Google Calendar)
**Goal:** Book real appointments in Google Calendar

**Steps:**
- [ ] Create Google Cloud project + enable Calendar API
- [ ] Generate service account JSON key
- [ ] Add credentials path to `.env`
- [ ] Add `BookingDetails` + `BookingResult` schemas
- [ ] Build `calendar_service.py` — Google Calendar API wrapper
- [ ] Build `booking_agent.py` — LLM extracts date/time/reason, calls calendar
- [ ] Replace placeholder in `graph.py` with real node
- [ ] Add `booking` prompt to `prompts.json`
- [ ] Test: "kal 3 baje appointment chahiye" → calendar event created

**Files to modify:**
- `app/agents/booking_agent.py`
- `app/services/calendar_service.py`
- `app/agents/graph.py`
- `app/models/schemas.py`
- `prompts.json`

---

### 3. Health Data
**Goal:** Populate `data/health_docs/` with real, authoritative health content

**Steps:**
- [ ] Write MedlinePlus API scraper script
- [ ] Pull 15-20 Pakistan-relevant topics:
  - hepatitis-c, dengue, malaria, typhoid, tuberculosis
  - diabetes, heatstroke, pneumonia, diarrhea, cholera
  - heart-attack, high-blood-pressure, asthma, food-poisoning
  - anemia, maternal-health, child-nutrition, first-aid
- [ ] Add Pakistan-specific files (emergency numbers, local context)
- [ ] Run ingestion to populate Pinecone

**Files:**
- `scripts/scrape_medlineplus.py` (new)
- `data/health_docs/*.md`

---

## 🟡 Remaining — Medium Priority

### 4. Supabase Integration
**Goal:** Store chat history and user sessions

**Steps:**
- [ ] Create Supabase project + get keys
- [ ] Design tables: `sessions`, `messages`
- [ ] Build `db_service.py` — CRUD operations
- [ ] Add chat history to graph state
- [ ] Add `GET /chat/history/{session_id}` endpoint

**Files to modify:**
- `app/services/db_service.py`
- `app/agents/state.py` (add `chat_history` field)
- `app/api/routes/chat.py`

---

### 5. Frontend (Streamlit)
**Goal:** Chat UI that judges can interact with

**Steps:**
- [ ] Create `frontend/streamlit_app.py`
- [ ] WhatsApp-style chat interface
- [ ] Connect to FastAPI `/chat` endpoint
- [ ] Show route badge (triage/health_info/booking)
- [ ] Show severity color for triage (red/yellow/green)

---

### 6. Booking API Route
**Goal:** Direct booking endpoint

**Steps:**
- [ ] Wire `app/api/routes/booking.py` to booking agent
- [ ] Add validation and error handling

---

## 🟢 Remaining — Low Priority (Polish)

### 7. Emergency Red Flag Detection
- [ ] Detect critical keywords: "chest pain + sweating", "unconscious"
- [ ] Bypass normal flow — immediately return "CALL 1122"
- [ ] Add to `app/utils/red_flags.py`

### 8. Shared LLM Service
- [ ] Create single Gemini client in `app/services/llm_service.py`
- [ ] All agents use it instead of creating their own

### 9. Tests
- [ ] Update existing tests for new graph structure
- [ ] Add integration tests for full flow
- [ ] Test all 4 routes (triage, health_info, booking, general)

### 10. Deployment
- [ ] Test Docker build locally
- [ ] Deploy to free tier (Railway / Render / Fly.io)
- [ ] Set environment variables
- [ ] Test live endpoint

---

## Build Order (Recommended)

```
Phase 1: Get RAG Working
  ├── 1a. Scrape health data (MedlinePlus)
  ├── 1b. Connect embeddings + Pinecone in ingest.py
  ├── 1c. Build health_info_agent.py
  └── 1d. Wire into graph + test

Phase 2: Get Booking Working
  ├── 2a. Set up Google Calendar credentials
  ├── 2b. Build calendar_service.py
  ├── 2c. Build booking_agent.py
  └── 2d. Wire into graph + test

Phase 3: Make It Presentable
  ├── 3a. Build Streamlit frontend
  ├── 3b. Add Supabase chat history
  └── 3c. Polish API responses

Phase 4: Ship It
  ├── 4a. Docker build + test
  ├── 4b. Deploy to cloud
  └── 4c. Prepare demo script
```

---

## Demo Scenarios (for judges)

| # | Input | Expected Flow |
|---|-------|---------------|
| 1 | "seene me dard hai aur saans nahi aa rahi" | triage → EMERGENCY → "Call 1122" |
| 2 | "diabetes me kya khana chahiye?" | health_info → RAG answer with source |
| 3 | "kal shaam 3 baje doctor se milna hai" | booking → Calendar event created |
| 4 | "assalam o alaikum" | general → Urdu greeting |
| 5 | "bukhar hai 3 din se" | triage → MODERATE → suggests booking |

---

## Quick Commands

```bash
# Run the API
uvicorn app.main:app --reload

# Test supervisor routing
python -m app.agents.supervisor

# Test full graph
python -m app.agents.graph

# Run RAG ingestion (after adding data)
python -m app.rag.ingest

# Open API docs
# http://localhost:8000/docs
```
