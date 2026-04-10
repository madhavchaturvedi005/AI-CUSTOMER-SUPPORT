"""Tests for FallbackHandler."""

import pytest
from unittest.mock import AsyncMock
from fallback_handler import FallbackHandler, ErrorType, FallbackMode


@pytest.mark.asyncio
async def test_initial_state():
    """Test initial state of FallbackHandler."""
    # Setup
    handler = FallbackHandler()
    
    # Verify
    assert handler.current_mode == FallbackMode.NORMAL
    assert handler.is_in_fallback_mode() is False
    assert len(handler.error_log) == 0
    assert handler.max_speech_failures == 3
    
    print("✅ Test passed: Initial state correct")


@pytest.mark.asyncio
async def test_handle_openai_connection_failure():
    """Test handling OpenAI connection failure."""
    # Setup
    alert_sent = []
    
    async def alert_callback(subject, message):
        alert_sent.append({"subject": subject, "message": message})
    
    handler = FallbackHandler(alert_callback=alert_callback)
    
    # Execute
    result = await handler.handle_openai_connection_failure(
        call_id="call-123",
        error_details="Connection timeout"
    )
    
    # Verify
    assert handler.current_mode == FallbackMode.PRE_RECORDED_RESPONSES
    assert handler.is_in_fallback_mode() is True
    assert result["mode"] == "pre_recorded_responses"
    assert "options" in result
    assert len(result["options"]) > 0
    assert len(alert_sent) == 1
    assert "OpenAI" in alert_sent[0]["subject"]
    assert len(handler.error_log) == 1
    
    print("✅ Test passed: OpenAI connection failure handled")


@pytest.mark.asyncio
async def test_pre_recorded_menu():
    """Test pre-recorded menu options."""
    # Setup
    handler = FallbackHandler()
    
    # Execute
    menu = handler.get_pre_recorded_menu()
    
    # Verify
    assert len(menu) >= 3
    assert any(opt["action"] == "transfer_to_sales" for opt in menu)
    assert any(opt["action"] == "transfer_to_support" for opt in menu)
    assert any(opt["action"] == "record_voicemail" for opt in menu)
    
    print("✅ Test passed: Pre-recorded menu has required options")


@pytest.mark.asyncio
async def test_speech_recognition_failure_retry():
    """Test speech recognition failure with retry."""
    # Setup
    handler = FallbackHandler()
    
    # Execute - First failure
    result1 = await handler.handle_speech_recognition_failure("call-456", "+1234567890")
    
    # Verify - Should retry
    assert result1["action"] == "retry"
    assert result1["attempts_remaining"] == 2
    assert "didn't catch that" in result1["message"].lower()
    
    # Execute - Second failure
    result2 = await handler.handle_speech_recognition_failure("call-456", "+1234567890")
    
    # Verify - Should still retry
    assert result2["action"] == "retry"
    assert result2["attempts_remaining"] == 1
    
    print("✅ Test passed: Speech failures trigger retry")


@pytest.mark.asyncio
async def test_speech_recognition_failure_offer_options():
    """Test speech recognition failure offers transfer after 3 attempts."""
    # Setup
    handler = FallbackHandler()
    
    # Execute - 3 failures
    await handler.handle_speech_recognition_failure("call-789", "+1234567890")
    await handler.handle_speech_recognition_failure("call-789", "+1234567890")
    result = await handler.handle_speech_recognition_failure("call-789", "+1234567890")
    
    # Verify - Should offer options
    assert result["action"] == "offer_options"
    assert "options" in result
    assert len(result["options"]) == 2
    assert any(opt["option"] == "agent" for opt in result["options"])
    assert any(opt["option"] == "message" for opt in result["options"])
    
    print("✅ Test passed: After 3 failures, offers transfer or message")


@pytest.mark.asyncio
async def test_reset_speech_failure_count():
    """Test resetting speech failure count."""
    # Setup
    handler = FallbackHandler()
    
    # Add failures
    await handler.handle_speech_recognition_failure("call-111", "+1234567890")
    await handler.handle_speech_recognition_failure("call-111", "+1234567890")
    assert handler.speech_failure_count["call-111"] == 2
    
    # Reset
    handler.reset_speech_failure_count("call-111")
    
    # Verify
    assert "call-111" not in handler.speech_failure_count
    
    print("✅ Test passed: Speech failure count reset")


@pytest.mark.asyncio
async def test_handle_system_failure():
    """Test handling complete system failure."""
    # Setup
    alert_sent = []
    voicemail_recorded = []
    
    async def alert_callback(subject, message):
        alert_sent.append({"subject": subject, "message": message})
    
    async def voicemail_callback(call_id, caller_phone):
        voicemail_recorded.append({"call_id": call_id, "phone": caller_phone})
    
    handler = FallbackHandler(
        alert_callback=alert_callback,
        voicemail_callback=voicemail_callback
    )
    
    # Execute
    result = await handler.handle_system_failure(
        call_id="call-999",
        caller_phone="+1234567890",
        error_details="Database connection lost"
    )
    
    # Verify
    assert handler.current_mode == FallbackMode.VOICEMAIL_ONLY
    assert result["action"] == "voicemail"
    assert result["voicemail_recorded"] is True
    assert len(alert_sent) == 1
    assert "Critical" in alert_sent[0]["subject"]
    assert len(voicemail_recorded) == 1
    assert len(handler.error_log) == 1
    
    print("✅ Test passed: System failure handled with voicemail and alert")


