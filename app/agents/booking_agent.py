"""Smart booking agent for Sehat Sathi.

Fully LLM-driven booking through conversation:
1. Location → 2. Facility → 3. Doctor → 4. Date → 5. Slot → 6. Token

The LLM extracts intent from natural language and writes every user-facing
message. Code only validates the LLM's extraction against the database
and attaches structured data for the frontend. No static replies.
"""

import json
import os
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.agents.state import SehatSathiState
from app.services import db_service
from app.services.llm_service import get_llm


_PROMPTS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "prompts.json")
with open(_PROMPTS_PATH, "r", encoding="utf-8") as f:
    _PROMPTS = json.load(f)

BOOKING_PROMPT = _PROMPTS["booking"]["system_prompt"]


class BookingProgress(BaseModel):
    location: Optional[str] = None
    facility_name: Optional[str] = None
    doctor_name: Optional[str] = None
    requested_date: Optional[date] = None
    slot: Optional[str] = None
    next_question: str = Field(..., description="Which field is missing: location, facility, doctor, date, slot, or ready")
    reply: str = Field(..., description="Complete reply to the user, in the same language as the user's message. Must never be empty.")


llm = get_llm()
progress_llm = llm.with_structured_output(BookingProgress, method="json_mode")


def _ask_llm(history: Optional[str], query: str, situation: str) -> BookingProgress:
    """Let the LLM read the conversation and the current situation.

    situation = short description of the booking state right now
    (facility list, doctor list, available slots, created booking, etc).
    The LLM writes the reply — no static response templates anywhere.
    """
    prompt = BOOKING_PROMPT.format(
        options=situation,
        history=history or "(no previous messages)",
        query=query,
        today=date.today().isoformat(),
    )
    result = progress_llm.invoke(prompt)
    if not (result.reply or "").strip():
        # LLM returned an empty reply — ask once more, emphasizing it is required
        result = progress_llm.invoke(prompt + "\n\nThe reply field MUST be a non-empty Roman Urdu message.")
    if not (result.reply or "").strip():
        raise ValueError("Booking LLM returned an empty reply twice.")
    return result


# ---- validators: map the LLM's extraction to real DB rows ----

def _match_facility(name: Optional[str], facilities: list) -> Optional[dict]:
    """Match the LLM-extracted facility name to an actual DB row."""
    if not name or not facilities:
        return None
    name_lower = name.lower()
    for f in facilities:
        if name_lower in f["name"].lower() or name_lower in (f.get("type") or "").lower():
            return f
    return None


def _match_doctor(name: Optional[str], doctors: list) -> Optional[dict]:
    """Match the LLM-extracted doctor name/specialty to an actual DB row."""
    if not name or not doctors:
        return None
    name_lower = name.lower()
    for d in doctors:
        if name_lower in d["name"].lower() or name_lower in (d.get("specialty") or "").lower():
            return d
    return None


def _valid_slot(slot: Optional[str], slots: list) -> Optional[str]:
    """Return the slot only if it is a real, available slot."""
    if not slot:
        return None
    for s in slots:
        if s["time"] == slot and s["available"]:
            return slot
    return None


# ---- context builders: feed real DB data to the LLM ----

def _facilities_text(facilities: list) -> str:
    if not facilities:
        return "No facilities found."
    return "\n".join(f"- {f['name']} ({f['type']}) | {f.get('address') or f.get('district')}" for f in facilities[:4])


def _doctors_text(doctors: list) -> str:
    if not doctors:
        return "No doctors found."
    return "\n".join(f"- {d['name']} ({d.get('specialty') or 'General'})" for d in doctors[:4])


def _slots_text(slots: list) -> str:
    available = [s["time"] for s in slots if s["available"]]
    if not available:
        return "No slots available on this date."
    return "Available slots: " + ", ".join(available)


