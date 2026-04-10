"""Unit tests for call routing decision engine.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 11.1, 11.2, 11.3, 11.4**
"""

import pytest
from datetime import time, datetime, date, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
import pytz
from call_router import CallRouter, RoutingRule
from models import CallContext, Intent, Language


class TestRoutingRule:
    """Test RoutingRule dataclass validation."""
    
    def test_routing_rule_creation(self):
        """Test creating a valid routing rule."""
        rule = RoutingRule(
            intent=Intent.SALES_INQUIRY,
            priority=5,
            business_hours_only=True,
            agent_skills_required=["sales"],
            max_queue_time_seconds=300
        )
        
        assert rule.intent == Intent.SALES_INQUIRY
        assert rule.priority == 5
        assert rule.business_hours_only is True
        assert rule.agent_skills_required == ["sales"]
        assert rule.max_queue_time_seconds == 300
    
    def test_routing_rule_validation_negative_priority(self):
        """Test routing rule validation fails with negative priority."""
        rule = RoutingRule(
            intent=Intent.SALES_INQUIRY,
            priority=-1,
            business_hours_only=True,
            agent_skills_required=["sales"],
            max_queue_time_seconds=300
        )
        
        with pytest.raises(ValueError, match="priority must be non-negative"):
            rule.validate()
    
    def test_routing_rule_validation_negative_queue_time(self):
        """Test routing rule validation fails with negative queue time."""
        rule = RoutingRule(
            intent=Intent.SALES_INQUIRY,
            priority=5,
            business_hours_only=True,
            agent_skills_required=["sales"],
            max_queue_time_seconds=-100
        )
        
        with pytest.raises(ValueError, match="max_queue_time_seconds must be non-negative"):
            rule.validate()


