"""Simple booking endpoints for Sehat Sathi."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user
from app.models.schemas import BookingOut, BookingRequest, DoctorOut, FacilityOut, SlotOut
from app.services import db_service

router = APIRouter()


@router.get("/facilities", response_model=list[FacilityOut])
def list_facilities(location: Optional[str] = Query(None)):
    """List health facilities by location."""
    rows = db_service.get_facilities(location=location)
    return [FacilityOut(**r) for r in rows]


@router.get("/doctors", response_model=list[DoctorOut])
def list_doctors(facility_id: Optional[str] = Query(None)):
    """List doctors, optionally filtered by facility."""
    rows = db_service.get_doctors(facility_id=facility_id)
    return [DoctorOut(**r) for r in rows]


@router.get("/slots", response_model=list[SlotOut])
def list_slots(doctor_id: str, date: date):
    """Return available time slots for a doctor on a date."""
    return db_service.get_available_slots(doctor_id, date)


@router.post("/request", response_model=BookingOut)
def request_booking(request: BookingRequest, user: dict = Depends(get_current_user)):
    """Create a pending booking request."""
    doctor = db_service.get_doctor(request.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    booking = db_service.create_booking(
        patient_id=user["id"],
        doctor_id=request.doctor_id,
        facility_id=doctor["facility_id"],
        requested_date=request.requested_date,
        slot=request.slot,
        patient_phone=request.patient_phone,
    )
    if not booking:
        raise HTTPException(status_code=500, detail="Failed to create booking")
    return BookingOut(**booking)


@router.get("/my", response_model=list[BookingOut])
def my_bookings(user: dict = Depends(get_current_user)):
    """List current user's bookings."""
    rows = db_service.get_user_bookings(user["id"])
    return [BookingOut(**r) for r in rows]


@router.get("/{token}", response_model=BookingOut)
def get_booking(token: str, user: dict = Depends(get_current_user)):
    """Get booking by token."""
    booking = db_service.get_booking_by_token(token)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["patient_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return BookingOut(**booking)


@router.patch("/{booking_id}/status")
def update_status(
    booking_id: str,
    status: str = Query(..., pattern="^(confirmed|cancelled|completed)$"),
    user: dict = Depends(get_current_user),
):
    """Admin: confirm/cancel a booking."""
    profile = db_service.get_profile(user["id"])
    if not profile or profile.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    updated = db_service.update_booking_status(booking_id, status)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update booking")
    return {"success": True, "booking": updated}
