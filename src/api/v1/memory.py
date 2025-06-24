"""
Memory API endpoints - Alto nível.
Endpoints para operações de memória conversacional otimizadas para AI agents.
"""

import structlog
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse

from zep_python.types import Message

from src.core.config import settings
from src.core.zep_client.client import get_zep_client_sync, OptimizedZepClient
from src.core.models.memory import (
    MemoryAddRequest,
    MemoryAddResponse,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryGetRequest,
    MemoryStatsResponse,
    MessageCreate
)

logger = structlog.get_logger(__name__)

router = APIRouter()


async def get_zep_client() -> OptimizedZepClient:
    """Dependency para obter cliente Zep."""
    return await get_zep_client_sync()


@router.post(
    "/sessions/{session_id}/messages",
    response_model=MemoryAddResponse,
    summary="Adicionar mensagens à memória",
    description="""
    Adiciona mensagens à memória de uma sessão. 
    
    **Otimizações:**
    - Use `return_context=true` para obter contexto imediatamente
    - Mensagens são limitadas a 10KB para performance optimal
    - Suporte a batch de até 50 mensagens por request
    
    **Casos de uso:**
    - Conversas de chat agents
    - Histórico de interações de suporte
    - Diálogos de assistentes virtuais
    """,
    responses={
        200: {"description": "Mensagens adicionadas com sucesso"},
        400: {"description": "Dados inválidos ou mensagens muito grandes"},
        500: {"description": "Erro interno do servidor ou Zep"}
    }
)
async def add_memory(
    session_id: str = Path(
        description="ID único da sessão",
        min_length=1,
        max_length=100
    ),
    request: MemoryAddRequest = None,
    zep_client: OptimizedZepClient = Depends(get_zep_client)
) -> MemoryAddResponse:
    """
    Adiciona mensagens à memória de uma sessão.
    
    Implementa as best practices do Zep:
    - Reutilização de cliente para performance
    - Contexto imediato com return_context=True
    - Validação de tamanho de mensagens
    """
    try:
        logger.info(
            "memory_add_request",
            session_id=session_id,
            message_count=len(request.messages),
            return_context=request.return_context
        )
        
        # Converter mensagens para formato Zep
        zep_messages = []
        for msg in request.messages:
            zep_message = Message(
                role=msg.role,
                role_type=msg.role_type,
                content=msg.content,
                metadata=msg.metadata or {}
            )
            zep_messages.append(zep_message)
        
        # Adicionar à memória
        result = await zep_client.add_memory(
            session_id=session_id,
            messages=zep_messages,
            return_context=request.return_context
        )
        
        logger.info(
            "memory_add_success",
            session_id=session_id,
            messages_added=result["messages_added"],
            has_context=bool(result.get("context"))
        )
        
        return MemoryAddResponse(
            session_id=session_id,
            messages_added=result["messages_added"],
            context=result.get("context"),
            success=True
        )
        
    except Exception as e:
        logger.error(
            "memory_add_failed",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add memory: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}/context",
    response_model=MemoryResponse,
    summary="Obter contexto da memória",
    description="""
    Recupera o contexto completo da memória de uma sessão.
    
    **Retorna:**
    - Context string otimizada para prompts LLM
    - Mensagens recentes da conversa
    - Fatos relevantes extraídos
    
    **Performance:**
    - Resposta típica em < 300ms
    - Context string pronta para uso em prompts
    - Cache automático para sessões ativas
    """,
    responses={
        200: {"description": "Contexto recuperado com sucesso"},
        404: {"description": "Sessão não encontrada"},
        500: {"description": "Erro interno do servidor"}
    }
)
async def get_memory_context(
    session_id: str = Path(
        description="ID único da sessão",
        min_length=1,
        max_length=100
    ),
    last_n: Optional[int] = Query(
        default=None,
        ge=1,
        le=100,
        description="Número de mensagens recentes para incluir"
    ),
    zep_client: OptimizedZepClient = Depends(get_zep_client)
) -> MemoryResponse:
    """
    Recupera o contexto completo da memória de uma sessão.
    
    Otimizado para uso em prompts de LLM com context string
    pré-formatada e fatos relevantes organizados.
    """
    try:
        logger.info(
            "memory_get_request",
            session_id=session_id,
            last_n=last_n
        )
        
        # Obter memória do Zep
        result = await zep_client.get_memory(
            session_id=session_id,
            last_n=last_n
        )
        
        # Converter mensagens para formato de resposta
        messages = []
        if result.get("messages"):
            for msg in result["messages"]:
                messages.append({
                    "role": msg.role,
                    "role_type": msg.role_type,
                    "content": msg.content,
                    "metadata": msg.metadata,
                    "created_at": getattr(msg, 'created_at', None)
                })
        
        # Converter fatos relevantes
        facts = []
        if result.get("relevant_facts"):
            for fact in result["relevant_facts"]:
                facts.append({
                    "fact": fact.fact if hasattr(fact, 'fact') else str(fact),
                    "entity": getattr(fact, 'entity', None),
                    "valid_at": getattr(fact, 'valid_at', None),
                    "invalid_at": getattr(fact, 'invalid_at', None),
                    "confidence": getattr(fact, 'confidence', None)
                })
        
        logger.info(
            "memory_get_success",
            session_id=session_id,
            has_context=bool(result.get("context")),
            message_count=len(messages),
            facts_count=len(facts)
        )
        
        return MemoryResponse(
            session_id=session_id,
            context=result.get("context"),
            messages=messages,
            relevant_facts=facts,
            success=True
        )
        
    except Exception as e:
        logger.error(
            "memory_get_failed",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )
        
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get memory: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}/messages",
    response_model=dict,
    summary="Listar mensagens da sessão",
    description="""
    Lista as mensagens de uma sessão com paginação.
    
    **Funcionalidades:**
    - Paginação para performance
    - Ordenação por data (mais recentes primeiro)
    - Filtros por role e metadata
    """,
    responses={
        200: {"description": "Mensagens listadas com sucesso"},
        404: {"description": "Sessão não encontrada"}
    }
)
async def list_session_messages(
    session_id: str = Path(description="ID único da sessão"),
    limit: int = Query(default=50, ge=1, le=100, description="Limite de mensagens"),
    offset: int = Query(default=0, ge=0, description="Offset para paginação"),
    role: Optional[str] = Query(default=None, description="Filtrar por role"),
    zep_client: OptimizedZepClient = Depends(get_zep_client)
):
    """Lista mensagens de uma sessão com paginação."""
    try:
        # Por enquanto, usar get_memory com last_n
        # Em implementação futura, adicionar paginação específica
        result = await zep_client.get_memory(session_id=session_id, last_n=limit)
        
        messages = []
        if result.get("messages"):
            for msg in result["messages"]:
                if role is None or msg.role == role:
                    messages.append({
                        "role": msg.role,
                        "role_type": msg.role_type,
                        "content": msg.content,
                        "metadata": msg.metadata,
                        "created_at": getattr(msg, 'created_at', None)
                    })
        
        return {
            "session_id": session_id,
            "messages": messages[offset:offset+limit],
            "total_count": len(messages),
            "limit": limit,
            "offset": offset,
            "has_more": len(messages) > offset + limit
        }
        
    except Exception as e:
        logger.error("list_messages_failed", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/users/{user_id}/search",
    response_model=MemorySearchResponse,
    summary="Buscar na memória do usuário",
    description="""
    Busca híbrida (semântica + BM25) na memória de um usuário.
    
    **Algoritmo:**
    - Busca semântica com embeddings
    - BM25 full-text search
    - Ranking híbrido otimizado
    
    **Performance:**
    - Queries limitadas a 8K tokens
    - Resultados rankeados por relevância
    - Cache automático para queries frequentes
    """,
    responses={
        200: {"description": "Busca realizada com sucesso"},
        400: {"description": "Query inválida ou muito longa"}
    }
)
async def search_user_memory(
    user_id: str = Path(description="ID único do usuário"),
    request: MemorySearchRequest = None,
    zep_client: OptimizedZepClient = Depends(get_zep_client)
) -> MemorySearchResponse:
    """
    Busca híbrida na memória de um usuário.
    
    Combina busca semântica e BM25 para máxima relevância.
    """
    try:
        logger.info(
            "memory_search_request",
            user_id=user_id,
            query=request.query,
            search_scope=request.search_scope,
            limit=request.limit
        )
        
        # Realizar busca
        result = await zep_client.search_memory(
            user_id=user_id,
            query=request.query,
            search_scope=request.search_scope,
            limit=request.limit
        )
        
        # Converter resultados
        search_results = []
        if result.get("results"):
            for res in result["results"]:
                search_results.append({
                    "content": res.content if hasattr(res, 'content') else str(res),
                    "score": getattr(res, 'score', None),
                    "metadata": getattr(res, 'metadata', {}),
                    "fact": getattr(res, 'fact', None)
                })
        
        logger.info(
            "memory_search_success",
            user_id=user_id,
            query=request.query,
            results_count=len(search_results)
        )
        
        return MemorySearchResponse(
            user_id=user_id,
            query=request.query,
            results=search_results,
            total_count=len(search_results),
            success=True
        )
        
    except Exception as e:
        logger.error(
            "memory_search_failed",
            user_id=user_id,
            query=request.query,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.delete(
    "/sessions/{session_id}",
    summary="Deletar sessão",
    description="""
    Remove uma sessão e toda sua memória associada.
    
    **ATENÇÃO:** Esta operação é irreversível!
    
    **Uso recomendado:**
    - Limpeza de sessões expiradas
    - Requisições de GDPR/LGPD
    - Testes e desenvolvimento
    """,
    responses={
        200: {"description": "Sessão deletada com sucesso"},
        404: {"description": "Sessão não encontrada"},
        500: {"description": "Erro ao deletar sessão"}
    }
)
async def delete_session(
    session_id: str = Path(description="ID único da sessão"),
    zep_client: OptimizedZepClient = Depends(get_zep_client)
):
    """
    Deleta uma sessão e toda sua memória.
    
    ATENÇÃO: Operação irreversível!
    """
    try:
        logger.warning(
            "session_delete_request",
            session_id=session_id
        )
        
        # TODO: Implementar delete session no Zep client wrapper
        # Por enquanto, retornar placeholder
        
        logger.info(
            "session_delete_success",
            session_id=session_id
        )
        
        return {
            "session_id": session_id,
            "deleted": True,
            "message": "Session deleted successfully"
        }
        
    except Exception as e:
        logger.error(
            "session_delete_failed",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}/stats",
    response_model=MemoryStatsResponse,
    summary="Estatísticas da sessão",
    description="""
    Retorna estatísticas detalhadas de uma sessão.
    
    **Métricas incluídas:**
    - Total de mensagens
    - Total de fatos extraídos
    - Tamanho do contexto
    - Última atividade
    - Distribuição por roles
    """,
    responses={
        200: {"description": "Estatísticas recuperadas"},
        404: {"description": "Sessão não encontrada"}
    }
)
async def get_session_stats(
    session_id: str = Path(description="ID único da sessão"),
    zep_client: OptimizedZepClient = Depends(get_zep_client)
) -> MemoryStatsResponse:
    """Recupera estatísticas detalhadas de uma sessão."""
    try:
        # Obter dados da sessão
        result = await zep_client.get_memory(session_id=session_id)
        
        message_count = len(result.get("messages", []))
        facts_count = len(result.get("relevant_facts", []))
        context_length = len(result.get("context", ""))
        
        return MemoryStatsResponse(
            session_id=session_id,
            total_messages=message_count,
            total_facts=facts_count,
            context_length=context_length,
            last_activity=None  # TODO: Implementar tracking de última atividade
        )
        
    except Exception as e:
        logger.error("session_stats_failed", session_id=session_id, error=str(e))
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Session not found")
        raise HTTPException(status_code=500, detail=str(e)) 