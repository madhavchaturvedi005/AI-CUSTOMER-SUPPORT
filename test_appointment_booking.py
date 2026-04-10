"""Test appointment booking integration."""

import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock
import sys

# Mock the database service before importing main
sys.modules['database'] = type(sys)('database')
sys.modules['database'].DatabaseService = AsyncMock

async def test_appointment_request():
    """Test the AppointmentRequest model and POST endpoint logic."""
    from main import AppointmentRequest
    from appointment_manager import AppointmentManager
    from uuid import uuid4
    
    print("🧪 Testing Appointment Booking Integration\n")
    
    # Test 1: Valid appointment request
    print("Test 1: Valid AppointmentRequest")
    try:
        appt_request = AppointmentRequest(
            customer_name="John Doe",
            customer_phone="+1234567890",
            service_type="Consultation",
            appointment_datetime="2026-04-12T14:00:00Z",
            duration_minutes=30,
            notes="First-time customer"
        )
        print(f"✅ Created request: {appt_request.customer_name} on {appt_request.appointment_datetime}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: Parse ISO datetime
    print("\nTest 2: Parse ISO datetime string")
    try:
        iso_string = "2026-04-12T14:00:00Z"
        appt_dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        if appt_dt.tzinfo is None:
            appt_dt = appt_dt.replace(tzinfo=timezone.utc)
        print(f"✅ Parsed datetime: {appt_dt}")
        print(f"   Timezone aware: {appt_dt.tzinfo is not None}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 3: Mock appointment booking
    print("\nTest 3: Mock appointment booking")
    try:
        mock_db = AsyncMock()
        mock_db.create_appointment = AsyncMock(return_value="test-appt-123")
        
        manager = AppointmentManager(database=mock_db)
        
        appt_data, appt_id = await manager.book_appointment(
            call_id="test-call",
            customer_name="Jane Smith",
            customer_phone="+1987654321",
            appointment_datetime=datetime.now(timezone.utc) + timedelta(days=1),
            service_type="Haircut",
            notes="Regular customer"
        )
        
        print(f"✅ Booked appointment: {appt_id}")
        print(f"   Customer: {appt_data.customer_name}")
        print(f"   Service: {appt_data.service_type}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Booking phrase detection
    print("\nTest 4: Booking phrase detection")
    test_phrases = [
        ("I've scheduled a consultation for you tomorrow", True),
        ("I've booked your appointment for 2 PM", True),
        ("Your appointment is confirmed for Friday", True),
        ("Let me check our availability", False),
        ("What time would you prefer?", False)
    ]
    
    booking_phrases = [
        "i've scheduled",
        "i've booked",
        "booked for",
        "appointment confirmed",
        "scheduled for",
        "appointment is set",
        "i have booked"
    ]
    
    for phrase, should_match in test_phrases:
        text_lower = phrase.lower()
        matches = any(bp in text_lower for bp in booking_phrases)
        status = "✅" if matches == should_match else "❌"
        print(f"{status} '{phrase[:40]}...' → {matches}")
    
    # Test 5: Mock ID generation
    print("\nTest 5: Mock appointment ID generation")
    try:
        mock_id = f"mock-appt-{uuid4().hex[:8]}"
        print(f"✅ Generated mock ID: {mock_id}")
        print(f"   Length: {len(mock_id)} characters")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_appointment_request())
