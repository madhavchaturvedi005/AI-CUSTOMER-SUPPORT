"""Call routing decision engine for AI Voice Automation system.

This module provides intelligent call routing based on intent detection,
business rules, and agent availability.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 11.1, 11.2, 11.3, 11.4**
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime, time, date, timedelta
import pytz
from models import CallContext, Intent
from redis_service import RedisService


@dataclass
class RoutingRule:
    """Configuration for call routing logic.
    
    Defines how calls with specific intents should be routed based on
    business rules, agent availability, and time constraints.
    
    **Validates: Requirement 4.1** - Routing destination determination
    """
    intent: Intent
    priority: int  # Higher = more priority
    business_hours_only: bool
    agent_skills_required: List[str]
    max_queue_time_seconds: int
    
    def validate(self) -> None:
        """Validate routing rule configuration."""
        if self.priority < 0:
            raise ValueError("priority must be non-negative")
        
        if self.max_queue_time_seconds < 0:
            raise ValueError("max_queue_time_seconds must be non-negative")
        
        if not isinstance(self.intent, Intent):
            raise ValueError("intent must be an Intent enum value")


class CallRouter:
    """Intelligent call routing based on intent and business rules.
    
    Routes calls to appropriate destinations (AI continuation, agent transfer,
    or voicemail) based on detected intent, business hours, agent availability,
    and lead value.
    
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 11.1, 11.2, 11.3, 11.4**
    """
    
    def __init__(
        self,
        business_hours: Optional[Dict[str, List[tuple]]] = None,
        timezone: str = "UTC",
        holiday_dates: Optional[List[date]] = None,
        redis_service: Optional[RedisService] = None
    ):
        """Initialize call router.
        
        Args:
            business_hours: Dictionary mapping day names to list of (start, end) time tuples.
                Example: {"monday": [(time(9, 0), time(17, 0))]}
            timezone: Timezone string (e.g., "America/New_York", "Asia/Kolkata")
                **Validates: Requirement 11.1** - Support configurable business hours per timezone
            holiday_dates: List of holiday dates when business is closed
                **Validates: Requirement 11.2** - Handle holiday schedules
            redis_service: RedisService instance for querying agent availability
                **Validates: Requirement 4.2** - Query Redis for agent availability
        """
        self.routing_rules: Dict[Intent, RoutingRule] = {}
        self.business_hours = business_hours or self._default_business_hours()
        self.timezone = pytz.timezone(timezone)
        self.holiday_dates = holiday_dates or []
        self.redis_service = redis_service
    
    def add_routing_rule(self, rule: RoutingRule) -> None:
        """Add or update a routing rule for an intent.
        
        Args:
            rule: RoutingRule configuration to add.
            
        Raises:
            ValueError: If rule validation fails.
        """
        rule.validate()
        self.routing_rules[rule.intent] = rule
    
    async def route_call(
        self,
        call_context: CallContext,
        agent_availability: Dict[str, bool]
    ) -> str:
        """Determine routing destination for call.
        
        Analyzes call context, intent, business hours, and agent availability
        to make intelligent routing decisions.
        
        **Validates: Requirement 4.1** - Routing destination determination
        **Validates: Requirement 4.2** - Business hours and agent availability check
        **Validates: Requirement 4.3** - AI continuation when no agent available
        **Validates: Requirement 4.4** - Priority routing for high-value leads
        
        Args:
            call_context: Complete context for the current call.
            agent_availability: Dictionary mapping agent IDs to availability status.
            
        Returns:
            Routing decision string:
                - "ai_continue": Continue with AI-assisted conversation
                - "transfer_to_agent:{agent_id}": Transfer to specific agent
                - "voicemail": Route to voicemail system
                
        Raises:
            ValueError: If call_context is invalid.
        """
        # Validate call context
        if not call_context:
            raise ValueError("call_context cannot be None")
        
        call_context.validate()
        
        # If no intent detected, continue with AI
        if not call_context.intent:
            return "ai_continue"
        
        # Get routing rule for this intent
        rule = self.routing_rules.get(call_context.intent)
        if not rule:
            # No specific routing rule, continue with AI
            return "ai_continue"
        
        # Check business hours requirement (Requirement 4.2)
        if rule.business_hours_only and not self._is_business_hours():
            return "ai_continue"
        
        # Find available agents with required skills (Requirement 4.2)
        available_agents = await self._find_available_agents(
            agent_availability,
            rule.agent_skills_required
        )
        
        # If no agents available, continue with AI (Requirement 4.3)
        if not available_agents:
            return "ai_continue"
        
        # Priority routing for high-value leads (Requirement 4.4)
        if call_context.lead_data:
            lead_score = call_context.lead_data.get("lead_score", 0)
            if lead_score >= 7:
                # High-value lead gets immediate transfer
                return f"transfer_to_agent:{available_agents[0]}"
        
        # Standard routing to first available agent
        return f"transfer_to_agent:{available_agents[0]}"
    
    def _is_business_hours(self, check_time: Optional[datetime] = None) -> bool:
        """Check if current time is within business hours.
        
        **Validates: Requirement 4.2** - Route calls based on business hours
        **Validates: Requirement 11.1** - Support configurable business hours per timezone
        **Validates: Requirement 11.2** - Handle holiday schedules
        
        Args:
            check_time: Time to check (defaults to current time in configured timezone)
        
        Returns:
            True if within business hours, False otherwise.
        """
        # Get current time in configured timezone
        if check_time is None:
            now = datetime.now(self.timezone)
        else:
            # Convert provided time to configured timezone
            if check_time.tzinfo is None:
                # Assume UTC if no timezone info
                now = pytz.utc.localize(check_time).astimezone(self.timezone)
            else:
                now = check_time.astimezone(self.timezone)
        
        # Check if today is a holiday
        if now.date() in self.holiday_dates:
            return False
        
        day_name = now.strftime("%A").lower()
        current_time = now.time()
        
        # Get business hours for current day
        day_hours = self.business_hours.get(day_name, [])
        
        # Check if current time falls within any business hour range
        for start_time, end_time in day_hours:
            if start_time <= current_time <= end_time:
                return True
        
        return False
    
    async def _find_available_agents(
        self,
        agent_availability: Dict[str, bool],
        required_skills: List[str]
    ) -> List[str]:
        """Find available agents with required skills.
        
        Queries Redis for real-time agent availability and skills, then filters
        agents based on availability status and required skill matching.
        
        **Validates: Requirement 4.2** - Query Redis for agent availability
        **Validates: Requirement 4.4** - Match agent skills with routing requirements
        
        Args:
            agent_availability: Dictionary mapping agent IDs to availability (fallback).
            required_skills: List of required skill tags.
            
        Returns:
            List of available agent IDs sorted by priority.
        """
        # If Redis service is available, query for real-time agent data
        if self.redis_service:
            try:
                # Get all agents' availability from Redis
                redis_availability = await self.redis_service.get_all_agents_availability()
                
                # Get agent skills from Redis (stored as JSON in agent metadata)
                available_agents = []
                
                for agent_id, status in redis_availability.items():
                    # Only consider agents with "available" status
                    if status != "available":
                        continue
                    
                    # Get agent skills from Redis
                    agent_skills = await self._get_agent_skills(agent_id)
                    
                    # Check if agent has all required skills
                    if self._has_required_skills(agent_skills, required_skills):
                        available_agents.append(agent_id)
                
                return available_agents
                
            except Exception as e:
                # Fall back to provided agent_availability if Redis query fails
                print(f"Redis query failed, using fallback availability: {e}")
        
        # Fallback: use provided agent_availability dictionary
        # Filter by availability status
        available = [
            agent_id
            for agent_id, is_available in agent_availability.items()
            if is_available
        ]
        
        return available
    
    async def _get_agent_skills(self, agent_id: str) -> List[str]:
        """Get agent skills from Redis.
        
        **Validates: Requirement 4.4** - Match agent skills with routing requirements
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of skill tags for the agent
        """
        if not self.redis_service:
            return []
        
        try:
            # Get agent metadata from Redis
            key = f"agent:{agent_id}:skills"
            skills_json = await self.redis_service.client.get(key)
            
            if skills_json:
                import json
                return json.loads(skills_json)
            
            return []
            
        except Exception as e:
            print(f"Failed to get agent skills for {agent_id}: {e}")
            return []
    
    async def transfer_to_agent(
        self,
        call_context: CallContext,
        agent_id: str,
        transfer_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transfer call to live agent with full context handoff.
        
        Prepares a comprehensive context summary including caller history,
        detected intent, lead data, and conversation transcript, then stores
        it in Redis for agent access.
        
        **Validates: Requirement 4.5** - Transfer calls to live agents with full context handoff
        
        Args:
            call_context: Complete context for the current call
            agent_id: Agent identifier to transfer to
            transfer_phone: Optional phone number to transfer to (for Twilio)
            
        Returns:
            Dictionary containing:
                - status: "success" or "failed"
                - agent_id: Agent identifier
                - context_key: Redis key where context is stored
                - error: Error message if failed
                
        Raises:
            ValueError: If call_context or agent_id is invalid
        """
        # Validate inputs
        if not call_context:
            raise ValueError("call_context cannot be None")
        
        if not agent_id:
            raise ValueError("agent_id cannot be empty")
        
        call_context.validate()
        
        try:
            # Prepare comprehensive context summary
            context_summary = self._prepare_context_summary(call_context)
            
            # Store context in Redis for agent access
            context_key = f"transfer_context:{call_context.call_id}:{agent_id}"
            
            if self.redis_service:
                # Store with 1 hour TTL (enough time for agent to access)
                await self.redis_service.client.setex(
                    context_key,
                    3600,  # 1 hour
                    self._serialize_context(context_summary)
                )
            else:
                # If no Redis service, log warning but continue
                print(f"Warning: No Redis service available for context storage")
            
            # Return transfer status
            return {
                "status": "success",
                "agent_id": agent_id,
                "context_key": context_key,
                "transfer_phone": transfer_phone,
                "context_summary": context_summary
            }
            
        except Exception as e:
            print(f"Failed to prepare transfer context: {e}")
            return {
                "status": "failed",
                "agent_id": agent_id,
                "error": str(e)
            }
    
    def _prepare_context_summary(self, call_context: CallContext) -> Dict[str, Any]:
        """Prepare comprehensive context summary for agent.
        
        **Validates: Requirement 4.5** - Provide agent with caller history and intent
        
        Args:
            call_context: Complete context for the current call
            
        Returns:
            Dictionary containing context summary with:
                - caller_info: Phone, name, language
                - intent_info: Detected intent and confidence
                - lead_info: Lead data if available
                - conversation_summary: Recent conversation history
                - metadata: Additional context information
        """
        # Prepare caller information
        caller_info = {
            "phone": call_context.caller_phone,
            "name": call_context.caller_name or "Unknown",
            "language": call_context.language.value if call_context.language else "en"
        }
        
        # Prepare intent information
        intent_info = {
            "intent": call_context.intent.value if call_context.intent else "unknown",
            "confidence": call_context.intent_confidence,
            "description": self._get_intent_description(call_context.intent)
        }
        
        # Prepare lead information if available
        lead_info = None
        if call_context.lead_data:
            lead_info = {
                "lead_score": call_context.lead_data.get("lead_score", 0),
                "name": call_context.lead_data.get("name"),
                "email": call_context.lead_data.get("email"),
                "inquiry_details": call_context.lead_data.get("inquiry_details"),
                "budget_indication": call_context.lead_data.get("budget_indication"),
                "timeline": call_context.lead_data.get("timeline"),
                "decision_authority": call_context.lead_data.get("decision_authority", False)
            }
        
        # Prepare conversation summary (last 10 turns)
        conversation_summary = []
        recent_history = call_context.conversation_history[-10:] if call_context.conversation_history else []
        
        for turn in recent_history:
            conversation_summary.append({
                "speaker": turn.get("speaker", "unknown"),
                "text": turn.get("text", ""),
                "timestamp": turn.get("timestamp")
            })
        
        # Prepare appointment information if available
        appointment_info = None
        if call_context.appointment_data:
            appointment_info = {
                "service_type": call_context.appointment_data.get("service_type"),
                "appointment_datetime": call_context.appointment_data.get("appointment_datetime"),
                "duration_minutes": call_context.appointment_data.get("duration_minutes"),
                "notes": call_context.appointment_data.get("notes")
            }
        
        # Compile complete context summary
        context_summary = {
            "call_id": call_context.call_id,
            "caller_info": caller_info,
            "intent_info": intent_info,
            "lead_info": lead_info,
            "appointment_info": appointment_info,
            "conversation_summary": conversation_summary,
            "metadata": call_context.metadata,
            "created_at": call_context.created_at.isoformat() if call_context.created_at else None,
            "transfer_timestamp": datetime.now(self.timezone).isoformat()
        }
        
        return context_summary
    
    def _get_intent_description(self, intent: Optional[Intent]) -> str:
        """Get human-readable description of intent.
        
        Args:
            intent: Intent enum value
            
        Returns:
            Human-readable description
        """
        descriptions = {
            Intent.SALES_INQUIRY: "Customer is interested in purchasing products or services",
            Intent.SUPPORT_REQUEST: "Customer needs technical or product support",
            Intent.APPOINTMENT_BOOKING: "Customer wants to schedule an appointment",
            Intent.COMPLAINT: "Customer has a complaint or issue to resolve",
            Intent.GENERAL_INQUIRY: "Customer has general questions or information needs",
            Intent.UNKNOWN: "Intent could not be determined"
        }
        
        return descriptions.get(intent, "No intent detected")
    
    def _serialize_context(self, context_summary: Dict[str, Any]) -> str:
        """Serialize context summary to JSON string.
        
        Args:
            context_summary: Context summary dictionary
            
        Returns:
            JSON string
        """
        import json
        return json.dumps(context_summary, default=str)
    
    async def get_transfer_context(
        self,
        call_id: str,
        agent_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve transfer context for agent.
        
        Allows agents to retrieve the context summary that was prepared
        during call transfer.
        
        **Validates: Requirement 4.5** - Provide agent with caller history and intent
        
        Args:
            call_id: Call identifier
            agent_id: Agent identifier
            
        Returns:
            Context summary dictionary or None if not found
        """
        if not self.redis_service:
            return None
        
        try:
            context_key = f"transfer_context:{call_id}:{agent_id}"
            context_json = await self.redis_service.client.get(context_key)
            
            if context_json:
                import json
                return json.loads(context_json)
            
            return None
            
        except Exception as e:
            print(f"Failed to retrieve transfer context: {e}")
            return None
    
    def _has_required_skills(
        self,
        agent_skills: List[str],
        required_skills: List[str]
    ) -> bool:
        """Check if agent has all required skills.
        
        **Validates: Requirement 4.4** - Match agent skills with routing requirements
        
        Args:
            agent_skills: List of skills the agent has
            required_skills: List of skills required for routing
            
        Returns:
            True if agent has all required skills, False otherwise
        """
        # If no skills required, any agent qualifies
        if not required_skills:
            return True
        
        # Check if agent has all required skills
        agent_skill_set = set(skill.lower() for skill in agent_skills)
        required_skill_set = set(skill.lower() for skill in required_skills)
        
        return required_skill_set.issubset(agent_skill_set)
    
    def _default_business_hours(self) -> Dict[str, List[tuple]]:
        """Get default business hours configuration.
        
        Returns:
            Default business hours (Monday-Friday, 9 AM - 5 PM).
        """
        default_hours = [(time(9, 0), time(17, 0))]
        
        return {
            "monday": default_hours,
            "tuesday": default_hours,
            "wednesday": default_hours,
            "thursday": default_hours,
            "friday": default_hours,
            "saturday": [],
            "sunday": []
        }
    
    async def load_config_from_db(self, db_service, business_id: str) -> None:
        """Load business hours and holiday configuration from database.
        
        **Validates: Requirement 11.1** - Support configurable business hours per timezone
        **Validates: Requirement 11.2** - Handle holiday schedules
        
        Args:
            db_service: DatabaseService instance
            business_id: Business identifier
            
        Raises:
            ValueError: If business configuration not found
        """
        config = await db_service.get_business_config(business_id)
        
        if not config:
            raise ValueError(f"Business configuration not found for ID: {business_id}")
        
        # Parse business hours from JSONB
        if config.get("business_hours"):
            self.business_hours = self._parse_business_hours(config["business_hours"])
        
        # Parse holiday schedule from JSONB
        if config.get("holiday_schedule"):
            self.holiday_dates = self._parse_holiday_schedule(config["holiday_schedule"])
        
        # Update timezone if configured
        if config.get("timezone"):
            self.timezone = pytz.timezone(config["timezone"])
    
    def _parse_business_hours(self, hours_config: Dict) -> Dict[str, List[tuple]]:
        """Parse business hours from database configuration.
        
        Args:
            hours_config: Business hours configuration from database
                Example: {
                    "monday": [{"start": "09:00", "end": "17:00"}],
                    "tuesday": [{"start": "09:00", "end": "17:00"}]
                }
        
        Returns:
            Parsed business hours dictionary
        """
        parsed_hours = {}
        
        for day, hours_list in hours_config.items():
            day_hours = []
            for hours in hours_list:
                start_time = self._parse_time(hours["start"])
                end_time = self._parse_time(hours["end"])
                day_hours.append((start_time, end_time))
            parsed_hours[day.lower()] = day_hours
        
        return parsed_hours
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string to time object.
        
        Args:
            time_str: Time string in format "HH:MM" or "HH:MM:SS"
        
        Returns:
            time object
        """
        parts = time_str.split(":")
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) > 2 else 0
        
        return time(hour, minute, second)
    
    def _parse_holiday_schedule(self, holiday_config: List[Dict]) -> List[date]:
        """Parse holiday schedule from database configuration.
        
        Args:
            holiday_config: Holiday schedule configuration from database
                Example: [
                    {"date": "2024-12-25", "name": "Christmas"},
                    {"date": "2024-01-01", "name": "New Year"}
                ]
        
        Returns:
            List of holiday dates
        """
        holidays = []
        
        for holiday in holiday_config:
            holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d").date()
            holidays.append(holiday_date)
        
        return holidays
    
    def update_business_hours(self, business_hours: Dict[str, List[tuple]]) -> None:
        """Update business hours configuration.
        
        **Validates: Requirement 11.5** - Apply configuration changes within 5 minutes
        
        Args:
            business_hours: New business hours configuration
        """
        self.business_hours = business_hours
    
    def update_holiday_schedule(self, holiday_dates: List[date]) -> None:
        """Update holiday schedule.
        
        **Validates: Requirement 11.2** - Handle holiday schedules
        
        Args:
            holiday_dates: List of holiday dates
        """
        self.holiday_dates = holiday_dates
    
    def update_timezone(self, timezone: str) -> None:
        """Update timezone configuration.
        
        **Validates: Requirement 11.4** - Support multiple time zones
        
        Args:
            timezone: Timezone string (e.g., "America/New_York", "Asia/Kolkata")
            
        Raises:
            ValueError: If timezone is invalid
        """
        try:
            self.timezone = pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {timezone}")
    
    def get_next_available_time(self) -> Optional[datetime]:
        """Get the next available business time.
        
        **Validates: Requirement 11.3** - Provide after-hours messaging
        
        Returns:
            Next available datetime in configured timezone, or None if no business hours configured
        """
        now = datetime.now(self.timezone)
        
        # Check up to 14 days ahead
        for days_ahead in range(14):
            check_date = now.date() + timedelta(days=days_ahead)
            
            # Skip holidays
            if check_date in self.holiday_dates:
                continue
            
            day_name = check_date.strftime("%A").lower()
            day_hours = self.business_hours.get(day_name, [])
            
            if not day_hours:
                continue
            
            # Get first business hour slot for this day
            start_time, _ = day_hours[0]
            
            # Create naive datetime for this slot, then localize
            next_available_naive = datetime.combine(check_date, start_time)
            
            # For UTC, we can use replace; for other timezones, use localize
            if self.timezone.zone == 'UTC':
                next_available = next_available_naive.replace(tzinfo=pytz.utc)
            else:
                next_available = self.timezone.localize(next_available_naive)
            
            # If it's today, make sure it's in the future
            if days_ahead == 0 and next_available <= now:
                # Check if there are later slots today
                for start_time, end_time in day_hours:
                    slot_start_naive = datetime.combine(check_date, start_time)
                    if self.timezone.zone == 'UTC':
                        slot_start = slot_start_naive.replace(tzinfo=pytz.utc)
                    else:
                        slot_start = self.timezone.localize(slot_start_naive)
                    
                    if slot_start > now:
                        return slot_start
                # No more slots today, continue to next day
                continue
            
            return next_available
        
        return None
