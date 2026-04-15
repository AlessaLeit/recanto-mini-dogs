"""
Router Pacotes - CRUD, pagamento e integração com serviço de validação.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.models import Pacote, Cachorro
from app.schemas import PacoteCreate, PacoteUpdate, PacoteResponse, PacoteWithBanhos
from app.services import PacoteService

router = APIRouter(redirect_slashes=True)


@router.post("/", response_model=PacoteResponse, status_code=status.HTTP_201_CREATED)
def criar_pacote(pacote: PacoteCreate, db: Session = Depends(get_db)):
    """
    Cria um novo pacote de banhos para um cachorro.
    """
    # Verifica se cachorro existe
    cachorro = db.query(Cachorro).filter(Cachorro.id == pacote.cachorro_id).first()
    if not cachorro:
        raise HTTPException(status_code=404, detail="Cachorro não encontrado")
    
    db_pacote = Pacote(**pacote.model_dump(exclude={'limite_banhos_mes'}))
    db.add(db_pacote)
    db.commit()
    db.refresh(db_pacote)
    return db_pacote.to_dict()


@router.get("/", response_model=List[PacoteResponse])
def listar_pacotes(
    cachorro_id: Optional[int] = Query(None, description="Filtrar por cachorro"),
    ativo: Optional[bool] = Query(True, description="Filtrar por status ativo"),
    incluir_inativos: bool = Query(False, description="Incluir pacotes inativos"),
    db: Session = Depends(get_db)
):
    """
    Lista pacotes com filtros.
    Por padrão retorna apenas ativos, a menos que incluir_inativos=true.
    """
    service = PacoteService(db)
    
    if cachorro_id:
        pacotes = service.listar_pacotes_ativos_por_cachorro(cachorro_id, incluir_inativos)
        return [p.to_dict() for p in pacotes]
    
    query = db.query(Pacote).options(joinedload(Pacote.cachorro))
    if not incluir_inativos:
        query = query.filter(Pacote.ativo == True)
    
    pacotes = query.all()
    return [p.to_dict() for p in pacotes]


@router.get("/{pacote_id}", response_model=PacoteWithBanhos)
def obter_pacote(pacote_id: int, db: Session = Depends(get_db)):
    """
    Obtém detalhes do pacote incluindo banhos realizados.
    """
    service = PacoteService(db)
    pacote = service.get_pacote_com_relacionamentos(pacote_id)
    
    if not pacote:
        raise HTTPException(status_code=404, detail="Pacote não encontrado")
    
    # Adiciona contagem total de banhos
    pacote.total_banhos_realizados = len(pacote.banhos)
    return pacote.to_dict()


@router.put("/{pacote_id}", response_model=PacoteResponse)
def atualizar_pacote(
    pacote_id: int,
    pacote_update: PacoteUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza dados do pacote (plano, valores, status).
    """
    db_pacote = db.query(Pacote).filter(Pacote.id == pacote_id).first()
    if not db_pacote:
        raise HTTPException(status_code=404, detail="Pacote não encontrado")
    
    update_data = pacote_update.model_dump(exclude_unset=True, exclude={'limite_banhos_mes'})
    for field, value in update_data.items():
        setattr(db_pacote, field, value)
    
    db.commit()
    db.refresh(db_pacote)
    return db_pacote


@router.post("/{pacote_id}/pagar", response_model=PacoteResponse)
def registrar_pagamento(
    pacote_id: int,
    valor_pago: float,
    data_pagamento: date,
    db: Session = Depends(get_db)
):
    """
    Endpoint específico para registrar pagamento de um pacote.
    """
    service = PacoteService(db)
    return service.registrar_pagamento(pacote_id, valor_pago, data_pagamento)


@router.delete("/{pacote_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_pacote(pacote_id: int, db: Session = Depends(get_db)):
    """
    Remove um pacote e todos os seus banhos.
    """
    db_pacote = db.query(Pacote).filter(Pacote.id == pacote_id).first()
    if not db_pacote:
        raise HTTPException(status_code=404, detail="Pacote não encontrado")
    
    db.delete(db_pacote)
    db.commit()
    return None

