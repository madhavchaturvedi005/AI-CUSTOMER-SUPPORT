# CallManager Documentation

## Overview

The `CallManager` class manages the complete call lifecycle for the AI Voice Automation system. It provides integration with PostgreSQL for persistence and Redis for session caching.

## Features

- **Call Lifecycle Management**: Handles call initiation, answering, and completion
- **State Transitions**: Manages call state transitions (initiated → in_progress → completed)
- **Database Integration**: Persists call records to PostgreSQL
- **Cache Integration**: Caches call context in Redis for fast access
- **Conversation Tracking**: Maintains conversation history throughout the call
- **Intent Management**: Updates and tracks caller intent with confidence scores
- **Caller History**: Retrieves previous call history for returning callers

## Requirements

Validates the following requirements:
- **1.1**: Automatic call answering
- **1.2**: Professional greeting playback
- **1.4**: 24/7 call acceptance
- **1.5**: Independent handling of multiple simultaneous calls
- **18.1**: Support for 50+ concurrent calls

## Installation

1. Install dependencies:
```bash
pip install asyncpg redis
```

2. Configure environment variables in `.env`:
```bash
# PostgreSQL Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_automation
DB_USER=postgres
DB_PASSWORD=your_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

3. Run database migrations:
```bash
python3 migrations/run_migration.py 001_initial_schema.sql
```

## Usage

### Initialize Services

```python
from database import initialize_database, shutdown_database
from redis_service import initialize_redis, shutdown_redis
from call_manager import CallManager

# Initialize database and Redis
db = await initialize_database()
redis = await initialize_redis()

# Create CallManager instance
call_manager = CallManager(database=db, redis=redis)
```

### Initiate a Call

```python
from models import Language

# Initiate a new inbound call
context = await call_manager.initiate_call(
    call_sid="CA1234567890",
    caller_phone="+1234567890",
    direction="inbound",
    caller_name="John Doe",
    language=Language.ENGLISH
)

print(f"Call initiated with ID: {context.call_id}")
```

### Answer a Call

```python
# Mark call as answered (transitions to in_progress)
await call_manager.answer_call(call_sid="CA1234567890")
```

### Update Call Intent

```python
from models import Intent

# Update detected intent
await call_manager.update_call_intent(
    call_sid="CA1234567890",
    intent=Intent.SALES_INQUIRY,
    confidence=0.85
)
```

### Track Conversation

```python
# Add conversation turns
await call_manager.add_conversation_turn(
    call_sid="CA1234567890",
    speaker="caller",
    text="Hello, I need help with my order"
)

await call_manager.add_conversation_turn(
    call_sid="CA1234567890",
    speaker="assistant",
    text="I'd be happy to help you with your order. Can you provide your order number?"
)
```

### Complete a Call

```python
# Complete call with recording URLs
await call_manager.complete_call(
    call_sid="CA1234567890",
    recording_url="https://example.com/recordings/call123.wav",
    transcript_url="https://example.com/transcripts/call123.json"
)
```

### Handle Call Failures

```python
# Mark call as failed
await call_manager.fail_call(
    call_sid="CA1234567890",
    error_message="Connection lost to OpenAI API"
)
```

### Retrieve Call Context

```python
# Get current call context
context = await call_manager.get_call_context(call_sid="CA1234567890")

if context:
    print(f"Caller: {context.caller_phone}")
    print(f"Intent: {context.intent}")
    print(f"Confidence: {context.intent_confidence}")
    print(f"Conversation turns: {len(context.conversation_history)}")
```

### Get Caller History

```python
# Retrieve previous calls from a caller
history = await call_manager.get_caller_history(
    caller_phone="+1234567890",
    limit=10
)

for call in history:
    print(f"Call {call['id']}: {call['status']} - {call['started_at']}")
```

## Architecture

### Database Schema

The CallManager uses the following PostgreSQL tables:

- **calls**: Stores call records with metadata, status, and intent
- **transcripts**: Stores conversation transcripts (used by TranscriptService)
- **leads**: Stores captured lead information (used by LeadManager)
- **appointments**: Stores scheduled appointments (used by AppointmentManager)

### Redis Cache Structure

Session state is cached with the following structure:

```python
{
    "call_id": "uuid",
    "caller_phone": "+1234567890",
    "caller_name": "John Doe",
    "language": "en",
    "intent": "sales_inquiry",
    "intent_confidence": 0.85,
    "conversation_history": [
        {"speaker": "caller", "text": "Hello", "timestamp_ms": 1234567890}
    ],
    "lead_data": {...},
    "appointment_data": {...},
    "metadata": {...},
    "created_at": "2024-01-01T00:00:00+00:00"
}
```

Cache keys:
- `session:{call_sid}` - Call context (TTL: 1 hour)
- `caller:{phone_number}` - Caller history (TTL: 180 days)

## State Transitions

```
initiated → in_progress → completed
                       → failed
                       → no_answer
```

- **initiated**: Call received, record created
- **in_progress**: Call answered, conversation active
- **completed**: Call ended successfully
- **failed**: Call failed due to error
- **no_answer**: Call not answered (future use)

## Error Handling

The CallManager raises `ValueError` exceptions when:
- Call context is not found in cache
- Invalid call_sid is provided

Always wrap CallManager operations in try-except blocks:

```python
try:
    await call_manager.answer_call(call_sid)
except ValueError as e:
    print(f"Error: {e}")
    # Handle error appropriately
```

## Testing

Run unit tests:

```bash
python3 -m pytest test_call_manager.py -v
```

All tests use mocked dependencies (DatabaseService and RedisService) to ensure fast, isolated testing.

## Performance Considerations

- **Connection Pooling**: Database uses connection pool (min: 10, max: 50)
- **Redis Caching**: Fast session state retrieval with 1-hour TTL
- **Concurrent Calls**: Supports 50+ concurrent calls without performance degradation
- **Async Operations**: All operations are async for non-blocking I/O

## Integration with Other Services

The CallManager is designed to work with:

- **IntentDetector**: Updates call intent based on conversation analysis
- **CallRouter**: Uses intent to route calls to appropriate handlers
- **TranscriptService**: Provides conversation history for transcript generation
- **LeadManager**: Stores lead data in call context
- **AppointmentManager**: Stores appointment data in call context
- **AnalyticsService**: Provides call metrics for reporting

## Cleanup

Always cleanup resources when shutting down:

```python
# Shutdown services
await shutdown_redis()
await shutdown_database()
```

## Future Enhancements

- Support for outbound calls
- Call transfer functionality
- Call recording integration
- Real-time call monitoring
- Call queuing for high volume
