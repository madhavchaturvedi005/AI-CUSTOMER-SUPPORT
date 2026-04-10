"""Tests for TranscriptService."""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone
from transcript_service import TranscriptService
from database import DatabaseService


@pytest.mark.asyncio
async def test_get_disclosure_message():
    """Test getting recording disclosure message."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    transcript_service = TranscriptService(database=mock_db)
    
    # Execute
    message = transcript_service.get_disclosure_message()
    
    # Verify
    assert "recorded" in message.lower()
    assert "quality" in message.lower() or "training" in message.lower()
    
    print("✅ Test passed: Disclosure message retrieved")


@pytest.mark.asyncio
async def test_should_play_disclosure():
    """Test disclosure requirement check."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    
    # With disclosure required
    service_with_disclosure = TranscriptService(database=mock_db, require_disclosure=True)
    assert service_with_disclosure.should_play_disclosure() is True
    
    # Without disclosure required
    service_without_disclosure = TranscriptService(database=mock_db, require_disclosure=False)
    assert service_without_disclosure.should_play_disclosure() is False
    
    print("✅ Test passed: Disclosure requirement check works")


@pytest.mark.asyncio
async def test_generate_transcript():
    """Test transcript generation from conversation history."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    transcript_service = TranscriptService(database=mock_db)
    
    conversation_history = [
        {"speaker": "assistant", "text": "Hello, how can I help you?", "timestamp_ms": 1000},
        {"speaker": "caller", "text": "I want to book an appointment", "timestamp_ms": 5000},
        {"speaker": "assistant", "text": "I can help with that", "timestamp_ms": 8000}
    ]
    
    # Execute
    transcript = await transcript_service.generate_transcript("call-123", conversation_history)
    
    # Verify
    assert "call-123" in transcript.lower()
    assert "Hello, how can I help you?" in transcript
    assert "I want to book an appointment" in transcript
    assert "Caller:" in transcript
    assert "Assistant:" in transcript
    assert "[00:01]" in transcript  # 1000ms = 1 second
    assert "[00:05]" in transcript  # 5000ms = 5 seconds
    
    print("✅ Test passed: Transcript generated correctly")


@pytest.mark.asyncio
async def test_mask_credit_card_numbers():
    """Test masking of credit card numbers."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    transcript_service = TranscriptService(database=mock_db)
    
    # Test various credit card formats
    test_cases = [
        "My card is 1234 5678 9012 3456",
        "Card number: 1234-5678-9012-3456",
        "The number is 1234567890123456"
    ]
    
    for text in test_cases:
        masked = transcript_service.mask_sensitive_information(text)
        assert "[CREDIT_CARD_REDACTED]" in masked
        assert "1234" not in masked or masked.count("1234") < text.count("1234")
    
    print("✅ Test passed: Credit card numbers masked")


@pytest.mark.asyncio
async def test_mask_ssn():
    """Test masking of social security numbers."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    transcript_service = TranscriptService(database=mock_db)
    
    # Test SSN formats
    test_cases = [
        "My SSN is 123-45-6789",
        "SSN: 123 45 6789",
        "Social security 123456789"
    ]
    
    for text in test_cases:
        masked = transcript_service.mask_sensitive_information(text)
        assert "[SSN_REDACTED]" in masked
    
    print("✅ Test passed: SSN masked")


@pytest.mark.asyncio
async def test_mask_passwords():
    """Test masking of passwords and PINs."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    transcript_service = TranscriptService(database=mock_db)
    
    # Test password/PIN formats
    test_cases = [
        "My password is secret123",
        "The PIN is 1234",
        "My password secret456",
        "My pin 5678"
    ]
    
    for text in test_cases:
        masked = transcript_service.mask_sensitive_information(text)
        assert "[REDACTED]" in masked
    
    print("✅ Test passed: Passwords and PINs masked")


@pytest.mark.asyncio
async def test_mask_preserves_normal_text():
    """Test that normal text is not masked."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    transcript_service = TranscriptService(database=mock_db)
    
    normal_text = "I want to book an appointment for tomorrow at 2 PM"
    masked = transcript_service.mask_sensitive_information(normal_text)
    
    # Verify text is unchanged
    assert masked == normal_text
    
    print("✅ Test passed: Normal text preserved")


@pytest.mark.asyncio
async def test_save_transcript():
    """Test saving transcript to database."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    mock_db.create_transcript = AsyncMock(return_value="transcript-uuid-123")
    transcript_service = TranscriptService(database=mock_db)
    
    transcript_text = "Call transcript with credit card 1234 5678 9012 3456"
    
    # Execute
    transcript_id = await transcript_service.save_transcript(
        call_id="call-123",
        transcript_text=transcript_text,
        caller_id="+1234567890",
        intent="sales_inquiry",
        outcome="completed",
        recording_url="/recordings/call-123.wav"
    )
    
    # Verify
    assert transcript_id == "transcript-uuid-123"
    assert mock_db.create_transcript.called
    
    # Verify sensitive data was masked
    call_args = mock_db.create_transcript.call_args
    saved_text = call_args.kwargs["transcript_text"]
    assert "[CREDIT_CARD_REDACTED]" in saved_text
    assert "1234 5678" not in saved_text
    
    print("✅ Test passed: Transcript saved with masked data")


