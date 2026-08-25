from app.services.calendar_service import book_slot


def test_booking_returns_confirmation():
    result = book_slot(user_id="test-user", urgent=False)
    assert result["status"] == "confirmed"
    assert "scheduled_time" in result
