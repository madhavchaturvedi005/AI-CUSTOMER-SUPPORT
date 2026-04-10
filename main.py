"""FastAPI application for Twilio-OpenAI voice assistant with AI features."""

import asyncio
import os
import json
import websockets
from fastapi import FastAPI, WebSocket, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from twilio.twiml.voice_response import VoiceResponse, Connect
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from unittest.mock import AsyncMock
from pydantic import BaseModel
from uuid import uuid4

from config import (
    OPENAI_API_KEY, PORT, TEMPERATURE, SYSTEM_MESSAGE,
    BUSINESS_NAME, BUSINESS_TYPE, AGENT_NAME, COMPANY_DESCRIPTION,
    LANGUAGE_NAMES, SUPPORTED_LANGUAGES, get_system_message, OPENAI_REALTIME_MODEL
)
from session import SessionState
from handlers import receive_from_twilio, send_to_twilio
from utils import initialize_session, create_ssl_context

# Import our AI features
from call_manager import CallManager
from intent_detector import OpenAIIntentDetector
from language_manager import LanguageManager
from call_router import CallRouter, RoutingRule
from models import Intent, Language
from database import DatabaseService
from redis_service import RedisService
from event_broadcaster import broadcaster

# Pydantic models for API requests
class AppointmentRequest(BaseModel):
    """Request model for creating appointments."""
    customer_name: str
    customer_phone: str
    service_type: str
    appointment_datetime: str  # ISO format like "2026-04-12T14:00:00Z"
    duration_minutes: int = 30
    notes: Optional[str] = None
    call_id: Optional[str] = None

app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Global service instances (will be initialized on startup)
call_manager = None
intent_detector = None
language_manager = None
call_router = None
database_service = None
redis_service = None
appointment_manager = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    global call_manager, intent_detector, language_manager, call_router, database_service, redis_service, appointment_manager
    
    print("🚀 Initializing AI Voice Automation services...")
    
    # Check if we should use real database or mock
    use_real_db = os.getenv("USE_REAL_DB", "false").lower() == "true"
    use_real_redis = os.getenv("USE_REAL_REDIS", "false").lower() == "true"
    
    if use_real_db:
        try:
            # Initialize real database
            from database import initialize_database
            database_service = await initialize_database()
            print("   ✅ Connected to PostgreSQL database")
        except Exception as e:
            print(f"   ⚠️  Failed to connect to database: {e}")
            print("   → Falling back to mock database")
            use_real_db = False
    
    if use_real_redis:
        try:
            # Initialize real Redis
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_service = RedisService(host=redis_host, port=redis_port)
            await redis_service.connect()
            print("   ✅ Connected to Redis cache")
        except Exception as e:
            print(f"   ⚠️  Failed to connect to Redis: {e}")
            print("   → Falling back to mock Redis")
            use_real_redis = False
    
    # Use mock services if real ones aren't available
    if not use_real_db:
        from unittest.mock import AsyncMock
        database_service = AsyncMock(spec=DatabaseService)
        database_service.create_call = AsyncMock(return_value="call-uuid")
        database_service.update_call_status = AsyncMock(return_value=True)
        database_service.update_call_intent = AsyncMock(return_value=True)
        database_service.update_call_language = AsyncMock(return_value=True)
        database_service.get_business_config = AsyncMock(return_value=None)
        database_service.get_recent_caller_history = AsyncMock(return_value=[])
        database_service.get_calls = AsyncMock(return_value=[])
        database_service.get_caller_history = AsyncMock(return_value=[])
        print("   → Using mock database")
    
    if not use_real_redis:
        # Use real in-memory storage instead of AsyncMock
        # so call contexts are actually saved and retrieved
        _session_store = {}  # in-memory dict that persists during runtime
        
        class InMemoryRedis:
            async def set_session_state(self, call_sid: str, session_data: dict, ttl_seconds: int = 3600):
                _session_store[call_sid] = session_data
                return True
            
            async def get_session_state(self, call_sid: str):
                return _session_store.get(call_sid, None)
            
            async def add_caller_history(self, caller_phone: str, call_id: str):
                pass  # no-op for mock
            
            async def get_caller_history(self, caller_phone: str, limit: int = 10):
                return []
        
        redis_service = InMemoryRedis()
        print("   → Using in-memory Redis (sessions will persist during runtime)")
    
    # Initialize AI services
    language_manager = LanguageManager(
        base_instructions="You are a helpful AI assistant for customer service."
    )
    
    call_manager = CallManager(
        database=database_service,
        redis=redis_service,
        language_manager=language_manager
    )
    
    intent_detector = OpenAIIntentDetector(api_key=OPENAI_API_KEY)
    
    # Initialize call router with business rules
    call_router = CallRouter(redis_service=redis_service)
    
    # Add routing rules
    sales_rule = RoutingRule(
        intent=Intent.SALES_INQUIRY,
        priority=5,
        business_hours_only=False,
        agent_skills_required=["sales"],
        max_queue_time_seconds=300
    )
    call_router.add_routing_rule(sales_rule)
    
    support_rule = RoutingRule(
        intent=Intent.SUPPORT_REQUEST,
        priority=3,
        business_hours_only=False,
        agent_skills_required=["support"],
        max_queue_time_seconds=600
    )
    call_router.add_routing_rule(support_rule)
    
    # Initialize AppointmentManager for tool calling with business hours
    from appointment_manager import AppointmentManager
    
    # Define business hours (Monday-Friday 9 AM - 5 PM, Saturday 10 AM - 2 PM)
    business_hours = {
        "monday": [(9, 17)],      # 9 AM - 5 PM
        "tuesday": [(9, 17)],     # 9 AM - 5 PM
        "wednesday": [(9, 17)],   # 9 AM - 5 PM
        "thursday": [(9, 17)],    # 9 AM - 5 PM
        "friday": [(9, 17)],      # 9 AM - 5 PM
        "saturday": [(10, 14)],   # 10 AM - 2 PM
        "sunday": []              # Closed
    }
    
    appointment_manager = AppointmentManager(
        database=database_service,
        business_hours=business_hours,
        slot_duration_minutes=30  # 30-minute slots
    )
    
    print("✅ AI Voice Automation services initialized!")
    print("   • CallManager: Ready")
    print("   • IntentDetector: Ready")
    print("   • LanguageManager: Ready (5 languages)")
    print("   • CallRouter: Ready (2 routing rules)")
    print("   • AppointmentManager: Ready (tool calling enabled)")
    print(f"   • Database: {'PostgreSQL' if use_real_db else 'Mock'}")
    print(f"   • Cache: {'Redis' if use_real_redis else 'Mock'}")


