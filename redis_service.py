"""Redis service for caching and session management."""

import json
import os
from typing import Optional, Dict, Any, List
from datetime import timedelta
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool


class RedisService:
    """Manages Redis connections and caching operations for the voice automation system."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 50,
        decode_responses: bool = True
    ):
        """
        Initialize Redis service with connection pooling.
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            password: Redis password (if required)
            max_connections: Maximum number of connections in pool
            decode_responses: Whether to decode responses to strings
        """
        self.pool = ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            decode_responses=decode_responses
        )
        self._client: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Establish Redis connection."""
        self._client = redis.Redis(connection_pool=self.pool)
        # Test connection
        await self._client.ping()
    
    async def disconnect(self) -> None:
        """Close Redis connection and cleanup pool."""
        if self._client:
            await self._client.aclose()
            await self.pool.aclose()
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance."""
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client
    
    # Session State Caching (TTL: 1 hour)
    
    async def set_session_state(
        self,
        call_sid: str,
        session_data: Dict[str, Any],
        ttl_seconds: int = 3600
    ) -> bool:
        """
        Cache session state for a call.
        
        Args:
            call_sid: Twilio call SID
            session_data: Session state data to cache
            ttl_seconds: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful
        """
        key = f"session:{call_sid}"
        value = json.dumps(session_data)
        await self.client.setex(key, ttl_seconds, value)
        return True
    
    async def get_session_state(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session state for a call.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            Session state data or None if not found
        """
        key = f"session:{call_sid}"
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def delete_session_state(self, call_sid: str) -> bool:
        """
        Delete session state for a call.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            True if deleted, False if not found
        """
        key = f"session:{call_sid}"
        result = await self.client.delete(key)
        return result > 0
    
    # Caller History Caching (TTL: 180 days)
    
    async def add_caller_history(
        self,
        phone_number: str,
        call_id: str,
        ttl_days: int = 180
    ) -> bool:
        """
        Add a call to caller's history.
        
        Args:
            phone_number: Caller's phone number
            call_id: Call UUID
            ttl_days: Time to live in days (default: 180 days)
            
        Returns:
            True if successful
        """
        key = f"caller:{phone_number}"
        # Add call_id to the list
        await self.client.lpush(key, call_id)
        # Set expiration
        await self.client.expire(key, timedelta(days=ttl_days))
        return True
    
    async def get_caller_history(
        self,
        phone_number: str,
        limit: int = 10
    ) -> List[str]:
        """
        Retrieve caller's call history.
        
        Args:
            phone_number: Caller's phone number
            limit: Maximum number of call IDs to return
            
        Returns:
            List of call IDs (most recent first)
        """
        key = f"caller:{phone_number}"
        call_ids = await self.client.lrange(key, 0, limit - 1)
        return call_ids if call_ids else []
    
    # Agent Availability Caching (TTL: 5 minutes)
    
    async def set_agent_availability(
        self,
        agent_id: str,
        status: str,
        ttl_seconds: int = 300
    ) -> bool:
        """
        Set agent availability status.
        
        Args:
            agent_id: Agent identifier
            status: Availability status (available, busy, offline)
            ttl_seconds: Time to live in seconds (default: 5 minutes)
            
        Returns:
            True if successful
        """
        key = "agents:availability"
        await self.client.hset(key, agent_id, status)
        await self.client.expire(key, ttl_seconds)
        return True
    
    async def get_agent_availability(self, agent_id: str) -> Optional[str]:
        """
        Get agent availability status.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Availability status or None if not found
        """
        key = "agents:availability"
        status = await self.client.hget(key, agent_id)
        return status
    
    async def get_all_agents_availability(self) -> Dict[str, str]:
        """
        Get availability status for all agents.
        
        Returns:
            Dictionary mapping agent_id to status
        """
        key = "agents:availability"
        agents = await self.client.hgetall(key)
        return agents if agents else {}
    
    async def set_agent_skills(
        self,
        agent_id: str,
        skills: List[str],
        ttl_seconds: int = 86400
    ) -> bool:
        """
        Set agent skills in Redis.
        
        Args:
            agent_id: Agent identifier
            skills: List of skill tags
            ttl_seconds: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if successful
        """
        key = f"agent:{agent_id}:skills"
        value = json.dumps(skills)
        await self.client.setex(key, ttl_seconds, value)
        return True
    
    async def get_agent_skills(self, agent_id: str) -> List[str]:
        """
        Get agent skills from Redis.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of skill tags
        """
        key = f"agent:{agent_id}:skills"
        skills_json = await self.client.get(key)
        
        if skills_json:
            return json.loads(skills_json)
        
        return []
    
    # Configuration Caching (TTL: 5 minutes)
    
    async def set_business_config(
        self,
        business_id: str,
        config_data: Dict[str, Any],
        ttl_seconds: int = 300
    ) -> bool:
        """
        Cache business configuration.
        
        Args:
            business_id: Business identifier
            config_data: Configuration data
            ttl_seconds: Time to live in seconds (default: 5 minutes)
            
        Returns:
            True if successful
        """
        key = f"config:{business_id}"
        value = json.dumps(config_data)
        await self.client.setex(key, ttl_seconds, value)
        return True
    
    async def get_business_config(self, business_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve business configuration from cache.
        
        Args:
            business_id: Business identifier
            
        Returns:
            Configuration data or None if not found
        """
        key = f"config:{business_id}"
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def invalidate_business_config(self, business_id: str) -> bool:
        """
        Invalidate cached business configuration.
        
        Args:
            business_id: Business identifier
            
        Returns:
            True if deleted, False if not found
        """
        key = f"config:{business_id}"
        result = await self.client.delete(key)
        return result > 0


# Global Redis service instance
_redis_service: Optional[RedisService] = None


def get_redis_service() -> RedisService:
    """
    Get the global Redis service instance.
    
    Returns:
        RedisService instance
        
    Raises:
        RuntimeError: If Redis service not initialized
    """
    global _redis_service
    if not _redis_service:
        raise RuntimeError("Redis service not initialized. Call initialize_redis() first.")
    return _redis_service


async def initialize_redis(
    host: Optional[str] = None,
    port: Optional[int] = None,
    password: Optional[str] = None,
    db: int = 0
) -> RedisService:
    """
    Initialize the global Redis service instance.
    
    Args:
        host: Redis host (defaults to REDIS_HOST env var or localhost)
        port: Redis port (defaults to REDIS_PORT env var or 6379)
        password: Redis password (defaults to REDIS_PASSWORD env var)
        db: Redis database number (defaults to REDIS_DB env var or 0)
        
    Returns:
        Initialized RedisService instance
    """
    global _redis_service
    
    # Get configuration from environment variables if not provided
    host = host or os.getenv("REDIS_HOST", "localhost")
    port = port or int(os.getenv("REDIS_PORT", "6379"))
    password = password or os.getenv("REDIS_PASSWORD")
    db = int(os.getenv("REDIS_DB", str(db)))
    
    _redis_service = RedisService(
        host=host,
        port=port,
        db=db,
        password=password
    )
    
    await _redis_service.connect()
    return _redis_service


async def shutdown_redis() -> None:
    """Shutdown the global Redis service instance."""
    global _redis_service
    if _redis_service:
        await _redis_service.disconnect()
        _redis_service = None
