# Call Transfer with Context Handoff - Usage Example

This document demonstrates how to use the call transfer functionality with full context handoff in the AI Voice Automation system.

## Overview

The `CallRouter` class now supports transferring calls to live agents with comprehensive context handoff. When a call is transferred, the system prepares a detailed context summary including:

- Caller information (phone, name, language)
- Detected intent and confidence score
- Lead data (if captured)
- Appointment data (if scheduled)
- Recent conversation history (last 10 turns)
- Metadata and timestamps

This context is stored in Redis and can be retrieved by the agent to provide seamless customer service.

## Basic Usage

```python
from call_router import CallRouter
from models import CallContext, Intent
from redis_service import RedisService

# Initialize Redis service
redis_service = RedisService(host="localhost", port=6379)
await redis_service.connect()

# Initialize call router
router = CallRouter(redis_service=redis_service)

# Create call context with comprehensive data
call_context = CallContext(
    call_id="CA1234567890abcdef",
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
        {
            "speaker": "caller",
            "text": "I want to buy your premium package",
            "timestamp": "2024-01-15T10:00:00"
        },
        {
            "speaker": "assistant",
            "text": "Great! Let me connect you with our sales team",
            "timestamp": "2024-01-15T10:00:05"
        }
    ]
)

# Transfer call to agent
transfer_result = await router.transfer_to_agent(
    call_context=call_context,
    agent_id="agent_sales_001",
    transfer_phone="+15551234567"  # Optional: Twilio transfer number
)

if transfer_result["status"] == "success":
    print(f"Call transferred to {transfer_result['agent_id']}")
    print(f"Context stored at: {transfer_result['context_key']}")
else:
    print(f"Transfer failed: {transfer_result['error']}")
```

## Agent Retrieving Context

When an agent receives a transferred call, they can retrieve the context:

```python
# Agent retrieves context for the call
context = await router.get_transfer_context(
    call_id="CA1234567890abcdef",
    agent_id="agent_sales_001"
)

if context:
    # Access caller information
    print(f"Caller: {context['caller_info']['name']}")
    print(f"Phone: {context['caller_info']['phone']}")
    print(f"Language: {context['caller_info']['language']}")
    
    # Access intent information
    print(f"Intent: {context['intent_info']['intent']}")
    print(f"Confidence: {context['intent_info']['confidence']}")
    print(f"Description: {context['intent_info']['description']}")
    
    # Access lead information (if available)
    if context['lead_info']:
        print(f"Lead Score: {context['lead_info']['lead_score']}")
        print(f"Budget: {context['lead_info']['budget_indication']}")
        print(f"Timeline: {context['lead_info']['timeline']}")
    
    # Access conversation history
    print("\nRecent Conversation:")
    for turn in context['conversation_summary']:
        print(f"{turn['speaker']}: {turn['text']}")
else:
    print("Context not found")
```

## Context Summary Structure

The context summary includes the following fields:

```python
{
    "call_id": "CA1234567890abcdef",
    "caller_info": {
        "phone": "+1234567890",
        "name": "John Doe",
        "language": "en"
    },
    "intent_info": {
        "intent": "sales_inquiry",
        "confidence": 0.85,
        "description": "Customer is interested in purchasing products or services"
    },
    "lead_info": {
        "lead_score": 8,
        "name": "John Doe",
        "email": "john@example.com",
        "inquiry_details": "Interested in premium package",
        "budget_indication": "$5000",
        "timeline": "Next quarter",
        "decision_authority": False
    },
    "appointment_info": None,  # Or appointment details if scheduled
    "conversation_summary": [
        {
            "speaker": "caller",
            "text": "I want to buy your premium package",
            "timestamp": "2024-01-15T10:00:00"
        },
        {
            "speaker": "assistant",
            "text": "Great! Let me connect you with our sales team",
            "timestamp": "2024-01-15T10:00:05"
        }
    ],
    "metadata": {},
    "created_at": "2024-01-15T10:00:00+00:00",
    "transfer_timestamp": "2024-01-15T10:00:10+00:00"
}
```

## Integration with Call Routing

The transfer functionality integrates seamlessly with the existing routing logic:

```python
# Add routing rule for sales inquiries
from call_router import RoutingRule

rule = RoutingRule(
    intent=Intent.SALES_INQUIRY,
    priority=5,
    business_hours_only=True,
    agent_skills_required=["sales"],
    max_queue_time_seconds=300
)
router.add_routing_rule(rule)

# Route call (automatically transfers if agent available)
routing_decision = await router.route_call(
    call_context=call_context,
    agent_availability={"agent_sales_001": True}
)

if routing_decision.startswith("transfer_to_agent:"):
    agent_id = routing_decision.split(":")[1]
    
    # Perform transfer with context handoff
    transfer_result = await router.transfer_to_agent(
        call_context=call_context,
        agent_id=agent_id
    )
```

## Error Handling

The transfer functionality handles errors gracefully:

```python
# Transfer without Redis (logs warning but continues)
router_no_redis = CallRouter(redis_service=None)
result = await router_no_redis.transfer_to_agent(call_context, "agent_001")
# Returns success but context won't be stored

# Transfer with Redis failure
result = await router.transfer_to_agent(call_context, "agent_001")
if result["status"] == "failed":
    print(f"Transfer failed: {result['error']}")
    # Implement fallback logic (e.g., voicemail, retry)
```

## Redis Storage

Context is stored in Redis with:
- **Key format**: `transfer_context:{call_id}:{agent_id}`
- **TTL**: 1 hour (3600 seconds)
- **Format**: JSON string

This ensures agents have sufficient time to access the context while preventing stale data accumulation.

## Requirements Validation

This implementation validates:
- **Requirement 4.5**: Transfer calls to live agents with full context handoff
  - Prepares comprehensive context summary
  - Stores context in Redis for agent access
  - Provides caller history, intent, and lead data
  - Returns transfer status and agent ID

## Testing

Comprehensive unit tests are available in `test_call_router.py`:
- Test successful transfer with context preparation
- Test context summary structure and completeness
- Test transfer without lead/appointment data
- Test conversation history limiting (last 10 turns)
- Test error handling (invalid inputs, Redis failures)
- Test context retrieval by agents
- Test end-to-end transfer and retrieve workflow

Run tests with:
```bash
python3 -m pytest test_call_router.py::TestCallTransferWithContextHandoff -v
```
