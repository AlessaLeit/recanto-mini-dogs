"""
Serviço de Pacote - Contém regras de negócio específicas.
Validação de limites de banhos por plano.
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract, and_, or_
from fastapi import HTTPException
from typing import List, Optional
from datetime import date, timedelta
import calendar
from app.models import Pacote, Banho, Agendamento, Cachorro, Cliente, TipoPlano
from app.services import whatsapp_service


_MAPA_DIA_SEMANA = {
    "terca": 1,   # Segunda=0
    "quarta": 2,
    "quinta": 3,
    "sexta": 4,
    "sabado": 5,
}


def gerar_datas_ciclo(tipo_plano: str, dia_da_semana: str, ano: int, mes: int) -> List[date]:
    """
    Gera as datas de banho de um ciclo mensal para um dia da semana fixo,
    dentro dos limites do mês/ano informado.
    - Semanal: até 4 datas (a cada 7 dias a partir da 1ª ocorrência no mês)
    - Quinzenal: até 2 datas (a cada 15 dias)
    - Mensal: 1 data (1ª ocorrência no mês)
    A quantidade real pode variar (ex.: menos de 4 datas semanais) quando a
    1ª ocorrência do dia da semana cai perto do fim do mês.
    """
    primeiro_dia_mes = date(ano, mes, 1)
    ultimo_dia_mes = date(ano, mes, calendar.monthrange(ano, mes)[1])

    alvo_dow = _MAPA_DIA_SEMANA.get(dia_da_semana)
    if alvo_dow is None:
        return []

    d = primeiro_dia_mes
    primeira = None
    while d <= ultimo_dia_mes:
        if d.weekday() == alvo_dow:
            primeira = d
            break
        d += timedelta(days=1)

    if not primeira:
        return []

    if tipo_plano == "semanal":
        datas = [primeira + timedelta(days=7 * i) for i in range(4)]
    elif tipo_plano == "quinzenal":
        datas = [primeira + timedelta(days=15 * i) for i in range(2)]
    elif tipo_plano == "mensal":
        datas = [primeira]
    else:
        datas = []

    return [d for d in datas if primeiro_dia_mes <= d <= ultimo_dia_mes]


class PacoteService:    
    """
    Serviço para gerenciar lógica de negócios de pacotes.
    Principal responsabilidade: validar limites de banhos por plano.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def contar_banhos_no_mes(self, pacote_id: int, ano: int, mes: int) -> int:
        """
        Conta quantos banhos foram realizados no mês/ano especificado.
        """
        return self.db.query(Banho).filter(
            and_(
                Banho.pacote_id == pacote_id,
                extract('year', Banho.data_banho) == ano,
                extract('month', Banho.data_banho) == mes
            )
        ).count()
    
    def validar_limite_banhos(
        self, 
        pacote_id: int, 
        data_banho: date
    ) -> None:
        """
        Valida se ainda é possível registrar um banho no pacote para a data especificada.
        """
        pacote = self.db.query(Pacote).filter(Pacote.id == pacote_id).first()
        if not pacote:
            raise HTTPException(status_code=404, detail="Pacote não encontrado")
        
        if not pacote.ativo:
            raise HTTPException(status_code=400, detail="Nao e possivel adicionar banho a um pacote inativo")
        
        limite = pacote.limite_banhos_mes
        
        total_banhos = self.contar_banhos_no_mes(
            pacote_id, 
            data_banho.year, 
            data_banho.month
        )
        
        if total_banhos >= limite:
            raise HTTPException(
                status_code=400,
                detail=f"Limite de banhos excedido para o plano {pacote.tipo_plano.value}. Maximo permitido: {limite} banhos/mes. Ja realizados: {total_banhos} banhos em {data_banho.month:02d}/{data_banho.year}."
            )
    
    def validar_limite_agendamentos(
        self, 
        pacote_id: int, 
        data_banho: date
    ) -> None:
        """
        Valida limites para agendamentos (conta agendamentos no mes).
        """
        pacote = self.db.query(Pacote).filter(Pacote.id == pacote_id).first()
        if not pacote:
            raise HTTPException(status_code=404, detail="Pacote nao encontrado")
        
        if not pacote.ativo:
            raise HTTPException(status_code=400, detail="Pacote inativo")
        
        total_agendamentos = self.db.query(Agendamento).filter(
            and_(
                Agendamento.pacote_id == pacote_id,
                extract('year', Agendamento.data_banho) == data_banho.year,
                extract('month', Agendamento.data_banho) == data_banho.month
            )
        ).count()
        
        limite = pacote.limite_banhos_mes
        
        if total_agendamentos >= limite:
            raise HTTPException(
                status_code=400,
                detail=f"Limite de agendamentos excedido ({limite}). Ja existem {total_agendamentos} no mes."
            )
    
    def registrar_pagamento(
        self,
        pacote_id: int,
        valor_pago: float,
        data_pagamento: date,
        tipo_pagamento: Optional[str] = "pix",
        fechar_pacote: bool = False,
        observacao: Optional[str] = None
    ) -> dict:
        pacote = self.db.query(Pacote).options(
            joinedload(Pacote.cachorro).joinedload(Cachorro.cliente),
            joinedload(Pacote.pagamentos)
        ).filter(Pacote.id == pacote_id).first()

        if not pacote:
            raise HTTPException(status_code=404, detail="Pacote não encontrado")

        # Import local para evitar circularidade se necessário
        from app.models.pacote import Pagamento, TipoPagamento

        # Criar novo registro de pagamento
        novo_pagamento = Pagamento(
            pacote_id=pacote_id,
            valor_pago=valor_pago,
            data_pagamento=data_pagamento,
            tipo_pagamento=tipo_pagamento,
            observacao=observacao
        )
        self.db.add(novo_pagamento)

        # Se solicitado fechar o pacote
        if fechar_pacote:
            pacote.fechado = True

        self.db.commit()
        self.db.refresh(pacote)

        if fechar_pacote:
            whatsapp_service.enviar_comanda_se_configurado(pacote)
            self.criar_pacote_seguinte(pacote)

        return pacote.to_dict()

    def fechar_se_completo(self, pacote_id: int) -> Optional[Pacote]:
        """
        Fecha o pacote automaticamente quando todos os agendamentos do ciclo já
        foram resolvidos (concluído ou faltou — nenhum mais pendente). Ao
        fechar, envia a comanda por WhatsApp se o cliente tiver essa
        preferência configurada.

        Retorna o pacote se ele acabou de ser fechado por esta chamada, ou
        None se não havia nada a fazer (já fechado, inativo, sem agendamentos,
        ou ainda com agendamentos pendentes).
        """
        pacote = self.db.query(Pacote).options(
            joinedload(Pacote.cachorro).joinedload(Cachorro.cliente),
            joinedload(Pacote.agendamentos)
        ).filter(Pacote.id == pacote_id).first()

        if not pacote or not pacote.ativo or pacote.fechado:
            return None

        agendamentos = pacote.agendamentos
        if not agendamentos:
            return None

        if any(ag.status_presenca == "pendente" for ag in agendamentos):
            return None

        pacote.fechado = True
        self.db.commit()
        self.db.refresh(pacote)

        whatsapp_service.enviar_comanda_se_configurado(pacote)
        self.criar_pacote_seguinte(pacote)
        return pacote

    def criar_pacote_seguinte(self, pacote_fechado: Pacote) -> Optional[Pacote]:
        """
        Ao fechar um pacote, cria automaticamente o pacote do próximo mês para
        o(s) mesmo(s) cachorro(s), repetindo a configuração (plano, dia da
        semana, valores por cachorro). A quantidade de banhos e o valor
        cobrado se ajustam ao número real de ocorrências daquele dia da
        semana no novo mês (varia de mês para mês).

        Retorna o novo pacote criado, ou None se não havia nada a fazer
        (cachorro inativo, já existe um pacote em aberto para ele, ou o mês
        seguinte não tem nenhuma data válida para o dia da semana configurado).
        """
        cachorro_principal = pacote_fechado.cachorro
        if not cachorro_principal or not cachorro_principal.ativo:
            return None

        # Evita duplicar: se qualquer cachorro do pacote (principal ou
        # adicional) já tem um pacote em aberto, não cria outro. Isso também
        # protege contra fechar → reabrir → fechar de novo criando duplicatas.
        for c in pacote_fechado.cachorros_todos:
            conflito = self.db.query(Pacote).filter(
                Pacote.ativo == True,
                Pacote.fechado == False,
                or_(
                    Pacote.cachorro_id == c.id,
                    Pacote.cachorros_adicionais.any(Cachorro.id == c.id)
                )
            ).first()
            if conflito:
                return None

        # Usa a última data do ciclo que fechou como referência (não a data de
        # hoje), para manter a sequência correta mesmo se o fechamento for
        # feito com atraso.
        datas_ciclo_anterior = [ag.data_banho for ag in pacote_fechado.agendamentos]
        referencia = max(datas_ciclo_anterior) if datas_ciclo_anterior else date.today()
        ano, mes = referencia.year, referencia.month
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1

        datas = gerar_datas_ciclo(
            pacote_fechado.tipo_plano.value,
            pacote_fechado.dia_da_semana.value,
            ano, mes
        )
        if not datas:
            return None

        cachorros_adicionais = list(pacote_fechado.cachorros_adicionais or [])
        valores_cachorros = dict(pacote_fechado.valores_cachorros or {})

        valor_por_banho = pacote_fechado.valor_banho_base or 0.0
        for c in cachorros_adicionais:
            valor_custom = valores_cachorros.get(str(c.id))
            valor_por_banho += valor_custom if valor_custom is not None else (pacote_fechado.valor_banho_base or 0.0)
        valor_cobrado = (valor_por_banho * len(datas)) + (pacote_fechado.valor_transporte or 0.0)

        novo_pacote = Pacote(
            cachorro_id=pacote_fechado.cachorro_id,
            tipo_plano=pacote_fechado.tipo_plano,
            dia_da_semana=pacote_fechado.dia_da_semana,
            valor_banho_base=pacote_fechado.valor_banho_base,
            valor_cobrado=valor_cobrado,
            valor_transporte=pacote_fechado.valor_transporte or 0.0,
            valores_cachorros=valores_cachorros or None,
            fechado=False,
            ativo=True,
        )
        self.db.add(novo_pacote)
        self.db.flush()

        if cachorros_adicionais:
            novo_pacote.cachorros_adicionais = cachorros_adicionais

        for d in datas:
            self.db.add(Agendamento(
                pacote_id=novo_pacote.id,
                data_banho=d,
                status_presenca="pendente",
                extras={},
            ))

        self.db.commit()
        self.db.refresh(novo_pacote)
        return novo_pacote