"""
Redis caching layer for external API responses.
"""
import json
import hashlib
from typing import Any
import redis
from .config import get_settings


class CacheService:
    """Redis-based caching for API responses."""
    
    def __init__(self):
        settings = get_settings()
        self._client: redis.Redis | None = None
        self._redis_url = settings.redis_url
        self._default_ttl = settings.cache_ttl_seconds
    
    @property
    def client(self) -> redis.Redis | None:
        """Lazy connect to Redis."""
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self._redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                # Test connection
                self._client.ping()
            except (redis.ConnectionError, redis.TimeoutError):
                self._client = None
        return self._client
    
    def _make_key(self, prefix: str, params: dict[str, Any]) -> str:
        """Generate a cache key from prefix and parameters."""
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:12]
        return f"agentic_buyer:{prefix}:{param_hash}"
    
    def get(self, prefix: str, params: dict[str, Any]) -> Any | None:
        """
        Retrieve cached value if available.
        
        Args:
            prefix: Cache key prefix (e.g., 'bestbuy_search')
            params: Parameters that uniquely identify the cached data
            
        Returns:
            Cached data or None if not found/expired
        """
        if self.client is None:
            return None
        
        key = self._make_key(prefix, params)
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
        except (redis.RedisError, json.JSONDecodeError):
            pass
        return None
    
    def set(
        self,
        prefix: str,
        params: dict[str, Any],
        value: Any,
        ttl_seconds: int | None = None
    ) -> bool:
        """
        Store value in cache.
        
        Args:
            prefix: Cache key prefix
            params: Parameters that uniquely identify the cached data
            value: Data to cache (must be JSON-serializable)
            ttl_seconds: Time-to-live in seconds (default: 600)
            
        Returns:
            True if cached successfully, False otherwise
        """
        if self.client is None:
            return False
        
        key = self._make_key(prefix, params)
        ttl = ttl_seconds or self._default_ttl
        
        try:
            self.client.setex(key, ttl, json.dumps(value))
            return True
        except (redis.RedisError, TypeError):
            return False
    
    def invalidate(self, prefix: str, params: dict[str, Any]) -> bool:
        """Delete a specific cache entry."""
        if self.client is None:
            return False
        
        key = self._make_key(prefix, params)
        try:
            self.client.delete(key)
            return True
        except redis.RedisError:
            return False
    
    def clear_prefix(self, prefix: str) -> int:
        """Clear all cache entries with given prefix."""
        if self.client is None:
            return 0
        
        pattern = f"agentic_buyer:{prefix}:*"
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
        except redis.RedisError:
            pass
        return 0


# Global cache instance
_cache_service: CacheService | None = None


def get_cache() -> CacheService:
    """Get or create the global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
