"""
Models SQLAlchemy 2.x usando Mapped e mapped_column.
"""
from .cliente import Cliente
from .cachorro import Cachorro, PorteCachorro
from .pacote import Pacote, TipoPlano, Pagamento, TipoPagamento
from .banho import Banho
from .agendamento import Agendamento, StatusPresenca
from .comanda_impressao import ComandaImpressao

__all__ = [
    "Cliente",
    "Cachorro",
    "PorteCachorro",
    "Pacote",
    "TipoPlano",
    "Pagamento",
    "TipoPagamento",
    "Banho",
    "Agendamento",
    "StatusPresenca",
    "ComandaImpressao"
]
