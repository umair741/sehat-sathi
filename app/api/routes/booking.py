from fastapi import APIRouter

from app.models.schemas import BookingRequest
from app.services.calendar_service import book_slot

router = APIRouter()


@router.post("/booking")
def create_booking(request: BookingRequest):
    return book_slot(user_id=request.user_id, urgent=request.urgent)
