"""
Example integration of greeting message playback with CallManager.

This example demonstrates how to:
1. Initialize CallManager with database and Redis services
2. Retrieve business-specific greeting message
3. Send greeting to OpenAI for playback
4. Handle greeting completion

Requirements: 1.2, 17.1
"""

import asyncio
import websockets
from call_manager import CallManager
from database import DatabaseService
from redis_service import RedisService
from utils import send_greeting_message


async def example_greeting_flow():
    """
    Example flow showing greeting message playback on call answer.
    """
    # Initialize services (in production, these would be initialized at app startup)
    database = DatabaseService(
        host="localhost",
        port=5432,
        database="voice_automation",
        user="postgres",
        password="your_password"
    )
    await database.connect()
    
    redis = RedisService(
        host="localhost",
        port=6379
    )
    await redis.connect()
    
    # Initialize CallManager
    call_manager = CallManager(database=database, redis=redis)
    
    # Simulate call initiation
    call_sid = "CA1234567890abcdef"
    caller_phone = "+1234567890"
    
    # Step 1: Initiate call
    context = await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone=caller_phone,
        direction="inbound"
    )
    print(f"Call initiated: {context.call_id}")
    
    # Step 2: Answer call (within 3 seconds of receiving)
    await call_manager.answer_call(call_sid)
    print("Call answered")
    
    # Step 3: Retrieve greeting message
    # Use business_id from configuration or default
    business_id = "default"
    greeting_message = await call_manager.get_greeting_message(business_id)
    print(f"Greeting message: {greeting_message}")
    
    # Step 4: Send greeting to OpenAI for playback
    # In production, this would be called within the WebSocket handler
    # Here we show the structure
    print("In production, send greeting via:")
    print(f"  await send_greeting_message(openai_ws, '{greeting_message}')")
    
    # Step 5: Greeting completion is handled automatically
    # The response.done event indicates greeting playback is complete
    # System then listens for caller speech via server VAD
    
    # Cleanup
    await database.disconnect()
    await redis.disconnect()


async def example_with_websocket(openai_ws: websockets.WebSocketClientProtocol):
    """
    Example showing greeting integration within WebSocket handler.
    
    This would be called from handle_media_stream in main.py after
    the OpenAI session is initialized.
    
    Args:
        openai_ws: WebSocket connection to OpenAI
    """
    # Initialize services
    database = DatabaseService()
    await database.connect()
    
    redis = RedisService()
    await redis.connect()
    
    call_manager = CallManager(database=database, redis=redis)
    
    # Get call context (from Twilio stream start event)
    call_sid = "CA1234567890abcdef"
    
    # Retrieve greeting
    greeting = await call_manager.get_greeting_message("default")
    
    # Send greeting to OpenAI for playback
    # This happens within 3 seconds of call answer
    await send_greeting_message(openai_ws, greeting)
    
    print("Greeting sent to OpenAI for playback")
    print("System will automatically listen for caller speech after greeting completes")


if __name__ == "__main__":
    print("Greeting Integration Example")
    print("=" * 50)
    print()
    print("This example shows how to integrate greeting message playback")
    print("with the CallManager and OpenAI Realtime API.")
    print()
    
    # Run example
    asyncio.run(example_greeting_flow())