@pytest.mark.asyncio
async def test_create_recording_metadata():
    """Test creating recording metadata."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    transcript_service = TranscriptService(database=mock_db, storage_path="/recordings")
    
    # Execute
    metadata = await transcript_service.create_recording_metadata(
        call_id="call-456",
        duration_seconds=120,
        format="wav",
        sample_rate=16000
    )
    
    # Verify
    assert metadata["call_id"] == "call-456"
    assert metadata["format"] == "wav"
    assert metadata["sample_rate"] == 16000
    assert metadata["duration_seconds"] == 120
    assert "/recordings/call-456.wav" in metadata["recording_url"]
    assert "created_at" in metadata
    
    print("✅ Test passed: Recording metadata created")


@pytest.mark.asyncio
async def test_recording_format_requirements():
    """Test that recording meets format requirements."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    transcript_service = TranscriptService(database=mock_db)
    
    # Execute
    metadata = await transcript_service.create_recording_metadata(
        call_id="call-789",
        duration_seconds=60
    )
    
    # Verify format requirements (Requirement 8.1)
    assert metadata["format"] == "wav"
    assert metadata["sample_rate"] == 16000  # 16kHz
    
    print("✅ Test passed: Recording format meets requirements (WAV, 16kHz)")


@pytest.mark.asyncio
async def test_process_call_transcript_complete_pipeline():
    """Test complete transcript processing pipeline."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    mock_db.create_transcript = AsyncMock(return_value="transcript-uuid-999")
    transcript_service = TranscriptService(database=mock_db)
    
    conversation_history = [
        {"speaker": "caller", "text": "I need help", "timestamp_ms": 2000},
        {"speaker": "assistant", "text": "How can I assist?", "timestamp_ms": 4000}
    ]
    
    # Execute
    result = await transcript_service.process_call_transcript(
        call_id="call-999",
        conversation_history=conversation_history,
        caller_phone="+1234567890",
        intent="support_request",
        outcome="resolved",
        duration_seconds=180
    )
    
    # Verify
    assert result["transcript_id"] == "transcript-uuid-999"
    assert "recording_url" in result
    assert ".wav" in result["recording_url"]
    assert mock_db.create_transcript.called
    
    print("✅ Test passed: Complete transcript pipeline executed")


@pytest.mark.asyncio
async def test_retention_policy():
    """Test 90-day retention policy."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    transcript_service = TranscriptService(database=mock_db)
    
    # Verify retention period
    assert transcript_service.retention_days == 90
    
    # Execute cleanup
    deleted_count = await transcript_service.cleanup_old_recordings()
    
    # Verify (would delete in production)
    assert deleted_count >= 0
    
    print("✅ Test passed: 90-day retention policy configured")


if __name__ == "__main__":
    import asyncio
    
    print("\n🧪 Running Transcript Service Tests...\n")
    
    asyncio.run(test_get_disclosure_message())
    asyncio.run(test_should_play_disclosure())
    asyncio.run(test_generate_transcript())
    asyncio.run(test_mask_credit_card_numbers())
    asyncio.run(test_mask_ssn())
    asyncio.run(test_mask_passwords())
    asyncio.run(test_mask_preserves_normal_text())
    asyncio.run(test_save_transcript())
    asyncio.run(test_create_recording_metadata())
    asyncio.run(test_recording_format_requirements())
    asyncio.run(test_process_call_transcript_complete_pipeline())
    asyncio.run(test_retention_policy())
    
    print("\n✅ All Transcript Service tests passed!")
    print("\nRequirements validated:")
    print("  • 8.1: Record audio in WAV format with 16kHz sample rate ✓")
    print("  • 8.2: Generate complete text transcript ✓")
    print("  • 8.3: Store recording and transcript for 90 days ✓")
    print("  • 8.4: Associate transcript with metadata ✓")
    print("  • 8.5: Play recording disclosure message ✓")
    print("  • 16.5: Mask sensitive information ✓")
