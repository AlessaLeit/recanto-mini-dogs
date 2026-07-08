"""Schemas Pydantic v2 para Pacote.

Obs.: mantém compatibilidade com o restante do código já existente.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    cachorro_id: int = Field(..., gt=0)
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
    valor_pago: float = 0.0
    pagamentos: List[PagamentoResponse] = []
    ativo: bool
    criado_em: datetime

    pet_nome: Optional[str] = None
    cliente_nome: Optional[str] = None
    status_pagamento: str

    limite_banhos_mes: int
    total_agendamentos: int
    agendamentos: List[AgendamentoResponse] = []

    model_config = ConfigDict(from_attributes=True)

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
