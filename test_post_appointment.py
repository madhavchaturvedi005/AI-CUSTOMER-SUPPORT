"""Test POST /api/appointments endpoint."""

import asyncio
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

async def test_post_appointment():
    """Test creating an appointment via POST endpoint."""
    
    print("🧪 Testing POST /api/appointments\n")
    print("="*60)
    
    # Check if real database is enabled
    use_real_db = os.getenv("USE_REAL_DB", "false").lower() == "true"
    print(f"USE_REAL_DB: {use_real_db}\n")
    
    # Prepare test data
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    tomorrow = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    
    appointment_data = {
        "customer_name": "Test Customer",
        "customer_phone": "+1234567890",
        "service_type": "Test Consultation",
        "appointment_datetime": tomorrow.isoformat(),
        "duration_minutes": 30,
        "notes": "Test appointment from diagnostic script",
        "call_id": None
    }
    
    print("📝 Test appointment data:")
    print(f"   Customer: {appointment_data['customer_name']}")
    print(f"   Phone: {appointment_data['customer_phone']}")
    print(f"   Service: {appointment_data['service_type']}")
    print(f"   DateTime: {appointment_data['appointment_datetime']}")
    print(f"   Duration: {appointment_data['duration_minutes']} minutes")
    print()
    
    # Test the booking logic directly
    try:
        from main import AppointmentRequest
        from appointment_manager import AppointmentManager
        from database import initialize_database
        from uuid import uuid4
        
        # Create request object
        request = AppointmentRequest(**appointment_data)
        print("✅ AppointmentRequest created successfully\n")
        
        # Initialize database
        if use_real_db:
            print("📡 Connecting to database...")
            database_service = await initialize_database()
            print("✅ Connected to database\n")
        else:
            print("⚠️  Using mock database (USE_REAL_DB=false)\n")
            from unittest.mock import AsyncMock
            database_service = AsyncMock()
            database_service.create_appointment = AsyncMock(return_value="mock-appt-123")
        
        # Parse datetime
        appt_dt = datetime.fromisoformat(request.appointment_datetime.replace('Z', '+00:00'))
        if appt_dt.tzinfo is None:
            appt_dt = appt_dt.replace(tzinfo=timezone.utc)
        
        print(f"📅 Parsed datetime: {appt_dt}")
        print(f"   Timezone-aware: {appt_dt.tzinfo is not None}\n")
        
        # Create appointment manager
        manager = AppointmentManager(database=database_service)
        print("✅ AppointmentManager created\n")
        
        # Book appointment
        print("📞 Booking appointment...")
        appointment_obj, appointment_id = await manager.book_appointment(
            call_id=None,  # No call_id for manual booking
            customer_name=request.customer_name,
            customer_phone=request.customer_phone,
            appointment_datetime=appt_dt,
            service_type=request.service_type,
            notes=request.notes
        )
        
        print(f"✅ Appointment booked successfully!")
        print(f"   Appointment ID: {appointment_id}")
        print(f"   Customer: {appointment_obj.customer_name}")
        print(f"   DateTime: {appointment_obj.appointment_datetime}")
        print()
        
        # Verify in database if real DB
        if use_real_db and not isinstance(database_service, type(AsyncMock())):
            print("🔍 Verifying in database...")
            async with database_service.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM appointments WHERE id = $1",
                    appointment_id
                )
                
                if row:
                    print("✅ Appointment found in database!")
                    print(f"   ID: {row['id']}")
                    print(f"   Customer: {row['customer_name']}")
                    print(f"   DateTime: {row['appointment_datetime']}")
                    print(f"   Status: {row['status']}")
                else:
                    print("❌ Appointment NOT found in database!")
            
            await database_service.close()
        
        print("\n" + "="*60)
        print("✅ Test completed successfully!")
        print("="*60)
        
        if use_real_db:
            print("\n💡 Next steps:")
            print("   1. Open frontend: http://localhost:8080/frontend/index.html")
            print("   2. Go to Appointments tab")
            print("   3. Click Refresh button")
            print("   4. You should see the test appointment")
        else:
            print("\n⚠️  Mock mode - appointment not saved to database")
            print("   Set USE_REAL_DB=true in .env to save to database")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_post_appointment())
