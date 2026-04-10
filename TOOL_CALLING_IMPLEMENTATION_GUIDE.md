# Tool Calling Implementation Guide for AI Voice Automation

## Overview

Tool calling (also called function calling) allows your AI agent to execute real actions during conversations, not just respond with text. This transforms your voice assistant from a chatbot into an intelligent automation system.

## What Tool Calling Gives You

### Current State (What You Have)
- AI can understand intent and language
- AI can have conversations
- AI can detect when someone wants to book an appointment
- **But**: AI can only talk about actions, not execute them

### With Tool Calling (What You'll Get)
- AI can **actually book** appointments in your calendar
- AI can **check real availability** from your database
- AI can **send SMS confirmations** automatically
- AI can **create leads** in your CRM
- AI can **transfer calls** to human agents
- AI can **look up customer history** and personalize responses

## How It Works

```
Caller: "I'd like to book a haircut for Friday at 2pm"
   ↓
AI detects intent: APPOINTMENT_BOOKING
   ↓
AI decides to call tool: check_availability(date="2024-04-12", time="14:00")
   ↓
Your Python function executes → Returns: "Available"
   ↓
AI calls tool: book_appointment(name="John", date="2024-04-12", time="14:00", service="haircut")
   ↓
Your Python function creates DB record + sends SMS
   ↓
AI responds: "Perfect! I've booked your haircut for Friday at 2pm. You'll receive a confirmation text shortly."
```

## Architecture for Your Project

### 1. Tool Definition Layer
Define what tools are available to the AI:

```python
# tools/appointment_tools.py
from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

class CheckAvailabilityInput(BaseModel):
    """Input schema for checking appointment availability."""
    date: str = Field(description="Date in YYYY-MM-DD format")
    service_type: str = Field(description="Type of service (haircut, coloring, etc)")
    duration_minutes: int = Field(default=30, description="Duration in minutes")

class BookAppointmentInput(BaseModel):
    """Input schema for booking an appointment."""
    customer_name: str = Field(description="Customer's full name")
    customer_phone: str = Field(description="Customer's phone number")
    date: str = Field(description="Date in YYYY-MM-DD format")
    time: str = Field(description="Time in HH:MM format (24-hour)")
    service_type: str = Field(description="Type of service")
    duration_minutes: int = Field(default=30)
    notes: str = Field(default="", description="Additional notes")

class ToolDefinition(BaseModel):
    """Tool definition for OpenAI Realtime API."""
    type: str = "function"
    name: str
    description: str
    parameters: Dict[str, Any]

# Define available tools
APPOINTMENT_TOOLS = [
    ToolDefinition(
        name="check_availability",
        description="Check if appointment slots are available for a given date and service",
        parameters=CheckAvailabilityInput.schema()
    ),
    ToolDefinition(
        name="book_appointment",
        description="Book an appointment for a customer",
        parameters=BookAppointmentInput.schema()
    ),
    ToolDefinition(
        name="get_available_slots",
        description="Get list of available time slots for a specific date",
        parameters={
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "service_type": {"type": "string", "description": "Type of service"}
            },
            "required": ["date"]
        }
    )
]
```

### 2. Tool Execution Layer
Implement the actual functions:

