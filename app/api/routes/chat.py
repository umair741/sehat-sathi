import asyncio
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from app.agents.graph import compiled_graph
from app.api.deps import get_optional_user
from app.services.db_service import add_message, create_conversation

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

    # Persist user message if logged in
    if user:
        if not conversation_id:
            title = request.message[:60] + ("..." if len(request.message) > 60 else "")
            conv = create_conversation(user["id"], title)
            conversation_id = conv["id"] if conv else None

        if conversation_id:
            add_message(
                user_id=user["id"],
                conversation_id=conversation_id,
                role="user",
                content=request.message,
            )

    # LangGraph invoke is sync — run in thread pool so it doesn't block other users
    state = await asyncio.to_thread(
        compiled_graph.invoke,
        {
            "query": request.message,
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

    return ChatResponse(
        session_id=conversation_id if conversation_id else session_id,
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
    """Build a user-friendly response based on the agent route."""

    if route == "triage":
        severity = state.get("severity", "unknown")
        reasoning = state.get("reasoning", "")

        if severity == "emergency":
            return (
                f"⚠️ EMERGENCY DETECTED: {reasoning}\n"
                "Please call 1122 (Rescue) or go to the nearest hospital immediately."
            )
        elif severity == "moderate":
            return f"{reasoning}\nYou should see a doctor soon. Would you like to book an appointment?"
        else:
            return f"{reasoning}\nThis seems mild. Rest, stay hydrated, and monitor your symptoms."

    elif route == "health_info":
        return state.get("health_response", "I couldn't find relevant information for your question.")

    elif route == "booking":
        booking = state.get("booking_confirmation")
        if booking and booking.get("success"):
            return f"Appointment booked! {booking.get('message', '')}"
        return "I'd be happy to help you book an appointment. Please tell me the date and time."

    elif route == "general":
        return state.get(
            "health_response",
            "Assalam o Alaikum! Main Sehat Sathi hoon. Apni sehat ke baare mein kuch bhi pooch sakte hain.",
        )

    return "Something went wrong. Please try again."