@app.get("/", response_class=JSONResponse)
async def index_page():
    """Return a simple status message for the root endpoint."""
    return {
        "message": "AI Voice Automation System is running!",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": {
            "call_management": "enabled",
            "intent_detection": "enabled",
            "language_detection": "enabled (5 languages)",
            "call_routing": "enabled",
            "conversation_history": "enabled"
        },
        "status": "ready"
    }


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint for monitoring."""
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected" if database_service and not isinstance(database_service, AsyncMock) else "mock",
        "redis": "connected" if redis_service and not isinstance(redis_service, AsyncMock) else "mock"
    })


@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request) -> HTMLResponse:
    """
    Handle incoming call and return TwiML response to connect to Media Stream.
    
    This endpoint now integrates with our AI features:
    - Initiates call in CallManager
    - Prepares for language detection
    - Sets up intent detection
    - Uses custom greeting from configuration
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTMLResponse containing TwiML XML
    """
    print("\n" + "="*60)
    print("📞 /incoming-call endpoint HIT!")
    print("="*60)
    
    # Extract caller information from Twilio request
    form_data = await request.form()
    caller_phone = form_data.get("From", "unknown")
    call_sid = form_data.get("CallSid", "unknown")
    
    print(f"\n📞 Incoming call from {caller_phone} (SID: {call_sid})")
    print(f"   Form data keys: {list(form_data.keys())}")
    print(f"   call_manager exists: {call_manager is not None}")
    print(f"   redis_service exists: {redis_service is not None}")
    print(f"   database_service exists: {database_service is not None}")
    
    # Get custom greeting from configuration
    custom_greeting = None
    try:
        if hasattr(app.state, 'config') and 'greeting' in app.state.config:
            custom_greeting = app.state.config['greeting'].get('message')
        elif database_service and not isinstance(database_service, AsyncMock):
            # Only try database if it's a real database service, not a mock
            try:
                async with database_service.pool.acquire() as conn:
                    config = await conn.fetchrow(
                        "SELECT greeting_message FROM business_config WHERE business_id = $1 AND active = TRUE",
                        "default"
                    )
                    if config and config.get('greeting_message'):
                        custom_greeting = str(config['greeting_message'])  # Ensure it's a string
            except Exception as e:
                print(f"   ⚠️  Error fetching greeting from database: {e}")
    except Exception as e:
        print(f"   ⚠️  Error getting custom greeting: {e}")
    
    # Initiate call in our system
    if call_manager:
        try:
            print(f"🔄 Initiating call in system...")
            context = await call_manager.initiate_call(
                call_sid=call_sid,
                caller_phone=caller_phone,
                direction="inbound"
            )
            print(f"✅ Call initiated in system: {context.call_id}")
            print(f"   Call SID: {call_sid}")
            print(f"   Caller: {caller_phone}")
            
            # Check for conversation history
            has_history = await call_manager.integrate_conversation_history(
                call_sid=call_sid,
                caller_phone=caller_phone
            )
            
            if has_history:
                print(f"👤 Returning caller detected!")
                summary = await call_manager.get_conversation_summary(call_sid)
                print(f"   History: {summary}")
        except Exception as e:
            print(f"⚠️  Error initiating call: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"❌ call_manager is None! Call will not be tracked.")
    
    response = VoiceResponse()
    
    # Use custom greeting if configured, otherwise use multilingual default
    if custom_greeting and isinstance(custom_greeting, str):
        print(f"🎤 Using custom greeting: {custom_greeting[:50]}...")
        response.say(
            custom_greeting,
            voice="Google.en-US-Chirp3-HD-Aoede"
        )
    else:
        # Multilingual default greeting - covers all 5 supported languages
        print(f"🎤 Using multilingual default greeting")
        response.say(
            f"Thank you for calling {BUSINESS_NAME}. Aapka swagat hai. Vanakkam. Meeru swagatam. Apnakey swagat.",
            voice="Google.en-US-Chirp3-HD-Aoede"
        )
    
    host = request.url.hostname
    connect = Connect()
    # Include call_sid as query parameter so WebSocket can access it
    connect.stream(url=f'wss://{host}/media-stream?call_sid={call_sid}')
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")


@app.get("/api/analytics")
async def get_analytics() -> JSONResponse:
    """
    Get dashboard analytics and statistics.
    
    Returns:
        Analytics data including call volume, intent distribution, and metrics
        
    Requirement 15.3: Dashboard showing call volume trends and metrics
    """
    try:
        # Try to get real data from database
        if database_service and not isinstance(database_service, AsyncMock):
            # Get real analytics from database
            async with database_service.pool.acquire() as conn:
                # Total calls
                total_calls = await conn.fetchval("SELECT COUNT(*) FROM calls")
                
                # Total leads
                total_leads = await conn.fetchval("SELECT COUNT(*) FROM leads")
                
                # Total appointments
                total_appointments = await conn.fetchval("SELECT COUNT(*) FROM appointments")
                
                # Average duration
                avg_duration_seconds = await conn.fetchval(
                    "SELECT AVG(duration_seconds) FROM calls WHERE duration_seconds IS NOT NULL"
                )
                avg_duration = int(avg_duration_seconds / 60) if avg_duration_seconds else 0
                
                # Call volume (last 7 days)
                call_volume_data = await conn.fetch("""
                    SELECT 
                        TO_CHAR(started_at, 'Dy') as day,
                        COUNT(*) as count
                    FROM calls
                    WHERE started_at >= NOW() - INTERVAL '7 days'
                    GROUP BY TO_CHAR(started_at, 'Dy'), DATE(started_at)
                    ORDER BY DATE(started_at)
                """)
                
                call_volume_labels = [row['day'] for row in call_volume_data] if call_volume_data else ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                call_volume_counts = [row['count'] for row in call_volume_data] if call_volume_data else [0, 0, 0, 0, 0, 0, 0]
                
                # Intent distribution
                intent_data = await conn.fetch("""
                    SELECT intent, COUNT(*) as count
                    FROM calls
                    WHERE intent IS NOT NULL
                    GROUP BY intent
                    ORDER BY count DESC
                """)
                
                intent_labels = [row['intent'].replace('_', ' ').title() for row in intent_data] if intent_data else ["Sales Inquiry", "Support", "Appointment", "General", "Complaint"]
                intent_counts = [row['count'] for row in intent_data] if intent_data else [0, 0, 0, 0, 0]
                
                # Recent activity
                recent_calls = await conn.fetch("""
                    SELECT caller_phone, started_at, intent
                    FROM calls
                    ORDER BY started_at DESC
                    LIMIT 3
                """)
                
                recent_activity = []
                for call in recent_calls:
                    # Make started_at timezone-aware if it's naive
                    started_at = call['started_at']
                    if started_at.tzinfo is None:
                        started_at = started_at.replace(tzinfo=timezone.utc)
                    
                    time_diff = datetime.now(timezone.utc) - started_at
                    if time_diff.seconds < 3600:
                        time_str = f"{time_diff.seconds // 60} minutes ago"
                    else:
                        time_str = f"{time_diff.seconds // 3600} hours ago"
                    
                    recent_activity.append({
                        "type": "call",
                        "title": f"New call from {call['caller_phone']}",
                        "time": time_str
                    })
                
                return JSONResponse(content={
                    "total_calls": total_calls or 0,
                    "total_leads": total_leads or 0,
                    "total_appointments": total_appointments or 0,
                    "avg_duration": avg_duration,
                    "call_volume": {
                        "labels": call_volume_labels,
                        "data": call_volume_counts
                    },
                    "intent_distribution": {
                        "labels": intent_labels,
                        "data": intent_counts
                    },
                    "recent_activity": recent_activity if recent_activity else [
                        {"type": "call", "title": "No recent activity", "time": ""}
                    ]
                })
        
    except Exception as e:
        print(f"Error fetching real analytics: {e}")
    
    # Fall back to mock data
    analytics = {
        "total_calls": 127,
        "total_leads": 34,
        "total_appointments": 18,
        "avg_duration": 4,  # minutes
        "call_volume": {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "data": [15, 22, 18, 25, 20, 12, 15]
        },
        "intent_distribution": {
            "labels": ["Sales Inquiry", "Support", "Appointment", "General", "Complaint"],
            "data": [45, 28, 18, 12, 7]
        },
        "recent_activity": [
            {
                "type": "call",
                "title": "New call from +1234567890",
                "time": "2 minutes ago"
            },
            {
                "type": "lead",
                "title": "High-value lead captured (Score: 9)",
                "time": "15 minutes ago"
            },
            {
                "type": "appointment",
                "title": "Appointment scheduled for tomorrow",
                "time": "1 hour ago"
            }
        ]
    }
    
    return JSONResponse(content=analytics)


@app.get("/api/calls/{call_id}")
async def get_call_details(call_id: str) -> JSONResponse:
    """
    Get detailed information about a specific call including conversation log and insights.
    
    Args:
        call_id: Call UUID
        
    Returns:
        Call details with conversation transcript and AI insights
        
    Requirement 8.2, 8.4: Retrieve conversation transcripts with metadata
    """
    try:
        call_data = None
        conversation = []
        
        # Try to get from database if available
        if database_service and not isinstance(database_service, AsyncMock):
            try:
                async with database_service.pool.acquire() as conn:
                    # Get call record
                    call_row = await conn.fetchrow(
                        "SELECT * FROM calls WHERE id = $1",
                        call_id
                    )
                    
                    if call_row:
                        call_data = {
                            "id": str(call_row['id']),
                            "call_sid": call_row['call_sid'],
                            "caller_phone": call_row['caller_phone'],
                            "caller_name": call_row.get('caller_name'),
                            "started_at": call_row['started_at'].isoformat() if call_row.get('started_at') else None,
                            "ended_at": call_row['ended_at'].isoformat() if call_row.get('ended_at') else None,
                            "duration_seconds": call_row.get('duration_seconds'),
                            "status": call_row['status'],
                            "intent": call_row.get('intent'),
                            "intent_confidence": float(call_row['intent_confidence']) if call_row.get('intent_confidence') else None,
                            "language": call_row.get('language'),
                            "direction": call_row.get('direction'),
                            "metadata": call_row.get('metadata', {})
                        }
                        
                        # Get conversation transcript
                        transcript_rows = await conn.fetch("""
                            SELECT speaker, text, timestamp_ms, language, confidence
                            FROM transcripts
                            WHERE call_id = $1
                            ORDER BY timestamp_ms ASC
                        """, call_id)
                        
                        conversation = [
                            {
                                "speaker": row['speaker'],
                                "text": row['text'],
                                "timestamp_ms": row['timestamp_ms'],
                                "language": row.get('language'),
                                "confidence": float(row['confidence']) if row.get('confidence') else None
                            }
                            for row in transcript_rows
                        ]
                        
                        print(f"✅ Loaded call details: {call_id}")
            except Exception as db_error:
                print(f"⚠️  Database error loading call: {db_error}")
        
        # Generate insights from conversation
        insights = generate_call_insights(call_data, conversation) if call_data else {}
        
        if not call_data:
            # Return mock data for demo purposes
            if call_id in ["call-001", "call-002", "call-003"]:
                mock_calls = {
                    "call-001": {
                        "id": "call-001",
                        "call_sid": "CA1234567890",
                        "caller_phone": "+1234567890",
                        "caller_name": "John Doe",
                        "started_at": "2026-04-09T17:30:00Z",
                        "ended_at": "2026-04-09T17:34:05Z",
                        "duration_seconds": 245,
                        "status": "completed",
                        "intent": "sales_inquiry",
                        "intent_confidence": 0.92,
                        "language": "en",
                        "direction": "inbound"
                    },
                    "call-002": {
                        "id": "call-002",
                        "call_sid": "CA0987654321",
                        "caller_phone": "+1987654321",
                        "caller_name": "Jane Smith",
                        "started_at": "2026-04-09T14:30:00Z",
                        "ended_at": "2026-04-09T14:33:00Z",
                        "duration_seconds": 180,
                        "status": "completed",
                        "intent": "appointment_booking",
                        "intent_confidence": 0.88,
                        "language": "en",
                        "direction": "inbound"
                    },
                    "call-003": {
                        "id": "call-003",
                        "call_sid": "CA5555555555",
                        "caller_phone": "+1555555555",
                        "caller_name": "Bob Johnson",
                        "started_at": "2026-04-09T11:30:00Z",
                        "ended_at": "2026-04-09T11:35:20Z",
                        "duration_seconds": 320,
                        "status": "completed",
                        "intent": "support_request",
                        "intent_confidence": 0.85,
                        "language": "en",
                        "direction": "inbound"
                    }
                }
                
                mock_conversations = {
                    "call-001": [
                        {"speaker": "customer", "text": "Hi, I'm interested in your salon services. What packages do you offer?", "timestamp_ms": 0},
                        {"speaker": "assistant", "text": "Hello! Thank you for your interest. We offer several packages including haircut, styling, coloring, and spa treatments. Would you like to know about any specific service?", "timestamp_ms": 5000},
                        {"speaker": "customer", "text": "Yes, I'd like to know about the pricing for a haircut and color.", "timestamp_ms": 15000},
                        {"speaker": "assistant", "text": "Our haircut starts at $45 and color treatments range from $80 to $150 depending on the technique. We also have a combo package for $120. Would you like to book an appointment?", "timestamp_ms": 20000},
                        {"speaker": "customer", "text": "That sounds good. Can I get more information sent to my email?", "timestamp_ms": 35000},
                        {"speaker": "assistant", "text": "Absolutely! I'll send you detailed information about our services and pricing. May I have your email address?", "timestamp_ms": 40000}
                    ],
                    "call-002": [
                        {"speaker": "customer", "text": "I'd like to schedule an appointment for a haircut.", "timestamp_ms": 0},
                        {"speaker": "assistant", "text": "I'd be happy to help you schedule an appointment. What day works best for you?", "timestamp_ms": 3000},
                        {"speaker": "customer", "text": "How about this Friday afternoon?", "timestamp_ms": 10000},
                        {"speaker": "assistant", "text": "Let me check our availability for Friday afternoon. We have slots at 2 PM, 3 PM, and 4 PM. Which time would you prefer?", "timestamp_ms": 13000},
                        {"speaker": "customer", "text": "3 PM would be perfect.", "timestamp_ms": 22000},
                        {"speaker": "assistant", "text": "Great! I've scheduled you for Friday at 3 PM for a haircut. You'll receive a confirmation SMS shortly. Is there anything else I can help you with?", "timestamp_ms": 25000}
                    ],
                    "call-003": [
                        {"speaker": "customer", "text": "Hi, I had an appointment yesterday but had to cancel. Can I reschedule?", "timestamp_ms": 0},
                        {"speaker": "assistant", "text": "Of course! I can help you reschedule. Let me pull up your previous appointment details.", "timestamp_ms": 4000},
                        {"speaker": "customer", "text": "Thank you. I'm looking for a time next week.", "timestamp_ms": 12000},
                        {"speaker": "assistant", "text": "I see your previous appointment was for a haircut and styling. We have availability next Tuesday at 11 AM, Wednesday at 2 PM, or Thursday at 4 PM. Which works best for you?", "timestamp_ms": 15000},
                        {"speaker": "customer", "text": "Wednesday at 2 PM sounds great.", "timestamp_ms": 28000},
                        {"speaker": "assistant", "text": "Perfect! I've rescheduled your appointment for Wednesday at 2 PM. You'll receive a confirmation shortly. We look forward to seeing you!", "timestamp_ms": 31000}
                    ]
                }
                
                call_data = mock_calls[call_id]
                conversation = mock_conversations[call_id]
                insights = generate_call_insights(call_data, conversation)
                
                return JSONResponse(content={
                    "success": True,
                    "call": call_data,
                    "conversation": conversation,
                    "insights": insights
                })
            
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Call not found"}
            )
        
        return JSONResponse(content={
            "success": True,
            "call": call_data,
            "conversation": conversation,
            "insights": insights
        })
        
    except Exception as e:
        print(f"❌ Error getting call details: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


def generate_call_insights(call_data: dict, conversation: list) -> dict:
    """
    Generate insights from call data and conversation.
    
    Args:
        call_data: Call metadata
        conversation: List of conversation turns
        
    Returns:
        Dictionary of insights
    """
    insights = {
        "summary": "",
        "key_points": [],
        "sentiment": "neutral",
        "topics": [],
        "action_items": [],
        "customer_satisfaction": "unknown"
    }
    
    # Handle empty conversation
    if not conversation or len(conversation) == 0:
        # Generate insights from call metadata only
        duration = call_data.get('duration_seconds', 0)
        status = call_data.get('status', 'unknown')
        
        if status == 'initiated':
            insights["summary"] = "Call is in progress. Conversation data will be available after the call completes."
        elif status == 'completed' and duration == 0:
            insights["summary"] = "Call completed but no conversation was recorded."
        else:
            insights["summary"] = f"Call lasted {duration} seconds. No conversation transcript available yet."
        
        # Add basic key points from metadata
        if call_data.get('intent'):
            insights["key_points"].append(f"Intent: {call_data['intent'].replace('_', ' ').title()}")
        
        if call_data.get('language'):
            lang_names = {
                'en': 'English', 'hi': 'Hindi', 'ta': 'Tamil', 
                'te': 'Telugu', 'bn': 'Bengali'
            }
            insights["key_points"].append(f"Language: {lang_names.get(call_data['language'], call_data['language'])}")
        
        if call_data.get('caller_name'):
            insights["key_points"].append(f"Caller: {call_data['caller_name']}")
        
        insights["action_items"].append("Wait for call to complete to see full conversation analysis")
        
        return insights
    
    # Generate summary from conversation
    # Handle both 'caller' and 'customer' speaker types
    caller_turns = [turn for turn in conversation if turn['speaker'] in ['caller', 'customer']]
    assistant_turns = [turn for turn in conversation if turn['speaker'] == 'assistant']
    
    insights["summary"] = f"Call lasted {call_data.get('duration_seconds', 0)} seconds with {len(caller_turns)} customer messages and {len(assistant_turns)} AI responses."
    
    # Extract key points
    if call_data.get('intent'):
        insights["key_points"].append(f"Intent: {call_data['intent'].replace('_', ' ').title()}")
    
    if call_data.get('language'):
        lang_names = {
            'en': 'English', 'hi': 'Hindi', 'ta': 'Tamil', 
            'te': 'Telugu', 'bn': 'Bengali'
        }
        insights["key_points"].append(f"Language: {lang_names.get(call_data['language'], call_data['language'])}")
    
    # Analyze conversation for topics
    all_text = " ".join([turn['text'].lower() for turn in conversation])
    
    # Common topics
    topic_keywords = {
        "pricing": ["price", "cost", "fee", "charge", "expensive", "cheap"],
        "appointment": ["appointment", "schedule", "book", "reservation", "time", "date"],
        "service": ["service", "offer", "provide", "available"],
        "location": ["location", "address", "where", "directions"],
        "hours": ["hours", "open", "close", "timing", "when"],
        "complaint": ["problem", "issue", "complaint", "unhappy", "disappointed"]
    }
    
    for topic, keywords in topic_keywords.items():
        if any(keyword in all_text for keyword in keywords):
            insights["topics"].append(topic.title())
    
    # Simple sentiment analysis
    positive_words = ["thank", "great", "good", "excellent", "happy", "satisfied", "perfect"]
    negative_words = ["bad", "poor", "terrible", "unhappy", "disappointed", "problem", "issue"]
    
    positive_count = sum(1 for word in positive_words if word in all_text)
    negative_count = sum(1 for word in negative_words if word in all_text)
    
    if positive_count > negative_count:
        insights["sentiment"] = "positive"
        insights["customer_satisfaction"] = "satisfied"
    elif negative_count > positive_count:
        insights["sentiment"] = "negative"
        insights["customer_satisfaction"] = "unsatisfied"
    else:
        insights["sentiment"] = "neutral"
        insights["customer_satisfaction"] = "neutral"
    
    # Extract action items
    if "appointment" in insights["topics"]:
        insights["action_items"].append("Follow up on appointment booking")
    if "complaint" in insights["topics"]:
        insights["action_items"].append("Address customer complaint")
    if call_data.get('intent') == 'sales_inquiry':
        insights["action_items"].append("Send product information")
    
    return insights


@app.get("/api/events/live")
async def live_events_stream():
    """SSE stream of all live call events for the dashboard."""
    q = broadcaster.subscribe_global()
    
    async def event_generator():
        # Send a heartbeat immediately so the connection opens cleanly
        yield "data: {\"type\": \"connected\", \"message\": \"live feed ready\"}\n\n"
        try:
            async for chunk in broadcaster.stream(q):
                yield chunk
        finally:
            broadcaster.unsubscribe(q)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )


@app.get("/api/events/call/{call_sid}")
async def call_events_stream(call_sid: str):
    """SSE stream for a specific call — used by the call detail page."""
    q = broadcaster.subscribe_call(call_sid)
    
    async def event_generator():
        yield f"data: {{\"type\": \"connected\", \"call_sid\": \"{call_sid}\"}}\n\n"
        try:
            async for chunk in broadcaster.stream(q):
                yield chunk
        finally:
            broadcaster.unsubscribe(q, call_sid)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )


@app.get("/api/calls")
async def get_calls(
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> JSONResponse:
    """
    Get list of call records with optional filters.
    
    Args:
        status: Filter by call status (completed, in_progress, failed)
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        
    Returns:
        List of call records
        
    Requirement 15.5: Allow export of analytics data
    """
    try:
        # Try to get real data from database
        if database_service and not isinstance(database_service, AsyncMock):
            async with database_service.pool.acquire() as conn:
                query = "SELECT * FROM calls WHERE 1=1"
                params = []
                param_count = 1
                
                if status:
                    query += f" AND status = ${param_count}"
                    params.append(status)
                    param_count += 1
                
                if start_date:
                    query += f" AND started_at >= ${param_count}"
                    params.append(start_date)
                    param_count += 1
                
                if end_date:
                    query += f" AND started_at <= ${param_count}"
                    params.append(end_date)
                    param_count += 1
                
                query += " ORDER BY started_at DESC LIMIT 50"
                
                rows = await conn.fetch(query, *params)
                
                calls = []
                for row in rows:
                    calls.append({
                        "id": str(row['id']),
                        "caller_phone": row['caller_phone'],
                        "started_at": row['started_at'].isoformat() if row['started_at'] else None,
                        "duration_seconds": row['duration_seconds'],
                        "intent": row['intent'],
                        "status": row['status']
                    })
                
                return JSONResponse(content={"calls": calls})
    
    except Exception as e:
        print(f"Error fetching real calls: {e}")
    
    # Fall back to mock data
    calls = [
        {
            "id": "call-001",
            "caller_phone": "+1234567890",
            "started_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "duration_seconds": 245,
            "intent": "sales_inquiry",
            "status": "completed"
        },
        {
            "id": "call-002",
            "caller_phone": "+1987654321",
            "started_at": (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat(),
            "duration_seconds": 180,
            "intent": "appointment_booking",
            "status": "completed"
        },
        {
            "id": "call-003",
            "caller_phone": "+1555555555",
            "started_at": (datetime.now(timezone.utc) - timedelta(hours=8)).isoformat(),
            "duration_seconds": 320,
            "intent": "support_request",
            "status": "completed"
        }
    ]
    
    # Apply status filter if provided
    if status:
        calls = [c for c in calls if c["status"] == status]
    
    return JSONResponse(content={"calls": calls})


@app.get("/api/leads")
async def get_leads(filter: Optional[str] = None) -> JSONResponse:
    """
    Get list of leads with optional filtering by score.
    
    Args:
        filter: Filter by lead value (high: 7-10, medium: 4-6, low: 1-3)
        
    Returns:
        List of lead records with scoring
        
    Requirement 15.3: Dashboard with lead metrics
    """
    try:
        # Try to get real data from database
        if database_service and not isinstance(database_service, AsyncMock):
            async with database_service.pool.acquire() as conn:
                query = "SELECT * FROM leads WHERE 1=1"
                params = []
                
                if filter == "high":
                    query += " AND lead_score >= 7"
                elif filter == "medium":
                    query += " AND lead_score >= 4 AND lead_score < 7"
                elif filter == "low":
                    query += " AND lead_score < 4"
                
                query += " ORDER BY created_at DESC LIMIT 50"
                
                rows = await conn.fetch(query, *params)
                
                leads = []
                for row in rows:
                    leads.append({
                        "id": str(row['id']),
                        "name": row['name'],
                        "phone": row['phone'],
                        "email": row['email'],
                        "lead_score": row['lead_score'],
                        "budget_indication": row['budget_indication'],
                        "timeline": row['timeline'],
                        "inquiry_details": row['inquiry_details']
                    })
                
                return JSONResponse(content={"leads": leads})
    
    except Exception as e:
        print(f"Error fetching real leads: {e}")
    
    # Fall back to mock data
    leads = [
        {
            "id": "lead-001",
            "name": "John Smith",
            "phone": "+1234567890",
            "email": "john@example.com",
            "lead_score": 9,
            "budget_indication": "high",
            "timeline": "immediate",
            "inquiry_details": "Interested in enterprise solution"
        },
        {
            "id": "lead-002",
            "name": "Sarah Johnson",
            "phone": "+1987654321",
            "email": "sarah@example.com",
            "lead_score": 7,
            "budget_indication": "medium",
            "timeline": "short-term",
            "inquiry_details": "Looking for consultation"
        },
        {
            "id": "lead-003",
            "name": "Mike Davis",
            "phone": "+1555555555",
            "email": None,
            "lead_score": 4,
            "budget_indication": "low",
            "timeline": "long-term",
            "inquiry_details": "General inquiry about services"
        }
    ]
    
    # Apply filter if provided
    if filter == "high":
        leads = [l for l in leads if l["lead_score"] >= 7]
    elif filter == "medium":
        leads = [l for l in leads if 4 <= l["lead_score"] < 7]
    elif filter == "low":
        leads = [l for l in leads if l["lead_score"] < 4]
    
    return JSONResponse(content={"leads": leads})


@app.get("/api/appointments")
async def get_appointments() -> JSONResponse:
    """
    Get list of scheduled appointments.
    
    Returns:
        List of appointment records
        
    Requirement 15.3: Dashboard with appointment metrics
    """
    try:
        # Try to get real data from database
        if database_service and not isinstance(database_service, AsyncMock):
            async with database_service.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM appointments
                    WHERE appointment_datetime >= NOW()
                    ORDER BY appointment_datetime ASC
                    LIMIT 50
                """)
                
                appointments = []
                for row in rows:
                    appointments.append({
                        "id": str(row['id']),
                        "customer_name": row['customer_name'],
                        "customer_phone": row['customer_phone'],
                        "service_type": row['service_type'],
                        "appointment_datetime": row['appointment_datetime'].isoformat() if row['appointment_datetime'] else None,
                        "duration_minutes": row['duration_minutes'],
                        "status": row['status'],
                        "notes": row['notes']
                    })
                
                return JSONResponse(content={"appointments": appointments})
    
    except Exception as e:
        print(f"Error fetching real appointments: {e}")
    
    # Fall back to mock data
    appointments = [
        {
            "id": "appt-001",
            "customer_name": "John Smith",
            "customer_phone": "+1234567890",
            "service_type": "Consultation",
            "appointment_datetime": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "duration_minutes": 30,
            "status": "scheduled",
            "notes": "First-time customer"
        },
        {
            "id": "appt-002",
            "customer_name": "Sarah Johnson",
            "customer_phone": "+1987654321",
            "service_type": "Follow-up",
            "appointment_datetime": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "duration_minutes": 45,
            "status": "scheduled",
            "notes": None
        },
        {
            "id": "appt-003",
            "customer_name": "Mike Davis",
            "customer_phone": "+1555555555",
            "service_type": "Demo",
            "appointment_datetime": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
            "duration_minutes": 60,
            "status": "scheduled",
            "notes": "Interested in enterprise features"
        }
    ]
    
    return JSONResponse(content={"appointments": appointments})