```python
# tools/tool_executor.py
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from appointment_manager import AppointmentManager
from database import DatabaseService

class ToolExecutor:
    """Executes tools called by the AI agent."""
    
    def __init__(
        self,
        appointment_manager: AppointmentManager,
        database: DatabaseService
    ):
        self.appointment_manager = appointment_manager
        self.database = database
        
        # Map tool names to execution functions
        self.tools = {
            "check_availability": self.check_availability,
            "book_appointment": self.book_appointment,
            "get_available_slots": self.get_available_slots,
            "get_customer_history": self.get_customer_history,
            "send_sms": self.send_sms,
            "create_lead": self.create_lead
        }
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        call_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool and return the result.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments from AI
            call_context: Optional call context for personalization
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }
        
        try:
            result = await self.tools[tool_name](arguments, call_context)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_availability(
        self,
        args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Check if appointment slot is available."""
        date_str = args.get("date")
        service_type = args.get("service_type", "general")
        
        # Parse date
        appointment_date = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
        
        # Check availability
        slots = await self.appointment_manager.retrieve_available_slots(
            start_date=appointment_date,
            end_date=appointment_date + timedelta(days=1),
            service_type=service_type
        )
        
        return {
            "available": len(slots) > 0,
            "slot_count": len(slots),
            "date": date_str,
            "service_type": service_type
        }
    
    async def get_available_slots(
        self,
        args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get list of available time slots."""
        date_str = args.get("date")
        service_type = args.get("service_type")
        
        appointment_date = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
        
        slots = await self.appointment_manager.propose_time_slots(
            preferred_date=appointment_date,
            service_type=service_type,
            num_slots=5
        )
        
        # Format slots for AI
        formatted_slots = [
            slot.strftime("%I:%M %p") for slot in slots
        ]
        
        return {
            "date": date_str,
            "available_slots": formatted_slots,
            "count": len(formatted_slots)
        }
    
    async def book_appointment(
        self,
        args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Book an appointment."""
        # Parse datetime
        date_str = args.get("date")
        time_str = args.get("time")
        datetime_str = f"{date_str}T{time_str}:00Z"
        appointment_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        
        # Get call context
        call_id = context.get("call_id") if context else None
        
        # Book appointment
        appointment, appointment_id = await self.appointment_manager.book_appointment(
            call_id=call_id,
            customer_name=args.get("customer_name"),
            customer_phone=args.get("customer_phone"),
            appointment_datetime=appointment_datetime,
            service_type=args.get("service_type"),
            notes=args.get("notes")
        )
        
        return {
            "appointment_id": appointment_id,
            "customer_name": appointment.customer_name,
            "date": appointment.appointment_datetime.strftime("%B %d, %Y"),
            "time": appointment.appointment_datetime.strftime("%I:%M %p"),
            "service": appointment.service_type,
            "confirmation_sent": appointment.confirmation_sent
        }
    
    async def get_customer_history(
        self,
        args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get customer's call and appointment history."""
        phone = args.get("phone") or (context.get("caller_phone") if context else None)
        
        if not phone:
            return {"error": "Phone number required"}
        
        # Get call history
        calls = await self.database.get_caller_history(phone, limit=5)
        
        # Get appointments
        appointments = await self.database.get_customer_appointments(phone, limit=5)
        
        return {
            "phone": phone,
            "total_calls": len(calls),
            "total_appointments": len(appointments),
            "last_call_date": calls[0].get("started_at") if calls else None,
            "upcoming_appointments": [
                {
                    "date": appt.get("appointment_datetime"),
                    "service": appt.get("service_type")
                }
                for appt in appointments
                if appt.get("status") == "scheduled"
            ]
        }
    
    async def create_lead(
        self,
        args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a sales lead."""
        from lead_manager import LeadManager
        
        lead_manager = LeadManager(database=self.database)
        
        lead_id = await lead_manager.capture_lead(
            call_id=context.get("call_id") if context else None,
            name=args.get("name"),
            phone=args.get("phone"),
            email=args.get("email"),
            inquiry_details=args.get("inquiry_details", ""),
            budget_indication=args.get("budget"),
            timeline=args.get("timeline"),
            lead_score=args.get("lead_score", 5)
        )
        
        return {
            "lead_id": lead_id,
            "name": args.get("name"),
            "score": args.get("lead_score", 5)
        }
    
    async def send_sms(
        self,
        args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send SMS message."""
        # Integrate with Twilio SMS
        phone = args.get("phone")
        message = args.get("message")
        
        # TODO: Implement actual Twilio SMS sending
        print(f"📱 SMS to {phone}: {message}")
        
        return {
            "sent": True,
            "phone": phone,
            "message_length": len(message)
        }
```

### 3. Integration with OpenAI Realtime API

Update your session initialization to include tools:

```python
# session.py - Add to SessionState class
from tools.appointment_tools import APPOINTMENT_TOOLS
from tools.tool_executor import ToolExecutor

class SessionState:
    def __init__(self):
        # ... existing code ...
        self.tool_executor = None
        self.pending_tool_calls = []
    
    def initialize_tool_executor(
        self,
        appointment_manager: AppointmentManager,
        database: DatabaseService
    ):
        """Initialize tool executor with dependencies."""
        self.tool_executor = ToolExecutor(
            appointment_manager=appointment_manager,
            database=database
        )
```

Update your WebSocket connection to register tools:

```python
# utils.py - Update initialize_session function
async def initialize_session(openai_ws, state: SessionState):
    """Send session configuration to OpenAI including tool definitions."""
    from tools.appointment_tools import APPOINTMENT_TOOLS
    
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": TEMPERATURE,
            # Add tools here
            "tools": [tool.dict() for tool in APPOINTMENT_TOOLS],
            "tool_choice": "auto"  # Let AI decide when to use tools
        }
    }
    
    print('Sending session update with tools:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))
```

### 4. Handle Tool Calls in Event Handler

Update `handlers.py` to process tool calls:

