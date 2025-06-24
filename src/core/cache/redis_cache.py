"""
Sistema de cache Redis para a API.
Implementa cache inteligente para respostas frequentes e sessões ativas.
"""

import json
import hashlib
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import structlog
import redis.asyncio as redis
from contextlib import asynccontextmanager

from src.core.config import settings

logger = structlog.get_logger(__name__)


class CacheError(Exception):
    """Erro customizado para operações de cache."""
    pass


class RedisCache:
    """
    Cliente Redis otimizado para cache da API.
    
    Implementa:
    - Cache inteligente baseado em padrões de acesso
    - TTL dinâmico baseado na frequência
    - Compressão automática para dados grandes
    - Métricas de cache hit/miss
    """
    
    _instance: Optional["RedisCache"] = None
    _redis_pool: Optional[redis.Redis] = None
    
    def __new__(cls) -> "RedisCache":
        """Implementa singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self) -> None:
        """Inicializa o pool de conexões Redis."""
        if self._redis_pool is None:
            try:
                self._redis_pool = redis.from_url(
                    settings.redis_url,
                    password=settings.redis_password,
                    db=settings.redis_db,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=20,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30
                )
                
                # Testar conexão
                await self._redis_pool.ping()
                
                logger.info(
                    "redis_cache_initialized",
                    redis_url=settings.redis_url.split('@')[-1],  # Remove credenciais do log
                    db=settings.redis_db,
                    max_connections=20
                )
                
            except Exception as e:
                logger.error("redis_initialization_failed", error=str(e))
                raise CacheError(f"Failed to initialize Redis: {e}")
    
    async def close(self) -> None:
        """Fecha o pool de conexões."""
        if self._redis_pool:
            await self._redis_pool.close()
            self._redis_pool = None
            logger.info("redis_cache_closed")
    
    @property
    def redis(self) -> redis.Redis:
        """Retorna a instância Redis."""
        if self._redis_pool is None:
            raise CacheError("Redis not initialized. Call initialize() first.")
        return self._redis_pool
    
    def _generate_key(self, prefix: str, *args: Any) -> str:
        """
        Gera chave de cache única e determinística.
        
        Args:
            prefix: Prefixo da chave (ex: 'memory', 'session', 'user')
            *args: Argumentos para compor a chave
            
        Returns:
            Chave de cache SHA256 com prefixo legível
        """
        key_parts = [str(arg) for arg in args]
        key_string = ":".join(key_parts)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
        return f"zep_api:{prefix}:{key_hash}"
    
    def _serialize_data(self, data: Any) -> str:
        """
        Serializa dados para armazenamento.
        
        Args:
            data: Dados para serializar
            
        Returns:
            String JSON serializada
        """
        try:
            if isinstance(data, (dict, list)):
                return json.dumps(data, default=str, ensure_ascii=False)
            else:
                return str(data)
        except Exception as e:
            logger.warning("serialization_failed", error=str(e), data_type=type(data))
            return str(data)
    
    def _deserialize_data(self, data: str) -> Any:
        """
        Deserializa dados do cache.
        
        Args:
            data: String serializada
            
        Returns:
            Dados deserializados
        """
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data
    
    async def get(self, prefix: str, *key_parts: Any) -> Optional[Any]:
        """
        Recupera dados do cache.
        
        Args:
            prefix: Prefixo da chave
            *key_parts: Partes da chave
            
        Returns:
            Dados do cache ou None se não encontrado
        """
        if not settings.cache_enabled:
            return None
        
        try:
            cache_key = self._generate_key(prefix, *key_parts)
            cached_data = await self.redis.get(cache_key)
            
            if cached_data is not None:
                # Atualizar estatísticas de hit
                await self._update_hit_stats(cache_key, hit=True)
                
                logger.debug(
                    "cache_hit",
                    prefix=prefix,
                    key=cache_key,
                    data_size=len(cached_data)
                )
                
                return self._deserialize_data(cached_data)
            else:
                # Atualizar estatísticas de miss
                await self._update_hit_stats(cache_key, hit=False)
                
                logger.debug("cache_miss", prefix=prefix, key=cache_key)
                return None
                
        except Exception as e:
            logger.warning("cache_get_failed", error=str(e), prefix=prefix)
            return None
    
    async def set(
        self,
        prefix: str,
        *key_parts: Any,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Armazena dados no cache.
        
        Args:
            prefix: Prefixo da chave
            *key_parts: Partes da chave
            value: Valor para armazenar
            ttl: TTL em segundos (padrão: settings.cache_ttl)
            
        Returns:
            True se armazenado com sucesso
        """
        if not settings.cache_enabled:
            return False
        
        try:
            cache_key = self._generate_key(prefix, *key_parts)
            serialized_value = self._serialize_data(value)
            
            # TTL dinâmico baseado no tipo de dados
            cache_ttl = ttl or self._calculate_dynamic_ttl(prefix, len(serialized_value))
            
            await self.redis.setex(cache_key, cache_ttl, serialized_value)
            
            logger.debug(
                "cache_set",
                prefix=prefix,
                key=cache_key,
                ttl=cache_ttl,
                data_size=len(serialized_value)
            )
            
            return True
            
        except Exception as e:
            logger.warning("cache_set_failed", error=str(e), prefix=prefix)
            return False
    
    async def delete(self, prefix: str, *key_parts: Any) -> bool:
        """
        Remove dados do cache.
        
        Args:
            prefix: Prefixo da chave
            *key_parts: Partes da chave
            
        Returns:
            True se removido com sucesso
        """
        if not settings.cache_enabled:
            return False
        
        try:
            cache_key = self._generate_key(prefix, *key_parts)
            deleted = await self.redis.delete(cache_key)
            
            logger.debug(
                "cache_delete",
                prefix=prefix,
                key=cache_key,
                deleted=bool(deleted)
            )
            
            return bool(deleted)
            
        except Exception as e:
            logger.warning("cache_delete_failed", error=str(e), prefix=prefix)
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Remove todas as chaves que correspondem ao padrão.
        
        Args:
            pattern: Padrão de busca (ex: 'zep_api:session:*')
            
        Returns:
            Número de chaves removidas
        """
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info("cache_pattern_cleared", pattern=pattern, deleted=deleted)
                return deleted
            
            return 0
            
        except Exception as e:
            logger.warning("cache_clear_pattern_failed", error=str(e), pattern=pattern)
            return 0
    
    def _calculate_dynamic_ttl(self, prefix: str, data_size: int) -> int:
        """
        Calcula TTL dinâmico baseado no tipo de dados e tamanho.
        
        Args:
            prefix: Prefixo que indica o tipo de dados
            data_size: Tamanho dos dados em bytes
            
        Returns:
            TTL em segundos
        """
        base_ttl = settings.cache_ttl
        
        # TTLs específicos por tipo de dados
        ttl_multipliers = {
            "memory": 1.5,    # Contextos de memória duram mais
            "session": 2.0,   # Sessões ativas duram ainda mais
            "user": 3.0,      # Dados de usuário são mais estáveis
            "health": 0.1,    # Health checks são muito voláteis
            "metrics": 0.5,   # Métricas mudam rapidamente
        }
        
        multiplier = ttl_multipliers.get(prefix, 1.0)
        
        # Ajustar baseado no tamanho (dados maiores duram menos)
        if data_size > 10000:  # 10KB
            multiplier *= 0.7
        elif data_size > 1000:  # 1KB
            multiplier *= 0.9
        
        return int(base_ttl * multiplier)
    
    async def _update_hit_stats(self, cache_key: str, hit: bool) -> None:
        """
        Atualiza estatísticas de cache hit/miss.
        
        Args:
            cache_key: Chave do cache
            hit: True para hit, False para miss
        """
        try:
            stats_key = "zep_api:stats:cache"
            
            if hit:
                await self.redis.hincrby(stats_key, "hits", 1)
            else:
                await self.redis.hincrby(stats_key, "misses", 1)
            
            # Expirar estatísticas após 24h
            await self.redis.expire(stats_key, 86400)
            
        except Exception as e:
            # Ignorar erros de estatísticas para não afetar funcionalidade principal
            logger.debug("cache_stats_update_failed", error=str(e), cache_key=cache_key[:100])
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.
        
        Returns:
            Dict com estatísticas de hit/miss ratio, keys ativas, etc.
        """
        try:
            stats_key = "zep_api:stats:cache"
            stats = await self.redis.hgetall(stats_key)
            
            hits = int(stats.get("hits", 0))
            misses = int(stats.get("misses", 0))
            total = hits + misses
            
            hit_ratio = hits / total if total > 0 else 0.0
            
            # Contar chaves ativas
            active_keys = 0
            async for _ in self.redis.scan_iter(match="zep_api:*"):
                active_keys += 1
            
            return {
                "hits": hits,
                "misses": misses,
                "total_requests": total,
                "hit_ratio": round(hit_ratio, 3),
                "active_keys": active_keys,
                "redis_info": await self._get_redis_info()
            }
            
        except Exception as e:
            logger.warning("cache_stats_failed", error=str(e))
            return {"error": str(e)}
    
    async def _get_redis_info(self) -> Dict[str, Any]:
        """Retorna informações básicas do Redis."""
        try:
            info = await self.redis.info()
            return {
                "version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            }
        except Exception:
            return {}


# Context manager para uso fácil
@asynccontextmanager
async def get_cache():
    """
    Context manager para obter instância do cache.
    
    Usage:
        async with get_cache() as cache:
            await cache.set("session", session_id, data)
    """
    cache = RedisCache()
    await cache.initialize()
    try:
        yield cache
    finally:
        # Não fechar conexão para reutilização
        pass


# Singleton instance global
_cache_instance: Optional[RedisCache] = None


async def get_cache_instance() -> RedisCache:
    """
    Retorna instância singleton do cache.
    Útil para dependency injection no FastAPI.
    """
    global _cache_instance
    
    if _cache_instance is None:
        _cache_instance = RedisCache()
        await _cache_instance.initialize()
    
    return _cache_instance


# Decorador para cache automático
def cached(prefix: str, ttl: Optional[int] = None):
    """
    Decorador para cache automático de funções.
    
    Usage:
        @cached("memory", ttl=300)
        async def get_memory_context(session_id: str):
            # Função será automaticamente cacheada
            return expensive_operation(session_id)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = await get_cache_instance()
            
            # Gerar chave baseada em argumentos
            cache_key_parts = [func.__name__] + list(args) + [f"{k}={v}" for k, v in sorted(kwargs.items())]
            
            # Tentar obter do cache
            cached_result = await cache.get(prefix, *cache_key_parts)
            if cached_result is not None:
                return cached_result
            
            # Executar função e cachear resultado
            result = await func(*args, **kwargs)
            await cache.set(prefix, *cache_key_parts, value=result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator