# Conversation History Retrieval

## Overview

The conversation history retrieval feature enables the AI Voice Automation system to recognize returning callers and provide personalized experiences based on their previous interactions. This feature implements Requirements 9.1, 9.2, and 9.3 from the system specification.

## Features

### 1. Automatic Caller Recognition
- Identifies returning callers by phone number
- Retrieves conversation history from PostgreSQL and Redis cache
- Integrates history into current call context automatically

### 2. Conversation History Storage
- **PostgreSQL**: Stores call records and conversation transcripts
- **Redis Cache**: Provides fast access to recent caller history
- **Retention**: Maintains history for 180 days (configurable)

### 3. Personalized Greetings
- Generates context-aware greetings for returning callers
- References previous interactions when relevant
- Customizes conversation flow based on history

## Architecture

```
┌─────────────────┐
│  Incoming Call  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  CallManager.initiate_call()        │
│  - Creates call record              │
│  - Adds to caller history cache     │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  integrate_conversation_history()   │
│  1. Check Redis for caller history  │
│  2. Query PostgreSQL for calls      │
│  3. Load transcripts for each call  │
│  4. Integrate into CallContext      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  get_conversation_summary()         │
│  - Generates human-readable summary │
│  - Includes previous intents        │
│  - Shows last call date             │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Personalized Conversation          │
│  - AI has context from history      │
│  - Can reference previous calls     │
│  - Provides continuity              │
└─────────────────────────────────────┘
```

## API Reference

### CallManager Methods

#### `retrieve_conversation_history(caller_phone, days=30, max_calls=5)`

Retrieves conversation history for a caller.

**Parameters:**
- `caller_phone` (str): Caller's phone number
- `days` (int): Number of days to look back (default: 30)
- `max_calls` (int): Maximum number of previous calls to retrieve (default: 5)

**Returns:**
- List of dictionaries containing call metadata and transcripts

**Example:**
```python
history = await call_manager.retrieve_conversation_history(
    caller_phone="+1234567890",
    days=60,
    max_calls=10
)

for call in history:
    print(f"Call ID: {call['call_id']}")
    print(f"Intent: {call['intent']}")
    print(f"Transcripts: {len(call['transcripts'])}")
```

#### `integrate_conversation_history(call_sid, caller_phone)`

Integrates conversation history into current call context.

**Parameters:**
- `call_sid` (str): Current call's Twilio call SID
- `caller_phone` (str): Caller's phone number

**Returns:**
- `True` if history was found and integrated
- `False` if no history exists (new caller)

**Example:**
```python
has_history = await call_manager.integrate_conversation_history(
    call_sid="CA123456",
    caller_phone="+1234567890"
)

if has_history:
    print("Returning caller detected!")
else:
    print("New caller")
```

#### `get_conversation_summary(call_sid)`

Generates a human-readable summary of previous conversations.

**Parameters:**
- `call_sid` (str): Current call's Twilio call SID

**Returns:**
- Summary string or `None` if no history available

**Example:**
```python
summary = await call_manager.get_conversation_summary(call_sid)
if summary:
    print(f"Caller History: {summary}")
    # Output: "This caller has contacted us 2 time(s) in the past 30 days. 
    #          Previous topics: sales_inquiry, support_request. 
    #          Last call was on 2024-01-15T10:00:00+00:00."
```

### DatabaseService Methods

#### `get_recent_caller_history(caller_phone, days=30, limit=5)`

Retrieves recent call history from PostgreSQL.

**Parameters:**
- `caller_phone` (str): Caller's phone number
- `days` (int): Number of days to look back
- `limit` (int): Maximum number of records to return

**Returns:**
- List of call records (only completed calls)

#### `get_call_transcripts(call_id)`

Retrieves conversation transcripts for a specific call.

**Parameters:**
- `call_id` (str): Call UUID

**Returns:**
- List of transcript entries ordered by timestamp

## Data Structures

### Call History Entry

```python
{
    "call_id": "uuid-string",
    "started_at": "2024-01-15T10:00:00+00:00",
    "intent": "sales_inquiry",
    "intent_confidence": 0.85,
    "duration_seconds": 120,
    "transcripts": [
        {
            "speaker": "caller",
            "text": "I want to buy your product",
            "timestamp_ms": 1000,
            "language": "en",
            "confidence": 0.95
        },
        {
            "speaker": "assistant",
            "text": "Great! Let me help you with that",
            "timestamp_ms": 2000,
            "language": "en",
            "confidence": 0.98
        }
    ]
}
```

### CallContext Metadata (with history)

```python
{
    "is_returning_caller": True,
    "previous_calls_count": 2,
    "previous_intents": ["sales_inquiry", "support_request"],
    "conversation_history": [
        # List of call history entries
    ]
}
```

## Usage Examples

### Example 1: Basic Integration

```python
from call_manager import CallManager
from database import initialize_database
from redis_service import initialize_redis

# Initialize services
database = await initialize_database()
redis = await initialize_redis()
call_manager = CallManager(database=database, redis=redis)

# Handle incoming call
call_sid = "CA123456"
caller_phone = "+1234567890"

# Initiate call
context = await call_manager.initiate_call(
    call_sid=call_sid,
    caller_phone=caller_phone,
    direction="inbound"
)

# Integrate conversation history
has_history = await call_manager.integrate_conversation_history(
    call_sid=call_sid,
    caller_phone=caller_phone
)

if has_history:
    # Get summary for logging or AI context
    summary = await call_manager.get_conversation_summary(call_sid)
    print(f"Returning caller: {summary}")
```

