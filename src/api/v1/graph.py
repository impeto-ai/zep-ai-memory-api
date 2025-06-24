"""
Graph API endpoints - Baixo nível.
Endpoints para operações diretas no Knowledge Graph temporal do Zep.
"""

import structlog
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, Path, Query
from pydantic import BaseModel, Field

from src.core.config import settings
from src.core.zep_client.client import get_zep_client_sync, OptimizedZepClient

logger = structlog.get_logger(__name__)

router = APIRouter()


# Modelos específicos para Graph API
class GraphDataRequest(BaseModel):
    """Request para adicionar dados ao graph."""
    
    data: Any = Field(description="Dados para adicionar ao graph")
    data_type: str = Field(
        default="json",
        description="Tipo dos dados: 'json', 'text', 'message'"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "user_preference": "email_notifications",
                    "value": True,
                    "category": "notification_settings"
                },
                "data_type": "json"
            }
        }


class GraphSearchRequest(BaseModel):
    """Request para busca no graph."""
    
    query: str = Field(
        description="Query de busca no graph",
        min_length=1,
        max_length=8192
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Limite de resultados"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "query": "user preferences for notifications",
                "limit": 10
            }
        }


async def get_zep_client() -> OptimizedZepClient:
    """Dependency para obter cliente Zep."""
    return await get_zep_client_sync()


@router.post(
    "/users/{user_id}/data",
    summary="Adicionar dados ao graph do usuário",
    description="""
    Adiciona dados estruturados ao Knowledge Graph de um usuário.
    
    **Knowledge Graph Temporal:**
    - Dados são organizados como entidades e relacionamentos
    - Suporte a versionamento temporal (valid_at, invalid_at)
    - Fusão automática de dados relacionados
    - Extração automática de fatos
    
    **Tipos de dados suportados:**
    - `json`: Dados estruturados (objetos, arrays)
    - `text`: Texto livre para extração de entidades  
    - `message`: Mensagens de chat para contexto
    
    **Casos de uso:**
    - Preferências do usuário
    - Dados de perfil
    - Histórico de transações
    - Metadados de negócio
    """,
    responses={
        200: {"description": "Dados adicionados ao graph com sucesso"},
        400: {"description": "Dados inválidos ou formato não suportado"},
        500: {"description": "Erro interno do servidor"}
    }
)
async def add_user_graph_data(
    user_id: str = Path(
        description="ID único do usuário",
        min_length=1,
        max_length=100
    ),
    request: GraphDataRequest = None,
    zep_client: OptimizedZepClient = Depends(get_zep_client)
):
    """
    Adiciona dados ao Knowledge Graph de um usuário.
    
    O Zep automaticamente:
    - Extrai entidades e relacionamentos
    - Organiza dados temporalmente
    - Funde informações relacionadas
    - Atualiza fatos existentes se necessário
    """
    try:
        logger.info(
            "graph_add_user_data_request",
            user_id=user_id,
            data_type=request.data_type,
            data_size=len(str(request.data))
        )
        
        # Adicionar dados ao graph
        result = await zep_client.add_graph_data(
            user_id=user_id,
            data=request.data,
            data_type=request.data_type
        )
        
        logger.info(
            "graph_add_user_data_success",
            user_id=user_id,
            data_type=request.data_type
        )
        
        return {
            "user_id": user_id,
            "data_type": request.data_type,
            "success": True,
            "message": "Data added to user graph successfully"
        }
        
    except Exception as e:
        logger.error(
            "graph_add_user_data_failed",
            user_id=user_id,
            data_type=request.data_type,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add data to user graph: {str(e)}"
        )


@router.post(
    "/groups/{group_id}/data",
    summary="Adicionar dados ao graph do grupo",
    description="""
    Adiciona dados estruturados ao Knowledge Graph de um grupo/organização.
    
    **Grupos vs Usuários:**
    - Grupos: Dados compartilhados entre múltiplos usuários
    - Usuários: Dados pessoais e preferências individuais
    
    **Casos de uso para grupos:**
    - Configurações da organização
    - Políticas da empresa
    - Dados compartilhados de projetos
    - Knowledge base corporativo
    """,
    responses={
        200: {"description": "Dados adicionados ao graph do grupo"},
        400: {"description": "Dados inválidos"},
        500: {"description": "Erro interno"}
    }
)
async def add_group_graph_data(
    group_id: str = Path(
        description="ID único do grupo/organização",
        min_length=1,
        max_length=100
    ),
    request: GraphDataRequest = None,
    zep_client: OptimizedZepClient = Depends(get_zep_client)
):
    """Adiciona dados ao Knowledge Graph de um grupo."""
    try:
        logger.info(
            "graph_add_group_data_request",
            group_id=group_id,
            data_type=request.data_type,
            data_size=len(str(request.data))
        )
        
        # Adicionar dados ao graph
        result = await zep_client.add_graph_data(
            group_id=group_id,
            data=request.data,
            data_type=request.data_type
        )
        
        logger.info(
            "graph_add_group_data_success",
            group_id=group_id,
            data_type=request.data_type
        )
        
        return {
            "group_id": group_id,
            "data_type": request.data_type,
            "success": True,
            "message": "Data added to group graph successfully"
        }
        
    except Exception as e:
        logger.error(
            "graph_add_group_data_failed",
            group_id=group_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add data to group graph: {str(e)}"
        )


