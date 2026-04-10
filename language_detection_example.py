"""
Example: Multi-Language Detection and Switching

This example demonstrates how to integrate language detection and switching
into the call flow using the LanguageManager and CallManager.

Requirements: 2.3, 13.1, 13.2, 13.3, 13.4, 13.5
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from language_manager import LanguageManager
from call_manager import CallManager
from models import Language, CallContext
from database import DatabaseService
from redis_service import RedisService


async def example_automatic_language_detection():
    """
    Example 1: Automatic Language Detection
    
    Demonstrates how the system automatically detects the caller's language
    within the first 10 seconds and updates the session accordingly.
    """
    print("\n=== Example 1: Automatic Language Detection ===\n")
    
    # Initialize services (mock for example)
    database = DatabaseService()
    redis = RedisService()
    language_manager = LanguageManager(
        base_instructions="You are a helpful AI assistant for customer support."
    )
    call_manager = CallManager(database, redis, language_manager)
    
    # Simulate call start
    call_sid = "CA_example_123"
    call_start_time = datetime.now(timezone.utc)
    
    print(f"Call started: {call_sid}")
    print(f"Initial language: English (default)")
    
    # Simulate conversation with Hindi speaker
    conversation_history = [
        {"speaker": "assistant", "text": "Hello, how can I help you?"},
        {"speaker": "caller", "text": "नमस्ते, मुझे अपने ऑर्डर के बारे में जानकारी चाहिए"}
    ]
    
    # Calculate elapsed time (5 seconds into call)
    elapsed_ms = 5000
    
    print(f"\nElapsed time: {elapsed_ms}ms (within 10-second detection window)")
    print(f"Caller spoke: '{conversation_history[1]['text']}'")
    
    # Detect language
    detected_language, confidence = await language_manager.detect_language(
        openai_ws=None,  # Mock
        conversation_history=conversation_history,
        elapsed_time_ms=elapsed_ms
    )
    
    print(f"\nDetection result:")
    print(f"  Language: {detected_language.value if detected_language else 'None'}")
    print(f"  Confidence: {confidence:.2f}")
    
    # Check if automatic switch should happen
    should_ask = await language_manager.should_request_language_selection(
        detected_language,
        confidence
    )
    
    if not should_ask:
        print(f"\n✓ High confidence ({confidence:.2f} >= 0.8)")
        print(f"  Automatically switching to {language_manager.get_language_name(detected_language)}")
        print(f"  Session updated with Hindi instructions")
    else:
        print(f"\n⚠ Low confidence ({confidence:.2f} < 0.8)")
        print(f"  Will ask caller to confirm language preference")


async def example_manual_language_selection():
    """
    Example 2: Manual Language Selection
    
    Demonstrates how the system prompts the caller to select their language
    when automatic detection confidence is low.
    """
    print("\n=== Example 2: Manual Language Selection ===\n")
    
    language_manager = LanguageManager()
    
    # Simulate low-confidence detection
    detected_language = Language.ENGLISH
    confidence = 0.6  # Below 0.8 threshold
    
    print(f"Detected language: {detected_language.value}")
    print(f"Confidence: {confidence:.2f} (below 0.8 threshold)")
    
    # Check if we should ask
    should_ask = await language_manager.should_request_language_selection(
        detected_language,
        confidence
    )
    
    if should_ask:
        print(f"\n⚠ Low confidence - requesting manual selection")
        
        # Get multi-language prompt
        prompt = language_manager.get_language_selection_prompt()
        print(f"\nPrompt to caller:")
        print(f"  '{prompt}'")
        
        # Simulate caller responses
        test_responses = [
            "Hindi please",
            "தமிழ்",
            "I want English",
            "తెలుగు",
            "Bengali"
        ]
        
        print(f"\nParsing different responses:")
        for response in test_responses:
            parsed = language_manager.parse_language_from_text(response)
            if parsed:
                print(f"  '{response}' → {language_manager.get_language_name(parsed)}")
            else:
                print(f"  '{response}' → Not recognized")


async def example_mid_conversation_language_switch():
    """
    Example 3: Mid-Conversation Language Switch
    
    Demonstrates how the system handles language switch requests during
    an ongoing conversation while preserving context.
    """
    print("\n=== Example 3: Mid-Conversation Language Switch ===\n")
    
    language_manager = LanguageManager()
    
    # Create call context with conversation history
    call_context = CallContext(
        call_id="call-123",
        caller_phone="+1234567890",
        language=Language.ENGLISH
    )
    
    # Add conversation history
    call_context.conversation_history = [
        {"speaker": "assistant", "text": "Hello, how can I help you?"},
        {"speaker": "caller", "text": "I need help with my order"},
        {"speaker": "assistant", "text": "I'd be happy to help. What's your order number?"},
        {"speaker": "caller", "text": "Can we switch to Tamil?"}
    ]
    
    print(f"Current language: {call_context.language.value}")
    print(f"Conversation history: {len(call_context.conversation_history)} turns")
    
    # Parse language switch request
    switch_request = "Can we switch to Tamil?"
    requested_language = language_manager.parse_language_from_text(switch_request)
    
    print(f"\nCaller request: '{switch_request}'")
    print(f"Parsed language: {language_manager.get_language_name(requested_language)}")
    
    # Simulate language switch
    print(f"\nSwitching language...")
    success = await language_manager.handle_language_switch_request(
        openai_ws=None,  # Mock
        requested_language=requested_language,
        call_context=call_context
    )
    
    if success:
        print(f"✓ Language switched to {call_context.language.value}")
        print(f"✓ Conversation history preserved: {len(call_context.conversation_history)} turns")
        print(f"✓ Metadata updated:")
        print(f"    - language_switched: {call_context.metadata.get('language_switched')}")
        print(f"    - language_switch_time: {call_context.metadata.get('language_switch_time')}")


async def example_complete_call_flow():
    """
    Example 4: Complete Call Flow with Language Detection
    
    Demonstrates a complete call flow integrating language detection,
    manual selection fallback, and mid-conversation switching.
    """
    print("\n=== Example 4: Complete Call Flow ===\n")
    
    language_manager = LanguageManager(
        base_instructions="You are a helpful customer service assistant."
    )
    
    # Simulate call timeline
    call_start = datetime.now(timezone.utc)
    
    print("📞 Call started")
    print("🔊 Playing greeting: 'Hello, how can I help you today?'")
    
    # Stage 1: First 3 seconds - waiting for caller
    print("\n⏱️  0-3 seconds: Waiting for caller to speak...")
    
    # Stage 2: 3-5 seconds - caller speaks in Telugu
    print("\n⏱️  3-5 seconds: Caller speaks")
    conversation_history = [
        {"speaker": "caller", "text": "నమస్కారం, నాకు సహాయం కావాలి"}
    ]
    
    elapsed_ms = 5000
    language, confidence = await language_manager.detect_language(
        openai_ws=None,
        conversation_history=conversation_history,
        elapsed_time_ms=elapsed_ms
    )
    
    print(f"  Detected: {language_manager.get_language_name(language)} (confidence: {confidence:.2f})")
    
    # Stage 3: 5-6 seconds - automatic language switch
    if confidence >= 0.8:
        print(f"\n⏱️  5-6 seconds: Automatic language switch")
        print(f"  ✓ Session updated to Telugu")
        print(f"  🔊 AI now responds in Telugu")
    
    # Stage 4: 10+ seconds - conversation continues in Telugu
    print(f"\n⏱️  10+ seconds: Conversation continues")
    print(f"  Language: Telugu")
    print(f"  Context: Preserved")
    
    # Stage 5: Mid-conversation - caller requests English
    print(f"\n⏱️  30 seconds: Caller requests language switch")
    print(f"  Caller: 'Can we switch to English?'")
    
    requested = language_manager.parse_language_from_text("switch to English")
    if requested:
        print(f"  ✓ Switching to {language_manager.get_language_name(requested)}")
        print(f"  ✓ Conversation context maintained")
        print(f"  🔊 AI now responds in English")


async def example_supported_languages():
    """
    Example 5: Supported Languages Overview
    
    Displays all supported languages and their configurations.
    """
    print("\n=== Example 5: Supported Languages ===\n")
    
    language_manager = LanguageManager()
    
    print("Supported Languages:")
    print("-" * 60)
    
    for language in language_manager.get_supported_languages():
        config = language_manager.LANGUAGE_CONFIGS[language]
        print(f"\n{config['name']} ({config['code']})")
        print(f"  Voice: {config['voice']}")
        print(f"  Instructions: {config['instructions_suffix']}")
    
    print("\n" + "-" * 60)
    print(f"Total languages supported: {len(language_manager.get_supported_languages())}")
    print(f"Detection window: {language_manager.DETECTION_WINDOW_MS / 1000} seconds")
    print(f"Confidence threshold: {language_manager.DETECTION_CONFIDENCE_THRESHOLD}")


async def main():
    """Run all examples."""
    print("=" * 70)
    print("Multi-Language Detection and Switching Examples")
    print("=" * 70)
    
    await example_automatic_language_detection()
    await example_manual_language_selection()
    await example_mid_conversation_language_switch()
    await example_complete_call_flow()
    await example_supported_languages()
    
    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    # Note: This example uses mock objects for demonstration
    # In production, you would use actual database, redis, and websocket connections
    print("\nNote: This example uses mock objects for demonstration purposes.")
    print("In production, initialize with actual database, redis, and websocket connections.\n")
    
    asyncio.run(main())
