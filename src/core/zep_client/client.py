"""
Zep Client Wrapper otimizado para performance e reutilização.
Implementa singleton pattern e connection pooling conforme best practices.
"""

import asyncio
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager
import structlog

from zep_python.client import AsyncZep
from zep_python.types import Message
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings


logger = structlog.get_logger(__name__)


class ZepClientError(Exception):
    """Erro customizado para operações do Zep Client."""
    pass


class OptimizedZepClient:
    """
    Cliente Zep otimizado com singleton pattern e connection pooling.
    
    Implementa as best practices do Zep:
    - Reutilização de uma única instância de cliente
    - Connection pooling para reduzir latência
    - Retry automático para operações falhosas
    - Logging estruturado para observabilidade
    """
    
    _instance: Optional["OptimizedZepClient"] = None
    _client: Optional[AsyncZep] = None
    _lock = asyncio.Lock()
    
    def __new__(cls) -> "OptimizedZepClient":
        """Implementa singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def __aenter__(self) -> "OptimizedZepClient":
        """Context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        await self.close()
    
    async def initialize(self) -> None:
        """Inicializa o cliente Zep se ainda não estiver inicializado."""
        async with self._lock:
            if self._client is None:
                try:
                    self._client = AsyncZep(
                        api_key=settings.zep_api_key,
                        base_url=settings.zep_api_url,
                        # Configurações de timeout e connection pooling
                        timeout=settings.zep_timeout,
                    )
                    logger.info(
                        "zep_client_initialized",
                        api_url=settings.zep_api_url,
                        timeout=settings.zep_timeout
                    )
                except Exception as e:
                    logger.error(
                        "zep_client_initialization_failed",
                        error=str(e),
                        api_url=settings.zep_api_url
                    )
                    raise ZepClientError(f"Failed to initialize Zep client: {e}")
    
    async def close(self) -> None:
        """Fecha o cliente Zep."""
        if self._client:
            # O AsyncZep não tem método close explícito,
            # mas podemos limpar a referência
            self._client = None
            logger.info("zep_client_closed")
    
    @property
    def client(self) -> AsyncZep:
        """Retorna o cliente Zep inicializado."""
        if self._client is None:
            raise ZepClientError("Zep client not initialized. Call initialize() first.")
        return self._client
    
    # Memory Operations (Alto Nível)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def add_memory(
        self,
        session_id: str,
        messages: List[Message],
        return_context: bool = False
    ) -> Dict[str, Any]:
        """
        Adiciona mensagens à memória de uma sessão.
        
        Args:
            session_id: ID da sessão
            messages: Lista de mensagens para adicionar
            return_context: Se deve retornar o contexto imediatamente (otimização)
            
        Returns:
            Resposta da API do Zep
            
        Raises:
            ZepClientError: Se houver erro na operação
        """
        try:
            logger.info(
                "memory_add_started",
                session_id=session_id,
                message_count=len(messages),
                return_context=return_context
            )
            
            response = await self.client.memory.add(
                session_id=session_id,
                messages=messages,
                return_context=return_context
            )
            
            logger.info(
                "memory_add_completed",
                session_id=session_id,
                message_count=len(messages),
                has_context=bool(response.context if return_context else False)
            )
            
            return {
                "session_id": session_id,
                "messages_added": len(messages),
                "context": response.context if return_context else None,
                "success": True
            }
            
        except Exception as e:
            logger.error(
                "memory_add_failed",
                session_id=session_id,
                error=str(e),
                message_count=len(messages)
            )
            raise ZepClientError(f"Failed to add memory: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_memory(
        self,
        session_id: str,
        last_n: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Recupera a memória de uma sessão.
        
        Args:
            session_id: ID da sessão
            last_n: Número de mensagens recentes para incluir
            
        Returns:
            Memória da sessão com contexto, mensagens e fatos relevantes
            
        Raises:
            ZepClientError: Se houver erro na operação
        """
        try:
            logger.info(
                "memory_get_started",
                session_id=session_id,
                last_n=last_n
            )
            
            memory = await self.client.memory.get(
                session_id=session_id,
                last_n=last_n
            )
            
            logger.info(
                "memory_get_completed",
                session_id=session_id,
                has_context=bool(memory.context),
                message_count=len(memory.messages) if memory.messages else 0,
                facts_count=len(memory.relevant_facts) if memory.relevant_facts else 0
            )
            
            return {
                "session_id": session_id,
                "context": memory.context,
                "messages": memory.messages,
                "relevant_facts": memory.relevant_facts,
                "success": True
            }
            
        except Exception as e:
            logger.error(
                "memory_get_failed",
                session_id=session_id,
                error=str(e)
            )
            raise ZepClientError(f"Failed to get memory: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def search_memory(
        self,
        user_id: str,
        query: str,
        search_scope: str = "facts",
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Busca na memória do usuário.
        
        Args:
            user_id: ID do usuário
            query: Query de busca
            search_scope: Escopo da busca ("facts", "messages", etc.)
            limit: Limite de resultados
            
        Returns:
            Resultados da busca
            
        Raises:
            ZepClientError: Se houver erro na operação
        """
        try:
            logger.info(
                "memory_search_started",
                user_id=user_id,
                query=query,
                search_scope=search_scope,
                limit=limit
            )
            
            # Use dictionary payload for compatibility
            search_payload = {
                "user_id": user_id,
                "search_scope": search_scope,
                "text": query,
                "limit": limit
            }
            
            results = await self.client.memory.search_sessions(**search_payload)
            
            logger.info(
                "memory_search_completed",
                user_id=user_id,
                query=query,
                results_count=len(results.results) if results.results else 0
            )
            
            return {
                "user_id": user_id,
                "query": query,
                "results": results.results,
                "total_count": len(results.results) if results.results else 0,
                "success": True
            }
            
        except Exception as e:
            logger.error(
                "memory_search_failed",
                user_id=user_id,
                query=query,
                error=str(e)
            )
            raise ZepClientError(f"Failed to search memory: {e}")
    
    # Graph Operations (Baixo Nível)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def add_graph_data(
        self,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        data: Any = None,
        data_type: str = "json"
    ) -> Dict[str, Any]:
        """
        Adiciona dados ao knowledge graph.
        
        Args:
            user_id: ID do usuário (para graph de usuário)
            group_id: ID do grupo (para graph de grupo)
            data: Dados para adicionar
            data_type: Tipo dos dados ("json", "text", "message")
            
        Returns:
            Resposta da operação
            
        Raises:
            ZepClientError: Se houver erro na operação
        """
        try:
            if not user_id and not group_id:
                raise ZepClientError("Either user_id or group_id must be provided")
            
            target_id = user_id or group_id
            target_type = "user" if user_id else "group"
            
            logger.info(
                "graph_add_started",
                target_id=target_id,
                target_type=target_type,
                data_type=data_type
            )
            
            response = await self.client.graph.add(
                user_id=user_id,
                group_id=group_id,
                data=data,
                type=data_type
            )
            
            logger.info(
                "graph_add_completed",
                target_id=target_id,
                target_type=target_type,
                data_type=data_type
            )
            
            return {
                "target_id": target_id,
                "target_type": target_type,
                "data_type": data_type,
                "success": True
            }
            
        except Exception as e:
            logger.error(
                "graph_add_failed",
                target_id=target_id,
                target_type=target_type,
                error=str(e)
            )
            raise ZepClientError(f"Failed to add graph data: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def search_graph(
        self,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        query: str = "",
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Busca no knowledge graph.
        
        Args:
            user_id: ID do usuário (para graph de usuário)
            group_id: ID do grupo (para graph de grupo)
            query: Query de busca
            limit: Limite de resultados
            
        Returns:
            Resultados da busca no graph
            
        Raises:
            ZepClientError: Se houver erro na operação
        """
        try:
            if not user_id and not group_id:
                raise ZepClientError("Either user_id or group_id must be provided")
            
            target_id = user_id or group_id
            target_type = "user" if user_id else "group"
            
            logger.info(
                "graph_search_started",
                target_id=target_id,
                target_type=target_type,
                query=query,
                limit=limit
            )
            
            results = await self.client.graph.search(
                user_id=user_id,
                group_id=group_id,
                query=query,
                limit=limit
            )
            
            logger.info(
                "graph_search_completed",
                target_id=target_id,
                target_type=target_type,
                query=query,
                results_count=len(results) if results else 0
            )
            
            return {
                "target_id": target_id,
                "target_type": target_type,
                "query": query,
                "results": results,
                "total_count": len(results) if results else 0,
                "success": True
            }
            
        except Exception as e:
            logger.error(
                "graph_search_failed",
                target_id=target_id,
                target_type=target_type,
                query=query,
                error=str(e)
            )
            raise ZepClientError(f"Failed to search graph: {e}")
    
    # User Management
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def create_user(
        self,
        user_id: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Cria um novo usuário.
        
        Args:
            user_id: ID único do usuário
            email: Email do usuário
            first_name: Primeiro nome
            last_name: Último nome
            metadata: Metadados adicionais
            
        Returns:
            Dados do usuário criado
            
        Raises:
            ZepClientError: Se houver erro na operação
        """
        try:
            logger.info(
                "user_create_started",
                user_id=user_id,
                has_email=bool(email)
            )
            
            user = await self.client.user.add(
                user_id=user_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                metadata=metadata or {}
            )
            
            logger.info(
                "user_create_completed",
                user_id=user_id
            )
            
            return {
                "user_id": user_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "metadata": metadata,
                "success": True
            }
            
        except Exception as e:
            logger.error(
                "user_create_failed",
                user_id=user_id,
                error=str(e)
            )
            raise ZepClientError(f"Failed to create user: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Recupera dados de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dados do usuário
            
        Raises:
            ZepClientError: Se houver erro na operação
        """
        try:
            logger.info("user_get_started", user_id=user_id)
            
            user = await self.client.user.get(user_id=user_id)
            
            logger.info("user_get_completed", user_id=user_id)
            
            return {
                "user_id": user_id,
                "user_data": user,
                "success": True
            }
            
        except Exception as e:
            logger.error(
                "user_get_failed",
                user_id=user_id,
                error=str(e)
            )
            raise ZepClientError(f"Failed to get user: {e}")


# Singleton instance global
_zep_client_instance: Optional[OptimizedZepClient] = None


@asynccontextmanager
async def get_zep_client():
    """
    Context manager para obter o cliente Zep otimizado.
    
    Usage:
        async with get_zep_client() as zep:
            result = await zep.add_memory(session_id, messages)
    """
    global _zep_client_instance
    
    if _zep_client_instance is None:
        _zep_client_instance = OptimizedZepClient()
    
    await _zep_client_instance.initialize()
    
    try:
        yield _zep_client_instance
    finally:
        # Não fechamos a conexão aqui para reutilização
        pass


async def get_zep_client_sync() -> OptimizedZepClient:
    """
    Função síncrona para obter o cliente Zep.
    Útil para dependency injection no FastAPI.
    """
    global _zep_client_instance
    
    if _zep_client_instance is None:
        _zep_client_instance = OptimizedZepClient()
        await _zep_client_instance.initialize()
    
    return _zep_client_instance 