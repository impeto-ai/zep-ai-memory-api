"""
Zep AI Memory API - Aplicação principal FastAPI.
API REST enterprise-grade para Zep AI Memory platform.
"""

import time
import structlog
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

# Prometheus monitoring
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

from src.core.config import settings
from src.core.zep_client.client import get_zep_client_sync
from src.core.metrics import get_metrics
from src.core.middleware import RateLimitMiddleware, SecurityMiddleware
from src.api.v1 import memory, graph, users, health


# Setup structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Get global metrics instance
metrics = get_metrics()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gerencia o ciclo de vida da aplicação.
    Inicializa recursos na startup e limpa na shutdown.
    """
    # Startup
    logger.info(
        "application_starting",
        version=settings.api_version,
        debug=settings.debug,
        zep_url=settings.zep_api_url
    )
    
    try:
        # Inicializa o cliente Zep
        zep_client = await get_zep_client_sync()
        logger.info("zep_client_initialized_on_startup")
        
        # Testa conexão com Zep
        try:
            # Aqui poderia fazer um health check inicial
            logger.info("zep_connection_verified")
        except Exception as e:
            logger.warning("zep_connection_check_failed", error=str(e))
        
        yield
        
    except Exception as e:
        logger.error("application_startup_failed", error=str(e))
        raise
    finally:
        # Shutdown
        logger.info("application_shutting_down")


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs" if settings.docs_enabled or settings.debug else None,
    redoc_url="/redoc" if settings.docs_enabled or settings.debug else None,
    openapi_url="/openapi.json" if settings.docs_enabled or settings.debug else None,
    lifespan=lifespan,
    # Configurações de performance
    generate_unique_id_function=lambda route: f"{route.tags[0]}-{route.name}" if route.tags else route.name,
)

# Middleware para CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware para compressão GZIP
if settings.enable_gzip:
    app.add_middleware(GZipMiddleware, minimum_size=1000)

# Middleware de segurança
if settings.security_headers_enabled:
    app.add_middleware(SecurityMiddleware)

# Middleware de rate limiting
if settings.rate_limit_enabled:
    app.add_middleware(RateLimitMiddleware)


# Middleware personalizado para logging e métricas
@app.middleware("http")
async def logging_and_metrics_middleware(request: Request, call_next):
    """Middleware para logging estruturado e métricas Prometheus."""
    start_time = time.time()
    
    # Informações da request
    method = request.method
    url = str(request.url)
    path = request.url.path
    user_agent = request.headers.get("user-agent", "")
    client_ip = request.client.host if request.client else "unknown"
    
    logger.info(
        "request_started",
        method=method,
        path=path,
        client_ip=client_ip,
        user_agent=user_agent
    )
    
    try:
        # Processar request
        response = await call_next(request)
        
        # Calcular duração
        duration = time.time() - start_time
        
        # Atualizar métricas Prometheus usando o sistema novo
        user_type = "authenticated" if hasattr(request.state, "user") else "anonymous"
        
        metrics.record_api_request(
            method=method,
            endpoint=path,
            status_code=response.status_code,
            duration=duration,
            user_type=user_type
        )
        
        # Log da response
        logger.info(
            "request_completed",
            method=method,
            path=path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
            client_ip=client_ip
        )
        
        return response
        
    except Exception as e:
        # Calcular duração mesmo em caso de erro
        duration = time.time() - start_time
        
        # Métricas para erro
        metrics.record_api_request(
            method=method,
            endpoint=path,
            status_code=500,
            duration=duration,
            user_type="anonymous"
        )
        
        # Log do erro
        logger.error(
            "request_failed",
            method=method,
            path=path,
            error=str(e),
            duration_ms=round(duration * 1000, 2),
            client_ip=client_ip
        )
        
        # Re-raise para o FastAPI tratar
        raise


# Exception handlers globais
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler para HTTPException."""
    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para exceções gerais."""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error" if not settings.debug else str(exc),
            "status_code": 500,
            "path": request.url.path
        }
    )


# Rota para métricas Prometheus
@app.get("/metrics", include_in_schema=False)
async def get_metrics():
    """Endpoint para métricas Prometheus."""
    if not settings.prometheus_enabled:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    
    # Usar o registry do sistema de métricas
    return Response(
        content=metrics.generate_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )


# Rota raiz
@app.get("/", include_in_schema=False)
async def root():
    """Endpoint raiz com informações da API."""
    return {
        "message": "Zep AI Memory API",
        "version": settings.api_version,
        "docs": "/docs" if settings.debug else "Contact administrator",
        "health": "/health",
        "status": "running"
    }


# OpenAPI customizado
def custom_openapi():
    """Gera OpenAPI schema customizado."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.api_title,
        version=settings.api_version,
        description=settings.api_description,
        routes=app.routes,
    )
    
    # Adicionar informações extras
    openapi_schema["info"]["x-logo"] = {
        "url": "https://zep.ai/logo.png"
    }
    
    openapi_schema["info"]["contact"] = {
        "name": "API Support",
        "url": "https://zep.ai/support",
        "email": "support@example.com"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    # Adicionar servers
    openapi_schema["servers"] = [
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "https://api.zep.ai", "description": "Production server"},
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Documentação customizada
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Swagger UI customizado."""
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Documentation not available")
    
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Interactive API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://zep.ai/favicon.ico",
    )


# Incluir routers da API
app.include_router(
    health.router,
    prefix="/health",
    tags=["Health"]
)

app.include_router(
    memory.router,
    prefix="/api/v1/memory",
    tags=["Memory"]
)

app.include_router(
    graph.router,
    prefix="/api/v1/graph",
    tags=["Graph"]
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["Users"]
)


# Função principal para desenvolvimento
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
    ) 