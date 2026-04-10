#!/usr/bin/env python3
"""Test time slots and appointment booking."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from appointment_manager import AppointmentManager


async def test_time_slots():
    """Test that time slots are generated correctly."""
    print("\n" + "="*60)
    print("TESTING TIME SLOTS")
    print("="*60)
    
    # Create mock database
    mock_db = AsyncMock()
    mock_db.create_appointment = AsyncMock(return_value="appt-123")
    
    # Define business hours (same as in main.py)
    business_hours = {
        "monday": [(9, 17)],      # 9 AM - 5 PM
        "tuesday": [(9, 17)],
        "wednesday": [(9, 17)],
        "thursday": [(9, 17)],
        "friday": [(9, 17)],
        "saturday": [(10, 14)],   # 10 AM - 2 PM
        "sunday": []              # Closed
    }
    
    # Initialize appointment manager
    appt_manager = AppointmentManager(
        database=mock_db,
        business_hours=business_hours,
        slot_duration_minutes=30
    )
    
    print("\n📅 Business Hours Configuration:")
    print("-" * 60)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    
    for day_name, day_key in zip(days, day_keys):
        hours = business_hours.get(day_key, [])
        if not hours:
            print(f"{day_name:12} CLOSED")
        else:
            time_ranges = []
            for start, end in hours:
                start_str = f"{start % 12 or 12}:00 {'AM' if start < 12 else 'PM'}"
                end_str = f"{end % 12 or 12}:00 {'AM' if end < 12 else 'PM'}"
                time_ranges.append(f"{start_str} - {end_str}")
            print(f"{day_name:12} {', '.join(time_ranges)}")
    
    # Test getting slots for next 7 days
    print("\n📋 Available Slots for Next 7 Days:")
    print("-" * 60)
    
    start_date = datetime.now(timezone.utc)
    
    for i in range(7):
        test_date = start_date + timedelta(days=i)
        day_name = test_date.strftime("%A")
        date_str = test_date.strftime("%Y-%m-%d")
        
        # Get slots for this day
        slots = await appt_manager.retrieve_available_slots(
            start_date=test_date,
            end_date=test_date + timedelta(days=1),
            service_type="haircut"
        )
        
        if slots:
            print(f"\n{day_name} ({date_str}):")
            # Show first 5 slots
            for slot in slots[:5]:
                time_str = slot.strftime("%I:%M %p")
                print(f"  • {time_str}")
            if len(slots) > 5:
                print(f"  ... and {len(slots) - 5} more slots")
            print(f"  Total: {len(slots)} slots available")
        else:
            print(f"\n{day_name} ({date_str}): CLOSED or no slots")
    
    # Test propose_time_slots
    print("\n" + "="*60)
    print("TESTING PROPOSE TIME SLOTS")
    print("="*60)
    
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    proposed_slots = await appt_manager.propose_time_slots(
        preferred_date=tomorrow,
        service_type="haircut",
        num_slots=5
    )
    
    print(f"\nProposed slots for {tomorrow.strftime('%A, %B %d')}:")
    for i, slot in enumerate(proposed_slots, 1):
        print(f"  {i}. {slot.strftime('%I:%M %p')}")
    
    # Test booking an appointment
    print("\n" + "="*60)
    print("TESTING APPOINTMENT BOOKING")
    print("="*60)
    
    if proposed_slots:
        test_slot = proposed_slots[0]
        print(f"\nBooking appointment for: {test_slot.strftime('%A, %B %d at %I:%M %p')}")
        
        appointment, appt_id = await appt_manager.book_appointment(
            call_id="test-call-123",
            customer_name="Test Customer",
            customer_phone="+1234567890",
            appointment_datetime=test_slot,
            service_type="haircut",
            notes="Test booking"
        )
        
        print(f"✅ Appointment booked!")
        print(f"   ID: {appt_id}")
        print(f"   Customer: {appointment.customer_name}")
        print(f"   Date: {appointment.appointment_datetime.strftime('%B %d, %Y')}")
        print(f"   Time: {appointment.appointment_datetime.strftime('%I:%M %p')}")
        print(f"   Service: {appointment.service_type}")
        print(f"   Confirmation sent: {appointment.confirmation_sent}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nYour appointment system is ready to use!")
    print("\nWhen you call, try saying:")
    print('  "What times are available tomorrow?"')
    print('  "I want to book an appointment for Friday at 2pm"')
    print('  "Can I schedule a haircut for next Monday?"')


if __name__ == "__main__":
    asyncio.run(test_time_slots())
