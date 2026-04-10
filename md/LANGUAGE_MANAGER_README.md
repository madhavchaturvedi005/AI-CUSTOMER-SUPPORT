# Language Manager - Multi-Language Support

## Overview

The Language Manager provides comprehensive multi-language support for the AI Voice Automation system. It enables automatic language detection within the first 10 seconds of a call, manual language selection, and mid-conversation language switching while preserving conversation context.

## Features

- **Automatic Language Detection**: Detects caller's language within first 10 seconds
- **Multi-Language Support**: English, Hindi, Tamil, Telugu, and Bengali
- **Manual Language Selection**: Prompts for language selection when confidence is low
- **Mid-Conversation Switching**: Allows language changes during the call
- **Context Preservation**: Maintains conversation history during language switches
- **OpenAI Integration**: Updates OpenAI Realtime API session with language preferences

## Supported Languages

| Language | Code | Script | Voice |
|----------|------|--------|-------|
| English  | en   | Latin  | alloy |
| Hindi    | hi   | Devanagari | alloy |
| Tamil    | ta   | Tamil  | alloy |
| Telugu   | te   | Telugu | alloy |
| Bengali  | bn   | Bengali | alloy |

## Requirements Addressed

- **Requirement 2.3**: Speech processing supports multiple languages
- **Requirement 13.1**: Detect language within first 10 seconds
- **Requirement 13.2**: Automatic language detection
- **Requirement 13.3**: Manual language switching support
- **Requirement 13.4**: Update OpenAI session with language preference
- **Requirement 13.5**: Maintain conversation context during language switch

## Architecture

### LanguageManager Class

The `LanguageManager` class provides the core language detection and switching functionality:

```python
from language_manager import LanguageManager
from models import Language

# Initialize with base instructions
language_manager = LanguageManager(
    base_instructions="You are a helpful AI assistant."
)

# Detect language from conversation
language, confidence = await language_manager.detect_language(
    openai_ws,
    conversation_history,
    elapsed_time_ms=5000
)

# Update OpenAI session with detected language
await language_manager.update_session_language(
    openai_ws,
    Language.HINDI
)
```

### CallManager Integration

The `CallManager` integrates language detection into the call lifecycle:

```python
from call_manager import CallManager

# Initialize CallManager with LanguageManager
call_manager = CallManager(
    database=database_service,
    redis=redis_service,
    language_manager=language_manager
)

# Detect and update language during call
language, confidence = await call_manager.detect_and_update_language(
    call_sid="CA123...",
    openai_ws=openai_ws,
    elapsed_time_ms=5000
)

# Handle manual language switch
success = await call_manager.handle_language_switch(
    call_sid="CA123...",
    openai_ws=openai_ws,
    requested_language=Language.TAMIL
)
```

## Usage Examples

### Example 1: Automatic Language Detection

```python
import asyncio
from language_manager import LanguageManager
from models import Language

async def detect_caller_language():
    """Detect language from caller's initial speech."""
    
    language_manager = LanguageManager()
    
    # Conversation history with Hindi text
    conversation_history = [
        {"speaker": "caller", "text": "नमस्ते, मुझे मदद चाहिए"}
    ]
    
    # Detect language (within 10-second window)
    language, confidence = await language_manager.detect_language(
        openai_ws,
        conversation_history,
        elapsed_time_ms=5000
    )
    
    print(f"Detected: {language.value}, Confidence: {confidence}")
    # Output: Detected: hi, Confidence: 0.9
    
    # Check if we should ask for confirmation
    should_ask = await language_manager.should_request_language_selection(
        language,
        confidence
    )
    
    if not should_ask:
        # High confidence - automatically switch
        await language_manager.update_session_language(
            openai_ws,
            language
        )
        print(f"Automatically switched to {language.value}")
    else:
        # Low confidence - ask caller
        prompt = language_manager.get_language_selection_prompt()
        print(f"Asking caller: {prompt}")

asyncio.run(detect_caller_language())
```

