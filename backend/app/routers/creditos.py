"""
Router Créditos - Pagamento adiantado do cliente.

Crédito é dinheiro já pago que ainda não pertence a nenhum pacote. Fica
guardado até um pacote novo nascer, quando vira pagamento dele
automaticamente (ver app/services/credito_service.py).
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import Cliente
from app.schemas.credito import CreditoCreate, CreditoResponse, SaldoCreditoResponse
from app.services import credito_service

router = APIRouter(
    tags=["Créditos"],
    redirect_slashes=True,
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=SaldoCreditoResponse)
def obter_creditos(
    cliente_id: int = Query(..., description="Cliente dono dos créditos"),
    db: Session = Depends(get_db),
):
    """Saldo e lista de créditos disponíveis do cliente."""
    creditos = credito_service.listar_creditos_disponiveis(db, cliente_id)
    return {
        "cliente_id": cliente_id,
        "saldo": round(sum(c.saldo for c in creditos), 2),
        "creditos": [CreditoResponse.model_validate(c) for c in creditos],
    }


@router.post("/", response_model=CreditoResponse, status_code=status.HTTP_201_CREATED)
def registrar_pagamento_adiantado(dados: CreditoCreate, db: Session = Depends(get_db)):
    """
    Guarda um pagamento adiantado como crédito do cliente.

    A conferência de pacotes em aberto é feita na interface, que já tem o
    histórico carregado e pergunta ao usuário se é mesmo adiantamento — aqui
    só validamos que o cliente existe.
    """
    if not db.query(Cliente).filter(Cliente.id == dados.cliente_id).first():
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    credito = credito_service.registrar_credito(
        db,
        cliente_id=dados.cliente_id,
        valor=dados.valor,
        data_pagamento=dados.data_pagamento,
        tipo_pagamento=dados.tipo_pagamento,
        observacao=dados.observacao,
    )
    return CreditoResponse.model_validate(credito)