@router.post(
    "/users/{user_id}/search",
    summary="Buscar no graph do usuário",
    description="""
    Busca híbrida no Knowledge Graph de um usuário.
    
    **Algoritmo de busca:**
    - Busca semântica em entidades e relacionamentos
    - Filtros temporais (dados válidos no momento)
    - Ranking por relevância e confiança
    - Agregação de fatos relacionados
    
    **Performance:**
    - Índices otimizados para busca rápida
    - Cache automático para queries frequentes
    - Resultados rankeados por score de relevância
    
    **Casos de uso:**
    - "Quais são as preferências do usuário?"
    - "Histórico de problemas relatados"
    - "Dados de contato atualizados"
    """,
    responses={
        200: {"description": "Resultados da busca no graph"},
        400: {"description": "Query inválida"},
        500: {"description": "Erro na busca"}
    }
)
async def search_user_graph(
    user_id: str = Path(description="ID único do usuário"),
    request: GraphSearchRequest = None,
    zep_client: OptimizedZepClient = Depends(get_zep_client)
):
    """
    Busca híbrida no Knowledge Graph de um usuário.
    
    Retorna entidades, relacionamentos e fatos relevantes
    organizados por score de relevância.
    """
    try:
        logger.info(
            "graph_search_user_request",
            user_id=user_id,
            query=request.query,
            limit=request.limit
        )
        
        # Realizar busca no graph
        result = await zep_client.search_graph(
            user_id=user_id,
            query=request.query,
            limit=request.limit
        )
        
        logger.info(
            "graph_search_user_success",
            user_id=user_id,
            query=request.query,
            results_count=result.get("total_count", 0)
        )
        
        return {
            "user_id": user_id,
            "query": request.query,
            "results": result.get("results", []),
            "total_count": result.get("total_count", 0),
            "success": True
        }
        
    except Exception as e:
        logger.error(
            "graph_search_user_failed",
            user_id=user_id,
            query=request.query,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Graph search failed: {str(e)}"
        )


@router.post(
    "/groups/{group_id}/search",
    summary="Buscar no graph do grupo",
    description="""
    Busca híbrida no Knowledge Graph de um grupo/organização.
    
    **Diferenças da busca de usuário:**
    - Escopo: Dados compartilhados do grupo
    - Permissões: Dados acessíveis por membros do grupo
    - Contexto: Informações organizacionais e políticas
    
    **Casos de uso:**
    - Knowledge base da empresa
    - Políticas e procedimentos
    - Dados de projetos compartilhados
    """,
    responses={
        200: {"description": "Resultados da busca no graph do grupo"},
        404: {"description": "Grupo não encontrado"},
        500: {"description": "Erro na busca"}
    }
)
async def search_group_graph(
    group_id: str = Path(description="ID único do grupo"),
    request: GraphSearchRequest = None,
    zep_client: OptimizedZepClient = Depends(get_zep_client)
):
    """Busca híbrida no Knowledge Graph de um grupo."""
    try:
        logger.info(
            "graph_search_group_request",
            group_id=group_id,
            query=request.query,
            limit=request.limit
        )
        
        # Realizar busca no graph
        result = await zep_client.search_graph(
            group_id=group_id,
            query=request.query,
            limit=request.limit
        )
        
        logger.info(
            "graph_search_group_success",
            group_id=group_id,
            query=request.query,
            results_count=result.get("total_count", 0)
        )
        
        return {
            "group_id": group_id,
            "query": request.query,
            "results": result.get("results", []),
            "total_count": result.get("total_count", 0),
            "success": True
        }
        
    except Exception as e:
        logger.error(
            "graph_search_group_failed",
            group_id=group_id,
            query=request.query,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Group graph search failed: {str(e)}"
        )


