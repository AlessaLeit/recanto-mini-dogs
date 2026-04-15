"""
Model Pacote - Representa um plano de banhos contratado.
Um pacote pode ter múltiplos banhos registrados.
"""
from sqlalchemy import String, Float, ForeignKey, Boolean, DateTime, Date, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from typing import List, Optional, Literal
from datetime import datetime, date
import enum


class TipoPlano(str, enum.Enum):
    """Tipos de plano disponíveis"""
    SEMANAL = "semanal"      # Até 4 banhos/mês
    QUINZENAL = "quinzenal"  # Até 2 banhos/mês
    MENSAL = "mensal"        # Até 1 banho/mês


class Pacote(Base):
    __tablename__ = "pacotes"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Foreign Key para cachorro (obrigatório)
    cachorro_id: Mapped[int] = mapped_column(
        ForeignKey("cachorros.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Tipo do plano contratado
    tipo_plano: Mapped[TipoPlano] = mapped_column(
        Enum(TipoPlano, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    
    # Valor acordado para o pacote mensal
    valor_cobrado: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Campos de pagamento (opcionais - pacote pode estar em aberto)
    valor_pago: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    data_pagamento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status do pacote
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamp
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relacionamentos
    cachorro: Mapped["Cachorro"] = relationship(back_populates="pacotes")
    
# Um pacote contém múltiplos agendamentos (e banhos legados se existirem)
    agendamentos: Mapped[List["Agendamento"]] = relationship(
        back_populates="pacote",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Agendamento.data_banho"  # Ordena por data_banho
    )
    banhos: Mapped[List["Banho"]] = relationship(  # Mantém compatibilidade legada
        back_populates="pacote",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Propriedade calculada: limite de banhos baseado no plano
    @property
    def limite_banhos_mes(self) -> int:
        """Retorna o limite de banhos permitidos por mês baseado no tipo de plano"""
        limites = {
            TipoPlano.SEMANAL: 4,
            TipoPlano.QUINZENAL: 2,
            TipoPlano.MENSAL: 1
        }
        return limites.get(self.tipo_plano, 1)
    
    # Propriedade calculada: status de pagamento
    @property
    def status_pagamento(self) -> str:
        """Retorna o status do pagamento do pacote"""
        if self.valor_pago is None:
            return "em_aberto"
        if self.valor_pago >= self.valor_cobrado:
            return "pago"
        return "parcial"
    
    def to_dict(self) -> dict:
        """Serialização completa incluindo pet nome e agendamentos para frontend."""
        return {
            "id": self.id,
            "cachorro_id": self.cachorro_id,
            "tipo_plano": self.tipo_plano.value if self.tipo_plano else None,
            "valor_cobrado": self.valor_cobrado,
            "valor_pago": self.valor_pago,
            "data_pagamento": self.data_pagamento.isoformat() if self.data_pagamento else None,
            "ativo": self.ativo,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "pet_nome": self.cachorro.nome if self.cachorro else None,
            "cliente_nome": self.cachorro.cliente.nome if self.cachorro and self.cachorro.cliente else None,
            "status_pagamento": self.status_pagamento,
            "limite_banhos_mes": self.limite_banhos_mes,
            "total_agendamentos": len(self.agendamentos) if self.agendamentos else 0,
            "agendamentos": [ag.to_dict() for ag in self.agendamentos] if self.agendamentos else []
        }
    
    def __repr__(self) -> str:
        return f"<Pacote(id={self.id}, tipo='{self.tipo_plano.value}', ativo={self.ativo})>"
