"""
Sistema de autenticação JWT para a API.
Implementa geração, validação e middleware de autenticação.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from src.core.config import settings

logger = structlog.get_logger(__name__)

# Configuração do JWT
ALGORITHM = "HS256"
security = HTTPBearer()


class JWTError(Exception):
    """Erro customizado para operações JWT."""
    pass


class TokenData:
    """Dados extraídos do token JWT."""
    
    def __init__(self, user_id: str, scopes: list = None, exp: datetime = None):
        self.user_id = user_id
        self.scopes = scopes or []
        self.exp = exp


def create_access_token(
    user_id: str,
    scopes: list = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Cria um token JWT de acesso.
    
    Args:
        user_id: ID do usuário
        scopes: Lista de escopos/permissões
        expires_delta: Tempo de expiração customizado
        
    Returns:
        Token JWT assinado
        
    Raises:
        JWTError: Se houver erro na criação do token
    """
    try:
        to_encode = {"sub": user_id}
        
        if scopes:
            to_encode["scopes"] = scopes
            
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.token_expire_hours)
            
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.api_secret_key,
            algorithm=ALGORITHM
        )
        
        logger.info(
            "jwt_token_created",
            user_id=user_id,
            scopes=scopes,
            expires_at=expire
        )
        
        return encoded_jwt
        
    except Exception as e:
        logger.error("jwt_token_creation_failed", error=str(e), user_id=user_id)
        raise JWTError(f"Failed to create token: {e}")


def verify_token(token: str) -> TokenData:
    """
    Verifica e decodifica um token JWT.
    
    Args:
        token: Token JWT para verificar
        
    Returns:
        TokenData com informações do usuário
        
    Raises:
        JWTError: Se o token for inválido
    """
    try:
        payload = jwt.decode(
            token,
            settings.api_secret_key,
            algorithms=[ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise JWTError("Token missing user ID")
            
        scopes: list = payload.get("scopes", [])
        exp: datetime = datetime.fromtimestamp(payload.get("exp", 0))
        
        logger.debug(
            "jwt_token_verified",
            user_id=user_id,
            scopes=scopes,
            expires_at=exp
        )
        
        return TokenData(user_id=user_id, scopes=scopes, exp=exp)
        
    except jwt.ExpiredSignatureError:
        logger.warning("jwt_token_expired", token_prefix=token[:20])
        raise JWTError("Token has expired")
    except jwt.JWTError as e:
        logger.warning("jwt_token_invalid", error=str(e), token_prefix=token[:20])
        raise JWTError(f"Invalid token: {e}")
    except Exception as e:
        logger.error("jwt_verification_failed", error=str(e))
        raise JWTError(f"Token verification failed: {e}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> TokenData:
    """
    Dependency para obter usuário atual do token JWT.
    
    Args:
        credentials: Credenciais HTTP Bearer
        
    Returns:
        TokenData com informações do usuário autenticado
        
    Raises:
        HTTPException: Se autenticação falhar
    """
    if not settings.auth_enabled:
        # Modo desenvolvimento sem autenticação
        logger.debug("auth_disabled_dev_mode")
        return TokenData(user_id="dev_user", scopes=["admin"])
    
    try:
        token = credentials.credentials
        token_data = verify_token(token)
        
        logger.info(
            "user_authenticated",
            user_id=token_data.user_id,
            scopes=token_data.scopes
        )
        
        return token_data
        
    except JWTError as e:
        logger.warning("authentication_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Dependency para verificar se usuário tem permissões de admin.
    
    Args:
        current_user: Usuário atual autenticado
        
    Returns:
        TokenData se usuário for admin
        
    Raises:
        HTTPException: Se usuário não for admin
    """
    if "admin" not in current_user.scopes:
        logger.warning(
            "admin_access_denied",
            user_id=current_user.user_id,
            scopes=current_user.scopes
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


def create_api_key(
    user_id: str,
    name: str,
    scopes: list = None,
    expires_days: int = 365
) -> Dict[str, Any]:
    """
    Cria uma API key de longa duração.
    
    Args:
        user_id: ID do usuário
        name: Nome da API key
        scopes: Escopos/permissões
        expires_days: Dias até expiração
        
    Returns:
        Dict com API key e metadados
    """
    try:
        expires_delta = timedelta(days=expires_days)
        token = create_access_token(
            user_id=user_id,
            scopes=scopes or ["read", "write"],
            expires_delta=expires_delta
        )
        
        api_key_data = {
            "api_key": token,
            "name": name,
            "user_id": user_id,
            "scopes": scopes or ["read", "write"],
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + expires_delta
        }
        
        logger.info(
            "api_key_created",
            user_id=user_id,
            name=name,
            scopes=scopes,
            expires_days=expires_days
        )
        
        return api_key_data
        
    except Exception as e:
        logger.error("api_key_creation_failed", error=str(e), user_id=user_id)
        raise JWTError(f"Failed to create API key: {e}")


class RequireScopes:
    """
    Dependency class para verificar escopos específicos.
    
    Usage:
        @app.get("/admin")
        async def admin_endpoint(user: TokenData = Depends(RequireScopes(["admin"]))):
            pass
    """
    
    def __init__(self, required_scopes: list):
        self.required_scopes = required_scopes
    
    def __call__(self, current_user: TokenData = Depends(get_current_user)) -> TokenData:
        """Verifica se usuário tem escopos necessários."""
        missing_scopes = [
            scope for scope in self.required_scopes 
            if scope not in current_user.scopes
        ]
        
        if missing_scopes:
            logger.warning(
                "insufficient_scopes",
                user_id=current_user.user_id,
                required=self.required_scopes,
                user_scopes=current_user.scopes,
                missing=missing_scopes
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scopes: {missing_scopes}"
            )
        
        return current_user


# Dependency aliases para facilitar uso
ReadAccess = RequireScopes(["read"])
WriteAccess = RequireScopes(["write"])
AdminAccess = RequireScopes(["admin"])


def generate_test_token(user_id: str = "test_user") -> str:
    """
    Gera token de teste para desenvolvimento.
    
    Args:
        user_id: ID do usuário de teste
        
    Returns:
        Token JWT de teste
    """
    return create_access_token(
        user_id=user_id,
        scopes=["read", "write", "admin"],
        expires_delta=timedelta(days=30)
    )


# Middleware opcional para logging de autenticação
async def auth_logging_middleware(request, call_next):
    """Middleware para log de tentativas de autenticação."""
    response = await call_next(request)
    
    # Log apenas para endpoints protegidos
    if hasattr(request.state, "user"):
        logger.info(
            "authenticated_request",
            method=request.method,
            path=request.url.path,
            user_id=request.state.user.user_id
        )
    
    return response