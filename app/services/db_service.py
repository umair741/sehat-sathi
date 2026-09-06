"""Supabase database service for Sehat Sathi."""

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
