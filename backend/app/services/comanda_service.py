"""
Serviço de despacho e impressão de comandas (pacote fechado).

Ao fechar um pacote:
- Cliente com envio_comanda='whatsapp' -> envia a mensagem via Evolution API.
- Cliente com envio_comanda='impresso' -> entra na fila de impressão
  (tabela ComandaImpressao), acumulando até o dono gerar o PDF em lote.
"""
import io
import logging
import os
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.models import ComandaImpressao, Pacote, Cachorro
from app.services import whatsapp_service

logger = logging.getLogger(__name__)

_LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.jpg")
_logo_reader: Optional[ImageReader] = None
_logo_carregado = False


def _obter_logo() -> Optional[ImageReader]:
    """Carrega a logo uma única vez (cacheada em memória entre requisições)."""
    global _logo_reader, _logo_carregado
    if not _logo_carregado:
        _logo_carregado = True
        if os.path.exists(_LOGO_PATH):
            try:
                _logo_reader = ImageReader(_LOGO_PATH)
            except Exception as e:
                logger.warning(f"Falha ao carregar logo do canil ({_LOGO_PATH}): {e}")
    return _logo_reader


def processar_fechamento(db: Session, pacote: Pacote) -> None:
    """
    Despacha a comanda de um pacote recém-fechado conforme a preferência do
    cliente. Best-effort: nunca interrompe o fluxo de fechamento do pacote.
    """
    cliente = pacote.cachorro.cliente if pacote.cachorro else None
    if not cliente:
        return

    if cliente.envio_comanda == "whatsapp":
        whatsapp_service.enviar_comanda_se_configurado(pacote)
    else:
        try:
            db.add(ComandaImpressao(pacote_id=pacote.id))
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Falha ao enfileirar comanda para impressão (pacote {pacote.id}): {e}")


def listar_pendentes(db: Session) -> List[ComandaImpressao]:
    """Lista comandas na fila que ainda não foram impressas, mais antigas primeiro."""
    return (
        db.query(ComandaImpressao)
        .options(
            joinedload(ComandaImpressao.pacote).joinedload(Pacote.cachorro).joinedload(Cachorro.cliente),
            joinedload(ComandaImpressao.pacote).joinedload(Pacote.agendamentos),
        )
        .filter(ComandaImpressao.impresso_em.is_(None))
        .order_by(ComandaImpressao.criado_em)
        .all()
    )


# A4 em pontos (reportlab): ~595 x 842. Cada comanda ocupa 1/4 da página (2x2),
# do tamanho aproximado de uma folha A6 - compacto o bastante pra corte.
_PAGE_W, _PAGE_H = A4
_QUAD_W, _QUAD_H = _PAGE_W / 2, _PAGE_H / 2
_MARGEM = 10

# Letreiro fixo do canil (mesmo texto do talão de pedido em papel).
_NOME_CANIL = "Canil Recanto Mini Dogs"
_PIX_CPF = "Chave Pix - CPF 757.124.909-00"
_TELEFONE = "WhatsApp (47) 98868-6391"
_ENDERECO_L1 = "Av. Expedicionarios, 2479 - Campo D'Agua Verde"
_ENDERECO_L2 = "CEP 89466-434 - Canoinhas/SC"

# Larguras proporcionais das colunas da tabela: Qtd | Descrição | V.Unid | Total
_COL_PROP = [0.12, 0.50, 0.19, 0.19]


def _montar_linhas_tabela(dados: dict) -> List[tuple]:
    """Converte os banhos/transporte da comanda em linhas (qtd, descricao, v_unid, total)."""
    linhas = []
    for banho in dados["banhos"]:
        data_fmt = banho["data"].strftime("%d/%m")
        qtd = banho.get("qtd_pets") or 1
        desc = f"Banho - {data_fmt}"
        # Pacote multi-cachorro em que só parte dos pets tomou banho: nomeia quem veio.
        if banho.get("pets"):
            desc += f" ({', '.join(banho['pets'])})"
        # V.Unid. é o valor por pet do dia; o total da linha soma todos os pets.
        linhas.append((str(qtd), desc, banho["valor"] / qtd if qtd else banho["valor"], banho["valor"]))
        if banho["extra_valor"]:
            desc = banho["extra_info"] or "Item extra"
            linhas.append(("1", f"{desc} - {data_fmt}", banho["extra_valor"], banho["extra_valor"]))
    if dados["transporte"]:
        linhas.append(("1", "Transporte", dados["transporte"], dados["transporte"]))
    return linhas


