"""
Model Agendamento - Representa um agendamento de banho/tosa de um pacote.
Permite edição retroativa de status e extras.
"""
from sqlalchemy import Text, ForeignKey, DateTime, Date, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SQLEnum
from app.database import Base
from typing import Optional, Dict, Any
from datetime import datetime, date
import enum

class StatusPresenca(str, enum.Enum):
    """Status de presença no agendamento"""
    PENDENTE = "pendente"
    CONCLUIDO = "concluido"
    FALTOU = "faltou"

class Agendamento(Base):
    __tablename__ = "agendamentos"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Foreign Key para pacote (obrigatório, cascade delete)
    pacote_id: Mapped[int] = mapped_column(
        ForeignKey("pacotes.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Data planejada do agendamento
    data_banho: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Status de presença (editável retroativamente)
    status_presenca: Mapped[StatusPresenca] = mapped_column(
        SQLEnum(StatusPresenca, values_callable=lambda obj: [e.value for e in obj]),
        default=StatusPresenca.PENDENTE,
        nullable=False
    )
    
    # Extras como JSONB (medicamentos, produtos especiais, observações)
    extras: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        default=dict,
        nullable=True
    )
    
    # Timestamp de registro/edição
    registrado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    atualizado_em: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now()
    )
    
    # Relacionamentos
    pacote: Mapped["Pacote"] = relationship(back_populates="agendamentos")
    
    def to_dict(self) -> dict:
        """Serialização completa para JSON/API"""
        return {
            "id": self.id,
            "pacote_id": self.pacote_id,
            "data_banho": self.data_banho.isoformat() if self.data_banho else None,
            "status_presenca": self.status_presenca.value if self.status_presenca else None,
            "extras": self.extras or {},
            "registrado_em": self.registrado_em.isoformat() if self.registrado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None
        }
    
    def __repr__(self) -> str:
        return f"<Agendamento(id={self.id}, data='{self.data_banho}', status='{self.status_presenca.value}')>"

