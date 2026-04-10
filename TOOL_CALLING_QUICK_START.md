# Tool Calling - Quick Start Guide

## What Is Tool Calling?

Tool calling lets your AI agent execute real Python functions during phone conversations. Instead of just talking about actions, the AI can actually DO them.

## Example Conversation

**Without Tool Calling:**
```
Caller: "I'd like to book a haircut for tomorrow at 2pm"
AI: "I'll take your information and have someone call you back to schedule that."
```

**With Tool Calling:**
```
Caller: "I'd like to book a haircut for tomorrow at 2pm"
AI: [calls check_availability tool]
AI: "Perfect! I have 2pm available. Can I get your name?"
Caller: "John Doe"
AI: [calls book_appointment tool]
AI: "Done! I've booked your haircut for tomorrow at 2pm. 
     You'll receive a confirmation text shortly."
```

## Available Tools (6 Total)

### 1. check_availability
Check if appointment slots exist for a date
```python
check_availability(date="2026-04-15", service_type="haircut")
→ {"available": true, "slot_count": 5}
```

### 2. get_available_slots
Get specific available times
```python
get_available_slots(date="2026-04-15")
→ {"available_slots": ["09:00 AM", "10:00 AM", "02:00 PM"]}
```

### 3. book_appointment
Book an appointment with full details
```python
book_appointment(
    customer_name="John Doe",
    customer_phone="+1234567890",
    date="2026-04-15",
    time="14:00",
    service_type="haircut"
)
→ {"appointment_id": "appt-123", "confirmation_sent": true}
```

### 4. create_lead
Capture sales leads
```python
create_lead(
    name="Jane Smith",
    phone="+1987654321",
    inquiry_details="Interested in premium package",
    lead_score=8
)
→ {"lead_id": "lead-456", "score": 8}
```

### 5. get_customer_history
Look up previous interactions
```python
get_customer_history(phone="+1234567890")
→ {"is_returning_customer": true, "total_calls": 3}
```

### 6. send_sms
Send text messages
```python
send_sms(phone="+1234567890", message="Your appointment is confirmed")
→ {"sent": true}
```

## How to Test

### 1. Start Server
```bash
python3 main.py
```

Look for:
```
✅ AppointmentManager: Ready (tool calling enabled)
📋 Sending session update with 6 tools
```

### 2. Call Your Number

Try these phrases:
- "I want to book an appointment"
- "What times are available tomorrow?"
- "Can I schedule a haircut?"

### 3. Watch Logs

You'll see:
```
🔧 TOOL CALL RECEIVED
Tool: check_availability
✅ TOOL EXECUTION RESULT
Success: True
```

## Adding New Tools

### Step 1: Define Tool
In `tools/appointment_tools.py`:
```python
ToolDefinition(
    name="my_new_tool",
    description="What this tool does",
    parameters={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "..."}
        },
        "required": ["param1"]
    }
)
```

### Step 2: Implement Function
In `tools/tool_executor.py`:
```python
async def my_new_tool(self, args, context):
    param1 = args.get("param1")
    # Your logic here
    return {"result": "success"}
```

### Step 3: Register Tool
Add to `self.tools` dict in `__init__`:
```python
self.tools = {
    # ... existing tools ...
    "my_new_tool": self.my_new_tool
}
```

That's it! The AI will automatically learn to use it.

## Architecture

```
Phone Call → OpenAI → Tool Call → ToolExecutor → Your Services
                ↓                        ↓
            AI Response ← Tool Result ← Database/APIs
```

## Key Files

- `tools/appointment_tools.py` - Tool definitions
- `tools/tool_executor.py` - Tool implementations
- `handlers.py` - Tool call routing
- `session.py` - Tool executor initialization
- `main.py` - Service setup

## Common Issues

### Tools Not Called
✓ Check tool descriptions are clear
✓ Verify tools registered in `utils.py`
✓ Ensure `tool_choice: "auto"` is set

### Execution Errors
✓ Check logs for error details
✓ Run `python3 test_tool_calling.py`
✓ Verify services are initialized

## Benefits

✅ **Automation** - AI handles complete workflows
✅ **Accuracy** - Real-time data access
✅ **Speed** - Instant execution during calls
✅ **Scalability** - Handle unlimited calls
✅ **Consistency** - Same quality every time

## What's Next?

1. Test with real calls
2. Add more tools for your business
3. Integrate with your calendar/CRM
4. Monitor tool usage metrics
5. Optimize based on results

## Quick Test

Run the test suite:
```bash
python3 test_tool_calling.py
```

Should see:
```
✅ ALL TESTS PASSED!
Tool calling is ready to use!
```

---

**You're all set!** Your AI can now take real actions during phone calls. 🚀
