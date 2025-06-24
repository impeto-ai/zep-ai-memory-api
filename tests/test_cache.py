"""
Testes para sistema de cache Redis.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from src.core.cache.redis_cache import RedisCache, CacheError, cached
from src.core.config import settings


@pytest.fixture
async def cache_instance():
    """Fixture para instância de cache com mock Redis."""
    cache = RedisCache()
    
    # Mock do Redis
    mock_redis = AsyncMock()
    cache._redis_pool = mock_redis
    
    return cache, mock_redis


@pytest.mark.asyncio
class TestRedisCache:
    """Testes para RedisCache."""
    
    async def test_generate_key(self):
        """Testa geração de chaves de cache."""
        cache = RedisCache()
        
        # Teste com argumentos simples
        key1 = cache._generate_key("test", "arg1", "arg2")
        key2 = cache._generate_key("test", "arg1", "arg2")
        
        # Chaves idênticas para argumentos idênticos
        assert key1 == key2
        assert key1.startswith("zep_api:test:")
        
        # Chaves diferentes para argumentos diferentes
        key3 = cache._generate_key("test", "arg1", "different")
        assert key1 != key3
    
    async def test_serialize_deserialize_data(self):
        """Testa serialização e deserialização de dados."""
        cache = RedisCache()
        
        # Teste com dict
        data_dict = {"key": "value", "number": 42}
        serialized = cache._serialize_data(data_dict)
        deserialized = cache._deserialize_data(serialized)
        assert deserialized == data_dict
        
        # Teste com lista
        data_list = [1, 2, 3, "string"]
        serialized = cache._serialize_data(data_list)
        deserialized = cache._deserialize_data(serialized)
        assert deserialized == data_list
        
        # Teste com string simples
        data_str = "simple string"
        serialized = cache._serialize_data(data_str)
        deserialized = cache._deserialize_data(serialized)
        assert deserialized == data_str
    
    async def test_get_cache_hit(self, cache_instance):
        """Testa cache hit (dados encontrados)."""
        cache, mock_redis = cache_instance
        
        # Configurar mock para retornar dados
        test_data = '{"cached": "data"}'
        mock_redis.get.return_value = test_data
        
        # Simular cache habilitado
        original_cache_enabled = settings.cache_enabled
        settings.cache_enabled = True
        
        try:
            result = await cache.get("test", "key1")
            
            # Verificar chamada ao Redis
            mock_redis.get.assert_called_once()
            
            # Verificar resultado
            assert result == {"cached": "data"}
        finally:
            settings.cache_enabled = original_cache_enabled
    
    async def test_get_cache_miss(self, cache_instance):
        """Testa cache miss (dados não encontrados)."""
        cache, mock_redis = cache_instance
        
        # Configurar mock para retornar None
        mock_redis.get.return_value = None
        
        # Simular cache habilitado
        original_cache_enabled = settings.cache_enabled
        settings.cache_enabled = True
        
        try:
            result = await cache.get("test", "key1")
            
            # Verificar chamada ao Redis
            mock_redis.get.assert_called_once()
            
            # Resultado deve ser None
            assert result is None
        finally:
            settings.cache_enabled = original_cache_enabled
    
    async def test_get_cache_disabled(self, cache_instance):
        """Testa get quando cache está desabilitado."""
        cache, mock_redis = cache_instance
        
        # Simular cache desabilitado
        original_cache_enabled = settings.cache_enabled
        settings.cache_enabled = False
        
        try:
            result = await cache.get("test", "key1")
            
            # Redis não deve ser chamado
            mock_redis.get.assert_not_called()
            
            # Resultado deve ser None
            assert result is None
        finally:
            settings.cache_enabled = original_cache_enabled
    
    async def test_set_success(self, cache_instance):
        """Testa set bem-sucedido."""
        cache, mock_redis = cache_instance
        
        # Simular cache habilitado
        original_cache_enabled = settings.cache_enabled
        settings.cache_enabled = True
        
        try:
            test_data = {"test": "value"}
            result = await cache.set("test", "key1", value=test_data, ttl=300)
            
            # Verificar chamada ao Redis
            mock_redis.setex.assert_called_once()
            
            # Verificar argumentos da chamada
            call_args = mock_redis.setex.call_args
            assert call_args[0][1] == 300  # TTL
            
            # Resultado deve ser True
            assert result is True
        finally:
            settings.cache_enabled = original_cache_enabled
    
    async def test_set_cache_disabled(self, cache_instance):
        """Testa set quando cache está desabilitado."""
        cache, mock_redis = cache_instance
        
        # Simular cache desabilitado
        original_cache_enabled = settings.cache_enabled
        settings.cache_enabled = False
        
        try:
            result = await cache.set("test", "key1", value={"data": "test"})
            
            # Redis não deve ser chamado
            mock_redis.setex.assert_not_called()
            
            # Resultado deve ser False
            assert result is False
        finally:
            settings.cache_enabled = original_cache_enabled
    
    async def test_delete_success(self, cache_instance):
        """Testa delete bem-sucedido."""
        cache, mock_redis = cache_instance
        
        # Configurar mock para retornar 1 (deletado)
        mock_redis.delete.return_value = 1
        
        # Simular cache habilitado
        original_cache_enabled = settings.cache_enabled
        settings.cache_enabled = True
        
        try:
            result = await cache.delete("test", "key1")
            
            # Verificar chamada ao Redis
            mock_redis.delete.assert_called_once()
            
            # Resultado deve ser True
            assert result is True
        finally:
            settings.cache_enabled = original_cache_enabled
    
    async def test_delete_not_found(self, cache_instance):
        """Testa delete quando chave não existe."""
        cache, mock_redis = cache_instance
        
        # Configurar mock para retornar 0 (não encontrado)
        mock_redis.delete.return_value = 0
        
        # Simular cache habilitado
        original_cache_enabled = settings.cache_enabled
        settings.cache_enabled = True
        
        try:
            result = await cache.delete("test", "key1")
            
            # Verificar chamada ao Redis
            mock_redis.delete.assert_called_once()
            
            # Resultado deve ser False
            assert result is False
        finally:
            settings.cache_enabled = original_cache_enabled
    
    async def test_clear_pattern(self, cache_instance):
        """Testa limpeza por padrão."""
        cache, mock_redis = cache_instance
        
        # Configurar mock para scan_iter
        mock_keys = ["key1", "key2", "key3"]
        mock_redis.scan_iter.return_value = mock_keys
        mock_redis.delete.return_value = 3
        
        result = await cache.clear_pattern("test:*")
        
        # Verificar chamadas
        mock_redis.scan_iter.assert_called_once_with(match="test:*")
        mock_redis.delete.assert_called_once_with(*mock_keys)
        
        # Resultado deve ser 3
        assert result == 3
    
    async def test_calculate_dynamic_ttl(self):
        """Testa cálculo de TTL dinâmico."""
        cache = RedisCache()
        
        base_ttl = settings.cache_ttl
        
        # Teste com diferentes prefixos
        memory_ttl = cache._calculate_dynamic_ttl("memory", 1000)
        session_ttl = cache._calculate_dynamic_ttl("session", 1000)
        health_ttl = cache._calculate_dynamic_ttl("health", 1000)
        
        # Memory deve durar mais que health
        assert memory_ttl > health_ttl
        assert session_ttl > memory_ttl
        
        # Dados maiores devem ter TTL menor
        small_data_ttl = cache._calculate_dynamic_ttl("test", 100)
        large_data_ttl = cache._calculate_dynamic_ttl("test", 20000)
        assert small_data_ttl > large_data_ttl
    
    async def test_get_cache_stats(self, cache_instance):
        """Testa obtenção de estatísticas do cache."""
        cache, mock_redis = cache_instance
        
        # Configurar mocks
        mock_redis.hgetall.return_value = {"hits": "100", "misses": "20"}
        mock_redis.scan_iter.return_value = ["key1", "key2", "key3"]
        mock_redis.info.return_value = {
            "redis_version": "6.2.0",
            "connected_clients": 5,
            "used_memory_human": "1.2M",
            "uptime_in_seconds": 3600
        }
        
        stats = await cache.get_cache_stats()
        
        # Verificar estatísticas
        assert stats["hits"] == 100
        assert stats["misses"] == 20
        assert stats["total_requests"] == 120
        assert abs(stats["hit_ratio"] - 0.833) < 0.001  # 100/120 ≈ 0.833
        assert stats["active_keys"] == 3
        assert "redis_info" in stats


@pytest.mark.asyncio
class TestCachedDecorator:
    """Testes para o decorador @cached."""
    
    async def test_cached_decorator_first_call(self):
        """Testa primeiro call (cache miss)."""
        with patch('src.core.cache.redis_cache.get_cache_instance') as mock_get_cache:
            # Setup mock cache
            mock_cache = AsyncMock()
            mock_cache.get.return_value = None  # Cache miss
            mock_get_cache.return_value = mock_cache
            
            @cached("test", ttl=300)
            async def test_function(arg1, arg2):
                return f"result_{arg1}_{arg2}"
            
            # Primeira chamada
            result = await test_function("a", "b")
            
            # Verificar resultado
            assert result == "result_a_b"
            
            # Verificar chamadas ao cache
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_called_once()
    
    async def test_cached_decorator_cache_hit(self):
        """Testa segundo call (cache hit)."""
        with patch('src.core.cache.redis_cache.get_cache_instance') as mock_get_cache:
            # Setup mock cache
            mock_cache = AsyncMock()
            cached_result = "cached_result_a_b"
            mock_cache.get.return_value = cached_result  # Cache hit
            mock_get_cache.return_value = mock_cache
            
            @cached("test", ttl=300)
            async def test_function(arg1, arg2):
                return f"fresh_result_{arg1}_{arg2}"
            
            # Segunda chamada
            result = await test_function("a", "b")
            
            # Resultado deve vir do cache
            assert result == cached_result
            
            # Cache get deve ser chamado, mas set não
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_not_called()


class TestCacheUtils:
    """Testes para utilitários de cache."""
    
    @pytest.mark.asyncio
    async def test_get_cache_instance_singleton(self):
        """Testa se get_cache_instance retorna singleton."""
        from src.core.cache.redis_cache import get_cache_instance
        
        with patch.object(RedisCache, 'initialize') as mock_init:
            # Primeira chamada
            cache1 = await get_cache_instance()
            
            # Segunda chamada
            cache2 = await get_cache_instance()
            
            # Deve ser a mesma instância
            assert cache1 is cache2
            
            # Initialize deve ser chamado apenas uma vez
            assert mock_init.call_count == 1
    
    @pytest.mark.asyncio
    async def test_get_cache_context_manager(self):
        """Testa context manager do cache."""
        from src.core.cache.redis_cache import get_cache
        
        with patch.object(RedisCache, 'initialize') as mock_init:
            async with get_cache() as cache:
                assert isinstance(cache, RedisCache)
                mock_init.assert_called_once()


class TestCacheErrors:
    """Testes para tratamento de erros do cache."""
    
    @pytest.mark.asyncio
    async def test_cache_error_handling(self, cache_instance):
        """Testa tratamento de erros do Redis."""
        cache, mock_redis = cache_instance
        
        # Configurar mock para lançar exceção
        mock_redis.get.side_effect = Exception("Redis connection failed")
        
        # Simular cache habilitado
        original_cache_enabled = settings.cache_enabled
        settings.cache_enabled = True
        
        try:
            # Get deve retornar None em caso de erro
            result = await cache.get("test", "key1")
            assert result is None
        finally:
            settings.cache_enabled = original_cache_enabled
    
    @pytest.mark.asyncio
    async def test_initialization_error(self):
        """Testa erro na inicialização do Redis."""
        cache = RedisCache()
        
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping.side_effect = Exception("Connection failed")
            mock_from_url.return_value = mock_redis
            
            # Deve lançar CacheError
            with pytest.raises(CacheError, match="Failed to initialize Redis"):
                await cache.initialize()