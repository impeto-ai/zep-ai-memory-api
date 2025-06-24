"""
Configuração global para testes pytest.
"""

import pytest
import asyncio
import os
from typing import Generator
from unittest.mock import patch

# Set test environment variables before importing settings
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("API_SECRET_KEY", "test-secret-key-for-testing-only-32-chars")
os.environ.setdefault("ZEP_API_KEY", "test-zep-api-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("CACHE_ENABLED", "false")
os.environ.setdefault("AUTH_ENABLED", "false")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("PROMETHEUS_ENABLED", "false")
os.environ.setdefault("SECURITY_HEADERS_ENABLED", "false")
os.environ.setdefault("SECURITY_MIDDLEWARE_ENABLED", "false")

from src.core.config import settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Fixture para event loop global nos testes."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_settings():
    """Fixture para resetar configurações após cada teste."""
    # Save original field values only
    original_values = {}
    for field_name in settings.model_fields.keys():
        if hasattr(settings, field_name):
            original_values[field_name] = getattr(settings, field_name)
    
    yield
    
    # Restore original values
    for field_name, value in original_values.items():
        setattr(settings, field_name, value)


@pytest.fixture
def test_settings():
    """Fixture para configurações de teste."""
    # Store original values
    original_debug = settings.debug
    original_testing = settings.testing
    original_cache_enabled = settings.cache_enabled
    original_auth_enabled = settings.auth_enabled
    original_rate_limit_enabled = settings.rate_limit_enabled
    original_prometheus_enabled = settings.prometheus_enabled
    
    # Set test values
    settings.debug = True
    settings.testing = True
    settings.cache_enabled = False
    settings.auth_enabled = False
    settings.rate_limit_enabled = False
    settings.prometheus_enabled = False
    
    yield settings
    
    # Restore original values
    settings.debug = original_debug
    settings.testing = original_testing
    settings.cache_enabled = original_cache_enabled
    settings.auth_enabled = original_auth_enabled
    settings.rate_limit_enabled = original_rate_limit_enabled
    settings.prometheus_enabled = original_prometheus_enabled


@pytest.fixture
def mock_zep_client():
    """Fixture para mock do cliente Zep."""
    from unittest.mock import AsyncMock
    
    mock_client = AsyncMock()
    
    # Mock dos métodos principais
    mock_client.add_memory.return_value = {
        "session_id": "test_session",
        "messages_added": 1,
        "context": "Test context",
        "success": True
    }
    
    mock_client.get_memory.return_value = {
        "session_id": "test_session",
        "context": "Test context",
        "messages": [],
        "relevant_facts": [],
        "success": True
    }
    
    mock_client.search_memory.return_value = {
        "user_id": "test_user",
        "query": "test query",
        "results": [],
        "total_count": 0,
        "success": True
    }
    
    return mock_client


@pytest.fixture
def mock_cache():
    """Fixture para mock do cache Redis."""
    from unittest.mock import AsyncMock
    
    mock_cache = AsyncMock()
    
    # Mock dos métodos principais
    mock_cache.get.return_value = None  # Cache miss por padrão
    mock_cache.set.return_value = True
    mock_cache.delete.return_value = True
    mock_cache.get_cache_stats.return_value = {
        "hits": 0,
        "misses": 0,
        "total_requests": 0,
        "hit_ratio": 0.0,
        "active_keys": 0
    }
    
    return mock_cache


@pytest.fixture
def auth_headers():
    """Fixture para headers de autenticação nos testes."""
    from src.core.auth import generate_test_token
    
    token = generate_test_token("test_user")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_memory_request():
    """Fixture para request de memória de exemplo."""
    return {
        "messages": [
            {
                "role": "user",
                "role_type": "human",
                "content": "Hello, I need help with my account"
            },
            {
                "role": "assistant",
                "role_type": "ai", 
                "content": "I'd be happy to help you with your account. What specific issue are you experiencing?"
            }
        ],
        "return_context": True
    }


@pytest.fixture
def sample_search_request():
    """Fixture para request de busca de exemplo."""
    return {
        "query": "account issues",
        "search_scope": "facts",
        "limit": 10
    }


@pytest.fixture
def client():
    """Fixture para cliente HTTP de teste sem middleware de segurança."""
    from starlette.testclient import TestClient
    from unittest.mock import patch
    
    # Criar uma app sem middleware de segurança para testes
    with patch('src.core.config.settings.security_headers_enabled', False):
        from src.main import app
        return TestClient(app)