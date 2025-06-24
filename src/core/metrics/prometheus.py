"""
Sistema de métricas Prometheus para observabilidade completa.
Coleta métricas de performance, uso e saúde da aplicação.
"""

import time
import psutil
from typing import Dict, Any, Optional
import structlog
from prometheus_client import (
    Counter, Histogram, Gauge, Info, Enum,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from contextlib import asynccontextmanager

from src.core.config import settings

logger = structlog.get_logger(__name__)


class PrometheusMetrics:
    """
    Coletor centralizado de métricas Prometheus.
    
    Coleta métricas sobre:
    - Performance da API (latência, throughput, erros)
    - Operações Zep (memory, graph, users)
    - Cache Redis (hit ratio, performance)
    - Sistema (CPU, memória, conexões)
    - Rate limiting (requests, blocks)
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self._start_time = time.time()
        self._setup_metrics()
    
    def _setup_metrics(self):
        """Inicializa todas as métricas Prometheus."""
        
        # === API Metrics ===
        self.api_requests_total = Counter(
            'api_requests_total',
            'Total number of API requests',
            ['method', 'endpoint', 'status_code', 'user_type'],
            registry=self.registry
        )
        
        self.api_request_duration = Histogram(
            'api_request_duration_seconds',
            'API request duration in seconds',
            ['method', 'endpoint'],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry
        )
        
        self.api_request_size = Histogram(
            'api_request_size_bytes',
            'API request size in bytes',
            ['method', 'endpoint'],
            buckets=(100, 1000, 10000, 100000, 1000000),
            registry=self.registry
        )
        
        self.api_response_size = Histogram(
            'api_response_size_bytes',
            'API response size in bytes',
            ['method', 'endpoint', 'status_code'],
            buckets=(100, 1000, 10000, 100000, 1000000),
            registry=self.registry
        )
        
        # === Zep Operations Metrics ===
        self.zep_operations_total = Counter(
            'zep_operations_total',
            'Total Zep operations',
            ['operation', 'status', 'user_id_hash'],
            registry=self.registry
        )
        
        self.zep_operation_duration = Histogram(
            'zep_operation_duration_seconds',
            'Zep operation duration in seconds',
            ['operation'],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
            registry=self.registry
        )
        
        self.zep_connection_pool = Gauge(
            'zep_connection_pool_size',
            'Current Zep connection pool size',
            registry=self.registry
        )
        
        # === Memory Operations ===
        self.memory_sessions_active = Gauge(
            'memory_sessions_active',
            'Currently active memory sessions',
            registry=self.registry
        )
        
        self.memory_messages_total = Counter(
            'memory_messages_total',
            'Total messages added to memory',
            ['session_type', 'role', 'role_type'],
            registry=self.registry
        )
        
        self.memory_context_length = Histogram(
            'memory_context_length_chars',
            'Memory context string length in characters',
            ['session_type'],
            buckets=(100, 500, 1000, 2000, 5000, 10000, 20000),
            registry=self.registry
        )
        
        # === Cache Metrics ===
        self.cache_operations_total = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'prefix', 'status'],
            registry=self.registry
        )
        
        self.cache_hit_ratio = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio (0-1)',
            ['prefix'],
            registry=self.registry
        )
        
        self.cache_operation_duration = Histogram(
            'cache_operation_duration_seconds',
            'Cache operation duration in seconds',
            ['operation', 'prefix'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25),
            registry=self.registry
        )
        
        self.redis_connections_active = Gauge(
            'redis_connections_active',
            'Active Redis connections',
            registry=self.registry
        )
        
        # === Rate Limiting Metrics ===
        self.rate_limit_checks_total = Counter(
            'rate_limit_checks_total',
            'Total rate limit checks',
            ['check_type', 'result'],
            registry=self.registry
        )
        
        self.rate_limit_blocks_total = Counter(
            'rate_limit_blocks_total',
            'Total rate limit blocks',
            ['check_type', 'severity'],
            registry=self.registry
        )
        
        # === System Metrics ===
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            ['type'],
            registry=self.registry
        )
        
        self.process_memory_usage = Gauge(
            'process_memory_usage_bytes',
            'Process memory usage in bytes',
            ['type'],
            registry=self.registry
        )
        
        self.system_disk_usage = Gauge(
            'system_disk_usage_percent',
            'System disk usage percentage',
            ['mount_point'],
            registry=self.registry
        )
        
        # === Application Info ===
        self.app_info = Info(
            'app_info',
            'Application information',
            registry=self.registry
        )
        
        self.app_uptime = Gauge(
            'app_uptime_seconds',
            'Application uptime in seconds',
            registry=self.registry
        )
        
        self.app_status = Enum(
            'app_status',
            'Application status',
            states=['starting', 'healthy', 'degraded', 'unhealthy'],
            registry=self.registry
        )
        
        # === Health Check Metrics ===
        self.health_check_duration = Histogram(
            'health_check_duration_seconds',
            'Health check duration in seconds',
            ['check_type', 'status'],
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
            registry=self.registry
        )
        
        self.dependency_status = Gauge(
            'dependency_status',
            'Dependency health status (1=healthy, 0=unhealthy)',
            ['dependency'],
            registry=self.registry
        )
        
        # Inicializar informações da aplicação
        self._set_app_info()
    
    def _set_app_info(self):
        """Define informações estáticas da aplicação."""
        self.app_info.info({
            'version': settings.api_version,
            'title': settings.api_title,
            'python_version': f"{psutil.LINUX}",  # Placeholder - ajustar conforme necessário
            'debug': str(settings.debug),
            'environment': 'development' if settings.debug else 'production'
        })
        
        self.app_status.state('healthy')
    
    # === Métodos para registrar métricas ===
    
    def record_api_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        request_size: int = 0,
        response_size: int = 0,
        user_type: str = "anonymous"
    ):
        """Registra métricas de request da API."""
        self.api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            user_type=user_type
        ).inc()
        
        self.api_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        if request_size > 0:
            self.api_request_size.labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)
        
        if response_size > 0:
            self.api_response_size.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).observe(response_size)
    
    def record_zep_operation(
        self,
        operation: str,
        duration: float,
        status: str = "success",
        user_id_hash: str = "anonymous"
    ):
        """Registra métricas de operação Zep."""
        self.zep_operations_total.labels(
            operation=operation,
            status=status,
            user_id_hash=user_id_hash[:8]  # Apenas primeiros 8 chars para privacidade
        ).inc()
        
        self.zep_operation_duration.labels(
            operation=operation
        ).observe(duration)
    
    def record_memory_operation(
        self,
        session_type: str,
        message_count: int = 0,
        context_length: int = 0,
        role: str = "",
        role_type: str = ""
    ):
        """Registra métricas de operação de memória."""
        if message_count > 0:
            self.memory_messages_total.labels(
                session_type=session_type,
                role=role,
                role_type=role_type
            ).inc(message_count)
        
        if context_length > 0:
            self.memory_context_length.labels(
                session_type=session_type
            ).observe(context_length)
    
    def record_cache_operation(
        self,
        operation: str,
        prefix: str,
        duration: float,
        status: str = "success"
    ):
        """Registra métricas de operação de cache."""
        self.cache_operations_total.labels(
            operation=operation,
            prefix=prefix,
            status=status
        ).inc()
        
        self.cache_operation_duration.labels(
            operation=operation,
            prefix=prefix
        ).observe(duration)
    
    def update_cache_hit_ratio(self, prefix: str, hit_ratio: float):
        """Atualiza ratio de cache hit."""
        self.cache_hit_ratio.labels(prefix=prefix).set(hit_ratio)
    
    def record_rate_limit(
        self,
        check_type: str,
        result: str,
        severity: str = "normal"
    ):
        """Registra métricas de rate limiting."""
        self.rate_limit_checks_total.labels(
            check_type=check_type,
            result=result
        ).inc()
        
        if result == "blocked":
            self.rate_limit_blocks_total.labels(
                check_type=check_type,
                severity=severity
            ).inc()
    
    def record_health_check(
        self,
        check_type: str,
        duration: float,
        status: str,
        is_healthy: bool
    ):
        """Registra métricas de health check."""
        self.health_check_duration.labels(
            check_type=check_type,
            status=status
        ).observe(duration)
        
        self.dependency_status.labels(
            dependency=check_type
        ).set(1 if is_healthy else 0)
    
    async def update_system_metrics(self):
        """Atualiza métricas do sistema."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent()
            self.system_cpu_usage.set(cpu_percent)
            
            # Memória do sistema
            memory = psutil.virtual_memory()
            self.system_memory_usage.labels(type='total').set(memory.total)
            self.system_memory_usage.labels(type='available').set(memory.available)
            self.system_memory_usage.labels(type='used').set(memory.used)
            
            # Memória do processo
            process = psutil.Process()
            process_memory = process.memory_info()
            self.process_memory_usage.labels(type='rss').set(process_memory.rss)
            self.process_memory_usage.labels(type='vms').set(process_memory.vms)
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.system_disk_usage.labels(mount_point='/').set(disk_percent)
            
            # Uptime
            current_uptime = time.time() - self._start_time
            self.app_uptime.set(current_uptime)
            
        except Exception as e:
            logger.warning("system_metrics_update_failed", error=str(e))
    
    def update_active_sessions(self, count: int):
        """Atualiza contador de sessões ativas."""
        self.memory_sessions_active.set(count)
    
    def update_connection_pools(self, zep_pool: int = 0, redis_pool: int = 0):
        """Atualiza métricas de connection pools."""
        if zep_pool > 0:
            self.zep_connection_pool.set(zep_pool)
        if redis_pool > 0:
            self.redis_connections_active.set(redis_pool)
    
    def set_app_status(self, status: str):
        """Define status da aplicação."""
        valid_statuses = ['starting', 'healthy', 'degraded', 'unhealthy']
        if status in valid_statuses:
            self.app_status.state(status)
    
    def generate_metrics(self) -> bytes:
        """Gera métricas em formato Prometheus."""
        return generate_latest(self.registry)
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Retorna resumo das métricas em formato JSON."""
        await self.update_system_metrics()
        
        return {
            "timestamp": time.time(),
            "uptime_seconds": time.time() - self._start_time,
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            },
            "application": {
                "version": settings.api_version,
                "debug": settings.debug,
                "status": "healthy"  # Simplificado - implementar lógica real
            }
        }


# Context manager para métricas com timing automático
@asynccontextmanager
async def timed_operation(metrics: PrometheusMetrics, operation_type: str, **labels):
    """
    Context manager para medir tempo de operações automaticamente.
    
    Usage:
        async with timed_operation(metrics, "zep_operation", operation="memory_add"):
            result = await zep_client.add_memory(...)
    """
    start_time = time.time()
    status = "success"
    
    try:
        yield
    except Exception as e:
        status = "error"
        raise
    finally:
        duration = time.time() - start_time
        
        if operation_type == "zep_operation":
            metrics.record_zep_operation(
                operation=labels.get("operation", "unknown"),
                duration=duration,
                status=status,
                user_id_hash=labels.get("user_id_hash", "anonymous")
            )
        elif operation_type == "cache_operation":
            metrics.record_cache_operation(
                operation=labels.get("operation", "unknown"),
                prefix=labels.get("prefix", "unknown"),
                duration=duration,
                status=status
            )


# Singleton instance global
_metrics_instance: Optional[PrometheusMetrics] = None


def get_metrics() -> PrometheusMetrics:
    """
    Retorna instância singleton das métricas.
    Útil para dependency injection no FastAPI.
    """
    global _metrics_instance
    
    if _metrics_instance is None:
        _metrics_instance = PrometheusMetrics()
    
    return _metrics_instance


# Helper functions para facilitar uso
def increment_api_request(method: str, endpoint: str, status_code: int, **kwargs):
    """Incrementa contador de requests da API."""
    metrics = get_metrics()
    metrics.api_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code,
        user_type=kwargs.get("user_type", "anonymous")
    ).inc()


def observe_duration(metric_name: str, duration: float, **labels):
    """Observa duração em histograma específico."""
    metrics = get_metrics()
    
    if hasattr(metrics, metric_name):
        histogram = getattr(metrics, metric_name)
        histogram.labels(**labels).observe(duration)