"""
Schemas Pydantic v2 para Cachorro.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime


class CachorroBase(BaseModel):
    """Schema base para cachorro"""
    nome: str = Field(..., min_length=1, max_length=100, description="Nome do pet")
    raca: Optional[str] = Field(None, max_length=50, description="Raça do cachorro")
    porte: Literal["pequeno", "medio", "grande"] = Field(
        default="medio",
        description="Porte do cachorro: pequeno, medio ou grande"
    )
    observacoes: Optional[str] = Field(None, description="Observações gerais sobre o pet")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "Rex",
                "raca": "Golden Retriever",
                "porte": "grande",
                "observacoes": "Alergia a determinados shampoos"
            }
        }
    )


class CachorroCreate(CachorroBase):
    """Schema para criar cachorro (requer cliente_id)"""
    cliente_id: int = Field(..., gt=0, description="ID do dono do cachorro")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cliente_id": 1,
                "nome": "Rex",
                "raca": "Golden Retriever",
                "porte": "grande",
                "observacoes": "Muito tranquilo durante o banho"
            }
        }
    )


class CachorroUpdate(BaseModel):
    """Schema para atualização parcial"""
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    raca: Optional[str] = Field(None, max_length=50)
    porte: Optional[Literal["pequeno", "medio", "grande"]] = None
    observacoes: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "observacoes": "Atualizado: desenvolveu alergia recentemente"
            }
        }
    )


class CachorroResponse(CachorroBase):
    """Schema de resposta completo"""
    id: int
    cliente_id: int
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "cliente_id": 1,
                "nome": "Rex",
                "raca": "Golden Retriever",
                "porte": "grande",
                "observacoes": "Alergia a shampoos com perfume"
            }
        }
    )


# Schema para pacote aninhado
class _PacoteSimples(BaseModel):
    """Pacote simplificado para listagem"""
    id: int
    tipo_plano: str
    valor_cobrado: float
    ativo: bool
    status_pagamento: str
    
    model_config = ConfigDict(from_attributes=True)


class CachorroWithPacotes(CachorroResponse):
    """Schema incluindo histórico de pacotes"""
    pacotes: List[_PacoteSimples] = []
    
    model_config = ConfigDict(from_attributes=True)