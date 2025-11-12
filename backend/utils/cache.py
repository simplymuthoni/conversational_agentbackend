"""
Redis Cache Utilities Module

Provides caching functionality using Redis for:
- Response caching to reduce redundant API calls
- Rate limiting for API protection
- Session management
- Pub/sub for real-time updates

This module uses redis-py with async support (aioredis).
"""

import json
import logging
import hashlib
from typing import Optional, Any, Dict, List
from datetime import timedelta
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

from ..config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis cache manager with connection pooling.
    
    Provides high-level caching operations with automatic
    serialization/deserialization and error handling.
    """
    
    def __init__(self, redis_url: str = None):
        """
        Initialize cache manager.
        
        Args:
            redis_url: Redis connection URL (defaults to settings.REDIS_URL)
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis: Optional[Redis] = None
        self._initialized = False
    
    async def initialize(self):
        """
        Initialize Redis connection pool.
        
        Creates connection pool with automatic reconnection.
        """
        if self._initialized:
            logger.warning("Cache already initialized")
            return
        
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis.ping()
            
            self._initialized = True
            logger.info("Redis cache initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {str(e)}")
            raise
    
    async def close(self):
        """Close Redis connections."""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connections closed")
    
    async def health_check(self) -> bool:
        """
        Check Redis connectivity.
        
        Returns:
            True if Redis is accessible, False otherwise
        """
        try:
            if not self.redis:
                return False
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False
    
    # ==================== Basic Cache Operations ====================
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value (deserialized) or None if not found
            
        Example:
            >>> value = await cache_manager.get("user:123")
            >>> print(value)
            {'name': 'John', 'email': 'john@example.com'}
        """
        if not self.redis:
            logger.warning("Redis not initialized")
            return None
        
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Return as string if not JSON
                return value
        
        except RedisError as e:
            logger.error(f"Redis GET error for key '{key}': {str(e)}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (None = no expiration)
            
        Returns:
            True if successful, False otherwise
            
        Example:
            >>> await cache_manager.set("user:123", {"name": "John"}, ttl=3600)
            True
        """
        if not self.redis:
            logger.warning("Redis not initialized")
            return False
        
        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            else:
                serialized = str(value)
            
            # Set with optional TTL
            if ttl:
                await self.redis.setex(key, ttl, serialized)
            else:
                await self.redis.set(key, serialized)
            
            return True
        
        except RedisError as e:
            logger.error(f"Redis SET error for key '{key}': {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.redis:
            return False
        
        try:
            result = await self.redis.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis DELETE error for key '{key}': {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if exists, False otherwise
        """
        if not self.redis:
            return False
        
        try:
            result = await self.redis.exists(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis EXISTS error for key '{key}': {str(e)}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Cache key
            seconds: Expiration time in seconds
            
        Returns:
            True if expiration set, False otherwise
        """
        if not self.redis:
            return False
        
        try:
            result = await self.redis.expire(key, seconds)
            return result
        except RedisError as e:
            logger.error(f"Redis EXPIRE error for key '{key}': {str(e)}")
            return False
    
    # ==================== Pattern Operations ====================
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
            
        Example:
            >>> deleted = await cache_manager.delete_pattern("cache:query:*")
            >>> print(f"Deleted {deleted} cached queries")
        """
        if not self.redis:
            return 0
        
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern, count=100):
                keys.append(key)
            
            if keys:
                return await self.redis.delete(*keys)
            return 0
        
        except RedisError as e:
            logger.error(f"Redis DELETE_PATTERN error for pattern '{pattern}': {str(e)}")
            return 0
    
    async def get_keys(self, pattern: str) -> List[str]:
        """
        Get all keys matching a pattern.
        
        Args:
            pattern: Redis key pattern
            
        Returns:
            List of matching keys
        """
        if not self.redis:
            return []
        
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern, count=100):
                keys.append(key)
            return keys
        
        except RedisError as e:
            logger.error(f"Redis GET_KEYS error for pattern '{pattern}': {str(e)}")
            return []
    
    # ==================== Hash Operations ====================
    
    async def hset(self, name: str, key: str, value: Any) -> bool:
        """
        Set hash field value.
        
        Args:
            name: Hash name
            key: Field key
            value: Field value
            
        Returns:
            True if successful
        """
        if not self.redis:
            return False
        
        try:
            serialized = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            await self.redis.hset(name, key, serialized)
            return True
        except RedisError as e:
            logger.error(f"Redis HSET error: {str(e)}")
            return False
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """
        Get hash field value.
        
        Args:
            name: Hash name
            key: Field key
            
        Returns:
            Field value or None
        """
        if not self.redis:
            return None
        
        try:
            value = await self.redis.hget(name, key)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        
        except RedisError as e:
            logger.error(f"Redis HGET error: {str(e)}")
            return None
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """
        Get all hash fields and values.
        
        Args:
            name: Hash name
            
        Returns:
            Dictionary of all fields
        """
        if not self.redis:
            return {}
        
        try:
            data = await self.redis.hgetall(name)
            result = {}
            for key, value in data.items():
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = value
            return result
        
        except RedisError as e:
            logger.error(f"Redis HGETALL error: {str(e)}")
            return {}
    
    # ==================== Counter Operations ====================
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment counter.
        
        Args:
            key: Counter key
            amount: Amount to increment (default: 1)
            
        Returns:
            New counter value
        """
        if not self.redis:
            return 0
        
        try:
            return await self.redis.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis INCR error: {str(e)}")
            return 0
    
    async def decr(self, key: str, amount: int = 1) -> int:
        """
        Decrement counter.
        
        Args:
            key: Counter key
            amount: Amount to decrement (default: 1)
            
        Returns:
            New counter value
        """
        if not self.redis:
            return 0
        
        try:
            return await self.redis.decrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis DECR error: {str(e)}")
            return 0


# Global cache manager instance
cache_manager = CacheManager()


# ==================== Rate Limiting ====================

class RateLimiter:
    """
    Token bucket rate limiter using Redis.
    
    Implements sliding window rate limiting for API protection.
    """
    
    def __init__(self, cache: CacheManager):
        """
        Initialize rate limiter.
        
        Args:
            cache: CacheManager instance
        """
        self.cache = cache
    
    async def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
        namespace: str = "rate_limit"
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: Unique identifier (user ID, IP, etc.)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            namespace: Redis key namespace
            
        Returns:
            Tuple of (allowed: bool, remaining: int, reset_time: int)
            
        Example:
            >>> allowed, remaining, reset = await rate_limiter.check_rate_limit(
            ...     "user:123", max_requests=100, window_seconds=3600
            ... )
            >>> if not allowed:
            ...     raise HTTPException(429, f"Rate limit exceeded. Reset in {reset}s")
        """
        if not self.cache.redis:
            # If Redis unavailable, allow request (fail open)
            return True, max_requests, 0
        
        key = f"{namespace}:{identifier}"
        
        try:
            # Get current count
            current = await self.cache.redis.get(key)
            current_count = int(current) if current else 0
            
            if current_count >= max_requests:
                # Rate limit exceeded
                ttl = await self.cache.redis.ttl(key)
                return False, 0, ttl if ttl > 0 else window_seconds
            
            # Increment counter
            if current_count == 0:
                # First request in window
                await self.cache.redis.setex(key, window_seconds, 1)
                remaining = max_requests - 1
            else:
                # Subsequent request
                new_count = await self.cache.redis.incr(key)
                remaining = max_requests - new_count
            
            ttl = await self.cache.redis.ttl(key)
            return True, remaining, ttl if ttl > 0 else window_seconds
        
        except RedisError as e:
            logger.error(f"Rate limit check error: {str(e)}")
            # Fail open on error
            return True, max_requests, 0


# Global rate limiter instance
rate_limiter = RateLimiter(cache_manager)


# ==================== Cache Decorators ====================

def cache_result(ttl: int = 3600, key_prefix: str = "cache"):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Cache TTL in seconds (default: 1 hour)
        key_prefix: Redis key prefix
        
    Example:
        >>> @cache_result(ttl=1800, key_prefix="search")
        ... async def search_web(query: str):
        ...     # Expensive operation
        ...     return results
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            
            cache_key = ":".join(key_parts)
            cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
            redis_key = f"{key_prefix}:{func.__name__}:{cache_key_hash}"
            
            # Try to get from cache
            if settings.enable_caching:
                cached = await cache_manager.get(redis_key)
                if cached is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            if settings.enable_caching and result is not None:
                await cache_manager.set(redis_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


# ==================== Initialization Functions ====================

async def init_cache():
    """
    Initialize cache on application startup.
    
    Call this function during FastAPI startup event.
    """
    await cache_manager.initialize()
    logger.info("Cache initialization complete")


async def close_cache():
    """
    Close cache connections on application shutdown.
    
    Call this function during FastAPI shutdown event.
    """
    await cache_manager.close()
    logger.info("Cache connections closed")
