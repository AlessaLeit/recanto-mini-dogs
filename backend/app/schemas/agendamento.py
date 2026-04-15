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
    extras: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Extras JSON (remedio, produtos etc.)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data_banho": "2024-03-15",
                "status_presenca": "concluido",
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

class AgendamentoUpdate(BaseModel):
    "Schema para edição (retroativa permitida)"
    status_presenca: Optional[Literal["pendente", "concluido", "faltou"]] = None
    extras: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status_presenca": "faltou",
                "extras": {"motivo": "cliente avisou"}
            }
        }
    )

class AgendamentoResponse(AgendamentoBase):
    "Schema de resposta completa"
    id: int
    pacote_id: int
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

