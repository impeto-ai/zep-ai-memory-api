"""
Testes para sistema de autenticação JWT.
"""

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException

from src.core.auth.jwt_auth import (
    create_access_token,
    verify_token,
    TokenData,
    JWTError,
    generate_test_token
)
from src.core.config import settings


class TestJWTAuth:
    """Testes para autenticação JWT."""
    
    def test_create_access_token_success(self):
        """Testa criação de token JWT bem-sucedida."""
        user_id = "test_user_123"
        scopes = ["read", "write"]
        
        token = create_access_token(user_id=user_id, scopes=scopes)
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT deve ser relativamente longo
        assert "." in token  # JWT deve ter pontos separadores
    
    def test_create_access_token_with_custom_expiry(self):
        """Testa criação de token com expiração customizada."""
        user_id = "test_user_123"
        expires_delta = timedelta(minutes=30)
        
        token = create_access_token(
            user_id=user_id,
            expires_delta=expires_delta
        )
        
        # Verificar se token foi criado
        assert isinstance(token, str)
        
        # Verificar se token pode ser decodificado
        token_data = verify_token(token)
        assert token_data.user_id == user_id
    
    def test_verify_token_success(self):
        """Testa verificação de token válido."""
        user_id = "test_user_456"
        scopes = ["admin"]
        
        # Criar token
        token = create_access_token(user_id=user_id, scopes=scopes)
        
        # Verificar token
        token_data = verify_token(token)
        
        assert isinstance(token_data, TokenData)
        assert token_data.user_id == user_id
        assert token_data.scopes == scopes
        assert isinstance(token_data.exp, datetime)
    
    def test_verify_invalid_token(self):
        """Testa verificação de token inválido."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(JWTError, match="Invalid token"):
            verify_token(invalid_token)
    
    def test_verify_expired_token(self):
        """Testa verificação de token expirado."""
        user_id = "test_user_789"
        
        # Criar token com expiração no passado
        expired_token = create_access_token(
            user_id=user_id,
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(JWTError, match="Token has expired"):
            verify_token(expired_token)
    
    def test_generate_test_token(self):
        """Testa geração de token de teste."""
        test_token = generate_test_token("dev_user")
        
        assert isinstance(test_token, str)
        
        # Verificar se token é válido
        token_data = verify_token(test_token)
        assert token_data.user_id == "dev_user"
        assert "admin" in token_data.scopes
    
    def test_token_data_creation(self):
        """Testa criação de TokenData."""
        user_id = "test_user"
        scopes = ["read", "write"]
        exp = datetime.utcnow() + timedelta(hours=1)
        
        token_data = TokenData(user_id=user_id, scopes=scopes, exp=exp)
        
        assert token_data.user_id == user_id
        assert token_data.scopes == scopes
        assert token_data.exp == exp
    
    def test_token_without_scopes(self):
        """Testa token sem escopos."""
        user_id = "simple_user"
        
        token = create_access_token(user_id=user_id)
        token_data = verify_token(token)
        
        assert token_data.user_id == user_id
        assert token_data.scopes == []


@pytest.mark.asyncio
class TestAuthDependencies:
    """Testes para dependencies de autenticação."""
    
    @pytest.fixture
    def mock_credentials(self):
        """Mock para HTTPAuthorizationCredentials."""
        class MockCredentials:
            def __init__(self, token):
                self.credentials = token
        
        return MockCredentials
    
    async def test_get_current_user_success(self, mock_credentials):
        """Testa obtenção de usuário atual com token válido."""
        from src.core.auth.jwt_auth import get_current_user
        
        # Gerar token válido
        token = generate_test_token("test_user")
        credentials = mock_credentials(token)
        
        # Simular que auth está habilitada
        original_auth_enabled = settings.auth_enabled
        settings.auth_enabled = True
        
        try:
            token_data = await get_current_user(credentials)
            assert token_data.user_id == "test_user"
            assert "admin" in token_data.scopes
        finally:
            settings.auth_enabled = original_auth_enabled
    
    async def test_get_current_user_auth_disabled(self, mock_credentials):
        """Testa obtenção de usuário quando auth está desabilitada."""
        from src.core.auth.jwt_auth import get_current_user
        
        credentials = mock_credentials("invalid_token")
        
        # Simular que auth está desabilitada
        original_auth_enabled = settings.auth_enabled
        settings.auth_enabled = False
        
        try:
            token_data = await get_current_user(credentials)
            assert token_data.user_id == "dev_user"
            assert "admin" in token_data.scopes
        finally:
            settings.auth_enabled = original_auth_enabled
    
    async def test_get_current_user_invalid_token(self, mock_credentials):
        """Testa obtenção de usuário com token inválido."""
        from src.core.auth.jwt_auth import get_current_user
        
        credentials = mock_credentials("invalid.token.here")
        
        # Simular que auth está habilitada
        original_auth_enabled = settings.auth_enabled
        settings.auth_enabled = True
        
        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)
            
            assert exc_info.value.status_code == 401
        finally:
            settings.auth_enabled = original_auth_enabled


class TestAPIKeyGeneration:
    """Testes para geração de API keys."""
    
    def test_create_api_key_success(self):
        """Testa criação de API key bem-sucedida."""
        from src.core.auth.jwt_auth import create_api_key
        
        user_id = "api_user"
        name = "Test API Key"
        scopes = ["read", "write"]
        
        api_key_data = create_api_key(
            user_id=user_id,
            name=name,
            scopes=scopes,
            expires_days=30
        )
        
        assert isinstance(api_key_data, dict)
        assert "api_key" in api_key_data
        assert api_key_data["name"] == name
        assert api_key_data["user_id"] == user_id
        assert api_key_data["scopes"] == scopes
        assert "created_at" in api_key_data
        assert "expires_at" in api_key_data
        
        # Verificar se API key é um token JWT válido
        token_data = verify_token(api_key_data["api_key"])
        assert token_data.user_id == user_id
        assert token_data.scopes == scopes
    
    def test_create_api_key_default_scopes(self):
        """Testa criação de API key com escopos padrão."""
        from src.core.auth.jwt_auth import create_api_key
        
        api_key_data = create_api_key(
            user_id="test_user",
            name="Default Scopes Key"
        )
        
        assert api_key_data["scopes"] == ["read", "write"]


class TestRequireScopes:
    """Testes para dependency RequireScopes."""
    
    def test_require_scopes_success(self):
        """Testa verificação de escopos bem-sucedida."""
        from src.core.auth.jwt_auth import RequireScopes, TokenData
        
        # Criar dependency
        require_read = RequireScopes(["read"])
        
        # Criar usuário com escopo necessário
        user = TokenData(user_id="test_user", scopes=["read", "write"])
        
        # Deve passar sem exceção
        result = require_read(user)
        assert result == user
    
    def test_require_scopes_insufficient(self):
        """Testa verificação de escopos insuficientes."""
        from src.core.auth.jwt_auth import RequireScopes, TokenData
        
        # Criar dependency
        require_admin = RequireScopes(["admin"])
        
        # Criar usuário sem escopo necessário
        user = TokenData(user_id="test_user", scopes=["read", "write"])
        
        # Deve lançar exceção
        with pytest.raises(HTTPException) as exc_info:
            require_admin(user)
        
        assert exc_info.value.status_code == 403
        assert "admin" in str(exc_info.value.detail)
    
    def test_require_multiple_scopes(self):
        """Testa verificação de múltiplos escopos."""
        from src.core.auth.jwt_auth import RequireScopes, TokenData
        
        # Criar dependency que requer múltiplos escopos
        require_read_write = RequireScopes(["read", "write"])
        
        # Usuário com apenas um escopo
        user_partial = TokenData(user_id="user1", scopes=["read"])
        
        with pytest.raises(HTTPException):
            require_read_write(user_partial)
        
        # Usuário com todos os escopos
        user_complete = TokenData(user_id="user2", scopes=["read", "write", "admin"])
        
        result = require_read_write(user_complete)
        assert result == user_complete