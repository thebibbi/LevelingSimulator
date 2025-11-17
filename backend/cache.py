"""
Caching layer using Redis for IK calculation results
"""

import hashlib
import json
from functools import wraps
from typing import Any, Optional

import redis

from config import settings

# Redis client
redis_client = None


def init_cache():
    """Initialize Redis connection"""
    global redis_client

    if not settings.redis_enabled:
        return

    try:
        redis_client = redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=5)
        # Test connection
        redis_client.ping()
        print(f"✓ Redis connected: {settings.redis_url}")
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        print("  Continuing without cache...")
        redis_client = None


def generate_cache_key(prefix: str, data: dict) -> str:
    """Generate a cache key from data"""
    # Sort keys for consistent hashing
    json_str = json.dumps(data, sort_keys=True)
    hash_str = hashlib.md5(json_str.encode()).hexdigest()
    return f"{prefix}:{hash_str}"


def get_cached(key: str) -> Optional[Any]:
    """Get value from cache"""
    if redis_client is None:
        return None

    try:
        cached = redis_client.get(key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        print(f"Cache get error: {e}")

    return None


def set_cached(key: str, value: Any, expiration: int = 300):
    """Set value in cache with expiration (seconds)"""
    if redis_client is None:
        return

    try:
        redis_client.setex(key, expiration, json.dumps(value))
    except Exception as e:
        print(f"Cache set error: {e}")


def invalidate_cache(pattern: str):
    """Invalidate all keys matching pattern"""
    if redis_client is None:
        return

    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except Exception as e:
        print(f"Cache invalidate error: {e}")


def cache_result(prefix: str = "calc", expiration: int = 300):
    """
    Decorator to cache function results

    Args:
        prefix: Cache key prefix
        expiration: Cache expiration in seconds
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key from arguments
            cache_key = generate_cache_key(prefix, kwargs)

            # Try to get from cache
            cached = get_cached(cache_key)
            if cached is not None:
                return cached

            # Calculate and cache
            result = await func(*args, **kwargs)
            set_cached(cache_key, result, expiration)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key from arguments
            cache_key = generate_cache_key(prefix, kwargs)

            # Try to get from cache
            cached = get_cached(cache_key)
            if cached is not None:
                return cached

            # Calculate and cache
            result = func(*args, **kwargs)
            set_cached(cache_key, result, expiration)
            return result

        # Return appropriate wrapper based on function type
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_cache_stats() -> dict:
    """Get cache statistics"""
    if redis_client is None:
        return {"enabled": False}

    try:
        info = redis_client.info("stats")
        return {
            "enabled": True,
            "total_connections": info.get("total_connections_received", 0),
            "total_commands": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": (
                info.get("keyspace_hits", 0)
                / max(
                    1,
                    info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0),
                )
                * 100
            ),
        }
    except Exception as e:
        return {"enabled": True, "error": str(e)}
