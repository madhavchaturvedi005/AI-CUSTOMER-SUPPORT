"""Language Manager for multi-language detection and switching."""

import json
from typing import Optional, Tuple
from datetime import datetime, timezone
import websockets

from models import Language, CallContext


class LanguageManager:
    """
    Manages language detection and switching for voice calls.
    
    Responsibilities:
    - Detect caller's language within first 10 seconds
    - Update OpenAI session with detected language
    - Handle mid-conversation language switch requests
    - Support English, Hindi, Tamil, Telugu, and Bengali
    
    Requirements: 2.3, 13.1, 13.2, 13.3, 13.4, 13.5
    """
    
    # Language configuration for OpenAI
    LANGUAGE_CONFIGS = {
        Language.ENGLISH: {
            "code": "en",
            "name": "English",
            "voice": "alloy",
            "instructions_suffix": "Respond in English."
        },
        Language.HINDI: {
            "code": "hi",
            "name": "Hindi",
            "voice": "alloy",
            "instructions_suffix": "Respond in Hindi (हिंदी में जवाब दें)."
        },
        Language.TAMIL: {
            "code": "ta",
            "name": "Tamil",
            "voice": "alloy",
            "instructions_suffix": "Respond in Tamil (தமிழில் பதிலளிக்கவும்)."
        },
        Language.TELUGU: {
            "code": "te",
            "name": "Telugu",
            "voice": "alloy",
            "instructions_suffix": "Respond in Telugu (తెలుగులో స్పందించండి)."
        },
        Language.BENGALI: {
            "code": "bn",
            "name": "Bengali",
            "voice": "alloy",
            "instructions_suffix": "Respond in Bengali (বাংলায় উত্তর দিন)."
        }
    }
    
    # Language detection threshold (confidence score)
    DETECTION_CONFIDENCE_THRESHOLD = 0.8
    
    # Time window for initial language detection (milliseconds)
    DETECTION_WINDOW_MS = 10000  # 10 seconds
    
    def __init__(self, base_instructions: str = ""):
        """
        Initialize LanguageManager.
        
        Args:
            base_instructions: Base system instructions for the AI assistant
        """
        self.base_instructions = base_instructions
    
    async def detect_language(
        self,
        openai_ws: websockets.WebSocketClientProtocol,
        conversation_history: list[dict],
        elapsed_time_ms: int
    ) -> Tuple[Optional[Language], float]:
        """
        Detect the caller's language from conversation history.
        
        This method analyzes the conversation within the first 10 seconds
        to detect the caller's language. It uses OpenAI function calling
        to classify the language with a confidence score.
        
        Args:
            openai_ws: WebSocket connection to OpenAI
            conversation_history: List of conversation turns
            elapsed_time_ms: Time elapsed since call start (milliseconds)
            
        Returns:
            Tuple of (detected_language, confidence_score)
            Returns (None, 0.0) if detection window hasn't passed or no speech detected
            
        Requirements: 13.1, 13.2
        """
        # Only detect within the first 10 seconds
        if elapsed_time_ms > self.DETECTION_WINDOW_MS:
            return (None, 0.0)
        
        # Need at least one caller utterance to detect language
        caller_utterances = [
            turn for turn in conversation_history
            if turn.get("speaker") == "caller"
        ]
        
        if not caller_utterances:
            return (None, 0.0)
        
        # Combine caller utterances for analysis
        caller_text = " ".join([turn.get("text", "") for turn in caller_utterances])
        
        if not caller_text.strip():
            return (None, 0.0)
        
        # Use simple heuristics for language detection
        # In a production system, this would use OpenAI function calling
        # or a dedicated language detection service
        detected_language, confidence = self._detect_language_heuristic(caller_text)
        
        return (detected_language, confidence)
    
    def _detect_language_heuristic(self, text: str) -> Tuple[Language, float]:
        """
        Detect language using simple heuristics.
        
        This is a simplified implementation. In production, this would use
        OpenAI function calling or a dedicated language detection library.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (detected_language, confidence_score)
        """
        # Simple heuristic: check for language-specific characters
        text_lower = text.lower()
        
        # Hindi detection (Devanagari script)
        if any('\u0900' <= char <= '\u097F' for char in text):
            return (Language.HINDI, 0.9)
        
        # Tamil detection (Tamil script)
        if any('\u0B80' <= char <= '\u0BFF' for char in text):
            return (Language.TAMIL, 0.9)
        
        # Telugu detection (Telugu script)
        if any('\u0C00' <= char <= '\u0C7F' for char in text):
            return (Language.TELUGU, 0.9)
        
        # Bengali detection (Bengali script)
        if any('\u0980' <= char <= '\u09FF' for char in text):
            return (Language.BENGALI, 0.9)
        
        # Default to English
        return (Language.ENGLISH, 0.85)
    
    async def should_request_language_selection(
        self,
        detected_language: Optional[Language],
        confidence: float
    ) -> bool:
        """
        Determine if the system should ask the caller to select their language.
        
        If language detection confidence is below 0.8, the system should
        ask the caller to explicitly select their preferred language.
        
        Args:
            detected_language: Detected language (or None)
            confidence: Detection confidence score
            
        Returns:
            True if language selection should be requested
            
        Requirements: 13.4
        """
        if detected_language is None:
            return True
        
        return confidence < self.DETECTION_CONFIDENCE_THRESHOLD
    
    async def update_session_language(
        self,
        openai_ws: websockets.WebSocketClientProtocol,
        language: Language,
        preserve_context: bool = True
    ) -> bool:
        """
        Update OpenAI session with the specified language.
        
        This method sends a session.update event to OpenAI to change
        the language configuration. It updates the instructions to
        include language-specific guidance.
        
        Args:
            openai_ws: WebSocket connection to OpenAI
            language: Target language
            preserve_context: Whether to preserve conversation context (default: True)
            
        Returns:
            True if update was successful
            
        Requirements: 13.3, 13.4, 13.5
        """
        if language not in self.LANGUAGE_CONFIGS:
            raise ValueError(f"Unsupported language: {language}")
        
        lang_config = self.LANGUAGE_CONFIGS[language]
        
        # Build updated instructions with language-specific suffix
        updated_instructions = self.base_instructions
        if updated_instructions and not updated_instructions.endswith("."):
            updated_instructions += "."
        updated_instructions += f" {lang_config['instructions_suffix']}"
        
        # Send session update to OpenAI
        session_update = {
            "type": "session.update",
            "session": {
                "instructions": updated_instructions,
                "audio": {
                    "output": {
                        "voice": lang_config["voice"]
                    }
                }
            }
        }
        
        try:
            await openai_ws.send(json.dumps(session_update))
            print(f"Updated session language to {lang_config['name']} ({lang_config['code']})")
            return True
        except Exception as e:
            print(f"Error updating session language: {e}")
            return False
    
    async def handle_language_switch_request(
        self,
        openai_ws: websockets.WebSocketClientProtocol,
        requested_language: Language,
        call_context: CallContext
    ) -> bool:
        """
        Handle a mid-conversation language switch request.
        
        This method:
        1. Updates the OpenAI session with the new language
        2. Updates the call context with the new language
        3. Preserves conversation context during the switch
        
        Args:
            openai_ws: WebSocket connection to OpenAI
            requested_language: Language requested by caller
            call_context: Current call context
            
        Returns:
            True if language switch was successful
            
        Requirements: 13.3, 13.5
        """
        # Update OpenAI session
        success = await self.update_session_language(
            openai_ws,
            requested_language,
            preserve_context=True
        )
        
        if not success:
            return False
        
        # Update call context
        call_context.language = requested_language
        call_context.metadata["language_switched"] = True
        call_context.metadata["language_switch_time"] = datetime.now(timezone.utc).isoformat()
        
        return True
    
    def get_language_selection_prompt(self) -> str:
        """
        Get a prompt asking the caller to select their preferred language.
        
        Returns:
            Multi-language prompt for language selection
            
        Requirements: 13.4
        """
        return (
            "Please select your preferred language. "
            "कृपया अपनी पसंदीदा भाषा चुनें। "
            "தயவுசெய்து உங்கள் விருப்பமான மொழியைத் தேர்ந்தெடுக்கவும். "
            "దయచేసి మీ ఇష్టమైన భాషను ఎంచుకోండి। "
            "আপনার পছন্দের ভাষা নির্বাচন করুন। "
            "Say English, Hindi, Tamil, Telugu, or Bengali."
        )
    
    def parse_language_from_text(self, text: str) -> Optional[Language]:
        """
        Parse language selection from caller's text response.
        
        Args:
            text: Caller's text response
            
        Returns:
            Detected Language or None if not recognized
        """
        text_lower = text.lower().strip()
        
        # English
        if any(word in text_lower for word in ["english", "inglish", "angrezi"]):
            return Language.ENGLISH
        
        # Hindi
        if any(word in text_lower for word in ["hindi", "हिंदी", "हिन्दी"]):
            return Language.HINDI
        
        # Tamil
        if any(word in text_lower for word in ["tamil", "தமிழ்"]):
            return Language.TAMIL
        
        # Telugu
        if any(word in text_lower for word in ["telugu", "తెలుగు"]):
            return Language.TELUGU
        
        # Bengali
        if any(word in text_lower for word in ["bengali", "bangla", "বাংলা"]):
            return Language.BENGALI
        
        return None
    
    def get_supported_languages(self) -> list[Language]:
        """
        Get list of supported languages.
        
        Returns:
            List of supported Language enums
            
        Requirements: 13.1
        """
        return list(self.LANGUAGE_CONFIGS.keys())
    
    def get_language_name(self, language: Language) -> str:
        """
        Get human-readable name for a language.
        
        Args:
            language: Language enum
            
        Returns:
            Language name
        """
        return self.LANGUAGE_CONFIGS.get(language, {}).get("name", "Unknown")
