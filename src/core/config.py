"""
Configuração centralizada da aplicação usando Pydantic Settings.
Todas as configurações de ambiente são definidas aqui.
"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação carregadas do ambiente."""
    
    # API Configuration
    api_title: str = Field(default="Zep AI Memory API", description="Nome da API")
    api_version: str = Field(default="1.0.0", description="Versão da API")
    api_description: str = Field(
        default="Enterprise-grade REST API wrapper for Zep AI Memory platform",
        description="Descrição da API"
    )
    api_secret_key: str = Field(
        description="Chave secreta para assinatura de tokens",
        min_length=32
    )
    debug: bool = Field(default=False, description="Modo debug")
    log_level: str = Field(default="INFO", description="Nível de log")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Origens permitidas para CORS"
    )
    
    # Server Configuration
    host: str = Field(default="127.0.0.1", description="Host do servidor (use 0.0.0.0 para produção)")
    port: int = Field(default=8000, description="Porta do servidor")
    workers: int = Field(default=1, description="Número de workers")
    
    # Zep Configuration
    zep_api_url: str = Field(
        default="http://localhost:8000",
        description="URL da API do Zep"
    )
    zep_api_key: str = Field(description="Chave da API do Zep")
    zep_timeout: int = Field(default=30, description="Timeout do Zep em segundos")
    zep_client_pool_size: int = Field(
        default=20,
        description="Tamanho do pool de conexões do Zep"
    )
    
    # Database Configuration (PostgreSQL)
    database_url: Optional[str] = Field(
        default=None,
        description="URL de conexão com PostgreSQL"
    )
    database_pool_size: int = Field(
        default=20,
        description="Tamanho do pool de conexões do banco"
    )
    database_max_overflow: int = Field(
        default=30,
        description="Máximo de conexões overflow"
    )
    
    # Cache Configuration (Redis)
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="URL do Redis"
    )
    redis_password: Optional[str] = Field(
        default=None,
        description="Senha do Redis"
    )
    redis_db: int = Field(default=0, description="Banco do Redis")
    cache_ttl: int = Field(default=300, description="TTL do cache em segundos")
    cache_enabled: bool = Field(default=True, description="Cache habilitado")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Rate limiting habilitado"
    )
    rate_limit_requests: int = Field(
        default=1000,
        description="Número de requests por janela"
    )
    rate_limit_window: int = Field(
        default=3600,
        description="Janela de rate limiting em segundos"
    )
    
    # Authentication
    auth_enabled: bool = Field(default=True, description="Autenticação habilitada")
    api_key_length: int = Field(default=32, description="Tamanho da API key")
    token_expire_hours: int = Field(
        default=24,
        description="Expiração do token em horas"
    )
    
    # Monitoring and Observability
    prometheus_enabled: bool = Field(
        default=True,
        description="Prometheus habilitado"
    )
    metrics_port: int = Field(default=9090, description="Porta das métricas")
    health_check_timeout: int = Field(
        default=10,
        description="Timeout do health check"
    )
    
    # Performance Optimization
    enable_gzip: bool = Field(default=True, description="GZIP habilitado")
    max_request_size: int = Field(
        default=10485760,  # 10MB
        description="Tamanho máximo do request"
    )
    connection_pool_size: int = Field(
        default=100,
        description="Tamanho do pool de conexões HTTP"
    )
    
    # Development/Testing
    testing: bool = Field(default=False, description="Modo de teste")
    test_database_url: Optional[str] = Field(
        default=None,
        description="URL do banco de teste"
    )
    
    # Google Cloud Platform (Production)
    gcp_project_id: Optional[str] = Field(
        default=None,
        description="ID do projeto GCP"
    )
    cloud_sql_connection_name: Optional[str] = Field(
        default=None,
        description="Nome da conexão Cloud SQL"
    )
    google_application_credentials: Optional[str] = Field(
        default=None,
        description="Caminho para credenciais GCP"
    )
    
    # Security Headers
    security_headers_enabled: bool = Field(
        default=True,
        description="Headers de segurança habilitados"
    )
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="Hosts permitidos"
    )
    
    # Logging
    log_format: str = Field(default="json", description="Formato do log")
    log_file: Optional[str] = Field(
        default=None,
        description="Arquivo de log"
    )
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="DSN do Sentry para error tracking"
    )
    
    # Feature Flags
    enable_analytics: bool = Field(default=True, description="Analytics habilitado")
    enable_webhooks: bool = Field(default=False, description="Webhooks habilitados")
    enable_bulk_operations: bool = Field(
        default=True,
        description="Operações em lote habilitadas"
    )
    enable_streaming: bool = Field(
        default=False,
        description="Streaming habilitado"
    )
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("allowed_hosts", pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from string or list."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @validator("log_format")
    def validate_log_format(cls, v):
        """Validate log format."""
        valid_formats = {"json", "text"}
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of {valid_formats}")
        return v.lower()
    
    class Config:
        """Configuração do Pydantic Settings."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Permite carregar de múltiplos arquivos
        env_prefix = ""
        
        # Configuração para validação
        validate_assignment = True
        
        # Schema extra para documentação
        schema_extra = {
            "example": {
                "api_title": "Zep AI Memory API",
                "api_version": "1.0.0",
                "debug": False,
                "zep_api_url": "http://localhost:8000",
                "zep_api_key": "your-zep-api-key",
                "database_url": "postgresql+asyncpg://user:pass@localhost:5432/db",
                "redis_url": "redis://localhost:6379",
                "cache_enabled": True,
                "prometheus_enabled": True
            }
        }


# Singleton instance
settings = Settings()


def get_settings() -> Settings:
    """
    Função para obter as configurações.
    Útil para dependency injection no FastAPI.
    """
    return settings


# Aliases para backward compatibility
DATABASE_URL = settings.database_url or "sqlite:///memory_test.db"
REDIS_URL = settings.redis_url
ZEP_API_URL = settings.zep_api_url
ZEP_API_KEY = settings.zep_api_key 