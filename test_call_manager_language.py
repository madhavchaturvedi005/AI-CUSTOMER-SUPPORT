"""Integration tests for CallManager language detection and switching."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from call_manager import CallManager
from language_manager import LanguageManager
from models import CallContext, Language
from database import DatabaseService
from redis_service import RedisService


@pytest.fixture
def mock_database():
    """Create mock database service."""
    db = AsyncMock(spec=DatabaseService)
    db.create_call = AsyncMock(return_value="call-uuid-123")
    db.update_call_status = AsyncMock(return_value=True)
    db.update_call_intent = AsyncMock(return_value=True)
    db.update_call_language = AsyncMock(return_value=True)
    db.get_business_config = AsyncMock(return_value=None)
    return db


@pytest.fixture
def mock_redis():
    """Create mock Redis service."""
    redis = AsyncMock(spec=RedisService)
    redis.set_session_state = AsyncMock()
    redis.get_session_state = AsyncMock(return_value=None)
    redis.add_caller_history = AsyncMock()
    return redis


@pytest.fixture
def language_manager():
    """Create LanguageManager instance."""
    return LanguageManager(base_instructions="You are a helpful assistant.")


@pytest.fixture
def call_manager(mock_database, mock_redis, language_manager):
    """Create CallManager instance with mocked dependencies."""
    return CallManager(
        database=mock_database,
        redis=mock_redis,
        language_manager=language_manager
    )


@pytest.fixture
def mock_openai_ws():
    """Create mock OpenAI WebSocket."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    return ws


