# Agent Availability Checking - Usage Example

This document demonstrates how to use the enhanced agent availability checking feature in the CallRouter.

## Overview

Task 4.3 implements agent availability checking with the following features:
- Query Redis for real-time agent availability status
- Match agent skills with routing requirements
- Implement priority routing for high-value leads (lead_score >= 7)

## Requirements Validated

- **Requirement 4.2**: Route calls based on business hours and agent availability
- **Requirement 4.4**: Implement priority routing for high-value leads

## Setup

### 1. Initialize Redis Service

```python
from redis_service import initialize_redis

# Initialize Redis connection
redis_service = await initialize_redis(
    host="localhost",
    port=6379,
    password=None  # Optional
)
```

### 2. Set Agent Availability and Skills

```python
# Set agent availability status
await redis_service.set_agent_availability("agent_001", "available")
await redis_service.set_agent_availability("agent_002", "busy")
await redis_service.set_agent_availability("agent_003", "available")

# Set agent skills
await redis_service.set_agent_skills("agent_001", ["sales", "support"])
await redis_service.set_agent_skills("agent_002", ["technical", "support"])
await redis_service.set_agent_skills("agent_003", ["sales", "technical"])
```

### 3. Initialize CallRouter with Redis

```python
from call_router import CallRouter, RoutingRule
from models import Intent

# Create router with Redis service
router = CallRouter(
    redis_service=redis_service,
    timezone="America/New_York"
)

# Add routing rule for sales inquiries
sales_rule = RoutingRule(
    intent=Intent.SALES_INQUIRY,
    priority=5,
    business_hours_only=True,
    agent_skills_required=["sales"],
    max_queue_time_seconds=300
)
router.add_routing_rule(sales_rule)
```

## Usage Examples

### Example 1: Basic Agent Routing

```python
from models import CallContext, Intent

# Create call context
call_context = CallContext(
    call_id="call-123",
    caller_phone="+1234567890",
    intent=Intent.SALES_INQUIRY,
    intent_confidence=0.85
)

# Route the call
routing_decision = await router.route_call(call_context, {})

# Result: "transfer_to_agent:agent_001" or "transfer_to_agent:agent_003"
# (both have "sales" skill and are available)
print(f"Routing decision: {routing_decision}")
```

### Example 2: High-Value Lead Priority Routing

```python
# Create call context with high-value lead
call_context = CallContext(
    call_id="call-456",
    caller_phone="+1234567890",
    intent=Intent.SALES_INQUIRY,
    intent_confidence=0.92,
    lead_data={
        "lead_score": 9,  # High-value lead (>= 7)
        "name": "John Doe",
        "budget_indication": "High"
    }
)

# Route the call - high-value leads get immediate priority
routing_decision = await router.route_call(call_context, {})

# Result: Immediately routes to first available agent with sales skill
print(f"Priority routing: {routing_decision}")
```

### Example 3: Skill Matching

```python
# Add routing rule requiring multiple skills
technical_rule = RoutingRule(
    intent=Intent.SUPPORT_REQUEST,
    priority=3,
    business_hours_only=False,
    agent_skills_required=["technical", "support"],
    max_queue_time_seconds=600
)
router.add_routing_rule(technical_rule)

# Create support request call
call_context = CallContext(
    call_id="call-789",
    caller_phone="+1234567890",
    intent=Intent.SUPPORT_REQUEST,
    intent_confidence=0.88
)

# Route the call
routing_decision = await router.route_call(call_context, {})

# Result: "transfer_to_agent:agent_002" 
# (only agent with both "technical" AND "support" skills)
print(f"Skill-matched routing: {routing_decision}")
```

### Example 4: Fallback When No Agents Available

```python
# Set all agents to busy
await redis_service.set_agent_availability("agent_001", "busy")
await redis_service.set_agent_availability("agent_002", "busy")
await redis_service.set_agent_availability("agent_003", "offline")

# Create call context
call_context = CallContext(
    call_id="call-999",
    caller_phone="+1234567890",
    intent=Intent.SALES_INQUIRY,
    intent_confidence=0.80
)

# Route the call
routing_decision = await router.route_call(call_context, {})

# Result: "ai_continue" (no agents available, continue with AI)
print(f"Fallback routing: {routing_decision}")
```

### Example 5: Graceful Degradation (Redis Failure)

```python
# If Redis fails, the router falls back to provided availability
fallback_availability = {
    "agent_001": True,
    "agent_002": False,
    "agent_003": True
}

# Route with fallback
routing_decision = await router.route_call(call_context, fallback_availability)

# Result: Uses fallback availability if Redis is unavailable
print(f"Fallback routing: {routing_decision}")
```

## Redis Data Structure

### Agent Availability
```
Key: agents:availability
Type: Hash
TTL: 5 minutes

Fields:
  agent_001: "available"
  agent_002: "busy"
  agent_003: "offline"
```

### Agent Skills
```
Key: agent:{agent_id}:skills
Type: String (JSON array)
TTL: 24 hours

Example:
  agent:agent_001:skills = '["sales", "support"]'
  agent:agent_002:skills = '["technical", "support"]'
```

## Skill Matching Logic

The skill matching is **case-insensitive** and requires **all** specified skills:

```python
# Agent has: ["Sales", "SUPPORT", "Technical"]
# Required: ["sales", "support"]
# Result: MATCH ✓

# Agent has: ["sales", "support"]
# Required: ["sales", "technical"]
# Result: NO MATCH ✗ (missing "technical")

# Agent has: []
# Required: []
# Result: MATCH ✓ (no skills required)
```

## Priority Routing Logic

High-value leads (lead_score >= 7) receive priority routing:

1. **High-value lead** (score >= 7):
   - Immediately routes to first available agent with required skills
   - No queueing or waiting

2. **Standard lead** (score < 7):
   - Routes to first available agent with required skills
   - May be queued if all agents busy

## Testing

Run the tests to verify the implementation:

```bash
# Run all call router tests
python3 -m pytest test_call_router.py -v

# Run only agent availability tests
python3 -m pytest test_call_router.py::TestAgentAvailabilityChecking -v
```

## Integration with Existing Code

The enhanced `_find_available_agents()` method is backward compatible:

- **With Redis**: Queries Redis for real-time availability and skills
- **Without Redis**: Falls back to provided `agent_availability` dictionary
- **Redis Failure**: Gracefully falls back to provided availability

No changes required to existing code that doesn't use Redis.