@router.get(
    "/users/{user_id}/entities",
    summary="Listar entidades do usuário",
    description="""
    Lista todas as entidades extraídas do Knowledge Graph do usuário.
    
    **Entidades incluem:**
    - Pessoas mencionadas nas conversas
    - Produtos ou serviços discutidos
    - Localizações referenciadas
    - Organizações mencionadas
    - Conceitos importantes
    
    **Metadados por entidade:**
    - Frequência de menção
    - Primeira/última ocorrência
    - Contextos relacionados
    - Score de importância
    """,
    responses={
        200: {"description": "Lista de entidades do usuário"},
        404: {"description": "Usuário não encontrado"},
        500: {"description": "Erro ao listar entidades"}
    }
)
async def list_user_entities(
    user_id: str = Path(description="ID único do usuário"),
    limit: int = Query(default=50, ge=1, le=200, description="Limite de entidades"),
    entity_type: Optional[str] = Query(default=None, description="Filtrar por tipo de entidade"),
    zep_client: OptimizedZepClient = Depends(get_zep_client)
):
    """
    Lista entidades do Knowledge Graph do usuário.
    
    TODO: Implementar listagem específica de entidades quando
    o Zep SDK disponibilizar esta funcionalidade.
    """
    try:
        logger.info(
            "graph_list_user_entities_request",
            user_id=user_id,
            limit=limit,
            entity_type=entity_type
        )
        
        # Por enquanto, usar busca geral para simular listagem
        # Em versão futura, implementar endpoint específico
        result = await zep_client.search_graph(
            user_id=user_id,
            query="entities",  # Query genérica para entidades
            limit=limit
        )
        
        # Filtrar por tipo se especificado
        entities = result.get("results", [])
        if entity_type:
            entities = [e for e in entities if e.get("type") == entity_type]
        
        logger.info(
            "graph_list_user_entities_success",
            user_id=user_id,
            entities_count=len(entities)
        )
        
        return {
            "user_id": user_id,
            "entities": entities,
            "total_count": len(entities),
            "entity_type_filter": entity_type,
            "success": True
        }
        
    except Exception as e:
        logger.error(
            "graph_list_user_entities_failed",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list entities: {str(e)}"
        )


@router.get(
    "/users/{user_id}/facts",
    summary="Listar fatos do usuário",
    description="""
    Lista fatos extraídos automaticamente das conversas do usuário.
    
    **Tipos de fatos:**
    - Preferências pessoais
    - Informações de contato
    - Histórico de problemas
    - Relacionamentos
    - Dados demográficos
    
    **Metadados por fato:**
    - Confiança do fato (0.0 a 1.0)
    - Data de validade (valid_at, invalid_at)
    - Fonte da informação
    - Número de confirmações
    """,
    responses={
        200: {"description": "Lista de fatos do usuário"},
        404: {"description": "Usuário não encontrado"}
    }
)
async def list_user_facts(
    user_id: str = Path(description="ID único do usuário"),
    limit: int = Query(default=50, ge=1, le=200, description="Limite de fatos"),
    min_confidence: float = Query(default=0.0, ge=0.0, le=1.0, description="Confiança mínima"),
    valid_only: bool = Query(default=True, description="Apenas fatos válidos atualmente"),
    zep_client: OptimizedZepClient = Depends(get_zep_client)
):
    """
    Lista fatos do Knowledge Graph do usuário.
    
    Fatos são informações estruturadas extraídas automaticamente
    das conversas e dados fornecidos.
    """
    try:
        logger.info(
            "graph_list_user_facts_request",
            user_id=user_id,
            limit=limit,
            min_confidence=min_confidence,
            valid_only=valid_only
        )
        
        # Usar busca de memória para obter fatos relevantes
        result = await zep_client.search_memory(
            user_id=user_id,
            query="facts",  # Query específica para fatos
            search_scope="facts",
            limit=limit
        )
        
        facts = []
        if result.get("results"):
            for fact_result in result["results"]:
                # Filtrar por confiança se especificado
                confidence = fact_result.get("score", 1.0)
                if confidence >= min_confidence:
                    facts.append({
                        "fact": fact_result.get("fact") or fact_result.get("content"),
                        "confidence": confidence,
                        "metadata": fact_result.get("metadata", {}),
                        "valid": True  # TODO: Implementar check de validade temporal
                    })
        
        logger.info(
            "graph_list_user_facts_success",
            user_id=user_id,
            facts_count=len(facts)
        )
        
        return {
            "user_id": user_id,
            "facts": facts,
            "total_count": len(facts),
            "filters": {
                "min_confidence": min_confidence,
                "valid_only": valid_only
            },
            "success": True
        }
        
    except Exception as e:
        logger.error(
            "graph_list_user_facts_failed",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list facts: {str(e)}"
        ) 