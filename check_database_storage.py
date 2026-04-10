#!/usr/bin/env python3
"""Check if appointments and leads are storing properly in the database."""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()


async def check_database_connection():
    """Check if database is configured and accessible."""
    print("\n" + "="*60)
    print("1. DATABASE CONNECTION CHECK")
    print("="*60)
    
    use_real_db = os.getenv("USE_REAL_DB", "false").lower() == "true"
    database_url = os.getenv("DATABASE_URL", "")
    
    # Also check individual DB parameters
    db_host = os.getenv("DB_HOST", "")
    db_port = os.getenv("DB_PORT", "")
    db_name = os.getenv("DB_NAME", "")
    db_user = os.getenv("DB_USER", "")
    db_password = os.getenv("DB_PASSWORD", "")
    
    print(f"\nUSE_REAL_DB: {use_real_db}")
    print(f"DATABASE_URL: {'Set' if database_url else 'Not set'}")
    print(f"DB_HOST: {db_host if db_host else 'Not set'}")
    print(f"DB_PORT: {db_port if db_port else 'Not set'}")
    print(f"DB_NAME: {db_name if db_name else 'Not set'}")
    print(f"DB_USER: {db_user if db_user else 'Not set'}")
    print(f"DB_PASSWORD: {'***' if db_password else 'Not set'}")
    
    if not use_real_db:
        print("\n⚠️  WARNING: Using MOCK database (in-memory)")
        print("   Data will NOT persist between server restarts")
        print("   To enable real database:")
        print("   1. Set USE_REAL_DB=true in .env")
        print("   2. Set DATABASE_URL or individual DB_* parameters in .env")
        print("   3. Run migrations: python3 migrations/run_migration.py")
        return False
    
    # Check if we have either DATABASE_URL or individual parameters
    has_connection_info = database_url or (db_host and db_port and db_name and db_user)
    
    if not has_connection_info:
        print("\n❌ ERROR: USE_REAL_DB=true but no database connection info set")
        print("\nSet either DATABASE_URL or individual DB_* parameters in .env")
        return False
    
    # Try to connect
    try:
        from database import initialize_database
        db = await initialize_database()
        print("\n✅ Database connection successful!")
        return db
    except Exception as e:
        print(f"\n❌ Database connection failed: {e}")
        return False


async def check_appointments_table(db):
    """Check if appointments table exists and has data."""
    print("\n" + "="*60)
    print("2. APPOINTMENTS TABLE CHECK")
    print("="*60)
    
    try:
        async with db.pool.acquire() as conn:
            # Check if table exists
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'appointments'
                )
            """)
            
            if not table_exists:
                print("\n❌ appointments table does NOT exist")
                print("   Run: python3 migrations/run_migration.py")
                return False
            
            print("\n✅ appointments table exists")
            
            # Count total appointments
            total = await conn.fetchval("SELECT COUNT(*) FROM appointments")
            print(f"   Total appointments: {total}")
            
            # Count by status
            scheduled = await conn.fetchval(
                "SELECT COUNT(*) FROM appointments WHERE status = 'scheduled'"
            )
            completed = await conn.fetchval(
                "SELECT COUNT(*) FROM appointments WHERE status = 'completed'"
            )
            cancelled = await conn.fetchval(
                "SELECT COUNT(*) FROM appointments WHERE status = 'cancelled'"
            )
            
            print(f"   Scheduled: {scheduled}")
            print(f"   Completed: {completed}")
            print(f"   Cancelled: {cancelled}")
            
            # Get recent appointments
            recent = await conn.fetch("""
                SELECT customer_name, customer_phone, service_type, 
                       appointment_datetime, status, created_at
                FROM appointments
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            if recent:
                print("\n   Recent appointments:")
                for row in recent:
                    created = row['created_at'].strftime("%Y-%m-%d %H:%M")
                    appt_time = row['appointment_datetime'].strftime("%Y-%m-%d %H:%M")
                    print(f"   • {row['customer_name']} - {row['service_type']}")
                    print(f"     Phone: {row['customer_phone']}")
                    print(f"     Appointment: {appt_time}")
                    print(f"     Status: {row['status']}")
                    print(f"     Created: {created}")
                    print()
            else:
                print("\n   ⚠️  No appointments in database yet")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error checking appointments table: {e}")
        import traceback
        traceback.print_exc()
        return False


