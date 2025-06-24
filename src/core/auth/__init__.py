"""
Módulo de autenticação para a API.
"""

from .jwt_auth import (
    create_access_token,
    verify_token,
    get_current_user,
    get_current_admin_user,
    create_api_key,
    TokenData,
    JWTError,
    RequireScopes,
    ReadAccess,
    WriteAccess,
    AdminAccess,
    generate_test_token
)

__all__ = [
    "create_access_token",
    "verify_token", 
    "get_current_user",
    "get_current_admin_user",
    "create_api_key",
    "TokenData",
    "JWTError",
    "RequireScopes",
    "ReadAccess",
    "WriteAccess", 
    "AdminAccess",
    "generate_test_token"
]