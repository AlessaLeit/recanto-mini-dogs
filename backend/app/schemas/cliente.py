"""
Schemas Pydantic v2 para Cliente.
Inclui exemplos para documentação automática da API.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

EXAMPLE_NOME = "Maria Silva"
EXAMPLE_TELEFONE = "(11) 98765-4321"


class ClienteBase(BaseModel):
    """Schema base com campos comuns"""
    nome: str = Field(..., min_length=2, max_length=100, description="Nome completo do cliente")
    telefone: Optional[str] = Field(None, max_length=20, description="Telefone para contato")
    endereco: Optional[str] = Field(None, max_length=255, description="Endereço residencial")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": EXAMPLE_NOME,
                "telefone": EXAMPLE_TELEFONE,
                "endereco": "Rua das Flores, 123 - São Paulo/SP"
            }
        }
    )


class ClienteCreate(ClienteBase):
    """Schema para criação de novo cliente"""
    pass


class ClienteUpdate(BaseModel):
    """Schema para atualização parcial (todos os campos opcionais)"""
    nome: Optional[str] = Field(None, min_length=2, max_length=100)
    telefone: Optional[str] = Field(None, max_length=20)
    endereco: Optional[str] = Field(None, max_length=255)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "telefone": "(11) 91234-5678"
            }
        }
    )


class ClienteResponse(ClienteBase):
    """Schema de resposta com ID e timestamps"""
    id: int
    criado_em: datetime
    
    model_config = ConfigDict(
        from_attributes=True,  # Permite criar a partir de objetos ORM
        json_schema_extra={
            "example": {
                "id": 1,
                "nome": EXAMPLE_NOME,
                "telefone": EXAMPLE_TELEFONE,
                "endereco": "Rua das Flores, 123 - São Paulo/SP",
                "criado_em": "2024-01-15T10:30:00"
            }
        }
    )


# Schema para cachorro aninhado (usado no ClienteWithCachorros)
class _CachorroSimples(BaseModel):
    """Cachorro simplificado para listagem aninhada"""
    id: int
    nome: str
    raca: Optional[str] = None
    porte: str
    
    model_config = ConfigDict(from_attributes=True)


class ClienteWithCachorros(ClienteResponse):
    """Schema de resposta incluindo os cachorros do cliente"""
    cachorros: List[_CachorroSimples] = []
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "nome": EXAMPLE_NOME,
                "telefone": EXAMPLE_TELEFONE,
                "endereco": "Rua das Flores, 123",
                "criado_em": "2024-01-15T10:30:00",
                "cachorros": [
                    {
                        "id": 1,
                        "nome": "Rex",
                        "raca": "Golden Retriever",
                        "porte": "grande"
                    }
                ]
            }
        }
    )