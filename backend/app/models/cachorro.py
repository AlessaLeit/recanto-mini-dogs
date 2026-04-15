"""
Model Cachorro - Representa o pet.
Um cachorro pertence a um cliente e pode ter múltiplos pacotes (histórico).
"""
from sqlalchemy import String, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from typing import List, Optional, Literal
import enum


class PorteCachorro(str, enum.Enum):
    """Enum para o porte do cachorro"""
    PEQUENO = "pequeno"
    MEDIO = "medio"
    GRANDE = "grande"


class Cachorro(Base):
    __tablename__ = "cachorros"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Foreign Key para cliente (obrigatório)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Campos básicos
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    raca: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Enum de porte usando String no banco
    porte: Mapped[PorteCachorro] = mapped_column(
        Enum(PorteCachorro, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=PorteCachorro.MEDIO
    )
    
    # Observações gerais sobre o cachorro (alergias, comportamento, etc)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relacionamentos
    cliente: Mapped["Cliente"] = relationship(back_populates="cachorros")
    
    # Um cachorro pode ter múltiplos pacotes ao longo do tempo (histórico)
    pacotes: Mapped[List["Pacote"]] = relationship(
        back_populates="cachorro",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Cachorro(id={self.id}, nome='{self.nome}', porte='{self.porte}')>"