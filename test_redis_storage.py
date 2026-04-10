"""Test Redis storage directly."""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_redis():
    """Test Redis connection and storage."""
    print("Testing Redis storage...")
    
    use_real_redis = os.getenv("USE_REAL_REDIS", "false").lower() == "true"
    print(f"USE_REAL_REDIS: {use_real_redis}")
    
    if use_real_redis:
        from redis_service import RedisService
        redis = RedisService(host="localhost", port=6379)
        await redis.connect()
        print("✅ Connected to real Redis")
        
        # Test set and get
        test_data = {
            "call_id": "test-123",
            "caller_phone": "+1234567890",
            "test": "data"
        }
        
        print("\n✓ Testing set_session_state...")
        result = await redis.set_session_state("TEST_SID_456", test_data)
        print(f"  Set result: {result}")
        
        print("\n✓ Testing get_session_state...")
        retrieved = await redis.get_session_state("TEST_SID_456")
        print(f"  Retrieved: {retrieved}")
        
        if retrieved and retrieved.get("call_id") == "test-123":
            print("\n✅ Redis storage is working correctly!")
        else:
            print("\n❌ Redis storage failed!")
            
        await redis.disconnect()
    else:
        print("❌ USE_REAL_REDIS is false, using mock")

if __name__ == "__main__":
    asyncio.run(test_redis())
