"""
Sistema de rate limiting para a API.
Implementa limitação de taxa baseada em sliding window usando Redis.
"""

import time
from typing import Optional, Dict, Any
import structlog
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.core.config import settings
from src.core.cache import get_cache_instance

logger = structlog.get_logger(__name__)


class RateLimitError(Exception):
    """Erro customizado para rate limiting."""
    pass


class RateLimiter:
    """
    Rate limiter baseado em sliding window usando Redis.
    
    Implementa:
    - Sliding window para rate limiting preciso
    - Limites por usuário, IP e endpoint
    - Burst allowance para tráfego legítimo
    - Whitelist para IPs e usuários privilegiados
    """
    
    def __init__(self):
        self.cache = None
    
    async def initialize(self):
        """Inicializa o rate limiter."""
        if not settings.rate_limit_enabled or not settings.cache_enabled:
            return
        if not self.cache:
            self.cache = await get_cache_instance()
    
    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int,
        burst_multiplier: float = 1.5
    ) -> Dict[str, Any]:
        """
        Verifica se request é permitida baseada no rate limit.
        
        Args:
            key: Chave única para o rate limit (ex: user_id, ip)
            limit: Número máximo de requests permitidas
            window: Janela de tempo em segundos
            burst_multiplier: Multiplicador para permitir bursts
            
        Returns:
            Dict com informações sobre o rate limit
        """
        if not settings.rate_limit_enabled:
            return {
                "allowed": True,
                "limit": limit,
                "remaining": limit,
                "reset_time": time.time() + window
            }
        
        try:
            current_time = time.time()
            window_start = current_time - window
            
            # Chave para sliding window
            rate_key = f"rate_limit:{key}:{int(current_time // 60)}"  # Bucket por minuto
            
            # Usar pipeline para operações atômicas
            pipe = self.cache.redis.pipeline()
            
            # Remover entradas antigas
            pipe.zremrangebyscore(rate_key, 0, window_start)
            
            # Contar requests atuais
            pipe.zcard(rate_key)
            
            # Adicionar request atual
            pipe.zadd(rate_key, {str(current_time): current_time})
            
            # Definir expiração
            pipe.expire(rate_key, window)
            
            # Executar pipeline
            results = await pipe.execute()
            current_count = results[1]
            
            # Calcular limite com burst
            effective_limit = int(limit * burst_multiplier)
            
            # Verificar se excedeu limite
            if current_count > effective_limit:
                # Log da violação
                logger.warning(
                    "rate_limit_exceeded",
                    key=key,
                    current_count=current_count,
                    limit=limit,
                    effective_limit=effective_limit,
                    window=window
                )
                
                return {
                    "allowed": False,
                    "limit": limit,
                    "remaining": 0,
                    "reset_time": current_time + window,
                    "retry_after": self._calculate_retry_after(current_count, limit, window)
                }
            
            # Request permitida
            remaining = max(0, limit - current_count)
            
            logger.debug(
                "rate_limit_check",
                key=key,
                current_count=current_count,
                limit=limit,
                remaining=remaining
            )
            
            return {
                "allowed": True,
                "limit": limit,
                "remaining": remaining,
                "reset_time": current_time + window
            }
            
        except Exception as e:
            logger.error("rate_limit_check_failed", error=str(e), key=key)
            # Em caso de erro, permitir request (fail open)
            return {
                "allowed": True,
                "limit": limit,
                "remaining": limit,
                "reset_time": time.time() + window,
                "error": str(e)
            }
    
    def _calculate_retry_after(self, current_count: int, limit: int, window: int) -> int:
        """
        Calcula tempo para retry baseado na severidade da violação.
        
        Args:
            current_count: Número atual de requests
            limit: Limite configurado
            window: Janela de tempo
            
        Returns:
            Segundos para retry
        """
        excess_ratio = current_count / limit
        
        if excess_ratio <= 1.2:  # Leve excesso
            return min(60, window // 4)
        elif excess_ratio <= 2.0:  # Excesso moderado
            return min(300, window // 2)
        else:  # Excesso severo
            return min(900, window)
    
    async def is_whitelisted(self, key: str) -> bool:
        """
        Verifica se chave está na whitelist.
        
        Args:
            key: Chave para verificar
            
        Returns:
            True se está na whitelist
        """
        try:
            whitelist_key = "rate_limit:whitelist"
            is_whitelisted = await self.cache.redis.sismember(whitelist_key, key)
            
            if is_whitelisted:
                logger.debug("rate_limit_whitelisted", key=key)
            
            return bool(is_whitelisted)
            
        except Exception as e:
            logger.warning("whitelist_check_failed", error=str(e), key=key)
            return False
    
    async def add_to_whitelist(self, key: str, ttl: Optional[int] = None) -> bool:
        """
        Adiciona chave à whitelist.
        
        Args:
            key: Chave para adicionar
            ttl: TTL em segundos (None = permanente)
            
        Returns:
            True se adicionado com sucesso
        """
        try:
            whitelist_key = "rate_limit:whitelist"
            await self.cache.redis.sadd(whitelist_key, key)
            
            if ttl:
                await self.cache.redis.expire(whitelist_key, ttl)
            
            logger.info("rate_limit_whitelist_added", key=key, ttl=ttl)
            return True
            
        except Exception as e:
            logger.error("whitelist_add_failed", error=str(e), key=key)
            return False
    
    async def get_stats(self, key: str) -> Dict[str, Any]:
        """
        Retorna estatísticas de rate limiting para uma chave.
        
        Args:
            key: Chave para obter estatísticas
            
        Returns:
            Dict com estatísticas
        """
        try:
            current_time = time.time()
            rate_key = f"rate_limit:{key}:{int(current_time // 60)}"
            
            # Contar requests na janela atual
            window_start = current_time - settings.rate_limit_window
            current_count = await self.cache.redis.zcount(
                rate_key, window_start, current_time
            )
            
            # Obter timestamps das últimas requests
            recent_requests = await self.cache.redis.zrevrange(
                rate_key, 0, 9, withscores=True
            )
            
            return {
                "key": key,
                "current_count": current_count,
                "limit": settings.rate_limit_requests,
                "window_seconds": settings.rate_limit_window,
                "is_whitelisted": await self.is_whitelisted(key),
                "recent_requests": [
                    {
                        "timestamp": score,
                        "time_ago": current_time - score
                    }
                    for _, score in recent_requests
                ]
            }
            
        except Exception as e:
            logger.error("rate_limit_stats_failed", error=str(e), key=key)
            return {"error": str(e)}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting para FastAPI.
    
    Aplica rate limiting baseado em:
    - IP do cliente
    - User ID (se autenticado)
    - Endpoint específico
    """
    
    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Processa request aplicando rate limiting."""
        
        # Inicializar rate limiter se necessário
        if not self.rate_limiter.cache:
            await self.rate_limiter.initialize()
        
        # Pular rate limiting para health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Obter identificadores para rate limiting
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)
        endpoint = self._get_endpoint_key(request)
        
        # Verificar rate limits em ordem de prioridade
        rate_limit_checks = [
            ("ip", client_ip, settings.rate_limit_requests, settings.rate_limit_window),
        ]
        
        if user_id:
            rate_limit_checks.append(
                ("user", user_id, settings.rate_limit_requests * 2, settings.rate_limit_window)
            )
        
        # Aplicar rate limiting mais restritivo para endpoints sensíveis
        if self._is_sensitive_endpoint(request):
            rate_limit_checks.append(
                ("endpoint", f"{client_ip}:{endpoint}", settings.rate_limit_requests // 2, settings.rate_limit_window)
            )
        
        # Verificar todos os rate limits
        for check_type, key, limit, window in rate_limit_checks:
            # Verificar whitelist
            if await self.rate_limiter.is_whitelisted(key):
                continue
            
            # Verificar rate limit
            result = await self.rate_limiter.is_allowed(key, limit, window)
            
            if not result["allowed"]:
                logger.warning(
                    "rate_limit_blocked",
                    check_type=check_type,
                    key=key,
                    limit=limit,
                    path=request.url.path,
                    user_agent=request.headers.get("user-agent", "")[:100]
                )
                
                # Retornar erro HTTP 429
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "limit": result["limit"],
                        "remaining": result["remaining"],
                        "reset_time": result["reset_time"],
                        "retry_after": result.get("retry_after", 60)
                    },
                    headers={
                        "X-RateLimit-Limit": str(result["limit"]),
                        "X-RateLimit-Remaining": str(result["remaining"]),
                        "X-RateLimit-Reset": str(int(result["reset_time"])),
                        "Retry-After": str(result.get("retry_after", 60))
                    }
                )
        
        # Processar request normalmente
        response = await call_next(request)
        
        # Adicionar headers de rate limit na resposta
        if rate_limit_checks:
            check_type, key, limit, window = rate_limit_checks[0]  # Usar primeiro check
            result = await self.rate_limiter.is_allowed(key, limit, window)
            
            response.headers["X-RateLimit-Limit"] = str(result["limit"])
            response.headers["X-RateLimit-Remaining"] = str(result["remaining"])
            response.headers["X-RateLimit-Reset"] = str(int(result["reset_time"]))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extrai IP do cliente considerando proxies."""
        # Verificar headers de proxy
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # IP direto
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extrai user ID do token JWT se disponível."""
        try:
            # Verificar se há token no header Authorization
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            # Extrair user_id do estado da request se já processado
            if hasattr(request.state, "user"):
                return request.state.user.user_id
            
            return None
            
        except Exception:
            return None
    
    def _get_endpoint_key(self, request: Request) -> str:
        """Gera chave única para o endpoint."""
        method = request.method
        path = request.url.path
        
        # Normalizar paths com parâmetros
        normalized_path = path
        if "/sessions/" in path:
            normalized_path = path.split("/sessions/")[0] + "/sessions/{id}"
        if "/users/" in path:
            normalized_path = path.split("/users/")[0] + "/users/{id}"
        
        return f"{method}:{normalized_path}"
    
    def _is_sensitive_endpoint(self, request: Request) -> bool:
        """Verifica se endpoint é sensível e precisa de rate limiting mais restritivo."""
        sensitive_patterns = [
            "/api/v1/memory/",
            "/api/v1/graph/",
            "/auth/",
            "/admin/"
        ]
        
        path = request.url.path
        return any(pattern in path for pattern in sensitive_patterns)


# Singleton instance global
_rate_limiter_instance: Optional[RateLimiter] = None


async def get_rate_limiter() -> RateLimiter:
    """
    Retorna instância singleton do rate limiter.
    Útil para dependency injection.
    """
    global _rate_limiter_instance
    
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter()
        await _rate_limiter_instance.initialize()
    
    return _rate_limiter_instance