"""Unit tests for IntentDetectorInterface.

**Validates: Requirements 3.1, 3.2, 3.4**
"""

import pytest
from typing import List, Dict, Any, Tuple
from intent_detector import IntentDetectorInterface
from models import Intent


class MockIntentDetector(IntentDetectorInterface):
    """Mock implementation of IntentDetectorInterface for testing."""
    
    async def detect_intent(
        self,
        conversation_history: List[Dict[str, Any]],
        current_transcript: str
    ) -> Tuple[Intent, float]:
        """Mock implementation that returns predefined intent."""
        # Simple mock: return sales_inquiry with high confidence
        return (Intent.SALES_INQUIRY, 0.85)
    
    async def request_clarification(
        self,
        current_intent: Intent,
        confidence: float
    ) -> str:
        """Mock implementation that returns a clarification question."""
        return f"Could you please clarify if you're looking for {current_intent.value}?"


class TestIntentDetectorInterface:
    """Test suite for IntentDetectorInterface abstract class."""
    
    def test_interface_cannot_be_instantiated(self):
        """Test that IntentDetectorInterface cannot be instantiated directly.
        
        **Validates: Requirement 3.1** - Interface definition
        """
        with pytest.raises(TypeError):
            IntentDetectorInterface()
    
    @pytest.mark.asyncio
    async def test_detect_intent_signature(self):
        """Test that detect_intent method has correct signature.
        
        **Validates: Requirement 3.1, 3.2** - Intent detection method
        """
        detector = MockIntentDetector()
        
        conversation_history = [
            {"speaker": "caller", "text": "Hello", "timestamp": 0},
            {"speaker": "assistant", "text": "Hi, how can I help?", "timestamp": 1000}
        ]
        current_transcript = "I want to buy your product"
        
        intent, confidence = await detector.detect_intent(
            conversation_history,
            current_transcript
        )
        
        # Verify return types
        assert isinstance(intent, Intent)
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_detect_intent_returns_valid_intent(self):
        """Test that detect_intent returns a valid Intent enum value.
        
        **Validates: Requirement 3.2** - Intent categorization
        """
        detector = MockIntentDetector()
        
        intent, confidence = await detector.detect_intent([], "test transcript")
        
        # Verify intent is one of the valid enum values
        valid_intents = [
            Intent.SALES_INQUIRY,
            Intent.SUPPORT_REQUEST,
            Intent.APPOINTMENT_BOOKING,
            Intent.COMPLAINT,
            Intent.GENERAL_INQUIRY,
            Intent.UNKNOWN
        ]
        assert intent in valid_intents
    
    @pytest.mark.asyncio
    async def test_detect_intent_confidence_in_range(self):
        """Test that confidence score is between 0.0 and 1.0.
        
        **Validates: Requirement 3.1** - Confidence score assignment
        """
        detector = MockIntentDetector()
        
        intent, confidence = await detector.detect_intent([], "test transcript")
        
        assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_request_clarification_signature(self):
        """Test that request_clarification method has correct signature.
        
        **Validates: Requirement 3.4** - Clarification request method
        """
        detector = MockIntentDetector()
        
        clarification = await detector.request_clarification(
            Intent.SALES_INQUIRY,
            0.65
        )
        
        # Verify return type
        assert isinstance(clarification, str)
        assert len(clarification) > 0
    
    @pytest.mark.asyncio
    async def test_request_clarification_for_low_confidence(self):
        """Test clarification request for low confidence intent.
        
        **Validates: Requirement 3.4** - Request clarification when confidence < 0.7
        """
        detector = MockIntentDetector()
        
        # Test with confidence below threshold
        clarification = await detector.request_clarification(
            Intent.UNKNOWN,
            0.5
        )
        
        assert isinstance(clarification, str)
        assert len(clarification) > 0
    
    @pytest.mark.asyncio
    async def test_multiple_intent_types(self):
        """Test that interface supports all intent types.
        
        **Validates: Requirement 3.2** - Support for all intent categories
        """
        detector = MockIntentDetector()
        
        # Test that all intent types can be used
        all_intents = [
            Intent.SALES_INQUIRY,
            Intent.SUPPORT_REQUEST,
            Intent.APPOINTMENT_BOOKING,
            Intent.COMPLAINT,
            Intent.GENERAL_INQUIRY,
            Intent.UNKNOWN
        ]
        
        for intent_type in all_intents:
            clarification = await detector.request_clarification(intent_type, 0.6)
            assert isinstance(clarification, str)


