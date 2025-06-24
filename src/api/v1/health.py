"""
Health Check endpoints robustos para monitoramento e observabilidade.
Implementa probes para Kubernetes e monitoramento completo de dependências.
"""

import time
import asyncio
import psutil
from typing import Dict, Any, List
import structlog
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.zep_client.client import get_zep_client_sync
from src.core.cache import get_cache_instance, CacheError
from src.core.metrics import get_metrics

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get(
    "/live",
    summary="Liveness Probe",
    description="""
    Endpoint de liveness probe para Kubernetes.
    
    **Uso:**
    - Kubernetes liveness probe
    - Load balancer health check
    - Monitoring básico de uptime
    
    **Resposta:**
    - 200: Aplicação está rodando
    - 500: Aplicação com problemas críticos
    """,
    responses={
        200: {"description": "Aplicação funcionando"},
        500: {"description": "Aplicação com problemas críticos"}
    }
)
async def liveness_probe():
    """
    Liveness probe - verifica se a aplicação está rodando.
    
    Este endpoint deve responder rapidamente e apenas verificar
    se o processo está funcionando, sem verificar dependências externas.
    """
    try:
        return {
            "status": "alive",
            "timestamp": time.time(),
            "version": settings.api_version,
            "service": "zep-ai-memory-api"
        }
    except Exception as e:
        logger.error("liveness_probe_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Liveness check failed"
        )


@router.get(
    "/ready",
    summary="Readiness Probe", 
    description="""
    Endpoint de readiness probe para Kubernetes.
    
    **Verificações:**
    - Conectividade com Zep
    - Status das dependências críticas
    - Configurações essenciais
    
    **Uso:**
    - Kubernetes readiness probe
    - Deploy verification
    - Dependency health monitoring
    """,
    responses={
        200: {"description": "Aplicação pronta para receber tráfego"},
        503: {"description": "Aplicação não pronta - dependências indisponíveis"}
    }
)
async def readiness_probe():
    """
    Readiness probe - verifica se a aplicação está pronta para tráfego.
    
    Verifica todas as dependências críticas antes de aceitar requests.
    """
    health_checks = {}
    overall_healthy = True
    
    try:
        # 1. Verificar configurações essenciais
        config_check = await _check_configuration()
        health_checks["configuration"] = config_check
        if not config_check["healthy"]:
            overall_healthy = False
        
        # 2. Verificar conectividade com Zep
        zep_check = await _check_zep_connectivity()
        health_checks["zep"] = zep_check
        if not zep_check["healthy"]:
            overall_healthy = False
        
        # 3. Verificar dependências opcionais (não afetam readiness)
        cache_check = await _check_cache_connectivity()
        health_checks["cache"] = cache_check
        # Cache não afeta readiness - apenas warning
        
        response = {
            "status": "ready" if overall_healthy else "not_ready",
            "timestamp": time.time(),
            "version": settings.api_version,
            "checks": health_checks,
            "healthy": overall_healthy
        }
        
        if overall_healthy:
            return response
        else:
            return JSONResponse(
                status_code=503,
                content=response
            )
            
    except Exception as e:
        logger.error("readiness_probe_failed", error=str(e), exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "timestamp": time.time(),
                "error": str(e),
                "healthy": False
            }
        )


