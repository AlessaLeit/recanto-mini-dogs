"""
Router Clientes - CRUD completo e listagem com cachorros.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Annotated
from app.database import get_db
from app.models import Cliente, Cachorro
from app.schemas import ClienteCreate, ClienteUpdate, ClienteResponse, ClienteWithCachorros

CLIENTE_NOT_FOUND = "Cliente não encontrado"

router = APIRouter(tags=["Clientes"], redirect_slashes=True)


@router.post("/", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def criar_cliente(cliente: ClienteCreate, db: Annotated[Session, Depends(get_db)]):
    """
    Cria um novo cliente.
    """
    db_cliente = Cliente(**cliente.model_dump())
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return ClienteResponse.model_validate(db_cliente).model_dump()

@router.get("/", response_model=List[ClienteWithCachorros])
def listar_clientes(
    skip: Annotated[int, Query(ge=0, description="Registros para pular (paginação)")] = 0,
    limit: Annotated[int, Query(ge=1, le=1000, description="Limite de registros")] = 100,
    busca: Annotated[Optional[str], Query(description="Buscar por nome")] = None,
    db: Annotated[Session, Depends(get_db)] = None
):
    """
    Lista todos os clientes com paginação e busca opcional por nome.
    """
    query = db.query(Cliente).options(
        joinedload(Cliente.cachorros)
    )
    
    if busca:
        query = query.filter(Cliente.nome.ilike(f"%{busca}%"))
    
    clientes = query.offset(skip).limit(limit).all()
    return [ClienteWithCachorros.model_validate(c).model_dump() for c in clientes]

@router.get(
    "/{cliente_id}",
    response_model=ClienteWithCachorros,
    responses={status.HTTP_404_NOT_FOUND: {"description": CLIENTE_NOT_FOUND}}
)
def obter_cliente(cliente_id: int, db: Annotated[Session, Depends(get_db)]):
    """
    Obtém detalhes de um cliente específico incluindo seus cachorros.
    """
    cliente = db.query(Cliente).options(
        joinedload(Cliente.cachorros)
    ).filter(Cliente.id == cliente_id).first()
    
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CLIENTE_NOT_FOUND)
    
    return ClienteWithCachorros.model_validate(cliente).model_dump()


@router.put(
    "/{cliente_id}",
    response_model=ClienteResponse,
    responses={status.HTTP_404_NOT_FOUND: {"description": CLIENTE_NOT_FOUND}}
)
def atualizar_cliente(
    cliente_id: int,
    cliente_update: ClienteUpdate,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Atualiza dados de um cliente (atualização parcial suportada).
    """
    db_cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not db_cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CLIENTE_NOT_FOUND)
    
    # Atualiza apenas campos fornecidos
    update_data = cliente_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_cliente, field, value)
    
    db.commit()
    db.refresh(db_cliente)
    return ClienteResponse.model_validate(db_cliente).model_dump()

@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_404_NOT_FOUND: {"description": CLIENTE_NOT_FOUND}}
)
def deletar_cliente(cliente_id: int, db: Annotated[Session, Depends(get_db)]):
    """
    Remove um cliente e todos os seus cachorros (cascade).
    """
    db_cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not db_cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CLIENTE_NOT_FOUND)
    
    db.delete(db_cliente)
    db.commit()
    return None