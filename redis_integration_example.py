"""Example integration of Redis service with the voice automation system."""

import asyncio
from redis_service import initialize_redis, get_redis_service, shutdown_redis


async def example_call_flow():
    """Demonstrate Redis service usage in a typical call flow."""
    
    # Initialize Redis (done once at application startup)
    await initialize_redis()
    redis = get_redis_service()
    
    # Simulate an incoming call
    call_sid = "CA1234567890abcdef"
    caller_phone = "+1234567890"
    
    print("=== Incoming Call ===")
    print(f"Call SID: {call_sid}")
    print(f"Caller: {caller_phone}")
    
    # 1. Check caller history
    print("\n=== Checking Caller History ===")
    history = await redis.get_caller_history(caller_phone)
    if history:
        print(f"Returning caller! Previous calls: {len(history)}")
        print(f"Most recent call IDs: {history[:3]}")
    else:
        print("New caller - no previous history")
    
    # 2. Store session state
    print("\n=== Storing Session State ===")
    session_data = {
        "call_id": "uuid-call-123",
        "stream_sid": "MZ1234567890",
        "caller_phone": caller_phone,
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [],
        "latest_media_timestamp": 0
    }
    await redis.set_session_state(call_sid, session_data)
    print("Session state cached successfully")
    
    # 3. Simulate conversation and intent detection
    print("\n=== Conversation Progress ===")
    session_data["intent"] = "sales_inquiry"
    session_data["intent_confidence"] = 0.85
    session_data["conversation_history"] = [
        {"role": "assistant", "content": "Hello! How can I help you today?"},
        {"role": "user", "content": "I'm interested in your product pricing"}
    ]
    await redis.set_session_state(call_sid, session_data)
    print("Intent detected: sales_inquiry (confidence: 0.85)")
    
    # 4. Check agent availability for potential transfer
    print("\n=== Checking Agent Availability ===")
    
    # Simulate setting agent statuses
    await redis.set_agent_availability("agent_001", "available")
    await redis.set_agent_availability("agent_002", "busy")
    await redis.set_agent_availability("agent_003", "offline")
    
    all_agents = await redis.get_all_agents_availability()
    print(f"Agent statuses: {all_agents}")
    
    available_agents = [
        agent_id for agent_id, status in all_agents.items() 
        if status == "available"
    ]
    print(f"Available agents: {available_agents}")
    
    # 5. Load business configuration
    print("\n=== Loading Business Configuration ===")
    
    # Simulate business config
    business_config = {
        "business_id": "business_001",
        "business_hours": {
            "monday": "9:00-17:00",
            "tuesday": "9:00-17:00",
            "wednesday": "9:00-17:00",
            "thursday": "9:00-17:00",
            "friday": "9:00-17:00"
        },
        "greeting_message": "Thank you for calling! How may I assist you?",
        "routing_rules": {
            "sales_inquiry": {"priority": 1, "transfer_enabled": True},
            "support_request": {"priority": 2, "transfer_enabled": True}
        }
    }
    
    await redis.set_business_config("business_001", business_config)
    print("Business configuration cached")
    
    # Retrieve from cache
    cached_config = await redis.get_business_config("business_001")
    print(f"Greeting: {cached_config['greeting_message']}")
    
    # 6. Call completion - add to history
    print("\n=== Call Completion ===")
    await redis.add_caller_history(caller_phone, "uuid-call-123")
    print("Call added to caller history")
    
    # Clean up session
    await redis.delete_session_state(call_sid)
    print("Session state cleaned up")
    
    # Verify history was updated
    updated_history = await redis.get_caller_history(caller_phone)
    print(f"Updated caller history: {len(updated_history)} calls")
    
    # Shutdown Redis (done once at application shutdown)
    await shutdown_redis()
    print("\n=== Redis Connection Closed ===")


async def example_configuration_update():
    """Demonstrate configuration cache invalidation."""
    
    await initialize_redis()
    redis = get_redis_service()
    
    business_id = "business_001"
    
    # Initial configuration
    config_v1 = {
        "greeting_message": "Hello, welcome!",
        "business_hours": {"monday": "9-17"}
    }
    await redis.set_business_config(business_id, config_v1)
    print(f"Cached config v1: {config_v1['greeting_message']}")
    
    # Simulate configuration update in database
    # In real scenario, this would be updated in PostgreSQL
    config_v2 = {
        "greeting_message": "Thank you for calling! How can we help?",
        "business_hours": {"monday": "8-18"}
    }
    
    # Invalidate cache to force reload
    await redis.invalidate_business_config(business_id)
    print("Cache invalidated")
    
    # Set new configuration
    await redis.set_business_config(business_id, config_v2)
    print(f"Cached config v2: {config_v2['greeting_message']}")
    
    await shutdown_redis()


if __name__ == "__main__":
    print("=" * 60)
    print("Redis Service Integration Example")
    print("=" * 60)
    
    # Run example call flow
    asyncio.run(example_call_flow())
    
    print("\n" + "=" * 60)
    print("Configuration Update Example")
    print("=" * 60)
    
    # Run configuration update example
    asyncio.run(example_configuration_update())