def _fmt_moeda(v: float) -> str:
    return f"{v:.2f}".replace(".", ",")


def _desenhar_comanda(c: canvas.Canvas, x: float, y: float, dados: dict) -> None:
    """
    Desenha uma comanda no quadrante (origem inferior-esquerda x, y), no estilo
    do talão de pedido em papel do canil: cabeçalho com logo + dados do
    negócio, cliente/data, tabela de itens e Total/Assinatura.
    """
    pad = _MARGEM
    inner_x = x + pad
    inner_w = _QUAD_W - 2 * pad
    top = y + _QUAD_H - pad

    # Moldura de corte (tracejada)
    c.saveState()
    c.setDash(3, 3)
    c.setLineWidth(0.5)
    c.rect(x + 4, y + 4, _QUAD_W - 8, _QUAD_H - 8)
    c.restoreState()

    # --- Cabeçalho: nome do canil (topo, largura toda) + logo/Pix/WhatsApp/endereço ---
    logo = _obter_logo()
    logo_lado = 36
    gap_logo = 8
    texto_x = inner_x + (logo_lado + gap_logo if logo else 0)

    linha_gap = 13
    header_top = top - 2
    c.setFont("Helvetica-Bold", 14)
    c.drawString(inner_x, header_top - 12, _NOME_CANIL)

    divisor_y = header_top - 19
    c.setLineWidth(0.5)
    c.line(inner_x, divisor_y, inner_x + inner_w, divisor_y)

    info_y = divisor_y - 11
    c.setFont("Helvetica", 9.5)
    for linha in (_PIX_CPF, _TELEFONE, _ENDERECO_L1, _ENDERECO_L2):
        c.drawString(texto_x, info_y, linha)
        info_y -= linha_gap
    header_bottom = info_y + linha_gap - 3  # fundo aproximado da última linha

    if logo:
        bloco_h = divisor_y - header_bottom
        logo_y = header_bottom + (bloco_h - logo_lado) / 2
        c.drawImage(
            logo, inner_x, logo_y, width=logo_lado, height=logo_lado,
            preserveAspectRatio=True, mask="auto"
        )

    cursor = header_bottom - 6
    c.setLineWidth(0.8)
    c.line(inner_x, cursor, inner_x + inner_w, cursor)
    cursor -= 14

    # --- Cliente (esquerda) / Data (direita) ---
    c.setFont("Helvetica", 11)
    c.drawString(inner_x, cursor, f"Sr.(a): {dados['cliente_nome'] or ''}")
    c.drawRightString(inner_x + inner_w, cursor, f"Data: {dados['data_fmt']}")
    cursor -= 8

    c.setLineWidth(0.5)
    c.line(inner_x, cursor, inner_x + inner_w, cursor)
    cursor -= 4

    # --- Tabela de itens (Qtd | Descrição | V.Unid | Total) ---
    col_w = [inner_w * p for p in _COL_PROP]
    col_x = [inner_x]
    for w in col_w[:-1]:
        col_x.append(col_x[-1] + w)

    row_h = 17
    tabela_top = cursor
    c.setLineWidth(0.6)
    c.line(inner_x, tabela_top, inner_x + inner_w, tabela_top)

    c.setFont("Helvetica-Bold", 10)
    headers = ["Qtd.", "Descricao", "V.Unid.", "Total"]
    for cx, htext in zip(col_x, headers):
        c.drawString(cx + 3, tabela_top - 12, htext)
    cursor = tabela_top - row_h
    c.line(inner_x, cursor, inner_x + inner_w, cursor)

    # Reserva espaço pro rodapé (Total + Assinatura, agora numa única linha) antes de estourar o quadrante.
    limite_y = y + pad + 18
    c.setFont("Helvetica", 10)
    for qtd, desc, v_unid, v_total in _montar_linhas_tabela(dados):
        if cursor - row_h < limite_y:
            break
        c.drawString(col_x[0] + 3, cursor - 12, qtd)
        c.drawString(col_x[1] + 3, cursor - 12, desc[:40])
        c.drawRightString(col_x[3] - 2, cursor - 12, _fmt_moeda(v_unid))
        c.drawRightString(col_x[3] + col_w[3] - 3, cursor - 12, _fmt_moeda(v_total))
        cursor -= row_h
        c.line(inner_x, cursor, inner_x + inner_w, cursor)

    # Preenche o restante da tabela com linhas em branco até chegar perto do rodapé,
    # igual ao talão de papel (que tem a grade toda pré-impressa).
    while cursor - row_h >= limite_y:
        cursor -= row_h
        c.line(inner_x, cursor, inner_x + inner_w, cursor)

    # Linhas verticais separando as colunas da tabela
    c.setLineWidth(0.4)
    for cx in col_x[1:]:
        c.line(cx, tabela_top, cx, cursor)
    c.line(inner_x + inner_w, tabela_top, inner_x + inner_w, cursor)
    c.line(inner_x, tabela_top, inner_x, cursor)

    # --- Total + Assinatura ---
    rodape_y = y + pad
    c.setFont("Helvetica", 10)
    c.drawString(inner_x, rodape_y, "Ass: ________________________")
    c.setFont("Helvetica-Bold", 13)
    c.drawRightString(inner_x + inner_w, rodape_y, f"Total R$ {_fmt_moeda(dados['total'])}")


