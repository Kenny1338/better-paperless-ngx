"""Caching layer for Better Paperless."""

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from aiocache import Cache as AIOCache
from aiocache import caches


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache with TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass


class MemoryCache(CacheBackend):
    """In-memory cache implementation."""

    def __init__(self) -> None:
        """Initialize memory cache."""
        self._cache: Dict[str, tuple[Any, datetime]] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now() < expiry:
                return value
            else:
                del self._cache[key]
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in memory cache."""
        expiry = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = (value, expiry)

    async def delete(self, key: str) -> None:
        """Delete value from memory cache."""
        if key in self._cache:
            del self._cache[key]

    async def clear(self) -> None:
        """Clear all memory cache entries."""
        self._cache.clear()

    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        if key in self._cache:
            _, expiry = self._cache[key]
            if datetime.now() < expiry:
                return True
            else:
                del self._cache[key]
        return False


class RedisCache(CacheBackend):
    """Redis cache implementation."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
        """
        caches.set_config(
            {
                "default": {
                    "cache": "aiocache.RedisCache",
                    "endpoint": redis_url.split("://")[1].split("/")[0],
                    "port": 6379,
                    "timeout": 1,
                    "serializer": {"class": "aiocache.serializers.JsonSerializer"},
                }
            }
        )
        self._cache: AIOCache = caches.get("default")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        return await self._cache.get(key)

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in Redis cache."""
        await self._cache.set(key, value, ttl=ttl)

    async def delete(self, key: str) -> None:
        """Delete value from Redis cache."""
        await self._cache.delete(key)

    async def clear(self) -> None:
        """Clear all Redis cache entries."""
        await self._cache.clear()

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        return await self._cache.exists(key)


class CacheManager:
    """Manager for caching operations."""

    def __init__(self, backend: str = "memory", **kwargs: Any) -> None:
        """
        Initialize cache manager.

        Args:
            backend: Cache backend type ('memory' or 'redis')
            **kwargs: Backend-specific configuration
        """
        if backend == "redis":
            redis_url = kwargs.get("redis_url", "redis://localhost:6379/0")
            self._backend: CacheBackend = RedisCache(redis_url)
        else:
            self._backend = MemoryCache()

        self.enabled = kwargs.get("enabled", True)
        self.default_ttl = kwargs.get("ttl", 3600)

    def _generate_key(self, prefix: str, *args: Any, **kwargs: Any) -> str:
        """
        Generate cache key from arguments.

        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key
        """
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.enabled:
            return None
        return await self._backend.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: self.default_ttl)
        """
        if not self.enabled:
            return

        cache_ttl = ttl if ttl is not None else self.default_ttl
        await self._backend.set(key, value, cache_ttl)

    async def delete(self, key: str) -> None:
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        if not self.enabled:
            return
        await self._backend.delete(key)

    async def clear(self) -> None:
        """Clear all cache entries."""
        if not self.enabled:
            return
        await self._backend.clear()

    async def get_or_set(
        self, key: str, factory_func: Any, ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or compute and cache it.

        Args:
            key: Cache key
            factory_func: Async function to compute value if not cached
            ttl: Time to live in seconds

        Returns:
            Cached or computed value
        """
        value = await self.get(key)
        if value is not None:
            return value

        value = await factory_func()
        await self.set(key, value, ttl)
        return value

    def cache_key(self, prefix: str, *args: Any, **kwargs: Any) -> str:
        """
        Generate cache key.

        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Generated cache key
        """
        return self._generate_key(prefix, *args, **kwargs)