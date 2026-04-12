# Backend Documentation

## Overview

This is an AI-powered voice automation system built with FastAPI that integrates Twilio for phone calls and OpenAI's Realtime API for conversational AI. The system handles inbound calls, detects intent and language, manages appointments, captures leads, and provides real-time analytics.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│                         (main.py)                            │
└──────────────┬──────────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
   ┌───▼────┐      ┌───▼────┐
   │ Twilio │      │ OpenAI │
   │  Call  │      │   AI   │
   └───┬────┘      └───┬────┘
       │                │
       └───────┬────────┘
               │
    ┌──────────▼──────────┐
    │   WebSocket Layer   │
    │    (handlers.py)    │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │   AI Services       │
    │  - CallManager      │
    │  - IntentDetector   │
    │  - LanguageManager  │
    │  - CallRouter       │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │   Data Layer        │
    │  - PostgreSQL       │
    │  - Redis Cache      │
    │  - Qdrant Vector DB │
    └─────────────────────┘
```

## File Structure

### Main Application Files

- **main.py** - FastAPI application entry point
  - HTTP endpoints for webhooks and API
  - WebSocket handling for real-time communication
  - Service initialization and lifecycle management
  - Dashboard analytics endpoints

- **handlers.py** - WebSocket event handlers
  - Bidirectional communication between Twilio and OpenAI
  - Real-time audio streaming
  - Conversation transcript processing
  - Tool call execution

- **config.py** - Configuration management
  - Environment variables
  - Business settings (name, type, agent name)
  - Language configuration (5 languages supported)
  - System message generation

### AI Services

- **call_manager.py** - Central call orchestration
  - Call lifecycle management (initiate, answer, complete)
  - Conversation history tracking
  - Language and intent detection coordination
  - Lead and appointment analysis

- **intent_detector.py** - Intent classification
  - Analyzes conversation to detect caller intent
  - Supports: sales inquiry, support, appointment, complaint, general
  - Confidence scoring
  - Clarification handling

- **language_manager.py** - Multi-language support
  - Detects language from speech (EN, HI, TA, TE, BN)
  - Dynamic system message translation
  - Language-specific greetings and responses

- **call_router.py** - Intelligent call routing
  - Priority-based routing rules
  - Business hours checking
  - Agent skill matching
  - Queue management

- **lead_manager.py** - Lead capture and scoring
  - Extracts lead information from conversations
  - Scores leads (1-10) based on quality signals
  - Tracks budget, timeline, decision authority

- **appointment_manager.py** - Appointment scheduling
  - Business hours validation
  - Time slot availability checking
  - Appointment booking and confirmation
  - Calendar integration ready

### Tool System

- **tools/appointment_tools.py** - Appointment booking tools
  - `book_appointment` - Schedule appointments
  - `check_availability` - Check time slot availability
  - `get_business_hours` - Retrieve business hours

- **tools/rag_tool.py** - Knowledge base retrieval
  - `search_knowledge_base` - Semantic search in documents
  - Vector database integration (Qdrant)
  - Context-aware responses

- **tools/tool_executor.py** - Tool execution engine
  - Validates and executes tool calls
  - Manages tool registry
  - Error handling and logging

### Data Layer

- **database.py** - PostgreSQL database service
  - Connection pooling
  - Call records (CRUD operations)
  - Transcript storage
  - Lead and appointment management
  - Business configuration

- **redis_service.py** - Redis caching
  - Session state management
  - Caller history caching
  - Real-time data storage
  - TTL-based expiration

- **vector_service.py** - Vector database (Qdrant)
  - Document embedding and storage
  - Semantic search
  - RAG (Retrieval-Augmented Generation)
  - Knowledge base synchronization

### Models & Utilities

- **models.py** - Data models and enums
  - `CallContext` - Complete call session data
  - `LeadData` - Lead information structure
  - `AppointmentData` - Appointment details
  - Enums: `CallStatus`, `Intent`, `Language`

- **session.py** - WebSocket session state
  - Manages per-call state
  - Audio buffer tracking
  - Interruption handling
  - Service references

- **utils.py** - Utility functions
  - SSL context creation
  - Session initialization
  - Audio buffer management
  - Mark and truncate events

- **event_broadcaster.py** - Server-Sent Events (SSE)
  - Real-time event broadcasting
  - Dashboard live updates
  - Multi-client support

### Supporting Services

- **transcript_service.py** - Transcript processing
  - Real-time transcription
  - Speaker identification
  - Timestamp management

- **fallback_handler.py** - Error handling
  - Graceful degradation
  - Fallback responses
  - Error recovery

## Database Schema

### Tables

**calls**
- `id` (UUID) - Primary key
- `call_sid` (VARCHAR) - Twilio call SID
- `caller_phone` (VARCHAR) - Caller's phone number
- `caller_name` (VARCHAR) - Caller's name
- `status` (VARCHAR) - Call status
- `intent` (VARCHAR) - Detected intent
- `intent_confidence` (DECIMAL) - Confidence score
- `language` (VARCHAR) - Detected language
- `started_at` (TIMESTAMP) - Call start time
- `ended_at` (TIMESTAMP) - Call end time
- `duration_seconds` (INTEGER) - Call duration
- `metadata` (JSONB) - Additional data

**transcripts**
- `id` (UUID) - Primary key
- `call_id` (UUID) - Foreign key to calls
- `speaker` (VARCHAR) - Speaker identifier
- `text` (TEXT) - Transcript text
- `timestamp_ms` (BIGINT) - Timestamp in milliseconds
- `language` (VARCHAR) - Language code
- `confidence` (DECIMAL) - Confidence score

**leads**
- `id` (UUID) - Primary key
- `call_id` (UUID) - Foreign key to calls
- `name` (VARCHAR) - Lead name
- `phone` (VARCHAR) - Phone number
- `email` (VARCHAR) - Email address
- `inquiry_details` (TEXT) - Inquiry description
- `budget_indication` (VARCHAR) - Budget level
- `timeline` (VARCHAR) - Purchase timeline
- `decision_authority` (BOOLEAN) - Decision maker flag
- `lead_score` (INTEGER) - Score 1-10
- `source` (VARCHAR) - Lead source
- `created_at` (TIMESTAMP) - Creation time

**appointments**
- `id` (UUID) - Primary key
- `call_id` (UUID) - Foreign key to calls
- `customer_name` (VARCHAR) - Customer name
- `customer_phone` (VARCHAR) - Phone number
- `customer_email` (VARCHAR) - Email address
- `service_type` (VARCHAR) - Service requested
- `appointment_datetime` (TIMESTAMP) - Scheduled time
- `duration_minutes` (INTEGER) - Duration
- `notes` (TEXT) - Additional notes
- `status` (VARCHAR) - Appointment status
- `created_at` (TIMESTAMP) - Creation time

**business_config**
- `business_id` (VARCHAR) - Business identifier
- `business_name` (VARCHAR) - Business name
- `greeting_message` (TEXT) - Custom greeting
- `active` (BOOLEAN) - Active flag

## API Endpoints

### HTTP Endpoints

**GET /** - Health check and status
- Returns system status and enabled features

**GET /health** - Health check
- Returns database and Redis connection status

**POST /incoming-call** - Twilio webhook
- Handles incoming calls
- Returns TwiML response
- Initiates call tracking

**GET /api/analytics** - Dashboard analytics
- Returns call volume, intent distribution
- Recent activity feed
- Lead and appointment counts

**GET /api/calls/{call_id}** - Call details
- Returns complete call information
- Conversation transcript
- AI-generated insights

**POST /api/appointments** - Create appointment
- Manual appointment creation
- Validates business hours
- Returns appointment ID

**GET /api/events** - SSE endpoint
- Real-time event stream
- Live dashboard updates

### WebSocket Endpoints

**WS /media-stream** - Twilio Media Stream
- Bidirectional audio streaming
- Real-time conversation processing
- Tool call execution

## Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview
TEMPERATURE=0.8

# Server Configuration
PORT=5050

# Business Configuration
BUSINESS_NAME=Your Business Name
BUSINESS_TYPE=salon
AGENT_NAME=Alex
COMPANY_DESCRIPTION=Your company description

# Database Configuration
USE_REAL_DB=true
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_automation
DB_USER=postgres
DB_PASSWORD=your_password
DB_SSLMODE=require

# Redis Configuration
USE_REAL_REDIS=true
REDIS_HOST=localhost
REDIS_PORT=6379

# Qdrant Configuration (Vector DB)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_api_key
QDRANT_COLLECTION=knowledge_base
```