async def check_leads_table(db):
    """Check if leads table exists and has data."""
    print("\n" + "="*60)
    print("3. LEADS TABLE CHECK")
    print("="*60)
    
    try:
        async with db.pool.acquire() as conn:
            # Check if table exists
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'leads'
                )
            """)
            
            if not table_exists:
                print("\n❌ leads table does NOT exist")
                print("   Run: python3 migrations/run_migration.py")
                return False
            
            print("\n✅ leads table exists")
            
            # Count total leads
            total = await conn.fetchval("SELECT COUNT(*) FROM leads")
            print(f"   Total leads: {total}")
            
            # Count by score range
            high = await conn.fetchval(
                "SELECT COUNT(*) FROM leads WHERE lead_score >= 7"
            )
            medium = await conn.fetchval(
                "SELECT COUNT(*) FROM leads WHERE lead_score >= 4 AND lead_score < 7"
            )
            low = await conn.fetchval(
                "SELECT COUNT(*) FROM leads WHERE lead_score < 4"
            )
            
            print(f"   High value (7-10): {high}")
            print(f"   Medium value (4-6): {medium}")
            print(f"   Low value (1-3): {low}")
            
            # Get recent leads
            recent = await conn.fetch("""
                SELECT name, phone, email, lead_score, 
                       inquiry_details, created_at
                FROM leads
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            if recent:
                print("\n   Recent leads:")
                for row in recent:
                    created = row['created_at'].strftime("%Y-%m-%d %H:%M")
                    print(f"   • {row['name']} (Score: {row['lead_score']}/10)")
                    print(f"     Phone: {row['phone']}")
                    if row['email']:
                        print(f"     Email: {row['email']}")
                    print(f"     Inquiry: {row['inquiry_details'][:50]}...")
                    print(f"     Created: {created}")
                    print()
            else:
                print("\n   ⚠️  No leads in database yet")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error checking leads table: {e}")
        import traceback
        traceback.print_exc()
        return False


