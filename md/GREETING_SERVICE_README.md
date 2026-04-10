# Greeting Service Documentation

## Overview

The Greeting Service provides business-specific greeting message playback functionality for the AI Voice Automation system. When a call is answered, the system retrieves and plays a customized greeting message within 3 seconds, creating a professional first impression for callers.

**Requirements Addressed:** 1.2, 17.1

## Features

- **Business-Specific Greetings**: Retrieve custom greeting messages from business configuration
- **Default Fallback**: Automatic fallback to default greeting if no custom greeting is configured
- **Fast Playback**: Greeting is played within 3 seconds of call answer
- **OpenAI Integration**: Seamless integration with OpenAI Realtime API for natural voice playback
- **Event Handling**: Automatic handling of greeting completion events

## Architecture

### Components

1. **CallManager.get_greeting_message()**: Retrieves greeting from database configuration
2. **DatabaseService.get_business_config()**: Fetches business configuration from PostgreSQL
3. **send_greeting_message()**: Sends greeting to OpenAI for voice playback
4. **Event Handler**: Handles `response.done` event for greeting completion

### Data Flow

```
Call Answered
    ↓
CallManager.answer_call()
    ↓
CallManager.get_greeting_message(business_id)
    ↓
DatabaseService.get_business_config(business_id)
    ↓
send_greeting_message(openai_ws, greeting_text)
    ↓
OpenAI Realtime API (Text-to-Speech)
    ↓
Audio Streamed to Twilio
    ↓
Caller Hears Greeting
    ↓
response.done Event
    ↓
System Ready for Caller Input
```

## Usage

### Basic Usage

```python
from call_manager import CallManager
from database import DatabaseService
from redis_service import RedisService
from utils import send_greeting_message

# Initialize services
database = DatabaseService()
await database.connect()

redis = RedisService()
await redis.connect()

call_manager = CallManager(database=database, redis=redis)

# Retrieve greeting for a business
business_id = "my_business"
greeting = await call_manager.get_greeting_message(business_id)

# Send greeting to OpenAI for playback
await send_greeting_message(openai_ws, greeting)
```

### Integration with WebSocket Handler

```python
@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    await websocket.accept()
    
    # Connect to OpenAI
    async with websockets.connect(...) as openai_ws:
        await initialize_session(openai_ws)
        
        # Initialize CallManager
        call_manager = CallManager(database, redis)
        
        # Wait for stream start event from Twilio
        # ... (receive call_sid from Twilio)
        
        # Answer call
        await call_manager.answer_call(call_sid)
        
        # Get and send greeting
        greeting = await call_manager.get_greeting_message("default")
        await send_greeting_message(openai_ws, greeting)
        
        # Continue with normal call handling
        await asyncio.gather(
            receive_from_twilio(websocket, openai_ws, state),
            send_to_twilio(websocket, openai_ws, state)
        )
```

## Configuration

### Database Schema

Greeting messages are stored in the `business_config` table:

```sql
CREATE TABLE business_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id VARCHAR(255) UNIQUE NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    greeting_message TEXT,  -- Custom greeting message
    -- ... other fields
);
```

### Setting Custom Greeting

```sql
-- Insert or update business configuration with custom greeting
INSERT INTO business_config (business_id, business_name, greeting_message)
VALUES (
    'my_business',
    'My Business Name',
    'Welcome to My Business! Thank you for calling. How can we assist you today?'
)
ON CONFLICT (business_id) 
DO UPDATE SET greeting_message = EXCLUDED.greeting_message;
```

### Default Greeting

If no custom greeting is configured, the system uses:

```
"Hello! Thank you for calling. I'm an AI assistant here to help you. 
How can I assist you today?"
```

## API Reference

### CallManager.get_greeting_message()

Retrieves business-specific greeting message from configuration.

**Signature:**
```python
async def get_greeting_message(
    self,
    business_id: str = "default"
) -> str
```

**Parameters:**
- `business_id` (str): Business identifier (defaults to "default")

