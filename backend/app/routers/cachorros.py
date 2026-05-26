"""
Router Cachorros - CRUD e listagem com histórico de pacotes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database import get_db
from app.models import Cachorro, Cliente
from app.schemas import CachorroCreate, CachorroUpdate, CachorroResponse, CachorroWithPacotes

router = APIRouter(tags=["Cachorros"], redirect_slashes=True)


@router.post("/", response_model=CachorroResponse, status_code=status.HTTP_201_CREATED)
def criar_cachorro(cachorro: CachorroCreate, db: Session = Depends(get_db)):
    """
    Cria um novo cachorro vinculado a um cliente existente.
    """
    # Verifica se cliente existe
    cliente = db.query(Cliente).filter(Cliente.id == cachorro.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    db_cachorro = Cachorro(**cachorro.model_dump())
    db.add(db_cachorro)
    db.commit()
    db.refresh(db_cachorro)
    return CachorroResponse.model_validate(db_cachorro).model_dump()


@router.get("/", response_model=List[CachorroResponse])
def listar_cachorros(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    cliente_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    porte: Optional[str] = Query(None, description="Filtrar por porte: pequeno, medio, grande"),
    db: Session = Depends(get_db)
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


@router.get("/{cachorro_id}", response_model=CachorroWithPacotes)
def obter_cachorro(cachorro_id: int, db: Session = Depends(get_db)):
    """
    Obtém detalhes do cachorro incluindo histórico de pacotes.
    """
    cachorro = db.query(Cachorro).options(
        joinedload(Cachorro.pacotes)
    ).filter(Cachorro.id == cachorro_id).first()
    
    if not cachorro:
        raise HTTPException(status_code=404, detail="Cachorro não encontrado")
    
    return CachorroWithPacotes.model_validate(cachorro).model_dump()


@router.put("/{cachorro_id}", response_model=CachorroResponse)
def atualizar_cachorro(
    cachorro_id: int,
    cachorro_update: CachorroUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza dados do cachorro.
    """
    db_cachorro = db.query(Cachorro).filter(Cachorro.id == cachorro_id).first()
    if not db_cachorro:
        raise HTTPException(status_code=404, detail="Cachorro não encontrado")
    
    update_data = cachorro_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_cachorro, field, value)
    
    db.commit()
    db.refresh(db_cachorro)
    return CachorroResponse.model_validate(db_cachorro).model_dump()


@router.delete("/{cachorro_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_cachorro(cachorro_id: int, db: Session = Depends(get_db)):
    """
    Remove um cachorro e todos os seus pacotes/banhos.
    """
    db_cachorro = db.query(Cachorro).filter(Cachorro.id == cachorro_id).first()
    if not db_cachorro:
        raise HTTPException(status_code=404, detail="Cachorro não encontrado")
    
    db.delete(db_cachorro)
    db.commit()
    return None