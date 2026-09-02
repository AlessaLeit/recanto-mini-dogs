"""
Model ComandaImpressao - Fila de comandas de pacotes fechados que precisam
ser impressas (clientes com envio_comanda='impresso'). Acumula ao longo do
mês; o dono gera o PDF em lote quando quiser (tipicamente início do mês) e
os itens ficam marcados como impressos.
"""
from sqlalchemy import ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from typing import Optional
from datetime import datetime


class ComandaImpressao(Base):
    __tablename__ = "comandas_impressao"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    pacote_id: Mapped[int] = mapped_column(ForeignKey("pacotes.id", ondelete="CASCADE"), nullable=False)

    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    impresso_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    pacote: Mapped["Pacote"] = relationship()

    def __repr__(self) -> str:
        return f"<ComandaImpressao(id={self.id}, pacote_id={self.pacote_id}, impresso={self.impresso_em is not None})>"
