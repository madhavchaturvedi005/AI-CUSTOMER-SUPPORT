"""Core data models and enums for AI Voice Automation system."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class CallStatus(Enum):
    """Status of a call throughout its lifecycle."""
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"


class Intent(Enum):
    """Detected intent of the caller."""
    SALES_INQUIRY = "sales_inquiry"
    SUPPORT_REQUEST = "support_request"
    APPOINTMENT_BOOKING = "appointment_booking"
    COMPLAINT = "complaint"
    GENERAL_INQUIRY = "general_inquiry"
    UNKNOWN = "unknown"


class Language(Enum):
    """Supported languages for conversation."""
    ENGLISH = "en"
    HINDI = "hi"
    TAMIL = "ta"
    TELUGU = "te"
    BENGALI = "bn"


@dataclass
class CallContext:
    """Complete context for a call session."""
    call_id: str
    caller_phone: str
    caller_name: Optional[str] = None
    language: Language = Language.ENGLISH
    intent: Optional[Intent] = None
    intent_confidence: float = 0.0
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    lead_data: Optional[Dict[str, Any]] = None
    appointment_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def validate(self) -> None:
        """Validate data integrity of CallContext."""
        if not self.call_id:
            raise ValueError("call_id cannot be empty")
        
        if not self.caller_phone:
            raise ValueError("caller_phone cannot be empty")
        
        if self.intent_confidence < 0.0 or self.intent_confidence > 1.0:
            raise ValueError("intent_confidence must be between 0.0 and 1.0")
        
        if not isinstance(self.language, Language):
            raise ValueError("language must be a Language enum value")
        
        if self.intent is not None and not isinstance(self.intent, Intent):
            raise ValueError("intent must be an Intent enum value or None")


@dataclass
class LeadData:
    """Lead information captured during conversation."""
    name: str
    phone: str
    email: Optional[str] = None
    inquiry_details: str = ""
    budget_indication: Optional[str] = None
    timeline: Optional[str] = None
    decision_authority: bool = False
    lead_score: int = 0  # 1-10
    source: str = "voice_call"
    
    def validate(self) -> None:
        """Validate data integrity of LeadData."""
        if not self.name:
            raise ValueError("name cannot be empty")
        
        if not self.phone:
            raise ValueError("phone cannot be empty")
        
        if self.lead_score < 0 or self.lead_score > 10:
            raise ValueError("lead_score must be between 0 and 10")
        
        if self.email is not None and self.email and "@" not in self.email:
            raise ValueError("email must be a valid email address")


@dataclass
class AppointmentData:
    """Appointment booking information."""
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    service_type: str = ""
    appointment_datetime: Optional[datetime] = None
    duration_minutes: int = 30
    notes: Optional[str] = None
    confirmation_sent: bool = False
    
    def validate(self) -> None:
        """Validate data integrity of AppointmentData."""
        if not self.customer_name:
            raise ValueError("customer_name cannot be empty")
        
        if not self.customer_phone:
            raise ValueError("customer_phone cannot be empty")
        
        if not self.service_type:
            raise ValueError("service_type cannot be empty")
        
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        
        if self.appointment_datetime is not None and self.appointment_datetime < datetime.now(timezone.utc):
            raise ValueError("appointment_datetime cannot be in the past")
        
        if self.customer_email is not None and self.customer_email and "@" not in self.customer_email:
            raise ValueError("customer_email must be a valid email address")