### Example 2: Manual Language Selection

```python
async def handle_language_selection():
    """Handle manual language selection from caller."""
    
    language_manager = LanguageManager()
    
    # Get multi-language prompt
    prompt = language_manager.get_language_selection_prompt()
    # "Please select your preferred language. कृपया अपनी पसंदीदा भाषा चुनें..."
    
    # Play prompt to caller via OpenAI
    await send_language_selection_prompt(openai_ws, prompt)
    
    # Caller responds: "Hindi please"
    caller_response = "Hindi please"
    
    # Parse language from response
    selected_language = language_manager.parse_language_from_text(caller_response)
    
    if selected_language:
        # Update session with selected language
        await language_manager.update_session_language(
            openai_ws,
            selected_language
        )
        print(f"Language set to: {selected_language.value}")
    else:
        print("Could not understand language selection")
```

### Example 3: Mid-Conversation Language Switch

```python
async def switch_language_mid_call():
    """Handle language switch during an ongoing call."""
    
    call_manager = CallManager(database, redis)
    
    # Caller requests language switch: "Switch to Tamil"
    caller_request = "Switch to Tamil"
    
    # Parse requested language
    requested_language = call_manager.language_manager.parse_language_from_text(
        caller_request
    )
    
    if requested_language:
        # Handle language switch (preserves context)
        success = await call_manager.handle_language_switch(
            call_sid="CA123...",
            openai_ws=openai_ws,
            requested_language=requested_language
        )
        
        if success:
            print(f"Successfully switched to {requested_language.value}")
            print("Conversation context preserved")
        else:
            print("Failed to switch language")
```

### Example 4: Integration with Call Flow

```python
async def handle_call_with_language_detection(websocket, openai_ws):
    """Complete call flow with language detection."""
    
    # Initialize services
    call_manager = CallManager(database, redis)
    
    # Start call
    call_sid = "CA123..."
    context = await call_manager.initiate_call(
        call_sid=call_sid,
        caller_phone="+1234567890"
    )
    
    # Answer call
    await call_manager.answer_call(call_sid)
    
    # Play initial greeting
    greeting = await call_manager.get_greeting_message()
    await send_greeting_message(openai_ws, greeting)
    
    # Track elapsed time
    call_start_time = datetime.now(timezone.utc)
    
    # During conversation (within first 10 seconds)
    while True:
        # Calculate elapsed time
        elapsed_ms = int((datetime.now(timezone.utc) - call_start_time).total_seconds() * 1000)
        
        # Attempt language detection
        if elapsed_ms <= 10000:  # Within 10-second window
            language, confidence = await call_manager.detect_and_update_language(
                call_sid=call_sid,
                openai_ws=openai_ws,
                elapsed_time_ms=elapsed_ms
            )
            
            if language and confidence >= 0.8:
                print(f"Language detected: {language.value} (confidence: {confidence})")
                # Language automatically updated
            elif language and confidence < 0.8:
                # Ask for language selection
                prompt = await call_manager.get_language_selection_prompt()
                await send_message(openai_ws, prompt)
                
                # Wait for response and parse
                caller_response = await get_caller_response()
                success, selected = await call_manager.parse_language_selection(
                    call_sid=call_sid,
                    openai_ws=openai_ws,
                    caller_response=caller_response
                )
        
        # Continue with normal call flow
        # ... handle conversation, intent detection, etc.
```

## Language Detection Algorithm

The language detection uses a multi-stage approach:

1. **Script Detection**: Identifies language-specific Unicode character ranges
   - Devanagari (U+0900-U+097F) → Hindi
   - Tamil (U+0B80-U+0BFF) → Tamil
   - Telugu (U+0C00-U+0C7F) → Telugu
   - Bengali (U+0980-U+09FF) → Bengali
   - Latin characters → English (default)