@pytest.mark.asyncio
async def test_error_logging():
    """Test error logging with context."""
    # Setup
    handler = FallbackHandler()
    
    # Execute
    await handler.log_error(
        error_type=ErrorType.NETWORK_FAILURE,
        call_id="call-222",
        error_details="Network timeout",
        recovery_action="retry_connection"
    )
    
    # Verify
    assert len(handler.error_log) == 1
    error = handler.error_log[0]
    assert error["error_type"] == "network_failure"
    assert error["call_id"] == "call-222"
    assert error["error_details"] == "Network timeout"
    assert error["recovery_action"] == "retry_connection"
    assert "timestamp" in error
    
    print("✅ Test passed: Error logged with all context")


@pytest.mark.asyncio
async def test_service_restoration():
    """Test service restoration and resuming normal operation."""
    # Setup
    handler = FallbackHandler()
    
    # Put in fallback mode
    await handler.handle_openai_connection_failure("call-333", "Test error")
    assert handler.current_mode == FallbackMode.PRE_RECORDED_RESPONSES
    
    # Check restoration
    is_restored = await handler.check_service_restoration()
    assert is_restored is True
    
    # Resume normal operation
    result = await handler.resume_normal_operation()
    
    # Verify
    assert handler.current_mode == FallbackMode.NORMAL
    assert handler.is_in_fallback_mode() is False
    assert result["status"] == "restored"
    assert result["previous_mode"] == "pre_recorded_responses"
    assert result["current_mode"] == "normal"
    
    print("✅ Test passed: Service restored and normal operation resumed")


@pytest.mark.asyncio
async def test_error_statistics():
    """Test error statistics collection."""
    # Setup
    handler = FallbackHandler()
    
    # Add various errors
    await handler.log_error(ErrorType.OPENAI_CONNECTION_FAILURE, "call-1", "Error 1", "action1")
    await handler.log_error(ErrorType.OPENAI_CONNECTION_FAILURE, "call-2", "Error 2", "action2")
    await handler.log_error(ErrorType.SPEECH_RECOGNITION_FAILURE, "call-3", "Error 3", "action3")
    await handler.handle_speech_recognition_failure("call-4", "+1234567890")
    
    # Execute
    stats = handler.get_error_statistics()
    
    # Verify
    assert stats["total_errors"] == 4
    assert stats["error_counts"]["openai_connection_failure"] == 2
    assert stats["error_counts"]["speech_recognition_failure"] == 2
    assert stats["current_mode"] == "normal"
    assert stats["active_speech_failures"] == 1
    
    print("✅ Test passed: Error statistics collected correctly")


@pytest.mark.asyncio
async def test_multiple_calls_independent_failure_tracking():
    """Test that failure tracking is independent per call."""
    # Setup
    handler = FallbackHandler()
    
    # Call 1 - 2 failures
    await handler.handle_speech_recognition_failure("call-A", "+1111111111")
    await handler.handle_speech_recognition_failure("call-A", "+1111111111")
    
    # Call 2 - 1 failure
    await handler.handle_speech_recognition_failure("call-B", "+2222222222")
    
    # Verify independent tracking
    assert handler.speech_failure_count["call-A"] == 2
    assert handler.speech_failure_count["call-B"] == 1
    
    # Call 1 - 3rd failure should offer options
    result_a = await handler.handle_speech_recognition_failure("call-A", "+1111111111")
    assert result_a["action"] == "offer_options"
    
    # Call 2 - 2nd failure should still retry
    result_b = await handler.handle_speech_recognition_failure("call-B", "+2222222222")
    assert result_b["action"] == "retry"
    
    print("✅ Test passed: Failure tracking independent per call")


@pytest.mark.asyncio
async def test_get_error_log():
    """Test retrieving error log."""
    # Setup
    handler = FallbackHandler()
    
    # Add errors
    await handler.log_error(ErrorType.DATABASE_FAILURE, "call-X", "DB error", "reconnect")
    await handler.log_error(ErrorType.NETWORK_FAILURE, "call-Y", "Network error", "retry")
    
    # Execute
    log = handler.get_error_log()
    
    # Verify
    assert len(log) == 2
    assert log[0]["error_type"] == "database_failure"
    assert log[1]["error_type"] == "network_failure"
    
    # Verify it's a copy (not reference)
    log.append({"test": "value"})
    assert len(handler.error_log) == 2
    
    print("✅ Test passed: Error log retrieved correctly")


if __name__ == "__main__":
    import asyncio
    
    print("\n🧪 Running Fallback Handler Tests...\n")
    
    asyncio.run(test_initial_state())
    asyncio.run(test_handle_openai_connection_failure())
    asyncio.run(test_pre_recorded_menu())
    asyncio.run(test_speech_recognition_failure_retry())
    asyncio.run(test_speech_recognition_failure_offer_options())
    asyncio.run(test_reset_speech_failure_count())
    asyncio.run(test_handle_system_failure())
    asyncio.run(test_error_logging())
    asyncio.run(test_service_restoration())
    asyncio.run(test_error_statistics())
    asyncio.run(test_multiple_calls_independent_failure_tracking())
    asyncio.run(test_get_error_log())
    
    print("\n✅ All Fallback Handler tests passed!")
    print("\nRequirements validated:")
    print("  • 14.1: Switch to pre-recorded responses on OpenAI failure ✓")
    print("  • 14.2: Offer transfer or message after 3 speech failures ✓")
    print("  • 14.3: Record voicemail and alert on system failure ✓")
    print("  • 14.4: Log all errors with context ✓")
    print("  • 14.5: Resume normal operation automatically ✓")
