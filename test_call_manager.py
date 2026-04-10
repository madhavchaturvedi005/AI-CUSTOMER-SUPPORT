"""Unit tests for CallManager class."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from call_manager import CallManager
from models import CallStatus, CallContext, Intent, Language
from database import DatabaseService
from redis_service import RedisService


@pytest.fixture
def mock_database():
    """Create a mock DatabaseService."""
    db = AsyncMock(spec=DatabaseService)
    return db


@pytest.fixture
def mock_redis():
    """Create a mock RedisService."""
    redis = AsyncMock(spec=RedisService)
    return redis


@pytest.fixture
def call_manager(mock_database, mock_redis):
    """Create a CallManager instance with mocked dependencies."""
    return CallManager(database=mock_database, redis=mock_redis)


@pytest.mark.asyncio
async def test_initiate_call_creates_database_record(call_manager, mock_database, mock_redis):
    """Test that initiating a call creates a database record."""
    # Arrange
    call_sid = "CA1234567890"
    caller_phone = "+1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    
    mock_database.create_call.return_value = call_id
    
    # Act
    context = await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone=caller_phone
    )
    
    # Assert
    mock_database.create_call.assert_called_once()
    assert context.call_id == call_id
    assert context.caller_phone == caller_phone
    assert context.language == Language.ENGLISH


@pytest.mark.asyncio
async def test_initiate_call_caches_context_in_redis(call_manager, mock_database, mock_redis):
    """Test that initiating a call caches context in Redis."""
    # Arrange
    call_sid = "CA1234567890"
    caller_phone = "+1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    
    mock_database.create_call.return_value = call_id
    
    # Act
    await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone=caller_phone
    )
    
    # Assert
    mock_redis.set_session_state.assert_called_once()
    call_args = mock_redis.set_session_state.call_args
    assert call_args[0][0] == call_sid
    assert call_args[0][1]["call_id"] == call_id


@pytest.mark.asyncio
async def test_initiate_call_adds_to_caller_history(call_manager, mock_database, mock_redis):
    """Test that initiating a call adds to caller history."""
    # Arrange
    call_sid = "CA1234567890"
    caller_phone = "+1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    
    mock_database.create_call.return_value = call_id
    
    # Act
    await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone=caller_phone
    )
    
    # Assert
    mock_redis.add_caller_history.assert_called_once_with(caller_phone, call_id)


@pytest.mark.asyncio
async def test_answer_call_transitions_to_in_progress(call_manager, mock_database, mock_redis):
    """Test that answering a call transitions status to in_progress."""
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # Mock get_call_context
    mock_context = CallContext(
        call_id=call_id,
        caller_phone="+1234567890"
    )
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Act
    result = await call_manager.answer_call(call_sid)
    
    # Assert
    assert result is True
    mock_database.update_call_status.assert_called_once()
    call_args = mock_database.update_call_status.call_args
    assert call_args[1]["status"] == CallStatus.IN_PROGRESS.value


@pytest.mark.asyncio
async def test_answer_call_raises_error_if_context_not_found(call_manager, mock_redis):
    """Test that answering a call raises error if context not found."""
    # Arrange
    call_sid = "CA1234567890"
    mock_redis.get_session_state.return_value = None
    
    # Act & Assert
    with pytest.raises(ValueError, match="Call context not found"):
        await call_manager.answer_call(call_sid)


@pytest.mark.asyncio
async def test_update_call_intent_updates_database_and_cache(call_manager, mock_database, mock_redis):
    """Test that updating intent updates both database and cache."""
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    intent = Intent.SALES_INQUIRY
    confidence = 0.85
    
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Act
    result = await call_manager.update_call_intent(call_sid, intent, confidence)
    
    # Assert
    assert result is True
    mock_database.update_call_intent.assert_called_once_with(
        call_id=call_id,
        intent=intent.value,
        intent_confidence=confidence
    )
    mock_redis.set_session_state.assert_called_once()


@pytest.mark.asyncio
async def test_add_conversation_turn_appends_to_history(call_manager, mock_redis):
    """Test that adding a conversation turn appends to history."""
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    speaker = "caller"
    text = "Hello, I need help"
    
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Act
    result = await call_manager.add_conversation_turn(call_sid, speaker, text)
    
    # Assert
    assert result is True
    mock_redis.set_session_state.assert_called_once()
    call_args = mock_redis.set_session_state.call_args
    conversation_history = call_args[0][1]["conversation_history"]
    assert len(conversation_history) == 1
    assert conversation_history[0]["speaker"] == speaker
    assert conversation_history[0]["text"] == text


@pytest.mark.asyncio
async def test_complete_call_calculates_duration(call_manager, mock_database, mock_redis):
    """Test that completing a call calculates duration correctly."""
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    started_at = datetime.now(timezone.utc)
    
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": started_at.isoformat()
    }
    
    # Act
    result = await call_manager.complete_call(call_sid)
    
    # Assert
    assert result is True
    mock_database.update_call_status.assert_called_once()
    call_args = mock_database.update_call_status.call_args
    assert call_args[1]["status"] == CallStatus.COMPLETED.value
    assert call_args[1]["duration_seconds"] is not None


@pytest.mark.asyncio
async def test_complete_call_updates_recording_urls(call_manager, mock_database, mock_redis):
    """Test that completing a call updates recording URLs."""
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    recording_url = "https://example.com/recording.wav"
    transcript_url = "https://example.com/transcript.json"
    
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Act
    result = await call_manager.complete_call(
        call_sid,
        recording_url=recording_url,
        transcript_url=transcript_url
    )
    
    # Assert
    assert result is True
    mock_database.update_call_recording.assert_called_once_with(
        call_id=call_id,
        recording_url=recording_url,
        transcript_url=transcript_url
    )


@pytest.mark.asyncio
async def test_fail_call_marks_as_failed(call_manager, mock_database, mock_redis):
    """Test that failing a call marks it as failed."""
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    error_message = "Connection lost"
    
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Act
    result = await call_manager.fail_call(call_sid, error_message)
    
    # Assert
    assert result is True
    mock_database.update_call_status.assert_called_once()
    call_args = mock_database.update_call_status.call_args
    assert call_args[1]["status"] == CallStatus.FAILED.value


@pytest.mark.asyncio
async def test_get_call_context_reconstructs_from_redis(call_manager, mock_redis):
    """Test that get_call_context reconstructs CallContext from Redis."""
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "caller_name": "John Doe",
        "language": "en",
        "intent": "sales_inquiry",
        "intent_confidence": 0.85,
        "conversation_history": [{"speaker": "caller", "text": "Hello"}],
        "metadata": {"test": "value"},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Act
    context = await call_manager.get_call_context(call_sid)
    
    # Assert
    assert context is not None
    assert context.call_id == call_id
    assert context.caller_phone == "+1234567890"
    assert context.caller_name == "John Doe"
    assert context.intent == Intent.SALES_INQUIRY
    assert context.intent_confidence == 0.85


@pytest.mark.asyncio
async def test_get_call_context_returns_none_if_not_found(call_manager, mock_redis):
    """Test that get_call_context returns None if not found."""
    # Arrange
    call_sid = "CA1234567890"
    mock_redis.get_session_state.return_value = None
    
    # Act
    context = await call_manager.get_call_context(call_sid)
    
    # Assert
    assert context is None


@pytest.mark.asyncio
async def test_get_caller_history_from_redis_and_database(call_manager, mock_database, mock_redis):
    """Test that get_caller_history retrieves from Redis and database."""
    # Arrange
    caller_phone = "+1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    
    mock_redis.get_caller_history.return_value = [call_id]
    mock_database.get_call.return_value = {
        "id": call_id,
        "caller_phone": caller_phone,
        "status": "completed"
    }
    
    # Act
    history = await call_manager.get_caller_history(caller_phone)
    
    # Assert
    assert len(history) == 1
    assert history[0]["id"] == call_id
    mock_redis.get_caller_history.assert_called_once()
    mock_database.get_call.assert_called_once_with(call_id)


@pytest.mark.asyncio
async def test_get_caller_history_falls_back_to_database(call_manager, mock_database, mock_redis):
    """Test that get_caller_history falls back to database if Redis is empty."""
    # Arrange
    caller_phone = "+1234567890"
    
    mock_redis.get_caller_history.return_value = []
    mock_database.get_caller_history.return_value = [
        {"id": "call1", "caller_phone": caller_phone}
    ]
    
    # Act
    history = await call_manager.get_caller_history(caller_phone)
    
    # Assert
    assert len(history) == 1
    mock_database.get_caller_history.assert_called_once_with(caller_phone, 10)


@pytest.mark.asyncio
async def test_concurrent_call_handling(call_manager, mock_database, mock_redis):
    """Test that CallManager can handle multiple concurrent calls."""
    # Arrange
    call_sids = ["CA001", "CA002", "CA003"]
    call_ids = ["id001", "id002", "id003"]
    
    mock_database.create_call.side_effect = call_ids
    
    # Act - Initiate multiple calls concurrently
    import asyncio
    contexts = await asyncio.gather(*[
        call_manager.initiate_call(
            call_sid=sid,
            caller_phone=f"+123456789{i}"
        )
        for i, sid in enumerate(call_sids)
    ])
    
    # Assert
    assert len(contexts) == 3
    assert mock_database.create_call.call_count == 3
    assert mock_redis.set_session_state.call_count == 3



# Tests for clarification logic (Task 3.3)

class MockIntentDetector:
    """Mock intent detector for testing clarification logic."""
    
    def __init__(self, intent: Intent = Intent.UNKNOWN, confidence: float = 0.5):
        self.intent = intent
        self.confidence = confidence
        self.detect_count = 0
    
    async def detect_intent(self, conversation_history, current_transcript):
        """Mock detect_intent that returns configured values."""
        self.detect_count += 1
        # On second call (after clarification), return higher confidence
        if self.detect_count > 1:
            return (self.intent, 0.85)
        return (self.intent, self.confidence)
    
    async def request_clarification(self, current_intent, confidence):
        """Mock request_clarification."""
        return f"Could you clarify if you need {current_intent.value}?"


@pytest.mark.asyncio
async def test_handle_intent_with_clarification_high_confidence(call_manager, mock_database, mock_redis):
    """Test that high confidence intent does not trigger clarification.
    
    **Validates: Requirement 3.4** - No clarification when confidence >= 0.7
    """
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Create mock detector with high confidence
    detector = MockIntentDetector(intent=Intent.SALES_INQUIRY, confidence=0.85)
    
    # Act
    intent, confidence, clarification = await call_manager.handle_intent_with_clarification(
        call_sid=call_sid,
        intent_detector=detector,
        conversation_history=[],
        current_transcript="I want to buy your product"
    )
    
    # Assert
    assert intent == Intent.SALES_INQUIRY
    assert confidence == 0.85
    assert clarification is None  # No clarification needed


@pytest.mark.asyncio
async def test_handle_intent_with_clarification_low_confidence(call_manager, mock_database, mock_redis):
    """Test that low confidence intent triggers clarification request.
    
    **Validates: Requirement 3.4** - Request clarification when confidence < 0.7
    """
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Create mock detector with low confidence
    detector = MockIntentDetector(intent=Intent.UNKNOWN, confidence=0.5)
    
    # Act
    intent, confidence, clarification = await call_manager.handle_intent_with_clarification(
        call_sid=call_sid,
        intent_detector=detector,
        conversation_history=[],
        current_transcript="Hello"
    )
    
    # Assert
    assert intent == Intent.UNKNOWN
    assert confidence == 0.5
    assert clarification is not None
    assert "clarify" in clarification.lower()
    assert "unknown" in clarification.lower()


@pytest.mark.asyncio
async def test_handle_intent_with_clarification_threshold_boundary(call_manager, mock_database, mock_redis):
    """Test clarification at exactly 0.7 threshold.
    
    **Validates: Requirement 3.4** - Threshold boundary behavior
    """
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Test at exactly 0.7 - should NOT trigger clarification
    detector = MockIntentDetector(intent=Intent.SALES_INQUIRY, confidence=0.7)
    
    # Act
    intent, confidence, clarification = await call_manager.handle_intent_with_clarification(
        call_sid=call_sid,
        intent_detector=detector,
        conversation_history=[],
        current_transcript="I'm interested"
    )
    
    # Assert
    assert confidence == 0.7
    assert clarification is None  # No clarification at exactly 0.7


@pytest.mark.asyncio
async def test_handle_intent_with_clarification_updates_metadata(call_manager, mock_database, mock_redis):
    """Test that clarification request updates call metadata.
    
    **Validates: Requirement 3.4** - Metadata tracking
    """
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Create mock detector with low confidence
    detector = MockIntentDetector(intent=Intent.SUPPORT_REQUEST, confidence=0.6)
    
    # Act
    await call_manager.handle_intent_with_clarification(
        call_sid=call_sid,
        intent_detector=detector,
        conversation_history=[],
        current_transcript="I need something"
    )
    
    # Assert - Check that metadata was updated
    mock_redis.set_session_state.assert_called()
    call_args = mock_redis.set_session_state.call_args
    metadata = call_args[0][1]["metadata"]
    assert metadata["clarification_requested"] is True
    assert "clarification_question" in metadata


@pytest.mark.asyncio
async def test_update_intent_after_clarification(call_manager, mock_database, mock_redis):
    """Test that intent is updated after clarification response.
    
    **Validates: Requirement 3.4** - Update intent after clarification
    """
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent": "unknown",
        "intent_confidence": 0.5,
        "conversation_history": [
            {"speaker": "assistant", "text": "Could you clarify?", "timestamp_ms": 1000}
        ],
        "metadata": {
            "clarification_requested": True
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Create mock detector that returns higher confidence on second call
    # Note: This is the first call in this test, but we simulate it being after clarification
    detector = MockIntentDetector(intent=Intent.SALES_INQUIRY, confidence=0.5)
    # Simulate that this is a second detection (after clarification)
    detector.detect_count = 1  # Set to 1 so next call returns 0.85
    
    # Act
    intent, confidence = await call_manager.update_intent_after_clarification(
        call_sid=call_sid,
        intent_detector=detector,
        clarification_response="Yes, I want to buy your product"
    )
    
    # Assert
    assert intent == Intent.SALES_INQUIRY
    assert confidence == 0.85  # Higher confidence after clarification
    mock_database.update_call_intent.assert_called_once()


@pytest.mark.asyncio
async def test_update_intent_after_clarification_adds_conversation_turn(call_manager, mock_database, mock_redis):
    """Test that clarification response is added to conversation history.
    
    **Validates: Requirement 3.4** - Conversation tracking
    """
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    clarification_response = "I need help with my account"
    
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent": "unknown",
        "intent_confidence": 0.5,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    detector = MockIntentDetector(intent=Intent.SUPPORT_REQUEST, confidence=0.5)
    
    # Act
    await call_manager.update_intent_after_clarification(
        call_sid=call_sid,
        intent_detector=detector,
        clarification_response=clarification_response
    )
    
    # Assert - Check that conversation turn was added
    # The method calls add_conversation_turn which updates Redis
    assert mock_redis.set_session_state.call_count >= 2  # At least twice


@pytest.mark.asyncio
async def test_update_intent_after_clarification_marks_resolved(call_manager, mock_database, mock_redis):
    """Test that clarification is marked as resolved in metadata.
    
    **Validates: Requirement 3.4** - Clarification resolution tracking
    """
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent": "unknown",
        "intent_confidence": 0.5,
        "conversation_history": [],
        "metadata": {
            "clarification_requested": True
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    detector = MockIntentDetector(intent=Intent.APPOINTMENT_BOOKING, confidence=0.5)
    
    # Act
    await call_manager.update_intent_after_clarification(
        call_sid=call_sid,
        intent_detector=detector,
        clarification_response="I want to schedule an appointment"
    )
    
    # Assert - Check that metadata was updated with resolution
    call_args = mock_redis.set_session_state.call_args
    metadata = call_args[0][1]["metadata"]
    assert metadata["clarification_resolved"] is True
    assert "clarification_response" in metadata


@pytest.mark.asyncio
async def test_clarification_flow_end_to_end(call_manager, mock_database, mock_redis):
    """Test complete clarification flow from detection to resolution.
    
    **Validates: Requirement 3.4** - Complete clarification workflow
    """
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # Initial state
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    detector = MockIntentDetector(intent=Intent.SALES_INQUIRY, confidence=0.6)
    
    # Act - Step 1: Detect intent with low confidence
    intent1, confidence1, clarification = await call_manager.handle_intent_with_clarification(
        call_sid=call_sid,
        intent_detector=detector,
        conversation_history=[],
        current_transcript="I'm interested"
    )
    
    # Assert Step 1
    assert confidence1 == 0.6
    assert clarification is not None
    
    # Update mock to include clarification in history
    mock_redis.get_session_state.return_value["conversation_history"] = [
        {"speaker": "assistant", "text": clarification, "timestamp_ms": 1000}
    ]
    mock_redis.get_session_state.return_value["metadata"] = {
        "clarification_requested": True,
        "clarification_question": clarification
    }
    
    # Act - Step 2: Update intent after clarification
    intent2, confidence2 = await call_manager.update_intent_after_clarification(
        call_sid=call_sid,
        intent_detector=detector,
        clarification_response="Yes, I want to buy your product"
    )
    
    # Assert Step 2
    assert intent2 == Intent.SALES_INQUIRY
    assert confidence2 == 0.85  # Higher confidence after clarification
    assert confidence2 > confidence1


@pytest.mark.asyncio
async def test_clarification_with_different_intent_types(call_manager, mock_database, mock_redis):
    """Test clarification works for all intent types.
    
    **Validates: Requirement 3.4** - Clarification for all intent types
    """
    # Arrange
    call_sid = "CA1234567890"
    call_id = "550e8400-e29b-41d4-a716-446655440000"
    
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Test all intent types
    intent_types = [
        Intent.SALES_INQUIRY,
        Intent.SUPPORT_REQUEST,
        Intent.APPOINTMENT_BOOKING,
        Intent.COMPLAINT,
        Intent.GENERAL_INQUIRY,
        Intent.UNKNOWN
    ]
    
    for intent_type in intent_types:
        detector = MockIntentDetector(intent=intent_type, confidence=0.6)
        
        # Act
        intent, confidence, clarification = await call_manager.handle_intent_with_clarification(
            call_sid=call_sid,
            intent_detector=detector,
            conversation_history=[],
            current_transcript="test"
        )
        
        # Assert
        assert intent == intent_type
        assert clarification is not None
        assert len(clarification) > 0
