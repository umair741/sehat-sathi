"""Authentication and conversation history endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional

from app.api.deps import get_current_user, get_optional_user
from app.services.db_service import (
    add_message,
    create_conversation,
    get_conversation_messages,
    get_conversations,
)

router = APIRouter()


class UserProfile(BaseModel):
    id: str
    email: Optional[str]
    aud: Optional[str]


class ConversationOut(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    user_id: str
    role: str
    content: str
    route: Optional[str]
    severity: Optional[str]
    timestamp: str


@router.get("/me", response_model=UserProfile)
async def me(user: dict = Depends(get_current_user)):
    """Return the currently authenticated Supabase user."""
    return user


@router.get("/conversations", response_model=List[ConversationOut])
async def list_conversations(user: dict = Depends(get_current_user)):
    """List all conversations for the authenticated user."""
    conversations = get_conversations(user["id"])
    return [
        ConversationOut(
            id=c["id"],
            user_id=c["user_id"],
            title=c["title"],
            created_at=c["created_at"],
        )
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageOut])
async def list_messages(conversation_id: str, user: dict = Depends(get_current_user)):
    """List messages for a specific conversation."""
    messages = get_conversation_messages(user["id"], conversation_id)
    return [
        MessageOut(
            id=m["id"],
            conversation_id=m["conversation_id"],
            user_id=m["user_id"],
            role=m["role"],
            content=m["content"],
            route=m.get("route"),
            severity=m.get("severity"),
            timestamp=m["timestamp"],
        )
        for m in messages
    ]
