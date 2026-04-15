"""
Models SQLAlchemy 2.x usando Mapped e mapped_column.
"""
from .cliente import Cliente
from .cachorro import Cachorro, PorteCachorro
from .pacote import Pacote, TipoPlano
from .banho import Banho
from .agendamento import Agendamento, StatusPresenca

__all__ = [
    "Cliente", 
    "Cachorro", 
    "PorteCachorro",
    "Pacote", 
    "TipoPlano",
    "Banho",
    "Agendamento",
    "StatusPresenca"
]
