"""
Example: Using Conversation History Retrieval for Returning Callers

This example demonstrates how to use the conversation history retrieval
functionality to provide personalized experiences for returning callers.

Requirements: 9.1, 9.2, 9.3
"""

import asyncio
from call_manager import CallManager
from database import initialize_database
from redis_service import initialize_redis


async def example_returning_caller_flow():
    """
    Example flow for handling a returning caller with conversation history.
    """
    
    # Initialize services
    database = await initialize_database()
    redis = await initialize_redis()
    
    # Create call manager
    call_manager = CallManager(database=database, redis=redis)
    
    # Simulate an incoming call
    call_sid = "CA1234567890abcdef"
    caller_phone = "+1234567890"
    
    print("=" * 60)
    print("INCOMING CALL")
    print("=" * 60)
    
    # Step 1: Initiate the call
    print(f"\n1. Initiating call from {caller_phone}...")
    context = await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone=caller_phone,
        direction="inbound"
    )
    print(f"   ✓ Call initiated with ID: {context.call_id}")
    
    # Step 2: Check if this is a returning caller and integrate history
    print(f"\n2. Checking for conversation history...")
    has_history = await call_manager.integrate_conversation_history(
        call_sid=call_sid,
        caller_phone=caller_phone
    )
    
    if has_history:
        print("   ✓ Returning caller detected!")
        
        # Get conversation summary
        summary = await call_manager.get_conversation_summary(call_sid)
        print(f"\n   Conversation Summary:")
        print(f"   {summary}")
        
        # Get detailed history
        context = await call_manager.get_call_context(call_sid)
        history = context.metadata.get("conversation_history", [])
        
        print(f"\n   Previous Calls: {len(history)}")
        for i, call in enumerate(history, 1):
            print(f"\n   Call {i}:")
            print(f"   - Date: {call.get('started_at')}")
            print(f"   - Intent: {call.get('intent')}")
            print(f"   - Duration: {call.get('duration_seconds')}s")
            print(f"   - Transcript entries: {len(call.get('transcripts', []))}")
            
            # Show first few transcript entries
            transcripts = call.get('transcripts', [])[:3]
            if transcripts:
                print(f"   - Sample conversation:")
                for t in transcripts:
                    print(f"     {t['speaker']}: {t['text'][:50]}...")
    else:
        print("   ✓ New caller - no previous history")
    
    # Step 3: Answer the call
    print(f"\n3. Answering call...")
    await call_manager.answer_call(call_sid)
    print("   ✓ Call answered")
    
    # Step 4: Get personalized greeting
    greeting = await call_manager.get_greeting_message()
    
    if has_history:
        # Customize greeting for returning caller
        context = await call_manager.get_call_context(call_sid)
        previous_intents = context.metadata.get("previous_intents", [])
        
        if "sales_inquiry" in previous_intents:
            greeting = (
                "Welcome back! I see you've contacted us before about our products. "
                "How can I help you today?"
            )
        elif "support_request" in previous_intents:
            greeting = (
                "Welcome back! I hope your previous issue was resolved. "
                "What can I help you with today?"
            )
    
    print(f"\n4. Playing greeting:")
    print(f"   \"{greeting}\"")
    
    # Step 5: Simulate conversation
    print(f"\n5. Conversation in progress...")
    await call_manager.add_conversation_turn(
        call_sid=call_sid,
        speaker="caller",
        text="I want to follow up on my previous inquiry"
    )
    
    await call_manager.add_conversation_turn(
        call_sid=call_sid,
        speaker="assistant",
        text="Of course! Let me pull up your previous conversation..."
    )
    
    print("   ✓ Conversation turns recorded")
    
    # Step 6: Complete the call
    print(f"\n6. Completing call...")
    await call_manager.complete_call(
        call_sid=call_sid,
        recording_url="https://example.com/recordings/call123.wav"
    )
    print("   ✓ Call completed")
    
    print("\n" + "=" * 60)
    print("CALL COMPLETED")
    print("=" * 60)


