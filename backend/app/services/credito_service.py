"""
Serviço de créditos do cliente.

Crédito é dinheiro que o cliente já pagou e que ainda não pertence a nenhum
pacote. Ele nasce de duas formas:

- Adiantamento: o cliente paga sem ter pacote aberto para receber o valor
  (típico de quem paga atrasado e aproveita para deixar o próximo adiantado).
- Sobra: pagou mais do que o pacote custava; a diferença vira crédito em vez
  de ficar escondida como "saldo a favor" dentro de um pacote já quitado.

E é consumido quando um pacote novo nasce, virando um Pagamento de verdade no
histórico dele — preservando forma de pagamento e data originais.
"""
import logging
from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import CreditoCliente, Pacote, Cachorro
from app.models.pacote import Pagamento

logger = logging.getLogger(__name__)


def _cliente_id_do_pacote(pacote: Pacote) -> Optional[int]:
    """Cliente dono do pacote, via cachorro principal."""
    if pacote.cachorro and pacote.cachorro.cliente_id:
        return pacote.cachorro.cliente_id
    return None


def listar_creditos_disponiveis(db: Session, cliente_id: int) -> List[CreditoCliente]:
    """
    Créditos com saldo, mais antigos primeiro (FIFO): o dinheiro que entrou
    antes é gasto antes, o que mantém a ordem cronológica do histórico.
    """
    creditos = (
        db.query(CreditoCliente)
        .filter(CreditoCliente.cliente_id == cliente_id)
        .order_by(CreditoCliente.data_pagamento, CreditoCliente.id)
        .all()
    )
    return [c for c in creditos if c.saldo > 0.001]


def saldo_disponivel(db: Session, cliente_id: int) -> float:
    """Total de crédito que o cliente tem para usar."""
    return round(sum(c.saldo for c in listar_creditos_disponiveis(db, cliente_id)), 2)


def registrar_credito(
    db: Session,
    cliente_id: int,
    valor: float,
    data_pagamento: date,
    tipo_pagamento: str = "pix",
    observacao: Optional[str] = None,
    origem_pacote_id: Optional[int] = None,
) -> CreditoCliente:
    """Guarda um valor como crédito do cliente."""
    credito = CreditoCliente(
        cliente_id=cliente_id,
        valor=valor,
        valor_consumido=0.0,
        data_pagamento=data_pagamento,
        tipo_pagamento=tipo_pagamento,
        observacao=observacao,
        origem_pacote_id=origem_pacote_id,
    )
    db.add(credito)
    db.commit()
    db.refresh(credito)
    return credito


def aplicar_creditos(db: Session, pacote: Pacote) -> float:
    """
    Usa o crédito disponível do cliente para pagar o pacote informado.

    Consome parcialmente: um crédito maior que o pacote paga o que couber e
    mantém o restante para o mês seguinte. Devolve quanto foi aplicado.

    Best-effort: qualquer falha aqui não pode impedir a criação do pacote, que
    é a operação principal de quem chamou.
    """
    try:
        cliente_id = _cliente_id_do_pacote(pacote)
        if not cliente_id:
            return 0.0

        restante = round((pacote.valor_cobrado or 0.0) - (pacote.valor_pago_total or 0.0), 2)
        if restante <= 0:
            return 0.0

        aplicado_total = 0.0
        for credito in listar_creditos_disponiveis(db, cliente_id):
            if restante <= 0.001:
                break

            usar = min(credito.saldo, restante)
            db.add(Pagamento(
                pacote_id=pacote.id,
                valor_pago=usar,
                data_pagamento=credito.data_pagamento,
                tipo_pagamento=credito.tipo_pagamento,
                observacao=f"Crédito adiantado de {credito.data_pagamento.strftime('%d/%m/%Y')}",
            ))
            credito.valor_consumido = round((credito.valor_consumido or 0.0) + usar, 2)

            restante = round(restante - usar, 2)
            aplicado_total = round(aplicado_total + usar, 2)

        if aplicado_total > 0:
            db.commit()
            db.refresh(pacote)
            logger.info(
                f"Crédito de R$ {aplicado_total:.2f} aplicado ao pacote {pacote.id} "
                f"(cliente {cliente_id})."
            )
        return aplicado_total
    except Exception as e:
        db.rollback()
        logger.warning(f"Falha ao aplicar crédito no pacote {getattr(pacote, 'id', '?')}: {e}")
        return 0.0
