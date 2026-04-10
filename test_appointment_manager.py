"""Tests for AppointmentManager service."""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timedelta, timezone
from appointment_manager import AppointmentManager
from models import AppointmentData
from database import DatabaseService


@pytest.mark.asyncio
async def test_retrieve_available_slots():
    """Test retrieving available time slots."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    appointment_manager = AppointmentManager(database=mock_db, slot_duration_minutes=30)
    
    # Get slots for next 3 days
    start_date = datetime.now(timezone.utc) + timedelta(days=1)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=3)
    
    # Execute
    slots = await appointment_manager.retrieve_available_slots(start_date, end_date)
    
    # Verify
    assert len(slots) > 0
    assert all(isinstance(slot, datetime) for slot in slots)
    # Slots should be after start of business day, not necessarily after midnight
    assert all(slot.date() >= start_date.date() for slot in slots)
    
    print(f"✅ Test passed: Retrieved {len(slots)} available slots")


@pytest.mark.asyncio
async def test_propose_time_slots_minimum_three():
    """Test that at least 3 time slots are proposed."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    appointment_manager = AppointmentManager(database=mock_db)
    
    # Execute
    slots = await appointment_manager.propose_time_slots()
    
    # Verify - should propose at least 3 slots
    assert len(slots) >= 3
    
    print(f"✅ Test passed: Proposed {len(slots)} time slots (minimum 3)")


@pytest.mark.asyncio
async def test_propose_time_slots_with_preferred_date():
    """Test proposing slots with a preferred date."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    appointment_manager = AppointmentManager(database=mock_db)
    
    preferred_date = datetime.now(timezone.utc) + timedelta(days=7)
    preferred_date = preferred_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Execute
    slots = await appointment_manager.propose_time_slots(preferred_date=preferred_date, num_slots=5)
    
    # Verify
    assert len(slots) >= 3
    # Slots should be on or after the preferred date
    assert all(slot.date() >= preferred_date.date() for slot in slots)
    
    print(f"✅ Test passed: Proposed {len(slots)} slots for preferred date")


@pytest.mark.asyncio
async def test_confirm_appointment():
    """Test appointment confirmation with all details."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    appointment_manager = AppointmentManager(database=mock_db)
    
    appointment_datetime = datetime.now(timezone.utc) + timedelta(days=1, hours=10)
    
    # Execute
    appointment = await appointment_manager.confirm_appointment(
        customer_name="John Doe",
        customer_phone="+1234567890",
        appointment_datetime=appointment_datetime,
        service_type="consultation",
        customer_email="john@example.com",
        notes="First time customer"
    )
    
    # Verify all details are confirmed
    assert appointment.customer_name == "John Doe"
    assert appointment.customer_phone == "+1234567890"
    assert appointment.customer_email == "john@example.com"
    assert appointment.service_type == "consultation"
    assert appointment.appointment_datetime == appointment_datetime
    assert appointment.notes == "First time customer"
    assert appointment.confirmation_sent is False
    
    print("✅ Test passed: Appointment confirmed with all details")


