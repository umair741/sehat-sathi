from datetime import date
from pydantic import BaseModel
from typing import Literal, Optional


class TriageResult(BaseModel):
    severity: Literal["emergency", "moderate", "mild"]
    reasoning: str


class TriageRequest(BaseModel):
    query: str
    history: Optional[str] = None


class RoutingResult(BaseModel):
    route: Literal["triage", "health_info", "booking", "general"]
    reasoning: str


# ---------- Booking / Facility schemas ----------

class FacilityOut(BaseModel):
    id: str
    name: str
    type: str
    district: str
    tehsil: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class DoctorOut(BaseModel):
    id: str
    facility_id: str
    name: str
    specialty: Optional[str] = None
    qualification: Optional[str] = None


class SlotOut(BaseModel):
    time: str
    available: bool


class BookingRequest(BaseModel):
    doctor_id: str
    requested_date: date
    slot: str
    patient_phone: Optional[str] = None
    notes: Optional[str] = None


class BookingOut(BaseModel):
    id: str
    doctor_id: str
    facility_id: str
    requested_date: str
    slot: str
    status: str
    token: str
    patient_phone: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None