async def example_retrieve_history_manually():
    """
    Example of manually retrieving conversation history.
    """
    
    # Initialize services
    database = await initialize_database()
    redis = await initialize_redis()
    
    # Create call manager
    call_manager = CallManager(database=database, redis=redis)
    
    caller_phone = "+1234567890"
    
    print("\n" + "=" * 60)
    print("MANUAL HISTORY RETRIEVAL")
    print("=" * 60)
    
    # Retrieve conversation history with custom parameters
    print(f"\nRetrieving history for {caller_phone}...")
    print("Parameters: last 60 days, max 10 calls")
    
    history = await call_manager.retrieve_conversation_history(
        caller_phone=caller_phone,
        days=60,
        max_calls=10
    )
    
    if history:
        print(f"\nFound {len(history)} previous calls:")
        
        for i, call in enumerate(history, 1):
            print(f"\n{i}. Call on {call.get('started_at')}")
            print(f"   Intent: {call.get('intent')} (confidence: {call.get('intent_confidence')})")
            print(f"   Duration: {call.get('duration_seconds')}s")
            print(f"   Transcript entries: {len(call.get('transcripts', []))}")
            
            # Analyze conversation
            transcripts = call.get('transcripts', [])
            caller_messages = [t for t in transcripts if t['speaker'] == 'caller']
            assistant_messages = [t for t in transcripts if t['speaker'] == 'assistant']
            
            print(f"   Caller messages: {len(caller_messages)}")
            print(f"   Assistant messages: {len(assistant_messages)}")
    else:
        print("\nNo previous calls found")
    
    print("\n" + "=" * 60)


async def example_personalized_ai_context():
    """
    Example of using conversation history to provide context to AI assistant.
    """
    
    # Initialize services
    database = await initialize_database()
    redis = await initialize_redis()
    
    # Create call manager
    call_manager = CallManager(database=database, redis=redis)
    
    call_sid = "CA_example_123"
    caller_phone = "+1234567890"
    
    print("\n" + "=" * 60)
    print("AI CONTEXT PERSONALIZATION")
    print("=" * 60)
    
    # Initiate call
    await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone=caller_phone,
        direction="inbound"
    )
    
    # Integrate history
    has_history = await call_manager.integrate_conversation_history(
        call_sid=call_sid,
        caller_phone=caller_phone
    )
    
    # Build AI context
    context = await call_manager.get_call_context(call_sid)
    
    ai_system_prompt = "You are a helpful AI assistant."
    
    if has_history:
        summary = await call_manager.get_conversation_summary(call_sid)
        
        # Add history context to AI prompt
        ai_system_prompt += f"\n\nCaller History: {summary}"
        
        # Add specific context from previous conversations
        history = context.metadata.get("conversation_history", [])
        if history:
            recent_call = history[0]
            recent_intent = recent_call.get("intent")
            
            if recent_intent == "sales_inquiry":
                ai_system_prompt += (
                    "\n\nNote: This caller previously inquired about purchasing. "
                    "Be prepared to discuss product details and pricing."
                )
            elif recent_intent == "support_request":
                ai_system_prompt += (
                    "\n\nNote: This caller previously had a support issue. "
                    "Ask if their previous issue was resolved."
                )
    
    print("\nAI System Prompt:")
    print("-" * 60)
    print(ai_system_prompt)
    print("-" * 60)
    
    print("\n✓ AI assistant now has personalized context for this caller")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CONVERSATION HISTORY RETRIEVAL EXAMPLES")
    print("=" * 60)
    
    print("\nThese examples demonstrate:")
    print("1. Automatic history integration for returning callers")
    print("2. Manual history retrieval with custom parameters")
    print("3. Using history to personalize AI assistant context")
    
    print("\n" + "=" * 60)
    print("Note: These examples require a running PostgreSQL and Redis instance")
    print("with the appropriate schema and test data.")
    print("=" * 60)
    
    # Uncomment to run examples:
    # asyncio.run(example_returning_caller_flow())
    # asyncio.run(example_retrieve_history_manually())
    # asyncio.run(example_personalized_ai_context())