@router.get(
    "/detailed",
    summary="Health Check Detalhado",
    description="""
    Health check completo com detalhes de todas as dependências.
    
    **Informações incluídas:**
    - Status de todas as dependências
    - Métricas de performance
    - Configurações ativas
    - Tempos de resposta
    - Versões de componentes
    
    **Uso:**
    - Debugging de problemas
    - Monitoring detalhado
    - Dashboards de observabilidade
    """,
    responses={
        200: {"description": "Status detalhado do sistema"}
    }
)
async def detailed_health_check():
    """
    Health check detalhado com informações completas do sistema.
    
    Inclui métricas, dependências e configurações para debugging.
    """
    start_time = time.time()
    
    try:
        # Executar todos os checks em paralelo para performance
        config_task = _check_configuration()
        zep_task = _check_zep_connectivity()
        cache_task = _check_cache_connectivity()
        system_task = _check_system_resources()
        database_task = _check_database_connectivity()
        
        # Aguardar todos os checks
        config_check, zep_check, cache_check, system_check, database_check = await asyncio.gather(
            config_task, zep_task, cache_task, system_task, database_task,
            return_exceptions=True
        )
        
        # Processar resultados (handle exceptions)
        checks = {}
        
        # Configuration Check
        if isinstance(config_check, Exception):
            checks["configuration"] = {
                "healthy": False,
                "error": str(config_check),
                "response_time": None
            }
        else:
            checks["configuration"] = config_check
        
        # Zep Check
        if isinstance(zep_check, Exception):
            checks["zep"] = {
                "healthy": False, 
                "error": str(zep_check),
                "response_time": None
            }
        else:
            checks["zep"] = zep_check
            
        # Cache Check
        if isinstance(cache_check, Exception):
            checks["cache"] = {
                "healthy": False,
                "error": str(cache_check), 
                "response_time": None
            }
        else:
            checks["cache"] = cache_check
            
        # System Check
        if isinstance(system_check, Exception):
            checks["system"] = {
                "healthy": False,
                "error": str(system_check),
                "response_time": None
            }
        else:
            checks["system"] = system_check
            
        # Database Check
        if isinstance(database_check, Exception):
            checks["database"] = {
                "healthy": False,
                "error": str(database_check),
                "response_time": None
            }
        else:
            checks["database"] = database_check
        
        # Calcular status geral baseado em serviços críticos
        critical_services = ["configuration", "zep"]
        optional_services = ["cache", "database"]
        system_services = ["system"]
        
        # Críticos devem estar 100% saudáveis
        critical_healthy = all(
            checks.get(service, {}).get("healthy", False) 
            for service in critical_services
        )
        
        # Sistema deve estar em níveis aceitáveis  
        system_healthy = checks.get("system", {}).get("healthy", True)
        
        # Opcionais podem estar degradados sem afetar status geral
        optional_issues = [
            service for service in optional_services
            if not checks.get(service, {}).get("healthy", True)
        ]
        
        # Status geral
        if critical_healthy and system_healthy:
            if optional_issues:
                overall_status = "degraded"
            else:
                overall_status = "healthy"
        else:
            overall_status = "unhealthy"
        
        total_time = time.time() - start_time
        
        # Obter métricas adicionais
        try:
            metrics = get_metrics()
            uptime_seconds = time.time() - metrics._start_time
        except Exception:
            uptime_seconds = 0
        
        return {
            "status": overall_status,
            "timestamp": time.time(),
            "version": settings.api_version,
            "service": "zep-ai-memory-api",
            "environment": {
                "debug": settings.debug,
                "log_level": settings.log_level,
                "prometheus_enabled": settings.prometheus_enabled,
                "cache_enabled": settings.cache_enabled,
                "auth_enabled": settings.auth_enabled,
                "rate_limit_enabled": settings.rate_limit_enabled
            },
            "checks": checks,
            "overall_healthy": overall_status in ["healthy", "degraded"],
            "critical_services_healthy": critical_healthy,
            "system_healthy": system_healthy,
            "optional_issues": optional_issues,
            "response_time_ms": round(total_time * 1000, 2),
            "uptime_seconds": round(uptime_seconds, 2),
        }
        
    except Exception as e:
        logger.error("detailed_health_check_failed", error=str(e), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "timestamp": time.time(),
                "error": str(e),
                "healthy": False
            }
        )


async def _check_configuration() -> Dict[str, Any]:
    """Verifica se as configurações essenciais estão presentes."""
    check_start = time.time()
    
    try:
        # Verificar configurações críticas
        missing_configs = []
        
        if not settings.zep_api_key:
            missing_configs.append("ZEP_API_KEY")
        
        if not settings.zep_api_url:
            missing_configs.append("ZEP_API_URL")
            
        if not settings.api_secret_key or len(settings.api_secret_key) < 32:
            missing_configs.append("API_SECRET_KEY (must be 32+ chars)")
        
        healthy = len(missing_configs) == 0
        
        response_time = time.time() - check_start
        
        result = {
            "healthy": healthy,
            "response_time": round(response_time * 1000, 2),
            "details": {
                "missing_configs": missing_configs if missing_configs else None,
                "zep_url_configured": bool(settings.zep_api_url),
                "api_key_configured": bool(settings.zep_api_key),
                "secret_key_length": len(settings.api_secret_key) if settings.api_secret_key else 0
            }
        }
        
        if not healthy:
            result["error"] = f"Missing required configurations: {', '.join(missing_configs)}"
        
        return result
        
    except Exception as e:
        return {
            "healthy": False,
            "response_time": round((time.time() - check_start) * 1000, 2),
            "error": str(e),
            "details": None
        }


