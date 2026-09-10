import asyncio
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from app.agents.graph import compiled_graph
from app.api.deps import get_optional_user
from app.services.db_service import (
    add_message,
    create_conversation,
    get_conversation_messages,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    route: str
    response: str
    severity: Optional[str] = None
    booking: Optional[dict] = None
    timestamp: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user: Optional[dict] = Depends(get_optional_user)):
    """
    Main chat endpoint. Handles multiple concurrent users via async.

    - Send a message, get back the agent's response
    - Optional session_id for conversation continuity
    - If Authorization header is provided, conversation is persisted to Supabase
    """
    session_id = request.session_id or str(uuid.uuid4())
    conversation_id = request.session_id if user else None
    print(f"[CHAT] user={user['id'] if user else None} request.session_id={request.session_id} conversation_id={conversation_id}")

    # Persist user message if logged in
    if user:
        if not conversation_id:
            title = request.message[:60] + ("..." if len(request.message) > 60 else "")
            conv = create_conversation(user["id"], title)
            if conv:
                conversation_id = conv["id"]
                logger.info("Created conversation %s for user %s", conversation_id, user["id"])
            else:
                logger.error("Failed to create conversation for user %s", user["id"])

        if conversation_id:
            add_message(
                user_id=user["id"],
                conversation_id=conversation_id,
                role="user",
                content=request.message,
            )

    # Build conversation history for context (logged-in users only)
    history = None
    if user and conversation_id:
        previous_messages = get_conversation_messages(user["id"], conversation_id)
        # Exclude the current user message we just saved
        history_messages = [m for m in previous_messages if m["role"] != "user" or m["content"] != request.message]
        if history_messages:
            history_lines = []
            for m in history_messages:
                role_label = "User" if m["role"] == "user" else "Assistant"
                history_lines.append(f"{role_label}: {m['content']}")
            history = "\n\n".join(history_lines)

    # LangGraph invoke is sync — run in thread pool so it doesn't block other users
    state = await asyncio.to_thread(
        compiled_graph.invoke,
        {
            "query": request.message,
            "history": history,
            "user_id": user["id"] if user else None,
            "route_to": None,
            "severity": None,
            "reasoning": None,
            "health_response": None,
            "needs_booking": False,
            "booking_confirmation": None,
        },
    )

    # Build response based on which agent handled it
    route = state.get("route_to", "general")
    response = _build_response(state, route)

    # Persist assistant message if logged in
    if user and conversation_id:
        add_message(
            user_id=user["id"],
            conversation_id=conversation_id,
            role="bot",
            content=response,
            route=route,
            severity=state.get("severity"),
        )

    final_session_id = conversation_id if conversation_id else session_id
    print(f"[CHAT RESPONSE] conversation_id={conversation_id} final_session_id={final_session_id} route={route}")
    return ChatResponse(
        session_id=final_session_id,
        route=route,
        response=response,
        severity=state.get("severity"),
        booking=state.get("booking_confirmation"),
        timestamp=datetime.now().isoformat(),
    )


@router.get("/health")
async def health():
    return {"status": "ok", "service": "Sehat Sathi"}


def _build_response(state: dict, route: str) -> str:
    if route == "triage":
        return state.get("reasoning") or ""
    if route == "booking":
        return (state.get("booking_confirmation") or {}).get("message") or ""
    return state.get("health_response") or ""
