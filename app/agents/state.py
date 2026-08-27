from typing import TypedDict, Optional


class SehatSathiState(TypedDict):
    query: str
    severity: Optional[str]
    reasoning: Optional[str]
    health_response: Optional[str]
    needs_booking: bool
    booking_confirmation: Optional[dict]