**Returns:**
- `str`: Greeting message text

**Example:**
```python
greeting = await call_manager.get_greeting_message("my_business")
print(greeting)  # "Welcome to My Business! ..."
```

### send_greeting_message()

Sends greeting message to OpenAI for playback to caller.

**Signature:**
```python
async def send_greeting_message(
    openai_ws: websockets.WebSocketClientProtocol,
    greeting_text: str
) -> None
```

**Parameters:**
- `openai_ws`: WebSocket connection to OpenAI
- `greeting_text`: Greeting message text to play

**Example:**
```python
await send_greeting_message(openai_ws, "Welcome to our business!")
```

### DatabaseService.get_business_config()

Retrieves business configuration from database.

**Signature:**
```python
async def get_business_config(
    self,
    business_id: str
) -> Optional[Dict[str, Any]]
```

**Parameters:**
- `business_id` (str): Business identifier

**Returns:**
- `Optional[Dict[str, Any]]`: Business configuration dictionary or None

**Example:**
```python
config = await database.get_business_config("my_business")
if config:
    greeting = config.get("greeting_message")
```

## Event Handling

### response.done Event

The `response.done` event is emitted by OpenAI when the greeting playback completes:

```python
async def send_to_twilio(websocket, openai_ws, state):
    async for openai_message in openai_ws:
        response = json.loads(openai_message)
        
        # Handle greeting completion
        if response.get('type') == 'response.done':
            print("Response completed (greeting or conversation turn finished)")
            # System automatically listens for caller speech via server VAD
```

After the greeting completes, the system automatically transitions to listening mode, ready to receive caller input through server-side Voice Activity Detection (VAD).

## Performance

### Timing Requirements

- **Call Answer**: Within 3 seconds of receiving call (Requirement 1.1)
- **Greeting Playback**: Within 3 seconds of call answer (Requirement 1.2)
- **Total Time to Greeting**: < 6 seconds from call initiation

### Optimization

The greeting service is optimized for fast retrieval:

1. **Database Connection Pooling**: Reuses connections for fast queries
2. **Redis Caching**: Configuration can be cached in Redis (future enhancement)
3. **Async Operations**: Non-blocking database queries
4. **Minimal Processing**: Direct text-to-speech without intermediate processing

## Testing

### Unit Tests

Run the greeting service tests:

```bash
python -m pytest test_greeting.py -v
```

### Test Coverage

- ✅ Custom greeting retrieval
- ✅ Default greeting fallback
- ✅ Missing configuration handling
- ✅ Empty greeting handling
- ✅ Special characters in greeting
- ✅ Multilingual greeting support
- ✅ Performance (< 3 seconds)
- ✅ OpenAI WebSocket integration

### Example Test

```python
@pytest.mark.asyncio
async def test_get_greeting_message_with_custom_greeting(call_manager, mock_database):
    """Test retrieving custom greeting from business configuration."""
    business_id = "test_business"
    custom_greeting = "Welcome to Test Business!"
    mock_database.get_business_config.return_value = {
        "greeting_message": custom_greeting
    }
    
    greeting = await call_manager.get_greeting_message(business_id)
    
    assert greeting == custom_greeting
```

## Best Practices

### 1. Keep Greetings Concise

Greetings should be brief (10-15 seconds) to avoid caller frustration:

```python
# Good
"Welcome to ABC Company! How can I help you today?"

# Too long
"Welcome to ABC Company, the leading provider of innovative solutions 
in the industry since 1995. We're here to serve you with excellence..."
```

### 2. Include Call-to-Action

End greetings with a clear prompt for caller action:

```python
"Hello! Thank you for calling XYZ Services. How can I assist you today?"
```

### 3. Match Brand Voice

Customize greeting to match your brand personality:

```python
# Professional
"Good day. Thank you for contacting Smith & Associates. How may I help you?"

# Friendly
"Hey there! Thanks for calling! What can I do for you today?"
```