async def _check_zep_connectivity() -> Dict[str, Any]:
    """Verifica conectividade com o Zep com timeout e retry."""
    check_start = time.time()
    
    try:
        # Usar timeout específico para health check
        async with asyncio.timeout(settings.health_check_timeout):
            zep_client = await get_zep_client_sync()
            
            # Realizar um health check real fazendo uma operação leve
            try:
                # Tentar listar usuários (operação leve) para verificar conectividade real
                await asyncio.wait_for(
                    zep_client.client.user.list(limit=1),
                    timeout=5.0
                )
                zep_operational = True
                zep_error = None
            except Exception as e:
                # Cliente inicializado mas Zep pode estar down
                zep_operational = False
                zep_error = str(e)
            
            response_time = time.time() - check_start
            
            return {
                "healthy": zep_operational,
                "response_time": round(response_time * 1000, 2),
                "details": {
                    "zep_url": settings.zep_api_url,
                    "client_initialized": zep_client is not None,
                    "timeout_configured": settings.zep_timeout,
                    "operational": zep_operational,
                    "error": zep_error
                }
            }
        
    except asyncio.TimeoutError:
        return {
            "healthy": False,
            "response_time": round((time.time() - check_start) * 1000, 2),
            "error": "Health check timeout",
            "details": {
                "zep_url": settings.zep_api_url,
                "timeout": settings.health_check_timeout,
                "error_type": "TimeoutError"
            }
        }
    except Exception as e:
        return {
            "healthy": False,
            "response_time": round((time.time() - check_start) * 1000, 2),
            "error": str(e),
            "details": {
                "zep_url": settings.zep_api_url,
                "error_type": type(e).__name__
            }
        }


async def _check_cache_connectivity() -> Dict[str, Any]:
    """Verifica conectividade com o cache (Redis) com operações reais."""
    check_start = time.time()
    
    try:
        if not settings.cache_enabled:
            return {
                "healthy": True,
                "response_time": 0,
                "details": {
                    "status": "disabled",
                    "cache_enabled": False
                }
            }
        
        # Realizar operações reais no Redis
        cache = await get_cache_instance()
        
        # Teste de conectividade básica
        await cache.redis.ping()
        
        # Teste de operações read/write
        test_key = "health_check_test"
        test_value = f"test_{int(time.time())}"
        
        # Write test
        await cache.set("health", test_key, value=test_value, ttl=60)
        
        # Read test
        cached_value = await cache.get("health", test_key)
        
        # Cleanup
        await cache.delete("health", test_key)
        
        # Verificar se operações funcionaram
        operations_working = cached_value == test_value
        
        # Obter estatísticas do cache
        cache_stats = await cache.get_cache_stats()
        
        response_time = time.time() - check_start
        
        return {
            "healthy": operations_working,
            "response_time": round(response_time * 1000, 2),
            "details": {
                "redis_url": settings.redis_url.split('@')[-1],  # Remove credenciais
                "cache_enabled": settings.cache_enabled,
                "cache_ttl": settings.cache_ttl,
                "operations_working": operations_working,
                "stats": {
                    "hit_ratio": cache_stats.get("hit_ratio", 0),
                    "active_keys": cache_stats.get("active_keys", 0),
                    "total_requests": cache_stats.get("total_requests", 0)
                }
            }
        }
        
    except CacheError as e:
        return {
            "healthy": False,
            "response_time": round((time.time() - check_start) * 1000, 2),
            "error": f"Cache error: {str(e)}",
            "details": {
                "redis_url": settings.redis_url.split('@')[-1],
                "cache_enabled": settings.cache_enabled,
                "error_type": "CacheError"
            }
        }
    except Exception as e:
        return {
            "healthy": False,
            "response_time": round((time.time() - check_start) * 1000, 2),
            "error": str(e),
            "details": {
                "redis_url": settings.redis_url.split('@')[-1],
                "cache_enabled": settings.cache_enabled,
                "error_type": type(e).__name__
            }
        }


async def _check_system_resources() -> Dict[str, Any]:
    """Verifica recursos do sistema (CPU, memória, disco)."""
    check_start = time.time()
    
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memória
        memory = psutil.virtual_memory()
        
        # Disco
        disk = psutil.disk_usage('/')
        
        # Processo atual
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Verificar se recursos estão em níveis saudáveis
        cpu_healthy = cpu_percent < 80.0
        memory_healthy = memory.percent < 85.0
        disk_healthy = (disk.used / disk.total) * 100 < 90.0
        
        overall_healthy = cpu_healthy and memory_healthy and disk_healthy
        
        response_time = time.time() - check_start
        
        return {
            "healthy": overall_healthy,
            "response_time": round(response_time * 1000, 2),
            "details": {
                "cpu": {
                    "percent": cpu_percent,
                    "healthy": cpu_healthy,
                    "threshold": 80.0
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent": memory.percent,
                    "healthy": memory_healthy,
                    "threshold": 85.0
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": round((disk.used / disk.total) * 100, 2),
                    "healthy": disk_healthy,
                    "threshold": 90.0
                },
                "process": {
                    "memory_mb": round(process_memory.rss / (1024**2), 2),
                    "memory_percent": round(process.memory_percent(), 2)
                }
            }
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "response_time": round((time.time() - check_start) * 1000, 2),
            "error": str(e),
            "details": {
                "error_type": type(e).__name__
            }
        }


