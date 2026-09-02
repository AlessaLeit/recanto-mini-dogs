"""
Serviço de Relatórios - Gera métricas mensais do negócio.
Calcula receitas, banhos realizados e pacotes em aberto.
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract, func, and_
from typing import List, Dict, Any
from datetime import date, datetime
import calendar
from app.models import Pacote, Cachorro, Agendamento, Pagamento


class RelatorioService:
    """
    Serviço para geração de relatórios mensais.
    """

    def __init__(self, db: Session):
        self.db = db

    def gerar_relatorio_mensal(self, ano: int, mes: int) -> Dict[str, Any]:
        """
        Gera relatório completo para um mês/ano específico.
        """
        # 1. Total de banhos realizados no mês (agendamentos concluídos)
        total_banhos = self._contar_banhos_mes(ano, mes)

        # 2. Receita prevista (soma de valor_cobrado de pacotes ativos até o mês)
        receita_prevista = self._calcular_receita_prevista(ano, mes)

        # 3. Receita recebida (soma dos pagamentos registrados no mês)
        receita_recebida = self._calcular_receita_recebida(ano, mes)

        # 4. Pacotes em aberto (ativos com saldo devedor)
        pacotes_em_aberto = self._listar_pacotes_em_aberto()

        # 5. Agendamentos com observações no período
        banhos_com_observacoes = self._listar_banhos_com_observacoes(ano, mes)

        return {
            "periodo": {
                "ano": ano,
                "mes": mes,
                "nome_mes": self._nome_mes(mes)
            },
            "resumo": {
                "total_banhos_realizados": total_banhos,
                "receita_prevista": round(receita_prevista, 2),
                "receita_recebida": round(receita_recebida, 2),
                "receita_pendente": round(receita_prevista - receita_recebida, 2),
                "taxa_recebimento": round(
                    (receita_recebida / receita_prevista * 100) if receita_prevista > 0 else 0,
                    2
                ),
                "total_pacotes_em_aberto": len(pacotes_em_aberto)
            },
            "detalhes": {
                "pacotes_em_aberto": pacotes_em_aberto,
                "banhos_com_observacoes": banhos_com_observacoes
            }
        }

    def _contar_banhos_mes(self, ano: int, mes: int) -> int:
        """Conta agendamentos concluídos no mês."""
        return self.db.query(Agendamento).filter(
            and_(
                extract('year', Agendamento.data_banho) == ano,
                extract('month', Agendamento.data_banho) == mes,
                Agendamento.status_presenca == 'concluido'
            )
        ).count()

    def _calcular_receita_prevista(self, ano: int, mes: int) -> float:
        """Calcula receita prevista baseada em pacotes ativos criados até o fim do mês."""
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        limite = datetime(ano, mes, ultimo_dia, 23, 59, 59)

        pacotes = self.db.query(Pacote).filter(
            and_(
                Pacote.ativo == True,
                Pacote.criado_em <= limite
            )
        ).all()

        return sum(p.valor_cobrado for p in pacotes)

    def _calcular_receita_recebida(self, ano: int, mes: int) -> float:
        """Calcula receita efetivamente recebida no mês (soma dos pagamentos registrados)."""
        resultado = self.db.query(
            func.coalesce(func.sum(Pagamento.valor_pago), 0.0)
        ).filter(
            and_(
                extract('year', Pagamento.data_pagamento) == ano,
                extract('month', Pagamento.data_pagamento) == mes
            )
        ).scalar()

        return float(resultado) if resultado else 0.0

    def _listar_pacotes_em_aberto(self) -> List[Dict[str, Any]]:
        """Lista pacotes ativos com saldo devedor (em aberto, parcial ou atrasado)."""
        pacotes = self.db.query(Pacote).options(
            joinedload(Pacote.cachorro).joinedload(Cachorro.cliente)
        ).filter(Pacote.ativo == True).order_by(Pacote.criado_em.desc()).all()

        resultado = []
        for p in pacotes:
            if p.status_pagamento not in ("em_aberto", "parcial", "atrasado"):
                continue
            resultado.append({
                "pacote_id": p.id,
                "tipo_plano": p.tipo_plano.value,
                "valor_cobrado": p.valor_cobrado,
                "valor_pago": p.valor_pago_total,
                "status_pagamento": p.status_pagamento,
                "criado_em": p.criado_em.isoformat(),
                "cachorro": {
                    "id": p.cachorro.id,
                    "nome": p.cachorro.nome,
                    "porte": p.cachorro.porte.value
                },
                "cliente": {
                    "id": p.cachorro.cliente.id,
                    "nome": p.cachorro.cliente.nome,
                    "whatsapp": p.cachorro.cliente.whatsapp
                }
            })

        return resultado

    def _listar_banhos_com_observacoes(self, ano: int, mes: int) -> List[Dict[str, Any]]:
        """Lista agendamentos do mês que possuem observações (itens extra) registradas."""
        agendamentos = self.db.query(Agendamento).options(
            joinedload(Agendamento.pacote).joinedload(Pacote.cachorro)
        ).filter(
            and_(
                extract('year', Agendamento.data_banho) == ano,
                extract('month', Agendamento.data_banho) == mes
            )
        ).order_by(Agendamento.data_banho.desc()).all()

        resultado = []
        for ag in agendamentos:
            info = (ag.extras or {}).get("info") if isinstance(ag.extras, dict) else None
            if not info:
                continue
            resultado.append({
                "banho_id": ag.id,
                "data_banho": ag.data_banho.isoformat(),
                "observacao": info,
                "cachorro": {
                    "id": ag.pacote.cachorro.id,
                    "nome": ag.pacote.cachorro.nome
                },
                "pacote": {
                    "id": ag.pacote.id,
                    "tipo_plano": ag.pacote.tipo_plano.value
                }
            })

        return resultado

    def _nome_mes(self, mes: int) -> str:
        """Retorna nome do mês em português."""
        meses = [
            "Janeiro", "Fevereiro", "Março", "Abril",
            "Maio", "Junho", "Julho", "Agosto",
            "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        return meses[mes - 1] if 1 <= mes <= 12 else "Desconhecido"