_QUADRANTES = [
    (0, _QUAD_H),          # topo-esquerda
    (_QUAD_W, _QUAD_H),    # topo-direita
    (0, 0),                # baixo-esquerda
    (_QUAD_W, 0),          # baixo-direita
]


def _montar_dados_impressao(item: ComandaImpressao) -> dict:
    """Combina os dados da comanda com a data de impressão."""
    dados = whatsapp_service.montar_dados_comanda(item.pacote)
    dados["data_fmt"] = datetime.now().strftime("%d/%m/%Y")
    return dados


def gerar_pdf(comandas: List[ComandaImpressao]) -> bytes:
    """Gera o PDF com até 4 comandas por página A4 (grade 2x2)."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    for i, item in enumerate(comandas):
        pos_na_pagina = i % 4
        if pos_na_pagina == 0 and i > 0:
            c.showPage()
        qx, qy = _QUADRANTES[pos_na_pagina]
        dados = _montar_dados_impressao(item)
        _desenhar_comanda(c, qx, qy, dados)

    c.save()
    buffer.seek(0)
    return buffer.read()


def _dados_exemplo() -> dict:
    """Dados fictícios só para visualizar o modelo da comanda impressa (não toca no banco)."""
    from datetime import date
    hoje = datetime.now()
    ultimo_dia = 28 if hoje.month == 2 else 30 if hoje.month in (4, 6, 9, 11) else 31
    datas = [min(d, ultimo_dia) for d in (7, 14, 21, 28)]

    banhos = [
        {"data": date(hoje.year, hoje.month, datas[0]), "valor": 25.0, "extra_info": None, "extra_valor": 0},
        {"data": date(hoje.year, hoje.month, datas[1]), "valor": 25.0, "extra_info": "Tosa higienica", "extra_valor": 15.0},
        {"data": date(hoje.year, hoje.month, datas[2]), "valor": 25.0, "extra_info": None, "extra_valor": 0},
        {"data": date(hoje.year, hoje.month, datas[3]), "valor": 25.0, "extra_info": None, "extra_valor": 0},
    ]
    transporte = 10.0
    total = sum(b["valor"] + b["extra_valor"] for b in banhos) + transporte

    return {
        "pet_nome": "Rex (exemplo)",
        "cliente_nome": "Maria da Silva",
        "mes_label": f"{whatsapp_service._MESES[hoje.month - 1]}/{hoje.year}",
        "banhos": banhos,
        "transporte": transporte,
        "total": total,
        "status_label": "Fechado",
        "data_fmt": hoje.strftime("%d/%m/%Y"),
    }


def gerar_pdf_exemplo() -> bytes:
    """Gera uma página A4 com 4 comandas de exemplo, só para visualizar o modelo."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    dados = _dados_exemplo()
    for qx, qy in _QUADRANTES:
        _desenhar_comanda(c, qx, qy, dados)
    c.save()
    buffer.seek(0)
    return buffer.read()


def marcar_impressas(db: Session, comandas: List[ComandaImpressao]) -> None:
    agora = datetime.now(timezone.utc)
    for item in comandas:
        item.impresso_em = agora
    db.commit()
