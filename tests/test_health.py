"""
Testes para endpoints de health check.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from src.main import app
from src.core.config import settings


@pytest.fixture
def client():
    """Fixture para cliente de teste."""
    # Mock external dependencies during testing
    with patch('src.core.zep_client.client.get_zep_client_sync') as mock_zep, \
         patch('src.core.cache.redis_cache.get_cache_instance') as mock_cache, \
         patch('src.core.metrics.get_metrics') as mock_metrics:
        
        # Setup mocks
        mock_zep.return_value = AsyncMock()
        mock_cache.return_value = AsyncMock()
        mock_metrics.return_value = MagicMock()
        
        return TestClient(app)


class TestHealthEndpoints:
    """Testes para endpoints de health check."""
    
    def test_liveness_probe_success(self, client):
        """Testa liveness probe bem-sucedido."""
        response = client.get("/health/live")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert "version" in data
        assert "service" in data
        assert data["service"] == "zep-ai-memory-api"
    
    def test_readiness_probe_success(self, client):
        """Testa readiness probe quando tudo está saudável."""
        with patch('src.api.v1.health._check_configuration') as mock_config, \
             patch('src.api.v1.health._check_zep_connectivity') as mock_zep:
            
            # Configurar mocks para retornar sucesso
            mock_config.return_value = {"healthy": True, "response_time": 5.0}
            mock_zep.return_value = {"healthy": True, "response_time": 100.0}
            
            response = client.get("/health/ready")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "ready"
            assert data["healthy"] is True
            assert "checks" in data
            assert data["checks"]["configuration"]["healthy"] is True
            assert data["checks"]["zep"]["healthy"] is True
    
    def test_readiness_probe_unhealthy(self, client):
        """Testa readiness probe quando serviços estão indisponíveis."""
        with patch('src.api.v1.health._check_configuration') as mock_config, \
             patch('src.api.v1.health._check_zep_connectivity') as mock_zep:
            
            # Configurar mocks para retornar falha
            mock_config.return_value = {"healthy": False, "error": "Config missing"}
            mock_zep.return_value = {"healthy": False, "error": "Zep unavailable"}
            
            response = client.get("/health/ready")
            
            assert response.status_code == 503
            
            data = response.json()
            assert data["status"] == "not_ready"
            assert data["healthy"] is False
    
    def test_detailed_health_check_success(self, client):
        """Testa health check detalhado com todos os serviços saudáveis."""
        with patch('src.api.v1.health._check_configuration') as mock_config, \
             patch('src.api.v1.health._check_zep_connectivity') as mock_zep, \
             patch('src.api.v1.health._check_cache_connectivity') as mock_cache, \
             patch('src.api.v1.health._check_system_resources') as mock_system, \
             patch('src.api.v1.health._check_database_connectivity') as mock_db:
            
            # Configurar todos os mocks para sucesso
            mock_config.return_value = {"healthy": True, "response_time": 5.0}
            mock_zep.return_value = {"healthy": True, "response_time": 100.0}
            mock_cache.return_value = {"healthy": True, "response_time": 10.0}
            mock_system.return_value = {"healthy": True, "response_time": 15.0}
            mock_db.return_value = {"healthy": True, "response_time": 20.0}
            
            response = client.get("/health/detailed")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["overall_healthy"] is True
            assert data["critical_services_healthy"] is True
            assert data["system_healthy"] is True
            assert len(data["optional_issues"]) == 0
            
            # Verificar se todos os checks estão presentes
            assert "configuration" in data["checks"]
            assert "zep" in data["checks"]
            assert "cache" in data["checks"]
            assert "system" in data["checks"]
            assert "database" in data["checks"]
    
    def test_detailed_health_check_degraded(self, client):
        """Testa health check com serviços opcionais degradados."""
        with patch('src.api.v1.health._check_configuration') as mock_config, \
             patch('src.api.v1.health._check_zep_connectivity') as mock_zep, \
             patch('src.api.v1.health._check_cache_connectivity') as mock_cache, \
             patch('src.api.v1.health._check_system_resources') as mock_system, \
             patch('src.api.v1.health._check_database_connectivity') as mock_db:
            
            # Serviços críticos saudáveis
            mock_config.return_value = {"healthy": True, "response_time": 5.0}
            mock_zep.return_value = {"healthy": True, "response_time": 100.0}
            mock_system.return_value = {"healthy": True, "response_time": 15.0}
            
            # Serviços opcionais com problemas
            mock_cache.return_value = {"healthy": False, "error": "Redis down"}
            mock_db.return_value = {"healthy": False, "error": "DB unavailable"}
            
            response = client.get("/health/detailed")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "degraded"
            assert data["overall_healthy"] is True  # Ainda considerado healthy
            assert data["critical_services_healthy"] is True
            assert data["system_healthy"] is True
            assert len(data["optional_issues"]) == 2  # cache e database
    
    def test_detailed_health_check_unhealthy(self, client):
        """Testa health check com serviços críticos falhando."""
        with patch('src.api.v1.health._check_configuration') as mock_config, \
             patch('src.api.v1.health._check_zep_connectivity') as mock_zep, \
             patch('src.api.v1.health._check_cache_connectivity') as mock_cache, \
             patch('src.api.v1.health._check_system_resources') as mock_system, \
             patch('src.api.v1.health._check_database_connectivity') as mock_db:
            
            # Serviço crítico falhando
            mock_config.return_value = {"healthy": True, "response_time": 5.0}
            mock_zep.return_value = {"healthy": False, "error": "Zep unreachable"}
            mock_cache.return_value = {"healthy": True, "response_time": 10.0}
            mock_system.return_value = {"healthy": True, "response_time": 15.0}
            mock_db.return_value = {"healthy": True, "response_time": 20.0}
            
            response = client.get("/health/detailed")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["overall_healthy"] is False
            assert data["critical_services_healthy"] is False
    
    def test_metrics_summary(self, client):
        """Testa endpoint de resumo de métricas."""
        with patch('src.core.metrics.get_metrics') as mock_get_metrics, \
             patch('src.core.cache.get_cache_instance') as mock_get_cache:
            
            # Mock das métricas
            mock_metrics = MagicMock()
            mock_metrics._start_time = 1000.0
            mock_metrics.update_system_metrics = AsyncMock()
            mock_get_metrics.return_value = mock_metrics
            
            # Mock do cache
            mock_cache = AsyncMock()
            mock_cache.get_cache_stats.return_value = {
                "hit_ratio": 0.85,
                "active_keys": 100,
                "total_requests": 1000
            }
            mock_get_cache.return_value = mock_cache
            
            response = client.get("/health/metrics-summary")
            
            assert response.status_code == 200
            
            data = response.json()
            assert "timestamp" in data
            assert "metrics" in data
            assert "api" in data["metrics"]
            assert "system" in data["metrics"]
            assert "cache" in data["metrics"]
            assert "services" in data["metrics"]
    
    def test_circuit_breaker_status(self, client):
        """Testa endpoint de status do circuit breaker."""
        with patch('src.api.v1.health._check_zep_connectivity') as mock_zep, \
             patch('src.api.v1.health._check_cache_connectivity') as mock_cache, \
             patch('src.api.v1.health._check_system_resources') as mock_system:
            
            # Configurar mocks
            mock_zep.return_value = {"healthy": True, "response_time": 100.0}
            mock_cache.return_value = {"healthy": True, "response_time": 10.0}
            mock_system.return_value = {"healthy": True, "response_time": 15.0}
            
            response = client.get("/health/circuit-breaker")
            
            assert response.status_code == 200
            
            data = response.json()
            assert "timestamp" in data
            assert "circuit_breakers" in data
            assert "overall_status" in data
            
            # Verificar circuit breakers
            cb = data["circuit_breakers"]
            assert "zep" in cb
            assert "cache" in cb
            assert "system" in cb
            
            # Todos devem estar "closed" (funcionando)
            assert cb["zep"]["status"] == "closed"
            assert cb["cache"]["status"] == "closed"
            assert cb["system"]["status"] == "closed"
            
            assert data["overall_status"] == "healthy"


class TestHealthCheckFunctions:
    """Testes para funções individuais de health check."""
    
    @pytest.mark.asyncio
    async def test_check_configuration_success(self):
        """Testa verificação de configuração bem-sucedida."""
        from src.api.v1.health import _check_configuration
        
        # Simular configurações válidas
        original_values = (
            settings.zep_api_key,
            settings.zep_api_url,
            settings.api_secret_key
        )
        
        settings.zep_api_key = "valid_key"
        settings.zep_api_url = "http://localhost:8000"
        settings.api_secret_key = "a" * 32  # 32 caracteres
        
        try:
            result = await _check_configuration()
            
            assert result["healthy"] is True
            assert "response_time" in result
            assert result["details"]["missing_configs"] is None
        finally:
            # Restaurar valores originais
            settings.zep_api_key, settings.zep_api_url, settings.api_secret_key = original_values
    
    @pytest.mark.asyncio
    async def test_check_configuration_missing_keys(self):
        """Testa verificação com configurações faltando."""
        from src.api.v1.health import _check_configuration
        
        # Simular configurações inválidas
        original_values = (
            settings.zep_api_key,
            settings.zep_api_url,
            settings.api_secret_key
        )
        
        # Use object.__setattr__ to bypass validation for testing
        object.__setattr__(settings, 'zep_api_key', "")
        object.__setattr__(settings, 'zep_api_url', "")
        object.__setattr__(settings, 'api_secret_key', "short")  # Muito curta
        
        try:
            result = await _check_configuration()
            
            assert result["healthy"] is False
            assert "error" in result
            assert len(result["details"]["missing_configs"]) == 3
        finally:
            # Restaurar valores originais
            settings.zep_api_key, settings.zep_api_url, settings.api_secret_key = original_values
    
    @pytest.mark.asyncio
    async def test_check_zep_connectivity_success(self):
        """Testa verificação de conectividade Zep bem-sucedida."""
        from src.api.v1.health import _check_zep_connectivity
        
        with patch('src.core.zep_client.client.get_zep_client_sync') as mock_get_client:
            # Mock do cliente Zep
            mock_client = AsyncMock()
            mock_client.get_memory = AsyncMock(return_value={
                "session_id": "health_check_session", 
                "context": "", 
                "messages": [],
                "relevant_facts": []
            })
            mock_get_client.return_value = mock_client
            
            result = await _check_zep_connectivity()
            
            assert result["healthy"] is True
            assert "response_time" in result
            assert result["details"]["operational"] is True
    
    @pytest.mark.asyncio
    async def test_check_zep_connectivity_failure(self):
        """Testa verificação de conectividade Zep com falha."""
        from src.api.v1.health import _check_zep_connectivity
        
        with patch('src.core.zep_client.client.get_zep_client_sync') as mock_get_client:
            # Mock que lança exceção
            mock_get_client.side_effect = Exception("Connection failed")
            
            result = await _check_zep_connectivity()
            
            assert result["healthy"] is False
            assert "error" in result
            assert "Connection failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_check_cache_connectivity_disabled(self):
        """Testa verificação de cache quando está desabilitado."""
        from src.api.v1.health import _check_cache_connectivity
        
        # Simular cache desabilitado
        original_cache_enabled = settings.cache_enabled
        settings.cache_enabled = False
        
        try:
            result = await _check_cache_connectivity()
            
            assert result["healthy"] is True
            assert result["details"]["status"] == "disabled"
        finally:
            settings.cache_enabled = original_cache_enabled
    
    @pytest.mark.asyncio
    async def test_check_cache_connectivity_success(self):
        """Testa verificação de cache bem-sucedida."""
        from src.api.v1.health import _check_cache_connectivity
        
        # Simular cache habilitado
        original_cache_enabled = settings.cache_enabled
        settings.cache_enabled = True
        
        try:
            with patch('src.core.cache.redis_cache.get_cache_instance') as mock_get_cache:
                # Mock do cache
                mock_cache = AsyncMock()
                mock_cache.redis.ping = AsyncMock()
                mock_cache.set = AsyncMock(return_value=True)
                mock_cache.get = AsyncMock(return_value="test_value")
                mock_cache.delete = AsyncMock(return_value=True)
                mock_cache.get_cache_stats = AsyncMock(return_value={
                    "hit_ratio": 0.8,
                    "active_keys": 50
                })
                mock_get_cache.return_value = mock_cache
                
                result = await _check_cache_connectivity()
                
                assert result["healthy"] is True
                assert result["details"]["operations_working"] is True
        finally:
            settings.cache_enabled = original_cache_enabled
    
    @pytest.mark.asyncio
    async def test_check_system_resources(self):
        """Testa verificação de recursos do sistema."""
        from src.api.v1.health import _check_system_resources
        
        with patch('psutil.cpu_percent') as mock_cpu, \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('psutil.Process') as mock_process:
            
            # Mock dos recursos do sistema
            mock_cpu.return_value = 50.0  # 50% CPU
            
            mock_memory_info = MagicMock()
            mock_memory_info.total = 8 * 1024**3  # 8GB
            mock_memory_info.available = 4 * 1024**3  # 4GB disponível
            mock_memory_info.percent = 50.0
            mock_memory.return_value = mock_memory_info
            
            mock_disk_info = MagicMock()
            mock_disk_info.total = 100 * 1024**3  # 100GB
            mock_disk_info.used = 50 * 1024**3   # 50GB usado
            mock_disk_info.free = 50 * 1024**3   # 50GB livre
            mock_disk.return_value = mock_disk_info
            
            mock_process_instance = MagicMock()
            mock_memory_info_process = MagicMock()
            mock_memory_info_process.rss = 100 * 1024**2  # 100MB
            mock_process_instance.memory_info.return_value = mock_memory_info_process
            mock_process_instance.memory_percent.return_value = 1.2
            mock_process.return_value = mock_process_instance
            
            result = await _check_system_resources()
            
            assert result["healthy"] is True
            assert result["details"]["cpu"]["percent"] == 50.0
            assert result["details"]["memory"]["percent"] == 50.0
            assert result["details"]["disk"]["percent"] == 50.0
            assert result["details"]["process"]["memory_mb"] == 100.0