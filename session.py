"""Session state management for per-call data."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import Language, Intent


@dataclass
class SessionState:
    """Holds state for a single call session between Twilio and OpenAI."""
    
    # Twilio/OpenAI streaming state
    stream_sid: Optional[str] = None
    call_sid: Optional[str] = None  # Twilio Call SID (CA...)
    latest_media_timestamp: int = 0
    last_assistant_item: Optional[str] = None
    mark_queue: list[str] = field(default_factory=list)
    response_start_timestamp_twilio: Optional[int] = None
    
    # Call context fields
    call_id: Optional[str] = None
    caller_phone: Optional[str] = None
    language: Language = Language.ENGLISH
    intent: Optional[Intent] = None
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # AI feature services (injected from main.py)
    call_manager: Optional[Any] = None
    intent_detector: Optional[Any] = None
    language_manager: Optional[Any] = None
    call_router: Optional[Any] = None
    call_start_time: Optional[datetime] = None
    
    def reset_on_stream_start(self, stream_sid: str) -> None:
        """Reset state when a new stream starts."""
        self.stream_sid = stream_sid
        self.response_start_timestamp_twilio = None
        self.latest_media_timestamp = 0
        self.last_assistant_item = None
    
    def clear_interruption_state(self) -> None:
        """
        Clear state after handling an interruption.
        
        This method clears only the audio streaming state (mark queue, timestamps)
        while preserving conversation context (conversation_history, call_id, intent, language).
        This ensures the AI can resume with contextually appropriate responses after interruption.
        
        Requirement 10.5: Context preservation during interruptions
        """
        self.mark_queue.clear()
        self.last_assistant_item = None
        self.response_start_timestamp_twilio = None
        # NOTE: conversation_history, call_id, intent, and language are intentionally preserved
    
    def update_call_context(
        self,
        call_id: Optional[str] = None,
        caller_phone: Optional[str] = None,
        language: Optional[Language] = None,
        intent: Optional[Intent] = None
    ) -> None:
        """Update call context fields."""
        if call_id is not None:
            self.call_id = call_id
        if caller_phone is not None:
            self.caller_phone = caller_phone
        if language is not None:
            self.language = language
        if intent is not None:
            self.intent = intent
    
    def add_conversation_turn(
        self,
        speaker: str,
        text: str,
        timestamp_ms: Optional[int] = None
    ) -> None:
        """Add a conversation turn to history."""
        turn = {
            "speaker": speaker,
            "text": text,
            "timestamp_ms": timestamp_ms or self.latest_media_timestamp
        }
        self.conversation_history.append(turn)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the complete conversation history."""
        return self.conversation_history.copy()
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()

