"""Intent detection interface and implementations for AI Voice Automation system.

This module provides the abstract interface for intent detection implementations
and concrete implementations using OpenAI's function calling capability.

**Validates: Requirements 3.1, 3.2, 3.4**
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
import json
import asyncio
from models import Intent
from config import OPENAI_API_KEY


class IntentDetectorInterface(ABC):
    """Abstract interface for intent detection implementations.
    
    This interface defines the contract for intent detection components that
    analyze conversation content to determine caller intent and request
    clarification when confidence is low.
    
    **Validates: Requirements 3.1, 3.2, 3.4**
    """
    
    @abstractmethod
    async def detect_intent(
        self,
        conversation_history: List[Dict[str, Any]],
        current_transcript: str
    ) -> Tuple[Intent, float]:
        """Detect caller intent from conversation content.
        
        Analyzes the conversation history and current transcript to classify
        the caller's intent and provide a confidence score.
        
        **Validates: Requirement 3.1** - Intent classification
        **Validates: Requirement 3.2** - Intent categorization into defined types
        
        Args:
            conversation_history: List of previous conversation turns, where each
                turn is a dictionary containing speaker, text, and timestamp.
            current_transcript: The current conversation text to analyze.
            
        Returns:
            A tuple containing:
                - Intent: The detected intent (sales_inquiry, support_request,
                  appointment_booking, complaint, general_inquiry, or unknown)
                - float: Confidence score between 0.0 and 1.0
                
        Raises:
            ValueError: If conversation_history or current_transcript is invalid.
            RuntimeError: If intent detection service is unavailable.
        """
        pass
    
    @abstractmethod
    async def request_clarification(
        self,
        current_intent: Intent,
        confidence: float
    ) -> str:
        """Generate clarification question for low-confidence intent detection.
        
        When the confidence score is below the threshold (0.7), this method
        generates an appropriate clarification question to help improve
        intent detection accuracy.
        
        **Validates: Requirement 3.4** - Request clarification when confidence < 0.7
        
        Args:
            current_intent: The currently detected intent with low confidence.
            confidence: The confidence score (expected to be < 0.7).
            
        Returns:
            A clarification question string to ask the caller.
            
        Raises:
            ValueError: If confidence is not between 0.0 and 1.0.
        """
        pass


class OpenAIIntentDetector(IntentDetectorInterface):
    """Intent detection using OpenAI function calling.
    
    This implementation uses OpenAI's function calling capability to analyze
    conversation content and classify caller intent with confidence scores.
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.5**
    """
    
    # Function schema for intent classification
    INTENT_DETECTION_FUNCTIONS = [
        {
            "name": "classify_intent",
            "description": "Classify the caller's intent based on conversation content",
            "parameters": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "enum": [
                            "sales_inquiry",
                            "support_request",
                            "appointment_booking",
                            "complaint",
                            "general_inquiry",
                            "unknown"
                        ],
                        "description": "The primary intent of the caller"
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Confidence score for the classification (0.0 to 1.0)"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why this intent was chosen"
                    }
                },
                "required": ["intent", "confidence"]
            }
        }
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI intent detector.
        
        Args:
            api_key: OpenAI API key. If not provided, uses OPENAI_API_KEY from config.
            
        Raises:
            ValueError: If no API key is provided or available in config.
        """
        self.api_key = api_key if api_key is not None else OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required for intent detection")
        
        self.previous_intent: Optional[Intent] = None
    
    async def detect_intent(
        self,
        conversation_history: List[Dict[str, Any]],
        current_transcript: str
    ) -> Tuple[Intent, float]:
        """Detect caller intent using OpenAI function calling.
        
        **Validates: Requirement 3.1** - Intent classification
        **Validates: Requirement 3.2** - Intent categorization into defined types
        **Validates: Requirement 3.3** - Confidence score assignment
        **Validates: Requirement 3.5** - Intent change detection
        
        Args:
            conversation_history: List of previous conversation turns.
            current_transcript: The current conversation text to analyze.
            
        Returns:
            A tuple containing the detected Intent and confidence score.
            
        Raises:
            ValueError: If conversation_history or current_transcript is invalid.
            RuntimeError: If intent detection service is unavailable.
        """
        # Validate inputs
        if conversation_history is None:
            raise ValueError("conversation_history cannot be None")
        
        if not current_transcript or not isinstance(current_transcript, str):
            raise ValueError("current_transcript must be a non-empty string")
        
        try:
            # Build conversation context for analysis
            conversation_text = self._build_conversation_context(
                conversation_history,
                current_transcript
            )
            
            # Call OpenAI API with function calling
            result = await self._call_openai_function(conversation_text)
            
            # Parse the function call result
            intent_str = result.get("intent", "unknown")
            confidence = float(result.get("confidence", 0.0))
            
            # Convert string to Intent enum
            intent = self._parse_intent(intent_str)
            
            # Validate confidence score
            if not (0.0 <= confidence <= 1.0):
                confidence = max(0.0, min(1.0, confidence))
            
            # Detect intent change (Requirement 3.5)
            if self.previous_intent is not None and self.previous_intent != intent:
                print(f"Intent changed from {self.previous_intent.value} to {intent.value}")
            
            self.previous_intent = intent
            
            return (intent, confidence)
            
        except Exception as e:
            raise RuntimeError(f"Intent detection service unavailable: {str(e)}")
    
    async def request_clarification(
        self,
        current_intent: Intent,
        confidence: float
    ) -> str:
        """Generate clarification question for low-confidence intent detection.
        
        **Validates: Requirement 3.4** - Request clarification when confidence < 0.7
        
        Args:
            current_intent: The currently detected intent with low confidence.
            confidence: The confidence score (expected to be < 0.7).
            
        Returns:
            A clarification question string to ask the caller.
            
        Raises:
            ValueError: If confidence is not between 0.0 and 1.0.
        """
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")
        
        # Generate intent-specific clarification questions
        clarification_templates = {
            Intent.SALES_INQUIRY: "I want to make sure I understand correctly - are you interested in learning more about our products or services?",
            Intent.SUPPORT_REQUEST: "Just to clarify, are you looking for technical support or assistance with an existing product?",
            Intent.APPOINTMENT_BOOKING: "Would you like to schedule an appointment with us?",
            Intent.COMPLAINT: "I understand you may have a concern. Could you tell me more about the issue you're experiencing?",
            Intent.GENERAL_INQUIRY: "How can I best assist you today? Are you looking for information about our services?",
            Intent.UNKNOWN: "I want to make sure I can help you properly. Could you tell me a bit more about what you're looking for?"
        }
        
        return clarification_templates.get(
            current_intent,
            "Could you please clarify what you're looking for so I can assist you better?"
        )
    
    def _build_conversation_context(
        self,
        conversation_history: List[Dict[str, Any]],
        current_transcript: str
    ) -> str:
        """Build conversation context string for intent analysis.
        
        Args:
            conversation_history: List of previous conversation turns.
            current_transcript: The current conversation text.
            
        Returns:
            Formatted conversation context string.
        """
        context_parts = []
        
        # Add conversation history
        for turn in conversation_history:
            speaker = turn.get("speaker", "unknown")
            text = turn.get("text", "")
            if text:
                context_parts.append(f"{speaker}: {text}")
        
        # Add current transcript
        if current_transcript:
            context_parts.append(f"Current: {current_transcript}")
        
        return "\n".join(context_parts)
    
    async def _call_openai_function(self, conversation_text: str) -> Dict[str, Any]:
        """Call OpenAI API with function calling to classify intent.
        
        This is a placeholder implementation that simulates the OpenAI API call.
        In production, this would use the actual OpenAI Realtime API with function calling.
        
        Args:
            conversation_text: The conversation context to analyze.
            
        Returns:
            Dictionary containing intent classification result.
        """
        # TODO: Replace with actual OpenAI Realtime API function calling
        # For now, implement a simple keyword-based classifier as a placeholder
        
        text_lower = conversation_text.lower()
        
        # Extract only caller/current messages (ignore assistant greetings)
        caller_text = ""
        for line in text_lower.split("\n"):
            if line.startswith("caller:") or line.startswith("current:"):
                caller_text += " " + line
        
        # If no caller text, use full text
        if not caller_text.strip():
            caller_text = text_lower
        
        # Priority-based classification (check more specific intents first)
        # Check for complaint first (most specific)
        if any(word in caller_text for word in ["complaint", "unhappy", "disappointed", "refund", "terrible", "awful"]):
            return {"intent": "complaint", "confidence": 0.80, "reasoning": "Keywords indicate complaint"}
        
        # Check for support request
        elif any(word in caller_text for word in ["need help", "support", "problem", "issue", "not working", "broken"]):
            return {"intent": "support_request", "confidence": 0.80, "reasoning": "Keywords indicate support need"}
        
        # Check for appointment booking
        elif any(word in caller_text for word in ["appointment", "schedule", "book", "meeting", "available", "time slot"]):
            return {"intent": "appointment_booking", "confidence": 0.85, "reasoning": "Keywords indicate appointment booking"}
        
        # Check for sales inquiry
        elif any(word in caller_text for word in ["buy", "purchase", "price", "cost", "product", "service", "interested", "buying"]):
            return {"intent": "sales_inquiry", "confidence": 0.85, "reasoning": "Keywords indicate sales interest"}
        
        # Check for general inquiry
        elif any(word in caller_text for word in ["information", "tell me", "what is", "how does", "explain"]):
            return {"intent": "general_inquiry", "confidence": 0.75, "reasoning": "Keywords indicate general inquiry"}
        
        else:
            return {"intent": "unknown", "confidence": 0.50, "reasoning": "No clear intent detected"}
    
    def _parse_intent(self, intent_str: str) -> Intent:
        """Parse intent string to Intent enum.
        
        Args:
            intent_str: Intent string from function call result.
            
        Returns:
            Intent enum value.
        """
        intent_mapping = {
            "sales_inquiry": Intent.SALES_INQUIRY,
            "support_request": Intent.SUPPORT_REQUEST,
            "appointment_booking": Intent.APPOINTMENT_BOOKING,
            "complaint": Intent.COMPLAINT,
            "general_inquiry": Intent.GENERAL_INQUIRY,
            "unknown": Intent.UNKNOWN
        }
        
        return intent_mapping.get(intent_str, Intent.UNKNOWN)