async def check_calls_table(db):
    """Check if calls table exists and has data."""
    print("\n" + "="*60)
    print("4. CALLS TABLE CHECK")
    print("="*60)
    
    try:
        async with db.pool.acquire() as conn:
            # Check if table exists
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'calls'
                )
            """)
            
            if not table_exists:
                print("\n❌ calls table does NOT exist")
                return False
            
            print("\n✅ calls table exists")
            
            # Count total calls
            total = await conn.fetchval("SELECT COUNT(*) FROM calls")
            print(f"   Total calls: {total}")
            
            # Count by status
            initiated = await conn.fetchval(
                "SELECT COUNT(*) FROM calls WHERE status = 'initiated'"
            )
            in_progress = await conn.fetchval(
                "SELECT COUNT(*) FROM calls WHERE status = 'in_progress'"
            )
            completed = await conn.fetchval(
                "SELECT COUNT(*) FROM calls WHERE status = 'completed'"
            )
            
            print(f"   Initiated: {initiated}")
            print(f"   In progress: {in_progress}")
            print(f"   Completed: {completed}")
            
            # Get recent calls
            recent = await conn.fetch("""
                SELECT caller_phone, intent, language, status, 
                       started_at, duration_seconds
                FROM calls
                ORDER BY started_at DESC
                LIMIT 5
            """)
            
            if recent:
                print("\n   Recent calls:")
                for row in recent:
                    started = row['started_at'].strftime("%Y-%m-%d %H:%M")
                    duration = row['duration_seconds'] or 0
                    print(f"   • {row['caller_phone']}")
                    print(f"     Intent: {row['intent'] or 'unknown'}")
                    print(f"     Language: {row['language'] or 'unknown'}")
                    print(f"     Status: {row['status']}")
                    print(f"     Duration: {duration}s")
                    print(f"     Started: {started}")
                    print()
            else:
                print("\n   ⚠️  No calls in database yet")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error checking calls table: {e}")
        return False


async def test_appointment_creation(db):
    """Test creating a new appointment."""
    print("\n" + "="*60)
    print("5. TEST APPOINTMENT CREATION")
    print("="*60)
    
    try:
        print("\nCreating test appointment...")
        
        # Use naive UTC datetime (no timezone info) to match database TIMESTAMP column
        test_datetime = datetime.utcnow() + timedelta(days=1, hours=14)
        
        async with db.pool.acquire() as conn:
            appointment_id = await conn.fetchval("""
                INSERT INTO appointments (
                    customer_name, customer_phone, service_type,
                    appointment_datetime, duration_minutes, status, notes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, 
                "Test Customer",
                "+1234567890",
                "Test Service",
                test_datetime,
                30,
                "scheduled",
                "Test appointment from diagnostic script"
            )
            
            print(f"✅ Test appointment created: {appointment_id}")
            
            # Verify it was saved
            saved = await conn.fetchrow("""
                SELECT * FROM appointments WHERE id = $1
            """, appointment_id)
            
            if saved:
                print(f"✅ Verified: Appointment retrieved from database")
                print(f"   Customer: {saved['customer_name']}")
                print(f"   Service: {saved['service_type']}")
                print(f"   Date/Time: {saved['appointment_datetime']}")
                
                # Clean up test data
                await conn.execute("DELETE FROM appointments WHERE id = $1", appointment_id)
                print(f"✅ Test appointment cleaned up")
                
                return True
            else:
                print(f"❌ Could not retrieve test appointment")
                return False
                
    except Exception as e:
        print(f"❌ Error testing appointment creation: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_lead_creation(db):
    """Test creating a new lead."""
    print("\n" + "="*60)
    print("6. TEST LEAD CREATION")
    print("="*60)
    
    try:
        print("\nCreating test lead...")
        
        async with db.pool.acquire() as conn:
            lead_id = await conn.fetchval("""
                INSERT INTO leads (
                    name, phone, email, inquiry_details,
                    lead_score, budget_indication, timeline
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, 
                "Test Lead",
                "+1987654321",
                "test@example.com",
                "Test inquiry from diagnostic script",
                8,
                "$1000-2000",
                "next month"
            )
            
            print(f"✅ Test lead created: {lead_id}")
            
            # Verify it was saved
            saved = await conn.fetchrow("""
                SELECT * FROM leads WHERE id = $1
            """, lead_id)
            
            if saved:
                print(f"✅ Verified: Lead retrieved from database")
                print(f"   Name: {saved['name']}")
                print(f"   Score: {saved['lead_score']}/10")
                print(f"   Inquiry: {saved['inquiry_details']}")
                
                # Clean up test data
                await conn.execute("DELETE FROM leads WHERE id = $1", lead_id)
                print(f"✅ Test lead cleaned up")
                
                return True
            else:
                print(f"❌ Could not retrieve test lead")
                return False
                
    except Exception as e:
        print(f"❌ Error testing lead creation: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all database checks."""
    print("\n" + "="*60)
    print("DATABASE STORAGE DIAGNOSTIC")
    print("="*60)
    print("\nThis script checks if appointments and leads are")
    print("storing properly in your PostgreSQL database.\n")
    
    # Check connection
    db = await check_database_connection()
    
    if not db:
        print("\n" + "="*60)
        print("SUMMARY: Using MOCK database")
        print("="*60)
        print("\n⚠️  Your system is using in-memory mock data")
        print("   Appointments and leads will NOT persist")
        print("\nTo enable real database storage:")
        print("1. Create PostgreSQL database")
        print("2. Set in .env:")
        print("   USE_REAL_DB=true")
        print("   DATABASE_URL=postgresql://user:pass@localhost:5432/dbname")
        print("3. Run migrations:")
        print("   python3 migrations/run_migration.py")
        print("4. Restart server:")
        print("   python3 main.py")
        return 1
    
    # Run checks
    results = []
    results.append(("Appointments Table", await check_appointments_table(db)))
    results.append(("Leads Table", await check_leads_table(db)))
    results.append(("Calls Table", await check_calls_table(db)))
    results.append(("Test Appointment", await test_appointment_creation(db)))
    results.append(("Test Lead", await test_lead_creation(db)))
    
    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n" + "="*60)
        print("✅ ALL CHECKS PASSED!")
        print("="*60)
        print("\nYour database is properly configured and working!")
        print("\nAppointments and leads will be stored persistently.")
        print("Data will survive server restarts.")
        return 0
    else:
        print("\n" + "="*60)
        print("❌ SOME CHECKS FAILED")
        print("="*60)
        print("\nPlease fix the issues above.")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