def booking_node(state: SehatSathiState) -> SehatSathiState:
    query = state.get("query", "")
    history = state.get("history")
    user_id = state.get("user_id")

    # LLM call 1: read the conversation, extract everything known so far
    progress = _ask_llm(history, query, "Location is still unknown. Options will load once the city is known.")
    location = progress.location

    # Step 1: location
    if not location:
        state["booking_confirmation"] = {
            "success": False,
            "stage": "need_location",
            "message": progress.reply,
        }
        return state

    facilities = db_service.get_facilities(location=location)
    if not facilities:
        progress = _ask_llm(history, query, f"No registered health facilities exist in or near {location}.")
        state["booking_confirmation"] = {
            "success": False,
            "stage": "no_facilities",
            "message": progress.reply,
            "location": location,
        }
        return state

    # Step 2: facility
    facility = _match_facility(progress.facility_name, facilities)
    if not facility:
        progress = _ask_llm(history, query, _facilities_text(facilities))
        facility = _match_facility(progress.facility_name, facilities)
    if not facility:
        state["booking_confirmation"] = {
            "success": False,
            "stage": "need_facility",
            "message": progress.reply,
            "location": location,
            "facilities": facilities[:4],
        }
        return state

    # Step 3: doctor
    doctors = db_service.get_doctors(facility_id=facility["id"])
    doctor = _match_doctor(progress.doctor_name, doctors)
    if not doctor:
        progress = _ask_llm(history, query, _doctors_text(doctors))
        doctor = _match_doctor(progress.doctor_name, doctors)
    if not doctor:
        state["booking_confirmation"] = {
            "success": False,
            "stage": "need_doctor",
            "message": progress.reply,
            "location": location,
            "facility": facility,
            "doctors": doctors[:4],
        }
        return state

    # Step 4: date
    requested_date = progress.requested_date
    if not requested_date:
        progress = _ask_llm(history, query, f"Doctor chosen: {doctor['name']}. Appointment date is still unknown.")
        requested_date = progress.requested_date
    if not requested_date:
        state["booking_confirmation"] = {
            "success": False,
            "stage": "need_date",
            "message": progress.reply,
            "location": location,
            "facility": facility,
            "doctor": doctor,
        }
        return state

    # Step 5: slot (validated against real availability)
    slots = db_service.get_available_slots(doctor["id"], requested_date)
    slot = _valid_slot(progress.slot, slots)
    if not slot:
        progress = _ask_llm(history, query, _slots_text(slots))
        slot = _valid_slot(progress.slot, slots)
    if not slot:
        state["booking_confirmation"] = {
            "success": False,
            "stage": "need_slot",
            "message": progress.reply,
            "location": location,
            "facility": facility,
            "doctor": doctor,
            "requested_date": requested_date.isoformat(),
            "slots": slots,
        }
        return state

    # Step 6: create booking — the LLM writes the confirmation message
    if user_id:
        booking = db_service.create_booking(
            patient_id=user_id,
            doctor_id=doctor["id"],
            facility_id=facility["id"],
            requested_date=requested_date,
            slot=slot,
        )
        if booking:
            progress = _ask_llm(
                history, query,
                (
                    f"Booking created successfully. Token: {booking['token']}. "
                    f"Center: {facility['name']}. Doctor: {doctor['name']}. "
                    f"Date: {requested_date.isoformat()}. Time: {slot}. "
                    "Congratulate the user and tell them to save the token."
                ),
            )
            state["booking_confirmation"] = {
                "success": True,
                "stage": "booked",
                "message": progress.reply,
                "booking": booking,
                "facility": facility,
                "doctor": doctor,
                "requested_date": requested_date.isoformat(),
                "slot": slot,
            }
            return state

    # Not logged in — the LLM explains login is required
    progress = _ask_llm(
        history, query,
        (
            f"User is not logged in. Booking is otherwise ready: Center: {facility['name']}, "
            f"Doctor: {doctor['name']}, Date: {requested_date.isoformat()}, Time: {slot}. "
            "Tell the user to log in to finalize the booking."
        ),
    )
    state["booking_confirmation"] = {
        "success": False,
        "stage": "need_login",
        "message": progress.reply,
    }
    return state
