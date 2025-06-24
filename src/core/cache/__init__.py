"""
Módulo de cache para a API.
"""

from .redis_cache import (
    RedisCache,
    CacheError,
    get_cache,
    get_cache_instance,
    cached
)

__all__ = [
    "RedisCache",
    "CacheError", 
    "get_cache",
    "get_cache_instance",
    "cached"
]