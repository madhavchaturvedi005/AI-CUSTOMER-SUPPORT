"""Call Manager for managing call lifecycle and state."""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from models import CallStatus, CallContext, Intent, Language
from database import DatabaseService
from redis_service import RedisService
from language_manager import LanguageManager


class CallManager:
    """
    Manages the complete call lifecycle with database and cache integration.
    
    Responsibilities:
    - Call initiation and answer logic
    - Call state transitions (initiated → in_progress → completed)
    - Call termination and cleanup
    - Integration with PostgreSQL for persistence
    - Integration with Redis for session caching
    
    Requirements: 1.1, 1.2, 1.4, 1.5, 18.1
    """
    
    def __init__(
        self,
        database: DatabaseService,
        redis: RedisService,
        language_manager: Optional[LanguageManager] = None
    ):
        """
        Initialize CallManager with database and Redis services.
        
        Args:
            database: DatabaseService instance for persistence
            redis: RedisService instance for caching
            language_manager: LanguageManager instance for multi-language support
        """
        self.database = database
        self.redis = redis
        self.language_manager = language_manager or LanguageManager()
    
    async def initiate_call(
        self,
        call_sid: str,
        caller_phone: str,
        direction: str = "inbound",
        caller_name: Optional[str] = None,
        language: Language = Language.ENGLISH,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CallContext:
        """
        Initiate a new call and create initial context.
        
        This method:
        1. Creates a call record in PostgreSQL with status 'initiated'
        2. Creates a CallContext object
        3. Caches the call context in Redis
        
        Args:
            call_sid: Twilio call SID
            caller_phone: Caller's phone number
            direction: Call direction (inbound/outbound)
            caller_name: Caller's name (optional)
            language: Call language
            metadata: Additional metadata
            
        Returns:
            CallContext object for the new call
            
        Requirements: 1.1, 1.4
        """
        # Create call record in database
        call_id = await self.database.create_call(
            call_sid=call_sid,
            caller_phone=caller_phone,
            direction=direction,
            status=CallStatus.INITIATED.value,
            caller_name=caller_name,
            language=language.value,
            metadata=metadata
        )
        
        # Create call context
        context = CallContext(
            call_id=call_id,
            caller_phone=caller_phone,
            caller_name=caller_name,
            language=language,
            metadata=metadata or {}
        )
        
        # Cache context in Redis
        await self._cache_call_context(call_sid, context)
        
        # Add to caller history
        await self.redis.add_caller_history(caller_phone, call_id)
        
        return context
    
    async def answer_call(
        self,
        call_sid: str
    ) -> bool:
        """
        Mark call as answered and transition to in_progress state.
        
        This method transitions the call from 'initiated' to 'in_progress'.
        Should be called within 3 seconds of receiving the call (Requirement 1.1).
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            True if successful
            
        Requirements: 1.1, 1.2
        """
        # Get call context from cache
        context = await self.get_call_context(call_sid)
        if not context:
            raise ValueError(f"Call context not found for call_sid: {call_sid}")
        
        # Update status in database
        await self.database.update_call_status(
            call_id=context.call_id,
            status=CallStatus.IN_PROGRESS.value
        )
        
        # Update cached context
        context.metadata["status"] = CallStatus.IN_PROGRESS.value
        context.metadata["answered_at"] = datetime.now(timezone.utc).isoformat()
        await self._cache_call_context(call_sid, context)
        
        return True
    
    async def get_greeting_message(
        self,
        business_id: str = "default"
    ) -> str:
        """
        Retrieve business-specific greeting message from configuration.
        
        This method retrieves the greeting message from the business_config table.
        If no custom greeting is configured, returns a default greeting.
        
        Args:
            business_id: Business identifier (defaults to "default")
            
        Returns:
            Greeting message text
            
        Requirements: 1.2, 17.1
        """
        # Try to get business configuration
        config = await self.database.get_business_config(business_id)
        
        # Return custom greeting if configured
        if config and config.get("greeting_message"):
            return config["greeting_message"]
        
        # Return default greeting
        return (
            "Hello! Thank you for calling. I'm an AI assistant here to help you. "
            "How can I assist you today?"
        )
    
    async def update_call_intent(
        self,
        call_sid: str,
        intent: Intent,
        confidence: float
    ) -> bool:
        """
        Update call intent and confidence score.
        
        Args:
            call_sid: Twilio call SID
            intent: Detected intent
            confidence: Confidence score (0.0-1.0)
            
        Returns:
            True if successful
            
        Requirements: 3.1, 3.3
        """
        # Get call context
        context = await self.get_call_context(call_sid)
        if not context:
            raise ValueError(f"Call context not found for call_sid: {call_sid}")
        
        # Update context
        context.intent = intent
        context.intent_confidence = confidence
        
        # Update database
        await self.database.update_call_intent(
            call_id=context.call_id,
            intent=intent.value,
            intent_confidence=confidence
        )
        
        # Update cache
        await self._cache_call_context(call_sid, context)
        
        return True
    
    async def handle_intent_with_clarification(
        self,
        call_sid: str,
        intent_detector,
        conversation_history: list[Dict[str, Any]],
        current_transcript: str
    ) -> tuple[Intent, float, Optional[str]]:
        """
        Detect intent and request clarification if confidence is low.
        
        This method implements the clarification flow:
        1. Detects intent using the intent detector
        2. Checks if confidence is below 0.7 threshold
        3. If low confidence, generates a clarification question
        4. Returns intent, confidence, and optional clarification question
        
        Args:
            call_sid: Twilio call SID
            intent_detector: IntentDetectorInterface implementation
            conversation_history: List of previous conversation turns
            current_transcript: Current conversation text
            
        Returns:
            Tuple of (intent, confidence, clarification_question)
            clarification_question is None if confidence >= 0.7
            
        Requirements: 3.1, 3.3, 3.4
        """
        # Detect intent
        intent, confidence = await intent_detector.detect_intent(
            conversation_history,
            current_transcript
        )
        
        # Update call intent
        await self.update_call_intent(call_sid, intent, confidence)
        
        # Check if clarification is needed (confidence < 0.7)
        clarification_question = None
        if confidence < 0.7:
            clarification_question = await intent_detector.request_clarification(
                intent,
                confidence
            )
            
            # Mark that clarification was requested in metadata
            context = await self.get_call_context(call_sid)
            if context:
                context.metadata["clarification_requested"] = True
                context.metadata["clarification_question"] = clarification_question
                await self._cache_call_context(call_sid, context)
        
        return (intent, confidence, clarification_question)
    
    async def update_intent_after_clarification(
        self,
        call_sid: str,
        intent_detector,
        clarification_response: str
    ) -> tuple[Intent, float]:
        """
        Re-detect intent after receiving clarification response.
        
        This method is called after the caller responds to a clarification question.
        It re-analyzes the conversation including the clarification response to
        update the intent with improved confidence.
        
        Args:
            call_sid: Twilio call SID
            intent_detector: IntentDetectorInterface implementation
            clarification_response: Caller's response to clarification question
            
        Returns:
            Tuple of (updated_intent, updated_confidence)
            
        Requirements: 3.4
        """
        # Get call context
        context = await self.get_call_context(call_sid)
        if not context:
            raise ValueError(f"Call context not found for call_sid: {call_sid}")
        
        # Add clarification response to conversation history
        await self.add_conversation_turn(
            call_sid,
            "caller",
            clarification_response
        )
        
        # Re-detect intent with updated conversation
        context = await self.get_call_context(call_sid)
        intent, confidence = await intent_detector.detect_intent(
            context.conversation_history,
            clarification_response
        )
        
        # Update call intent
        await self.update_call_intent(call_sid, intent, confidence)
        
        # Mark that clarification was resolved
        context.metadata["clarification_resolved"] = True
        context.metadata["clarification_response"] = clarification_response
        await self._cache_call_context(call_sid, context)
        
        return (intent, confidence)
    
    async def detect_and_update_language(
        self,
        call_sid: str,
        openai_ws,
        elapsed_time_ms: int
    ) -> tuple[Optional[Language], float]:
        """
        Detect caller's language and update session if needed.
        
        This method should be called periodically during the first 10 seconds
        of the call to detect the caller's language. If a language is detected
        with high confidence, it automatically updates the OpenAI session.
        
        Args:
            call_sid: Twilio call SID
            openai_ws: WebSocket connection to OpenAI
            elapsed_time_ms: Time elapsed since call start (milliseconds)
            
        Returns:
            Tuple of (detected_language, confidence_score)
            
        Requirements: 13.1, 13.2, 13.4
        """
        # Get call context
        context = await self.get_call_context(call_sid)
        if not context:
            raise ValueError(f"Call context not found for call_sid: {call_sid}")
        
        # Detect language from conversation history
        detected_language, confidence = await self.language_manager.detect_language(
            openai_ws,
            context.conversation_history,
            elapsed_time_ms
        )
        
        if detected_language is None:
            return (None, 0.0)
        
        # Check if we should request language selection
        should_request = await self.language_manager.should_request_language_selection(
            detected_language,
            confidence
        )
        
        if should_request:
            # Low confidence - mark that we need to ask for language selection
            context.metadata["language_detection_confidence"] = confidence
            context.metadata["needs_language_selection"] = True
            await self._cache_call_context(call_sid, context)
            return (detected_language, confidence)
        
        # High confidence - automatically update language
        if detected_language != context.language:
            success = await self.language_manager.update_session_language(
                openai_ws,
                detected_language,
                preserve_context=True
            )
            
            if success:
                # Update call context
                context.language = detected_language
                context.metadata["language_detected"] = True
                context.metadata["language_detection_confidence"] = confidence
                context.metadata["language_detection_time"] = datetime.now(timezone.utc).isoformat()
                
                # Update database
                await self.database.update_call_language(
                    call_id=context.call_id,
                    language=detected_language.value
                )
                
                # Update cache
                await self._cache_call_context(call_sid, context)
        
        return (detected_language, confidence)
    
    async def handle_language_switch(
        self,
        call_sid: str,
        openai_ws,
        requested_language: Language
    ) -> bool:
        """
        Handle a mid-conversation language switch request.
        
        This method allows the caller to switch languages during the conversation.
        It updates both the OpenAI session and the call context while preserving
        the conversation history.
        
        Args:
            call_sid: Twilio call SID
            openai_ws: WebSocket connection to OpenAI
            requested_language: Language requested by caller
            
        Returns:
            True if language switch was successful
            
        Requirements: 13.3, 13.5
        """
        # Get call context
        context = await self.get_call_context(call_sid)
        if not context:
            raise ValueError(f"Call context not found for call_sid: {call_sid}")
        
        # Handle language switch
        success = await self.language_manager.handle_language_switch_request(
            openai_ws,
            requested_language,
            context
        )
        
        if success:
            # Update database
            await self.database.update_call_language(
                call_id=context.call_id,
                language=requested_language.value
            )
            
            # Update cache
            await self._cache_call_context(call_sid, context)
        
        return success
    
    async def get_language_selection_prompt(self) -> str:
        """
        Get a multi-language prompt for language selection.
        
        Returns:
            Multi-language prompt text
            
        Requirements: 13.4
        """
        return self.language_manager.get_language_selection_prompt()
    
    async def parse_language_selection(
        self,
        call_sid: str,
        openai_ws,
        caller_response: str
    ) -> tuple[bool, Optional[Language]]:
        """
        Parse and apply language selection from caller's response.
        
        This method parses the caller's language selection response and
        updates the session accordingly.
        
        Args:
            call_sid: Twilio call SID
            openai_ws: WebSocket connection to OpenAI
            caller_response: Caller's response text
            
        Returns:
            Tuple of (success, selected_language)
            
        Requirements: 13.4
        """
        # Parse language from response
        selected_language = self.language_manager.parse_language_from_text(caller_response)
        
        if selected_language is None:
            return (False, None)
        
        # Apply language switch
        success = await self.handle_language_switch(
            call_sid,
            openai_ws,
            selected_language
        )
        
        return (success, selected_language)
    
    async def add_conversation_turn(
        self,
        call_sid: str,
        speaker: str,
        text: str,
        timestamp_ms: Optional[int] = None
    ) -> bool:
        """
        Add a conversation turn to the call context.
        
        Args:
            call_sid: Twilio call SID
            speaker: Speaker identifier (caller/assistant/agent)
            text: Conversation text
            timestamp_ms: Timestamp in milliseconds
            
        Returns:
            True if successful
            
        Requirements: 8.2, 9.1
        """
        context = await self.get_call_context(call_sid)
        if not context:
            raise ValueError(f"Call context not found for call_sid: {call_sid}")
        
        # Add turn to conversation history
        turn = {
            "speaker": speaker,
            "text": text,
            "timestamp_ms": timestamp_ms or int(datetime.now(timezone.utc).timestamp() * 1000)
        }
        context.conversation_history.append(turn)
        
        # Update cache
        await self._cache_call_context(call_sid, context)
        
        return True
    
    async def complete_call(
        self,
        call_sid: str,
        recording_url: Optional[str] = None,
        transcript_url: Optional[str] = None
    ) -> bool:
        """
        Complete a call and perform cleanup.
        
        This method:
        1. Calculates call duration
        2. Updates call status to 'completed'
        3. Saves conversation transcripts to database
        4. Updates recording/transcript URLs if provided
        5. Keeps context in Redis cache (with TTL)
        
        Args:
            call_sid: Twilio call SID
            recording_url: URL to call recording (optional)
            transcript_url: URL to transcript (optional)
            
        Returns:
            True if successful
            
        Requirements: 1.4, 8.3
        """
        # Try to get call context from cache
        print(f"🔍 Attempting to complete call: {call_sid}")
        context = await self.get_call_context(call_sid)
        
        # If context not in cache, get call from database
        if not context:
            print(f"⚠️  Call context not in cache, fetching from database...")
            print(f"   Looking for call_sid: {call_sid}")
            call_record = await self.database.get_call_by_sid(call_sid)
            if not call_record:
                print(f"❌ Call not found in database: {call_sid}")
                print(f"   Skipping completion gracefully.")
                return False  # Don't raise — just exit cleanly
            
            # Calculate duration from database record
            ended_at = datetime.now(timezone.utc)
            started_at = call_record['started_at']
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
            duration_seconds = int((ended_at - started_at).total_seconds())
            
            # Update database
            await self.database.update_call_status(
                call_id=str(call_record['id']),
                status=CallStatus.COMPLETED.value,
                ended_at=ended_at,
                duration_seconds=duration_seconds
            )
            
            print(f"✅ Call completed (no transcripts - context was not cached)")
            return True
        
        # Calculate duration from context
        ended_at = datetime.now(timezone.utc)
        started_at = context.created_at
        # Ensure started_at is timezone-aware
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        duration_seconds = int((ended_at - started_at).total_seconds())
        
        # Update database
        await self.database.update_call_status(
            call_id=context.call_id,
            status=CallStatus.COMPLETED.value,
            ended_at=ended_at,
            duration_seconds=duration_seconds
        )
        
        # Save conversation transcripts to database
        if context.conversation_history:
            print(f"💾 Saving {len(context.conversation_history)} conversation turns to database...")
            for turn in context.conversation_history:
                try:
                    await self.database.save_transcript(
                        call_id=context.call_id,
                        speaker=turn['speaker'],
                        text=turn['text'],
                        timestamp_ms=turn.get('timestamp_ms', 0),
                        language=context.language.value,
                        confidence=1.0  # Default confidence
                    )
                except Exception as e:
                    print(f"⚠️  Error saving transcript turn: {e}")
            print(f"✅ Conversation transcripts saved to database")
        
        # Update recording URLs if provided
        if recording_url:
            await self.database.update_call_recording(
                call_id=context.call_id,
                recording_url=recording_url,
                transcript_url=transcript_url
            )
        
        # Analyze conversation and extract structured data
        if context.conversation_history and len(context.conversation_history) > 0:
            try:
                print(f"🤖 Analyzing conversation with AI...")
                from conversation_analyzer import ConversationAnalyzer
                analyzer = ConversationAnalyzer()
                
                analysis = await analyzer.analyze_conversation(
                    conversation_history=context.conversation_history,
                    caller_phone=context.caller_phone,
                    call_duration_seconds=duration_seconds
                )
                
                # Save appointments
                if analysis.get('appointments'):
                    from appointment_manager import AppointmentManager
                    appt_manager = AppointmentManager(database=self.database)
                    
                    for appt_data in analysis['appointments']:
                        try:
                            # Parse datetime
                            appt_dt_str = appt_data.get('appointment_datetime')
                            if appt_dt_str:
                                from datetime import datetime
                                appt_dt = datetime.fromisoformat(appt_dt_str.replace('Z', '+00:00'))
                                if appt_dt.tzinfo is None:
                                    appt_dt = appt_dt.replace(tzinfo=timezone.utc)
                                
                                # Book appointment
                                _, appt_id = await appt_manager.book_appointment(
                                    call_id=context.call_id,
                                    customer_name=appt_data.get('customer_name', 'Customer'),
                                    customer_phone=appt_data.get('customer_phone', context.caller_phone),
                                    appointment_datetime=appt_dt,
                                    service_type=appt_data.get('service_type', 'General'),
                                    notes=appt_data.get('notes')
                                )
                                print(f"✅ Appointment saved: {appt_id} for {appt_data.get('customer_name')}")
                        except Exception as appt_error:
                            print(f"⚠️  Error saving appointment: {appt_error}")
                
                # Save leads
                if analysis.get('leads'):
                    from lead_manager import LeadManager
                    lead_manager = LeadManager(database=self.database)
                    
                    for lead_data in analysis['leads']:
                        try:
                            lead_id = await lead_manager.capture_lead(
                                call_id=context.call_id,
                                name=lead_data.get('name', 'Customer'),
                                phone=lead_data.get('phone', context.caller_phone),
                                email=lead_data.get('email'),
                                inquiry_details=lead_data.get('inquiry_details', ''),
                                budget_indication=lead_data.get('budget_indication'),
                                timeline=lead_data.get('timeline'),
                                decision_authority=False,
                                lead_score=lead_data.get('lead_score', 5)
                            )
                            print(f"✅ Lead saved: {lead_id} (score: {lead_data.get('lead_score')})")
                        except Exception as lead_error:
                            print(f"⚠️  Error saving lead: {lead_error}")
                
                # Store call insights in metadata
                if analysis.get('call_insights'):
                    insights = analysis['call_insights']
                    context.metadata['ai_insights'] = insights
                    print(f"✅ Call insights: {insights.get('primary_intent')} - {insights.get('sentiment')}")
                
            except Exception as analysis_error:
                print(f"⚠️  Error analyzing conversation: {analysis_error}")
                import traceback
                traceback.print_exc()
        
        # Update cached context
        context.metadata["status"] = CallStatus.COMPLETED.value
        context.metadata["ended_at"] = ended_at.isoformat()
        context.metadata["duration_seconds"] = duration_seconds
        await self._cache_call_context(call_sid, context)
        
        return True
    
    async def fail_call(
        self,
        call_sid: str,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Mark call as failed and perform cleanup.
        
        Args:
            call_sid: Twilio call SID
            error_message: Error message describing the failure
            
        Returns:
            True if successful
            
        Requirements: 14.1, 14.4
        """
        # Get call context
        context = await self.get_call_context(call_sid)
        if not context:
            raise ValueError(f"Call context not found for call_sid: {call_sid}")
        
        # Calculate duration
        ended_at = datetime.now(timezone.utc)
        started_at = context.created_at
        duration_seconds = int((ended_at - started_at).total_seconds())
        
        # Update database
        await self.database.update_call_status(
            call_id=context.call_id,
            status=CallStatus.FAILED.value,
            ended_at=ended_at,
            duration_seconds=duration_seconds
        )
        
        # Update cached context
        context.metadata["status"] = CallStatus.FAILED.value
        context.metadata["ended_at"] = ended_at.isoformat()
        context.metadata["duration_seconds"] = duration_seconds
        if error_message:
            context.metadata["error_message"] = error_message
        await self._cache_call_context(call_sid, context)
        
        return True
    
    async def get_call_context(
        self,
        call_sid: str
    ) -> Optional[CallContext]:
        """
        Retrieve call context from Redis cache.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            CallContext object or None if not found
            
        Requirements: 9.1, 18.2
        """
        # Get from Redis cache
        session_data = await self.redis.get_session_state(call_sid)
        if not session_data:
            return None
        
        # Reconstruct CallContext from cached data
        created_at_str = session_data["created_at"]
        created_at = datetime.fromisoformat(created_at_str)
        # Ensure timezone-aware
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        context = CallContext(
            call_id=session_data["call_id"],
            caller_phone=session_data["caller_phone"],
            caller_name=session_data.get("caller_name"),
            language=Language(session_data.get("language", "en")),
            intent=Intent(session_data["intent"]) if session_data.get("intent") else None,
            intent_confidence=session_data.get("intent_confidence", 0.0),
            conversation_history=session_data.get("conversation_history", []),
            lead_data=session_data.get("lead_data"),
            appointment_data=session_data.get("appointment_data"),
            metadata=session_data.get("metadata", {}),
            created_at=created_at
        )
        
        return context
    
    async def get_caller_history(
        self,
        caller_phone: str,
        limit: int = 10
    ) -> list[Dict[str, Any]]:
        """
        Retrieve call history for a caller.
        
        First checks Redis cache, then falls back to database.
        
        Args:
            caller_phone: Caller's phone number
            limit: Maximum number of records to return
            
        Returns:
            List of call records
            
        Requirements: 9.1, 9.3
        """
        # Try Redis cache first
        call_ids = await self.redis.get_caller_history(caller_phone, limit)
        
        if not call_ids:
            # Fall back to database
            return await self.database.get_caller_history(caller_phone, limit)
        
        # Fetch call details from database
        calls = []
        for call_id in call_ids:
            call = await self.database.get_call(call_id)
            if call:
                calls.append(call)
        
        return calls
    
    async def retrieve_conversation_history(
        self,
        caller_phone: str,
        days: int = 30,
        max_calls: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a returning caller.
        
        This method retrieves recent call history (last N days, up to M calls)
        and loads conversation transcripts for each call. It combines data from
        PostgreSQL (call records and transcripts) and Redis cache (if available).
        
        Args:
            caller_phone: Caller's phone number
            days: Number of days to look back (default: 30)
            max_calls: Maximum number of previous calls to retrieve (default: 5)
            
        Returns:
            List of dictionaries containing call metadata and conversation transcripts
            Each entry has: call_id, started_at, intent, transcripts
            
        Requirements: 9.1, 9.2
        """
        # Get recent call history from database
        recent_calls = await self.database.get_recent_caller_history(
            caller_phone=caller_phone,
            days=days,
            limit=max_calls
        )
        
        if not recent_calls:
            return []
        
        # Load transcripts for each call
        history = []
        for call in recent_calls:
            call_id = str(call["id"])
            
            # Get transcripts from database
            transcripts = await self.database.get_call_transcripts(call_id)
            
            # Build history entry
            history_entry = {
                "call_id": call_id,
                "started_at": call["started_at"].isoformat() if call.get("started_at") else None,
                "intent": call.get("intent"),
                "intent_confidence": float(call["intent_confidence"]) if call.get("intent_confidence") else None,
                "duration_seconds": call.get("duration_seconds"),
                "transcripts": transcripts
            }
            
            history.append(history_entry)
        
        return history
    
    async def integrate_conversation_history(
        self,
        call_sid: str,
        caller_phone: str
    ) -> bool:
        """
        Integrate conversation history into current call context.
        
        This method retrieves previous conversation history for a returning caller
        and integrates it into the current call context. The history is stored in
        the CallContext metadata for reference during the conversation.
        
        Args:
            call_sid: Current call's Twilio call SID
            caller_phone: Caller's phone number
            
        Returns:
            True if history was integrated, False if no history found
            
        Requirements: 9.1, 9.2, 9.3
        """
        # Get current call context
        context = await self.get_call_context(call_sid)
        if not context:
            raise ValueError(f"Call context not found for call_sid: {call_sid}")
        
        # Retrieve conversation history
        history = await self.retrieve_conversation_history(caller_phone)
        
        if not history:
            # No previous history found
            context.metadata["is_returning_caller"] = False
            context.metadata["previous_calls_count"] = 0
            await self._cache_call_context(call_sid, context)
            return False
        
        # Integrate history into context
        context.metadata["is_returning_caller"] = True
        context.metadata["previous_calls_count"] = len(history)
        context.metadata["conversation_history"] = history
        
        # Extract summary information for quick reference
        previous_intents = [h["intent"] for h in history if h.get("intent")]
        if previous_intents:
            context.metadata["previous_intents"] = previous_intents
        
        # Cache updated context
        await self._cache_call_context(call_sid, context)
        
        return True
    
    async def get_conversation_summary(
        self,
        call_sid: str
    ) -> Optional[str]:
        """
        Generate a summary of previous conversations for a returning caller.
        
        This method creates a human-readable summary of the caller's history
        that can be used to personalize the greeting or provide context to
        the AI assistant.
        
        Args:
            call_sid: Current call's Twilio call SID
            
        Returns:
            Summary string or None if no history available
            
        Requirements: 9.3, 9.5
        """
        context = await self.get_call_context(call_sid)
        if not context:
            return None
        
        if not context.metadata.get("is_returning_caller"):
            return None
        
        history = context.metadata.get("conversation_history", [])
        if not history:
            return None
        
        # Build summary
        summary_parts = []
        summary_parts.append(f"This caller has contacted us {len(history)} time(s) in the past 30 days.")
        
        # Summarize previous intents
        previous_intents = context.metadata.get("previous_intents", [])
        if previous_intents:
            intent_summary = ", ".join(set(previous_intents))
            summary_parts.append(f"Previous topics: {intent_summary}.")
        
        # Include most recent call info
        most_recent = history[0]
        if most_recent.get("started_at"):
            summary_parts.append(f"Last call was on {most_recent['started_at']}.")
        
        return " ".join(summary_parts)
    
    async def _cache_call_context(
        self,
        call_sid: str,
        context: CallContext
    ) -> None:
        """
        Cache call context in Redis.
        
        Args:
            call_sid: Twilio call SID
            context: CallContext to cache
        """
        session_data = {
            "call_id": context.call_id,
            "caller_phone": context.caller_phone,
            "caller_name": context.caller_name,
            "language": context.language.value,
            "intent": context.intent.value if context.intent else None,
            "intent_confidence": context.intent_confidence,
            "conversation_history": context.conversation_history,
            "lead_data": context.lead_data,
            "appointment_data": context.appointment_data,
            "metadata": context.metadata,
            "created_at": context.created_at.isoformat()
        }
        
        await self.redis.set_session_state(call_sid, session_data)