### 4. Multi-Language Support

For businesses serving diverse customers, consider language-specific greetings:

```python
# English + Hindi
"Hello! नमस्ते! Welcome to our business. How can we help you?"
```

### 5. Error Handling

Always handle potential errors gracefully:

```python
try:
    greeting = await call_manager.get_greeting_message(business_id)
    await send_greeting_message(openai_ws, greeting)
except Exception as e:
    print(f"Error sending greeting: {e}")
    # Fall back to default greeting
    await send_greeting_message(openai_ws, 
        "Hello! Thank you for calling. How can I help you?")
```

## Troubleshooting

### Issue: Greeting Not Playing

**Symptoms:** Caller doesn't hear greeting after call is answered

**Possible Causes:**
1. OpenAI WebSocket not connected
2. Database configuration missing
3. Network latency

**Solutions:**
```python
# Verify OpenAI connection
if openai_ws.state.name != 'OPEN':
    print("OpenAI WebSocket not connected")
    
# Check database configuration
config = await database.get_business_config(business_id)
if not config:
    print(f"No configuration found for business_id: {business_id}")
    
# Add timeout handling
try:
    await asyncio.wait_for(
        send_greeting_message(openai_ws, greeting),
        timeout=3.0
    )
except asyncio.TimeoutError:
    print("Greeting send timeout")
```

### Issue: Greeting Delayed

**Symptoms:** Greeting plays more than 3 seconds after call answer

**Possible Causes:**
1. Slow database query
2. Network latency to OpenAI
3. Large greeting text

**Solutions:**
```python
# Cache configuration in Redis
await redis.set_config(business_id, config, ttl=300)

# Use shorter greeting
greeting = greeting[:200]  # Limit to 200 characters

# Monitor timing
import time
start = time.time()
greeting = await call_manager.get_greeting_message(business_id)
elapsed = time.time() - start
if elapsed > 1.0:
    print(f"Warning: Greeting retrieval took {elapsed}s")
```

### Issue: Special Characters Not Pronounced Correctly

**Symptoms:** OpenAI mispronounces special characters or abbreviations

**Solutions:**
```python
# Use phonetic spelling for abbreviations
"Welcome to A.I. Services"  # Bad
"Welcome to A I Services"   # Better

# Avoid special symbols
"Call us at 555-1234"       # Bad
"Call us at 555 1234"       # Better
```

## Future Enhancements

### Planned Features

1. **Redis Caching**: Cache greeting messages in Redis for faster retrieval
2. **A/B Testing**: Test different greeting variants for effectiveness
3. **Dynamic Greetings**: Time-based greetings (morning/afternoon/evening)
4. **Caller-Specific Greetings**: Personalized greetings for returning callers
5. **Multi-Language Auto-Detection**: Automatic language selection based on caller

### Example: Dynamic Greeting

```python
async def get_dynamic_greeting(business_id: str, caller_phone: str) -> str:
    """Get time-based and personalized greeting."""
    from datetime import datetime
    
    hour = datetime.now().hour
    
    # Time-based greeting
    if 5 <= hour < 12:
        time_greeting = "Good morning"
    elif 12 <= hour < 17:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"
    
    # Check if returning caller
    history = await call_manager.get_caller_history(caller_phone, limit=1)
    if history:
        return f"{time_greeting}! Welcome back to our business. How can we help you today?"
    else:
        return f"{time_greeting}! Thank you for calling. How can we assist you?"
```

## Related Documentation

- [Call Manager README](CALL_MANAGER_README.md)
- [Redis Service README](REDIS_SERVICE_README.md)
- [Design Document](.kiro/specs/ai-voice-automation-sme/design.md)
- [Requirements Document](.kiro/specs/ai-voice-automation-sme/requirements.md)

## Support

For issues or questions about the greeting service:

1. Check the troubleshooting section above
2. Review test cases in `test_greeting.py`
3. Examine the integration example in `greeting_integration_example.py`
4. Consult the design document for architectural details
