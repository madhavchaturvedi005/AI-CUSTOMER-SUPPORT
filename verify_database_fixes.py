#!/usr/bin/env python3
"""Verify all database timezone fixes are working."""

import asyncio
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()


async def test_all_operations():
    """Test all database operations that use timestamps."""
    print("\n" + "="*60)
    print("DATABASE TIMEZONE FIXES VERIFICATION")
    print("="*60)
    
    from database import initialize_database
    db = await initialize_database()
    
    test_results = []
    
    # Test 1: Create Call
    print("\n1. Testing create_call...")
    try:
        call_id = await db.create_call(
            call_sid="VERIFY_CALL_001",
            caller_phone="+1234567890",
            direction="inbound",
            status="initiated"
        )
        print(f"   ✅ Call created: {call_id}")
        test_results.append(("create_call", True))
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        test_results.append(("create_call", False))
        return test_results
    
    # Test 2: Update Call Status
    print("\n2. Testing update_call_status...")
    try:
        ended_at = datetime.now(timezone.utc)  # timezone-aware
        success = await db.update_call_status(
            call_id=call_id,
            status="completed",
            ended_at=ended_at,
            duration_seconds=120
        )
        print(f"   ✅ Call status updated: {success}")
        test_results.append(("update_call_status", success))
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        test_results.append(("update_call_status", False))
    
    # Test 3: Create Lead
    print("\n3. Testing create_lead...")
    try:
        lead_id = await db.create_lead(
            call_id=call_id,
            name="Test Lead",
            phone="+1987654321",
            email="test@example.com",
            inquiry_details="Test inquiry",
            lead_score=8
        )
        print(f"   ✅ Lead created: {lead_id}")
        test_results.append(("create_lead", True))
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        test_results.append(("create_lead", False))
    
    # Test 4: Create Appointment
    print("\n4. Testing create_appointment...")
    try:
        appt_datetime = datetime.now(timezone.utc) + timedelta(days=1)
        appt_id = await db.create_appointment(
            call_id=call_id,
            customer_name="Test Customer",
            customer_phone="+1555555555",
            customer_email="customer@example.com",
            service_type="Test Service",
            appointment_datetime=appt_datetime,
            duration_minutes=30,
            notes="Test appointment"
        )
        print(f"   ✅ Appointment created: {appt_id}")
        test_results.append(("create_appointment", True))
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        test_results.append(("create_appointment", False))
    
    # Test 5: Retrieve Call
    print("\n5. Testing get_call_by_sid...")
    try:
        call_record = await db.get_call_by_sid("VERIFY_CALL_001")
        if call_record:
            print(f"   ✅ Call retrieved")
            print(f"      Status: {call_record['status']}")
            print(f"      Duration: {call_record['duration_seconds']}s")
            test_results.append(("get_call_by_sid", True))
        else:
            print(f"   ❌ Call not found")
            test_results.append(("get_call_by_sid", False))
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        test_results.append(("get_call_by_sid", False))
    
    # Cleanup
    print("\n6. Cleaning up test data...")
    try:
        async with db.pool.acquire() as conn:
            await conn.execute("DELETE FROM appointments WHERE call_id = $1", call_id)
            await conn.execute("DELETE FROM leads WHERE call_id = $1", call_id)
            await conn.execute("DELETE FROM calls WHERE id = $1", call_id)
        print(f"   ✅ Test data cleaned up")
    except Exception as e:
        print(f"   ⚠️  Cleanup failed: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in test_results)
    
    if all_passed:
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nAll database operations are working correctly!")
        print("Calls, leads, and appointments will be stored properly.")
        print("\nRestart your server to apply the fixes:")
        print("  python3 main.py")
    else:
        print("\n" + "="*60)
        print("❌ SOME TESTS FAILED")
        print("="*60)
        print("\nPlease check the errors above.")
    
    return all_passed


if __name__ == "__main__":
    import sys
    success = asyncio.run(test_all_operations())
    sys.exit(0 if success else 1)
