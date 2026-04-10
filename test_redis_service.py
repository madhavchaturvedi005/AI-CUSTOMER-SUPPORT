"""Unit tests for Redis service."""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta
from redis_service import RedisService, initialize_redis, shutdown_redis, get_redis_service


@pytest.fixture
def redis_service():
    """Create a Redis service instance with mocked client."""
    service = RedisService(host="localhost", port=6379)
    
    # Mock the Redis client
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock()
    mock_client.setex = AsyncMock()
    mock_client.get = AsyncMock()
    mock_client.delete = AsyncMock(return_value=1)
    mock_client.lpush = AsyncMock()
    mock_client.lrange = AsyncMock()
    mock_client.expire = AsyncMock()
    mock_client.hset = AsyncMock()
    mock_client.hget = AsyncMock()
    mock_client.hgetall = AsyncMock()
    mock_client.aclose = AsyncMock()
    
    service._client = mock_client
    
    return service


class TestRedisServiceConnection:
    """Test Redis connection management."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful Redis connection."""
        service = RedisService()
        
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_instance = AsyncMock()
            mock_instance.ping = AsyncMock()
            mock_redis.return_value = mock_instance
            
            await service.connect()
            
            assert service._client is not None
            mock_instance.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test Redis disconnection."""
        redis_service = RedisService()
        mock_client = AsyncMock()
        mock_client.aclose = AsyncMock()
        redis_service._client = mock_client
        
        mock_pool = AsyncMock()
        redis_service.pool = mock_pool
        
        await redis_service.disconnect()
        
        mock_client.aclose.assert_called_once()
        mock_pool.aclose.assert_called_once()
    
    def test_client_property_not_connected(self):
        """Test accessing client property before connection raises error."""
        service = RedisService()
        
        with pytest.raises(RuntimeError, match="Redis client not connected"):
            _ = service.client


class TestSessionStateCaching:
    """Test session state caching operations."""
    
    @pytest.mark.asyncio
    async def test_set_session_state(self, redis_service):
        """Test setting session state."""
        call_sid = "CA1234567890"
        session_data = {
            "call_id": "uuid-123",
            "caller_phone": "+1234567890",
            "intent": "sales_inquiry"
        }
        
        result = await redis_service.set_session_state(call_sid, session_data)
        
        assert result is True
        redis_service.client.setex.assert_called_once()
        
        # Verify the key format
        call_args = redis_service.client.setex.call_args
        assert call_args[0][0] == f"session:{call_sid}"
        assert call_args[0][1] == 3600  # Default TTL
        assert json.loads(call_args[0][2]) == session_data
    
    @pytest.mark.asyncio
    async def test_set_session_state_custom_ttl(self, redis_service):
        """Test setting session state with custom TTL."""
        call_sid = "CA1234567890"
        session_data = {"test": "data"}
        custom_ttl = 7200
        
        await redis_service.set_session_state(call_sid, session_data, ttl_seconds=custom_ttl)
        
        call_args = redis_service.client.setex.call_args
        assert call_args[0][1] == custom_ttl
    
    @pytest.mark.asyncio
    async def test_get_session_state_exists(self, redis_service):
        """Test retrieving existing session state."""
        call_sid = "CA1234567890"
        session_data = {"call_id": "uuid-123", "intent": "support_request"}
        
        redis_service.client.get.return_value = json.dumps(session_data)
        
        result = await redis_service.get_session_state(call_sid)
        
        assert result == session_data
        redis_service.client.get.assert_called_once_with(f"session:{call_sid}")
    
    @pytest.mark.asyncio
    async def test_get_session_state_not_exists(self, redis_service):
        """Test retrieving non-existent session state."""
        call_sid = "CA1234567890"
        redis_service.client.get.return_value = None
        
        result = await redis_service.get_session_state(call_sid)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_session_state_exists(self, redis_service):
        """Test deleting existing session state."""
        call_sid = "CA1234567890"
        redis_service.client.delete.return_value = 1
        
        result = await redis_service.delete_session_state(call_sid)
        
        assert result is True
        redis_service.client.delete.assert_called_once_with(f"session:{call_sid}")
    
    @pytest.mark.asyncio
    async def test_delete_session_state_not_exists(self, redis_service):
        """Test deleting non-existent session state."""
        call_sid = "CA1234567890"
        redis_service.client.delete.return_value = 0
        
        result = await redis_service.delete_session_state(call_sid)
        
        assert result is False


class TestCallerHistoryCaching:
    """Test caller history caching operations."""
    
    @pytest.mark.asyncio
    async def test_add_caller_history(self, redis_service):
        """Test adding call to caller history."""
        phone_number = "+1234567890"
        call_id = "uuid-123"
        
        result = await redis_service.add_caller_history(phone_number, call_id)
        
        assert result is True
        redis_service.client.lpush.assert_called_once_with(f"caller:{phone_number}", call_id)
        redis_service.client.expire.assert_called_once()
        
        # Verify TTL is set to 180 days
        expire_call_args = redis_service.client.expire.call_args
        assert expire_call_args[0][0] == f"caller:{phone_number}"
        assert expire_call_args[0][1] == timedelta(days=180)
    
    @pytest.mark.asyncio
    async def test_add_caller_history_custom_ttl(self, redis_service):
        """Test adding call to caller history with custom TTL."""
        phone_number = "+1234567890"
        call_id = "uuid-123"
        custom_ttl = 90
        
        await redis_service.add_caller_history(phone_number, call_id, ttl_days=custom_ttl)
        
        expire_call_args = redis_service.client.expire.call_args
        assert expire_call_args[0][1] == timedelta(days=custom_ttl)
    
    @pytest.mark.asyncio
    async def test_get_caller_history_exists(self, redis_service):
        """Test retrieving caller history."""
        phone_number = "+1234567890"
        call_ids = ["uuid-3", "uuid-2", "uuid-1"]
        
        redis_service.client.lrange.return_value = call_ids
        
        result = await redis_service.get_caller_history(phone_number)
        
        assert result == call_ids
        redis_service.client.lrange.assert_called_once_with(f"caller:{phone_number}", 0, 9)
    
    @pytest.mark.asyncio
    async def test_get_caller_history_with_limit(self, redis_service):
        """Test retrieving caller history with custom limit."""
        phone_number = "+1234567890"
        limit = 5
        call_ids = ["uuid-5", "uuid-4", "uuid-3", "uuid-2", "uuid-1"]
        
        redis_service.client.lrange.return_value = call_ids
        
        result = await redis_service.get_caller_history(phone_number, limit=limit)
        
        assert result == call_ids
        redis_service.client.lrange.assert_called_once_with(f"caller:{phone_number}", 0, 4)
    
    @pytest.mark.asyncio
    async def test_get_caller_history_empty(self, redis_service):
        """Test retrieving empty caller history."""
        phone_number = "+1234567890"
        redis_service.client.lrange.return_value = []
        
        result = await redis_service.get_caller_history(phone_number)
        
        assert result == []


class TestAgentAvailabilityCaching:
    """Test agent availability caching operations."""
    
    @pytest.mark.asyncio
    async def test_set_agent_availability(self, redis_service):
        """Test setting agent availability."""
        agent_id = "agent_001"
        status = "available"
        
        result = await redis_service.set_agent_availability(agent_id, status)
        
        assert result is True
        redis_service.client.hset.assert_called_once_with("agents:availability", agent_id, status)
        redis_service.client.expire.assert_called_once_with("agents:availability", 300)
    
    @pytest.mark.asyncio
    async def test_set_agent_availability_custom_ttl(self, redis_service):
        """Test setting agent availability with custom TTL."""
        agent_id = "agent_001"
        status = "busy"
        custom_ttl = 600
        
        await redis_service.set_agent_availability(agent_id, status, ttl_seconds=custom_ttl)
        
        redis_service.client.expire.assert_called_once_with("agents:availability", custom_ttl)
    
    @pytest.mark.asyncio
    async def test_get_agent_availability_exists(self, redis_service):
        """Test getting agent availability."""
        agent_id = "agent_001"
        status = "available"
        
        redis_service.client.hget.return_value = status
        
        result = await redis_service.get_agent_availability(agent_id)
        
        assert result == status
        redis_service.client.hget.assert_called_once_with("agents:availability", agent_id)
    
    @pytest.mark.asyncio
    async def test_get_agent_availability_not_exists(self, redis_service):
        """Test getting non-existent agent availability."""
        agent_id = "agent_999"
        redis_service.client.hget.return_value = None
        
        result = await redis_service.get_agent_availability(agent_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_all_agents_availability(self, redis_service):
        """Test getting all agents availability."""
        agents_data = {
            "agent_001": "available",
            "agent_002": "busy",
            "agent_003": "offline"
        }
        
        redis_service.client.hgetall.return_value = agents_data
        
        result = await redis_service.get_all_agents_availability()
        
        assert result == agents_data
        redis_service.client.hgetall.assert_called_once_with("agents:availability")
    
    @pytest.mark.asyncio
    async def test_get_all_agents_availability_empty(self, redis_service):
        """Test getting all agents availability when empty."""
        redis_service.client.hgetall.return_value = {}
        
        result = await redis_service.get_all_agents_availability()
        
        assert result == {}


class TestBusinessConfigCaching:
    """Test business configuration caching operations."""
    
    @pytest.mark.asyncio
    async def test_set_business_config(self, redis_service):
        """Test setting business configuration."""
        business_id = "business_001"
        config_data = {
            "business_hours": {"monday": "9-17"},
            "greeting_message": "Hello!"
        }
        
        result = await redis_service.set_business_config(business_id, config_data)
        
        assert result is True
        redis_service.client.setex.assert_called_once()
        
        call_args = redis_service.client.setex.call_args
        assert call_args[0][0] == f"config:{business_id}"
        assert call_args[0][1] == 300  # Default TTL
        assert json.loads(call_args[0][2]) == config_data
    
    @pytest.mark.asyncio
    async def test_set_business_config_custom_ttl(self, redis_service):
        """Test setting business configuration with custom TTL."""
        business_id = "business_001"
        config_data = {"test": "config"}
        custom_ttl = 600
        
        await redis_service.set_business_config(business_id, config_data, ttl_seconds=custom_ttl)
        
        call_args = redis_service.client.setex.call_args
        assert call_args[0][1] == custom_ttl
    
    @pytest.mark.asyncio
    async def test_get_business_config_exists(self, redis_service):
        """Test retrieving business configuration."""
        business_id = "business_001"
        config_data = {"business_hours": {"monday": "9-17"}}
        
        redis_service.client.get.return_value = json.dumps(config_data)
        
        result = await redis_service.get_business_config(business_id)
        
        assert result == config_data
        redis_service.client.get.assert_called_once_with(f"config:{business_id}")
    
    @pytest.mark.asyncio
    async def test_get_business_config_not_exists(self, redis_service):
        """Test retrieving non-existent business configuration."""
        business_id = "business_999"
        redis_service.client.get.return_value = None
        
        result = await redis_service.get_business_config(business_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_invalidate_business_config_exists(self, redis_service):
        """Test invalidating business configuration."""
        business_id = "business_001"
        redis_service.client.delete.return_value = 1
        
        result = await redis_service.invalidate_business_config(business_id)
        
        assert result is True
        redis_service.client.delete.assert_called_once_with(f"config:{business_id}")
    
    @pytest.mark.asyncio
    async def test_invalidate_business_config_not_exists(self, redis_service):
        """Test invalidating non-existent business configuration."""
        business_id = "business_999"
        redis_service.client.delete.return_value = 0
        
        result = await redis_service.invalidate_business_config(business_id)
        
        assert result is False


class TestGlobalRedisService:
    """Test global Redis service management."""
    
    @pytest.mark.asyncio
    async def test_initialize_redis_default_config(self):
        """Test initializing Redis with default configuration."""
        with patch('redis_service.RedisService') as mock_service_class:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock()
            mock_service_class.return_value = mock_instance
            
            with patch.dict('os.environ', {}, clear=True):
                service = await initialize_redis()
                
                assert service is not None
                mock_service_class.assert_called_once_with(
                    host="localhost",
                    port=6379,
                    db=0,
                    password=None
                )
                mock_instance.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_redis_env_vars(self):
        """Test initializing Redis with environment variables."""
        with patch('redis_service.RedisService') as mock_service_class:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock()
            mock_service_class.return_value = mock_instance
            
            env_vars = {
                'REDIS_HOST': 'redis.example.com',
                'REDIS_PORT': '6380',
                'REDIS_PASSWORD': 'secret',
                'REDIS_DB': '1'
            }
            
            with patch.dict('os.environ', env_vars):
                service = await initialize_redis()
                
                mock_service_class.assert_called_once_with(
                    host="redis.example.com",
                    port=6380,
                    db=1,
                    password="secret"
                )
    
    @pytest.mark.asyncio
    async def test_initialize_redis_explicit_params(self):
        """Test initializing Redis with explicit parameters."""
        with patch('redis_service.RedisService') as mock_service_class:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock()
            mock_service_class.return_value = mock_instance
            
            service = await initialize_redis(
                host="custom.redis.com",
                port=6381,
                password="custom_pass",
                db=2
            )
            
            mock_service_class.assert_called_once_with(
                host="custom.redis.com",
                port=6381,
                db=2,
                password="custom_pass"
            )
    
    def test_get_redis_service_not_initialized(self):
        """Test getting Redis service before initialization raises error."""
        # Reset global state
        import redis_service
        redis_service._redis_service = None
        
        with pytest.raises(RuntimeError, match="Redis service not initialized"):
            get_redis_service()
    
    @pytest.mark.asyncio
    async def test_shutdown_redis(self):
        """Test shutting down Redis service."""
        mock_service = AsyncMock()
        mock_service.disconnect = AsyncMock()
        
        import redis_service
        redis_service._redis_service = mock_service
        
        await shutdown_redis()
        
        mock_service.disconnect.assert_called_once()
        assert redis_service._redis_service is None



class TestAgentSkillsManagement:
    """Test agent skills management in Redis."""
    
    @pytest.mark.asyncio
    async def test_set_agent_skills(self):
        """Test setting agent skills in Redis."""
        redis_service = RedisService()
        await redis_service.connect()
        
        try:
            skills = ["sales", "support", "technical"]
            result = await redis_service.set_agent_skills("agent_001", skills)
            
            assert result is True
            
            # Verify skills were stored
            stored_skills = await redis_service.get_agent_skills("agent_001")
            assert stored_skills == skills
            
        finally:
            # Cleanup
            await redis_service.client.delete("agent:agent_001:skills")
            await redis_service.disconnect()
    
    @pytest.mark.asyncio
    async def test_get_agent_skills(self):
        """Test retrieving agent skills from Redis."""
        redis_service = RedisService()
        await redis_service.connect()
        
        try:
            # Set skills first
            skills = ["sales", "support"]
            await redis_service.set_agent_skills("agent_002", skills)
            
            # Retrieve skills
            retrieved_skills = await redis_service.get_agent_skills("agent_002")
            
            assert retrieved_skills == skills
            
        finally:
            # Cleanup
            await redis_service.client.delete("agent:agent_002:skills")
            await redis_service.disconnect()
    
    @pytest.mark.asyncio
    async def test_get_agent_skills_not_found(self):
        """Test retrieving agent skills when not found."""
        redis_service = RedisService()
        await redis_service.connect()
        
        try:
            skills = await redis_service.get_agent_skills("nonexistent_agent")
            
            assert skills == []
            
        finally:
            await redis_service.disconnect()
    
    @pytest.mark.asyncio
    async def test_set_agent_skills_with_ttl(self):
        """Test setting agent skills with custom TTL."""
        redis_service = RedisService()
        await redis_service.connect()
        
        try:
            skills = ["sales"]
            # Set with 2 second TTL
            await redis_service.set_agent_skills("agent_003", skills, ttl_seconds=2)
            
            # Should exist immediately
            stored_skills = await redis_service.get_agent_skills("agent_003")
            assert stored_skills == skills
            
            # Wait for TTL to expire
            await asyncio.sleep(3)
            
            # Should be gone
            expired_skills = await redis_service.get_agent_skills("agent_003")
            assert expired_skills == []
            
        finally:
            await redis_service.disconnect()
    
    @pytest.mark.asyncio
    async def test_update_agent_skills(self):
        """Test updating agent skills."""
        redis_service = RedisService()
        await redis_service.connect()
        
        try:
            # Set initial skills
            initial_skills = ["sales"]
            await redis_service.set_agent_skills("agent_004", initial_skills)
            
            # Update skills
            updated_skills = ["sales", "support", "technical"]
            await redis_service.set_agent_skills("agent_004", updated_skills)
            
            # Verify updated skills
            stored_skills = await redis_service.get_agent_skills("agent_004")
            assert stored_skills == updated_skills
            
        finally:
            # Cleanup
            await redis_service.client.delete("agent:agent_004:skills")
            await redis_service.disconnect()
