"""
Router Banhos - CRUD com validação de limites do plano via serviço.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Annotated, Optional
from app.database import get_db
from app.models import Banho, Pacote, Cachorro, Cliente
from app.schemas import BanhoCreate, BanhoUpdate, BanhoResponse
from app.services.pacote_service import PacoteService

BANHO_NOT_FOUND = "Banho não encontrado"

router = APIRouter(redirect_slashes=True)


@router.post("/", response_model=BanhoResponse, status_code=status.HTTP_201_CREATED)
def criar_banho(
    banho: BanhoCreate,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Registra um novo banho.
    Valida automaticamente o limite do plano antes de permitir.
    """
    # Valida limite de banhos antes de criar
    service = PacoteService(db)
    service.validar_limite_banhos(banho.pacote_id, banho.data_banho)
    
    # Cria o banho
    db_banho = Banho(**banho.model_dump())
    db.add(db_banho)
    db.commit()
    db.refresh(db_banho)
    return db_banho


@router.get("/", response_model=List[BanhoResponse])
def listar_banhos(
    pacote_id: Annotated[Optional[int], Query(description="Filtrar por pacote")] = None,
    cachorro_id: Annotated[Optional[int], Query(description="Filtrar por cachorro")] = None,
    db: Annotated[Session, Depends(get_db)] = None
):
    """
    Lista banhos com filtros por pacote ou cachorro.
    """
    query = db.query(Banho).options(
        joinedload(Banho.pacote)
    )
    
    if pacote_id:
        query = query.filter(Banho.pacote_id == pacote_id)
    if cachorro_id:
        query = query.join(Pacote).filter(Pacote.cachorro_id == cachorro_id)
    
    return query.order_by(Banho.data_banho.desc()).all()


@router.get(
    "/{banho_id}",
    response_model=BanhoResponse,
    responses={status.HTTP_404_NOT_FOUND: {"description": BANHO_NOT_FOUND}}
)
def obter_banho(
    banho_id: Annotated[int, Query(description="ID do banho")],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Obtém detalhes de um banho específico.
    """
    banho = db.query(Banho).filter(Banho.id == banho_id).first()
    if not banho:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=BANHO_NOT_FOUND)
    return banho


@router.put(
    "/{banho_id}",
    response_model=BanhoResponse,
    responses={status.HTTP_404_NOT_FOUND: {"description": BANHO_NOT_FOUND}}
)
def atualizar_banho(
    banho_id: int,
    banho_update: BanhoUpdate,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Atualiza dados de um banho (data ou observação).
    """
    db_banho = db.query(Banho).filter(Banho.id == banho_id).first()
    if not db_banho:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=BANHO_NOT_FOUND)
    
    update_data = banho_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_banho, field, value)
    
    db.commit()
    db.refresh(db_banho)
    return db_banho


@router.delete(
    "/{banho_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_404_NOT_FOUND: {"description": BANHO_NOT_FOUND}}
)
def deletar_banho(
    banho_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Remove um registro de banho.
    """
    db_banho = db.query(Banho).filter(Banho.id == banho_id).first()
    if not db_banho:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=BANHO_NOT_FOUND)
    
    db.delete(db_banho)
    db.commit()
    return None