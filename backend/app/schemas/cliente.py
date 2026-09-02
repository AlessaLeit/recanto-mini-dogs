"""
Schemas Pydantic v2 para Cliente.
Inclui exemplos para documentação automática da API.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional, List
from datetime import datetime


class ClienteBase(BaseModel):
    """Schema base com campos comuns"""
    nome: str = Field(..., min_length=2, max_length=100, description="Nome completo do cliente")
    endereco: Optional[str] = Field(None, max_length=255, description="Endereço residencial")
    whatsapp: Optional[str] = Field(None, max_length=20, description="Número de WhatsApp para contato")
    envio_comanda: Literal["whatsapp", "impresso"] = Field(
        default="impresso", description="Como a comanda (pacote fechado) é entregue ao cliente"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "Maria Silva",
                "endereco": "Rua das Flores, 123 - São Paulo/SP",
                "whatsapp": "(11) 98765-4321",
                "envio_comanda": "whatsapp"
            }
        }
    )


class ClienteCreate(ClienteBase):
    """Schema para criação de novo cliente"""
    pass


class ClienteUpdate(BaseModel):
    """Schema para atualização parcial (todos os campos opcionais)"""
    nome: Optional[str] = Field(None, min_length=2, max_length=100)
    endereco: Optional[str] = Field(None, max_length=255)
    whatsapp: Optional[str] = Field(None, max_length=20)
    envio_comanda: Optional[Literal["whatsapp", "impresso"]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "whatsapp": "(11) 91234-5678"
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
                "nome": "Maria Silva",
                "endereco": "Rua das Flores, 123 - São Paulo/SP",
                "whatsapp": "(11) 98765-4321",
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
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class ClienteWithCachorros(ClienteResponse):
    """Schema de resposta incluindo os cachorros do cliente"""
    cachorros: List[_CachorroSimples] = []

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "nome": "Maria Silva",
                "endereco": "Rua das Flores, 123",
                "whatsapp": "(11) 98765-4321",
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
