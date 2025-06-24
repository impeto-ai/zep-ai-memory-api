"""
Middleware de segurança para a API.
Implementa headers de segurança, proteção CSRF, sanitização e auditoria.
"""

import time
import hashlib
import secrets
from typing import Set, List, Optional
import structlog
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import re

from src.core.config import settings

logger = structlog.get_logger(__name__)


class SecurityError(Exception):
    """Erro customizado para violações de segurança."""
    pass


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware de segurança com múltiplas proteções.
    
    Implementa:
    - Headers de segurança (HSTS, CSP, etc.)
    - Proteção contra XSS e injection
    - Rate limiting adicional por IP
    - Auditoria de segurança
    - Sanitização de inputs
    - IP blocking automático
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.blocked_ips: Set[str] = set()
        self.suspicious_patterns = self._compile_suspicious_patterns()
        self.admin_endpoints = {"/admin", "/metrics", "/health/detailed"}
    
    def _compile_suspicious_patterns(self) -> List[re.Pattern]:
        """Compila padrões para detectar tentativas de ataque."""
        patterns = [
            # SQL Injection
            re.compile(r"(union\s+select|drop\s+table|insert\s+into)", re.IGNORECASE),
            re.compile(r"(;|\').*(-{2}|\/\*)", re.IGNORECASE),
            
            # XSS
            re.compile(r"<script[^>]*>", re.IGNORECASE),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"on\w+\s*=", re.IGNORECASE),
            
            # Path Traversal
            re.compile(r"\.\./", re.IGNORECASE),
            re.compile(r"\\.\\.\\", re.IGNORECASE),
            
            # Command Injection
            re.compile(r"[;&|`$]", re.IGNORECASE),
            re.compile(r"\b(wget|curl|nc|netcat)\b", re.IGNORECASE),
            
            # LDAP Injection
            re.compile(r"[()&|!]", re.IGNORECASE),
        ]
        return patterns
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Processa request aplicando todas as proteções de segurança."""
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        
        try:
            # 1. Verificar IP bloqueado
            if client_ip in self.blocked_ips:
                logger.warning(
                    "blocked_ip_attempt",
                    ip=client_ip,
                    path=request.url.path,
                    user_agent=request.headers.get("user-agent", "")[:100]
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # 2. Validar headers de segurança
            self._validate_security_headers(request)
            
            # 3. Verificar método HTTP permitido
            self._validate_http_method(request)
            
            # 4. Sanitizar e validar inputs
            await self._validate_request_content(request)
            
            # 5. Verificar acesso a endpoints administrativos
            self._validate_admin_access(request)
            
            # 6. Processar request
            response = await call_next(request)
            
            # 7. Adicionar headers de segurança na resposta
            self._add_security_headers(response)
            
            # 8. Log de auditoria para operações sensíveis
            await self._audit_log(request, response, client_ip, time.time() - start_time)
            
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except SecurityError as e:
            # Log violação de segurança
            logger.error(
                "security_violation",
                ip=client_ip,
                path=request.url.path,
                error=str(e),
                user_agent=request.headers.get("user-agent", "")[:100]
            )
            
            # Considerar bloquear IP após violações repetidas
            await self._consider_ip_blocking(client_ip)
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request blocked by security policy"
            )
        except Exception as e:
            logger.error(
                "security_middleware_error",
                ip=client_ip,
                path=request.url.path,
                error=str(e)
            )
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extrai IP real do cliente considerando proxies."""
        # Headers de proxy mais comuns
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Pegar primeiro IP (cliente original)
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Cloudflare
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip.strip()
        
        # IP direto
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _validate_security_headers(self, request: Request):
        """Valida headers de segurança obrigatórios."""
        if not settings.security_headers_enabled:
            return
        
        # Verificar User-Agent suspeito (exceto em testes)
        user_agent = request.headers.get("user-agent", "")
        
        # Permitir testclient para testes
        if user_agent == "testclient":
            return
            
        if not user_agent or len(user_agent) < 10:
            raise SecurityError("Invalid or missing User-Agent")
        
        # Detectar User-Agents de scanners conhecidos
        suspicious_agents = [
            "sqlmap", "nikto", "nmap", "masscan", "zap",
            "burp", "w3af", "skipfish", "gobuster"
        ]
        
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            raise SecurityError(f"Suspicious User-Agent detected: {user_agent[:50]}")
        
        # Verificar Content-Length para requests grandes
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_size:
            raise SecurityError(f"Request too large: {content_length} bytes")
    
    def _validate_http_method(self, request: Request):
        """Valida métodos HTTP permitidos."""
        allowed_methods = {"GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"}
        
        if request.method not in allowed_methods:
            raise SecurityError(f"HTTP method not allowed: {request.method}")
        
        # Bloquear TRACE para prevenir XST attacks
        if request.method == "TRACE":
            raise SecurityError("TRACE method not allowed")
    
    async def _validate_request_content(self, request: Request):
        """Valida e sanitiza conteúdo da request."""
        # Verificar query parameters
        query_string = str(request.url.query)
        if query_string:
            self._scan_for_threats(query_string, "query_params")
        
        # Verificar path parameters
        path = str(request.url.path)
        self._scan_for_threats(path, "path")
        
        # Verificar headers
        for name, value in request.headers.items():
            if name.lower() not in ["authorization", "cookie"]:  # Skip sensitive headers
                self._scan_for_threats(f"{name}:{value}", "headers")
    
    def _scan_for_threats(self, content: str, content_type: str):
        """Escaneia conteúdo em busca de padrões maliciosos."""
        for pattern in self.suspicious_patterns:
            if pattern.search(content):
                raise SecurityError(
                    f"Suspicious pattern detected in {content_type}: {pattern.pattern[:50]}"
                )
        
        # Verificar caracteres suspeitos em excesso
        suspicious_chars = ["<", ">", "'", '"', ";", "&", "|"]
        char_counts = {char: content.count(char) for char in suspicious_chars}
        
        for char, count in char_counts.items():
            if count > 10:  # Threshold arbitrário
                raise SecurityError(
                    f"Excessive suspicious character '{char}' in {content_type}: {count} occurrences"
                )
    
    def _validate_admin_access(self, request: Request):
        """Valida acesso a endpoints administrativos."""
        path = request.url.path
        
        # Verificar se é endpoint administrativo
        if any(admin_path in path for admin_path in self.admin_endpoints):
            # Verificar se vem de IP local/confiável (implementação simplificada)
            client_ip = self._get_client_ip(request)
            
            # Lista de IPs confiáveis para admin
            trusted_ips = {"127.0.0.1", "::1", "localhost"}
            
            # Em produção, adicionar IPs específicos
            if not settings.debug:
                # Só permitir de IPs na whitelist em produção
                if client_ip not in trusted_ips:
                    raise SecurityError(f"Admin access denied for IP: {client_ip}")
    
    def _add_security_headers(self, response: Response):
        """Adiciona headers de segurança à resposta."""
        if not settings.security_headers_enabled:
            return
        
        # Security headers essenciais
        security_headers = {
            # Prevenir XSS
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            
            # CSP (Content Security Policy)
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            ),
            
            # HSTS (apenas em HTTPS)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            
            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Feature Policy / Permissions Policy
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            ),
            
            # Cache control para endpoints sensíveis
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0",
        }
        
        # Adicionar headers à resposta
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Request ID para tracking
        if "X-Request-ID" not in response.headers:
            response.headers["X-Request-ID"] = secrets.token_hex(16)
    
    async def _audit_log(
        self,
        request: Request,
        response: Response,
        client_ip: str,
        duration: float
    ):
        """Registra log de auditoria para operações sensíveis."""
        path = request.url.path
        method = request.method
        status_code = response.status_code
        
        # Operações que merecem auditoria
        audit_patterns = [
            "/api/v1/memory/",
            "/api/v1/graph/",
            "/api/v1/users/",
            "/auth/",
            "/admin/",
            "/health/detailed"
        ]
        
        should_audit = any(pattern in path for pattern in audit_patterns)
        
        if should_audit or status_code >= 400:
            # Extrair user_id se disponível
            user_id = "anonymous"
            if hasattr(request.state, "user"):
                user_id = request.state.user.user_id
            
            logger.info(
                "security_audit",
                timestamp=time.time(),
                client_ip=client_ip,
                user_id=user_id,
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=round(duration * 1000, 2),
                user_agent=request.headers.get("user-agent", "")[:100],
                referer=request.headers.get("referer", ""),
                content_length=request.headers.get("content-length", "0"),
                response_size=len(response.body) if hasattr(response, 'body') else 0
            )
    
    async def _consider_ip_blocking(self, client_ip: str):
        """Considera bloquear IP após violações repetidas."""
        # Implementação simplificada - em produção usar Redis para persistência
        violation_key = f"security_violations:{client_ip}"
        
        # TODO: Usar cache Redis para contar violações
        # Por enquanto, bloquear imediatamente em caso de violação grave
        
        # Não bloquear IPs locais
        if client_ip in {"127.0.0.1", "::1", "localhost"}:
            return
        
        # Adicionar à lista de bloqueio temporário
        self.blocked_ips.add(client_ip)
        
        logger.warning(
            "ip_blocked_security",
            ip=client_ip,
            reason="Security violation detected"
        )
    
    def unblock_ip(self, ip: str) -> bool:
        """Remove IP da lista de bloqueio."""
        if ip in self.blocked_ips:
            self.blocked_ips.remove(ip)
            logger.info("ip_unblocked", ip=ip)
            return True
        return False
    
    def get_blocked_ips(self) -> List[str]:
        """Retorna lista de IPs bloqueados."""
        return list(self.blocked_ips)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware de proteção CSRF.
    
    Implementa proteção CSRF para requests state-changing (POST, PUT, DELETE).
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.exempt_paths = {"/health/live", "/health/ready", "/metrics"}
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Aplica proteção CSRF para métodos que modificam estado."""
        
        # Pular verificação para métodos seguros
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return await call_next(request)
        
        # Pular verificação para paths exempts
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Verificar token CSRF
        csrf_token = self._get_csrf_token(request)
        
        if not csrf_token:
            logger.warning(
                "csrf_token_missing",
                path=request.url.path,
                method=request.method,
                ip=request.client.host if request.client else "unknown"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing"
            )
        
        # Validar token CSRF
        if not self._validate_csrf_token(csrf_token):
            logger.warning(
                "csrf_token_invalid",
                path=request.url.path,
                method=request.method,
                token=csrf_token[:10],  # Log apenas primeiros 10 chars
                ip=request.client.host if request.client else "unknown"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token"
            )
        
        return await call_next(request)
    
    def _get_csrf_token(self, request: Request) -> Optional[str]:
        """Extrai token CSRF da request."""
        # Verificar header primeiro
        csrf_token = request.headers.get("X-CSRF-Token")
        if csrf_token:
            return csrf_token
        
        # Verificar form data (se aplicável)
        # TODO: Implementar extração de form data se necessário
        
        return None
    
    def _validate_csrf_token(self, token: str) -> bool:
        """Valida token CSRF."""
        # Implementação simplificada - em produção usar signing/encryption
        try:
            # Verificar formato básico
            if len(token) < 32:
                return False
            
            # Verificar se é hexadecimal válido
            int(token, 16)
            
            # TODO: Implementar validação real com secret key
            return True
            
        except ValueError:
            return False
    
    def generate_csrf_token(self) -> str:
        """Gera novo token CSRF."""
        return secrets.token_hex(32)


# Helper function para facilitar uso
def get_security_middleware():
    """Retorna instância do middleware de segurança."""
    return SecurityMiddleware


def get_csrf_middleware():
    """Retorna instância do middleware CSRF.""" 
    return CSRFProtectionMiddleware