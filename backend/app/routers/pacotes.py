"""
Router Pacotes - CRUD, pagamento, geração automática agend
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Any, Optional
from datetime import date

from app.database import get_db
from app import models, schemas
from app.services.pacote_service import PacoteService, gerar_datas_ciclo
from app.services import whatsapp_service, comanda_service
from app.auth import get_current_user

router = APIRouter(
    tags=["Pacotes"],
    redirect_slashes=True,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Pacote não encontrado"}},
    dependencies=[Depends(get_current_user)]
)

@router.get("/", response_model=List[schemas.PacoteResponse])
def listar_pacotes(
    incluir_inativos: bool = Query(False, description="Incluir pacotes inativos?"),
    cachorro_id: Optional[int] = Query(None, description="Filtra pacotes de um cachorro específico"),
    cliente_id: Optional[int] = Query(None, description="Filtra pacotes de todos os cachorros de um cliente"),
    db: Session = Depends(get_db)
):
    """Lista pacotes (ativos por padrão; usa incluir_inativos=true para todos)."""
    query = db.query(models.Pacote).options(
        joinedload(models.Pacote.cachorro).joinedload(models.Cachorro.cliente),
        joinedload(models.Pacote.agendamentos)  # Garante que os agendamentos sejam carregados
    ).order_by(models.Pacote.criado_em.desc())

    if not incluir_inativos:
        # Usamos filter(or_...) caso existam registros legados com 'ativo' como NULL
        from sqlalchemy import or_
        query = query.filter(or_(models.Pacote.ativo == True, models.Pacote.ativo == None))

    if cachorro_id:
        query = query.filter(models.Pacote.cachorro_id == cachorro_id)

    if cliente_id:
        query = query.join(models.Cachorro).filter(models.Cachorro.cliente_id == cliente_id)

    pacotes = query.all()

    return [schemas.PacoteResponse.model_validate(p).model_dump() for p in pacotes]

def _pacote_aberto_do_cachorro(db: Session, cachorro_id: int, excluir_pacote_id: Optional[int] = None):
    """
    Retorna o pacote em aberto (ativo e não fechado) do cachorro, seja como
    principal ou como cachorro adicional, ou None se não houver nenhum.
    """
    query = db.query(models.Pacote).filter(
        models.Pacote.ativo == True,
        models.Pacote.fechado == False,
        or_(
            models.Pacote.cachorro_id == cachorro_id,
            models.Pacote.cachorros_adicionais.any(models.Cachorro.id == cachorro_id)
        )
    )
    if excluir_pacote_id is not None:
        query = query.filter(models.Pacote.id != excluir_pacote_id)
    return query.first()


def _validar_sem_pacote_aberto(db: Session, cachorros: List["models.Cachorro"], excluir_pacote_id: Optional[int] = None):
    """
    Garante que nenhum dos cachorros informados já tenha um pacote em aberto
    (regra: um cachorro só pode estar em um pacote em aberto por vez).
    """
    for c in cachorros:
        existente = _pacote_aberto_do_cachorro(db, c.id, excluir_pacote_id)
        if existente:
            raise HTTPException(
                status_code=400,
                detail=f"{c.nome} já possui um pacote em aberto (#{existente.id}). "
                       f"Feche o pacote atual antes de criar um novo para este cachorro."
            )


@router.post("/", response_model=schemas.PacoteResponse, status_code=status.HTTP_201_CREATED)
def criar_pacote(pacote_criar: schemas.PacoteCreate, db: Session = Depends(get_db)):
    """Cria um novo pacote para um cachorro específico."""
    # Verifica se o cachorro existe e é ativo
    cachorro = db.query(models.Cachorro).filter(
        models.Cachorro.id == pacote_criar.cachorro_id,
        models.Cachorro.ativo == True
    ).first()
    if not cachorro:
        raise HTTPException(status_code=404, detail="Cachorro não encontrado ou inativo")

    _validar_sem_pacote_aberto(db, [cachorro])

    # Cria o pacote
    dados_pacote = pacote_criar.model_dump()
    dados_pacote.pop('limite_banhos_mes', None)
    dados_pacote.pop('status_pagamento', None)
    cachorros_adicionais_ids = dados_pacote.pop('cachorros_adicionais_ids', [])
    valores_adicionais = dados_pacote.pop('valores_adicionais', {})

    # Garante que o dia da semana não seja nulo (correção IntegrityError)
    if not dados_pacote.get('dia_da_semana'):
        dados_pacote['dia_da_semana'] = pacote_criar.dia_da_semana or "terca"

    # Garante valor padrão para campos novos caso não venham no schema
    if 'fechado' not in dados_pacote:
        dados_pacote['fechado'] = False

    # Garante que o pacote seja criado como ativo explicitamente
    if 'ativo' not in dados_pacote:
        dados_pacote['ativo'] = True

    # Cachorros adicionais precisam ser do mesmo cliente do cachorro principal,
    # para manter cliente_nome e o fechamento/pagamento do pacote sem ambiguidade.
    cachorros_extras = []
    if cachorros_adicionais_ids:
        ids_unicos = {i for i in cachorros_adicionais_ids if i != cachorro.id}
        if ids_unicos:
            cachorros_extras = db.query(models.Cachorro).filter(
                models.Cachorro.id.in_(ids_unicos),
                models.Cachorro.cliente_id == cachorro.cliente_id
            ).all()
            if len(cachorros_extras) != len(ids_unicos):
                raise HTTPException(
                    status_code=400,
                    detail="Todos os cachorros adicionais devem pertencer ao mesmo cliente do cachorro principal"
                )
            _validar_sem_pacote_aberto(db, cachorros_extras)

    db_pacote = models.Pacote(**dados_pacote)
    if cachorros_extras:
        db_pacote.cachorros_adicionais = cachorros_extras
        # Só persiste valores explicitamente informados; cachorros sem entrada
        # aqui usam valor_banho_base como padrão (calculado em valor_banho_equivalente).
        valores_persistir = {
            str(c.id): valores_adicionais[c.id]
            for c in cachorros_extras
            if c.id in valores_adicionais
        }
        if valores_persistir:
            db_pacote.valores_cachorros = valores_persistir
    db.add(db_pacote)
    db.commit()
    db.refresh(db_pacote)

    # Geração automática de agendamentos para o mês atual, seguindo a mesma
    # regra usada para gerar o pacote do mês seguinte (ver gerar_datas_ciclo).
    hoje = date.today()
    datas_validas = gerar_datas_ciclo(
        db_pacote.tipo_plano.value, db_pacote.dia_da_semana.value, hoje.year, hoje.month
    )

    # Import aqui para evitar dependência circular no carregamento.
    from app.models import Agendamento

    for d in datas_validas:
        db_ag = Agendamento(

            pacote_id=db_pacote.id,
            data_banho=d,
            status_presenca="pendente",
            extras={},
        )
        db.add(db_ag)

    db.commit()
    db.refresh(db_pacote)

    # Retorna pacote com agendamentos carregados (para a resposta do endpoint)
    db_pacote = (
        db.query(models.Pacote)
        .options(
            joinedload(models.Pacote.agendamentos),
            joinedload(models.Pacote.cachorro).joinedload(models.Cachorro.cliente)
        )
        .filter(models.Pacote.id == db_pacote.id)
        .first()
    )

    # Em alguns cenários o FastAPI/Pydantic não consegue serializar diretamente o
    # modelo SQLAlchemy quando há tipos não-mapeados (ex.: relacionamento Agendamento).
    # Então, retornamos explicitamente via dict compatível com PacoteResponse.
    # Para o detalhe, a UI usa PacoteDetail.vue que espera agendamentos no payload.
    # Para compatibilidade com a serialização Pydantic, retornamos somente campos escalares + agendamentos.
    # (PacoteResponse.agendamentos é List[Any], então aceitamos dicts).
    return schemas.PacoteResponse.model_validate(db_pacote).model_dump()



@router.get("/{pacote_id}", response_model=schemas.PacoteResponse)

def obter_pacote(pacote_id: int, db: Session = Depends(get_db)):
    """Obtém detalhes de um pacote específico com agendamentos."""
    pacote = db.query(models.Pacote)\
        .options(
            joinedload(models.Pacote.cachorro).joinedload(models.Cachorro.cliente),
            joinedload(models.Pacote.agendamentos)
        )\
        .filter(models.Pacote.id == pacote_id)\
        .first()
    if not pacote:
        raise HTTPException(status_code=404, detail="Pacote não encontrado")
    
    return schemas.PacoteResponse.model_validate(pacote).model_dump()


@router.put("/{pacote_id}", response_model=schemas.PacoteResponse)
def atualizar_pacote(pacote_id: int, pacote_atualizar: schemas.PacoteUpdate, db: Session = Depends(get_db)):
    """Atualiza dados do pacote."""
    pacote = db.query(models.Pacote).filter(models.Pacote.id == pacote_id).first()
    if not pacote:
        raise HTTPException(status_code=404, detail="Pacote não encontrado")
    
    update_data = pacote_atualizar.model_dump(exclude_unset=True)
    cachorros_adicionais_ids = update_data.pop('cachorros_adicionais_ids', None)
    if 'valores_cachorros' in update_data:
        valores = update_data['valores_cachorros'] or {}
        update_data['valores_cachorros'] = {str(k): v for k, v in valores.items()}
    for field, value in update_data.items():
        setattr(pacote, field, value)

    if cachorros_adicionais_ids is not None:
        ids_unicos = {i for i in cachorros_adicionais_ids if i != pacote.cachorro_id}
        cachorros_extras = []
        if ids_unicos:
            cachorros_extras = db.query(models.Cachorro).filter(
                models.Cachorro.id.in_(ids_unicos),
                models.Cachorro.cliente_id == pacote.cachorro.cliente_id
            ).all()
            if len(cachorros_extras) != len(ids_unicos):
                raise HTTPException(
                    status_code=400,
                    detail="Todos os cachorros adicionais devem pertencer ao mesmo cliente do cachorro principal"
                )
            _validar_sem_pacote_aberto(db, cachorros_extras, excluir_pacote_id=pacote.id)
        pacote.cachorros_adicionais = cachorros_extras

    db.commit()
    db.refresh(pacote)

    return schemas.PacoteResponse.model_validate(pacote).model_dump()

@router.patch("/{pacote_id}/fechar", response_model=schemas.PacoteResponse)
def fechar_pacote(pacote_id: int, db: Session = Depends(get_db)):
    """
    Marca o pacote como fechado (ciclo concluído, aguardando acerto).
    Só permite fechar quando todos os banhos do ciclo já foram resolvidos
    (concluído ou faltou — nenhum pendente).
    """
    pacote = db.query(models.Pacote).options(
        joinedload(models.Pacote.cachorro).joinedload(models.Cachorro.cliente),
        joinedload(models.Pacote.agendamentos)
    ).filter(models.Pacote.id == pacote_id).first()

    if not pacote:
        raise HTTPException(status_code=404, detail="Pacote não encontrado")

    if not pacote.agendamentos:
        raise HTTPException(status_code=400, detail="Este pacote não tem agendamentos para fechar.")

    pendentes = [ag for ag in pacote.agendamentos if ag.status_presenca == "pendente"]
    if pendentes:
        raise HTTPException(
            status_code=400,
            detail=f"Ainda há {len(pendentes)} banho(s) pendente(s). "
                   f"Marque todos como concluído ou faltou antes de fechar o pacote."
        )

    pacote.fechado = True
    db.commit()
    db.refresh(pacote)
    comanda_service.processar_fechamento(db, pacote)
    PacoteService(db).criar_pacote_seguinte(pacote)
    return schemas.PacoteResponse.model_validate(pacote).model_dump()


@router.patch("/{pacote_id}/reabrir", response_model=schemas.PacoteResponse)
def reabrir_pacote(pacote_id: int, db: Session = Depends(get_db)):
    """
    Destrava o pacote (volta fechado=False) para permitir corrigir banhos
    (status, itens extras, datas) esquecidos ou errados. Depois de corrigir,
    o pacote precisa passar pelo fechamento novamente.
    """
    pacote = db.query(models.Pacote).filter(models.Pacote.id == pacote_id).first()
    if not pacote:
        raise HTTPException(status_code=404, detail="Pacote não encontrado")

    pacote.fechado = False
    db.commit()
    db.refresh(pacote)
    return schemas.PacoteResponse.model_validate(pacote).model_dump()


@router.post("/{pacote_id}/enviar-comanda")
def enviar_comanda_manual(pacote_id: int, db: Session = Depends(get_db)):
    """Reenvia a comanda por WhatsApp manualmente (independente do status de fechamento)."""
    pacote = db.query(models.Pacote).options(
        joinedload(models.Pacote.cachorro).joinedload(models.Cachorro.cliente),
        joinedload(models.Pacote.agendamentos)
    ).filter(models.Pacote.id == pacote_id).first()

    if not pacote:
        raise HTTPException(status_code=404, detail="Pacote não encontrado")

    cliente = pacote.cachorro.cliente if pacote.cachorro else None
    if not cliente or not cliente.whatsapp:
        raise HTTPException(status_code=400, detail="Cliente não tem WhatsApp cadastrado.")

    try:
        mensagem = whatsapp_service.formatar_comanda_mensagem(pacote)
        whatsapp_service.enviar_texto(cliente.whatsapp, mensagem)
    except whatsapp_service.WhatsAppNaoConfigurado:
        raise HTTPException(status_code=503, detail="Integração com WhatsApp não configurada.")
    except whatsapp_service.WhatsAppError as e:
        raise HTTPException(status_code=502, detail=f"Falha ao enviar comanda: {e}")

    return {"enviado": True}

@router.delete("/{pacote_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_pacote(
    pacote_id: int, 
    force: bool = Query(False, description="Se True, remove permanentemente do banco"),
    db: Session = Depends(get_db)
):
    """
    Remove pacote. 
    Por padrão realiza soft-delete (ativo=False) e remove agendamentos pendentes da agenda.
    Use force=true para remoção física completa do banco de dados.
    """
    pacote = db.query(models.Pacote).filter(models.Pacote.id == pacote_id).first()
    if not pacote:
        raise HTTPException(status_code=404, detail="Pacote não encontrado")

    if force:
        db.delete(pacote)
    else:
        pacote.ativo = False
        # Ao desativar, limpamos agendamentos futuros que ainda não foram realizados
        db.query(models.Agendamento).filter(
            models.Agendamento.pacote_id == pacote_id,
            models.Agendamento.status_presenca == "pendente"
        ).delete(synchronize_session=False)

    db.commit()
    return None

@router.patch("/{pacote_id}/pagar", response_model=dict)
def registrar_pagamento(
    pacote_id: int,
    dados: dict,  # Aceita payload JSON flexível
    db: Session = Depends(get_db)
):
    """Registra pagamento de um pacote usando o serviço."""
    service = PacoteService(db)

    valor_pago = dados.get("valor_pago")
    data_str = dados.get("data_pagamento")
    tipo = dados.get("tipo_pagamento", "pix")
    fechar = dados.get("fechar_pacote", False)
    observacao = dados.get("observacao")

    if valor_pago is None or data_str in (None, ""):
        raise HTTPException(status_code=400, detail="Valor e data são obrigatórios")

    # Normaliza valor_pago (pode vir como string)
    try:
        valor_pago_float = float(valor_pago)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Valor pago inválido")

    # Normaliza data_pagamento aceitando: YYYY-MM-DD ou ISO completo
    # Ex: 2026-06-29 ou 2026-06-29T10:20:30.000Z
    if isinstance(data_str, str):
        data_str = data_str.strip()

    if not isinstance(data_str, str):
        raise HTTPException(status_code=400, detail="Data do pagamento inválida")

    try:
        data_iso = data_str[:10]  # garante YYYY-MM-DD
        data = date.fromisoformat(data_iso)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data do pagamento inválido. Use YYYY-MM-DD")

    result = service.registrar_pagamento(
        pacote_id,
        valor_pago_float,
        data,
        tipo_pagamento=tipo,
        fechar_pacote=fechar,
        observacao=observacao
    )
    return result


@router.put("/{pacote_id}/pagamentos/{pagamento_id}", response_model=schemas.PagamentoResponse)
def atualizar_pagamento(
    pacote_id: int,
    pagamento_id: int,
    dados: schemas.PagamentoUpdate,
    db: Session = Depends(get_db)
):
    """Edita um pagamento já registrado (valor, data, método ou observação)."""
    pagamento = db.query(models.Pagamento).filter(
        models.Pagamento.id == pagamento_id,
        models.Pagamento.pacote_id == pacote_id
    ).first()
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    update_data = dados.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pagamento, field, value)

    db.commit()
    db.refresh(pagamento)
    return schemas.PagamentoResponse.model_validate(pagamento).model_dump()


@router.delete("/{pacote_id}/pagamentos/{pagamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_pagamento(
    pacote_id: int,
    pagamento_id: int,
    db: Session = Depends(get_db)
):
    """Remove um pagamento registrado (ex.: lançamento feito por engano)."""
    pagamento = db.query(models.Pagamento).filter(
        models.Pagamento.id == pagamento_id,
        models.Pagamento.pacote_id == pacote_id
    ).first()
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    db.delete(pagamento)
    db.commit()
    return None


@router.get("/{pacote_id}/agendamentos", response_model=List[schemas.AgendamentoResponse])
def listar_agendamentos_pacote(pacote_id: int, db: Session = Depends(get_db)):
    """Lista agendamentos vinculados a um pacote específico."""
    agendamentos = db.query(models.Agendamento).filter(
        models.Agendamento.pacote_id == pacote_id
    ).order_by(models.Agendamento.data_banho).all()
    return [schemas.AgendamentoResponse.model_validate(ag).model_dump() for ag in agendamentos]

@router.post("/{pacote_id}/agendamento-extra", response_model=schemas.AgendamentoResponse)
def adicionar_agendamento_extra(
    pacote_id: int, 
    data_banho: str, 
    db: Session = Depends(get_db)
):
    """Cria um agendamento extra sem validar o limite do plano."""
    pacote = db.query(models.Pacote).filter(models.Pacote.id == pacote_id).first()
    if not pacote:
        raise HTTPException(status_code=404, detail="Pacote não encontrado")
    if pacote.fechado:
        raise HTTPException(
            status_code=400,
            detail="Este pacote está fechado. Reabra o pacote para adicionar banhos."
        )

    db_ag = models.Agendamento(
        pacote_id=pacote_id,
        data_banho=date.fromisoformat(data_banho),
        status_presenca="pendente"
    )
    db.add(db_ag)
    db.commit()
    db.refresh(db_ag)
    return schemas.AgendamentoResponse.model_validate(db_ag).model_dump()
