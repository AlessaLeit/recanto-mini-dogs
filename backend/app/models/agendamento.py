"""
Model Agendamento - Representa um agendamento de banho/tosa de um pacote.
Permite edição retroativa de status e extras.
"""
from sqlalchemy import Text, Float, String, ForeignKey, DateTime, Date, func, JSON, Boolean
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

class Turno(str, enum.Enum):
    """Turno do dia em que o banho está agendado"""
    MANHA = "manha"
    TARDE = "tarde"

class Agendamento(Base):
    __tablename__ = "agendamentos"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Foreign Key para pacote (opcional: nulo para banhos avulsos sem pacote vinculado)
    pacote_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("pacotes.id", ondelete="CASCADE"),
        nullable=True
    )

    # Campos usados apenas em banhos avulsos (pacote_id nulo): nome digitado
    # livremente, já que o cliente/cachorro pode não estar cadastrado no sistema.
    pet_nome_avulso: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cliente_nome_avulso: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    valor_avulso: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Pagamento do banho avulso (não se aplica a agendamentos de pacote, que usam
    # a tabela Pagamento separada).
    pago_avulso: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    # Data planejada do agendamento
    data_banho: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Status de presença (editável retroativamente)
    status_presenca: Mapped[StatusPresenca] = mapped_column(
        SQLEnum(StatusPresenca, values_callable=lambda obj: [e.value for e in obj]),
        default=StatusPresenca.PENDENTE,
        nullable=False
    )

    # Turno do banho (manhã/tarde), usado para filtrar a agenda do dia
    turno: Mapped[Turno] = mapped_column(
        SQLEnum(Turno, values_callable=lambda obj: [e.value for e in obj]),
        default=Turno.MANHA,
        server_default=Turno.MANHA.value,
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
    pacote: Mapped[Optional["Pacote"]] = relationship(back_populates="agendamentos")

    # ── Presença por cachorro (pacotes multi-cachorro) ──────────────────────
    # Em pacotes com mais de um cachorro, cada pet pode ter comparecido ou não
    # no mesmo dia. O status individual fica em extras["presencas"], no formato
    # {"<cachorro_id>": "pendente|concluido|faltou"}, e status_presenca guarda
    # o resumo do dia (usado por dashboard, relatórios e fechamento do ciclo).

    @property
    def presencas(self) -> Dict[str, str]:
        """Status individual por cachorro; vazio em agendamentos de pet único."""
        return (self.extras or {}).get("presencas") or {}

    def presenca_do_cachorro(self, cachorro_id: int) -> str:
        """
        Status de um cachorro específico. Sem registro individual (agendamentos
        antigos ou pacotes de um pet só), vale o status geral do dia.
        """
        individual = self.presencas.get(str(cachorro_id))
        if individual:
            return individual
        return self.status_presenca.value if self.status_presenca else StatusPresenca.PENDENTE.value

    def definir_presencas(self, presencas: Dict[str, str]) -> None:
        """
        Grava o status individual dos cachorros em extras e recalcula o status
        geral do dia: pendente se algum pet ainda está pendente, concluído se ao
        menos um tomou banho, faltou se nenhum compareceu.
        """
        extras = dict(self.extras or {})
        limpas = {str(k): v for k, v in (presencas or {}).items() if v}
        if limpas:
            extras["presencas"] = limpas
        else:
            extras.pop("presencas", None)
        self.extras = extras

        valores = list(limpas.values())
        if not valores:
            return
        if StatusPresenca.PENDENTE.value in valores:
            self.status_presenca = StatusPresenca.PENDENTE
        elif StatusPresenca.CONCLUIDO.value in valores:
            self.status_presenca = StatusPresenca.CONCLUIDO
        else:
            self.status_presenca = StatusPresenca.FALTOU

    @property
    def valor_banho_dia(self) -> float:
        """
        Valor de banho cobrado neste dia: soma apenas os cachorros que de fato
        tomaram banho. Em pacotes de um pet só (ou agendamentos sem presença
        individual), equivale ao valor do dia inteiro quando concluído.
        """
        if not self.pacote:
            return 0.0
        valores = self.pacote.valor_banho_por_cachorro
        return sum(
            valor for cachorro_id, valor in valores.items()
            if self.presenca_do_cachorro(int(cachorro_id)) == StatusPresenca.CONCLUIDO.value
        )

    @property
    def cachorros_presentes(self) -> list:
        """Nomes dos cachorros que tomaram banho neste dia (para comandas)."""
        if not self.pacote:
            return []
        return [
            c.nome for c in self.pacote.cachorros_todos
            if self.presenca_do_cachorro(c.id) == StatusPresenca.CONCLUIDO.value
        ]

    def to_dict(self) -> dict:
        """Serialização completa para JSON/API"""
        return {
            "id": self.id,
            "pacote_id": self.pacote_id,
            "data_banho": self.data_banho.isoformat() if self.data_banho else None,
            "status_presenca": self.status_presenca.value if self.status_presenca else None,
            "turno": self.turno.value if self.turno else None,
            "extras": self.extras or {},
            "presencas": self.presencas,
            "valor_banho_dia": self.valor_banho_dia,
            "pet_nome_avulso": self.pet_nome_avulso,
            "cliente_nome_avulso": self.cliente_nome_avulso,
            "valor_avulso": self.valor_avulso,
            "pago_avulso": self.pago_avulso,
            "registrado_em": self.registrado_em.isoformat() if self.registrado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None
        }
    
    def __repr__(self) -> str:
        return f"<Agendamento(id={self.id}, data='{self.data_banho}', status='{self.status_presenca.value}')>"