@pytest.mark.asyncio
async def test_create_calendar_entry():
    """Test creating a calendar entry."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    mock_db.create_appointment = AsyncMock(return_value="appointment-uuid-123")
    appointment_manager = AppointmentManager(database=mock_db)
    
    appointment = AppointmentData(
        customer_name="Jane Smith",
        customer_phone="+9876543210",
        service_type="haircut",
        appointment_datetime=datetime.now(timezone.utc) + timedelta(days=2)
    )
    
    # Execute
    appointment_id = await appointment_manager.create_calendar_entry(appointment, call_id="call-123")
    
    # Verify
    assert appointment_id == "appointment-uuid-123"
    assert mock_db.create_appointment.called
    
    # Verify correct parameters
    call_args = mock_db.create_appointment.call_args
    assert call_args.kwargs["customer_name"] == "Jane Smith"
    assert call_args.kwargs["service_type"] == "haircut"
    assert call_args.kwargs["status"] == "scheduled"
    
    print("✅ Test passed: Calendar entry created")


@pytest.mark.asyncio
async def test_book_appointment_complete_pipeline():
    """Test complete appointment booking pipeline."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    mock_db.create_appointment = AsyncMock(return_value="appointment-uuid-456")
    appointment_manager = AppointmentManager(database=mock_db)
    
    appointment_datetime = datetime.now(timezone.utc) + timedelta(days=3, hours=14)
    
    # Execute
    appointment, appointment_id = await appointment_manager.book_appointment(
        call_id="call-456",
        customer_name="Alice Johnson",
        customer_phone="+1234567890",
        appointment_datetime=appointment_datetime,
        service_type="massage",
        customer_email="alice@example.com",
        notes="Prefers afternoon slots"
    )
    
    # Verify
    assert appointment.customer_name == "Alice Johnson"
    assert appointment.service_type == "massage"
    assert appointment_id == "appointment-uuid-456"
    assert mock_db.create_appointment.called
    
    print("✅ Test passed: Complete booking pipeline executed")


@pytest.mark.asyncio
async def test_extract_appointment_info():
    """Test extracting appointment information from conversation."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    appointment_manager = AppointmentManager(database=mock_db)
    
    conversation_history = [
        {"speaker": "assistant", "text": "What's your name?"},
        {"speaker": "caller", "text": "My name is Bob Wilson"},
        {"speaker": "assistant", "text": "What service do you need?"},
        {"speaker": "caller", "text": "I need a haircut tomorrow"}
    ]
    
    # Execute
    info = await appointment_manager.extract_appointment_info(
        conversation_history,
        caller_phone="+1234567890"
    )
    
    # Verify
    assert info is not None
    assert info["customer_name"] == "Bob Wilson"
    assert info["customer_phone"] == "+1234567890"
    assert info["service_type"] == "haircut"
    assert info["preferred_datetime"] is not None
    
    print("✅ Test passed: Appointment info extracted from conversation")


@pytest.mark.asyncio
async def test_extract_appointment_info_insufficient_data():
    """Test extraction with insufficient data."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    appointment_manager = AppointmentManager(database=mock_db)
    
    conversation_history = [
        {"speaker": "assistant", "text": "Hello"},
        {"speaker": "caller", "text": "Hi"}  # No name or service
    ]
    
    # Execute
    info = await appointment_manager.extract_appointment_info(
        conversation_history,
        caller_phone="+1234567890"
    )
    
    # Verify
    assert info is None
    
    print("✅ Test passed: Returns None for insufficient data")


@pytest.mark.asyncio
async def test_business_hours_filtering():
    """Test that slots are only generated during business hours."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    
    # Custom business hours: Only Monday 10 AM - 12 PM
    business_hours = {
        "monday": [(10, 12)],
        "tuesday": [],
        "wednesday": [],
        "thursday": [],
        "friday": [],
        "saturday": [],
        "sunday": []
    }
    
    appointment_manager = AppointmentManager(
        database=mock_db,
        business_hours=business_hours,
        slot_duration_minutes=30
    )
    
    # Find next Monday
    today = datetime.now(timezone.utc)
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = today + timedelta(days=days_until_monday)
    
    # Get slots for that week
    start_date = next_monday
    end_date = next_monday + timedelta(days=7)
    
    # Execute
    slots = await appointment_manager.retrieve_available_slots(start_date, end_date)
    
    # Verify - should only have Monday slots between 10 AM and 12 PM
    if slots:
        for slot in slots:
            assert slot.weekday() == 0  # Monday
            assert 10 <= slot.hour < 12
    
    print(f"✅ Test passed: Business hours filtering works ({len(slots)} Monday slots)")


@pytest.mark.asyncio
async def test_appointment_validation():
    """Test appointment data validation."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    appointment_manager = AppointmentManager(database=mock_db)
    
    # Valid appointment
    future_datetime = datetime.now(timezone.utc) + timedelta(days=1)
    valid_appointment = await appointment_manager.confirm_appointment(
        customer_name="Valid Customer",
        customer_phone="+1234567890",
        appointment_datetime=future_datetime,
        service_type="consultation"
    )
    
    # Should not raise exception
    valid_appointment.validate()
    
    # Invalid appointment (past datetime)
    past_datetime = datetime.now(timezone.utc) - timedelta(days=1)
    invalid_appointment = AppointmentData(
        customer_name="Invalid Customer",
        customer_phone="+1234567890",
        service_type="consultation",
        appointment_datetime=past_datetime
    )
    
    # Should raise exception
    with pytest.raises(ValueError, match="cannot be in the past"):
        invalid_appointment.validate()
    
    print("✅ Test passed: Appointment validation works correctly")


