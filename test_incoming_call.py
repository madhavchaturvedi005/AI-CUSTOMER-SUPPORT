"""Test if /incoming-call endpoint is working."""
import asyncio
import sys

async def test_incoming_call():
    """Test the incoming call flow."""
    print("Testing /incoming-call endpoint...")
    
    # Import after adding to path
    from main import app, call_manager, redis_service, database_service
    from unittest.mock import AsyncMock
    
    # Check if services are initialized
    print(f"\n✓ Services initialized:")
    print(f"  - call_manager: {type(call_manager).__name__}")
    print(f"  - redis_service: {type(redis_service).__name__}")
    print(f"  - database_service: {type(database_service).__name__}")
    
    # Test initiate_call directly
    print(f"\n✓ Testing initiate_call()...")
    try:
        context = await call_manager.initiate_call(
            call_sid="TEST_CALL_SID_123",
            caller_phone="+1234567890",
            direction="inbound"
        )
        print(f"  ✅ Call initiated: {context.call_id}")
        print(f"  ✅ Call SID: TEST_CALL_SID_123")
        
        # Check if it's in Redis
        print(f"\n✓ Checking Redis...")
        cached = await redis_service.get_session_state("TEST_CALL_SID_123")
        if cached:
            print(f"  ✅ Found in Redis: {cached.get('call_id')}")
        else:
            print(f"  ❌ NOT found in Redis!")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_incoming_call())
