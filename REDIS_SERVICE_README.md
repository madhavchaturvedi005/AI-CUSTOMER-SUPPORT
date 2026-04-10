# Redis Service Documentation

## Overview

The Redis service provides caching and session management for the AI Voice Automation system. It implements connection pooling and supports four main caching categories:

1. **Session State Caching** - Stores active call session data (TTL: 1 hour)
2. **Caller History Caching** - Maintains call history per phone number (TTL: 180 days)
3. **Agent Availability Caching** - Tracks agent availability status (TTL: 5 minutes)
4. **Business Configuration Caching** - Caches business settings (TTL: 5 minutes)

## Installation

Add Redis to your requirements:

```bash
pip install redis==5.2.1
```

## Configuration

Set the following environment variables in your `.env` file:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

## Usage

### Initialize Redis Service

```python
from redis_service import initialize_redis, shutdown_redis

# Initialize on application startup
await initialize_redis()

# Shutdown on application teardown
await shutdown_redis()
```

### Session State Caching

```python
from redis_service import get_redis_service

redis = get_redis_service()

# Store session state
session_data = {
    "call_id": "uuid-123",
    "caller_phone": "+1234567890",
    "intent": "sales_inquiry",
    "conversation_history": [...]
}
await redis.set_session_state("CA1234567890", session_data)

# Retrieve session state
session = await redis.get_session_state("CA1234567890")

# Delete session state
await redis.delete_session_state("CA1234567890")
```

### Caller History Caching

```python
# Add call to caller history
await redis.add_caller_history("+1234567890", "call-uuid-123")

# Get caller history (most recent 10 calls)
call_ids = await redis.get_caller_history("+1234567890", limit=10)
```

### Agent Availability Caching

```python
# Set agent availability
await redis.set_agent_availability("agent_001", "available")

# Get specific agent availability
status = await redis.get_agent_availability("agent_001")

# Get all agents availability
all_agents = await redis.get_all_agents_availability()
# Returns: {"agent_001": "available", "agent_002": "busy", ...}
```

### Business Configuration Caching

```python
# Cache business configuration
config = {
    "business_hours": {"monday": "9-17"},
    "greeting_message": "Hello!",
    "routing_rules": {...}
}
await redis.set_business_config("business_001", config)

# Retrieve cached configuration
config = await redis.get_business_config("business_001")

# Invalidate cache (force reload from database)
await redis.invalidate_business_config("business_001")
```

## Key Design Features

### Connection Pooling
- Maximum 50 connections by default
- Automatic connection management
- Efficient resource utilization

### TTL Management
- Session state: 1 hour (3600 seconds)
- Caller history: 180 days
- Agent availability: 5 minutes (300 seconds)
- Business config: 5 minutes (300 seconds)

### Data Structures

#### Session State
```
Key: session:{call_sid}
Value: JSON serialized session data
TTL: 1 hour
```

#### Caller History
```
Key: caller:{phone_number}
Value: List of call IDs (most recent first)
TTL: 180 days
```

#### Agent Availability
```
Key: agents:availability
Value: Hash map {agent_id: status}
TTL: 5 minutes
```

#### Business Configuration
```
Key: config:{business_id}
Value: JSON serialized configuration
TTL: 5 minutes
```

## Testing

Run the test suite:

```bash
python3 -m pytest test_redis_service.py -v
```

All tests use mocked Redis clients and don't require a running Redis server.

## Requirements Mapping

This implementation satisfies the following requirements:

- **Requirement 9.1**: Conversation context retrieval for returning callers
- **Requirement 9.3**: Conversation history maintenance for 180 days
- **Requirement 11.5**: Business hours and configuration management
- **Requirement 18.2**: Performance optimization with caching

## Error Handling

The service includes proper error handling:

- Raises `RuntimeError` if client accessed before connection
- Validates connection on initialization with ping
- Provides graceful cleanup on shutdown

## Integration with FastAPI

```python
from fastapi import FastAPI
from redis_service import initialize_redis, shutdown_redis

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await initialize_redis()

@app.on_event("shutdown")
async def shutdown_event():
    await shutdown_redis()
```