## Key Features

### 1. Multi-Language Support
- Detects language in first 10 seconds
- Supports: English, Hindi, Tamil, Telugu, Bengali
- Dynamic response translation

### 2. Intent Detection
- Real-time intent classification
- Confidence scoring
- Automatic clarification when uncertain

### 3. Lead Capture
- Automatic lead extraction from conversations
- Lead scoring (1-10)
- Tracks budget, timeline, decision authority

### 4. Appointment Booking
- Business hours validation
- Time slot availability
- Automatic confirmation

### 5. Conversation History
- Returning caller recognition
- Context-aware responses
- Full transcript storage

### 6. RAG (Retrieval-Augmented Generation)
- Vector database integration
- Semantic search in knowledge base
- Context-aware answers

### 7. Real-Time Analytics
- Live dashboard updates
- Call volume trends
- Intent distribution
- Lead and appointment tracking

### 8. Interruption Handling
- Detects speech within 300ms
- Stops AI audio immediately
- Preserves conversation context

## Running the Application

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Set up database
./setup_database.sh

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Start Server
```bash
# Development
python main.py

# Production (with uvicorn)
uvicorn main:app --host 0.0.0.0 --port 5050
```

### Database Migrations
```bash
# Run migrations
python migrations/run_migration.py

# Validate schema
python migrations/validate_migration.py
```

## Testing

The system includes comprehensive test coverage (removed for production):
- Unit tests for each service
- Integration tests for API endpoints
- WebSocket connection tests
- Database operation tests

## Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5050"]
```

### Environment Setup
1. Set up PostgreSQL database
2. Set up Redis cache
3. Set up Qdrant vector database (optional)
4. Configure Twilio webhook URL
5. Set environment variables
6. Run migrations
7. Start application

## Monitoring

- Health check endpoint: `/health`
- Real-time logs via console
- Database connection pooling metrics
- Redis cache hit rates
- Call volume and duration tracking

## Security

- SSL/TLS for all connections
- Environment variable configuration
- Database connection pooling
- Input validation and sanitization
- Error handling and logging

## Performance

- Connection pooling (10-50 connections)
- Redis caching for session data
- Async/await for non-blocking I/O
- WebSocket for real-time communication
- Vector database for fast semantic search

## Troubleshooting

### Common Issues

1. **Database connection failed**
   - Check DB credentials in .env
   - Verify PostgreSQL is running
   - Check SSL mode configuration

2. **Redis connection failed**
   - Verify Redis is running
   - Check host and port
   - Falls back to in-memory storage

3. **OpenAI API errors**
   - Verify API key is valid
   - Check rate limits
   - Monitor token usage

4. **Twilio webhook not receiving calls**
   - Verify webhook URL is publicly accessible
   - Check ngrok or tunnel configuration
   - Verify TwiML response format

## Support

For issues or questions:
1. Check logs for error messages
2. Verify environment configuration
3. Test database and Redis connections
4. Review Twilio webhook logs