@app.post("/api/appointments")
async def create_appointment(appointment: AppointmentRequest) -> JSONResponse:
    """
    Create a new appointment.
    
    Args:
        appointment: AppointmentRequest with customer details and appointment time
        
    Returns:
        Success confirmation with appointment ID
    """
    try:
        # Parse appointment_datetime from ISO string to timezone-aware datetime
        try:
            appt_dt = datetime.fromisoformat(appointment.appointment_datetime.replace('Z', '+00:00'))
            # Ensure it's timezone-aware
            if appt_dt.tzinfo is None:
                appt_dt = appt_dt.replace(tzinfo=timezone.utc)
        except Exception as parse_error:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": f"Invalid datetime format: {parse_error}"}
            )
        
        # Instantiate AppointmentManager
        from appointment_manager import AppointmentManager
        manager = AppointmentManager(database=database_service)
        
        # Validate call_id - must be None or a valid UUID
        call_id_to_use = None
        if appointment.call_id:
            # Try to validate it's a UUID
            try:
                from uuid import UUID
                UUID(appointment.call_id)  # This will raise ValueError if invalid
                call_id_to_use = appointment.call_id
            except (ValueError, AttributeError):
                # Invalid UUID, use None
                call_id_to_use = None
        
        # Book the appointment
        appointment_data, appointment_id = await manager.book_appointment(
            call_id=call_id_to_use,
            customer_name=appointment.customer_name,
            customer_phone=appointment.customer_phone,
            appointment_datetime=appt_dt,
            service_type=appointment.service_type,
            notes=appointment.notes
        )
        
        # Format success message
        formatted_date = appt_dt.strftime("%B %d, %Y at %I:%M %p")
        message = f"Appointment booked for {appointment.customer_name} on {formatted_date}"
        
        print(f"✅ Appointment created: {appointment_id}")
        
        return JSONResponse(content={
            "success": True,
            "appointment_id": appointment_id,
            "message": message
        })
        
    except Exception as e:
        print(f"❌ Error creating appointment: {e}")
        import traceback
        traceback.print_exc()
        
        # Handle mock database gracefully
        if isinstance(database_service, AsyncMock):
            mock_id = f"mock-appt-{uuid4().hex[:8]}"
            formatted_date = datetime.fromisoformat(appointment.appointment_datetime.replace('Z', '+00:00')).strftime("%B %d, %Y at %I:%M %p")
            return JSONResponse(content={
                "success": True,
                "appointment_id": mock_id,
                "message": f"Appointment booked for {appointment.customer_name} on {formatted_date} (mock mode)"
            })
        
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/config")
async def get_config() -> JSONResponse:
    """
    Get current business configuration.
    
    Returns:
        Current configuration including greeting, business hours, personality
        
    Requirement 17.1: Display current configuration
    """
    try:
        config = {
            "greeting": {
                "message": "Welcome to our AI-powered voice assistant. How can I help you today?"
            },
            "business_hours": {
                "weekday_start": "09:00",
                "weekday_end": "17:00",
                "weekend_start": "10:00",
                "weekend_end": "16:00"
            },
            "personality": {
                "tone": "professional",
                "style": "concise"
            },
            "languages": ["en", "hi", "ta", "te", "bn"],
            "company_description": {
                "text": COMPANY_DESCRIPTION
            }
        }
        
        # Try to get from database if available
        if database_service and not isinstance(database_service, AsyncMock):
            try:
                async with database_service.pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT * FROM business_config WHERE business_id = $1 AND active = TRUE",
                        "default"
                    )
                    
                    if row:
                        if row.get('greeting_message'):
                            config['greeting']['message'] = row['greeting_message']
                        
                        if row.get('business_hours'):
                            # Handle both string and dict types
                            hours_data = row['business_hours']
                            if isinstance(hours_data, str):
                                import json
                                config['business_hours'] = json.loads(hours_data)
                            elif isinstance(hours_data, dict):
                                config['business_hours'] = hours_data
                        
                        if row.get('ai_personality'):
                            # Handle both string and dict types
                            personality_data = row['ai_personality']
                            if isinstance(personality_data, str):
                                import json
                                config['personality'] = json.loads(personality_data)
                            elif isinstance(personality_data, dict):
                                config['personality'] = personality_data
                        
                        if row.get('supported_languages'):
                            # Handle both string and list types
                            lang_data = row['supported_languages']
                            if isinstance(lang_data, str):
                                import json
                                config['languages'] = json.loads(lang_data)
                            elif isinstance(lang_data, list):
                                config['languages'] = lang_data
                        
                        if row.get('company_description'):
                            config['company_description'] = {'text': row['company_description']}
                        
                        print(f"✅ Loaded configuration from database")
            except Exception as db_error:
                print(f"⚠️  Database error loading config: {db_error}")
                # Continue with default config
        
        # Check memory config (overrides database)
        if hasattr(app.state, 'config'):
            for key, value in app.state.config.items():
                if key in config:
                    config[key] = value
        
        return JSONResponse(content={
            "success": True,
            "config": config
        })
        
    except Exception as e:
        print(f"❌ Error getting config: {e}")
        import traceback
        traceback.print_exc()
        
        # Return default config even on error
        return JSONResponse(content={
            "success": True,
            "config": {
                "greeting": {
                    "message": "Welcome to our AI-powered voice assistant. How can I help you today?"
                },
                "business_hours": {
                    "weekday_start": "09:00",
                    "weekday_end": "17:00"
                },
                "personality": {
                    "tone": "professional",
                    "style": "concise"
                },
                "languages": ["en", "hi", "ta", "te", "bn"]
            }
        })


