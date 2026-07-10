"""
Model Pacote - Representa um plano de banhos contratado.
Um pacote pode ter múltiplos banhos e pagamentos registrados.
"""
from sqlalchemy import String, Text, Float, ForeignKey, Boolean, DateTime, Date, func, Enum, Table, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from typing import List, Optional, Literal
from datetime import datetime, date
import enum


# Tabela associativa: cachorros adicionais de um pacote (além do cachorro
# principal em Pacote.cachorro_id). Permite fechar um único pacote/pagamento
# para vários cachorros da mesma família.
pacote_cachorros_extras = Table(
    "pacote_cachorros_extras",
    Base.metadata,
    Column("pacote_id", Integer, ForeignKey("pacotes.id", ondelete="CASCADE"), primary_key=True),
    Column("cachorro_id", Integer, ForeignKey("cachorros.id", ondelete="CASCADE"), primary_key=True),
)


class TipoPlano(str, enum.Enum):
    """Tipos de plano disponíveis"""
    SEMANAL = "semanal"      # Até 4 banhos/mês
    QUINZENAL = "quinzenal"  # Até 2 banhos/mês
    MENSAL = "mensal"        # Até 1 banho/mês


class DiaSemana(str, enum.Enum):
    """Dias da semana aceitos para criação de agendamentos automáticos."""
    TERCA = "terca"
    QUARTA = "quarta"
    QUINTA = "quinta"
    SEXTA = "sexta"
    SABADO = "sabado"

class TipoPagamento(str, enum.Enum):
    """Métodos de pagamento aceitos."""
    PIX = "pix"
    DINHEIRO = "dinheiro"
    CARTAO_DEBITO = "cartao_debito"
    CARTAO_CREDITO = "cartao_credito"
    OUTRO = "outro"


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
    
    # Valor base por banho (exibido no detalhe do pacote)
    valor_banho_base: Mapped[float] = mapped_column(Float, nullable=False)

    # Valor acordado para o pacote (valor_banho_base * quantidade do plano)
    valor_cobrado: Mapped[float] = mapped_column(Float, nullable=False)

    # Valor de transporte para o pacote
    valor_transporte: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)


    # Dia da semana escolhido para gerar agendamentos automáticos
    dia_da_semana: Mapped[DiaSemana] = mapped_column(
        Enum(DiaSemana, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )

    # Indica se o ciclo de banhos do mês foi encerrado manualmente
    fechado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Status do pacote
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamp
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relacionamentos
    cachorro: Mapped["Cachorro"] = relationship(back_populates="pacotes", foreign_keys=[cachorro_id])

    # Cachorros adicionais (além do principal) incluídos neste pacote — permite
    # fechar/pagar de uma vez só vários cachorros da mesma família.
    cachorros_adicionais: Mapped[List["Cachorro"]] = relationship(
        secondary=pacote_cachorros_extras,
        lazy="selectin"
    )

    # Um pacote contém múltiplos agendamentos, pagamentos e banhos (legado)
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
    pagamentos: Mapped[List["Pagamento"]] = relationship(
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
    
    @property
    def valor_pago_total(self) -> float:
        """Soma todos os pagamentos registrados para este pacote."""
        if not self.pagamentos:
            return 0.0
        return sum(p.valor_pago for p in self.pagamentos)

    # Propriedade calculada: status de pagamento
    @property
    def status_pagamento(self) -> str:
        """Retorna o status do pagamento do pacote"""
        pago_total = self.valor_pago_total

        if pago_total >= self.valor_cobrado:
            return "pago"

        # Atrasado: já existe um pacote mais novo (ativo) do mesmo cachorro
        # e este pacote ainda tem saldo devedor (em aberto ou parcial).
        if self.cachorro and self.cachorro.pacotes:
            pacotes_ativos = [p for p in self.cachorro.pacotes if p.ativo]
            if pacotes_ativos:
                mais_recente = max(pacotes_ativos, key=lambda p: p.criado_em)
                if mais_recente.id != self.id and mais_recente.criado_em > self.criado_em:
                    return "atrasado"

        if pago_total == 0:
            return "fechado" if self.fechado else "em_aberto"

        return "parcial" # Se pago_total > 0 e < valor_cobrado
    
    @property
    def total_agendamentos(self) -> int:
        """Retorna o total de agendamentos vinculados"""
        return len(self.agendamentos) if self.agendamentos else 0

    @property
    def cachorros_todos(self) -> List["Cachorro"]:
        """Cachorro principal + cachorros adicionais (pacotes multi-cachorro)."""
        todos = [self.cachorro] if self.cachorro else []
        principal_id = self.cachorro.id if self.cachorro else None
        todos += [c for c in (self.cachorros_adicionais or []) if c.id != principal_id]
        return todos

    @property
    def pet_nome(self) -> Optional[str]:
        """Retorna o(s) nome(s) do(s) pet(s) vinculado(s), separados por vírgula"""
        nomes = [c.nome for c in self.cachorros_todos if c and c.nome]
        return ", ".join(nomes) if nomes else None

    @property
    def cliente_nome(self) -> Optional[str]:
        """Retorna o nome do cliente vinculado"""
        return self.cachorro.cliente.nome if self.cachorro and self.cachorro.cliente else None

    def to_dict(self) -> dict:
        """Serialização completa incluindo pet nome e agendamentos para frontend."""
        return {
            "id": self.id,
            "cachorro_id": self.cachorro_id,
            "tipo_plano": self.tipo_plano.value if self.tipo_plano else None,
            "dia_da_semana": self.dia_da_semana.value if self.dia_da_semana else None,

            "valor_banho_base": self.valor_banho_base,
            "valor_cobrado": self.valor_cobrado,
            "valor_transporte": self.valor_transporte,
            "valor_pago": self.valor_pago_total, # Mantém compatibilidade com UI que espera 'valor_pago'
            "fechado": self.fechado,
            "ativo": self.ativo,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "pet_nome": self.pet_nome,
            "cliente_nome": self.cliente_nome,
            "cachorros": [{"id": c.id, "nome": c.nome} for c in self.cachorros_todos],
            "status_pagamento": self.status_pagamento,
            "limite_banhos_mes": self.limite_banhos_mes,
            "total_agendamentos": self.total_agendamentos,
            "agendamentos": [ag.to_dict() for ag in self.agendamentos] if self.agendamentos else [],
            "pagamentos": [p.to_dict() for p in self.pagamentos] if self.pagamentos else []
        }
    
    def __repr__(self) -> str:
        return (
            f"<Pacote(id={self.id}, tipo='{self.tipo_plano.value}', "
            f"dia='{self.dia_da_semana.value}', ativo={self.ativo})>"
        )

class Pagamento(Base):
    __tablename__ = "pagamentos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pacote_id: Mapped[int] = mapped_column(ForeignKey("pacotes.id", ondelete="CASCADE"), nullable=False)
    
    valor_pago: Mapped[float] = mapped_column(Float, nullable=False)
    data_pagamento: Mapped[date] = mapped_column(Date, nullable=False)
    tipo_pagamento: Mapped[TipoPagamento] = mapped_column(
        Enum(TipoPagamento, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=TipoPagamento.PIX,
        server_default=TipoPagamento.PIX.value
    )

    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pacote: Mapped["Pacote"] = relationship(back_populates="pagamentos")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pacote_id": self.pacote_id,
            "valor_pago": self.valor_pago,
            "data_pagamento": self.data_pagamento.isoformat(),
            "tipo_pagamento": self.tipo_pagamento.value,
            "observacao": self.observacao,
        }
