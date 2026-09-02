"""
Schemas Pydantic v2 para Agendamento.
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Literal, Dict, Any
from datetime import date, datetime

class AgendamentoBase(BaseModel):
    "Schema base para agendamento"
    data_banho: date = Field(..., description="Data do agendamento")
    status_presenca: Literal["pendente", "concluido", "faltou"] = Field(
        default="pendente", description="Status: pendente, concluido ou faltou"
    )
    turno: Literal["manha", "tarde"] = Field(
        default="manha", description="Turno do banho: manha ou tarde"
    )
    extras: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Extras JSON (remedio, produtos etc.)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data_banho": "2024-03-15",
                "status_presenca": "concluido",
                "turno": "manha",
                "extras": {"remedio": "antipulgas", "observacao": "comportamento agitado"}
            }
        }
    )

    @field_validator('data_banho')
    @classmethod
    def validate_data_banho(cls, v):
        "Validação: permite edição retroativa, mas avisa se futura (opcional)"
        if v > date.today():
            # Não trava, só warning no log
            pass
        return v

class AgendamentoCreate(AgendamentoBase):
    "Schema para criar agendamento (requer pacote_id)"
    pacote_id: int = Field(..., gt=0, description="ID do pacote")


class AgendamentoAvulsoCreate(BaseModel):
    "Schema para criar um banho avulso (sem pacote vinculado)"
    pet_nome_avulso: str = Field(..., min_length=1, description="Nome do cachorro")
    cliente_nome_avulso: str = Field(..., min_length=1, description="Nome do cliente")
    data_banho: date = Field(..., description="Data do banho")
    turno: Literal["manha", "tarde"] = Field(default="manha", description="Turno do banho")
    valor_avulso: float = Field(..., ge=0, description="Valor cobrado pelo banho avulso")
    observacao: Optional[str] = Field(default=None, description="Ex: Tosa higiênica (deixe em branco se for só banho)")
    pago_avulso: bool = Field(default=False, description="Se o banho avulso já foi pago")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pet_nome_avulso": "Rex",
                "cliente_nome_avulso": "Maria Silva",
                "data_banho": "2026-07-15",
                "turno": "manha",
                "valor_avulso": 60.0,
                "observacao": "Tosa higiênica"
            }
        }
    )


class AgendamentoUpdate(BaseModel):
    "Schema para edição (retroativa permitida)"
    status_presenca: Optional[Literal["pendente", "concluido", "faltou"]] = None
    turno: Optional[Literal["manha", "tarde"]] = None
    extras: Optional[Dict[str, Any]] = None
    pago_avulso: Optional[bool] = None
    presencas: Optional[Dict[str, Literal["pendente", "concluido", "faltou"]]] = Field(
        default=None,
        description="Status por cachorro (id -> status) em pacotes multi-cachorro; "
                    "define automaticamente o status_presenca do dia"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status_presenca": "faltou",
                "presencas": {"3": "concluido", "7": "faltou"},
                "extras": {"motivo": "cliente avisou"}
            }
        }
    )

class AgendamentoResponse(AgendamentoBase):
    "Schema de resposta completa"
    id: int
    pacote_id: Optional[int] = None
    pet_nome_avulso: Optional[str] = None
    cliente_nome_avulso: Optional[str] = None
    valor_avulso: Optional[float] = None
    pago_avulso: bool = False
    presencas: Dict[str, str] = Field(default_factory=dict)
    valor_banho_dia: float = 0.0
    registrado_em: datetime
    atualizado_em: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "pacote_id": 1,
                "data_banho": "2024-03-15",
                "status_presenca": "pendente",
                "extras": {},
                "registrado_em": "2024-03-01T10:00:00"
            }
        }
    )

