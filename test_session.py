"""Unit tests for SessionState class."""

import pytest
from session import SessionState
from models import Language, Intent


class TestSessionState:
    """Test SessionState class functionality."""
    
    def test_initialization_defaults(self):
        """Test SessionState initializes with correct defaults."""
        state = SessionState()
        
        assert state.stream_sid is None
        assert state.latest_media_timestamp == 0
        assert state.last_assistant_item is None
        assert state.mark_queue == []
        assert state.response_start_timestamp_twilio is None
        assert state.call_id is None
        assert state.caller_phone is None
        assert state.language == Language.ENGLISH
        assert state.intent is None
        assert state.conversation_history == []
    
    def test_reset_on_stream_start(self):
        """Test reset_on_stream_start resets streaming state."""
        state = SessionState()
        state.stream_sid = "old_sid"
        state.latest_media_timestamp = 1000
        state.last_assistant_item = "item_123"
        state.response_start_timestamp_twilio = 500
        
        state.reset_on_stream_start("new_sid")
        
        assert state.stream_sid == "new_sid"
        assert state.latest_media_timestamp == 0
        assert state.last_assistant_item is None
        assert state.response_start_timestamp_twilio is None
    
    def test_clear_interruption_state(self):
        """Test clear_interruption_state clears interruption-related fields."""
        state = SessionState()
        state.mark_queue = ["mark1", "mark2"]
        state.last_assistant_item = "item_456"
        state.response_start_timestamp_twilio = 1000
        
        state.clear_interruption_state()
        
        assert state.mark_queue == []
        assert state.last_assistant_item is None
        assert state.response_start_timestamp_twilio is None
    
    def test_update_call_context_all_fields(self):
        """Test update_call_context updates all provided fields."""
        state = SessionState()
        
        state.update_call_context(
            call_id="call_123",
            caller_phone="+1234567890",
            language=Language.HINDI,
            intent=Intent.SALES_INQUIRY
        )
        
        assert state.call_id == "call_123"
        assert state.caller_phone == "+1234567890"
        assert state.language == Language.HINDI
        assert state.intent == Intent.SALES_INQUIRY
    
    def test_update_call_context_partial_fields(self):
        """Test update_call_context updates only provided fields."""
        state = SessionState()
        state.call_id = "existing_call"
        state.caller_phone = "+9876543210"
        
        state.update_call_context(language=Language.TAMIL)
        
        assert state.call_id == "existing_call"
        assert state.caller_phone == "+9876543210"
        assert state.language == Language.TAMIL
        assert state.intent is None
    
    def test_add_conversation_turn_with_timestamp(self):
        """Test add_conversation_turn adds turn with provided timestamp."""
        state = SessionState()
        
        state.add_conversation_turn(
            speaker="caller",
            text="Hello, I need help",
            timestamp_ms=5000
        )
        
        assert len(state.conversation_history) == 1
        assert state.conversation_history[0]["speaker"] == "caller"
        assert state.conversation_history[0]["text"] == "Hello, I need help"
        assert state.conversation_history[0]["timestamp_ms"] == 5000
    
    def test_add_conversation_turn_without_timestamp(self):
        """Test add_conversation_turn uses latest_media_timestamp when timestamp not provided."""
        state = SessionState()
        state.latest_media_timestamp = 3000
        
        state.add_conversation_turn(
            speaker="assistant",
            text="How can I help you?"
        )
        
        assert len(state.conversation_history) == 1
        assert state.conversation_history[0]["timestamp_ms"] == 3000
    
    def test_add_multiple_conversation_turns(self):
        """Test adding multiple conversation turns maintains order."""
        state = SessionState()
        
        state.add_conversation_turn("caller", "Hello", 1000)
        state.add_conversation_turn("assistant", "Hi there", 2000)
        state.add_conversation_turn("caller", "I need help", 3000)
        
        assert len(state.conversation_history) == 3
        assert state.conversation_history[0]["speaker"] == "caller"
        assert state.conversation_history[1]["speaker"] == "assistant"
        assert state.conversation_history[2]["speaker"] == "caller"
    
    def test_get_conversation_history_returns_copy(self):
        """Test get_conversation_history returns a copy, not reference."""
        state = SessionState()
        state.add_conversation_turn("caller", "Test", 1000)
        
        history = state.get_conversation_history()
        history.append({"speaker": "fake", "text": "fake", "timestamp_ms": 9999})
        
        assert len(state.conversation_history) == 1
        assert len(history) == 2
    
    def test_clear_conversation_history(self):
        """Test clear_conversation_history removes all turns."""
        state = SessionState()
        state.add_conversation_turn("caller", "Turn 1", 1000)
        state.add_conversation_turn("assistant", "Turn 2", 2000)
        
        state.clear_conversation_history()
        
        assert state.conversation_history == []
    
    def test_conversation_history_with_call_context(self):
        """Test conversation history works alongside call context updates."""
        state = SessionState()
        
        state.update_call_context(
            call_id="call_789",
            caller_phone="+1112223333",
            language=Language.ENGLISH,
            intent=Intent.APPOINTMENT_BOOKING
        )
        
        state.add_conversation_turn("caller", "I want to book an appointment", 1000)
        state.add_conversation_turn("assistant", "I can help with that", 2000)
        
        assert state.call_id == "call_789"
        assert state.intent == Intent.APPOINTMENT_BOOKING
        assert len(state.conversation_history) == 2
