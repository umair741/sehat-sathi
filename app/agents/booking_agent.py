"""Smart booking agent for Sehat Sathi.

Step-by-step booking through conversation:
1. Location → 2. Facility → 3. Doctor → 4. Date → 5. Slot → 6. Token
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
    reply: str = Field(..., description="Natural Roman Urdu reply to user")


llm = get_llm()
progress_llm = llm.with_structured_output(BookingProgress, method="json_mode")


def _ask_llm(history: Optional[str], query: str, options: str) -> BookingProgress:
    prompt = BOOKING_PROMPT.format(
        options=options,
        history=history or "(no previous messages)",
        query=query,
    )
    try:
        return progress_llm.invoke(prompt)
    except Exception:
        return BookingProgress(next_question="location", reply="Maaf kijiye, main samajh nahi paya. Apna sheher batain.")


def _match_facility(name: Optional[str], facilities: list) -> Optional[dict]:
    if not name or not facilities:
        return None
    name_lower = name.lower()
    for f in facilities:
        if name_lower in f["name"].lower() or name_lower in (f.get("type") or "").lower():
            return f
    return None


def _match_doctor(name: Optional[str], doctors: list) -> Optional[dict]:
    if not name or not doctors:
        return None
    name_lower = name.lower()
    for d in doctors:
        if (
            name_lower in d["name"].lower()
            or name_lower in (d.get("specialty") or "").lower()
        ):
            return d
    return None


def _facilities_text(facilities: list) -> str:
    if not facilities:
        return "No facilities found."
    return "\n".join(f"- {f['name']} ({f['type']}) | {f.get('address') or f.get('district')}" for f in facilities[:4])


def _doctors_text(doctors: list) -> str:
    if not doctors:
        return "No doctors found."
    return "\n".join(f"- {d['name']} ({d.get('specialty') or 'General'})" for d in doctors[:4])


def _slots_text(doctor_id: str, req_date: date) -> str:
    slots = db_service.get_available_slots(doctor_id, req_date)
    available = [s["time"] for s in slots if s["available"]]
    if not available:
        return "No slots available."
    return "Available slots: " + ", ".join(available[:8])


def booking_node(state: SehatSathiState) -> SehatSathiState:
    query = state.get("query", "")
    history = state.get("history")
    user_id = state.get("user_id")

    # First LLM call: understand what user wants and what is missing
    progress = _ask_llm(history, query, "(fetching options...)")
    location = progress.location

    # Step 1: Location missing
    if not location:
        state["booking_confirmation"] = {
            "success": False,
            "stage": "need_location",
            "message": progress.reply or "Aap ka sheher kaunsa hai?",
        }
        return state

    facilities = db_service.get_facilities(location=location)
    if not facilities:
        state["booking_confirmation"] = {
            "success": False,
            "stage": "no_facilities",
            "message": f"{location} mein abhi koi registered center nahi. Koi aur qareebi sheher batain.",
        }
        return state

    facility = _match_facility(progress.facility_name, facilities)
    if not facility:
        # Ask LLM again with facility options
        progress = _ask_llm(history, query, _facilities_text(facilities))
        facility = _match_facility(progress.facility_name, facilities)

    # Step 2: Facility missing
    if not facility:
        state["booking_confirmation"] = {
            "success": False,
            "stage": "need_facility",
            "message": progress.reply or f"{location} ke centers:\n{_facilities_text(facilities)}\n\nKonsa center pasand hai?",
            "location": location,
            "facilities": facilities[:4],
        }
        return state

    doctors = db_service.get_doctors(facility_id=facility["id"])
    doctor = _match_doctor(progress.doctor_name, doctors)
    if not doctor:
        progress = _ask_llm(history, query, _doctors_text(doctors))
        doctor = _match_doctor(progress.doctor_name, doctors)

    # Step 3: Doctor missing
    if not doctor:
        state["booking_confirmation"] = {
            "success": False,
            "stage": "need_doctor",
            "message": progress.reply or f"{facility['name']} ke doctors:\n{_doctors_text(doctors)}\n\nKonsa doctor chahiye?",
            "location": location,
            "facility": facility,
            "doctors": doctors[:4],
        }
        return state

    requested_date = progress.requested_date
    if not requested_date:
        progress = _ask_llm(history, query, f"Doctor: {doctor['name']}\nPlease ask for date.")
        requested_date = progress.requested_date

    # Step 4: Date missing
    if not requested_date:
        state["booking_confirmation"] = {
            "success": False,
            "stage": "need_date",
            "message": progress.reply or "Kis date ko appointment chahiye?",
            "location": location,
            "facility": facility,
            "doctor": doctor,
        }
        return state

    slot = progress.slot
    if not slot:
        progress = _ask_llm(history, query, f"Doctor: {doctor['name']}\nDate: {requested_date.isoformat()}\n{_slots_text(doctor['id'], requested_date)}")
        slot = progress.slot

    # Step 5: Slot missing
    if not slot:
        state["booking_confirmation"] = {
            "success": False,
            "stage": "need_slot",
            "message": progress.reply or f"{_slots_text(doctor['id'], requested_date)}\n\nKaunsa time suit karega?",
            "location": location,
            "facility": facility,
            "doctor": doctor,
            "requested_date": requested_date.isoformat(),
        }
        return state

    # Step 6: Create booking
    if user_id:
        booking = db_service.create_booking(
            patient_id=user_id,
            doctor_id=doctor["id"],
            facility_id=facility["id"],
            requested_date=requested_date,
            slot=slot,
        )
        if booking:
            state["booking_confirmation"] = {
                "success": True,
                "stage": "booked",
                "message": (
                    f"Aap ki appointment book ho gayi hai!\n"
                    f"Token: *{booking['token']}*\n"
                    f"Center: {facility['name']}\n"
                    f"Doctor: {doctor['name']}\n"
                    f"Date: {requested_date.isoformat()}\n"
                    f"Time: {slot}\n\n"
                    f"Yeh token save kar lein. Staff isay confirm karega."
                ),
                "booking": booking,
            }
            return state

    # Not logged in
    state["booking_confirmation"] = {
        "success": False,
        "stage": "need_login",
        "message": (
            f"Sab ready hai:\n"
            f"Center: {facility['name']}\n"
            f"Doctor: {doctor['name']}\n"
            f"Date: {requested_date.isoformat()}\n"
            f"Time: {slot}\n\n"
            f"Booking final karne ke liye login karein."
        ),
    }
    return state
