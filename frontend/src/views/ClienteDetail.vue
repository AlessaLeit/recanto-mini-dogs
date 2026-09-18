<template>
  <div class="cliente-detail">
    <div class="header">
      <button @click="voltar" class="btn-back">← Voltar</button>
      <div class="header-info">
        <h1>{{ cliente?.nome || 'Cliente' }}</h1>
        <p class="subheader" v-if="cliente?.whatsapp || cliente?.endereco">
          <span v-if="cliente.whatsapp">💬 {{ cliente.whatsapp }}</span>
          <span v-if="cliente.endereco">📍 {{ cliente.endereco }}</span>
        </p>
      </div>

      <!-- Crédito: dinheiro já pago que ainda não entrou em nenhum pacote.
           Entra sozinho no próximo pacote que for criado. -->
      <div class="credito-area">
        <span v-if="credito.saldo > 0" class="credito-saldo">
          💰 Crédito: <strong>R$ {{ formatarValor(credito.saldo) }}</strong>
        </span>
        <span v-else class="credito-vazio">Sem crédito adiantado</span>
        <button @click="abrirAdiantado" class="btn-adiantado">+ Pagamento adiantado</button>
      </div>
    </div>

    <!-- Resumo: tipo de pacote / dia da semana / cachorro -->
    <div class="resumo-card" v-if="resumoLinhas.length">
      <div v-for="linha in resumoLinhas" :key="linha.pet_nome" class="resumo-linha">
        <strong>{{ linha.tipo_plano_label }}</strong> · {{ linha.dia_semana_label }} — 🐾 {{ linha.pet_nome }}
      </div>
    </div>

    <div v-if="showAdiantado" class="modal-overlay" @click="showAdiantado = false">
      <div class="modal-adiantado" @click.stop>
        <h3>Pagamento adiantado</h3>
        <p class="modal-ajuda">
          Guarda o valor como crédito do cliente. Quando o próximo pacote for criado,
          ele entra lá como pagamento automaticamente.
        </p>

        <div v-if="totalEmAberto > 0" class="aviso-pendencia">
          ⚠️ Este cliente tem <strong>R$ {{ formatarValor(totalEmAberto) }}</strong> em aberto.
          Confira se não é o pagamento de um pacote antigo.
        </div>

        <label for="adiantado-valor">Valor</label>
        <input id="adiantado-valor" type="number" step="0.01" v-model.number="formAdiantado.valor" />

        <label for="adiantado-tipo">Forma de pagamento</label>
        <select id="adiantado-tipo" v-model="formAdiantado.tipo_pagamento">
          <option value="pix">Pix</option>
          <option value="dinheiro">Dinheiro</option>
          <option value="cartao_debito">Débito</option>
          <option value="cartao_credito">Crédito</option>
          <option value="outro">Outro</option>
        </select>

        <div class="modal-acoes">
          <button @click="showAdiantado = false" class="btn-cancelar">Cancelar</button>
          <button @click="salvarAdiantado" class="btn-pagar" :disabled="salvandoAdiantado">
            {{ salvandoAdiantado ? 'Salvando...' : 'Guardar crédito' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="empty-state">Carregando...</div>
    <div v-else-if="blocos.length === 0" class="empty-state">Nenhum pacote encontrado para este cliente.</div>

    <div v-else class="blocos">
      <div v-for="bloco in blocos" :key="bloco.pacote.id" class="bloco-card">
        <div class="bloco-topo">
          <div class="bloco-mes">
            {{ bloco.mesLabel }} <span class="bloco-ano">{{ bloco.anoLabel }}</span>
          </div>
          <div class="bloco-pacote-info">
            🐾 {{ bloco.pacote.pet_nome }} · {{ tipoPlanoLabel(bloco.pacote.tipo_plano) }} · {{ formatarDiaSemana(bloco.pacote.dia_da_semana) }}
            <router-link :to="`/pacotes/${bloco.pacote.id}`" class="link-detalhes">Ver detalhes completos →</router-link>
          </div>
        </div>

        <div class="bloco-corpo">
          <div class="datas-lista">
            <div v-if="bloco.agendamentos.length === 0" class="sem-datas">Nenhum banho agendado neste pacote.</div>
            <div
              v-for="ag in bloco.agendamentos"
              :key="ag.id"
              class="data-linha"
              :class="ag.status_presenca"
            >
              <span class="data-data">{{ formatarData(ag.data_banho) }}</span>
              <span class="data-valor">R$ {{ formatarValor(ag.valor_banho_dia ?? bloco.valorBanhoEquivalente) }}</span>
              <span v-if="ag.extras?.info" class="data-extra">{{ ag.extras.info }}</span>
              <span v-if="ag.extras?.valor_extra > 0" class="data-extra-valor">R$ {{ formatarValor(ag.extras.valor_extra) }}</span>
            </div>
            <div v-if="bloco.pacote.valor_transporte > 0" class="data-linha transporte">
              <span class="data-data">Transporte</span>
              <span class="data-valor">R$ {{ formatarValor(bloco.pacote.valor_transporte) }}</span>
            </div>

            <!-- Fecha a coluna de valores somando o que está acima. -->
            <div class="data-linha total-linha">
              <span class="data-data">Total</span>
              <span class="data-valor">R$ {{ formatarValor(bloco.total) }}</span>
            </div>
          </div>

          <div class="bracket"></div>

          <div class="total-bloco">
            <!-- Pagamentos já recebidos deste pacote, só os valores; a forma
                 de pagamento aparece em "Ver detalhes completos". -->
            <div v-if="bloco.valoresPagos.length" class="pagamentos-feitos">
              {{ bloco.valoresPagos.map(formatarValor).join(' + ') }}
            </div>
            <div class="total-rotulo">{{ bloco.saldoRestante > 0 ? 'Falta' : 'Quitado' }}</div>
            <div class="total-valor">R$ {{ formatarValor(bloco.saldoRestante) }}</div>
            <span class="status-badge" :class="`status-${bloco.pacote.status_pagamento}`">
              {{ statusLabel(bloco.pacote.status_pagamento) }}
            </span>

            <div v-if="bloco.pacote.status_pagamento === 'pago'" class="pago-info">
              via {{ formatarTipoPagamento(ultimoPagamentoTipo(bloco.pacote)) }}
            </div>

            <div v-else class="pagamento-inline">
              <select
                :id="'pag-tipo-' + bloco.pacote.id"
                aria-label="Forma de pagamento"
                v-model="formPagamento[bloco.pacote.id].tipo_pagamento"
                class="pag-select"
              >
                <option value="pix">Pix</option>
                <option value="dinheiro">Dinheiro</option>
                <option value="cartao_debito">Débito</option>
                <option value="cartao_credito">Crédito</option>
                <option value="outro">Outro</option>
              </select>
              <input
                :id="'pag-valor-' + bloco.pacote.id"
                aria-label="Valor do pagamento"
                type="number"
                step="0.01"
                v-model.number="formPagamento[bloco.pacote.id].valor_pago"
                class="pag-valor"
              />
              <button
                @click="marcarPago(bloco.pacote)"
                class="btn-pagar"
                :disabled="salvandoPagamento === bloco.pacote.id"
              >
                {{ salvandoPagamento === bloco.pacote.id ? 'Salvando...' : 'Marcar Pago' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import clienteApi from '../api/clientes.js'
import pacoteApi from '../api/pacotes.js'
import creditoApi from '../api/creditos.js'
import { usePacotesStore } from '../stores/pacotes.js'

const route = useRoute()
const router = useRouter()
const pacotesStore = usePacotesStore()

const clienteId = computed(() => Number.parseInt(route.params.id, 10))

const cliente = ref(null)
const pacotes = ref([])
const loading = ref(false)
const salvandoPagamento = ref(null)
const formPagamento = reactive({})

const mesesNomes = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

const tipoPlanoLabels = { semanal: 'Semanal', quinzenal: 'Quinzenal', mensal: 'Mensal' }
function tipoPlanoLabel(tipo) { return tipoPlanoLabels[tipo] || tipo }

function formatarDiaSemana(dia) {
  const map = { terca: 'Terça', quarta: 'Quarta', quinta: 'Quinta', sexta: 'Sexta', sabado: 'Sábado' }
  return map[dia] || '-'
}
function formatarData(isoDate) {
  if (!isoDate) return '-'
  return new Date(isoDate + 'T00:00:00').toLocaleDateString('pt-BR')
}
function formatarValor(valor) {
  return Number(valor || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function formatarTipoPagamento(tipo) {
  const map = { pix: 'Pix', dinheiro: 'Dinheiro', cartao_debito: 'Débito', cartao_credito: 'Crédito', outro: 'Outro' }
  return map[tipo] || tipo
}
function statusLabel(status) {
  const map = { em_aberto: 'Em Aberto', pago: 'Pago', parcial: 'Parcial', atrasado: 'Atrasado', fechado: 'Fechado' }
  return map[status] || 'Desconhecido'
}
function ultimoPagamentoTipo(pacote) {
  if (!pacote.pagamentos?.length) return null
  return pacote.pagamentos[pacote.pagamentos.length - 1].tipo_pagamento
}

// Resumo do topo: um pacote ativo por cachorro (o mais recente), sem repetir cachorro
const resumoLinhas = computed(() => {
  const vistos = new Set()
  const linhas = []
  for (const p of pacotes.value) {
    if (!p.ativo || vistos.has(p.pet_nome)) continue
    vistos.add(p.pet_nome)
    linhas.push({
      pet_nome: p.pet_nome,
      tipo_plano_label: tipoPlanoLabel(p.tipo_plano),
      dia_semana_label: formatarDiaSemana(p.dia_da_semana)
    })
  }
  return linhas
})

// Um bloco por pacote, mais recente primeiro
const blocos = computed(() => {
  const ordenados = [...pacotes.value].sort((a, b) => new Date(b.criado_em) - new Date(a.criado_em))
  return ordenados.map(pacote => {
    const agendamentosOrdenados = [...(pacote.agendamentos || [])].sort(
      (a, b) => new Date(a.data_banho) - new Date(b.data_banho)
    )

    const primeiraData = agendamentosOrdenados[0]?.data_banho
    const dataRef = primeiraData ? new Date(primeiraData + 'T00:00:00') : new Date(pacote.criado_em)

    // Pacotes com mais de um cachorro banham juntos no mesmo dia, mas cada pet
    // pode faltar individualmente — o backend já calcula em valor_banho_dia o
    // valor de cada data considerando só quem tomou banho.
    const valorBanhoEquivalente = pacote.valor_banho_equivalente
      ?? (pacote.valor_banho_base || 0) * (pacote.cachorros?.length || 1)

    const totalConcluidos = agendamentosOrdenados.reduce((sum, ag) => {
      if (ag.status_presenca !== 'concluido') return sum
      const valorBanho = ag.valor_banho_dia ?? valorBanhoEquivalente
      return sum + valorBanho + (ag.extras?.valor_extra || 0)
    }, 0)
    const total = totalConcluidos + (pacote.valor_transporte || 0)

    // Lado financeiro do bloco: o que já entrou e o que ainda falta. Usa
    // valor_cobrado/valor_pago (dinheiro), e não o total acima, que soma os
    // banhos efetivamente realizados — os dois divergem quando o pacote é
    // pago adiantado ou algum banho não acontece.
    const valoresPagos = (pacote.pagamentos || []).map(p => p.valor_pago || 0)
    const saldoRestante = Math.max((pacote.valor_cobrado || 0) - (pacote.valor_pago || 0), 0)

    if (!formPagamento[pacote.id]) {
      formPagamento[pacote.id] = { tipo_pagamento: 'pix', valor_pago: saldoRestante }
    }

    return {
      pacote,
      agendamentos: agendamentosOrdenados,
      mesLabel: mesesNomes[dataRef.getMonth()],
      anoLabel: dataRef.getFullYear(),
      valorBanhoEquivalente,
      total,
      valoresPagos,
      saldoRestante
    }
  })
})

// ── Crédito (pagamento adiantado) ───────────────────────────────────────
const credito = ref({ saldo: 0, creditos: [] })
const showAdiantado = ref(false)
const salvandoAdiantado = ref(false)
const formAdiantado = reactive({ valor: null, tipo_pagamento: 'pix' })

// Soma do que o cliente ainda deve, somando todos os pacotes. É isso que
// dispara o aviso: quem tem pendência pode estar só esquecendo de dar baixa
// num pacote antigo, em vez de realmente adiantando o próximo.
const totalEmAberto = computed(() =>
  pacotes.value.reduce(
    (soma, p) => soma + Math.max((p.valor_cobrado || 0) - (p.valor_pago || 0), 0),
    0
  )
)

const pacotesPendentes = computed(() =>
  pacotes.value.filter(p => (p.valor_cobrado || 0) - (p.valor_pago || 0) > 0.001)
)

function abrirAdiantado() {
  formAdiantado.valor = null
  formAdiantado.tipo_pagamento = 'pix'
  showAdiantado.value = true
}

async function salvarAdiantado() {
  if (!formAdiantado.valor || formAdiantado.valor <= 0) {
    alert('Informe um valor válido.')
    return
  }
  if (totalEmAberto.value > 0) {
    const ok = confirm(
      `Atenção: este cliente ainda tem R$ ${formatarValor(totalEmAberto.value)} em aberto ` +
      `(${pacotesPendentes.value.length} pacote(s)).\n\n` +
      `Guardar R$ ${formatarValor(formAdiantado.valor)} como pagamento adiantado mesmo assim?\n\n` +
      `Se o cliente estiver quitando um pacote antigo, cancele e use o botão ` +
      `"Marcar Pago" do pacote correspondente.`
    )
    if (!ok) return
  }

  salvandoAdiantado.value = true
  try {
    await creditoApi.registrar({
      cliente_id: clienteId.value,
      valor: formAdiantado.valor,
      data_pagamento: new Date().toISOString().split('T')[0],
      tipo_pagamento: formAdiantado.tipo_pagamento
    })
    showAdiantado.value = false
    await carregarTudo()
  } catch (err) {
    alert('Erro ao registrar adiantamento: ' + (err.response?.data?.detail || err.message))
  } finally {
    salvandoAdiantado.value = false
  }
}

async function carregarTudo() {
  loading.value = true
  try {
    const [respCliente, respPacotes, respCredito] = await Promise.all([
      clienteApi.obter(clienteId.value),
      pacoteApi.listar({ cliente_id: clienteId.value, incluir_inativos: true }),
      creditoApi.obterPorCliente(clienteId.value)
    ])
    cliente.value = respCliente.data
    pacotes.value = Array.isArray(respPacotes.data) ? respPacotes.data : []
    credito.value = respCredito.data || { saldo: 0, creditos: [] }
  } catch (err) {
    alert('Erro ao carregar dados do cliente: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

async function marcarPago(pacote) {
  const dados = formPagamento[pacote.id]
  if (!dados.valor_pago || dados.valor_pago <= 0) {
    alert('Informe um valor válido.')
    return
  }
  salvandoPagamento.value = pacote.id
  try {
    await pacotesStore.registrarPagamento(pacote.id, {
      valor_pago: dados.valor_pago,
      data_pagamento: new Date().toISOString().split('T')[0],
      tipo_pagamento: dados.tipo_pagamento,
      fechar_pacote: false
    })
    await carregarTudo()
  } catch (err) {
    alert('Erro ao registrar pagamento: ' + (err.response?.data?.detail || err.message))
  } finally {
    salvandoPagamento.value = null
  }
}

function voltar() { router.push('/clientes') }

onMounted(carregarTudo)
</script>

<style scoped>
.cliente-detail {
  --marrom:        #3b2a1a;
  --marrom-medio:  #5a3e28;
  --dourado:       #d4a843;
  --dourado-claro: #f5e4a8;
  --dourado-bg:    #fdf6e3;
  --verde:         #6b8f4e;
  --verde-bg:      #eef4e6;
  --creme:         #faf6ef;
  --creme-escuro:  #f0e8d8;
  --text:          #2e1e0f;
  --text-muted:    #7a6251;
  --white:         #ffffff;
  --radius:        10px;
  --shadow:        0 2px 12px rgba(59,42,26,0.1);

  max-width: 1000px;
  margin: 0 auto;
  padding: 1.5rem;
}

.header {
  display: flex; align-items: center; gap: 1rem;
  margin-bottom: 1.5rem; padding-bottom: 1.2rem;
  border-bottom: 2px solid var(--creme-escuro);
  flex-wrap: wrap;
}
.btn-back {
  background: var(--creme-escuro); border: none; font-size: 0.9rem; font-weight: 700;
  color: var(--marrom); cursor: pointer; padding: 0.55rem 1rem; border-radius: 8px;
  transition: background 0.15s; white-space: nowrap;
}
.btn-back:hover { background: var(--dourado-claro); }
.header-info h1 { margin: 0; font-size: 1.45rem; font-weight: 800; color: var(--marrom); }
.subheader { margin: 0.2rem 0 0; color: var(--text-muted); font-size: 0.9rem; font-weight: 600; display: flex; gap: 1rem; }

/* RESUMO */
.resumo-card {
  background: var(--dourado-bg); border: 2px solid var(--dourado-claro);
  border-radius: var(--radius); padding: 1rem 1.2rem; margin-bottom: 1.5rem;
}
.resumo-linha { font-size: 0.92rem; color: var(--marrom); padding: 0.2rem 0; }

.empty-state { text-align: center; padding: 3rem; color: var(--text-muted); font-style: italic; }

/* BLOCOS */
.blocos { display: flex; flex-direction: column; gap: 1.2rem; }
.bloco-card {
  background: var(--white); border-radius: var(--radius);
  padding: 1.3rem 1.4rem; box-shadow: var(--shadow);
}
.bloco-topo { margin-bottom: 0.9rem; padding-bottom: 0.8rem; border-bottom: 2px solid var(--creme-escuro); }
.bloco-mes { font-size: 1.15rem; font-weight: 800; color: var(--marrom); }
.bloco-ano { font-size: 0.85rem; font-weight: 600; color: var(--text-muted); }
.bloco-pacote-info {
  font-size: 0.85rem; color: var(--text-muted); margin-top: 0.3rem;
  display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap;
}
.link-detalhes { color: var(--marrom-claro); font-weight: 700; text-decoration: none; margin-left: auto; }
.link-detalhes:hover { color: var(--dourado); text-decoration: underline; }

.bloco-corpo { display: flex; align-items: stretch; gap: 0; }

.datas-lista { flex: 1; display: flex; flex-direction: column; gap: 0.35rem; min-width: 0; }
.data-linha {
  display: flex; align-items: center; gap: 0.7rem;
  padding: 0.4rem 0.6rem; border-radius: 6px;
  border-left: 3px solid var(--creme-escuro);
  font-size: 0.88rem; color: var(--text);
}
.data-linha.concluido { border-left-color: var(--verde); background: var(--verde-bg); }
.data-linha.faltou    { border-left-color: #b94040; background: #fdf0f0; opacity: 0.8; }
.data-linha.pendente  { border-left-color: var(--dourado); }
.data-linha.transporte { border-left-color: var(--marrom-claro); font-style: italic; color: var(--text-muted); }
.data-data { font-weight: 700; color: var(--marrom); min-width: 78px; }
.data-valor { font-weight: 700; }
.data-extra { color: var(--text-muted); font-size: 0.82rem; }
.data-extra-valor { color: var(--verde); font-weight: 700; font-size: 0.82rem; margin-left: -0.3rem; }
.sem-datas { color: var(--text-muted); font-style: italic; font-size: 0.88rem; padding: 0.5rem; }

.bracket {
  width: 2px;
  background: var(--creme-escuro);
  margin: 0 1.2rem;
  flex-shrink: 0;
}

.total-bloco {
  flex-shrink: 0; width: 200px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 0.5rem; text-align: center;
}
/* ── CRÉDITO (pagamento adiantado) ──
   Fica na ponta direita do cabeçalho, na mesma linha do nome do cliente.
   O 'margin-left: auto' empurra o bloco para a direita ocupando a sobra. */
.credito-area {
  margin-left: auto;
  display: flex; flex-direction: column; align-items: flex-end; gap: 0.35rem;
  text-align: right; flex-shrink: 0;
}
.credito-saldo { font-size: 0.88rem; color: var(--text); white-space: nowrap; }
.credito-saldo strong { color: var(--verde); font-size: 1rem; }
.credito-vazio { font-size: 0.8rem; color: var(--text-muted); white-space: nowrap; }
.btn-adiantado {
  background: var(--verde); color: var(--white);
  border: none; border-radius: 7px; padding: 0.55rem 1rem;
  font-weight: 700; font-size: 0.88rem; cursor: pointer;
}
.btn-adiantado:hover { background: #5a7c3e; }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center; z-index: 200;
}
.modal-adiantado {
  background: var(--white); border-radius: var(--radius);
  padding: 1.5rem; width: 100%; max-width: 380px;
  display: flex; flex-direction: column; gap: 0.5rem;
  box-shadow: 0 10px 40px rgba(0,0,0,0.25);
}
.modal-adiantado h3 { color: var(--marrom); font-size: 1.1rem; }
.modal-ajuda { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.3rem; }
.modal-adiantado label {
  font-size: 0.78rem; font-weight: 800; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.4px; margin-top: 0.4rem;
}
.modal-adiantado input, .modal-adiantado select {
  padding: 0.6rem 0.8rem; border: 2px solid var(--creme-escuro);
  border-radius: 7px; font-size: 0.95rem; font-family: inherit;
  background: var(--creme); color: var(--text); outline: none;
}
.aviso-pendencia {
  background: #fdeaea; color: #b94040;
  border-radius: 7px; padding: 0.6rem 0.8rem;
  font-size: 0.82rem; line-height: 1.4;
}
.modal-acoes { display: flex; gap: 0.5rem; margin-top: 1rem; }
.modal-acoes button { flex: 1; }
.btn-cancelar {
  background: var(--creme-escuro); color: var(--marrom);
  border: none; border-radius: 7px; padding: 0.55rem 1rem;
  font-weight: 700; cursor: pointer;
}

/* Linha de total, fechando a coluna de datas/valores. */
.data-linha.total-linha {
  border-left-color: var(--marrom);
  border-top: 2px solid var(--creme-escuro);
  border-radius: 0 0 6px 6px;
  font-weight: 800;
  color: var(--marrom);
  margin-top: 0.15rem;
}

/* Pagamentos já recebidos, em fonte menor acima do saldo. */
.pagamentos-feitos {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--verde);
}
.total-rotulo {
  font-size: 0.68rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--text-muted);
  margin-top: -0.25rem;
}
.total-valor { font-size: 1.3rem; font-weight: 800; color: var(--marrom); }

.status-badge { padding: 3px 10px; border-radius: 5px; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.4px; }
.status-em_aberto { background: var(--dourado-claro); color: #6b4c00; }
.status-pago       { background: var(--verde-bg); color: var(--verde); }
.status-parcial    { background: #fef0e0; color: #8b5e00; }
.status-atrasado   { background: #fdeaea; color: #b94040; }
.status-fechado    { background: #e0e0e0; color: #424242; }

.pago-info { font-size: 0.78rem; color: var(--text-muted); }

.pagamento-inline { display: flex; flex-direction: column; gap: 0.4rem; width: 100%; }
.pag-select, .pag-valor {
  width: 100%; padding: 0.4rem 0.5rem;
  border: 2px solid var(--creme-escuro); border-radius: 6px;
  font-size: 0.82rem; color: var(--text); background: var(--creme);
  box-sizing: border-box;
}
.pag-select:focus, .pag-valor:focus { border-color: var(--dourado); outline: none; }
.btn-pagar {
  background: var(--marrom); color: var(--dourado); border: none;
  padding: 0.45rem 0.6rem; border-radius: 6px; font-weight: 700; font-size: 0.82rem;
  cursor: pointer; transition: background 0.15s;
}
.btn-pagar:hover { background: var(--marrom-medio); }
.btn-pagar:disabled { opacity: 0.6; cursor: not-allowed; }

@media (max-width: 700px) {
  .bloco-corpo { flex-direction: column; }
  .bracket { width: 100%; height: 2px; margin: 1rem 0; }
  .total-bloco { width: 100%; }
}
</style>
