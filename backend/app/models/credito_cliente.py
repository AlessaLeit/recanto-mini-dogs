"""
Model CreditoCliente - Dinheiro do cliente que ainda não pertence a um pacote.

Nasce de duas formas:
- Pagamento adiantado: o cliente paga sem ter pacote aberto para receber o valor.
- Sobra de pagamento: pagou mais do que o pacote custava (ex.: R$ 200 num
  pacote de R$ 180); a diferença fica guardada em vez de sumir dentro do pacote.

É consumido quando um pacote novo é criado, virando um Pagamento de verdade no
histórico dele. O consumo é parcial: um crédito maior que o pacote paga o que
dá e mantém o restante para o mês seguinte — por isso 'valor_consumido' em vez
de um simples booleano de "usado".
"""
from sqlalchemy import String, Text, Float, ForeignKey, DateTime, Date, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.pacote import TipoPagamento
from typing import Optional
from datetime import datetime, date


class CreditoCliente(Base):
    __tablename__ = "creditos_cliente"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    valor: Mapped[float] = mapped_column(Float, nullable=False)
    valor_consumido: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")

    tipo_pagamento: Mapped[TipoPagamento] = mapped_column(
        Enum(TipoPagamento, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=TipoPagamento.PIX,
        server_default=TipoPagamento.PIX.value,
    )
    data_pagamento: Mapped[date] = mapped_column(Date, nullable=False)
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Preenchido quando o crédito veio da sobra de um pagamento, para dar
    # rastreabilidade de onde o dinheiro entrou.
    origem_pacote_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("pacotes.id", ondelete="SET NULL"), nullable=True
    )

    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cliente: Mapped["Cliente"] = relationship(back_populates="creditos")

    @property
    def saldo(self) -> float:
        """Quanto deste crédito ainda está disponível."""
        return round((self.valor or 0.0) - (self.valor_consumido or 0.0), 2)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "valor": self.valor,
            "valor_consumido": self.valor_consumido,
            "saldo": self.saldo,
            "tipo_pagamento": self.tipo_pagamento.value if self.tipo_pagamento else None,
            "data_pagamento": self.data_pagamento.isoformat() if self.data_pagamento else None,
            "observacao": self.observacao,
            "origem_pacote_id": self.origem_pacote_id,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
        }

    def __repr__(self) -> str:
        return f"<CreditoCliente(id={self.id}, cliente={self.cliente_id}, saldo={self.saldo})>"