@app.post("/api/config")
async def update_config(request: Request) -> JSONResponse:
    """
    Update business configuration.
    
    Accepts configuration updates for:
    - Business hours
    - Greeting message
    - AI personality
    
    Returns:
        Success confirmation
        
    Requirement 17.1: Allow customization of greeting, AI personality, conversation flow
    """
    try:
        data = await request.json()
        config_type = data.get("type")
        config_data = data.get("data")
        
        print(f"📝 Configuration update: {config_type}")
        print(f"   Data: {config_data}")
        
        # Save to database if available
        if database_service and not isinstance(database_service, AsyncMock):
            try:
                async with database_service.pool.acquire() as conn:
                    # Check if config exists
                    existing = await conn.fetchrow(
                        "SELECT * FROM business_config WHERE business_id = $1",
                        "default"
                    )
                    
                    if existing:
                        # Update existing config
                        if config_type == "greeting":
                            await conn.execute(
                                "UPDATE business_config SET greeting_message = $1, updated_at = NOW() WHERE business_id = $2",
                                config_data.get("message"),
                                "default"
                            )
                        elif config_type == "business_hours":
                            import json
                            await conn.execute(
                                "UPDATE business_config SET business_hours = $1, updated_at = NOW() WHERE business_id = $2",
                                json.dumps(config_data),
                                "default"
                            )
                        elif config_type == "personality":
                            import json
                            await conn.execute(
                                "UPDATE business_config SET ai_personality = $1, updated_at = NOW() WHERE business_id = $2",
                                json.dumps(config_data),
                                "default"
                            )
                    else:
                        # Insert new config
                        import json
                        greeting = config_data.get("message") if config_type == "greeting" else "Hello! How can I help you today?"
                        hours = json.dumps(config_data) if config_type == "business_hours" else json.dumps({})
                        personality = json.dumps(config_data) if config_type == "personality" else json.dumps({})
                        
                        await conn.execute("""
                            INSERT INTO business_config (business_id, greeting_message, business_hours, ai_personality, active, created_at, updated_at)
                            VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                        """, "default", greeting, hours, personality, True)
                    
                    print(f"   ✅ Saved to database")
                    
                    # Update language manager with new greeting if it's a greeting update
                    if config_type == "greeting" and language_manager:
                        language_manager.base_instructions = config_data.get("message")
                        print(f"   ✅ Updated AI greeting in memory")
                    
            except Exception as db_error:
                print(f"   ⚠️  Database error: {db_error}")
                # Continue anyway - config will be in memory
        
        # Handle company_description separately (special case with system prompt rebuild)
        if config_type == "company_description":
            # Validate it's not empty
            description_text = config_data.get("text", "").strip()
            if not description_text:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "Company description cannot be empty"}
                )
            
            # Save to database if available
            if database_service and not isinstance(database_service, AsyncMock):
                try:
                    async with database_service.pool.acquire() as conn:
                        await conn.execute(
                            """UPDATE business_config
                                SET company_description = $1, updated_at = NOW()
                                WHERE business_id = $2""",
                            description_text, "default"
                        )
                    print(f"   ✅ Company description saved to database")
                except Exception as db_error:
                    print(f"   ⚠️  Database error saving description: {db_error}")
            
            # Store in memory immediately
            if not hasattr(app.state, 'config'):
                app.state.config = {}
            app.state.config['company_description'] = {'text': description_text}
            
            # Rebuild system message with new description so next call uses it
            kb_text = getattr(app.state, 'knowledge_base', '')
            business_name = app.state.config.get('business_name', {}).get('name', BUSINESS_NAME)
            business_type = app.state.config.get('business_type', {}).get('type', BUSINESS_TYPE)
            tone = app.state.config.get('personality', {}).get('tone', 'professional')
            style = app.state.config.get('personality', {}).get('style', 'concise')
            
            rebuilt_prompt = get_system_message(
                business_name=business_name,
                business_type=business_type,
                knowledge_base_text=kb_text,
                company_description=description_text,
                tone=tone,
                style=style
            )
            
            if language_manager:
                language_manager.base_instructions = rebuilt_prompt
            
            app.state.active_system_prompt = rebuilt_prompt
            app.state.prompt_last_updated = datetime.now(timezone.utc).isoformat()
            
            word_count = len(description_text.split())
            print(f"   ✅ Company description updated ({word_count} words). System prompt rebuilt.")
            
            return JSONResponse(content={
                "success": True,
                "message": f"Company description updated ({word_count} words). Active on next call."
            })
        
        # Store in memory for immediate use
        if not hasattr(app.state, 'config'):
            app.state.config = {}
        app.state.config[config_type] = config_data
        
        return JSONResponse(content={
            "success": True,
            "message": f"Configuration '{config_type}' updated successfully and will be used in next call"
        })
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/system-prompt")
async def get_system_prompt_debug() -> JSONResponse:
    """
    Debug endpoint to view current system prompt configuration.
    
    Returns:
        System prompt details including language support and company description
    """
    try:
        # Get current configuration
        business_name = BUSINESS_NAME
        business_type = BUSINESS_TYPE
        company_description = COMPANY_DESCRIPTION
        tone = "professional"
        style = "concise"
        kb_text = ""
        
        if hasattr(app.state, 'config'):
            if 'business_name' in app.state.config:
                business_name = app.state.config['business_name'].get('name', BUSINESS_NAME)
            if 'business_type' in app.state.config:
                business_type = app.state.config['business_type'].get('type', BUSINESS_TYPE)
            if 'company_description' in app.state.config:
                company_description = app.state.config['company_description'].get('text', '')
            if 'personality' in app.state.config:
                tone = app.state.config['personality'].get('tone', 'professional')
                style = app.state.config['personality'].get('style', 'concise')
        
        if hasattr(app.state, 'knowledge_base'):
            kb_text = app.state.knowledge_base
        
        # Generate current system message
        current_prompt = get_system_message(
            business_name=business_name,
            business_type=business_type,
            knowledge_base_text=kb_text,
            company_description=company_description,
            tone=tone,
            style=style
        )
        
        return JSONResponse(content={
            "success": True,
            "business_name": business_name,
            "business_type": business_type,
            "tone": tone,
            "style": style,
            "supported_languages": SUPPORTED_LANGUAGES,
            "language_names": LANGUAGE_NAMES,
            "company_description_words": len(company_description.split()) if company_description else 0,
            "company_description_preview": company_description[:200] if company_description else "not set",
            "knowledge_base_chars": len(kb_text),
            "system_prompt_chars": len(current_prompt),
            "system_prompt_preview": current_prompt[:500] + "..." if len(current_prompt) > 500 else current_prompt
        })
        
    except Exception as e:
        print(f"❌ Error getting system prompt: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/documents")
