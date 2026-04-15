"""
Schemas Pydantic v2 para Pacote.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum

class TipoPlano(str, Enum):
    MENSAL = "mensal"
    QUINZENAL = "quinzenal"
    SEMANAL = "semanal"

class StatusPagamento(str, Enum):
    EM_ABERTO = "em_aberto"
    PAGO = "pago"
    ATRASADO = "atrasado"

class PacoteBase(BaseModel):
    tipo_plano: TipoPlano
    valor_cobrado: float = Field(gt=0)
    limite_banhos_mes: int = Field(ge=1)
    ativo: bool = True
    model_config = ConfigDict(from_attributes=True)

class PacoteCreate(BaseModel):
    cachorro_id: int = Field(..., gt=0)
    tipo_plano: TipoPlano
    valor_cobrado: float = Field(gt=0)
    limite_banhos_mes: Optional[int] = None
    ativo: bool = True

class PacoteUpdate(BaseModel):
    tipo_plano: Optional[TipoPlano] = None
    valor_cobrado: Optional[float] = None
    limite_banhos_mes: Optional[int] = None
    ativo: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True)

class PacoteResponse(BaseModel):
    id: int
    cachorro_id: int
    tipo_plano: str
    valor_cobrado: float
    valor_pago: Optional[float] = None
    data_pagamento: Optional[str] = None
    ativo: bool
    criado_em: str
    pet_nome: Optional[str] = None
    cliente_nome: Optional[str] = None
    status_pagamento: str
    limite_banhos_mes: int
    total_agendamentos: int
    agendamentos: List[Any] = []

    model_config = ConfigDict(from_attributes=True)

class PacoteWithBanhos(PacoteResponse):
    banhos: List[Any] = []

class PacoteWithAgendamentos(PacoteResponse):
    agendamentos: List[Any] = []

