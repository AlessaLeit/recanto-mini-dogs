"""
Router Cachorros - CRUD e listagem com histórico de pacotes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Annotated
from app.database import get_db
from app.models import Cachorro, Cliente
from app.schemas import CachorroCreate, CachorroUpdate, CachorroResponse, CachorroWithPacotes

CACHORRO_NOT_FOUND = "Cachorro não encontrado"

router = APIRouter(tags=["Cachorros"], redirect_slashes=True)


@router.post(
    "/",
    response_model=CachorroResponse,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Cliente não encontrado"}}
)
def criar_cachorro(cachorro: CachorroCreate, db: Annotated[Session, Depends(get_db)]):
    """
    Cria um novo cachorro vinculado a um cliente existente.
    """
    # Verifica se cliente existe
    cliente = db.query(Cliente).filter(Cliente.id == cachorro.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    
    db_cachorro = Cachorro(**cachorro.model_dump())
    db.add(db_cachorro)
    db.commit()
    db.refresh(db_cachorro)
    return CachorroResponse.model_validate(db_cachorro).model_dump()


@router.get("/", response_model=List[CachorroResponse])
def listar_cachorros(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    cliente_id: Annotated[Optional[int], Query(description="Filtrar por cliente")] = None,
    porte: Annotated[Optional[str], Query(description="Filtrar por porte: pequeno, medio, grande")] = None,
    db: Annotated[Session, Depends(get_db)] = None
):
    """
    Lista cachorros com filtros opcionais por cliente e porte.
    """
    query = db.query(Cachorro)
    
    if cliente_id:
        query = query.filter(Cachorro.cliente_id == cliente_id)
    if porte:
        query = query.filter(Cachorro.porte == porte)
    
    cachorros = query.offset(skip).limit(limit).all()
    return [CachorroResponse.model_validate(c).model_dump() for c in cachorros]


@router.get(
    "/{cachorro_id}",
    response_model=CachorroWithPacotes,
    responses={status.HTTP_404_NOT_FOUND: {"description": CACHORRO_NOT_FOUND}}
)
def obter_cachorro(cachorro_id: int, db: Annotated[Session, Depends(get_db)]):
    """
    Obtém detalhes do cachorro incluindo histórico de pacotes.
    """
    cachorro = db.query(Cachorro).options(
        joinedload(Cachorro.pacotes)
    ).filter(Cachorro.id == cachorro_id).first()
    
    if not cachorro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CACHORRO_NOT_FOUND)
    
    return CachorroWithPacotes.model_validate(cachorro).model_dump()


@router.put(
    "/{cachorro_id}",
    response_model=CachorroResponse,
    responses={status.HTTP_404_NOT_FOUND: {"description": CACHORRO_NOT_FOUND}}
)
def atualizar_cachorro(
    cachorro_id: int,
    cachorro_update: CachorroUpdate,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Atualiza dados do cachorro.
    """
    db_cachorro = db.query(Cachorro).filter(Cachorro.id == cachorro_id).first()
    if not db_cachorro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CACHORRO_NOT_FOUND)
    
    update_data = cachorro_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_cachorro, field, value)
    
    db.commit()
    db.refresh(db_cachorro)
    return CachorroResponse.model_validate(db_cachorro).model_dump()


@router.delete(
    "/{cachorro_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_404_NOT_FOUND: {"description": CACHORRO_NOT_FOUND}}
)
def deletar_cachorro(cachorro_id: int, db: Annotated[Session, Depends(get_db)]):
    """
    Remove um cachorro e todos os seus pacotes/banhos.
    """
    db_cachorro = db.query(Cachorro).filter(Cachorro.id == cachorro_id).first()
    if not db_cachorro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CACHORRO_NOT_FOUND)
    
    db.delete(db_cachorro)
    db.commit()
    return None