async def get_documents() -> JSONResponse:
    """
    Get list of uploaded documents in knowledge base.
    
    Returns:
        List of uploaded documents with metadata
        
    Requirement 17.1: Display uploaded documents
    """
    try:
        documents = []
        
        # Try to get from database if available
        if database_service and not isinstance(database_service, AsyncMock):
            try:
                async with database_service.pool.acquire() as conn:
                    rows = await conn.fetch("""
                        SELECT id, filename, file_type, uploaded_at, 
                               LENGTH(content) as size, active
                        FROM knowledge_base
                        WHERE active = TRUE
                        ORDER BY uploaded_at DESC
                        LIMIT 50
                    """)
                    
                    for row in rows:
                        documents.append({
                            "id": str(row['id']),
                            "filename": row['filename'],
                            "file_type": row['file_type'],
                            "size": row['size'],
                            "uploaded_at": row['uploaded_at'].isoformat() if row['uploaded_at'] else None,
                            "active": row['active']
                        })
                    
                    print(f"✅ Loaded {len(documents)} documents from database")
            except Exception as db_error:
                print(f"⚠️  Database error loading documents: {db_error}")
        
        return JSONResponse(content={
            "success": True,
            "documents": documents,
            "count": len(documents)
        })
        
    except Exception as e:
        print(f"❌ Error getting documents: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/documents")