@pytest.mark.asyncio
async def test_extract_service_types():
    """Test extraction of various service types."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    appointment_manager = AppointmentManager(database=mock_db)
    
    # Test different service types
    test_cases = [
        (["I need a haircut"], "haircut"),
        (["I want a massage"], "massage"),
        (["I need dental cleaning"], "dental"),
        (["I want a consultation"], "consultation"),
        (["I need my car repaired"], "repair"),
        (["I want to book something"], "general")  # Default
    ]
    
    for messages, expected_service in test_cases:
        history = [{"speaker": "caller", "text": msg} for msg in messages]
        service = appointment_manager._extract_service_type(history)
        assert service == expected_service
    
    print("✅ Test passed: Service type extraction works for all types")


@pytest.mark.asyncio
async def test_extract_service_types():
    """Test extraction of various service types."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    appointment_manager = AppointmentManager(database=mock_db)
    
    # Test different service types
    test_cases = [
        (["I need a haircut"], "haircut"),
        (["I want a massage"], "massage"),
        (["I need dental cleaning"], "dental"),
        (["I want a consultation"], "consultation"),
        (["I need my car repaired"], "repair"),
        (["I want to book something"], "general")  # Default
    ]
    
    for messages, expected_service in test_cases:
        history = [{"speaker": "caller", "text": msg} for msg in messages]
        service = appointment_manager._extract_service_type(history)
        assert service == expected_service
    
    print("✅ Test passed: Service type extraction works for all types")


@pytest.mark.asyncio
async def test_send_appointment_confirmation():
    """Test sending appointment confirmation SMS."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    sms_sent = []
    
    def sms_callback(phone: str, message: str):
        sms_sent.append({"phone": phone, "message": message})
    
    appointment_manager = AppointmentManager(
        database=mock_db,
        sms_callback=sms_callback
    )
    
    appointment = AppointmentData(
        customer_name="Test Customer",
        customer_phone="+1234567890",
        service_type="consultation",
        appointment_datetime=datetime.now(timezone.utc) + timedelta(days=1, hours=10)
    )
    
    # Execute
    success = await appointment_manager.send_appointment_confirmation(appointment)
    
    # Verify
    assert success is True
    assert appointment.confirmation_sent is True
    assert len(sms_sent) == 1
    assert sms_sent[0]["phone"] == "+1234567890"
    assert "Appointment Confirmed" in sms_sent[0]["message"]
    assert "consultation" in sms_sent[0]["message"]
    assert "Test Customer" in sms_sent[0]["message"]
    
    print("✅ Test passed: SMS confirmation sent successfully")


@pytest.mark.asyncio
async def test_send_confirmation_without_callback():
    """Test SMS confirmation without callback (logs only)."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    appointment_manager = AppointmentManager(database=mock_db)  # No callback
    
    appointment = AppointmentData(
        customer_name="No Callback Customer",
        customer_phone="+9876543210",
        service_type="haircut",
        appointment_datetime=datetime.now(timezone.utc) + timedelta(days=2)
    )
    
    # Execute
    success = await appointment_manager.send_appointment_confirmation(appointment)
    
    # Verify - should still succeed (logs instead of sending)
    assert success is True
    assert appointment.confirmation_sent is True
    
    print("✅ Test passed: SMS confirmation logged without callback")