### Example 2: Personalized Greeting

```python
# Get standard greeting
greeting = await call_manager.get_greeting_message()

# Customize for returning callers
if has_history:
    context = await call_manager.get_call_context(call_sid)
    previous_intents = context.metadata.get("previous_intents", [])
    
    if "sales_inquiry" in previous_intents:
        greeting = (
            "Welcome back! I see you've contacted us before about our products. "
            "How can I help you today?"
        )
    elif "support_request" in previous_intents:
        greeting = (
            "Welcome back! I hope your previous issue was resolved. "
            "What can I help you with today?"
        )

# Play greeting to caller
print(f"Greeting: {greeting}")
```

### Example 3: AI Context Enhancement

```python
# Build AI system prompt with conversation history
ai_system_prompt = "You are a helpful AI assistant."

if has_history:
    summary = await call_manager.get_conversation_summary(call_sid)
    ai_system_prompt += f"\n\nCaller History: {summary}"
    
    # Add specific context from previous conversations
    context = await call_manager.get_call_context(call_sid)
    history = context.metadata.get("conversation_history", [])
    
    if history:
        recent_call = history[0]
        recent_transcripts = recent_call.get("transcripts", [])
        
        # Extract key information from previous conversation
        caller_messages = [
            t["text"] for t in recent_transcripts 
            if t["speaker"] == "caller"
        ]
        
        if caller_messages:
            ai_system_prompt += (
                f"\n\nPrevious conversation highlights: "
                f"{' '.join(caller_messages[:3])}"
            )

# Use enhanced prompt with OpenAI
# openai_client.update_system_prompt(ai_system_prompt)
```

## Configuration

### Default Parameters

```python
# Conversation history retrieval defaults
HISTORY_LOOKBACK_DAYS = 30      # Look back 30 days
MAX_PREVIOUS_CALLS = 5          # Retrieve up to 5 previous calls
HISTORY_RETENTION_DAYS = 180    # Maintain history for 180 days

# Redis cache TTL
CALLER_HISTORY_TTL = 180 * 24 * 3600  # 180 days in seconds
SESSION_STATE_TTL = 3600               # 1 hour in seconds
```

### Environment Variables

```bash
# PostgreSQL configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_automation
DB_USER=postgres
DB_PASSWORD=your_password

# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DB=0
```

## Performance Considerations

### Caching Strategy

1. **Redis Cache**: Stores caller history (call IDs) for fast lookup
2. **Database Queries**: Optimized with indexes on `caller_phone` and `started_at`
3. **Lazy Loading**: Transcripts loaded only when needed

### Query Optimization

```sql
-- Indexes for fast history retrieval
CREATE INDEX idx_calls_caller_phone ON calls(caller_phone);
CREATE INDEX idx_calls_started_at ON calls(started_at);
CREATE INDEX idx_transcripts_call_id ON transcripts(call_id);
```

### Limits

- **Default**: Last 5 calls within 30 days
- **Maximum recommended**: 10 calls within 60 days
- **Transcript size**: Typically 50-200 entries per call

## Testing

Run the conversation history tests:

```bash
python3 -m pytest test_conversation_history.py -v
```

Test coverage includes:
- ✓ Retrieving history with results
- ✓ Retrieving history with no results
- ✓ Integrating history for returning callers
- ✓ Integrating history for new callers
- ✓ Generating conversation summaries
- ✓ Custom parameters (days, max_calls)
- ✓ Database query correctness

## Requirements Mapping

| Requirement | Description | Implementation |
|-------------|-------------|----------------|
| 9.1 | Retrieve previous Call_Context | `retrieve_conversation_history()` |
| 9.2 | Reference previous conversations | `integrate_conversation_history()` |
| 9.3 | Maintain history for 180 days | Redis TTL + PostgreSQL retention |

## Future Enhancements

1. **Semantic Search**: Search conversation history by topic or keywords
2. **Sentiment Analysis**: Track caller sentiment across conversations
3. **Conversation Clustering**: Group similar conversations for insights
4. **Predictive Intent**: Predict intent based on historical patterns
5. **Multi-channel History**: Include email, chat, and SMS interactions

## Troubleshooting

### No history retrieved for known caller

**Possible causes:**
- Caller phone number format mismatch (ensure consistent formatting)
- Previous calls not marked as "completed"
- Redis cache expired and database query failing
- History older than configured retention period

**Solution:**
```python
# Check if calls exist in database
calls = await database.get_caller_history(caller_phone, limit=10)
print(f"Found {len(calls)} calls in database")

# Check Redis cache
call_ids = await redis.get_caller_history(caller_phone, limit=10)
print(f"Found {len(call_ids)} call IDs in Redis")
```

### Slow history retrieval

**Possible causes:**
- Large number of transcripts per call
- Missing database indexes
- Network latency to database/Redis

**Solution:**
- Reduce `max_calls` parameter
- Verify database indexes are created
- Consider caching full history in Redis for frequent callers

## Support

For questions or issues related to conversation history retrieval:
1. Check the test files for usage examples
2. Review the example code in `conversation_history_example.py`
3. Consult the main design document for architecture details
