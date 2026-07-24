"""
Router Comandas - Fila de comandas impressas (clientes com envio_comanda
= 'impresso'). Lista pendentes e gera o PDF em lote (4 comandas por A4),
marcando-as como impressas.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.services import comanda_service

router = APIRouter(
    tags=["Comandas"],
    redirect_slashes=True,
    dependencies=[Depends(get_current_user)],
)


@router.get("/pendentes")
def listar_pendentes(db: Session = Depends(get_db)):
    """Lista as comandas na fila aguardando impressão."""
    pendentes = comanda_service.listar_pendentes(db)
    return [
        {
            "id": item.id,
            "pacote_id": item.pacote_id,
            "pet_nome": item.pacote.pet_nome,
            "cliente_nome": item.pacote.cliente_nome,
            "criado_em": item.criado_em,
        }
        for item in pendentes
    ]


@router.get("/pdf")
def gerar_pdf(db: Session = Depends(get_db)):
    """
    Gera o PDF com todas as comandas pendentes (4 por página A4) e marca
    todas como impressas.
    """
    pendentes = comanda_service.listar_pendentes(db)
    if not pendentes:
        return Response(status_code=204)

    pdf_bytes = comanda_service.gerar_pdf(pendentes)
    comanda_service.marcar_impressas(db, pendentes)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=comandas.pdf"},
    )


@router.get("/pdf/exemplo")
def gerar_pdf_exemplo():
    """Gera uma página A4 com dados fictícios, só para visualizar o modelo da comanda."""
    pdf_bytes = comanda_service.gerar_pdf_exemplo()
    return Response(content=pdf_bytes, media_type="application/pdf")