2. **Confidence Scoring**: Assigns confidence based on detection method
   - Script-based detection: 0.9 confidence
   - Default (English): 0.85 confidence

3. **Threshold Check**: Compares confidence against 0.8 threshold
   - ≥ 0.8: Automatic language switch
   - < 0.8: Request manual language selection

## Configuration

### Language-Specific Settings

Each language has its own configuration in `LanguageManager.LANGUAGE_CONFIGS`:

```python
LANGUAGE_CONFIGS = {
    Language.HINDI: {
        "code": "hi",
        "name": "Hindi",
        "voice": "alloy",
        "instructions_suffix": "Respond in Hindi (हिंदी में जवाब दें)."
    },
    # ... other languages
}
```

### Detection Parameters

```python
# Time window for initial detection (10 seconds)
DETECTION_WINDOW_MS = 10000

# Confidence threshold for automatic switching
DETECTION_CONFIDENCE_THRESHOLD = 0.8
```

## Database Schema

Language information is stored in the `calls` table:

```sql
CREATE TABLE calls (
    id UUID PRIMARY KEY,
    call_sid VARCHAR(255) UNIQUE NOT NULL,
    language VARCHAR(5) DEFAULT 'en',
    -- ... other fields
);
```

## Redis Caching

Language information is cached in the session state:

```python
{
    "call_id": "uuid",
    "language": "hi",  # Language code
    "metadata": {
        "language_detected": true,
        "language_detection_confidence": 0.9,
        "language_detection_time": "2024-01-15T10:30:00Z",
        "language_switched": false
    }
}
```

## Testing

Run the test suite:

```bash
python3 -m pytest test_language_manager.py -v
```

Test coverage includes:
- Language detection for all supported languages
- Confidence threshold handling
- Session update functionality
- Language switching with context preservation
- Language selection parsing
- Edge cases and error handling

## Best Practices

1. **Early Detection**: Call `detect_and_update_language()` as soon as caller starts speaking
2. **Graceful Fallback**: Always provide English as fallback if detection fails
3. **User Confirmation**: For low-confidence detections, ask user to confirm
4. **Context Preservation**: Never clear conversation history during language switches
5. **Database Sync**: Always update database when language changes
6. **Cache Consistency**: Keep Redis cache in sync with database

## Troubleshooting

### Language Not Detected

**Problem**: Language detection returns None or low confidence

**Solutions**:
- Ensure caller has spoken at least one utterance
- Check that detection is called within 10-second window
- Verify conversation_history contains caller turns
- Consider using manual language selection prompt

### Session Update Fails

**Problem**: `update_session_language()` returns False

**Solutions**:
- Verify OpenAI WebSocket connection is open
- Check that language is in LANGUAGE_CONFIGS
- Ensure base_instructions are properly formatted
- Review OpenAI API logs for errors

### Language Switch Doesn't Apply

**Problem**: Language changes but AI still responds in old language

**Solutions**:
- Verify session.update event was sent to OpenAI
- Check that instructions_suffix is properly formatted
- Ensure OpenAI model supports the target language
- Try sending a follow-up message to trigger new response

## Future Enhancements

1. **Advanced Detection**: Integrate dedicated language detection library (e.g., langdetect, fastText)
2. **More Languages**: Add support for additional regional languages
3. **Dialect Support**: Detect and handle language dialects
4. **Voice Matching**: Use language-specific voices for better experience
5. **Confidence Tuning**: Machine learning-based confidence scoring
6. **A/B Testing**: Test different detection thresholds and strategies

## References

- [OpenAI Realtime API Documentation](https://platform.openai.com/docs/guides/realtime)
- [Unicode Character Ranges](https://www.unicode.org/charts/)
- [Language Detection Best Practices](https://en.wikipedia.org/wiki/Language_identification)
- Requirements Document: Section 13 (Multi-Language Support)
- Design Document: Language Manager Component