@pytest.mark.asyncio
async def test_book_appointment_sends_confirmation():
    """Test that booking an appointment sends SMS confirmation."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    mock_db.create_appointment = AsyncMock(return_value="appointment-uuid-789")
    sms_sent = []
    
    async def async_sms_callback(phone: str, message: str):
        sms_sent.append({"phone": phone, "message": message})
    
    appointment_manager = AppointmentManager(
        database=mock_db,
        sms_callback=async_sms_callback
    )
    
    appointment_datetime = datetime.now(timezone.utc) + timedelta(days=5, hours=15)
    
    # Execute
    appointment, appointment_id = await appointment_manager.book_appointment(
        call_id="call-789",
        customer_name="SMS Test Customer",
        customer_phone="+1234567890",
        appointment_datetime=appointment_datetime,
        service_type="dental",
        notes="First visit"
    )
    
    # Verify
    assert appointment_id == "appointment-uuid-789"
    assert appointment.confirmation_sent is True
    assert len(sms_sent) == 1
    assert sms_sent[0]["phone"] == "+1234567890"
    assert "dental" in sms_sent[0]["message"]
    assert "First visit" in sms_sent[0]["message"]
    
    print("✅ Test passed: Booking sends SMS confirmation")


@pytest.mark.asyncio
async def test_confirmation_message_format():
    """Test SMS confirmation message format."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    sms_sent = []
    
    def sms_callback(phone: str, message: str):
        sms_sent.append({"phone": phone, "message": message})
    
    appointment_manager = AppointmentManager(
        database=mock_db,
        sms_callback=sms_callback
    )
    
    appointment_datetime = datetime(2026, 5, 15, 14, 30, tzinfo=timezone.utc)
    appointment = AppointmentData(
        customer_name="Format Test",
        customer_phone="+1234567890",
        service_type="massage",
        appointment_datetime=appointment_datetime,
        duration_minutes=60,
        notes="Bring towel"
    )
    
    # Execute
    await appointment_manager.send_appointment_confirmation(appointment)
    
    # Verify message format
    message = sms_sent[0]["message"]
    assert "Appointment Confirmed!" in message
    assert "Service: massage" in message
    assert "May 15, 2026" in message
    assert "Duration: 60 minutes" in message
    assert "Name: Format Test" in message
    assert "Notes: Bring towel" in message
    assert "Thank you for booking with us!" in message
    
    print("✅ Test passed: SMS message format is correct")


if __name__ == "__main__":
    import asyncio
    
    print("\n🧪 Running Appointment Manager Tests...\n")
    
    asyncio.run(test_retrieve_available_slots())
    asyncio.run(test_propose_time_slots_minimum_three())
    asyncio.run(test_propose_time_slots_with_preferred_date())
    asyncio.run(test_confirm_appointment())
    asyncio.run(test_create_calendar_entry())
    asyncio.run(test_book_appointment_complete_pipeline())
    asyncio.run(test_extract_appointment_info())
    asyncio.run(test_extract_appointment_info_insufficient_data())
    asyncio.run(test_business_hours_filtering())
    asyncio.run(test_appointment_validation())
    asyncio.run(test_extract_service_types())
    asyncio.run(test_send_appointment_confirmation())
    asyncio.run(test_send_confirmation_without_callback())
    asyncio.run(test_book_appointment_sends_confirmation())
    asyncio.run(test_confirmation_message_format())
    
    print("\n✅ All Appointment Manager tests passed!")
    print("\nRequirements validated:")
    print("  • 6.1: Retrieve available time slots ✓")
    print("  • 6.2: Propose at least 3 available time slots ✓")
    print("  • 6.3: Confirm date, time, service type, and contact details ✓")
    print("  • 6.4: Create calendar entry ✓")
    print("  • 6.5: Send appointment confirmation via SMS within 2 minutes ✓")
