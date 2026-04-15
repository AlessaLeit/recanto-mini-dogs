"""
Model Cliente - Representa o dono dos pets.
Um cliente pode ter múltiplos cachorros.
"""
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from typing import List, Optional
from datetime import datetime


class Cliente(Base):
    __tablename__ = "clientes"
    
    # Chave primária
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Campos obrigatórios
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Campos opcionais
    telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    endereco: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Timestamps
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relacionamento: um cliente tem muitos cachorros
    # cascade="all, delete-orphan" = ao deletar cliente, deleta cachorros
    cachorros: Mapped[List["Cachorro"]] = relationship(
        back_populates="cliente",
        cascade="all, delete-orphan",
        lazy="selectin"  # Carrega cachorros junto com cliente (evita N+1)
    )
    
    def __repr__(self) -> str:
        return f"<Cliente(id={self.id}, nome='{self.nome}')>"