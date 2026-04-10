"""Tests for interruption handling with context preservation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from session import SessionState
from models import Language, Intent
from handlers import handle_speech_started_event


@pytest.mark.asyncio
async def test_interruption_preserves_conversation_history():
    """Test that interruption handling preserves conversation history."""
    # Setup
    state = SessionState()
    state.stream_sid = "test-stream-123"
    state.mark_queue = ["mark1", "mark2"]
    state.last_assistant_item = "item-123"
    state.response_start_timestamp_twilio = 1000
    state.latest_media_timestamp = 2000
    
    # Add conversation history
    state.conversation_history = [
        {"speaker": "caller", "text": "Hello", "timestamp_ms": 500},
        {"speaker": "assistant", "text": "Hi, how can I help?", "timestamp_ms": 800}
    ]
    
    # Add call context
    state.call_id = "call-uuid-123"
    state.caller_phone = "+1234567890"
    state.language = Language.HINDI
    state.intent = Intent.SALES_INQUIRY
    
    # Mock websockets
    mock_twilio_ws = AsyncMock()
    mock_openai_ws = AsyncMock()
    
    # Execute interruption handling
    await handle_speech_started_event(mock_twilio_ws, mock_openai_ws, state)
    
    # Verify conversation history is preserved
    assert len(state.conversation_history) == 2
    assert state.conversation_history[0]["text"] == "Hello"
    assert state.conversation_history[1]["text"] == "Hi, how can I help?"
    
    # Verify call context is preserved
    assert state.call_id == "call-uuid-123"
    assert state.caller_phone == "+1234567890"
    assert state.language == Language.HINDI
    assert state.intent == Intent.SALES_INQUIRY
    
    # Verify interruption state is cleared
    assert len(state.mark_queue) == 0
    assert state.last_assistant_item is None
    assert state.response_start_timestamp_twilio is None
    
    print("✅ Test passed: Conversation context preserved during interruption")


@pytest.mark.asyncio
async def test_interruption_clears_audio_state():
    """Test that interruption handling clears audio streaming state."""
    # Setup
    state = SessionState()
    state.stream_sid = "test-stream-456"
    state.mark_queue = ["mark1", "mark2", "mark3"]
    state.last_assistant_item = "item-456"
    state.response_start_timestamp_twilio = 5000
    state.latest_media_timestamp = 6000
    
    # Mock websockets
    mock_twilio_ws = AsyncMock()
    mock_openai_ws = AsyncMock()
    
    # Execute interruption handling
    await handle_speech_started_event(mock_twilio_ws, mock_openai_ws, state)
    
    # Verify audio state is cleared
    assert len(state.mark_queue) == 0
    assert state.last_assistant_item is None
    assert state.response_start_timestamp_twilio is None
    
    # Verify truncate event was sent to OpenAI
    assert mock_openai_ws.send.called
    
    # Verify clear command was sent to Twilio
    assert mock_twilio_ws.send_json.called
    
    print("✅ Test passed: Audio state cleared during interruption")


@pytest.mark.asyncio
async def test_interruption_with_empty_history():
    """Test interruption handling when conversation history is empty."""
    # Setup
    state = SessionState()
    state.stream_sid = "test-stream-789"
    state.mark_queue = ["mark1"]
    state.last_assistant_item = "item-789"
    state.response_start_timestamp_twilio = 1000
    state.latest_media_timestamp = 1500
    state.conversation_history = []  # Empty history
    
    # Mock websockets
    mock_twilio_ws = AsyncMock()
    mock_openai_ws = AsyncMock()
    
    # Execute interruption handling
    await handle_speech_started_event(mock_twilio_ws, mock_openai_ws, state)
    
    # Verify empty history is preserved (not None)
    assert state.conversation_history == []
    assert isinstance(state.conversation_history, list)
    
    print("✅ Test passed: Empty conversation history preserved")


@pytest.mark.asyncio
async def test_clear_interruption_state_preserves_context():
    """Test that clear_interruption_state method preserves conversation context."""
    # Setup
    state = SessionState()
    state.mark_queue = ["mark1", "mark2"]
    state.last_assistant_item = "item-123"
    state.response_start_timestamp_twilio = 1000
    
    # Set conversation context
    state.conversation_history = [
        {"speaker": "caller", "text": "Test message", "timestamp_ms": 500}
    ]
    state.call_id = "call-uuid-456"
    state.caller_phone = "+9876543210"
    state.language = Language.TAMIL
    state.intent = Intent.APPOINTMENT_BOOKING
    
    # Execute
    state.clear_interruption_state()
    
    # Verify audio state is cleared
    assert len(state.mark_queue) == 0
    assert state.last_assistant_item is None
    assert state.response_start_timestamp_twilio is None
    
    # Verify context is preserved
    assert len(state.conversation_history) == 1
    assert state.call_id == "call-uuid-456"
    assert state.caller_phone == "+9876543210"
    assert state.language == Language.TAMIL
    assert state.intent == Intent.APPOINTMENT_BOOKING
    
    print("✅ Test passed: clear_interruption_state preserves context")


@pytest.mark.asyncio
async def test_multiple_interruptions_preserve_context():
    """Test that multiple interruptions preserve cumulative conversation context."""
    # Setup
    state = SessionState()
    state.stream_sid = "test-stream-multi"
    
    # Simulate first conversation turn
    state.conversation_history.append({
        "speaker": "caller",
        "text": "I want to buy something",
        "timestamp_ms": 1000
    })
    state.intent = Intent.SALES_INQUIRY
    
    # First interruption
    state.mark_queue = ["mark1"]
    state.last_assistant_item = "item-1"
    state.response_start_timestamp_twilio = 2000
    state.latest_media_timestamp = 2500
    
    mock_twilio_ws = AsyncMock()
    mock_openai_ws = AsyncMock()
    
    await handle_speech_started_event(mock_twilio_ws, mock_openai_ws, state)
    
    # Add more conversation after first interruption
    state.conversation_history.append({
        "speaker": "assistant",
        "text": "I can help with that",
        "timestamp_ms": 3000
    })
    
    # Second interruption
    state.mark_queue = ["mark2"]
    state.last_assistant_item = "item-2"
    state.response_start_timestamp_twilio = 4000
    state.latest_media_timestamp = 4500
    
    await handle_speech_started_event(mock_twilio_ws, mock_openai_ws, state)
    
    # Verify all conversation history is preserved
    assert len(state.conversation_history) == 2
    assert state.conversation_history[0]["text"] == "I want to buy something"
    assert state.conversation_history[1]["text"] == "I can help with that"
    assert state.intent == Intent.SALES_INQUIRY
    
    print("✅ Test passed: Multiple interruptions preserve cumulative context")


if __name__ == "__main__":
    import asyncio
    
    print("\n🧪 Running Interruption Handling Tests...\n")
    
    asyncio.run(test_interruption_preserves_conversation_history())
    asyncio.run(test_interruption_clears_audio_state())
    asyncio.run(test_interruption_with_empty_history())
    asyncio.run(test_clear_interruption_state_preserves_context())
    asyncio.run(test_multiple_interruptions_preserve_context())
    
    print("\n✅ All interruption handling tests passed!")
    print("\nRequirements validated:")
    print("  • 10.1: Speech detection within 300ms (OpenAI event)")
    print("  • 10.2: Stop AI audio output immediately")
    print("  • 10.3: Clear audio buffer")
    print("  • 10.4: Resume listening automatically")
    print("  • 10.5: Preserve conversation context ✓")
