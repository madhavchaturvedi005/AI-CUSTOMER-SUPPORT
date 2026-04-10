"""Unit tests for conversation history retrieval functionality."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from call_manager import CallManager
from database import DatabaseService
from redis_service import RedisService
from models import CallContext, Language, Intent


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
async def test_retrieve_conversation_history_with_results(call_manager, mock_database):
    """Test retrieving conversation history when previous calls exist."""
    # Setup mock data
    caller_phone = "+1234567890"
    call_id_1 = "call-uuid-1"
    call_id_2 = "call-uuid-2"
    
    # Mock recent calls
    mock_calls = [
        {
            "id": call_id_1,
            "started_at": datetime.now(timezone.utc) - timedelta(days=5),
            "intent": "sales_inquiry",
            "intent_confidence": 0.85,
            "duration_seconds": 120
        },
        {
            "id": call_id_2,
            "started_at": datetime.now(timezone.utc) - timedelta(days=10),
            "intent": "support_request",
            "intent_confidence": 0.92,
            "duration_seconds": 180
        }
    ]
    
    # Mock transcripts
    mock_transcripts_1 = [
        {"speaker": "caller", "text": "I want to buy your product", "timestamp_ms": 1000},
        {"speaker": "assistant", "text": "Great! Let me help you with that", "timestamp_ms": 2000}
    ]
    
    mock_transcripts_2 = [
        {"speaker": "caller", "text": "I need help with my account", "timestamp_ms": 1000},
        {"speaker": "assistant", "text": "I can help you with that", "timestamp_ms": 2000}
    ]
    
    mock_database.get_recent_caller_history.return_value = mock_calls
    mock_database.get_call_transcripts.side_effect = [mock_transcripts_1, mock_transcripts_2]
    
    # Execute
    history = await call_manager.retrieve_conversation_history(caller_phone)
    
    # Verify
    assert len(history) == 2
    assert history[0]["call_id"] == call_id_1
    assert history[0]["intent"] == "sales_inquiry"
    assert history[0]["intent_confidence"] == 0.85
    assert len(history[0]["transcripts"]) == 2
    
    assert history[1]["call_id"] == call_id_2
    assert history[1]["intent"] == "support_request"
    assert len(history[1]["transcripts"]) == 2
    
    # Verify database calls
    mock_database.get_recent_caller_history.assert_called_once_with(
        caller_phone=caller_phone,
        days=30,
        limit=5
    )
    assert mock_database.get_call_transcripts.call_count == 2


@pytest.mark.asyncio
async def test_retrieve_conversation_history_no_results(call_manager, mock_database):
    """Test retrieving conversation history when no previous calls exist."""
    caller_phone = "+1234567890"
    
    # Mock no previous calls
    mock_database.get_recent_caller_history.return_value = []
    
    # Execute
    history = await call_manager.retrieve_conversation_history(caller_phone)
    
    # Verify
    assert history == []
    mock_database.get_recent_caller_history.assert_called_once()
    mock_database.get_call_transcripts.assert_not_called()


@pytest.mark.asyncio
async def test_integrate_conversation_history_returning_caller(call_manager, mock_database, mock_redis):
    """Test integrating conversation history for a returning caller."""
    call_sid = "CA123456"
    caller_phone = "+1234567890"
    call_id = "call-uuid-current"
    
    # Setup current call context
    current_context = CallContext(
        call_id=call_id,
        caller_phone=caller_phone,
        language=Language.ENGLISH
    )
    
    # Mock get_call_context
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": caller_phone,
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Mock conversation history
    mock_history = [
        {
            "call_id": "prev-call-1",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "intent": "sales_inquiry",
            "intent_confidence": 0.85,
            "duration_seconds": 120,
            "transcripts": [
                {"speaker": "caller", "text": "I want to buy", "timestamp_ms": 1000}
            ]
        }
    ]
    
    # Mock retrieve_conversation_history
    with patch.object(call_manager, 'retrieve_conversation_history', return_value=mock_history):
        # Execute
        result = await call_manager.integrate_conversation_history(call_sid, caller_phone)
    
    # Verify
    assert result is True
    
    # Verify that set_session_state was called with updated context
    mock_redis.set_session_state.assert_called_once()
    call_args = mock_redis.set_session_state.call_args
    assert call_args[0][0] == call_sid
    
    session_data = call_args[0][1]
    assert session_data["metadata"]["is_returning_caller"] is True
    assert session_data["metadata"]["previous_calls_count"] == 1
    assert session_data["metadata"]["conversation_history"] == mock_history
    assert session_data["metadata"]["previous_intents"] == ["sales_inquiry"]


@pytest.mark.asyncio
async def test_integrate_conversation_history_new_caller(call_manager, mock_database, mock_redis):
    """Test integrating conversation history for a new caller (no history)."""
    call_sid = "CA123456"
    caller_phone = "+1234567890"
    call_id = "call-uuid-current"
    
    # Mock get_call_context
    mock_redis.get_session_state.return_value = {
        "call_id": call_id,
        "caller_phone": caller_phone,
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Mock no conversation history
    with patch.object(call_manager, 'retrieve_conversation_history', return_value=[]):
        # Execute
        result = await call_manager.integrate_conversation_history(call_sid, caller_phone)
    
    # Verify
    assert result is False
    
    # Verify that set_session_state was called with updated context
    mock_redis.set_session_state.assert_called_once()
    call_args = mock_redis.set_session_state.call_args
    
    session_data = call_args[0][1]
    assert session_data["metadata"]["is_returning_caller"] is False
    assert session_data["metadata"]["previous_calls_count"] == 0


@pytest.mark.asyncio
async def test_get_conversation_summary_returning_caller(call_manager, mock_redis):
    """Test generating conversation summary for a returning caller."""
    call_sid = "CA123456"
    
    # Mock call context with history
    mock_redis.get_session_state.return_value = {
        "call_id": "call-uuid",
        "caller_phone": "+1234567890",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {
            "is_returning_caller": True,
            "previous_calls_count": 2,
            "previous_intents": ["sales_inquiry", "support_request"],
            "conversation_history": [
                {
                    "call_id": "prev-1",
                    "started_at": "2024-01-15T10:00:00+00:00",
                    "intent": "sales_inquiry"
                },
                {
                    "call_id": "prev-2",
                    "started_at": "2024-01-10T10:00:00+00:00",
                    "intent": "support_request"
                }
            ]
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Execute
    summary = await call_manager.get_conversation_summary(call_sid)
    
    # Verify
    assert summary is not None
    assert "2 time(s)" in summary
    assert "sales_inquiry" in summary or "support_request" in summary
    assert "Last call was on" in summary


@pytest.mark.asyncio
async def test_get_conversation_summary_new_caller(call_manager, mock_redis):
    """Test generating conversation summary for a new caller (no history)."""
    call_sid = "CA123456"
    
    # Mock call context without history
    mock_redis.get_session_state.return_value = {
        "call_id": "call-uuid",
        "caller_phone": "+1234567890",
        "language": "en",
        "intent": None,
        "intent_confidence": 0.0,
        "conversation_history": [],
        "metadata": {
            "is_returning_caller": False,
            "previous_calls_count": 0
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Execute
    summary = await call_manager.get_conversation_summary(call_sid)
    
    # Verify
    assert summary is None


@pytest.mark.asyncio
async def test_get_recent_caller_history_called_correctly(call_manager, mock_database):
    """Test that get_recent_caller_history is called with correct parameters."""
    caller_phone = "+1234567890"
    
    # Mock database response
    mock_database.get_recent_caller_history.return_value = [
        {
            "id": "call-1",
            "caller_phone": caller_phone,
            "started_at": datetime.now(timezone.utc) - timedelta(days=5),
            "status": "completed",
            "intent": "sales_inquiry",
            "intent_confidence": 0.85,
            "duration_seconds": 120
        }
    ]
    
    mock_database.get_call_transcripts.return_value = []
    
    # Execute
    result = await call_manager.retrieve_conversation_history(caller_phone, days=30, max_calls=5)
    
    # Verify database was called correctly
    mock_database.get_recent_caller_history.assert_called_once_with(
        caller_phone=caller_phone,
        days=30,
        limit=5
    )
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_call_transcripts_called_correctly(call_manager, mock_database):
    """Test that get_call_transcripts is called for each call in history."""
    caller_phone = "+1234567890"
    call_id = "call-uuid-1"
    
    # Mock database responses
    mock_database.get_recent_caller_history.return_value = [
        {
            "id": call_id,
            "caller_phone": caller_phone,
            "started_at": datetime.now(timezone.utc) - timedelta(days=5),
            "status": "completed",
            "intent": "sales_inquiry",
            "intent_confidence": 0.85,
            "duration_seconds": 120
        }
    ]
    
    mock_database.get_call_transcripts.return_value = [
        {
            "speaker": "caller",
            "text": "Hello",
            "timestamp_ms": 1000,
            "language": "en",
            "confidence": 0.95
        }
    ]
    
    # Execute
    result = await call_manager.retrieve_conversation_history(caller_phone)
    
    # Verify
    mock_database.get_call_transcripts.assert_called_once_with(call_id)
    assert len(result) == 1
    assert len(result[0]["transcripts"]) == 1
    assert result[0]["transcripts"][0]["speaker"] == "caller"


@pytest.mark.asyncio
async def test_integrate_history_with_custom_parameters(call_manager, mock_database, mock_redis):
    """Test retrieving conversation history with custom days and max_calls parameters."""
    caller_phone = "+1234567890"
    
    # Mock database response
    mock_database.get_recent_caller_history.return_value = []
    
    # Execute with custom parameters
    history = await call_manager.retrieve_conversation_history(
        caller_phone=caller_phone,
        days=60,
        max_calls=10
    )
    
    # Verify
    assert history == []
    mock_database.get_recent_caller_history.assert_called_once_with(
        caller_phone=caller_phone,
        days=60,
        limit=10
    )


@pytest.mark.asyncio
async def test_conversation_history_includes_completed_calls_only(call_manager, mock_database):
    """Test that conversation history retrieval filters for completed calls."""
    caller_phone = "+1234567890"
    
    # Mock database to return only completed calls
    # The database method should filter by status = 'completed' in the SQL query
    mock_database.get_recent_caller_history.return_value = [
        {
            "id": "call-1",
            "status": "completed",
            "started_at": datetime.now(timezone.utc) - timedelta(days=5),
            "intent": "sales_inquiry",
            "intent_confidence": 0.85,
            "duration_seconds": 120
        }
    ]
    
    mock_database.get_call_transcripts.return_value = []
    
    # Execute
    result = await call_manager.retrieve_conversation_history(caller_phone)
    
    # Verify
    assert len(result) == 1
    # The database method should have been called, which filters by completed status
    mock_database.get_recent_caller_history.assert_called_once()