async def upload_documents(files: List[UploadFile] = File(...)) -> JSONResponse:
    """
    Upload company documents for knowledge base.
    
    Accepts PDF, DOCX, TXT files for AI knowledge base.
    Extracts text and stores for AI to use in conversations.
    
    Returns:
        Upload confirmation with file count
        
    Requirement 17.1: Support uploading business-specific knowledge bases
    """
    try:
        uploaded_files = []
        knowledge_base_texts = []
        
        # Create documents directory if it doesn't exist
        import os
        os.makedirs("documents", exist_ok=True)
        
        for file in files:
            # Validate file type
            allowed_types = [
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain"
            ]
            
            if file.content_type not in allowed_types:
                print(f"   ⚠️  Skipping {file.filename} - unsupported type: {file.content_type}")
                continue
            
            # Read file content
            content = await file.read()
            file_path = f"documents/{file.filename}"
            
            # Save file to disk
            with open(file_path, "wb") as f:
                f.write(content)
            
            print(f"📄 Processing document: {file.filename}")
            
            # Extract text based on file type
            extracted_text = ""
            
            if file.content_type == "application/pdf":
                # Extract text from PDF
                try:
                    import PyPDF2
                    import io
                    
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                    for page in pdf_reader.pages:
                        extracted_text += page.extract_text() + "\n"
                    
                    print(f"   ✅ Extracted {len(extracted_text)} characters from PDF")
                    
                except ImportError:
                    print(f"   ⚠️  PyPDF2 not installed. Install with: pip install PyPDF2")
                    extracted_text = f"[PDF content from {file.filename} - install PyPDF2 to extract text]"
                except Exception as e:
                    print(f"   ⚠️  Error extracting PDF: {e}")
                    extracted_text = f"[Error extracting PDF: {e}]"
            
            elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                # Extract text from DOCX
                try:
                    import docx
                    import io
                    
                    doc = docx.Document(io.BytesIO(content))
                    for paragraph in doc.paragraphs:
                        extracted_text += paragraph.text + "\n"
                    
                    print(f"   ✅ Extracted {len(extracted_text)} characters from DOCX")
                    
                except ImportError:
                    print(f"   ⚠️  python-docx not installed. Install with: pip install python-docx")
                    extracted_text = f"[DOCX content from {file.filename} - install python-docx to extract text]"
                except Exception as e:
                    print(f"   ⚠️  Error extracting DOCX: {e}")
                    extracted_text = f"[Error extracting DOCX: {e}]"
            
            elif file.content_type == "text/plain":
                # Read plain text
                extracted_text = content.decode('utf-8', errors='ignore')
                print(f"   ✅ Read {len(extracted_text)} characters from TXT")
            
            # Store in database if available
            if database_service and not isinstance(database_service, AsyncMock):
                try:
                    async with database_service.pool.acquire() as conn:
                        await conn.execute("""
                            INSERT INTO knowledge_base (filename, content, file_type, uploaded_at)
                            VALUES ($1, $2, $3, NOW())
                        """, file.filename, extracted_text, file.content_type)
                    
                    print(f"   ✅ Saved to database")
                except Exception as db_error:
                    print(f"   ⚠️  Database error: {db_error}")
            
            # Add to knowledge base for AI
            knowledge_base_texts.append({
                "filename": file.filename,
                "content": extracted_text
            })
            
            uploaded_files.append(file.filename)
        
        # Update language manager with knowledge base
        if knowledge_base_texts and language_manager:
            # Combine all knowledge base texts
            combined_knowledge = "\n\n".join([
                f"=== {doc['filename']} ===\n{doc['content']}"
                for doc in knowledge_base_texts
            ])
            
            # Update base instructions to include knowledge base
            if hasattr(app.state, 'knowledge_base'):
                app.state.knowledge_base += "\n\n" + combined_knowledge
            else:
                app.state.knowledge_base = combined_knowledge
            
            print(f"   ✅ Updated AI knowledge base with {len(knowledge_base_texts)} document(s)")
        
        return JSONResponse(content={
            "success": True,
            "uploaded": len(uploaded_files),
            "files": uploaded_files,
            "message": f"Uploaded {len(uploaded_files)} document(s). AI will use this information in conversations."
        })
        
    except Exception as e:
        print(f"   ❌ Error uploading documents: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )


async def maybe_book_appointment(call_sid: str, caller_phone: str, transcript_text: str) -> None:
    """
    Check if the AI assistant confirmed an appointment booking and auto-save it.
    
    This is a fire-and-forget function that runs in the background during calls.
    It detects booking confirmation phrases and extracts appointment details.
    
    Args:
        call_sid: Twilio call SID
        caller_phone: Caller's phone number
        transcript_text: The AI assistant's response text
    """
    try:
        # Check if transcript contains booking confirmation phrases
        text_lower = transcript_text.lower()
        booking_phrases = [
            "i've scheduled",
            "i've booked",
            "booked for",
            "appointment confirmed",
            "scheduled for",
            "appointment is set",
            "i have booked"
        ]
        
        if not any(phrase in text_lower for phrase in booking_phrases):
            return  # Not a booking confirmation
        
        print(f"🔍 Detected appointment booking confirmation in call {call_sid}")
        
        # Get active call context
        if not call_manager or not hasattr(call_manager, 'active_calls'):
            print(f"   ⚠️  CallManager not available")
            return
        
        context = call_manager.active_calls.get(call_sid)
        if not context:
            print(f"   ⚠️  Call context not found for {call_sid}")
            return
        
        # Get conversation history
        conversation_history = getattr(context, 'conversation_history', [])
        if not conversation_history:
            print(f"   ⚠️  No conversation history available")
            return
        
        # Extract appointment info using AppointmentManager
        from appointment_manager import AppointmentManager
        manager = AppointmentManager(database=database_service)
        
        info = await manager.extract_appointment_info(conversation_history, caller_phone)
        
        if not info:
            print(f"   ⚠️  Could not extract appointment info from conversation")
            return
        
        # Get preferred datetime, default to tomorrow if not specified
        appt_dt = info.get("preferred_datetime")
        if not appt_dt:
            appt_dt = datetime.now(timezone.utc) + timedelta(days=1)
            appt_dt = appt_dt.replace(hour=10, minute=0, second=0, microsecond=0)  # Default to 10 AM
        
        # Ensure timezone-aware
        if appt_dt.tzinfo is None:
            appt_dt = appt_dt.replace(tzinfo=timezone.utc)
        
        # Book the appointment
        appointment_data, appt_id = await manager.book_appointment(
            call_id=context.call_id,
            customer_name=info["customer_name"],
            customer_phone=info["customer_phone"],
            appointment_datetime=appt_dt,
            service_type=info.get("service_type", "general"),
            notes=None
        )
        
        print(f"✅ Appointment auto-saved: {appt_id} for {info['customer_name']}")
        
    except Exception as e:
        print(f"⚠️  Error in maybe_book_appointment: {e}")
        import traceback
        traceback.print_exc()
        # Don't raise - this is fire-and-forget


@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket) -> None:
    """
    Handle WebSocket connections between Twilio and OpenAI with AI features.
    
    Enhanced with:
    - Call lifecycle management
    - Language detection (first 10 seconds)
    - Intent detection with clarification
    - Call routing decisions
    - Custom greeting from configuration
    - Knowledge base from uploaded documents
    
    Args:
        websocket: WebSocket connection from Twilio
    """
    print("🔌 Client connected to media stream")
    await websocket.accept()
    
    # Extract call_sid from query parameters
    call_sid_from_query = websocket.query_params.get('call_sid')
    if call_sid_from_query:
        print(f"📞 Call SID from query: {call_sid_from_query}")
    else:
        print(f"⚠️  No call_sid in query parameters!")
        print(f"   This means Twilio is NOT calling /incoming-call first")
        print(f"   Query params: {dict(websocket.query_params)}")
        print(f"   Will wait for call_sid from Twilio start event...")
    
    # FALLBACK: If call doesn't exist in database, create it now
    # This handles cases where Twilio calls /media-stream directly
    if call_sid_from_query and call_manager:
        print(f"🔍 Checking if call exists in cache/database...")
        try:
            # Check if call exists
            existing_call = await call_manager.get_call_context(call_sid_from_query)
            print(f"   Cache check result: {existing_call is not None}")
            
            if not existing_call:
                # Try to get from database
                call_record = await database_service.get_call_by_sid(call_sid_from_query) if database_service else None
                print(f"   Database check result: {call_record is not None}")
                
                if not call_record:
                    print(f"⚠️  Call not found, creating it now (Twilio bypassed /incoming-call)")
                    # Extract caller phone from Twilio metadata if available
                    # For now, use a placeholder - Twilio will send it in the first message
                    context = await call_manager.initiate_call(
                        call_sid=call_sid_from_query,
                        caller_phone="unknown",  # Will be updated from Twilio messages
                        direction="inbound"
                    )
                    print(f"✅ Call created in WebSocket handler: {context.call_id}")
                    print(f"   Verifying Redis storage...")
                    verify = await call_manager.get_call_context(call_sid_from_query)
                    print(f"   Redis verification: {verify is not None}")
                else:
                    print(f"✅ Call found in database: {call_record.get('id')}")
            else:
                print(f"✅ Call found in cache: {existing_call.call_id}")
        except Exception as e:
            print(f"⚠️  Error checking/creating call: {e}")
            import traceback
            traceback.print_exc()
    elif call_sid_from_query:
        print(f"❌ call_manager is None! Cannot create call.")

    ssl_context = create_ssl_context()
    call_start_time = datetime.now(timezone.utc)
    state = None  # Initialize state outside try block
    
    # Build system message using get_system_message function
    business_name = BUSINESS_NAME
    business_type = BUSINESS_TYPE
    knowledge_base_text = ""
    company_description = ""
    tone = "professional"
    style = "concise"
    
    # Load configuration from app.state if available
    if hasattr(app.state, 'config'):
        if 'business_name' in app.state.config:
            business_name = app.state.config['business_name'].get('name', BUSINESS_NAME)
        if 'business_type' in app.state.config:
            business_type = app.state.config['business_type'].get('type', BUSINESS_TYPE)
        if 'company_description' in app.state.config:
            company_description = app.state.config['company_description'].get('text', '')
        if 'personality' in app.state.config:
            tone = app.state.config['personality'].get('tone', 'professional')
            style = app.state.config['personality'].get('style', 'concise')
    
    # Priority order for company_description: memory config > env var > empty
    if not company_description and COMPANY_DESCRIPTION:
        company_description = COMPANY_DESCRIPTION
    
    # Add knowledge base if available
    if hasattr(app.state, 'knowledge_base') and app.state.knowledge_base:
        knowledge_base_text = app.state.knowledge_base
        print(f"📚 Using knowledge base ({len(knowledge_base_text)} characters)")
    
    # Generate multilingual system message
    custom_instructions = get_system_message(
        business_name=business_name,
        business_type=business_type,
        knowledge_base_text=knowledge_base_text,
        company_description=company_description,
        tone=tone,
        style=style
    )
    print(f"🌍 System message generated with multilingual support ({len(SUPPORTED_LANGUAGES)} languages)")
    
    try:
        async with websockets.connect(
            f"wss://api.openai.com/v1/realtime?model={OPENAI_REALTIME_MODEL}&temperature={TEMPERATURE}",
            additional_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            },
            ssl=ssl_context
        ) as openai_ws:
            # Initialize session with custom instructions and tools
            from tools.appointment_tools import ALL_TOOLS
            
            # Convert tool definitions to dict format for OpenAI
            tools_config = [
                {
                    "type": tool.type,
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
                for tool in ALL_TOOLS
            ]
            
            session_update = {
                "type": "session.update",
                "session": {
                    "type": "realtime",
                    "model": OPENAI_REALTIME_MODEL,
                    "output_modalities": ["audio"],
                    "audio": {
                        "input": {
                            "format": {"type": "audio/pcmu"},
                            "turn_detection": {"type": "server_vad"}
                        },
                        "output": {
                            "format": {"type": "audio/pcmu"},
                            "voice": "alloy"
                        }
                    },
                    "instructions": custom_instructions,
                    # Add tools for function calling
                    "tools": tools_config,
                    "tool_choice": "auto"  # Let AI decide when to use tools
                }
            }
            print(f'📡 Sending session update with multilingual instructions and {len(tools_config)} tools')
            for tool in tools_config:
                print(f'   • {tool["name"]}: {tool["description"][:60]}...')
            await openai_ws.send(json.dumps(session_update))

            # Initialize session state with AI features
            state = SessionState()
            state.call_manager = call_manager
            state.intent_detector = intent_detector
            state.language_manager = language_manager
            state.call_router = call_router
            state.call_start_time = call_start_time
            # Language tracking
            state.detected_language = "unknown"
            state.language_confirmed = False
            # Set call_sid from query parameter
            if call_sid_from_query:
                state.call_sid = call_sid_from_query
                print(f"✅ Call SID set in state: {call_sid_from_query}")
            
            # Initialize tool executor for function calling
            if appointment_manager and database_service:
                try:
                    # Import lead_manager if available
                    lead_mgr = None
                    try:
                        from lead_manager import LeadManager
                        lead_mgr = LeadManager(database=database_service)
                    except:
                        pass
                    
                    state.initialize_tool_executor(
                        appointment_manager=appointment_manager,
                        database=database_service,
                        lead_manager=lead_mgr
                    )
                    print("✅ Tool executor initialized with appointment and lead management")
                except Exception as tool_init_error:
                    print(f"⚠️  Error initializing tool executor: {tool_init_error}")
            else:
                print("⚠️  Tool executor not initialized (missing dependencies)")
            
            print("✅ Session initialized with AI features and custom configuration")
            
            # Run both handlers concurrently
            try:
                # Create tasks so we can cancel them if needed
                receive_task = asyncio.create_task(receive_from_twilio(websocket, openai_ws, state))
                send_task = asyncio.create_task(send_to_twilio(websocket, openai_ws, state))
                
                # Wait for both tasks with a timeout
                done, pending = await asyncio.wait(
                    [receive_task, send_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Cancel any pending tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        print(f"✅ Task cancelled successfully")
                
                print("🏁 Both WebSocket handlers completed")
            except Exception as gather_error:
                print(f"⚠️  Error in asyncio.wait: {gather_error}")
                import traceback
                traceback.print_exc()
    except Exception as e:
        print(f"⚠️  WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"🔚 Finally block executing...")
        # Complete the call when WebSocket disconnects
        if call_manager and state and hasattr(state, 'call_sid') and state.call_sid:
            try:
                # Log call summary with language
                detected_lang = getattr(state, 'detected_language', 'unknown')
                print(f"📊 Call summary: language={detected_lang}, sid={state.call_sid}")
                
                print(f"📞 Call ended, completing call: {state.call_sid}")
                
                # Broadcast call_end event
                asyncio.create_task(broadcaster.publish("call_end", {
                    "call_sid": state.call_sid,
                    "language": getattr(state, 'detected_language', 'unknown'),
                    "duration_ms": int((datetime.now(timezone.utc) - state.call_start_time).total_seconds() * 1000) if state.call_start_time else 0
                }))
                
                try:
                    await call_manager.complete_call(state.call_sid)
                except ValueError as e:
                    print(f"⚠️ Could not complete call record: {e}")
                    # Call audio still worked fine — this is just a DB cleanup issue
                else:
                    print(f"✅ Call completed and transcripts saved")
            except Exception as e:
                print(f"⚠️  Error completing call: {e}")
                import traceback
                traceback.print_exc()
        elif state and hasattr(state, 'stream_sid') and state.stream_sid:
            print(f"⚠️  Call ended but call_sid not found (stream_sid: {state.stream_sid})")
        else:
            print(f"⚠️  Finally block: state or call_sid not available")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
