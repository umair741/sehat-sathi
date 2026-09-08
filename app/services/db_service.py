"""Supabase database service for Sehat Sathi."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from supabase import Client, create_client

from app.config import settings

_client: Optional[Client] = None


def get_db() -> Client:
    """Return a singleton Supabase client."""
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


# ---------- booking helpers ----------

DEFAULT_SLOTS = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                 "12:00", "12:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]


def get_facilities(location: Optional[str] = None, limit: int = 20) -> list:
    try:
        db = get_db()
        query = db.table("facilities").select("*").limit(limit)
        if location:
            ilike = f"%{location}%"
            query = query.or_(f"district.ilike.{ilike},tehsil.ilike.{ilike},name.ilike.{ilike}")
        return query.execute().data or []
    except Exception:
        return []


def get_doctors(facility_id: Optional[str] = None) -> list:
    try:
        db = get_db()
        query = db.table("doctors").select("*")
        if facility_id:
            query = query.eq("facility_id", facility_id)
        return query.execute().data or []
    except Exception:
        return []


def get_doctor(doctor_id: str) -> Optional[dict]:
    try:
        db = get_db()
        result = db.table("doctors").select("*").eq("id", doctor_id).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None


def get_available_slots(doctor_id: str, requested_date: date) -> list:
    try:
        db = get_db()
        confirmed = (
            db.table("bookings")
            .select("slot")
            .eq("doctor_id", doctor_id)
            .eq("requested_date", requested_date.isoformat())
            .eq("status", "confirmed")
            .execute()
            .data or []
        )
        taken = {b["slot"] for b in confirmed}
        return [{"time": s, "available": s not in taken} for s in DEFAULT_SLOTS]
    except Exception:
        return []


def create_booking(patient_id: str, doctor_id: str, facility_id: str,
                   requested_date: date, slot: str, patient_phone: Optional[str] = None) -> Optional[dict]:
    try:
        db = get_db()
        import random
        token = f"SS-{random.randint(1000, 9999)}"
        payload = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "facility_id": facility_id,
            "requested_date": requested_date.isoformat(),
            "slot": slot,
            "status": "pending",
            "token": token,
            "patient_phone": patient_phone,
        }
        result = db.table("bookings").insert(payload).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None


def get_booking_by_token(token: str) -> Optional[dict]:
    try:
        db = get_db()
        result = db.table("bookings").select("*").eq("token", token).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None


def get_user_bookings(patient_id: str) -> list:
    try:
        db = get_db()
        return (
            db.table("bookings")
            .select("*")
            .eq("patient_id", patient_id)
            .order("created_at", desc=True)
            .execute()
            .data or []
        )
    except Exception:
        return []


def update_booking_status(booking_id: str, status: str) -> Optional[dict]:
    try:
        db = get_db()
        result = (
            db.table("bookings")
            .update({"status": status, "updated_at": datetime.utcnow().isoformat()})
            .eq("id", booking_id)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception:
        return None


def get_profile(user_id: str) -> Optional[dict]:
    try:
        db = get_db()
        result = db.table("profiles").select("*").eq("id", user_id).execute()
        return result.data[0] if result.data else None
    except Exception:
        return None


def verify_user(jwt: str) -> Optional[dict]:
    """Verify a Supabase JWT and return the user dict, or None if invalid."""
    try:
        db = get_db()
        response = db.auth.get_user(jwt)
        if response and response.user:
            return {
                "id": str(response.user.id),
                "email": response.user.email,
                "aud": response.user.aud,
            }
    except Exception:
        return None
    return None


def create_conversation(user_id: str, title: str) -> Optional[dict]:
    """Create a new conversation row and return it."""
    try:
        db = get_db()
        result = (
            db.table("conversations")
            .insert({"user_id": user_id, "title": title})
            .execute()
        )
        if result.data:
            return result.data[0]
    except Exception:
        return None
    return None


def get_conversations(user_id: str) -> list:
    """Return all conversations for a user, newest first."""
    try:
        db = get_db()
        result = (
            db.table("conversations")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def get_conversation_messages(user_id: str, conversation_id: str) -> list:
    """Return messages for a specific conversation."""
    try:
        db = get_db()
        result = (
            db.table("messages")
            .select("*")
            .eq("user_id", user_id)
            .eq("conversation_id", conversation_id)
            .order("timestamp", desc=False)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def add_message(
    user_id: str,
    conversation_id: str,
    role: str,
    content: str,
    route: Optional[str] = None,
    severity: Optional[str] = None,
) -> Optional[dict]:
    """Insert a message into a conversation."""
    try:
        db = get_db()
        payload = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
        }
        if route:
            payload["route"] = route
        if severity:
            payload["severity"] = severity
        result = db.table("messages").insert(payload).execute()
        if result.data:
            return result.data[0]
    except Exception:
        return None
    return None
