"""
Serviço de integração com o Evolution API (WhatsApp self-hosted).

Responsável por:
- Formatar a mensagem de comanda (pacote fechado) enviada ao cliente.
- Criar/gerenciar a instância do WhatsApp (QR code, status de conexão).
- Enviar mensagens de texto via WhatsApp.

Todas as chamadas HTTP são best-effort: falhas aqui nunca devem derrubar o
fluxo principal do app (ex.: fechar um pacote continua funcionando mesmo se
o WhatsApp estiver desconectado).
"""
import logging
import re
from typing import Any, Dict, Optional

import httpx

from app.database import settings

logger = logging.getLogger(__name__)


class WhatsAppNaoConfigurado(Exception):
    """Levantada quando EVOLUTION_API_URL/KEY não estão configurados."""


class WhatsAppError(Exception):
    """Levantada quando a chamada ao Evolution API falha."""


def _client() -> httpx.Client:
    if not settings.EVOLUTION_API_URL or not settings.EVOLUTION_API_KEY:
        raise WhatsAppNaoConfigurado(
            "EVOLUTION_API_URL e EVOLUTION_API_KEY precisam estar configurados."
        )
    return httpx.Client(
        base_url=settings.EVOLUTION_API_URL,
        headers={"apikey": settings.EVOLUTION_API_KEY},
        timeout=15.0,
    )


def _instance() -> str:
    return settings.EVOLUTION_INSTANCE_NAME


def normalizar_numero(numero: str) -> str:
    """
    Remove tudo que não for dígito e garante o código do país (55 = Brasil)
    quando o número informado não tiver DDI. Evolution API espera formato
    '55DDDNUMERO' (ex.: 5547989036464).
    """
    digitos = re.sub(r"\D", "", numero or "")
    if not digitos:
        return ""
    if not digitos.startswith("55"):
        digitos = "55" + digitos
    return digitos


def garantir_instancia() -> Dict[str, Any]:
    """
    Cria a instância no Evolution API caso ainda não exista. Idempotente:
    se já existir, o Evolution API retorna erro que tratamos como sucesso.
    """
    with _client() as client:
        resp = client.post(
            "/instance/create",
            json={
                "instanceName": _instance(),
                "integration": "WHATSAPP-BAILEYS",
                "qrcode": True,
            },
        )
        # 403/400 aqui geralmente significa "instância já existe" - não é erro fatal.
        if resp.status_code not in (200, 201, 400, 403):
            raise WhatsAppError(f"Falha ao criar instância: {resp.status_code} {resp.text}")
        return {"status_code": resp.status_code}


def obter_qrcode() -> Dict[str, Any]:
    """Retorna o QR code (base64) para conectar o WhatsApp, se ainda não conectado."""
    garantir_instancia()
    with _client() as client:
        resp = client.get(f"/instance/connect/{_instance()}")
        if resp.status_code != 200:
            raise WhatsAppError(f"Falha ao obter QR code: {resp.status_code} {resp.text}")
        data = resp.json()
        # Evolution API retorna 'base64' (data:image/png;base64,...) quando desconectado,
        # ou dados de instância já conectada (sem QR) quando já autenticado.
        return {
            "qrcode_base64": data.get("base64"),
            "pairing_code": data.get("pairingCode"),
            "raw": data,
        }


def obter_status() -> Dict[str, Any]:
    """Consulta o estado de conexão da instância (open, connecting, close)."""
    with _client() as client:
        resp = client.get(f"/instance/connectionState/{_instance()}")
        if resp.status_code == 404:
            return {"state": "not_created"}
        if resp.status_code != 200:
            raise WhatsAppError(f"Falha ao consultar status: {resp.status_code} {resp.text}")
        data = resp.json()
        estado = data.get("instance", {}).get("state") or data.get("state")
        return {"state": estado, "raw": data}


def enviar_texto(numero: str, texto: str) -> Dict[str, Any]:
    """Envia uma mensagem de texto simples via WhatsApp."""
    numero_normalizado = normalizar_numero(numero)
    if not numero_normalizado:
        raise WhatsAppError("Número de WhatsApp inválido ou vazio.")

    with _client() as client:
        resp = client.post(
            f"/message/sendText/{_instance()}",
            json={"number": numero_normalizado, "text": texto},
        )
        if resp.status_code not in (200, 201):
            raise WhatsAppError(f"Falha ao enviar mensagem: {resp.status_code} {resp.text}")
        return resp.json()


