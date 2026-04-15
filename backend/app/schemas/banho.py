"""
Schemas Pydantic v2 para Banho.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date


class BanhoBase(BaseModel):
    """Schema base para banho"""
    data_banho: date = Field(..., description="Data em que o banho foi realizado")
    observacao: Optional[str] = Field(
        None,
        description="Observações: medicamentos, comportamento, produtos especiais"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data_banho": "2024-01-15",
                "observacao": "Usou shampoo antipulgas. Comportamento tranquilo."
            }
        }
    )


class BanhoCreate(BanhoBase):
    """Schema para criar banho (requer pacote_id)"""
    pacote_id: int = Field(..., gt=0, description="ID do pacote")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pacote_id": 1,
                "data_banho": "2024-01-15",
                "observacao": "Banho completo com tosa higiênica"
            }
        }
    )


class BanhoUpdate(BaseModel):
    """Schema para atualização de banho"""
    data_banho: Optional[date] = None
    observacao: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "observacao": "Observação atualizada: pet estava agitado"
            }
        }
    )


class BanhoResponse(BanhoBase):
    """Schema de resposta completo"""
    id: int
    pacote_id: int
    registrado_em: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "pacote_id": 1,
                "data_banho": "2024-01-15",
                "observacao": "Usou shampoo hipoalergênico",
                "registrado_em": "2024-01-15T14:30:00"
            }
        }
    )