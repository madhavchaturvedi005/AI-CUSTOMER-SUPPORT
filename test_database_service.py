#!/usr/bin/env python3
"""Test if database service is properly initialized and working."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_database_service():
    """Test database service initialization and call creation."""
    print("\n" + "="*60)
    print("DATABASE SERVICE TEST")
    print("="*60)
    
    # Check environment
    use_real_db = os.getenv("USE_REAL_DB", "false").lower() == "true"
    print(f"\n1. Environment check:")
    print(f"   USE_REAL_DB: {use_real_db}")
    
    if not use_real_db:
        print("\n❌ USE_REAL_DB is not true")
        print("   Set USE_REAL_DB=true in .env")
        return False
    
    # Initialize database
    print(f"\n2. Initializing database...")
    try:
        from database import initialize_database
        db = await initialize_database()
        print(f"   ✅ Database initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return False
    
    # Test create_call
    print(f"\n3. Testing create_call...")
    try:
        call_id = await db.create_call(
            call_sid="TEST_SID_123",
            caller_phone="+1234567890",
            direction="inbound",
            status="initiated",
            language="en"
        )
        print(f"   ✅ Call created: {call_id}")
    except Exception as e:
        print(f"   ❌ Failed to create call: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verify call was saved
    print(f"\n4. Verifying call was saved...")
    try:
        call_record = await db.get_call_by_sid("TEST_SID_123")
        if call_record:
            print(f"   ✅ Call found in database")
            print(f"      ID: {call_record['id']}")
            print(f"      SID: {call_record['call_sid']}")
            print(f"      Phone: {call_record['caller_phone']}")
            print(f"      Status: {call_record['status']}")
        else:
            print(f"   ❌ Call not found in database")
            return False
    except Exception as e:
        print(f"   ❌ Failed to retrieve call: {e}")
        return False
    
    # Clean up test call
    print(f"\n5. Cleaning up test data...")
    try:
        async with db.pool.acquire() as conn:
            await conn.execute("DELETE FROM calls WHERE call_sid = $1", "TEST_SID_123")
        print(f"   ✅ Test data cleaned up")
    except Exception as e:
        print(f"   ⚠️  Failed to clean up: {e}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nDatabase service is working correctly!")
    print("Calls should be created and stored properly.")
    return True


if __name__ == "__main__":
    import sys
    success = asyncio.run(test_database_service())
    sys.exit(0 if success else 1)