```python
# handlers.py - Add to send_to_twilio function
async def send_to_twilio(
    websocket: WebSocket,
    openai_ws: websockets.WebSocketClientProtocol,
    state: SessionState
) -> None:
    """Receive events from OpenAI and handle tool calls."""
    try:
        async for openai_message in openai_ws:
            response = json.loads(openai_message)
            
            # ... existing audio handling code ...
            
            # Handle tool calls
            if response.get('type') == 'response.function_call_arguments.done':
                await handle_tool_call(response, openai_ws, state)
            
            # ... rest of existing code ...

async def handle_tool_call(
    response: Dict[str, Any],
    openai_ws: websockets.WebSocketClientProtocol,
    state: SessionState
) -> None:
    """
    Handle tool call from OpenAI.
    
    Args:
        response: Tool call response from OpenAI
        openai_ws: WebSocket connection to OpenAI
        state: Session state
    """
    call_id = response.get('call_id')
    tool_name = response.get('name')
    arguments_str = response.get('arguments', '{}')
    
    print(f"🔧 Tool call: {tool_name}")
    print(f"   Arguments: {arguments_str}")
    
    # Parse arguments
    try:
        arguments = json.loads(arguments_str)
    except json.JSONDecodeError:
        arguments = {}
    
    # Get call context
    call_context = None
    if state.call_manager and state.call_sid:
        context = await state.call_manager.get_call_context(state.call_sid)
        if context:
            call_context = {
                "call_id": context.call_id,
                "caller_phone": context.caller_phone,
                "caller_name": context.caller_name
            }
    
    # Execute tool
    if state.tool_executor:
        result = await state.tool_executor.execute_tool(
            tool_name=tool_name,
            arguments=arguments,
            call_context=call_context
        )
        
        print(f"✅ Tool result: {result}")
        
        # Send result back to OpenAI
        tool_response = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(result)
            }
        }
        
        await openai_ws.send(json.dumps(tool_response))
        
        # Trigger response generation
        await openai_ws.send(json.dumps({"type": "response.create"}))
    else:
        print("⚠️  Tool executor not initialized")
```

## Implementation Steps

### Step 1: Create Tool Definitions
```bash
mkdir tools
touch tools/__init__.py
touch tools/appointment_tools.py
touch tools/tool_executor.py
```

### Step 2: Update System Message
Add tool usage instructions to your AI:

```python
# config.py
SYSTEM_MESSAGE = f"""You are {AGENT_NAME}, an AI voice assistant for {BUSINESS_NAME}.

CAPABILITIES:
- You can check appointment availability in real-time
- You can book appointments directly
- You can look up customer history
- You can create sales leads
- You can send SMS confirmations

TOOL USAGE GUIDELINES:
1. Always check availability before booking
2. Confirm details with customer before calling book_appointment
3. Use get_customer_history for returning callers
4. Create leads for sales inquiries
5. Be proactive - use tools to help customers efficiently

CONVERSATION FLOW:
1. Greet warmly
2. Understand customer need
3. Use tools to take action
4. Confirm completion
5. Ask if anything else needed

Remember: You're not just talking about actions - you can actually DO them!
"""
```

### Step 3: Initialize Tool Executor
Update `main.py`:

```python
# main.py - In media_stream endpoint
@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket, call_sid: str = None):
    # ... existing code ...
    
    # Initialize tool executor
    if appointment_manager and database_service:
        state.initialize_tool_executor(
            appointment_manager=appointment_manager,
            database=database_service
        )
        print("✅ Tool executor initialized")
    
    # ... rest of code ...
```

### Step 4: Test Tool Calling

Create a test script:

```python
# test_tool_calling.py
import asyncio
from tools.tool_executor import ToolExecutor
from appointment_manager import AppointmentManager
from database import DatabaseService

async def test_tools():
    # Initialize services
    db = await DatabaseService.create()
    appt_mgr = AppointmentManager(database=db)
    executor = ToolExecutor(appt_mgr, db)
    
    # Test check availability
    result = await executor.execute_tool(
        "check_availability",
        {"date": "2026-04-15", "service_type": "haircut"}
    )
    print("Availability:", result)
    
    # Test get available slots
    result = await executor.execute_tool(
        "get_available_slots",
        {"date": "2026-04-15"}
    )
    print("Available slots:", result)

if __name__ == "__main__":
    asyncio.run(test_tools())
```

## Benefits for Your Business

1. **Automation**: AI handles complete booking flow without human intervention
2. **Accuracy**: Real-time availability checks prevent double-booking
3. **Speed**: Instant confirmations and SMS notifications
4. **Scalability**: Handle multiple calls simultaneously
5. **Data Quality**: Structured data capture in database
6. **Customer Experience**: Seamless, efficient service

## Next Steps

1. Implement basic appointment tools (check availability, book)
2. Test with real calls
3. Add more tools (customer lookup, lead creation, SMS)
4. Integrate with your calendar system
5. Add business logic (pricing, promotions, etc.)
6. Monitor and optimize tool usage

Tool calling transforms your AI from a conversational interface into a complete automation platform!
