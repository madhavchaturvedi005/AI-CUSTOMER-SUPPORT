"""Diagnose appointment booking issues."""

import asyncio
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

async def diagnose_appointments():
    """Check what appointments are in the database."""
    
    print("🔍 Diagnosing Appointment Issues\n")
    print("="*60)
    
    # Check if real database is enabled
    use_real_db = os.getenv("USE_REAL_DB", "false").lower() == "true"
    print(f"USE_REAL_DB: {use_real_db}")
    
    if not use_real_db:
        print("\n⚠️  Real database is NOT enabled!")
        print("   Set USE_REAL_DB=true in .env file")
        print("   Appointments are only stored in memory (mock mode)")
        return
    
    # Try to connect to database
    try:
        from database import initialize_database
        
        print("\n📡 Connecting to database...")
        db = await initialize_database()
        print("✅ Connected to database\n")
        
        # Get current time
        now = datetime.now(timezone.utc)
        print(f"Current time (UTC): {now}")
        print(f"Current time (ISO): {now.isoformat()}\n")
        
        # Query ALL appointments (not just future ones)
        async with db.pool.acquire() as conn:
            print("📋 Querying ALL appointments in database...\n")
            
            rows = await conn.fetch("""
                SELECT 
                    id,
                    customer_name,
                    customer_phone,
                    service_type,
                    appointment_datetime,
                    duration_minutes,
                    status,
                    notes,
                    created_at
                FROM appointments
                ORDER BY created_at DESC
                LIMIT 10
            """)
            
            if not rows:
                print("❌ No appointments found in database!")
                print("\nPossible reasons:")
                print("   1. Appointment wasn't actually saved")
                print("   2. Database connection issue")
                print("   3. Wrong database being queried")
                return
            
            print(f"✅ Found {len(rows)} appointment(s):\n")
            
            for i, row in enumerate(rows, 1):
                appt_dt = row['appointment_datetime']
                created_dt = row['created_at']
                
                # Check if timezone-aware
                is_aware = appt_dt.tzinfo is not None if appt_dt else False
                
                # Calculate if it's in the future
                if appt_dt:
                    if appt_dt.tzinfo is None:
                        appt_dt_aware = appt_dt.replace(tzinfo=timezone.utc)
                    else:
                        appt_dt_aware = appt_dt
                    
                    is_future = appt_dt_aware > now
                    time_diff = appt_dt_aware - now
                else:
                    is_future = False
                    time_diff = None
                
                print(f"Appointment #{i}:")
                print(f"   ID: {row['id']}")
                print(f"   Customer: {row['customer_name']}")
                print(f"   Phone: {row['customer_phone']}")
                print(f"   Service: {row['service_type']}")
                print(f"   DateTime: {appt_dt}")
                print(f"   Timezone-aware: {is_aware}")
                print(f"   Is Future: {is_future}")
                if time_diff:
                    if is_future:
                        print(f"   Time until: {time_diff}")
                    else:
                        print(f"   Time ago: {-time_diff}")
                print(f"   Status: {row['status']}")
                print(f"   Duration: {row['duration_minutes']} minutes")
                print(f"   Notes: {row['notes']}")
                print(f"   Created: {created_dt}")
                print()
            
            # Check how many are future appointments
            future_count = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM appointments 
                WHERE appointment_datetime >= NOW()
            """)
            
            print(f"📊 Summary:")
            print(f"   Total appointments: {len(rows)}")
            print(f"   Future appointments: {future_count}")
            print(f"   Past appointments: {len(rows) - future_count}")
            
            if future_count == 0:
                print("\n⚠️  No future appointments found!")
                print("   The frontend only shows appointments with:")
                print("   appointment_datetime >= NOW()")
                print("\n💡 Solution:")
                print("   Book an appointment with a future date/time")
            else:
                print("\n✅ Future appointments exist and should be visible in frontend")
                print("   If not showing, check:")
                print("   1. Browser console for JavaScript errors")
                print("   2. Network tab - is /api/appointments returning data?")
                print("   3. Try clicking the Refresh button")
        
        await db.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n💡 Troubleshooting:")
        print("   1. Check DATABASE_URL in .env file")
        print("   2. Ensure PostgreSQL is running")
        print("   3. Run: python3 migrations/run_migration.py")

if __name__ == "__main__":
    asyncio.run(diagnose_appointments())
