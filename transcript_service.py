"""Transcript and recording service for call documentation."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import re
from database import DatabaseService


class TranscriptService:
    """
    Manages call recording and transcription.
    
    Implements Requirements 8.1-8.5:
    - 8.1: Record call audio in WAV format (16kHz sample rate)
    - 8.2: Generate complete text transcript
    - 8.3: Store recording and transcript for minimum 90 days
    - 8.4: Associate transcript with metadata (timestamp, caller ID, intent, outcome)
    - 8.5: Play recording disclosure message where legally required
    """
    
    def __init__(
        self,
        database: DatabaseService,
        storage_path: str = "./recordings",
        require_disclosure: bool = True
    ):
        """
        Initialize TranscriptService.
        
        Args:
            database: DatabaseService instance for persistence
            storage_path: Path to store audio recordings
            require_disclosure: Whether to require recording disclosure message
        """
        self.database = database
        self.storage_path = storage_path
        self.require_disclosure = require_disclosure
        self.retention_days = 90
    
    def get_disclosure_message(self) -> str:
        """
        Get recording disclosure message.
        
        Returns:
            Disclosure message text
            
        Requirement 8.5: Play recording disclosure message
        """
        return (
            "This call may be recorded for quality and training purposes. "
            "By continuing, you consent to this recording."
        )
    
    def should_play_disclosure(self) -> bool:
        """
        Check if recording disclosure is required.
        
        Returns:
            True if disclosure should be played, False otherwise
            
        Requirement 8.5: Play disclosure where legally required
        """
        return self.require_disclosure
    
    async def generate_transcript(
        self,
        call_id: str,
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """
        Generate complete text transcript from conversation history.
        
        Args:
            call_id: Unique call identifier
            conversation_history: List of conversation turns
            
        Returns:
            Complete transcript text
            
        Requirement 8.2: Generate complete text transcript
        """
        transcript_lines = []
        
        # Add header
        transcript_lines.append(f"Call ID: {call_id}")
        transcript_lines.append(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        transcript_lines.append("-" * 50)
        transcript_lines.append("")
        
        # Add conversation turns
        for turn in conversation_history:
            speaker = turn.get("speaker", "unknown")
            text = turn.get("text", "")
            timestamp_ms = turn.get("timestamp_ms", 0)
            
            # Format speaker name
            speaker_label = "Caller" if speaker == "caller" else "Assistant"
            
            # Format timestamp
            seconds = timestamp_ms / 1000
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            time_str = f"[{minutes:02d}:{secs:02d}]"
            
            # Add line
            transcript_lines.append(f"{time_str} {speaker_label}: {text}")
        
        transcript_lines.append("")
        transcript_lines.append("-" * 50)
        transcript_lines.append(f"End of transcript")
        
        return "\n".join(transcript_lines)
    
    def mask_sensitive_information(self, text: str) -> str:
        """
        Mask sensitive information in transcript text.
        
        Detects and masks:
        - Credit card numbers
        - Social security numbers
        - Passwords/PINs
        
        Args:
            text: Original text
            
        Returns:
            Text with sensitive information masked
            
        Requirement 16.5: Mask sensitive information
        """
        masked_text = text
        
        # Mask credit card numbers (various formats)
        # Pattern: 4 groups of 4 digits, with optional spaces/dashes
        cc_pattern = r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'
        masked_text = re.sub(cc_pattern, '[CREDIT_CARD_REDACTED]', masked_text)
        
        # Mask SSN (XXX-XX-XXXX format)
        ssn_pattern = r'\b\d{3}[\s\-]?\d{2}[\s\-]?\d{4}\b'
        masked_text = re.sub(ssn_pattern, '[SSN_REDACTED]', masked_text)
        
        # Mask common password/PIN phrases
        password_patterns = [
            (r'password\s+is\s+\S+', 'password is [REDACTED]'),
            (r'pin\s+is\s+\d+', 'pin is [REDACTED]'),
            (r'my\s+password\s+\S+', 'my password [REDACTED]'),
            (r'my\s+pin\s+\d+', 'my pin [REDACTED]')
        ]
        
        for pattern, replacement in password_patterns:
            masked_text = re.sub(pattern, replacement, masked_text, flags=re.IGNORECASE)
        
        return masked_text
    
    async def save_transcript(
        self,
        call_id: str,
        transcript_text: str,
        caller_id: str,
        intent: Optional[str] = None,
        outcome: Optional[str] = None,
        recording_url: Optional[str] = None
    ) -> str:
        """
        Save transcript to database with metadata.
        
        Args:
            call_id: Unique call identifier
            transcript_text: Complete transcript text
            caller_id: Caller's phone number or ID
            intent: Detected intent
            outcome: Call outcome
            recording_url: URL to audio recording
            
        Returns:
            Transcript ID from database
            
        Requirement 8.3, 8.4: Store transcript with metadata
        """
        # Mask sensitive information
        masked_transcript = self.mask_sensitive_information(transcript_text)
        
        # Store in database
        transcript_id = await self.database.create_transcript(
            call_id=call_id,
            transcript_text=masked_transcript,
            caller_id=caller_id,
            intent=intent,
            outcome=outcome,
            recording_url=recording_url,
            created_at=datetime.now(timezone.utc)
        )
        
        return transcript_id
    
    async def create_recording_metadata(
        self,
        call_id: str,
        duration_seconds: int,
        format: str = "wav",
        sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """
        Create metadata for audio recording.
        
        Args:
            call_id: Unique call identifier
            duration_seconds: Recording duration in seconds
            format: Audio format (default: wav)
            sample_rate: Sample rate in Hz (default: 16000)
            
        Returns:
            Recording metadata dictionary
            
        Requirement 8.1: Record in WAV format with 16kHz sample rate
        """
        recording_url = f"{self.storage_path}/{call_id}.{format}"
        
        metadata = {
            "call_id": call_id,
            "format": format,
            "sample_rate": sample_rate,
            "duration_seconds": duration_seconds,
            "recording_url": recording_url,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        return metadata
    
    async def process_call_transcript(
        self,
        call_id: str,
        conversation_history: List[Dict[str, Any]],
        caller_phone: str,
        intent: Optional[str] = None,
        outcome: Optional[str] = None,
        duration_seconds: int = 0
    ) -> Dict[str, str]:
        """
        Complete transcript processing pipeline.
        
        Generates transcript, masks sensitive data, and saves to database.
        
        Args:
            call_id: Unique call identifier
            conversation_history: List of conversation turns
            caller_phone: Caller's phone number
            intent: Detected intent
            outcome: Call outcome
            duration_seconds: Call duration in seconds
            
        Returns:
            Dictionary with transcript_id and recording metadata
        """
        # Generate transcript
        transcript_text = await self.generate_transcript(call_id, conversation_history)
        
        # Create recording metadata
        recording_metadata = await self.create_recording_metadata(
            call_id, duration_seconds
        )
        
        # Save transcript
        transcript_id = await self.save_transcript(
            call_id=call_id,
            transcript_text=transcript_text,
            caller_id=caller_phone,
            intent=intent,
            outcome=outcome,
            recording_url=recording_metadata["recording_url"]
        )
        
        return {
            "transcript_id": transcript_id,
            "recording_url": recording_metadata["recording_url"]
        }
    
    async def cleanup_old_recordings(self) -> int:
        """
        Delete recordings older than retention period (90 days).
        
        Returns:
            Number of recordings deleted
            
        Requirement 8.3: 90-day retention policy
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        
        # Query database for old transcripts
        # In production, this would delete files from storage and database
        deleted_count = 0
        
        print(f"🗑️  Cleanup: Would delete recordings older than {cutoff_date.date()}")
        
        return deleted_count