class TestCallRouter:
    """Test CallRouter routing logic."""
    
    def test_router_initialization(self):
        """Test router initializes with default business hours."""
        router = CallRouter()
        
        assert router.routing_rules == {}
        assert "monday" in router.business_hours
        assert router.business_hours["monday"] == [(time(9, 0), time(17, 0))]
    
    def test_router_custom_business_hours(self):
        """Test router initialization with custom business hours."""
        custom_hours = {
            "monday": [(time(8, 0), time(18, 0))],
            "tuesday": [(time(8, 0), time(18, 0))]
        }
        router = CallRouter(business_hours=custom_hours)
        
        assert router.business_hours == custom_hours
    
    def test_add_routing_rule(self):
        """Test adding a routing rule."""
        router = CallRouter()
        rule = RoutingRule(
            intent=Intent.SALES_INQUIRY,
            priority=5,
            business_hours_only=True,
            agent_skills_required=["sales"],
            max_queue_time_seconds=300
        )
        
        router.add_routing_rule(rule)
        
        assert Intent.SALES_INQUIRY in router.routing_rules
        assert router.routing_rules[Intent.SALES_INQUIRY] == rule
    
    def test_add_invalid_routing_rule(self):
        """Test adding an invalid routing rule raises error."""
        router = CallRouter()
        rule = RoutingRule(
            intent=Intent.SALES_INQUIRY,
            priority=-1,
            business_hours_only=True,
            agent_skills_required=["sales"],
            max_queue_time_seconds=300
        )
        
        with pytest.raises(ValueError):
            router.add_routing_rule(rule)
    
    @pytest.mark.asyncio
    async def test_route_call_no_intent(self):
        """Test routing continues with AI when no intent detected."""
        router = CallRouter()
        call_context = CallContext(
            call_id="test-123",
            caller_phone="+1234567890",
            intent=None
        )
        
        result = await router.route_call(call_context, {})
        
        assert result == "ai_continue"
    
    @pytest.mark.asyncio
    async def test_route_call_no_routing_rule(self):
        """Test routing continues with AI when no routing rule exists."""
        router = CallRouter()
        call_context = CallContext(
            call_id="test-123",
            caller_phone="+1234567890",
            intent=Intent.GENERAL_INQUIRY
        )
        
        result = await router.route_call(call_context, {})
        
        assert result == "ai_continue"
    
    @pytest.mark.asyncio
    async def test_route_call_outside_business_hours(self):
        """Test routing continues with AI outside business hours."""
        router = CallRouter()
        rule = RoutingRule(
            intent=Intent.SALES_INQUIRY,
            priority=5,
            business_hours_only=True,
            agent_skills_required=["sales"],
            max_queue_time_seconds=300
        )
        router.add_routing_rule(rule)
        
        call_context = CallContext(
            call_id="test-123",
            caller_phone="+1234567890",
            intent=Intent.SALES_INQUIRY
        )
        
        # Mock time to be outside business hours (8 PM)
        with patch('call_router.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 20, 0)  # Monday 8 PM
            mock_datetime.strftime = datetime.strftime
            
            result = await router.route_call(call_context, {"agent_001": True})
        
        assert result == "ai_continue"
    
    @pytest.mark.asyncio
    async def test_route_call_no_agents_available(self):
        """Test routing continues with AI when no agents available."""
        router = CallRouter()
        rule = RoutingRule(
            intent=Intent.SALES_INQUIRY,
            priority=5,
            business_hours_only=False,
            agent_skills_required=["sales"],
            max_queue_time_seconds=300
        )
        router.add_routing_rule(rule)
        
        call_context = CallContext(
            call_id="test-123",
            caller_phone="+1234567890",
            intent=Intent.SALES_INQUIRY
        )
        
        result = await router.route_call(call_context, {})
        
        assert result == "ai_continue"
    
    @pytest.mark.asyncio
    async def test_route_call_agent_available(self):
        """Test routing transfers to agent when available."""
        router = CallRouter()
        rule = RoutingRule(
            intent=Intent.SALES_INQUIRY,
            priority=5,
            business_hours_only=False,
            agent_skills_required=["sales"],
            max_queue_time_seconds=300
        )
        router.add_routing_rule(rule)
        
        call_context = CallContext(
            call_id="test-123",
            caller_phone="+1234567890",
            intent=Intent.SALES_INQUIRY
        )
        
        result = await router.route_call(
            call_context,
            {"agent_001": True, "agent_002": False}
        )
        
        assert result == "transfer_to_agent:agent_001"
    
    @pytest.mark.asyncio
    async def test_route_call_high_value_lead_priority(self):
        """Test high-value leads get priority routing."""
        router = CallRouter()
        rule = RoutingRule(
            intent=Intent.SALES_INQUIRY,
            priority=5,
            business_hours_only=False,
            agent_skills_required=["sales"],
            max_queue_time_seconds=300
        )
        router.add_routing_rule(rule)
        
        call_context = CallContext(
            call_id="test-123",
            caller_phone="+1234567890",
            intent=Intent.SALES_INQUIRY,
            lead_data={"lead_score": 8}
        )
        
        result = await router.route_call(
            call_context,
            {"agent_001": True, "agent_002": True}
        )
        
        assert result == "transfer_to_agent:agent_001"
    
    @pytest.mark.asyncio
    async def test_route_call_low_value_lead(self):
        """Test low-value leads still get routed to agents."""
        router = CallRouter()
        rule = RoutingRule(
            intent=Intent.SALES_INQUIRY,
            priority=5,
            business_hours_only=False,
            agent_skills_required=["sales"],
            max_queue_time_seconds=300
        )
        router.add_routing_rule(rule)
        
        call_context = CallContext(
            call_id="test-123",
            caller_phone="+1234567890",
            intent=Intent.SALES_INQUIRY,
            lead_data={"lead_score": 3}
        )
        
        result = await router.route_call(
            call_context,
            {"agent_001": True}
        )
        
        assert result == "transfer_to_agent:agent_001"
    
    @pytest.mark.asyncio
    async def test_route_call_invalid_context(self):
        """Test routing raises error with invalid call context."""
        router = CallRouter()
        
        with pytest.raises(ValueError):
            await router.route_call(None, {})
    
    def test_is_business_hours_within_hours(self):
        """Test business hours check returns True during business hours."""
        router = CallRouter()
        
        # Mock time to be within business hours (Monday 10 AM)
        with patch('call_router.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 10, 0)  # Monday 10 AM
            mock_datetime.now.return_value = mock_now
            
            result = router._is_business_hours()
        
        assert result is True
    
    def test_is_business_hours_outside_hours(self):
        """Test business hours check returns False outside business hours."""
        router = CallRouter()
        
        # Mock time to be outside business hours (Monday 8 PM)
        with patch('call_router.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 20, 0)  # Monday 8 PM
            mock_datetime.now.return_value = mock_now
            
            result = router._is_business_hours()
        
        assert result is False
    
    def test_is_business_hours_weekend(self):
        """Test business hours check returns False on weekend."""
        router = CallRouter()
        
        # Mock time to be on weekend (Saturday 10 AM)
        with patch('call_router.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 13, 10, 0)  # Saturday 10 AM
            mock_datetime.now.return_value = mock_now
            
            result = router._is_business_hours()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_find_available_agents(self):
        """Test finding available agents."""
        router = CallRouter()
        agent_availability = {
            "agent_001": True,
            "agent_002": False,
            "agent_003": True
        }
        
        result = await router._find_available_agents(agent_availability, ["sales"])
        
        assert "agent_001" in result
        assert "agent_003" in result
        assert "agent_002" not in result
    
    @pytest.mark.asyncio
    async def test_find_available_agents_none_available(self):
        """Test finding available agents when none available."""
        router = CallRouter()
        agent_availability = {
            "agent_001": False,
            "agent_002": False
        }
        
        result = await router._find_available_agents(agent_availability, ["sales"])
        
        assert result == []



class TestBusinessHoursEnhancements:
    """Test enhanced business hours checking with timezone and holiday support.
    
    **Validates: Requirements 11.1, 11.2, 11.3, 11.4**
    """
    
    def test_router_initialization_with_timezone(self):
        """Test router initialization with custom timezone."""
        router = CallRouter(timezone="America/New_York")
        
        assert router.timezone.zone == "America/New_York"
        assert router.holiday_dates == []
    
    def test_router_initialization_with_holidays(self):
        """Test router initialization with holiday dates."""
        holidays = [date(2024, 12, 25), date(2024, 1, 1)]
        router = CallRouter(holiday_dates=holidays)
        
        assert router.holiday_dates == holidays
    
    def test_is_business_hours_with_timezone_conversion(self):
        """Test business hours check with timezone conversion.
        
        **Validates: Requirement 11.1** - Support configurable business hours per timezone
        """
        # Create router with New York timezone
        router = CallRouter(timezone="America/New_York")
        
        # Create a time that is 10 AM in New York (within business hours)
        ny_tz = pytz.timezone("America/New_York")
        check_time = ny_tz.localize(datetime(2024, 1, 15, 10, 0))  # Monday 10 AM EST
        
        result = router._is_business_hours(check_time)
        
        assert result is True
    
    def test_is_business_hours_holiday(self):
        """Test business hours check returns False on holidays.
        
        **Validates: Requirement 11.2** - Handle holiday schedules
        """
        holidays = [date(2024, 12, 25)]
        router = CallRouter(holiday_dates=holidays)
        
        # Check time on Christmas (holiday)
        check_time = datetime(2024, 12, 25, 10, 0)  # Wednesday 10 AM
        
        result = router._is_business_hours(check_time)
        
        assert result is False
    
    def test_is_business_hours_not_holiday(self):
        """Test business hours check returns True on non-holidays."""
        holidays = [date(2024, 12, 25)]
        router = CallRouter(holiday_dates=holidays)
        
        # Check time on a regular Monday
        check_time = datetime(2024, 1, 15, 10, 0)  # Monday 10 AM
        
        result = router._is_business_hours(check_time)
        
        assert result is True
    
    def test_is_business_hours_utc_to_local_conversion(self):
        """Test business hours check with UTC to local timezone conversion."""
        # Create router with India timezone (UTC+5:30)
        router = CallRouter(timezone="Asia/Kolkata")
        
        # Create a UTC time that converts to 10 AM IST (within business hours)
        utc_time = pytz.utc.localize(datetime(2024, 1, 15, 4, 30))  # 4:30 AM UTC = 10:00 AM IST
        
        result = router._is_business_hours(utc_time)
        
        assert result is True
    
    def test_is_business_hours_naive_datetime(self):
        """Test business hours check with naive datetime (assumes UTC)."""
        router = CallRouter(timezone="UTC")
        
        # Naive datetime (no timezone info)
        check_time = datetime(2024, 1, 15, 10, 0)  # Monday 10 AM
        
        result = router._is_business_hours(check_time)
        
        assert result is True
    
    def test_update_business_hours(self):
        """Test updating business hours configuration."""
        router = CallRouter()
        
        new_hours = {
            "monday": [(time(8, 0), time(20, 0))],
            "tuesday": [(time(8, 0), time(20, 0))]
        }
        
        router.update_business_hours(new_hours)
        
        assert router.business_hours == new_hours
    
    def test_update_holiday_schedule(self):
        """Test updating holiday schedule."""
        router = CallRouter()
        
        new_holidays = [date(2024, 12, 25), date(2024, 1, 1), date(2024, 7, 4)]
        
        router.update_holiday_schedule(new_holidays)
        
        assert router.holiday_dates == new_holidays
    
    def test_update_timezone(self):
        """Test updating timezone configuration.
        
        **Validates: Requirement 11.4** - Support multiple time zones
        """
        router = CallRouter()
        
        router.update_timezone("America/Los_Angeles")
        
        assert router.timezone.zone == "America/Los_Angeles"
    
    def test_update_timezone_invalid(self):
        """Test updating timezone with invalid timezone raises error."""
        router = CallRouter()
        
        with pytest.raises(ValueError, match="Invalid timezone"):
            router.update_timezone("Invalid/Timezone")
    
    def test_get_next_available_time_same_day(self):
        """Test getting next available time when it's same day.
        
        **Validates: Requirement 11.3** - Provide after-hours messaging
        """
        # Set business hours to be later in the day
        custom_hours = {
            "monday": [(time(14, 0), time(18, 0))],  # 2 PM - 6 PM
            "tuesday": [(time(14, 0), time(18, 0))],
            "wednesday": [(time(14, 0), time(18, 0))],
            "thursday": [(time(14, 0), time(18, 0))],
            "friday": [(time(14, 0), time(18, 0))],
            "saturday": [],
            "sunday": []
        }
        router = CallRouter(business_hours=custom_hours, timezone="UTC")
        
        # Get next available time (should be today at 2 PM if before that, or tomorrow)
        next_time = router.get_next_available_time()
        
        assert next_time is not None
        # Should be either today or a future weekday at 2 PM
        assert next_time.hour == 14
        assert next_time.minute == 0
    
    def test_get_next_available_time_next_day(self):
        """Test getting next available time when it's next day."""
        # Set business hours to early morning (likely already passed)
        custom_hours = {
            "monday": [(time(0, 0), time(1, 0))],  # Midnight - 1 AM
            "tuesday": [(time(0, 0), time(1, 0))],
            "wednesday": [(time(0, 0), time(1, 0))],
            "thursday": [(time(0, 0), time(1, 0))],
            "friday": [(time(0, 0), time(1, 0))],
            "saturday": [],
            "sunday": []
        }
        router = CallRouter(business_hours=custom_hours, timezone="UTC")
        
        next_time = router.get_next_available_time()
        
        assert next_time is not None
        # Should be a future weekday at midnight
        assert next_time.hour == 0
        assert next_time.minute == 0
    
    def test_get_next_available_time_skip_weekend(self):
        """Test getting next available time skips weekend."""
        # Only set business hours for weekdays
        custom_hours = {
            "monday": [(time(9, 0), time(17, 0))],
            "tuesday": [(time(9, 0), time(17, 0))],
            "wednesday": [(time(9, 0), time(17, 0))],
            "thursday": [(time(9, 0), time(17, 0))],
            "friday": [(time(9, 0), time(17, 0))],
            "saturday": [],  # No weekend hours
            "sunday": []
        }
        router = CallRouter(business_hours=custom_hours, timezone="UTC")
        
        next_time = router.get_next_available_time()
        
        assert next_time is not None
        # Should be a weekday (Monday-Friday)
        assert next_time.strftime("%A").lower() in ["monday", "tuesday", "wednesday", "thursday", "friday"]
    
    def test_get_next_available_time_skip_holiday(self):
        """Test getting next available time skips holidays."""
        # Get tomorrow's date and mark it as a holiday
        tomorrow = date.today() + timedelta(days=1)
        holidays = [tomorrow]
        
        router = CallRouter(timezone="UTC", holiday_dates=holidays)
        
        next_time = router.get_next_available_time()
        
        assert next_time is not None
        # Should not be the holiday date
        assert next_time.date() != tomorrow
    
    def test_get_next_available_time_no_business_hours(self):
        """Test getting next available time when no business hours configured."""
        # Set all days to have no business hours
        no_hours = {
            "monday": [],
            "tuesday": [],
            "wednesday": [],
            "thursday": [],
            "friday": [],
            "saturday": [],
            "sunday": []
        }
        router = CallRouter(business_hours=no_hours)
        
        next_time = router.get_next_available_time()
        
        assert next_time is None
    
    def test_parse_business_hours(self):
        """Test parsing business hours from database format."""
        router = CallRouter()
        
        hours_config = {
            "monday": [{"start": "09:00", "end": "17:00"}],
            "tuesday": [
                {"start": "09:00", "end": "12:00"},
                {"start": "13:00", "end": "17:00"}
            ]
        }
        
        parsed = router._parse_business_hours(hours_config)
        
        assert parsed["monday"] == [(time(9, 0), time(17, 0))]
        assert parsed["tuesday"] == [
            (time(9, 0), time(12, 0)),
            (time(13, 0), time(17, 0))
        ]
    
    def test_parse_time(self):
        """Test parsing time string to time object."""
        router = CallRouter()
        
        # Test HH:MM format
        t1 = router._parse_time("09:30")
        assert t1 == time(9, 30, 0)
        
        # Test HH:MM:SS format
        t2 = router._parse_time("14:45:30")
        assert t2 == time(14, 45, 30)
    
    def test_parse_holiday_schedule(self):
        """Test parsing holiday schedule from database format."""
        router = CallRouter()
        
        holiday_config = [
            {"date": "2024-12-25", "name": "Christmas"},
            {"date": "2024-01-01", "name": "New Year"}
        ]
        
        parsed = router._parse_holiday_schedule(holiday_config)
        
        assert date(2024, 12, 25) in parsed
        assert date(2024, 1, 1) in parsed
        assert len(parsed) == 2
    
    @pytest.mark.asyncio
    async def test_load_config_from_db(self):
        """Test loading configuration from database."""
        router = CallRouter()
        
        # Mock database service
        mock_db = AsyncMock()
        mock_db.get_business_config.return_value = {
            "business_id": "test-business",
            "business_hours": {
                "monday": [{"start": "08:00", "end": "18:00"}],
                "tuesday": [{"start": "08:00", "end": "18:00"}]
            },
            "holiday_schedule": [
                {"date": "2024-12-25", "name": "Christmas"}
            ],
            "timezone": "America/New_York"
        }
        
        await router.load_config_from_db(mock_db, "test-business")
        
        assert router.business_hours["monday"] == [(time(8, 0), time(18, 0))]
        assert date(2024, 12, 25) in router.holiday_dates
        assert router.timezone.zone == "America/New_York"
    
    @pytest.mark.asyncio
    async def test_load_config_from_db_not_found(self):
        """Test loading configuration from database when not found."""
        router = CallRouter()
        
        # Mock database service returning None
        mock_db = AsyncMock()
        mock_db.get_business_config.return_value = None
        
        with pytest.raises(ValueError, match="Business configuration not found"):
            await router.load_config_from_db(mock_db, "nonexistent-business")
    
    @pytest.mark.asyncio
    async def test_route_call_with_timezone_aware_business_hours(self):
        """Test call routing respects timezone-aware business hours."""
        # Create router with New York timezone
        router = CallRouter(timezone="America/New_York")
        
        rule = RoutingRule(
            intent=Intent.SALES_INQUIRY,
            priority=5,
            business_hours_only=True,
            agent_skills_required=["sales"],
            max_queue_time_seconds=300
        )
        router.add_routing_rule(rule)
        
        call_context = CallContext(
            call_id="test-123",
            caller_phone="+1234567890",
            intent=Intent.SALES_INQUIRY
        )
        
        # Mock time to be 10 AM EST (within business hours)
        with patch.object(router, '_is_business_hours', return_value=True):
            result = await router.route_call(
                call_context,
                {"agent_001": True}
            )
        
        assert result == "transfer_to_agent:agent_001"



class TestAgentAvailabilityChecking:
    """Test agent availability checking with Redis integration.
    
    **Validates: Requirements 4.2, 4.4**
    """
    
    @pytest.mark.asyncio
    async def test_find_available_agents_with_redis(self):
        """Test finding available agents using Redis.
        
        **Validates: Requirement 4.2** - Query Redis for agent availability
        """
        # Mock Redis service
        mock_redis = AsyncMock()
        mock_redis.get_all_agents_availability.return_value = {
            "agent_001": "available",
            "agent_002": "busy",
            "agent_003": "available"
        }
        mock_redis.client.get.return_value = '["sales", "support"]'
        
        router = CallRouter(redis_service=mock_redis)
        
        result = await router._find_available_agents({}, ["sales"])
        
        # Should return available agents with required skills
        assert "agent_001" in result or "agent_003" in result
        mock_redis.get_all_agents_availability.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_available_agents_skill_matching(self):
        """Test agent skill matching.
        
        **Validates: Requirement 4.4** - Match agent skills with routing requirements
        """
        # Mock Redis service
        mock_redis = AsyncMock()
        mock_redis.get_all_agents_availability.return_value = {
            "agent_001": "available",
            "agent_002": "available",
            "agent_003": "available"
        }
        
        # Mock different skills for each agent
        async def mock_get_skills(key):
            if "agent_001" in key:
                return '["sales", "support"]'
            elif "agent_002" in key:
                return '["support", "technical"]'
            elif "agent_003" in key:
                return '["sales", "technical"]'
            return None
        
        mock_redis.client.get.side_effect = mock_get_skills
        
        router = CallRouter(redis_service=mock_redis)
        
        # Find agents with sales skill
        result = await router._find_available_agents({}, ["sales"])
        
        # Should only return agents with sales skill
        assert "agent_001" in result
        assert "agent_003" in result
        assert "agent_002" not in result
    
    @pytest.mark.asyncio
    async def test_find_available_agents_multiple_required_skills(self):
        """Test agent matching with multiple required skills.
        
        **Validates: Requirement 4.4** - Match agent skills with routing requirements
        """
        # Mock Redis service
        mock_redis = AsyncMock()
        mock_redis.get_all_agents_availability.return_value = {
            "agent_001": "available",
            "agent_002": "available",
            "agent_003": "available"
        }
        
        # Mock different skills for each agent
        async def mock_get_skills(key):
            if "agent_001" in key:
                return '["sales", "support", "technical"]'
            elif "agent_002" in key:
                return '["support", "technical"]'
            elif "agent_003" in key:
                return '["sales"]'
            return None
        
        mock_redis.client.get.side_effect = mock_get_skills
        
        router = CallRouter(redis_service=mock_redis)
        
        # Find agents with both sales AND technical skills
        result = await router._find_available_agents({}, ["sales", "technical"])
        
        # Should only return agent_001 who has both skills
        assert "agent_001" in result
        assert "agent_002" not in result
        assert "agent_003" not in result
    
    @pytest.mark.asyncio
    async def test_find_available_agents_no_required_skills(self):
        """Test agent matching when no skills required.
        
        **Validates: Requirement 4.4** - Match agent skills with routing requirements
        """
        # Mock Redis service
        mock_redis = AsyncMock()
        mock_redis.get_all_agents_availability.return_value = {
            "agent_001": "available",
            "agent_002": "available"
        }
        mock_redis.client.get.return_value = '[]'
        
        router = CallRouter(redis_service=mock_redis)
        
        # Find agents with no required skills
        result = await router._find_available_agents({}, [])
        
        # Should return all available agents
        assert "agent_001" in result
        assert "agent_002" in result
    
    @pytest.mark.asyncio
    async def test_find_available_agents_redis_failure_fallback(self):
        """Test fallback to provided availability when Redis fails.
        
        **Validates: Requirement 4.2** - Graceful fallback on Redis failure
        """
        # Mock Redis service that raises exception
        mock_redis = AsyncMock()
        mock_redis.get_all_agents_availability.side_effect = Exception("Redis connection failed")
        
        router = CallRouter(redis_service=mock_redis)
        
        # Provide fallback availability
        fallback_availability = {
            "agent_001": True,
            "agent_002": False,
            "agent_003": True
        }
        
        result = await router._find_available_agents(fallback_availability, ["sales"])
        
        # Should use fallback and return available agents
        assert "agent_001" in result
        assert "agent_003" in result
        assert "agent_002" not in result
    
    @pytest.mark.asyncio
    async def test_find_available_agents_no_redis_service(self):
        """Test agent finding without Redis service (fallback mode)."""
        router = CallRouter(redis_service=None)
        
        availability = {
            "agent_001": True,
            "agent_002": False,
            "agent_003": True
        }
        
        result = await router._find_available_agents(availability, ["sales"])
        
        # Should use provided availability
        assert "agent_001" in result
        assert "agent_003" in result
        assert "agent_002" not in result
    
    @pytest.mark.asyncio
    async def test_get_agent_skills(self):
        """Test retrieving agent skills from Redis."""
        # Mock Redis service
        mock_redis = AsyncMock()
        mock_redis.client.get.return_value = '["sales", "support", "technical"]'
        
        router = CallRouter(redis_service=mock_redis)
        
        skills = await router._get_agent_skills("agent_001")
        
        assert skills == ["sales", "support", "technical"]
        mock_redis.client.get.assert_called_once_with("agent:agent_001:skills")
    
    @pytest.mark.asyncio
    async def test_get_agent_skills_not_found(self):
        """Test retrieving agent skills when not found in Redis."""
        # Mock Redis service
        mock_redis = AsyncMock()
        mock_redis.client.get.return_value = None
        
        router = CallRouter(redis_service=mock_redis)
        
        skills = await router._get_agent_skills("agent_001")
        
        assert skills == []
    
    @pytest.mark.asyncio
    async def test_get_agent_skills_no_redis(self):
        """Test retrieving agent skills without Redis service."""
        router = CallRouter(redis_service=None)
        
        skills = await router._get_agent_skills("agent_001")
        
        assert skills == []
    
    def test_has_required_skills_all_match(self):
        """Test skill matching when agent has all required skills."""
        router = CallRouter()
        
        agent_skills = ["sales", "support", "technical"]
        required_skills = ["sales", "support"]
        
        result = router._has_required_skills(agent_skills, required_skills)
        
        assert result is True
    
    def test_has_required_skills_partial_match(self):
        """Test skill matching when agent has only some required skills."""
        router = CallRouter()
        
        agent_skills = ["sales", "support"]
        required_skills = ["sales", "technical"]
        
        result = router._has_required_skills(agent_skills, required_skills)
        
        assert result is False
    
    def test_has_required_skills_no_match(self):
        """Test skill matching when agent has no required skills."""
        router = CallRouter()
        
        agent_skills = ["support", "technical"]
        required_skills = ["sales"]
        
        result = router._has_required_skills(agent_skills, required_skills)
        
        assert result is False
    
    def test_has_required_skills_case_insensitive(self):
        """Test skill matching is case-insensitive."""
        router = CallRouter()
        
        agent_skills = ["Sales", "SUPPORT", "Technical"]
        required_skills = ["sales", "support"]
        
        result = router._has_required_skills(agent_skills, required_skills)
        
        assert result is True
    
    def test_has_required_skills_no_requirements(self):
        """Test skill matching when no skills required."""
        router = CallRouter()
        
        agent_skills = ["sales"]
        required_skills = []
        
        result = router._has_required_skills(agent_skills, required_skills)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_route_call_with_redis_agent_availability(self):
        """Test complete routing flow with Redis agent availability.
        
        **Validates: Requirements 4.2, 4.4** - Route calls based on agent availability and skills
        """
        # Mock Redis service
        mock_redis = AsyncMock()
        mock_redis.get_all_agents_availability.return_value = {
            "agent_001": "available",
            "agent_002": "busy"
        }
        mock_redis.client.get.return_value = '["sales", "support"]'
        
        router = CallRouter(redis_service=mock_redis)
        
        rule = RoutingRule(
            intent=Intent.SALES_INQUIRY,
            priority=5,
            business_hours_only=False,
            agent_skills_required=["sales"],
            max_queue_time_seconds=300
        )
        router.add_routing_rule(rule)
        
        call_context = CallContext(
            call_id="test-123",
            caller_phone="+1234567890",
            intent=Intent.SALES_INQUIRY
        )
        
        result = await router.route_call(call_context, {})
        
        # Should route to available agent with sales skill
        assert result == "transfer_to_agent:agent_001"
    
    @pytest.mark.asyncio
    async def test_route_call_high_value_lead_priority_with_redis(self):
        """Test high-value lead priority routing with Redis.
        
        **Validates: Requirement 4.4** - Priority routing for high-value leads
        """
        # Mock Redis service with multiple available agents
        mock_redis = AsyncMock()
        mock_redis.get_all_agents_availability.return_value = {
            "agent_001": "available",
            "agent_002": "available",
            "agent_003": "available"
        }
        mock_redis.client.get.return_value = '["sales"]'
        
        router = CallRouter(redis_service=mock_redis)
        
        rule = RoutingRule(
            intent=Intent.SALES_INQUIRY,
            priority=5,
            business_hours_only=False,
            agent_skills_required=["sales"],
            max_queue_time_seconds=300
        )
        router.add_routing_rule(rule)
        
        # High-value lead (score >= 7)
        call_context = CallContext(
            call_id="test-123",
            caller_phone="+1234567890",
            intent=Intent.SALES_INQUIRY,
            lead_data={"lead_score": 9}
        )
        
        result = await router.route_call(call_context, {})
        
        # Should route to first available agent (priority routing)
        assert result.startswith("transfer_to_agent:")
        assert "agent_001" in result or "agent_002" in result or "agent_003" in result


class TestCallTransferWithContextHandoff:
    """Test call transfer with context handoff functionality.
    
    **Validates: Requirement 4.5** - Transfer calls to live agents with full context handoff
    """
    
    @pytest.mark.asyncio
    async def test_transfer_to_agent_success(self):
        """Test successful call transfer with context preparation.
        
        **Validates: Requirement 4.5** - Transfer calls with full context
        """
        # Mock Redis service
        mock_redis = AsyncMock()
        mock_redis.client.setex = AsyncMock(return_value=True)
        
        router = CallRouter(redis_service=mock_redis)
        
        # Create call context with comprehensive data
        call_context = CallContext(
            call_id="test-call-123",
            caller_phone="+1234567890",
            caller_name="John Doe",
            intent=Intent.SALES_INQUIRY,
            intent_confidence=0.85,
            lead_data={
                "lead_score": 8,
                "name": "John Doe",
                "email": "john@example.com",
                "inquiry_details": "Interested in premium package",
                "budget_indication": "$5000",
                "timeline": "Next quarter"
            },
            conversation_history=[
                {"speaker": "caller", "text": "I want to buy your product", "timestamp": "2024-01-15T10:00:00"},
                {"speaker": "assistant", "text": "Great! Let me help you with that", "timestamp": "2024-01-15T10:00:05"}
            ]
        )
        
        result = await router.transfer_to_agent(call_context, "agent_001", "+15551234567")
        
        assert result["status"] == "success"
        assert result["agent_id"] == "agent_001"
        assert result["transfer_phone"] == "+15551234567"
        assert "context_key" in result
        assert result["context_key"] == "transfer_context:test-call-123:agent_001"
        
        # Verify context was stored in Redis
        mock_redis.client.setex.assert_called_once()
        call_args = mock_redis.client.setex.call_args
        assert call_args[0][0] == "transfer_context:test-call-123:agent_001"
        assert call_args[0][1] == 3600  # 1 hour TTL
    
    @pytest.mark.asyncio
    async def test_transfer_to_agent_context_summary_structure(self):
        """Test that context summary contains all required information.
        
        **Validates: Requirement 4.5** - Provide agent with caller history and intent
        """
        mock_redis = AsyncMock()
        mock_redis.client.setex = AsyncMock(return_value=True)
        
        router = CallRouter(redis_service=mock_redis)
        
        call_context = CallContext(
            call_id="test-call-123",
            caller_phone="+1234567890",
            caller_name="Jane Smith",
            intent=Intent.SUPPORT_REQUEST,
            intent_confidence=0.92,
            lead_data={
                "lead_score": 6,
                "name": "Jane Smith",
                "inquiry_details": "Need help with installation"
            },
            conversation_history=[
                {"speaker": "caller", "text": "I need support", "timestamp": "2024-01-15T10:00:00"}
            ]
        )
        
        result = await router.transfer_to_agent(call_context, "agent_002")
        
        assert result["status"] == "success"
        context_summary = result["context_summary"]
        
        # Verify caller info
        assert context_summary["caller_info"]["phone"] == "+1234567890"
        assert context_summary["caller_info"]["name"] == "Jane Smith"
        assert context_summary["caller_info"]["language"] == "en"
        
        # Verify intent info
        assert context_summary["intent_info"]["intent"] == "support_request"
        assert context_summary["intent_info"]["confidence"] == 0.92
        assert "description" in context_summary["intent_info"]
        
        # Verify lead info
        assert context_summary["lead_info"]["lead_score"] == 6
        assert context_summary["lead_info"]["name"] == "Jane Smith"
        assert context_summary["lead_info"]["inquiry_details"] == "Need help with installation"
        
        # Verify conversation summary
        assert len(context_summary["conversation_summary"]) == 1
        assert context_summary["conversation_summary"][0]["speaker"] == "caller"
        assert context_summary["conversation_summary"][0]["text"] == "I need support"
        
        # Verify metadata
        assert context_summary["call_id"] == "test-call-123"
        assert "transfer_timestamp" in context_summary
    
    @pytest.mark.asyncio
    async def test_transfer_to_agent_without_lead_data(self):
        """Test transfer when no lead data is available."""
        mock_redis = AsyncMock()
        mock_redis.client.setex = AsyncMock(return_value=True)
        
        router = CallRouter(redis_service=mock_redis)
        
        call_context = CallContext(
            call_id="test-call-123",
            caller_phone="+1234567890",
            intent=Intent.GENERAL_INQUIRY,
            intent_confidence=0.75
        )
        
        result = await router.transfer_to_agent(call_context, "agent_001")
        
        assert result["status"] == "success"
        context_summary = result["context_summary"]
        
        # Lead info should be None when no lead data
        assert context_summary["lead_info"] is None
    
    @pytest.mark.asyncio
    async def test_transfer_to_agent_with_appointment_data(self):
        """Test transfer includes appointment information when available."""
        mock_redis = AsyncMock()
        mock_redis.client.setex = AsyncMock(return_value=True)
        
        router = CallRouter(redis_service=mock_redis)
        
        call_context = CallContext(
            call_id="test-call-123",
            caller_phone="+1234567890",
            intent=Intent.APPOINTMENT_BOOKING,
            intent_confidence=0.88,
            appointment_data={
                "service_type": "Consultation",
                "appointment_datetime": "2024-01-20T14:00:00",
                "duration_minutes": 60,
                "notes": "First time customer"
            }
        )
        
        result = await router.transfer_to_agent(call_context, "agent_001")
        
        assert result["status"] == "success"
        context_summary = result["context_summary"]
        
        # Verify appointment info
        assert context_summary["appointment_info"]["service_type"] == "Consultation"
        assert context_summary["appointment_info"]["duration_minutes"] == 60
        assert context_summary["appointment_info"]["notes"] == "First time customer"
    
    @pytest.mark.asyncio
    async def test_transfer_to_agent_conversation_history_limit(self):
        """Test that conversation summary is limited to last 10 turns."""
        mock_redis = AsyncMock()
        mock_redis.client.setex = AsyncMock(return_value=True)
        
        router = CallRouter(redis_service=mock_redis)
        
        # Create 15 conversation turns
        conversation_history = [
            {"speaker": "caller", "text": f"Message {i}", "timestamp": f"2024-01-15T10:00:{i:02d}"}
            for i in range(15)
        ]
        
        call_context = CallContext(
            call_id="test-call-123",
            caller_phone="+1234567890",
            intent=Intent.SALES_INQUIRY,
            conversation_history=conversation_history
        )
        
        result = await router.transfer_to_agent(call_context, "agent_001")
        
        assert result["status"] == "success"
        context_summary = result["context_summary"]
        
        # Should only include last 10 turns
        assert len(context_summary["conversation_summary"]) == 10
        # Should be the most recent turns (5-14)
        assert context_summary["conversation_summary"][0]["text"] == "Message 5"
        assert context_summary["conversation_summary"][-1]["text"] == "Message 14"
    
    @pytest.mark.asyncio
    async def test_transfer_to_agent_invalid_call_context(self):
        """Test transfer fails with invalid call context."""
        router = CallRouter()
        
        with pytest.raises(ValueError, match="call_context cannot be None"):
            await router.transfer_to_agent(None, "agent_001")
    
    @pytest.mark.asyncio
    async def test_transfer_to_agent_empty_agent_id(self):
        """Test transfer fails with empty agent ID."""
        router = CallRouter()
        
        call_context = CallContext(
            call_id="test-call-123",
            caller_phone="+1234567890"
        )
        
        with pytest.raises(ValueError, match="agent_id cannot be empty"):
            await router.transfer_to_agent(call_context, "")
    
    @pytest.mark.asyncio
    async def test_transfer_to_agent_without_redis(self):
        """Test transfer works without Redis service (logs warning)."""
        router = CallRouter(redis_service=None)
        
        call_context = CallContext(
            call_id="test-call-123",
            caller_phone="+1234567890",
            intent=Intent.SALES_INQUIRY
        )
        
        result = await router.transfer_to_agent(call_context, "agent_001")
        
        # Should still succeed but log warning
        assert result["status"] == "success"
        assert result["agent_id"] == "agent_001"
    
    @pytest.mark.asyncio
    async def test_transfer_to_agent_redis_failure(self):
        """Test transfer handles Redis failures gracefully."""
        # Mock Redis service that raises exception
        mock_redis = AsyncMock()
        mock_redis.client.setex = AsyncMock(side_effect=Exception("Redis connection failed"))
        
        router = CallRouter(redis_service=mock_redis)
        
        call_context = CallContext(
            call_id="test-call-123",
            caller_phone="+1234567890",
            intent=Intent.SALES_INQUIRY
        )
        
        result = await router.transfer_to_agent(call_context, "agent_001")
        
        # Should return failure status
        assert result["status"] == "failed"
        assert result["agent_id"] == "agent_001"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_transfer_context_success(self):
        """Test retrieving transfer context for agent.
        
        **Validates: Requirement 4.5** - Provide agent with caller history and intent
        """
        # Mock Redis service
        mock_redis = AsyncMock()
        
        # Mock context data
        context_data = {
            "call_id": "test-call-123",
            "caller_info": {
                "phone": "+1234567890",
                "name": "John Doe"
            },
            "intent_info": {
                "intent": "sales_inquiry",
                "confidence": 0.85
            }
        }
        
        import json
        mock_redis.client.get = AsyncMock(return_value=json.dumps(context_data))
        
        router = CallRouter(redis_service=mock_redis)
        
        result = await router.get_transfer_context("test-call-123", "agent_001")
        
        assert result is not None
        assert result["call_id"] == "test-call-123"
        assert result["caller_info"]["phone"] == "+1234567890"
        assert result["intent_info"]["intent"] == "sales_inquiry"
        
        # Verify correct Redis key was used
        mock_redis.client.get.assert_called_once_with("transfer_context:test-call-123:agent_001")
    
    @pytest.mark.asyncio
    async def test_get_transfer_context_not_found(self):
        """Test retrieving transfer context when not found."""
        mock_redis = AsyncMock()
        mock_redis.client.get = AsyncMock(return_value=None)
        
        router = CallRouter(redis_service=mock_redis)
        
        result = await router.get_transfer_context("test-call-123", "agent_001")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_transfer_context_without_redis(self):
        """Test retrieving transfer context without Redis service."""
        router = CallRouter(redis_service=None)
        
        result = await router.get_transfer_context("test-call-123", "agent_001")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_transfer_context_redis_failure(self):
        """Test retrieving transfer context handles Redis failures."""
        mock_redis = AsyncMock()
        mock_redis.client.get = AsyncMock(side_effect=Exception("Redis connection failed"))
        
        router = CallRouter(redis_service=mock_redis)
        
        result = await router.get_transfer_context("test-call-123", "agent_001")
        
        assert result is None
    
    def test_get_intent_description(self):
        """Test getting human-readable intent descriptions."""
        router = CallRouter()
        
        # Test all intent types
        assert "purchasing" in router._get_intent_description(Intent.SALES_INQUIRY).lower()
        assert "support" in router._get_intent_description(Intent.SUPPORT_REQUEST).lower()
        assert "appointment" in router._get_intent_description(Intent.APPOINTMENT_BOOKING).lower()
        assert "complaint" in router._get_intent_description(Intent.COMPLAINT).lower()
        assert "general" in router._get_intent_description(Intent.GENERAL_INQUIRY).lower()
        assert "could not be determined" in router._get_intent_description(Intent.UNKNOWN).lower()
        
        # Test None intent
        assert "No intent detected" in router._get_intent_description(None)
    
    def test_serialize_context(self):
        """Test context serialization to JSON."""
        router = CallRouter()
        
        context = {
            "call_id": "test-123",
            "caller_info": {"phone": "+1234567890"},
            "intent_info": {"intent": "sales_inquiry"}
        }
        
        result = router._serialize_context(context)
        
        assert isinstance(result, str)
        
        # Verify it's valid JSON
        import json
        parsed = json.loads(result)
        assert parsed["call_id"] == "test-123"
        assert parsed["caller_info"]["phone"] == "+1234567890"
    
    @pytest.mark.asyncio
    async def test_end_to_end_transfer_and_retrieve(self):
        """Test complete transfer flow: prepare context, store, and retrieve.
        
        **Validates: Requirement 4.5** - Complete context handoff workflow
        """
        # Use real-like mock that stores data
        stored_data = {}
        
        async def mock_setex(key, ttl, value):
            stored_data[key] = value
            return True
        
        async def mock_get(key):
            return stored_data.get(key)
        
        mock_redis = AsyncMock()
        mock_redis.client.setex = mock_setex
        mock_redis.client.get = mock_get
        
        router = CallRouter(redis_service=mock_redis)
        
        # Create comprehensive call context
        call_context = CallContext(
            call_id="test-call-456",
            caller_phone="+1234567890",
            caller_name="Alice Johnson",
            intent=Intent.SALES_INQUIRY,
            intent_confidence=0.90,
            lead_data={
                "lead_score": 9,
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "inquiry_details": "Enterprise package inquiry",
                "budget_indication": "$50000",
                "timeline": "Immediate"
            },
            conversation_history=[
                {"speaker": "caller", "text": "I need enterprise solution", "timestamp": "2024-01-15T10:00:00"},
                {"speaker": "assistant", "text": "Let me connect you with our sales team", "timestamp": "2024-01-15T10:00:05"}
            ]
        )
        
        # Transfer to agent
        transfer_result = await router.transfer_to_agent(call_context, "agent_sales_001")
        
        assert transfer_result["status"] == "success"
        assert transfer_result["agent_id"] == "agent_sales_001"
        
        # Agent retrieves context
        retrieved_context = await router.get_transfer_context("test-call-456", "agent_sales_001")
        
        assert retrieved_context is not None
        assert retrieved_context["call_id"] == "test-call-456"
        assert retrieved_context["caller_info"]["name"] == "Alice Johnson"
        assert retrieved_context["intent_info"]["intent"] == "sales_inquiry"
        assert retrieved_context["lead_info"]["lead_score"] == 9
        assert len(retrieved_context["conversation_summary"]) == 2
