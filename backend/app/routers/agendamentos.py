"""
Router Agendamentos - CRUD básico e edição status/extras.
Integra com pacote_service para validações.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Agendamento
from app.schemas import AgendamentoCreate, AgendamentoUpdate, AgendamentoResponse, AgendamentoAvulsoCreate
from app.services.pacote_service import PacoteService
from app.models import Pacote, Cachorro, Cliente
from datetime import date

router = APIRouter(tags=["Agendamentos"], redirect_slashes=True)

@router.post("/", response_model=AgendamentoResponse, status_code=status.HTTP_201_CREATED)
def criar_agendamento(agendamento: AgendamentoCreate, db: Session = Depends(get_db)):
    """
    Cria novo agendamento para pacote (valida limite).
    """
    service = PacoteService(db)
    service.validar_limite_agendamentos(agendamento.pacote_id, agendamento.data_banho)
    
    db_ag = Agendamento(**agendamento.model_dump())
    db.add(db_ag)
    db.commit()
    db.refresh(db_ag)
    return AgendamentoResponse.model_validate(db_ag).model_dump()

@router.get("/", response_model=List[AgendamentoResponse])
def listar_agendamentos(pacote_id: int, db: Session = Depends(get_db)):
    """
    Lista agendamentos de um pacote (ordenados por data_banho).
    """
    agendamentos = db.query(Agendamento).filter(
        Agendamento.pacote_id == pacote_id
    ).order_by(Agendamento.data_banho).all()
    return agendamentos


@router.post("/avulso", response_model=AgendamentoResponse, status_code=status.HTTP_201_CREATED)
def criar_banho_avulso(dados: AgendamentoAvulsoCreate, db: Session = Depends(get_db)):
    """
    Cria um banho avulso (sem pacote vinculado). Entra na agenda normalmente.
    """
    db_ag = Agendamento(
        pacote_id=None,
        data_banho=dados.data_banho,
        turno=dados.turno,
        status_presenca="pendente",
        pet_nome_avulso=dados.pet_nome_avulso.strip(),
        cliente_nome_avulso=dados.cliente_nome_avulso.strip(),
        valor_avulso=dados.valor_avulso,
        pago_avulso=dados.pago_avulso,
        extras={"info": dados.observacao or "", "valor_extra": 0}
    )
    db.add(db_ag)
    db.commit()
    db.refresh(db_ag)
    return AgendamentoResponse.model_validate(db_ag).model_dump()


@router.get("/avulsos", response_model=List[AgendamentoResponse])
def listar_banhos_avulsos(db: Session = Depends(get_db)):
    """
    Lista todos os banhos avulsos (sem pacote), mais recentes primeiro.
    """
    agendamentos = db.query(Agendamento).filter(
        Agendamento.pacote_id.is_(None)
    ).order_by(Agendamento.data_banho.desc(), Agendamento.registrado_em.desc()).all()
    return agendamentos

@router.get("/dashboard/{data}")
def listar_agendamentos_data(
    data: str,
    turno: Optional[str] = Query(None, description="Filtra por turno: manha ou tarde"),
    db: Session = Depends(get_db)
):
    """
    Lista agendamentos de data específica (YYYY-MM-DD) para dashboard.
    Default: hoje se inválida. Inclui pet.nome, cliente.nome, pacote.id.
    """
    try:
        target_date = date.fromisoformat(data)
    except ValueError:
        target_date = date.today()

    query = (db.query(Agendamento)
        .outerjoin(Pacote, Agendamento.pacote_id == Pacote.id)
        .outerjoin(Cachorro, Pacote.cachorro_id == Cachorro.id)
        .filter(Agendamento.data_banho == target_date)
    )

    if turno in ("manha", "tarde"):
        query = query.filter(Agendamento.turno == turno)

    agendamentos = query.order_by(Agendamento.registrado_em.desc()).all()

    result = []
    for ag in agendamentos:
        avulso = ag.pacote_id is None
        ag_dict = {
            "id": ag.id,
            "pacote_id": ag.pacote_id,
            "avulso": avulso,
            "data_banho": ag.data_banho,
            "status_presenca": ag.status_presenca,
            "turno": ag.turno,
            "extras": ag.extras,
            "valor_avulso": ag.valor_avulso,
            "registrado_em": ag.registrado_em,
            "atualizado_em": ag.atualizado_em,
            "pet_nome": (ag.pet_nome_avulso or "Avulso") if avulso else (
                ag.pacote.pet_nome if ag.pacote and ag.pacote.pet_nome else "Pet não encontrado"
            ),
            "cliente_nome": (ag.cliente_nome_avulso or "-") if avulso else (
                ag.pacote.cachorro.cliente.nome if ag.pacote
                    and ag.pacote.cachorro
                    and ag.pacote.cachorro.cliente
                    else "Cliente não encontrado"
            )
        }
        result.append(ag_dict)

    return result


@router.put("/{agendamento_id}", response_model=AgendamentoResponse)
def atualizar_agendamento(
    agendamento_id: int,
    update_data: AgendamentoUpdate,
    db: Session = Depends(get_db)
):
    """
    Edita status_presenca e extras (retroativo permitido, sem trava de data).
    """
    db_ag = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()
    if not db_ag:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(db_ag, field, value)
    
    db.commit()
    db.refresh(db_ag)
    return AgendamentoResponse.model_validate(db_ag).model_dump()


@router.put("/{agendamento_id}/data", response_model=AgendamentoResponse)
def atualizar_data_agendamento(
    agendamento_id: int,
    data_banho: date,
    db: Session = Depends(get_db)
):
    """
    Edita APENAS a data_banho de um agendamento.
    Permite qualquer dia (retroativo ou futuro).
    """
    db_ag = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()
    if not db_ag:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    
    db_ag.data_banho = data_banho
    
    db.commit()
    db.refresh(db_ag)
    return AgendamentoResponse.model_validate(db_ag).model_dump()


@router.delete("/{agendamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_agendamento(agendamento_id: int, db: Session = Depends(get_db)):
    """
    Remove agendamento.
    """
    db_ag = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()
    if not db_ag:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    
    db.delete(db_ag)
    db.commit()
    return None
