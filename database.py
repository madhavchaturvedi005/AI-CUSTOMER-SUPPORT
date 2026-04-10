"""Database service for PostgreSQL connection and operations."""

import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import asyncpg
from asyncpg.pool import Pool


class DatabaseService:
    """Manages PostgreSQL connections and database operations."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "voice_automation",
        user: str = "postgres",
        password: Optional[str] = None,
        sslmode: Optional[str] = None,
        min_size: int = 10,
        max_size: int = 50
    ):
        """
        Initialize database service with connection pooling.
        
        Args:
            host: PostgreSQL server host
            port: PostgreSQL server port
            database: Database name
            user: Database user
            password: Database password
            sslmode: SSL mode (disable, allow, prefer, require, verify-ca, verify-full)
            min_size: Minimum number of connections in pool
            max_size: Maximum number of connections in pool
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.sslmode = sslmode
        self.min_size = min_size
        self.max_size = max_size
        self._pool: Optional[Pool] = None
    
    async def connect(self) -> None:
        """Establish database connection pool."""
        # Build connection parameters
        conn_params = {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password,
            'min_size': self.min_size,
            'max_size': self.max_size
        }
        
        # Add SSL if specified
        if self.sslmode:
            conn_params['ssl'] = self.sslmode
        
        self._pool = await asyncpg.create_pool(**conn_params)
    
    async def disconnect(self) -> None:
        """Close database connection pool."""
        if self._pool:
            await self._pool.close()
    
    @property
    def pool(self) -> Pool:
        """Get database connection pool."""
        if not self._pool:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._pool
    
    # Call operations
    
    async def create_call(
        self,
        call_sid: str,
        caller_phone: str,
        direction: str = "inbound",
        status: str = "initiated",
        caller_name: Optional[str] = None,
        language: str = "en",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new call record.
        
        Args:
            call_sid: Twilio call SID
            caller_phone: Caller's phone number
            direction: Call direction (inbound/outbound)
            status: Initial call status
            caller_name: Caller's name (optional)
            language: Call language
            metadata: Additional metadata
            
        Returns:
            Call UUID
        """
        query = """
            INSERT INTO calls (
                call_sid, caller_phone, direction, status, caller_name, 
                language, metadata, started_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            # Convert timezone-aware datetime to naive UTC for TIMESTAMP column
            started_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            call_id = await conn.fetchval(
                query,
                call_sid,
                caller_phone,
                direction,
                status,
                caller_name,
                language,
                json.dumps(metadata or {}),
                started_at
            )
            print(f"✅ Call created in database: {call_id} (SID: {call_sid})")
            return str(call_id)
    
    async def update_call_status(
        self,
        call_id: str,
        status: str,
        ended_at: Optional[datetime] = None,
        duration_seconds: Optional[int] = None
    ) -> bool:
        """
        Update call status and completion details.
        
        Args:
            call_id: Call UUID
            status: New status
            ended_at: Call end timestamp
            duration_seconds: Call duration
            
        Returns:
            True if updated successfully
        """
        # Ensure ended_at is naive UTC for TIMESTAMP column
        if ended_at and ended_at.tzinfo is not None:
            # Convert timezone-aware to naive UTC
            ended_at = ended_at.astimezone(timezone.utc).replace(tzinfo=None)
        elif ended_at and ended_at.tzinfo is None:
            # Already naive, assume it's UTC
            pass
        
        query = """
            UPDATE calls
            SET status = $2, ended_at = $3, duration_seconds = $4
            WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                query,
                call_id,
                status,
                ended_at,
                duration_seconds
            )
            return result == "UPDATE 1"
    
    async def update_call_intent(
        self,
        call_id: str,
        intent: str,
        intent_confidence: float
    ) -> bool:
        """
        Update call intent and confidence.
        
        Args:
            call_id: Call UUID
            intent: Detected intent
            intent_confidence: Confidence score (0.0-1.0)
            
        Returns:
            True if updated successfully
        """
        query = """
            UPDATE calls
            SET intent = $2, intent_confidence = $3
            WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                query,
                call_id,
                intent,
                intent_confidence
            )
            return result == "UPDATE 1"
    
    async def update_call_language(
        self,
        call_id: str,
        language: str
    ) -> bool:
        """
        Update call language.
        
        Args:
            call_id: Call UUID
            language: Language code (e.g., 'en', 'hi', 'ta')
            
        Returns:
            True if updated successfully
        """
        query = """
            UPDATE calls
            SET language = $2
            WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                query,
                call_id,
                language
            )
            return result == "UPDATE 1"
    
    async def update_call_recording(
        self,
        call_id: str,
        recording_url: str,
        transcript_url: Optional[str] = None
    ) -> bool:
        """
        Update call recording and transcript URLs.
        
        Args:
            call_id: Call UUID
            recording_url: URL to call recording
            transcript_url: URL to transcript (optional)
            
        Returns:
            True if updated successfully
        """
        query = """
            UPDATE calls
            SET recording_url = $2, transcript_url = $3
            WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                query,
                call_id,
                recording_url,
                transcript_url
            )
            return result == "UPDATE 1"
    
    async def save_transcript(
        self,
        call_id: str,
        speaker: str,
        text: str,
        timestamp_ms: int,
        language: str = "en",
        confidence: float = 1.0
    ) -> bool:
        """
        Save a conversation transcript turn to the database.
        
        Args:
            call_id: Call UUID
            speaker: Speaker identifier (caller/customer/assistant/agent)
            text: Transcript text
            timestamp_ms: Timestamp in milliseconds
            language: Language code
            confidence: Confidence score (0.0-1.0)
            
        Returns:
            True if saved successfully
        """
        query = """
            INSERT INTO transcripts (
                call_id, speaker, text, timestamp_ms, language, confidence
            )
            VALUES ($1, $2, $3, $4, $5, $6)
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                call_id,
                speaker,
                text,
                timestamp_ms,
                language,
                confidence
            )
            return True
    
    async def get_call(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve call record by ID.
        
        Args:
            call_id: Call UUID
            
        Returns:
            Call record as dictionary or None if not found
        """
        query = """
            SELECT * FROM calls WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, call_id)
            return dict(row) if row else None
    
    async def get_call_by_sid(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve call record by Twilio call SID.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            Call record as dictionary or None if not found
        """
        from datetime import timezone
        
        query = """
            SELECT * FROM calls WHERE call_sid = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, call_sid)
            if not row:
                return None
            
            # Convert to dict and ensure timestamps are timezone-aware
            result = dict(row)
            if result.get('started_at') and result['started_at'].tzinfo is None:
                result['started_at'] = result['started_at'].replace(tzinfo=timezone.utc)
            if result.get('ended_at') and result['ended_at'].tzinfo is None:
                result['ended_at'] = result['ended_at'].replace(tzinfo=timezone.utc)
            
            return result
    
    async def get_caller_history(
        self,
        caller_phone: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve call history for a caller.
        
        Args:
            caller_phone: Caller's phone number
            limit: Maximum number of records to return
            
        Returns:
            List of call records
        """
        query = """
            SELECT * FROM calls
            WHERE caller_phone = $1
            ORDER BY started_at DESC
            LIMIT $2
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, caller_phone, limit)
            return [dict(row) for row in rows]
    
    async def get_recent_caller_history(
        self,
        caller_phone: str,
        days: int = 30,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent call history for a caller within specified days.
        
        Args:
            caller_phone: Caller's phone number
            days: Number of days to look back (default: 30)
            limit: Maximum number of records to return (default: 5)
            
        Returns:
            List of call records from the last N days
        """
        query = """
            SELECT * FROM calls
            WHERE caller_phone = $1
            AND started_at >= NOW() - INTERVAL '%s days'
            AND status = 'completed'
            ORDER BY started_at DESC
            LIMIT $2
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query % days, caller_phone, limit)
            return [dict(row) for row in rows]
    
    async def get_call_transcripts(
        self,
        call_id: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation transcripts for a specific call.
        
        Args:
            call_id: Call UUID
            
        Returns:
            List of transcript entries ordered by timestamp
        """
        query = """
            SELECT speaker, text, timestamp_ms, language, confidence
            FROM transcripts
            WHERE call_id = $1
            ORDER BY timestamp_ms ASC
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, call_id)
            return [dict(row) for row in rows]
    
    # Business configuration operations
    
    async def get_business_config(
        self,
        business_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve business configuration.
        
        Args:
            business_id: Business identifier
            
        Returns:
            Business configuration as dictionary or None if not found
        """
        query = """
            SELECT * FROM business_config
            WHERE business_id = $1 AND active = TRUE
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, business_id)
            return dict(row) if row else None
    
    async def create_lead(
        self,
        call_id: str,
        name: str,
        phone: str,
        email: Optional[str] = None,
        inquiry_details: str = "",
        budget_indication: Optional[str] = None,
        timeline: Optional[str] = None,
        decision_authority: bool = False,
        lead_score: int = 0,
        source: str = "voice_call"
    ) -> str:
        """
        Create a new lead record in the database.
        
        Args:
            call_id: Associated call ID
            name: Lead's name
            phone: Lead's phone number
            email: Lead's email address (optional)
            inquiry_details: Details of the inquiry
            budget_indication: Budget indication (low/medium/high)
            timeline: Timeline for purchase (immediate/short-term/long-term)
            decision_authority: Whether lead has decision authority
            lead_score: Lead score from 1-10
            source: Lead source (default: voice_call)
            
        Returns:
            Lead ID (UUID)
            
        Requirement 5.4: Store lead information in structured format
        """
        query = """
            INSERT INTO leads (
                call_id, name, phone, email, inquiry_details,
                budget_indication, timeline, decision_authority,
                lead_score, source, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            # Convert timezone-aware datetime to naive UTC for TIMESTAMP column
            created_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            lead_id = await conn.fetchval(
                query,
                call_id, name, phone, email, inquiry_details,
                budget_indication, timeline, decision_authority,
                lead_score, source, created_at
            )
            return str(lead_id)
    
    async def create_appointment(
        self,
        call_id: Optional[str],
        customer_name: str,
        customer_phone: str,
        customer_email: Optional[str],
        service_type: str,
        appointment_datetime: datetime,
        duration_minutes: int,
        notes: Optional[str],
        status: str = "scheduled"
    ) -> str:
        """
        Create a new appointment record in the database.
        
        Args:
            call_id: Associated call ID (optional)
            customer_name: Customer's name
            customer_phone: Customer's phone number
            customer_email: Customer's email address (optional)
            service_type: Type of service
            appointment_datetime: Scheduled date and time
            duration_minutes: Duration in minutes
            notes: Additional notes (optional)
            status: Appointment status (default: scheduled)
            
        Returns:
            Appointment ID (UUID)
            
        Requirement 6.4: Create calendar entry
        """
        # Convert timezone-aware datetime to naive UTC for TIMESTAMP column
        # (Database uses TIMESTAMP not TIMESTAMPTZ)
        if appointment_datetime and appointment_datetime.tzinfo is not None:
            appointment_datetime = appointment_datetime.astimezone(timezone.utc).replace(tzinfo=None)
        
        query = """
            INSERT INTO appointments (
                call_id, customer_name, customer_phone, customer_email,
                service_type, appointment_datetime, duration_minutes,
                notes, status, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            appointment_id = await conn.fetchval(
                query,
                call_id, customer_name, customer_phone, customer_email,
                service_type, appointment_datetime, duration_minutes,
                notes, status, datetime.utcnow()  # Use naive datetime for TIMESTAMP column
            )
            return str(appointment_id)
    
    async def create_transcript(
        self,
        call_id: str,
        transcript_text: str,
        caller_id: str,
        intent: Optional[str],
        outcome: Optional[str],
        recording_url: Optional[str],
        created_at: datetime
    ) -> str:
        """
        Create a new transcript record in the database.
        
        Args:
            call_id: Associated call ID
            transcript_text: Complete transcript text
            caller_id: Caller's phone number or ID
            intent: Detected intent
            outcome: Call outcome
            recording_url: URL to audio recording
            created_at: Timestamp
            
        Returns:
            Transcript ID (UUID)
            
        Requirement 8.3, 8.4: Store transcript with metadata
        """
        query = """
            INSERT INTO transcripts (
                call_id, transcript_text, caller_id, intent,
                outcome, recording_url, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            transcript_id = await conn.fetchval(
                query,
                call_id, transcript_text, caller_id, intent,
                outcome, recording_url, created_at
            )
            return str(transcript_id)


# Global database service instance
_database_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """
    Get the global database service instance.
    
    Returns:
        DatabaseService instance
        
    Raises:
        RuntimeError: If database service not initialized
    """
    global _database_service
    if not _database_service:
        raise RuntimeError("Database service not initialized. Call initialize_database() first.")
    return _database_service


async def initialize_database(
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    sslmode: Optional[str] = None
) -> DatabaseService:
    """
    Initialize the global database service instance.
    
    Args:
        host: PostgreSQL host (defaults to DB_HOST env var or localhost)
        port: PostgreSQL port (defaults to DB_PORT env var or 5432)
        database: Database name (defaults to DB_NAME env var or voice_automation)
        user: Database user (defaults to DB_USER env var or postgres)
        password: Database password (defaults to DB_PASSWORD env var)
        sslmode: SSL mode (defaults to DB_SSLMODE env var)
        
    Returns:
        Initialized DatabaseService instance
    """
    global _database_service
    
    # Get configuration from environment variables if not provided
    host = host or os.getenv("DB_HOST", "localhost")
    port = port or int(os.getenv("DB_PORT", "5432"))
    database = database or os.getenv("DB_NAME", "voice_automation")
    user = user or os.getenv("DB_USER", "postgres")
    password = password or os.getenv("DB_PASSWORD")
    sslmode = sslmode or os.getenv("DB_SSLMODE")
    
    _database_service = DatabaseService(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        sslmode=sslmode
    )
    
    await _database_service.connect()
    return _database_service


async def shutdown_database() -> None:
    """Shutdown the global database service instance."""
    global _database_service
    if _database_service:
        await _database_service.disconnect()
        _database_service = None