@pytest.mark.asyncio
async def test_detect_and_update_language_hindi(call_manager, mock_database, mock_redis, mock_openai_ws):
    """Test automatic language detection and update for Hindi."""
    # Create call
    call_sid = "CA123"
    context = await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone="+1234567890"
    )
    
    # Mock Redis to return context with conversation (before adding turn)
    mock_redis.get_session_state.return_value = {
        "call_id": context.call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Add Hindi conversation
    await call_manager.add_conversation_turn(
        call_sid=call_sid,
        speaker="caller",
        text="नमस्ते, मुझे मदद चाहिए"
    )
    
    # Update mock to return context with conversation
    mock_redis.get_session_state.return_value = {
        "call_id": context.call_id,
        "caller_phone": "+1234567890",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [
            {"speaker": "caller", "text": "नमस्ते, मुझे मदद चाहिए"}
        ],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Detect and update language
    detected_language, confidence = await call_manager.detect_and_update_language(
        call_sid=call_sid,
        openai_ws=mock_openai_ws,
        elapsed_time_ms=5000
    )
    
    # Verify detection
    assert detected_language == Language.HINDI
    assert confidence >= 0.8
    
    # Verify session update was sent
    mock_openai_ws.send.assert_called()
    
    # Verify database update was called
    mock_database.update_call_language.assert_called_once_with(
        call_id=context.call_id,
        language="hi"
    )


@pytest.mark.asyncio
async def test_detect_and_update_language_tamil(call_manager, mock_database, mock_redis, mock_openai_ws):
    """Test automatic language detection for Tamil."""
    call_sid = "CA456"
    context = await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone="+9876543210"
    )
    
    # Mock Redis to return context (before adding turn)
    mock_redis.get_session_state.return_value = {
        "call_id": context.call_id,
        "caller_phone": "+9876543210",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Add Tamil conversation
    await call_manager.add_conversation_turn(
        call_sid=call_sid,
        speaker="caller",
        text="வணக்கம், எனக்கு உதவி தேவை"
    )
    
    # Update mock to return context with conversation
    mock_redis.get_session_state.return_value = {
        "call_id": context.call_id,
        "caller_phone": "+9876543210",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [
            {"speaker": "caller", "text": "வணக்கம், எனக்கு உதவி தேவை"}
        ],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    detected_language, confidence = await call_manager.detect_and_update_language(
        call_sid=call_sid,
        openai_ws=mock_openai_ws,
        elapsed_time_ms=6000
    )
    
    assert detected_language == Language.TAMIL
    assert confidence >= 0.8


@pytest.mark.asyncio
async def test_detect_and_update_language_no_utterances(call_manager, mock_redis, mock_openai_ws):
    """Test language detection with no caller utterances."""
    call_sid = "CA789"
    await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone="+1111111111"
    )
    
    mock_redis.get_session_state.return_value = {
        "call_id": "call-uuid",
        "caller_phone": "+1111111111",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [],  # No conversation yet
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    detected_language, confidence = await call_manager.detect_and_update_language(
        call_sid=call_sid,
        openai_ws=mock_openai_ws,
        elapsed_time_ms=3000
    )
    
    # Should return None when no utterances
    assert detected_language is None
    assert confidence == 0.0


@pytest.mark.asyncio
async def test_detect_and_update_language_outside_window(call_manager, mock_redis, mock_openai_ws):
    """Test language detection outside 10-second window."""
    call_sid = "CA999"
    await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone="+2222222222"
    )
    
    mock_redis.get_session_state.return_value = {
        "call_id": "call-uuid",
        "caller_phone": "+2222222222",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [
            {"speaker": "caller", "text": "Hello"}
        ],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Try to detect after 15 seconds (outside window)
    detected_language, confidence = await call_manager.detect_and_update_language(
        call_sid=call_sid,
        openai_ws=mock_openai_ws,
        elapsed_time_ms=15000
    )
    
    # Should return None outside detection window
    assert detected_language is None
    assert confidence == 0.0


@pytest.mark.asyncio
async def test_handle_language_switch(call_manager, mock_database, mock_redis, mock_openai_ws):
    """Test mid-conversation language switch."""
    call_sid = "CA_SWITCH"
    context = await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone="+3333333333",
        language=Language.ENGLISH
    )
    
    # Mock Redis to return context (before adding turn)
    mock_redis.get_session_state.return_value = {
        "call_id": context.call_id,
        "caller_phone": "+3333333333",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Add conversation history
    await call_manager.add_conversation_turn(
        call_sid=call_sid,
        speaker="caller",
        text="Hello, I need help"
    )
    
    # Update mock to return context with conversation
    mock_redis.get_session_state.return_value = {
        "call_id": context.call_id,
        "caller_phone": "+3333333333",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [
            {"speaker": "caller", "text": "Hello, I need help"}
        ],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Switch to Hindi
    success = await call_manager.handle_language_switch(
        call_sid=call_sid,
        openai_ws=mock_openai_ws,
        requested_language=Language.HINDI
    )
    
    assert success is True
    
    # Verify session update was sent
    mock_openai_ws.send.assert_called()
    
    # Verify database update
    mock_database.update_call_language.assert_called_with(
        call_id=context.call_id,
        language="hi"
    )


@pytest.mark.asyncio
async def test_get_language_selection_prompt(call_manager):
    """Test getting multi-language selection prompt."""
    prompt = await call_manager.get_language_selection_prompt()
    
    # Should contain text in multiple languages
    assert "English" in prompt
    assert "Hindi" in prompt or "हिंदी" in prompt
    assert "Tamil" in prompt or "தமிழ்" in prompt


@pytest.mark.asyncio
async def test_parse_language_selection_english(call_manager, mock_redis, mock_openai_ws):
    """Test parsing English language selection."""
    call_sid = "CA_SELECT_EN"
    await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone="+4444444444"
    )
    
    mock_redis.get_session_state.return_value = {
        "call_id": "call-uuid",
        "caller_phone": "+4444444444",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    success, selected_language = await call_manager.parse_language_selection(
        call_sid=call_sid,
        openai_ws=mock_openai_ws,
        caller_response="I want English"
    )
    
    assert success is True
    assert selected_language == Language.ENGLISH


@pytest.mark.asyncio
async def test_parse_language_selection_hindi(call_manager, mock_redis, mock_openai_ws):
    """Test parsing Hindi language selection."""
    call_sid = "CA_SELECT_HI"
    await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone="+5555555555"
    )
    
    mock_redis.get_session_state.return_value = {
        "call_id": "call-uuid",
        "caller_phone": "+5555555555",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    success, selected_language = await call_manager.parse_language_selection(
        call_sid=call_sid,
        openai_ws=mock_openai_ws,
        caller_response="Hindi please"
    )
    
    assert success is True
    assert selected_language == Language.HINDI


@pytest.mark.asyncio
async def test_parse_language_selection_unrecognized(call_manager, mock_redis, mock_openai_ws):
    """Test parsing unrecognized language returns failure."""
    call_sid = "CA_SELECT_UNKNOWN"
    await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone="+6666666666"
    )
    
    mock_redis.get_session_state.return_value = {
        "call_id": "call-uuid",
        "caller_phone": "+6666666666",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    success, selected_language = await call_manager.parse_language_selection(
        call_sid=call_sid,
        openai_ws=mock_openai_ws,
        caller_response="French please"  # Not supported
    )
    
    assert success is False
    assert selected_language is None


@pytest.mark.asyncio
async def test_language_switch_preserves_conversation_context(call_manager, mock_redis, mock_openai_ws):
    """Test that language switch preserves conversation history."""
    call_sid = "CA_PRESERVE"
    context = await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone="+7777777777"
    )
    
    # Add multiple conversation turns
    conversation_history = [
        {"speaker": "assistant", "text": "Hello, how can I help?"},
        {"speaker": "caller", "text": "I need help with my order"},
        {"speaker": "assistant", "text": "Sure, what's your order number?"}
    ]
    
    # Mock Redis to return context for each turn
    for i, turn in enumerate(conversation_history):
        mock_redis.get_session_state.return_value = {
            "call_id": context.call_id,
            "caller_phone": "+7777777777",
            "language": "en",
            "intent": None,
            "intent_confidence": 0.0,
            "conversation_history": conversation_history[:i],
            "metadata": {},
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await call_manager.add_conversation_turn(
            call_sid=call_sid,
            speaker=turn["speaker"],
            text=turn["text"]
        )
    
    # Final mock with all conversation
    mock_redis.get_session_state.return_value = {
        "call_id": context.call_id,
        "caller_phone": "+7777777777",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": conversation_history,
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Switch language
    await call_manager.handle_language_switch(
        call_sid=call_sid,
        openai_ws=mock_openai_ws,
        requested_language=Language.TELUGU
    )
    
    # Get updated context
    updated_context = await call_manager.get_call_context(call_sid)
    
    # Verify conversation history is preserved
    assert len(updated_context.conversation_history) == len(conversation_history)
    assert updated_context.metadata.get("language_switched") is True


@pytest.mark.asyncio
async def test_language_detection_metadata_tracking(call_manager, mock_redis, mock_openai_ws):
    """Test that language detection updates metadata correctly."""
    call_sid = "CA_METADATA"
    context = await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone="+8888888888"
    )
    
    # Mock Redis to return context (before adding turn)
    mock_redis.get_session_state.return_value = {
        "call_id": context.call_id,
        "caller_phone": "+8888888888",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Add Bengali conversation
    await call_manager.add_conversation_turn(
        call_sid=call_sid,
        speaker="caller",
        text="নমস্কার, আমার সাহায্য দরকার"
    )
    
    # Update mock to return context with conversation
    mock_redis.get_session_state.return_value = {
        "call_id": context.call_id,
        "caller_phone": "+8888888888",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [
            {"speaker": "caller", "text": "নমস্কার, আমার সাহায্য দরকার"}
        ],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Detect language
    await call_manager.detect_and_update_language(
        call_sid=call_sid,
        openai_ws=mock_openai_ws,
        elapsed_time_ms=4000
    )
    
    # Get updated context
    updated_context = await call_manager.get_call_context(call_sid)
    
    # Verify metadata
    assert updated_context.metadata.get("language_detected") is True
    assert "language_detection_confidence" in updated_context.metadata
    assert "language_detection_time" in updated_context.metadata
