"""FastAPI dependencies for authentication."""

from typing import Optional

from fastapi import Header, HTTPException

from app.services.db_service import verify_user


async def get_current_user(authorization: str = Header(None)) -> dict:
    """Require a valid Bearer JWT."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    user = verify_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user


async def get_optional_user(authorization: str = Header(None)) -> Optional[dict]:
    """Return user if a valid Bearer JWT is provided, otherwise None."""
    if not authorization:
        return None

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None

    return verify_user(token)
