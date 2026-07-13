<template>
  <div class="cliente-detail">
    <div class="header">
      <button @click="voltar" class="btn-back">← Voltar</button>
      <div class="header-info">
        <h1>{{ cliente?.nome || 'Cliente' }}</h1>
        <p class="subheader" v-if="cliente?.telefone || cliente?.endereco">
          <span v-if="cliente.telefone">📞 {{ cliente.telefone }}</span>
          <span v-if="cliente.endereco">📍 {{ cliente.endereco }}</span>
        </p>
      </div>
    </div>

    <!-- Resumo: tipo de pacote / dia da semana / cachorro -->
    <div class="resumo-card" v-if="resumoLinhas.length">
      <div v-for="linha in resumoLinhas" :key="linha.pet_nome" class="resumo-linha">
        <strong>{{ linha.tipo_plano_label }}</strong> · {{ linha.dia_semana_label }} — 🐾 {{ linha.pet_nome }}
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
              <span class="data-valor">R$ {{ formatarValor(bloco.valorBanhoEquivalente) }}</span>
              <span v-if="ag.extras?.info" class="data-extra">{{ ag.extras.info }}</span>
              <span v-if="ag.extras?.valor_extra > 0" class="data-extra-valor">R$ {{ formatarValor(ag.extras.valor_extra) }}</span>
            </div>
            <div v-if="bloco.pacote.valor_transporte > 0" class="data-linha transporte">
              <span class="data-data">Transporte</span>
              <span class="data-valor">R$ {{ formatarValor(bloco.pacote.valor_transporte) }}</span>
            </div>
          </div>

          <div class="bracket"></div>

          <div class="total-bloco">
            <div class="total-valor">R$ {{ formatarValor(bloco.total) }}</div>
            <span class="status-badge" :class="`status-${bloco.pacote.status_pagamento}`">
              {{ statusLabel(bloco.pacote.status_pagamento) }}
            </span>

            <div v-if="bloco.pacote.status_pagamento === 'pago'" class="pago-info">
              via {{ formatarTipoPagamento(ultimoPagamentoTipo(bloco.pacote)) }}
            </div>

            <div v-else class="pagamento-inline">
              <select v-model="formPagamento[bloco.pacote.id].tipo_pagamento" class="pag-select">
                <option value="pix">Pix</option>
                <option value="dinheiro">Dinheiro</option>
                <option value="cartao_debito">Débito</option>
                <option value="cartao_credito">Crédito</option>
                <option value="outro">Outro</option>
              </select>
              <input
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

    // Pacotes com mais de um cachorro banham juntos no mesmo dia, então o valor
    // do dia equivale ao valor base multiplicado pela quantidade de cachorros.
    const qtdCachorros = pacote.cachorros?.length || 1
    const valorBanhoEquivalente = (pacote.valor_banho_base || 0) * qtdCachorros

    const totalConcluidos = agendamentosOrdenados.reduce((sum, ag) => {
      if (ag.status_presenca !== 'concluido') return sum
      return sum + valorBanhoEquivalente + (ag.extras?.valor_extra || 0)
    }, 0)
    const total = totalConcluidos + (pacote.valor_transporte || 0)

    if (!formPagamento[pacote.id]) {
      const saldoRestante = Math.max((pacote.valor_cobrado || 0) - (pacote.valor_pago || 0), 0)
      formPagamento[pacote.id] = { tipo_pagamento: 'pix', valor_pago: saldoRestante }
    }

    return {
      pacote,
      agendamentos: agendamentosOrdenados,
      mesLabel: mesesNomes[dataRef.getMonth()],
      anoLabel: dataRef.getFullYear(),
      valorBanhoEquivalente,
      total
    }
  })
})

async function carregarTudo() {
  loading.value = true
  try {
    const [respCliente, respPacotes] = await Promise.all([
      clienteApi.obter(clienteId.value),
      pacoteApi.listar({ cliente_id: clienteId.value, incluir_inativos: true })
    ])
    cliente.value = respCliente.data
    pacotes.value = Array.isArray(respPacotes.data) ? respPacotes.data : []
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
