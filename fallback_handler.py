"""Fallback and error handling service for system resilience."""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum


class ErrorType(Enum):
    """Types of errors that can occur."""
    OPENAI_CONNECTION_FAILURE = "openai_connection_failure"
    SPEECH_RECOGNITION_FAILURE = "speech_recognition_failure"
    SYSTEM_FAILURE = "system_failure"
    DATABASE_FAILURE = "database_failure"
    NETWORK_FAILURE = "network_failure"


class FallbackMode(Enum):
    """Fallback operation modes."""
    NORMAL = "normal"
    PRE_RECORDED_RESPONSES = "pre_recorded_responses"
    VOICEMAIL_ONLY = "voicemail_only"


class FallbackHandler:
    """
    Handles errors and provides fallback mechanisms.
    
    Implements Requirements 14.1-14.5:
    - 14.1: Switch to pre-recorded responses on OpenAI failure
    - 14.2: Offer transfer or message after 3 speech failures
    - 14.3: Record voicemail and alert on system failure
    - 14.4: Log all errors with context
    - 14.5: Resume normal operation automatically
    """
    
    def __init__(
        self,
        alert_callback: Optional[callable] = None,
        voicemail_callback: Optional[callable] = None
    ):
        """
        Initialize FallbackHandler.
        
        Args:
            alert_callback: Optional callback to send alerts
            voicemail_callback: Optional callback to record voicemail
        """
        self.alert_callback = alert_callback
        self.voicemail_callback = voicemail_callback
        self.current_mode = FallbackMode.NORMAL
        self.error_log: List[Dict[str, Any]] = []
        self.speech_failure_count: Dict[str, int] = {}
        self.max_speech_failures = 3
    
    def is_in_fallback_mode(self) -> bool:
        """Check if system is in fallback mode."""
        return self.current_mode != FallbackMode.NORMAL
    
    def get_current_mode(self) -> FallbackMode:
        """Get current fallback mode."""
        return self.current_mode
    
    async def handle_openai_connection_failure(
        self,
        call_id: str,
        error_details: str
    ) -> Dict[str, Any]:
        """
        Handle OpenAI API connection failure.
        
        Switches to pre-recorded response tree fallback.
        
        Args:
            call_id: Unique call identifier
            error_details: Error description
            
        Returns:
            Recovery action details
            
        Requirement 14.1: Switch to pre-recorded responses
        """
        # Log error
        await self.log_error(
            error_type=ErrorType.OPENAI_CONNECTION_FAILURE,
            call_id=call_id,
            error_details=error_details,
            recovery_action="switched_to_pre_recorded_responses"
        )
        
        # Switch to fallback mode
        self.current_mode = FallbackMode.PRE_RECORDED_RESPONSES
        
        # Send alert
        await self.send_alert(
            "OpenAI API Connection Failed",
            f"Call {call_id}: Switched to pre-recorded responses. Error: {error_details}"
        )
        
        print(f"⚠️  OpenAI connection failed for call {call_id}")
        print(f"🔄 Switched to pre-recorded response mode")
        
        return {
            "mode": "pre_recorded_responses",
            "message": "I'm experiencing technical difficulties. Let me help you with our automated menu.",
            "options": self.get_pre_recorded_menu()
        }
    
    def get_pre_recorded_menu(self) -> List[Dict[str, str]]:
        """
        Get pre-recorded response menu options.
        
        Returns:
            List of menu options
            
        Requirement 14.1: Pre-recorded response tree
        """
        return [
            {
                "option": "1",
                "text": "Press 1 for sales inquiries",
                "action": "transfer_to_sales"
            },
            {
                "option": "2",
                "text": "Press 2 for support",
                "action": "transfer_to_support"
            },
            {
                "option": "3",
                "text": "Press 3 to leave a message",
                "action": "record_voicemail"
            },
            {
                "option": "0",
                "text": "Press 0 to speak with an operator",
                "action": "transfer_to_operator"
            }
        ]
    
    async def handle_speech_recognition_failure(
        self,
        call_id: str,
        caller_phone: str
    ) -> Dict[str, Any]:
        """
        Handle speech recognition failure.
        
        Tracks consecutive failures and offers transfer or message after 3 attempts.
        
        Args:
            call_id: Unique call identifier
            caller_phone: Caller's phone number
            
        Returns:
            Recovery action details
            
        Requirement 14.2: Offer transfer or message after 3 failures
        """
        # Increment failure count
        if call_id not in self.speech_failure_count:
            self.speech_failure_count[call_id] = 0
        
        self.speech_failure_count[call_id] += 1
        failure_count = self.speech_failure_count[call_id]
        
        # Log error
        await self.log_error(
            error_type=ErrorType.SPEECH_RECOGNITION_FAILURE,
            call_id=call_id,
            error_details=f"Speech recognition failure #{failure_count}",
            recovery_action="retry" if failure_count < self.max_speech_failures else "offer_transfer_or_message"
        )
        
        if failure_count < self.max_speech_failures:
            # Retry
            return {
                "action": "retry",
                "message": "I'm sorry, I didn't catch that. Could you please repeat?",
                "attempts_remaining": self.max_speech_failures - failure_count
            }
        else:
            # Offer transfer or message
            print(f"⚠️  Speech recognition failed {failure_count} times for call {call_id}")
            print(f"🔄 Offering transfer to human agent or voicemail")
            
            return {
                "action": "offer_options",
                "message": "I'm having trouble understanding. Would you like to speak with a human agent or leave a message?",
                "options": [
                    {"option": "agent", "text": "Transfer to agent"},
                    {"option": "message", "text": "Leave a message"}
                ]
            }
    
    def reset_speech_failure_count(self, call_id: str) -> None:
        """Reset speech failure count for a call."""
        if call_id in self.speech_failure_count:
            del self.speech_failure_count[call_id]
    
    async def handle_system_failure(
        self,
        call_id: str,
        caller_phone: str,
        error_details: str
    ) -> Dict[str, Any]:
        """
        Handle complete system failure.
        
        Records voicemail and sends alert to business owner.
        
        Args:
            call_id: Unique call identifier
            caller_phone: Caller's phone number
            error_details: Error description
            
        Returns:
            Recovery action details
            
        Requirement 14.3: Record voicemail and alert on system failure
        """
        # Log error
        await self.log_error(
            error_type=ErrorType.SYSTEM_FAILURE,
            call_id=call_id,
            error_details=error_details,
            recovery_action="record_voicemail_and_alert"
        )
        
        # Switch to voicemail-only mode
        self.current_mode = FallbackMode.VOICEMAIL_ONLY
        
        # Record voicemail
        voicemail_recorded = await self.record_voicemail(call_id, caller_phone)
        
        # Send alert to business owner
        await self.send_alert(
            "Critical System Failure",
            f"Call {call_id} from {caller_phone}: All systems failed. Voicemail recorded: {voicemail_recorded}. Error: {error_details}"
        )
        
        print(f"🚨 Critical system failure for call {call_id}")
        print(f"📧 Alert sent to business owner")
        
        return {
            "action": "voicemail",
            "message": "We're experiencing technical difficulties. Please leave a message and we'll call you back as soon as possible.",
            "voicemail_recorded": voicemail_recorded
        }
    
    async def record_voicemail(
        self,
        call_id: str,
        caller_phone: str
    ) -> bool:
        """
        Record voicemail for the caller.
        
        Args:
            call_id: Unique call identifier
            caller_phone: Caller's phone number
            
        Returns:
            True if voicemail recorded successfully
        """
        if self.voicemail_callback:
            try:
                await self.voicemail_callback(call_id, caller_phone)
                print(f"📼 Voicemail recording started for call {call_id}")
                return True
            except Exception as e:
                print(f"⚠️  Error starting voicemail recording: {e}")
                return False
        else:
            # Log voicemail request
            print(f"📼 Voicemail requested for call {call_id} from {caller_phone}")
            return True
    
    async def send_alert(self, subject: str, message: str) -> None:
        """
        Send alert to business owner.
        
        Args:
            subject: Alert subject
            message: Alert message
        """
        if self.alert_callback:
            try:
                await self.alert_callback(subject, message)
                print(f"📧 Alert sent: {subject}")
            except Exception as e:
                print(f"⚠️  Error sending alert: {e}")
        else:
            # Log alert
            print(f"📧 Alert: {subject}")
            print(f"   {message}")
    
    async def log_error(
        self,
        error_type: ErrorType,
        call_id: str,
        error_details: str,
        recovery_action: str
    ) -> None:
        """
        Log error with context.
        
        Args:
            error_type: Type of error
            call_id: Unique call identifier
            error_details: Error description
            recovery_action: Action taken to recover
            
        Requirement 14.4: Log all errors with context
        """
        error_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_type": error_type.value,
            "call_id": call_id,
            "error_details": error_details,
            "recovery_action": recovery_action
        }
        
        self.error_log.append(error_entry)
        
        # In production, would write to database or logging service
        print(f"📝 Error logged: {error_type.value} for call {call_id}")
    
    def get_error_log(self) -> List[Dict[str, Any]]:
        """Get complete error log."""
        return self.error_log.copy()
    
    async def check_service_restoration(self) -> bool:
        """
        Check if service has been restored.
        
        Returns:
            True if service is restored
            
        Requirement 14.5: Detect service restoration
        """
        # In production, would ping OpenAI API or check health endpoints
        # For now, simulate check
        return True
    
    async def resume_normal_operation(self) -> Dict[str, Any]:
        """
        Resume normal operation after service restoration.
        
        Returns:
            Status details
            
        Requirement 14.5: Resume normal operation automatically
        """
        previous_mode = self.current_mode
        self.current_mode = FallbackMode.NORMAL
        
        print(f"✅ Service restored - resuming normal operation")
        print(f"   Previous mode: {previous_mode.value}")
        
        return {
            "status": "restored",
            "previous_mode": previous_mode.value,
            "current_mode": self.current_mode.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get error statistics.
        
        Returns:
            Error statistics dictionary
        """
        error_counts = {}
        for error in self.error_log:
            error_type = error["error_type"]
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_log),
            "error_counts": error_counts,
            "current_mode": self.current_mode.value,
            "active_speech_failures": len(self.speech_failure_count)
        }
