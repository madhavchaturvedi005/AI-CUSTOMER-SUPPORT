"""
Unit tests for greeting message functionality.

Tests cover:
- Retrieving business-specific greeting from configuration
- Default greeting fallback
- Greeting message playback integration

Requirements: 1.2, 17.1
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from call_manager import CallManager
from models import Language
from utils import send_greeting_message


@pytest.fixture
def mock_database():
    """Mock DatabaseService for testing."""
    db = AsyncMock()
    db.get_business_config = AsyncMock()
    return db


@pytest.fixture
def mock_redis():
    """Mock RedisService for testing."""
    redis = AsyncMock()
    return redis


@pytest.fixture
def call_manager(mock_database, mock_redis):
    """Create CallManager instance with mocked dependencies."""
    return CallManager(database=mock_database, redis=mock_redis)


@pytest.mark.asyncio
async def test_get_greeting_message_with_custom_greeting(call_manager, mock_database):
    """Test retrieving custom greeting from business configuration."""
    # Arrange
    business_id = "test_business"
    custom_greeting = "Welcome to Test Business! How can we help you today?"
    mock_database.get_business_config.return_value = {
        "business_id": business_id,
        "greeting_message": custom_greeting,
        "active": True
    }
    
    # Act
    greeting = await call_manager.get_greeting_message(business_id)
    
    # Assert
    assert greeting == custom_greeting
    mock_database.get_business_config.assert_called_once_with(business_id)


@pytest.mark.asyncio
async def test_get_greeting_message_with_default_greeting(call_manager, mock_database):
    """Test default greeting when no custom greeting is configured."""
    # Arrange
    business_id = "test_business"
    mock_database.get_business_config.return_value = {
        "business_id": business_id,
        "greeting_message": None,
        "active": True
    }
    
    # Act
    greeting = await call_manager.get_greeting_message(business_id)
    
    # Assert
    assert "Hello!" in greeting
    assert "AI assistant" in greeting
    mock_database.get_business_config.assert_called_once_with(business_id)


@pytest.mark.asyncio
async def test_get_greeting_message_when_config_not_found(call_manager, mock_database):
    """Test default greeting when business configuration is not found."""
    # Arrange
    business_id = "nonexistent_business"
    mock_database.get_business_config.return_value = None
    
    # Act
    greeting = await call_manager.get_greeting_message(business_id)
    
    # Assert
    assert "Hello!" in greeting
    assert "AI assistant" in greeting
    mock_database.get_business_config.assert_called_once_with(business_id)


@pytest.mark.asyncio
async def test_get_greeting_message_with_empty_greeting(call_manager, mock_database):
    """Test default greeting when greeting_message is empty string."""
    # Arrange
    business_id = "test_business"
    mock_database.get_business_config.return_value = {
        "business_id": business_id,
        "greeting_message": "",
        "active": True
    }
    
    # Act
    greeting = await call_manager.get_greeting_message(business_id)
    
    # Assert
    assert "Hello!" in greeting
    assert "AI assistant" in greeting


@pytest.mark.asyncio
async def test_send_greeting_message():
    """Test sending greeting message to OpenAI WebSocket."""
    # Arrange
    mock_ws = AsyncMock()
    greeting_text = "Welcome to our business!"
    
    # Act
    await send_greeting_message(mock_ws, greeting_text)
    
    # Assert
    assert mock_ws.send.call_count == 2  # One for item.create, one for response.create
    
    # Verify first call (conversation.item.create)
    first_call_args = mock_ws.send.call_args_list[0][0][0]
    assert "conversation.item.create" in first_call_args
    assert greeting_text in first_call_args
    
    # Verify second call (response.create)
    second_call_args = mock_ws.send.call_args_list[1][0][0]
    assert "response.create" in second_call_args


@pytest.mark.asyncio
async def test_greeting_message_within_3_seconds():
    """
    Test that greeting can be retrieved and sent within 3 seconds.
    
    This test verifies the performance requirement that greeting
    should be played within 3 seconds of call answer.
    
    Requirements: 1.2
    """
    import time
    
    # Arrange
    mock_database = AsyncMock()
    mock_redis = AsyncMock()
    mock_database.get_business_config.return_value = {
        "greeting_message": "Welcome!"
    }
    call_manager = CallManager(database=mock_database, redis=mock_redis)
    mock_ws = AsyncMock()
    
    # Act
    start_time = time.time()
    greeting = await call_manager.get_greeting_message("default")
    await send_greeting_message(mock_ws, greeting)
    elapsed_time = time.time() - start_time
    
    # Assert
    assert elapsed_time < 3.0, f"Greeting took {elapsed_time}s, should be < 3s"
    assert mock_ws.send.call_count == 2


@pytest.mark.asyncio
async def test_greeting_with_special_characters(call_manager, mock_database):
    """Test greeting message with special characters and punctuation."""
    # Arrange
    business_id = "test_business"
    greeting_with_special_chars = "Hello! Welcome to O'Brien's Store. How can we help you today?"
    mock_database.get_business_config.return_value = {
        "greeting_message": greeting_with_special_chars
    }
    
    # Act
    greeting = await call_manager.get_greeting_message(business_id)
    
    # Assert
    assert greeting == greeting_with_special_chars


@pytest.mark.asyncio
async def test_greeting_with_multilingual_content(call_manager, mock_database):
    """Test greeting message with multilingual content."""
    # Arrange
    business_id = "test_business"
    multilingual_greeting = "Hello! नमस्ते! Welcome to our business!"
    mock_database.get_business_config.return_value = {
        "greeting_message": multilingual_greeting
    }
    
    # Act
    greeting = await call_manager.get_greeting_message(business_id)
    
    # Assert
    assert greeting == multilingual_greeting


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
