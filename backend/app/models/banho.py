"""
Model Banho - Representa um banho/tosa realizado.
Cada banho pertence a um pacote específico.
"""
from sqlalchemy import Text, ForeignKey, DateTime, Date, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from typing import Optional
from datetime import datetime, date


class Banho(Base):
    __tablename__ = "banhos"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Foreign Key para pacote (obrigatório)
    pacote_id: Mapped[int] = mapped_column(
        ForeignKey("pacotes.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Data em que o banho foi realizado
    data_banho: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Observações específicas deste banho (medicamentos, produtos, comportamento)
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamp de registro no sistema
    registrado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relacionamento
    pacote: Mapped["Pacote"] = relationship(back_populates="banhos")
    
    def __repr__(self) -> str:
        return f"<Banho(id={self.id}, data='{self.data_banho}')>"