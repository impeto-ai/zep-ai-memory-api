"""
Modelos Pydantic para operações de memória.
Define as estruturas de dados para requests e responses da Memory API.
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class MessageCreate(BaseModel):
    """Modelo para criação de mensagens."""
    
    role: str = Field(
        description="Papel da mensagem (ex: 'user', 'assistant', 'system')",
        min_length=1,
        max_length=50
    )
    role_type: Literal["human", "ai", "system", "function", "tool"] = Field(
        description="Tipo do papel da mensagem"
    )
    content: str = Field(
        description="Conteúdo da mensagem",
        min_length=1,
        max_length=10000  # Limite do Zep para mensagens
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadados adicionais da mensagem"
    )
    
    @field_validator("content")
    @classmethod
    def validate_content_length(cls, v):
        """Valida o tamanho do conteúdo conforme best practices."""
        if len(v.encode('utf-8')) > 10000:  # 10KB limit
            raise ValueError("Message content exceeds 10KB limit")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "user",
                "role_type": "human",
                "content": "Olá, preciso de ajuda com minha conta",
                "metadata": {"source": "n8n", "priority": "high"}
            }
        }
    )


class MemoryAddRequest(BaseModel):
    """Request para adicionar memória a uma sessão."""
    
    messages: List[MessageCreate] = Field(
        description="Lista de mensagens para adicionar",
        min_items=1,
        max_items=50  # Limite razoável para batch
    )
    return_context: bool = Field(
        default=False,
        description="Se deve retornar o contexto imediatamente (otimização)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messages": [
                    {
                        "role": "user",
                        "role_type": "human",
                        "content": "Quero cancelar minha assinatura"
                    },
                    {
                        "role": "assistant", 
                        "role_type": "ai",
                        "content": "Posso ajudar com o cancelamento. Vou verificar sua conta."
                    }
                ],
                "return_context": True
            }
        }
    )


class MemorySearchRequest(BaseModel):
    """Request para busca na memória."""
    
    query: str = Field(
        description="Query de busca",
        min_length=1,
        max_length=8192  # Limite do Zep para queries
    )
    search_scope: Literal["facts", "messages", "summaries"] = Field(
        default="facts",
        description="Escopo da busca"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Limite de resultados"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "problemas de pagamento do usuário",
                "search_scope": "facts",
                "limit": 10
            }
        }
    )


class MessageResponse(BaseModel):
    """Resposta com dados de uma mensagem."""
    
    role: str
    role_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "user",
                "role_type": "human",
                "content": "Olá, preciso de ajuda",
                "metadata": {"source": "n8n"},
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class FactResponse(BaseModel):
    """Resposta com dados de um fato."""
    
    fact: str
    entity: Optional[str] = None
    valid_at: Optional[datetime] = None
    invalid_at: Optional[datetime] = None
    confidence: Optional[float] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fact": "User prefers email notifications",
                "entity": "User",
                "valid_at": "2024-01-15T10:30:00Z",
                "invalid_at": None,
                "confidence": 0.95
            }
        }
    )


class MemoryResponse(BaseModel):
    """Resposta completa da memória de uma sessão."""
    
    session_id: str
    context: Optional[str] = Field(
        description="String de contexto otimizada para prompts"
    )
    messages: List[MessageResponse] = Field(
        default_factory=list,
        description="Mensagens recentes da sessão"
    )
    relevant_facts: List[FactResponse] = Field(
        default_factory=list,
        description="Fatos relevantes para a conversa atual"
    )
    success: bool = True
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "session_123",
                "context": "FACTS and ENTITIES...",
                "messages": [],
                "relevant_facts": [],
                "success": True
            }
        }
    )


class MemoryAddResponse(BaseModel):
    """Resposta da adição de memória."""
    
    session_id: str
    messages_added: int
    context: Optional[str] = Field(
        default=None,
        description="Contexto retornado se solicitado"
    )
    success: bool = True
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "session_123",
                "messages_added": 2,
                "context": "FACTS and ENTITIES...",
                "success": True
            }
        }
    )


class SearchResult(BaseModel):
    """Resultado individual de busca."""
    
    content: str
    score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    fact: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "User mentioned payment issues",
                "score": 0.85,
                "metadata": {"session_id": "session_123"},
                "fact": "User has payment problems"
            }
        }
    )


class MemorySearchResponse(BaseModel):
    """Resposta da busca na memória."""
    
    user_id: str
    query: str
    results: List[SearchResult] = Field(default_factory=list)
    total_count: int
    success: bool = True
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user_123",
                "query": "payment issues",
                "results": [],
                "total_count": 0,
                "success": True
            }
        }
    )


class SessionCreateRequest(BaseModel):
    """Request para criar uma nova sessão."""
    
    user_id: str = Field(description="ID do usuário proprietário da sessão")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadados da sessão"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user_123",
                "metadata": {
                    "channel": "n8n",
                    "workflow_id": "workflow_456",
                    "priority": "normal"
                }
            }
        }
    )


class SessionResponse(BaseModel):
    """Resposta com dados de uma sessão."""
    
    session_id: str
    user_id: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    message_count: int = 0
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "session_123",
                "user_id": "user_123", 
                "metadata": {"channel": "n8n"},
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:35:00Z",
                "message_count": 5
            }
        }
    )


class MemoryGetRequest(BaseModel):
    """Request para obter memória de uma sessão."""
    
    last_n: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Número de mensagens recentes para incluir"
    )
    include_context: bool = Field(
        default=True,
        description="Se deve incluir string de contexto"
    )
    include_facts: bool = Field(
        default=True,
        description="Se deve incluir fatos relevantes"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "last_n": 10,
                "include_context": True,
                "include_facts": True
            }
        }
    )


class MemoryStatsResponse(BaseModel):
    """Estatísticas de memória de uma sessão."""
    
    session_id: str
    total_messages: int
    total_facts: int
    context_length: int
    last_activity: Optional[datetime] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "session_123",
                "total_messages": 25,
                "total_facts": 12,
                "context_length": 1500,
                "last_activity": "2024-01-15T10:35:00Z"
            }
        }
    )
