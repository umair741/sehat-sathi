import asyncio
import uuid
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.agents.graph import compiled_graph

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
async def chat(request: ChatRequest):
    """
    Main chat endpoint. Handles multiple concurrent users via async.

    - Send a message, get back the agent's response
    - Optional session_id for conversation continuity
    """
    session_id = request.session_id or str(uuid.uuid4())

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

    return ChatResponse(
        session_id=session_id,
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