async def _check_database_connectivity() -> Dict[str, Any]:
    """Verifica conectividade com banco de dados (se configurado)."""
    check_start = time.time()
    
    try:
        # Se não há database_url configurada, considerar saudável
        if not hasattr(settings, 'database_url') or not settings.database_url:
            return {
                "healthy": True,
                "response_time": 0,
                "details": {
                    "status": "not_configured",
                    "message": "No database configured"
                }
            }
        
        # TODO: Implementar verificação real do banco quando necessário
        response_time = time.time() - check_start
        
        return {
            "healthy": True,
            "response_time": round(response_time * 1000, 2),
            "details": {
                "status": "simulated",
                "message": "Database check not implemented yet"
            }
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "response_time": round((time.time() - check_start) * 1000, 2),
            "error": str(e),
            "details": {
                "error_type": type(e).__name__
            }
        }


@router.get(
    "/metrics-summary",
    summary="Resumo de Métricas",
    description="""
    Resumo das métricas principais do sistema com dados reais.
    
    **Métricas incluídas:**
    - Performance da API
    - Recursos do sistema
    - Status das operações Zep
    - Cache e conectividade
    
    **Nota:** Para métricas completas, use `/metrics` (Prometheus format)
    """,
    responses={
        200: {"description": "Resumo das métricas"}
    }
)
async def metrics_summary():
    """Resumo das métricas principais em formato JSON com dados reais."""
    try:
        metrics = get_metrics()
        
        # Atualizar métricas do sistema
        await metrics.update_system_metrics()
        
        # Obter estatísticas do cache se disponível
        cache_stats = {}
        if settings.cache_enabled:
            try:
                cache = await get_cache_instance()
                cache_stats = await cache.get_cache_stats()
            except Exception:
                cache_stats = {"error": "Cache unavailable"}
        
        # Coleta de métricas básicas do sistema
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        process = psutil.Process()
        
        return {
            "timestamp": time.time(),
            "metrics": {
                "api": {
                    "status": "operational",
                    "version": settings.api_version,
                    "debug": settings.debug
                },
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_total_gb": round(memory.total / (1024**3), 2),
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "process_memory_mb": round(process.memory_info().rss / (1024**2), 2),
                    "uptime_seconds": round(time.time() - metrics._start_time, 2)
                },
                "cache": cache_stats,
                "services": {
                    "zep_configured": bool(settings.zep_api_url and settings.zep_api_key),
                    "cache_enabled": settings.cache_enabled,
                    "auth_enabled": settings.auth_enabled,
                    "rate_limit_enabled": settings.rate_limit_enabled,
                    "prometheus_enabled": settings.prometheus_enabled
                }
            }
        }
        
    except Exception as e:
        logger.error("metrics_summary_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to collect metrics: {str(e)}"
        )


@router.get(
    "/circuit-breaker",
    summary="Status do Circuit Breaker",
    description="""
    Status dos circuit breakers para serviços externos.
    
    **Serviços monitorados:**
    - Zep API
    - Redis Cache
    - Rate Limiting
    """,
    responses={
        200: {"description": "Status dos circuit breakers"}
    }
)
async def circuit_breaker_status():
    """Status dos circuit breakers para serviços críticos."""
    try:
        # Executar health checks críticos em paralelo
        zep_task = _check_zep_connectivity()
        cache_task = _check_cache_connectivity()
        system_task = _check_system_resources()
        
        zep_check, cache_check, system_check = await asyncio.gather(
            zep_task, cache_task, system_task,
            return_exceptions=True
        )
        
        # Processar resultados
        circuit_breakers = {}
        
        # Zep Circuit Breaker
        if isinstance(zep_check, Exception):
            circuit_breakers["zep"] = {"status": "open", "error": str(zep_check)}
        else:
            circuit_breakers["zep"] = {
                "status": "closed" if zep_check["healthy"] else "open",
                "response_time": zep_check["response_time"],
                "last_check": time.time()
            }
        
        # Cache Circuit Breaker
        if isinstance(cache_check, Exception):
            circuit_breakers["cache"] = {"status": "open", "error": str(cache_check)}
        else:
            circuit_breakers["cache"] = {
                "status": "closed" if cache_check["healthy"] else "half_open",
                "response_time": cache_check["response_time"],
                "last_check": time.time()
            }
        
        # System Circuit Breaker
        if isinstance(system_check, Exception):
            circuit_breakers["system"] = {"status": "open", "error": str(system_check)}
        else:
            circuit_breakers["system"] = {
                "status": "closed" if system_check["healthy"] else "half_open",
                "response_time": system_check["response_time"],
                "last_check": time.time()
            }
        
        return {
            "timestamp": time.time(),
            "circuit_breakers": circuit_breakers,
            "overall_status": "healthy" if all(
                cb.get("status") == "closed" 
                for cb in circuit_breakers.values()
            ) else "degraded"
        }
        
    except Exception as e:
        logger.error("circuit_breaker_status_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get circuit breaker status: {str(e)}"
        ) 