class TestMockIntentDetector:
    """Test suite for MockIntentDetector implementation."""
    
    @pytest.mark.asyncio
    async def test_mock_detector_basic_functionality(self):
        """Test that mock detector implements interface correctly."""
        detector = MockIntentDetector()
        
        # Test detect_intent
        intent, confidence = await detector.detect_intent(
            [{"speaker": "caller", "text": "Hello"}],
            "I need help"
        )
        assert intent == Intent.SALES_INQUIRY
        assert confidence == 0.85
        
        # Test request_clarification
        clarification = await detector.request_clarification(Intent.UNKNOWN, 0.5)
        assert "clarify" in clarification.lower()
        assert "unknown" in clarification.lower()



class TestOpenAIIntentDetector:
    """Test suite for OpenAIIntentDetector implementation.
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.5**
    """
    
    def test_initialization_with_api_key(self):
        """Test that OpenAIIntentDetector can be initialized with API key.
        
        **Validates: Requirement 3.1** - Detector initialization
        """
        from intent_detector import OpenAIIntentDetector
        
        detector = OpenAIIntentDetector(api_key="test_key")
        assert detector.api_key == "test_key"
    
    def test_initialization_without_api_key_raises_error(self):
        """Test that initialization fails without API key.
        
        **Validates: Requirement 3.1** - API key validation
        """
        from intent_detector import OpenAIIntentDetector
        
        # Pass empty string to simulate missing API key
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            OpenAIIntentDetector(api_key="")
    
    @pytest.mark.asyncio
    async def test_detect_sales_inquiry_intent(self):
        """Test detection of sales inquiry intent.
        
        **Validates: Requirement 3.2** - Sales inquiry classification
        """
        from intent_detector import OpenAIIntentDetector
        
        detector = OpenAIIntentDetector(api_key="test_key")
        
        conversation_history = [
            {"speaker": "assistant", "text": "Hello, how can I help you?", "timestamp": 0}
        ]
        current_transcript = "I'm interested in buying your product"
        
        intent, confidence = await detector.detect_intent(
            conversation_history,
            current_transcript
        )
        
        assert intent == Intent.SALES_INQUIRY
        assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_detect_support_request_intent(self):
        """Test detection of support request intent.
        
        **Validates: Requirement 3.2** - Support request classification
        """
        from intent_detector import OpenAIIntentDetector
        
        detector = OpenAIIntentDetector(api_key="test_key")
        
        conversation_history = []
        current_transcript = "I need help with my product, it's not working"
        
        intent, confidence = await detector.detect_intent(
            conversation_history,
            current_transcript
        )
        
        assert intent == Intent.SUPPORT_REQUEST
        assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_detect_appointment_booking_intent(self):
        """Test detection of appointment booking intent.
        
        **Validates: Requirement 3.2** - Appointment booking classification
        """
        from intent_detector import OpenAIIntentDetector
        
        detector = OpenAIIntentDetector(api_key="test_key")
        
        conversation_history = []
        current_transcript = "I'd like to schedule an appointment for next week"
        
        intent, confidence = await detector.detect_intent(
            conversation_history,
            current_transcript
        )
        
        assert intent == Intent.APPOINTMENT_BOOKING
        assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_detect_complaint_intent(self):
        """Test detection of complaint intent.
        
        **Validates: Requirement 3.2** - Complaint classification
        """
        from intent_detector import OpenAIIntentDetector
        
        detector = OpenAIIntentDetector(api_key="test_key")
        
        conversation_history = []
        current_transcript = "I'm very unhappy with your service, I want a refund"
        
        intent, confidence = await detector.detect_intent(
            conversation_history,
            current_transcript
        )
        
        assert intent == Intent.COMPLAINT
        assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_detect_general_inquiry_intent(self):
        """Test detection of general inquiry intent.
        
        **Validates: Requirement 3.2** - General inquiry classification
        """
        from intent_detector import OpenAIIntentDetector
        
        detector = OpenAIIntentDetector(api_key="test_key")
        
        conversation_history = []
        current_transcript = "Can you tell me more information about your company?"
        
        intent, confidence = await detector.detect_intent(
            conversation_history,
            current_transcript
        )
        
        assert intent == Intent.GENERAL_INQUIRY
        assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_detect_unknown_intent(self):
        """Test detection of unknown intent.
        
        **Validates: Requirement 3.2** - Unknown intent classification
        """
        from intent_detector import OpenAIIntentDetector
        
        detector = OpenAIIntentDetector(api_key="test_key")
        
        conversation_history = []
        current_transcript = "Hello there"
        
        intent, confidence = await detector.detect_intent(
            conversation_history,
            current_transcript
        )
        
        assert intent == Intent.UNKNOWN
        assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_confidence_score_in_valid_range(self):
        """Test that confidence scores are always between 0.0 and 1.0.
        
        **Validates: Requirement 3.3** - Confidence score assignment
        """
        from intent_detector import OpenAIIntentDetector
        
        detector = OpenAIIntentDetector(api_key="test_key")
        
        test_cases = [
            "I want to buy something",
            "I need help",
            "Book an appointment",
            "I have a complaint",
            "Tell me about your services",
            "Random text"
        ]
        
        for transcript in test_cases:
            intent, confidence = await detector.detect_intent([], transcript)
            assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} out of range for: {transcript}"
    
    @pytest.mark.asyncio
    async def test_intent_change_detection(self):
        """Test that intent changes are detected during conversation.
        
        **Validates: Requirement 3.5** - Intent change detection
        """
        from intent_detector import OpenAIIntentDetector
        
        detector = OpenAIIntentDetector(api_key="test_key")
        
        # First detection - sales inquiry
        intent1, _ = await detector.detect_intent([], "I want to buy your product")
        assert intent1 == Intent.SALES_INQUIRY
        
        # Second detection - support request (intent change)
        intent2, _ = await detector.detect_intent([], "Actually, I need help with an issue")
        assert intent2 == Intent.SUPPORT_REQUEST
        
        # Verify intent changed
        assert intent1 != intent2
    
    @pytest.mark.asyncio
    async def test_invalid_conversation_history_raises_error(self):
        """Test that invalid conversation history raises ValueError.
        
        **Validates: Requirement 3.1** - Input validation
        """
        from intent_detector import OpenAIIntentDetector
        
        detector = OpenAIIntentDetector(api_key="test_key")
        
        with pytest.raises(ValueError, match="conversation_history cannot be None"):
            await detector.detect_intent(None, "test")
    
    @pytest.mark.asyncio
    async def test_empty_transcript_raises_error(self):
        """Test that empty transcript raises ValueError.
        
        **Validates: Requirement 3.1** - Input validation
        """
        from intent_detector import OpenAIIntentDetector
        
        detector = OpenAIIntentDetector(api_key="test_key")
        
        with pytest.raises(ValueError, match="current_transcript must be a non-empty string"):
            await detector.detect_intent([], "")
    
    @pytest.mark.asyncio
    async def test_clarification_for_sales_inquiry(self):
        """Test clarification message for sales inquiry intent.
        
        **Validates: Requirement 3.4** - Clarification request generation
        """
        from intent_detector import OpenAIIntentDetector
        
        detector = OpenAIIntentDetector(api_key="test_key")
        
        clarification = await detector.request_clarification(Intent.SALES_INQUIRY, 0.6)
        
        assert isinstance(clarification, str)
        assert len(clarification) > 0
        assert "product" in clarification.lower() or "service" in clarification.lower()
    
    @pytest.mark.asyncio
    async def test_clarification_for_unknown_intent(self):
        """Test clarification message for unknown intent.
        
        **Validates: Requirement 3.4** - Clarification request generation
        """
        from intent_detector import OpenAIIntentDetector
        
        detector = OpenAIIntentDetector(api_key="test_key")
        
        clarification = await detector.request_clarification(Intent.UNKNOWN, 0.5)
        
        assert isinstance(clarification, str)
        assert len(clarification) > 0
    
    @pytest.mark.asyncio
    async def test_clarification_with_invalid_confidence_raises_error(self):
        """Test that invalid confidence score raises ValueError.
        
        **Validates: Requirement 3.4** - Confidence validation
        """
        from intent_detector import OpenAIIntentDetector
        
        detector = OpenAIIntentDetector(api_key="test_key")
        
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            await detector.request_clarification(Intent.SALES_INQUIRY, 1.5)
        
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            await detector.request_clarification(Intent.SALES_INQUIRY, -0.1)
    
    @pytest.mark.asyncio
    async def test_conversation_context_building(self):
        """Test that conversation context is properly built from history.
        
        **Validates: Requirement 3.1** - Conversation analysis
        """
        from intent_detector import OpenAIIntentDetector
        
        detector = OpenAIIntentDetector(api_key="test_key")
        
        conversation_history = [
            {"speaker": "assistant", "text": "Hello, how can I help?", "timestamp": 0},
            {"speaker": "caller", "text": "I have a question", "timestamp": 1000}
        ]
        current_transcript = "about your pricing"
        
        # This should not raise an error and should process the conversation
        intent, confidence = await detector.detect_intent(
            conversation_history,
            current_transcript
        )
        
        assert isinstance(intent, Intent)
        assert isinstance(confidence, float)
