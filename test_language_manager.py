"""Unit tests for LanguageManager."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from language_manager import LanguageManager
from models import Language, CallContext


class TestLanguageManager:
    """Test suite for LanguageManager class."""
    
    @pytest.fixture
    def language_manager(self):
        """Create LanguageManager instance for testing."""
        base_instructions = "You are a helpful AI assistant."
        return LanguageManager(base_instructions=base_instructions)
    
    @pytest.fixture
    def mock_openai_ws(self):
        """Create mock OpenAI WebSocket connection."""
        ws = AsyncMock()
        ws.send = AsyncMock()
        return ws
    
    @pytest.fixture
    def call_context(self):
        """Create CallContext for testing."""
        return CallContext(
            call_id="test-call-123",
            caller_phone="+1234567890",
            language=Language.ENGLISH
        )
    
    def test_language_configs_exist(self, language_manager):
        """Test that all supported languages have configurations."""
        # Verify all Language enum values have configs
        assert Language.ENGLISH in language_manager.LANGUAGE_CONFIGS
        assert Language.HINDI in language_manager.LANGUAGE_CONFIGS
        assert Language.TAMIL in language_manager.LANGUAGE_CONFIGS
        assert Language.TELUGU in language_manager.LANGUAGE_CONFIGS
        assert Language.BENGALI in language_manager.LANGUAGE_CONFIGS
    
    def test_language_config_structure(self, language_manager):
        """Test that language configs have required fields."""
        for lang, config in language_manager.LANGUAGE_CONFIGS.items():
            assert "code" in config
            assert "name" in config
            assert "voice" in config
            assert "instructions_suffix" in config
    
    def test_get_supported_languages(self, language_manager):
        """Test getting list of supported languages."""
        supported = language_manager.get_supported_languages()
        
        assert len(supported) >= 4  # At least English, Hindi, and 2 regional
        assert Language.ENGLISH in supported
        assert Language.HINDI in supported
        assert Language.TAMIL in supported
        assert Language.TELUGU in supported
    
    def test_get_language_name(self, language_manager):
        """Test getting human-readable language names."""
        assert language_manager.get_language_name(Language.ENGLISH) == "English"
        assert language_manager.get_language_name(Language.HINDI) == "Hindi"
        assert language_manager.get_language_name(Language.TAMIL) == "Tamil"
        assert language_manager.get_language_name(Language.TELUGU) == "Telugu"
        assert language_manager.get_language_name(Language.BENGALI) == "Bengali"
    
    @pytest.mark.asyncio
    async def test_detect_language_no_utterances(self, language_manager, mock_openai_ws):
        """Test language detection with no caller utterances."""
        conversation_history = []
        elapsed_time_ms = 5000  # 5 seconds
        
        language, confidence = await language_manager.detect_language(
            mock_openai_ws,
            conversation_history,
            elapsed_time_ms
        )
        
        assert language is None
        assert confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_detect_language_outside_window(self, language_manager, mock_openai_ws):
        """Test language detection outside the 10-second window."""
        conversation_history = [
            {"speaker": "caller", "text": "Hello"}
        ]
        elapsed_time_ms = 15000  # 15 seconds (outside window)
        
        language, confidence = await language_manager.detect_language(
            mock_openai_ws,
            conversation_history,
            elapsed_time_ms
        )
        
        assert language is None
        assert confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_detect_language_english(self, language_manager, mock_openai_ws):
        """Test language detection for English."""
        conversation_history = [
            {"speaker": "caller", "text": "Hello, I need help with my order"}
        ]
        elapsed_time_ms = 5000
        
        language, confidence = await language_manager.detect_language(
            mock_openai_ws,
            conversation_history,
            elapsed_time_ms
        )
        
        assert language == Language.ENGLISH
        assert confidence > 0.0
    
    @pytest.mark.asyncio
    async def test_detect_language_hindi(self, language_manager, mock_openai_ws):
        """Test language detection for Hindi (Devanagari script)."""
        conversation_history = [
            {"speaker": "caller", "text": "नमस्ते, मुझे मदद चाहिए"}
        ]
        elapsed_time_ms = 5000
        
        language, confidence = await language_manager.detect_language(
            mock_openai_ws,
            conversation_history,
            elapsed_time_ms
        )
        
        assert language == Language.HINDI
        assert confidence >= 0.8
    
    @pytest.mark.asyncio
    async def test_detect_language_tamil(self, language_manager, mock_openai_ws):
        """Test language detection for Tamil."""
        conversation_history = [
            {"speaker": "caller", "text": "வணக்கம், எனக்கு உதவி தேவை"}
        ]
        elapsed_time_ms = 5000
        
        language, confidence = await language_manager.detect_language(
            mock_openai_ws,
            conversation_history,
            elapsed_time_ms
        )
        
        assert language == Language.TAMIL
        assert confidence >= 0.8
    
    @pytest.mark.asyncio
    async def test_detect_language_telugu(self, language_manager, mock_openai_ws):
        """Test language detection for Telugu."""
        conversation_history = [
            {"speaker": "caller", "text": "నమస్కారం, నాకు సహాయం కావాలి"}
        ]
        elapsed_time_ms = 5000
        
        language, confidence = await language_manager.detect_language(
            mock_openai_ws,
            conversation_history,
            elapsed_time_ms
        )
        
        assert language == Language.TELUGU
        assert confidence >= 0.8
    
    @pytest.mark.asyncio
    async def test_detect_language_bengali(self, language_manager, mock_openai_ws):
        """Test language detection for Bengali."""
        conversation_history = [
            {"speaker": "caller", "text": "নমস্কার, আমার সাহায্য দরকার"}
        ]
        elapsed_time_ms = 5000
        
        language, confidence = await language_manager.detect_language(
            mock_openai_ws,
            conversation_history,
            elapsed_time_ms
        )
        
        assert language == Language.BENGALI
        assert confidence >= 0.8
    
    @pytest.mark.asyncio
    async def test_should_request_language_selection_none(self, language_manager):
        """Test language selection request when no language detected."""
        should_request = await language_manager.should_request_language_selection(
            None,
            0.0
        )
        
        assert should_request is True
    
    @pytest.mark.asyncio
    async def test_should_request_language_selection_low_confidence(self, language_manager):
        """Test language selection request with low confidence."""
        should_request = await language_manager.should_request_language_selection(
            Language.ENGLISH,
            0.5  # Below 0.8 threshold
        )
        
        assert should_request is True
    
    @pytest.mark.asyncio
    async def test_should_request_language_selection_high_confidence(self, language_manager):
        """Test language selection request with high confidence."""
        should_request = await language_manager.should_request_language_selection(
            Language.ENGLISH,
            0.9  # Above 0.8 threshold
        )
        
        assert should_request is False
    
    @pytest.mark.asyncio
    async def test_update_session_language(self, language_manager, mock_openai_ws):
        """Test updating OpenAI session with a new language."""
        success = await language_manager.update_session_language(
            mock_openai_ws,
            Language.HINDI
        )
        
        assert success is True
        
        # Verify session update was sent
        mock_openai_ws.send.assert_called_once()
        
        # Parse the sent message
        sent_data = json.loads(mock_openai_ws.send.call_args[0][0])
        assert sent_data["type"] == "session.update"
        assert "session" in sent_data
        assert "instructions" in sent_data["session"]
        assert "Hindi" in sent_data["session"]["instructions"] or "हिंदी" in sent_data["session"]["instructions"]
    
    @pytest.mark.asyncio
    async def test_update_session_language_unsupported(self, language_manager, mock_openai_ws):
        """Test updating session with unsupported language raises error."""
        # Create a fake language enum value
        with pytest.raises(ValueError, match="Unsupported language"):
            # This should raise an error since we're passing an invalid language
            await language_manager.update_session_language(
                mock_openai_ws,
                "invalid_language"  # type: ignore
            )
    
    @pytest.mark.asyncio
    async def test_update_session_language_preserves_base_instructions(self, language_manager, mock_openai_ws):
        """Test that updating language preserves base instructions."""
        await language_manager.update_session_language(
            mock_openai_ws,
            Language.TAMIL
        )
        
        sent_data = json.loads(mock_openai_ws.send.call_args[0][0])
        instructions = sent_data["session"]["instructions"]
        
        # Should contain both base instructions and language-specific suffix
        assert "helpful AI assistant" in instructions
        assert "Tamil" in instructions or "தமிழ்" in instructions
    
    @pytest.mark.asyncio
    async def test_handle_language_switch_request(self, language_manager, mock_openai_ws, call_context):
        """Test handling a mid-conversation language switch."""
        original_language = call_context.language
        
        success = await language_manager.handle_language_switch_request(
            mock_openai_ws,
            Language.HINDI,
            call_context
        )
        
        assert success is True
        assert call_context.language == Language.HINDI
        assert call_context.language != original_language
        assert call_context.metadata.get("language_switched") is True
        assert "language_switch_time" in call_context.metadata
    
    @pytest.mark.asyncio
    async def test_handle_language_switch_preserves_context(self, language_manager, mock_openai_ws, call_context):
        """Test that language switch preserves conversation context."""
        # Add some conversation history
        call_context.conversation_history = [
            {"speaker": "caller", "text": "Hello"},
            {"speaker": "assistant", "text": "Hi, how can I help?"}
        ]
        
        await language_manager.handle_language_switch_request(
            mock_openai_ws,
            Language.TAMIL,
            call_context
        )
        
        # Conversation history should be preserved
        assert len(call_context.conversation_history) == 2
        assert call_context.conversation_history[0]["text"] == "Hello"
    
    def test_get_language_selection_prompt(self, language_manager):
        """Test getting multi-language selection prompt."""
        prompt = language_manager.get_language_selection_prompt()
        
        # Should contain text in multiple languages
        assert "English" in prompt
        assert "Hindi" in prompt or "हिंदी" in prompt
        assert "Tamil" in prompt or "தமிழ்" in prompt
        assert "Telugu" in prompt or "తెలుగు" in prompt
        assert "Bengali" in prompt or "বাংলা" in prompt
    
    def test_parse_language_from_text_english(self, language_manager):
        """Test parsing English language selection."""
        assert language_manager.parse_language_from_text("English") == Language.ENGLISH
        assert language_manager.parse_language_from_text("english please") == Language.ENGLISH
        assert language_manager.parse_language_from_text("I want English") == Language.ENGLISH
    
    def test_parse_language_from_text_hindi(self, language_manager):
        """Test parsing Hindi language selection."""
        assert language_manager.parse_language_from_text("Hindi") == Language.HINDI
        assert language_manager.parse_language_from_text("हिंदी") == Language.HINDI
        assert language_manager.parse_language_from_text("I want hindi") == Language.HINDI
    
    def test_parse_language_from_text_tamil(self, language_manager):
        """Test parsing Tamil language selection."""
        assert language_manager.parse_language_from_text("Tamil") == Language.TAMIL
        assert language_manager.parse_language_from_text("தமிழ்") == Language.TAMIL
    
    def test_parse_language_from_text_telugu(self, language_manager):
        """Test parsing Telugu language selection."""
        assert language_manager.parse_language_from_text("Telugu") == Language.TELUGU
        assert language_manager.parse_language_from_text("తెలుగు") == Language.TELUGU
    
    def test_parse_language_from_text_bengali(self, language_manager):
        """Test parsing Bengali language selection."""
        assert language_manager.parse_language_from_text("Bengali") == Language.BENGALI
        assert language_manager.parse_language_from_text("Bangla") == Language.BENGALI
        assert language_manager.parse_language_from_text("বাংলা") == Language.BENGALI
    
    def test_parse_language_from_text_unrecognized(self, language_manager):
        """Test parsing unrecognized language returns None."""
        assert language_manager.parse_language_from_text("French") is None
        assert language_manager.parse_language_from_text("Spanish") is None
        assert language_manager.parse_language_from_text("xyz") is None
    
    def test_detection_window_constant(self, language_manager):
        """Test that detection window is set to 10 seconds."""
        assert language_manager.DETECTION_WINDOW_MS == 10000
    
    def test_confidence_threshold_constant(self, language_manager):
        """Test that confidence threshold is set to 0.8."""
        assert language_manager.DETECTION_CONFIDENCE_THRESHOLD == 0.8
