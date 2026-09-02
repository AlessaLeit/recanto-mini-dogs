"""Schemas Pydantic v2 para Pacote.

Obs.: mantém compatibilidade com o restante do código já existente.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .agendamento import AgendamentoResponse


class TipoPlano(str, Enum):
    MENSAL = "mensal"
    QUINZENAL = "quinzenal"
    SEMANAL = "semanal"


class DiaSemana(str, Enum):
    TERCA = "terca"
    QUARTA = "quarta"
    QUINTA = "quinta"
    SEXTA = "sexta"
    SABADO = "sabado"


class StatusPagamento(str, Enum):
    EM_ABERTO = "em_aberto"
    PAGO = "pago"
    ATRASADO = "atrasado"


class CachorroPacoteResponse(BaseModel):
    id: int
    nome: str

    model_config = ConfigDict(from_attributes=True)


class PagamentoResponse(BaseModel):
    id: int
    pacote_id: int
    valor_pago: float
    data_pagamento: date
    tipo_pagamento: str
    observacao: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PagamentoUpdate(BaseModel):
    valor_pago: Optional[float] = Field(default=None, gt=0)
    data_pagamento: Optional[date] = None
    tipo_pagamento: Optional[str] = None
    observacao: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PacoteBase(BaseModel):
    tipo_plano: TipoPlano
    valor_cobrado: float = Field(gt=0)
    limite_banhos_mes: int = Field(ge=1)
    ativo: bool = True

    model_config = ConfigDict(from_attributes=True)


class PacoteCreate(BaseModel):
    cachorro_id: int = Field(..., gt=0, description="Cachorro principal do pacote")
    cachorros_adicionais_ids: List[int] = Field(
        default_factory=list,
        description="Outros cachorros do mesmo cliente incluídos neste pacote"
    )
    valores_adicionais: Dict[int, float] = Field(
        default_factory=dict,
        description="Valor do banho por cachorro adicional (id -> valor); se omitido para um id usa valor_banho_base"
    )
    tipo_plano: TipoPlano

    dia_da_semana: Optional[DiaSemana] = None

    valor_banho_base: float = Field(gt=0)
    valor_cobrado: float = Field(gt=0)
    valor_transporte: Optional[float] = 0.0
    limite_banhos_mes: Optional[int] = None
    ativo: bool = True


class PacoteUpdate(BaseModel):
    tipo_plano: Optional[TipoPlano] = None
    dia_da_semana: Optional[DiaSemana] = None

    valor_cobrado: Optional[float] = None
    valor_banho_base: Optional[float] = None
    valor_transporte: Optional[float] = None
    limite_banhos_mes: Optional[int] = None
    ativo: Optional[bool] = None
    cachorros_adicionais_ids: Optional[List[int]] = None
    valores_cachorros: Optional[Dict[int, float]] = Field(
        default=None,
        description="Valor do banho por cachorro adicional (id -> valor); cachorros sem entrada usam valor_banho_base"
    )

    model_config = ConfigDict(from_attributes=True)


class PacoteResponse(BaseModel):
    id: int
    cachorro_id: int
    tipo_plano: str

    # Novo: exibido no detalhe do pacote
    dia_da_semana: Optional[DiaSemana] = None

    valor_banho_base: float
    valor_cobrado: float
    valor_transporte: float = 0.0
    valores_cachorros: Dict[str, float] = Field(default_factory=dict)
    valor_banho_equivalente: float = 0.0
    valor_banho_por_cachorro: Dict[str, float] = Field(default_factory=dict)
    valor_pago: float = 0.0
    pagamentos: List[PagamentoResponse] = []
    ativo: bool
    fechado: bool = False
    criado_em: datetime

    pet_nome: Optional[str] = None
    cliente_nome: Optional[str] = None
    cliente_whatsapp: Optional[str] = None
    cliente_envio_comanda: Optional[str] = None
    cachorros: List[CachorroPacoteResponse] = Field(default_factory=list, validation_alias="cachorros_todos")
    status_pagamento: str

    limite_banhos_mes: int
    total_agendamentos: int
    agendamentos: List[AgendamentoResponse] = []

    # populate_by_name=True: o endpoint valida o pacote 2x (uma vez manualmente
    # via model_validate(orm_obj).model_dump(), depois de novo pelo response_model
    # do FastAPI sobre o dict resultante). Na 2ª passada o input já é um dict com
    # a chave 'cachorros' (não 'cachorros_todos'), e sem populate_by_name a busca
    # por alias falha silenciosamente e cai no default [].
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @field_validator("valores_cachorros", mode="before")
    @classmethod
    def _valores_cachorros_default(cls, v):
        # Coluna no banco é nullable (pacotes antigos/sem customização ficam NULL).
        return v or {}

    @model_validator(mode="after")
    def _calcular_valor_pago(self):
        # 'valor_pago' não existe como atributo no model (só 'valor_pago_total',
        # calculado a partir de 'pagamentos'), então o from_attributes nunca o
        # preenche sozinho. Recalcula aqui para refletir a soma real dos pagamentos.
        self.valor_pago = sum(p.valor_pago for p in self.pagamentos)
        return self


class PacoteWithBanhos(PacoteResponse):
    banhos: List[Any] = []  


class PacoteWithAgendamentos(PacoteResponse):
    agendamentos: List[AgendamentoResponse] = []
