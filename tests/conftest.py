"""
Configuração global para testes pytest.
"""

import pytest
import asyncio
from typing import Generator
from unittest.mock import patch

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
    # Salvar valores originais
    original_values = {}
    for attr in dir(settings):
        if not attr.startswith('_') and hasattr(settings, attr):
            original_values[attr] = getattr(settings, attr)
    
    yield
    
    # Restaurar valores originais
    for attr, value in original_values.items():
        setattr(settings, attr, value)


@pytest.fixture
def test_settings():
    """Fixture para configurações de teste."""
    with patch.object(settings, 'debug', True), \
         patch.object(settings, 'testing', True), \
         patch.object(settings, 'cache_enabled', False), \
         patch.object(settings, 'auth_enabled', False), \
         patch.object(settings, 'rate_limit_enabled', False), \
         patch.object(settings, 'prometheus_enabled', False):
        yield settings


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