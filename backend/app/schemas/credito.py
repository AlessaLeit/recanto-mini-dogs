"""
Schemas de crédito do cliente (pagamento adiantado / sobra de pagamento).
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Literal
from datetime import date, datetime


class CreditoCreate(BaseModel):
    """Registro de um pagamento adiantado."""
    cliente_id: int
    valor: float = Field(..., gt=0, description="Valor pago adiantado")
    data_pagamento: date = Field(default_factory=date.today)
    tipo_pagamento: Literal["pix", "dinheiro", "cartao_debito", "cartao_credito", "outro"] = "pix"
    observacao: Optional[str] = None


class CreditoResponse(BaseModel):
    id: int
    cliente_id: int
    valor: float
    valor_consumido: float = 0.0
    saldo: float = 0.0
    tipo_pagamento: Optional[str] = None
    data_pagamento: Optional[date] = None
    observacao: Optional[str] = None
    origem_pacote_id: Optional[int] = None
    criado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SaldoCreditoResponse(BaseModel):
    """Situação do crédito de um cliente."""
    cliente_id: int
    saldo: float = 0.0
    creditos: List[CreditoResponse] = []
