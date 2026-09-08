"""Smoke tests for the booking agent."""

from app.agents.booking_agent import (
    _doctors_text,
    _facilities_text,
    _match_doctor,
    _match_facility,
    booking_node,
)


def test_facilities_text():
    facilities = [
        {"id": "f1", "name": "BHU Sukkur", "type": "BHU", "district": "Sukkur"}
    ]
    text = _facilities_text(facilities)
    assert "BHU Sukkur" in text
    assert "BHU" in text


def test_doctors_text():
    doctors = [{"id": "d1", "name": "Dr. Ayesha", "specialty": "General Physician"}]
    text = _doctors_text(doctors)
    assert "Dr. Ayesha" in text
    assert "General Physician" in text


def test_match_facility():
    facilities = [{"id": "f1", "name": "BHU Sukkur", "type": "BHU"}]
    matched = _match_facility("BHU Sukkur", facilities)
    assert matched is not None
    assert matched["id"] == "f1"


def test_match_doctor():
    doctors = [{"id": "d1", "name": "Dr. Ayesha", "specialty": "General Physician"}]
    matched = _match_doctor("Ayesha", doctors)
    assert matched is not None
    assert matched["id"] == "d1"


def test_booking_node_asks_for_location():
    state = booking_node({
        "query": "doctor chahiye",
        "history": None,
        "user_id": None,
        "route_to": "booking",
        "severity": None,
        "reasoning": None,
        "health_response": None,
        "needs_booking": True,
        "booking_confirmation": None,
    })
    b = state["booking_confirmation"]
    assert b["stage"] == "need_location"
    assert isinstance(b["message"], str)