_STATUS_LABELS = {
    "em_aberto": "Em Aberto",
    "pago": "Pago",
    "parcial": "Parcial",
    "atrasado": "Atrasado",
    "fechado": "Fechado",
}

_MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def montar_dados_comanda(pacote) -> Dict[str, Any]:
    """
    Reúne os dados da comanda (pacote fechado) num formato estruturado,
    reaproveitado tanto pela mensagem de WhatsApp quanto pela comanda impressa
    (PDF): pet/cliente, mês do ciclo, uma linha por banho concluído
    (data + valor + item extra, se houver), transporte e total.
    """
    agendamentos_concluidos = [
        ag for ag in sorted(pacote.agendamentos, key=lambda a: a.data_banho)
        if ag.status_presenca == "concluido"
    ]

    mes_label = None
    if agendamentos_concluidos:
        primeira_data = agendamentos_concluidos[0].data_banho
        mes_label = f"{_MESES[primeira_data.month - 1]}/{primeira_data.year}"

    # Em pacotes multi-cachorro cada pet pode ter faltado individualmente, então
    # o valor do dia vem de valor_banho_dia (só os pets que tomaram banho).
    total_cachorros = len(pacote.cachorros_todos)

    linhas_banhos = []
    for ag in agendamentos_concluidos:
        valor_extra = (ag.extras or {}).get("valor_extra", 0) or 0
        presentes = ag.cachorros_presentes
        linhas_banhos.append({
            "data": ag.data_banho,
            "valor": ag.valor_banho_dia,
            "extra_info": (ag.extras or {}).get("info") if valor_extra else None,
            "extra_valor": valor_extra,
            # Só descreve quais pets vieram quando o pacote tem mais de um e
            # nem todos tomaram banho nesse dia.
            "pets": presentes if total_cachorros > 1 and len(presentes) < total_cachorros else [],
            "qtd_pets": len(presentes) if total_cachorros > 1 else 1,
        })

    return {
        "pet_nome": pacote.pet_nome or "Pacote",
        "cliente_nome": pacote.cliente_nome,
        "mes_label": mes_label,
        "banhos": linhas_banhos,
        "transporte": pacote.valor_transporte or 0.0,
        "total": pacote.valor_cobrado,
        "status_label": _STATUS_LABELS.get(pacote.status_pagamento, pacote.status_pagamento),
    }


def formatar_comanda_mensagem(pacote) -> str:
    """
    Monta o texto da comanda (pacote fechado) no mesmo formato exibido na
    página de detalhes do cliente: datas + valor de cada banho, transporte e
    total, com o status de pagamento.
    """
    dados = montar_dados_comanda(pacote)

    linhas = [
        "🐾 *Recanto Mini Dogs*",
        f"Comanda — {dados['pet_nome']}",
        "",
    ]

    if dados["banhos"]:
        linhas.append(f"📅 {dados['mes_label']}")
        for banho in dados["banhos"]:
            data_fmt = banho["data"].strftime("%d/%m/%Y")
            linha = f"{data_fmt} — R$ {banho['valor']:.2f}".replace(".", ",")
            if banho["pets"]:
                linha += f" ({', '.join(banho['pets'])})"
            if banho["extra_valor"]:
                linha += f" + {banho['extra_info'] or 'extra'} R$ {banho['extra_valor']:.2f}".replace(".", ",")
            linhas.append(linha)
    else:
        linhas.append("Nenhum banho concluído neste ciclo.")

    if dados["transporte"]:
        linhas.append(f"🚗 Transporte: R$ {dados['transporte']:.2f}".replace(".", ","))

    linhas.append("")
    linhas.append(f"💰 *Total: R$ {dados['total']:.2f}*".replace(".", ","))
    return "\n".join(linhas)


def enviar_comanda_se_configurado(pacote) -> None:
    """
    Envia a comanda por WhatsApp se o cliente do pacote tiver essa preferência
    configurada (envio_comanda == 'whatsapp') e um número cadastrado.
    Best-effort: qualquer falha (WhatsApp desconectado, número inválido, etc.)
    é apenas logada, nunca interrompe o fluxo que chamou esta função (ex.:
    fechamento manual ou automático de um pacote).
    """
    cliente = pacote.cachorro.cliente if pacote.cachorro else None
    if not cliente or cliente.envio_comanda != "whatsapp" or not cliente.whatsapp:
        return
    try:
        mensagem = formatar_comanda_mensagem(pacote)
        enviar_texto(cliente.whatsapp, mensagem)
    except Exception as e:
        logger.warning(f"Falha ao enviar comanda por WhatsApp (pacote {pacote.id}): {e}")
