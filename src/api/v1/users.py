"""
Users API endpoints.
Gerenciamento de usuários no sistema Zep.
"""

import structlog
from fastapi import APIRouter, HTTPException, Depends, Path
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from src.core.config import settings
from src.core.zep_client.client import get_zep_client_sync, OptimizedZepClient

logger = structlog.get_logger(__name__)
router = APIRouter()


class UserCreateRequest(BaseModel):
    """Request para criar usuário."""
    
    email: Optional[str] = Field(default=None, description="Email do usuário")
    first_name: Optional[str] = Field(default=None, description="Primeiro nome")
    last_name: Optional[str] = Field(default=None, description="Último nome")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados adicionais")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "usuario@exemplo.com",
                "first_name": "João",
                "last_name": "Silva",
                "metadata": {"department": "engineering", "role": "developer"}
            }
        }


async def get_zep_client() -> OptimizedZepClient:
    """Dependency para obter cliente Zep."""
    return await get_zep_client_sync()


@router.post("/{user_id}", summary="Criar usuário")
async def create_user(
    user_id: str = Path(description="ID único do usuário"),
    request: UserCreateRequest = None,
    zep_client: OptimizedZepClient = Depends(get_zep_client)
):
    """Cria um novo usuário no sistema Zep."""
    try:
        result = await zep_client.create_user(
            user_id=user_id,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            metadata=request.metadata
        )
        return result
    except Exception as e:
        logger.error("create_user_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", summary="Obter usuário")
async def get_user(
    user_id: str = Path(description="ID único do usuário"),
    zep_client: OptimizedZepClient = Depends(get_zep_client)
):
    """Recupera dados de um usuário."""
    try:
        result = await zep_client.get_user(user_id=user_id)
        return result
    except Exception as e:
        logger.error("get_user_failed", user_id=user_id, error=str(e))
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="User not found")
        raise HTTPException(status_code=500, detail=str(e)) 