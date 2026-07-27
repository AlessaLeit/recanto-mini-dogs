<template>
  <div class="dashboard">
    <div class="page-header">
      <h1 class="page-title">Dashboard</h1>
      <div class="periodo-filtro">
        <label for="periodo-select">Período</label>
        <select id="periodo-select" v-model="statsFiltro">
          <option value="dia">Dia</option>
          <option value="semana">Semana</option>
          <option value="mes">Mês</option>
          <option value="periodo">Período</option>
          <option value="ano">Ano</option>
        </select>
        <template v-if="statsFiltro === 'periodo'">
          <input type="date" v-model="statsPeriodoInicio" class="periodo-data" />
          <span class="periodo-ate">até</span>
          <input type="date" v-model="statsPeriodoFim" class="periodo-data" />
        </template>
      </div>
    </div>

    <div class="dashboard-main-grid">
      <div class="dashboard-col-left">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">👥</div>
            <div class="stat-value">{{ totalClientesFiltrado }}</div>
            <div class="stat-label">Clientes</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">🐕</div>
            <div class="stat-value">{{ totalCachorrosFiltrado }}</div>
            <div class="stat-label">Cachorros</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">📦</div>
            <div class="stat-value">{{ pacotesAtivosFiltrados.length }}</div>
            <div class="stat-label">Pacotes Ativos</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">💰</div>
            <div class="stat-value">R$ {{ formatarValor(receitaPrevistaFiltrada) }}</div>
            <div class="stat-label">Receita Prevista</div>
          </div>
        </div>

        <div class="card">
          <div class="card-title"><span class="card-title-bar"></span>📅 Calendário de Banhos</div>
          <CalendarioMes :banhos="agendamentosStore.agendamentosDashboard" @data-selecionada="onDataSelecionada" />
        </div>
      </div>

      <div class="dashboard-col-right">
        <div class="card card-agendamentos">
          <div class="card-header-row">
            <div class="card-title" style="margin-bottom:0"><span class="card-title-bar"></span>📋 Agendamentos — {{ formatarData(dataSelecionada) }}</div>
            <div class="ag-header-actions">
              <select v-model="turnoFiltro" @change="carregarAgendamentos()" class="select-turno">
                <option value="todos">Todos os turnos</option>
                <option value="manha">Manhã</option>
                <option value="tarde">Tarde</option>
              </select>
              <button @click="carregarAgendamentos()" class="btn-refresh">↻ Atualizar</button>
            </div>
          </div>
          <div v-if="agendamentosStore.agendamentosDashboard.length === 0" class="empty-state">
            Nenhum agendamento nesta data. Clique no calendário para ver outros dias.
          </div>
          <div v-else class="agendamentos-list">
            <template v-for="entry in agendamentosExibicao" :key="entry.tipo === 'divider' ? `divider-${entry.turno}` : entry.ag.id">
              <div v-if="entry.tipo === 'divider'" class="turno-divider">
                <span>{{ entry.turno === 'tarde' ? 'Tarde' : 'Manhã' }}</span>
              </div>
              <div
                v-else
                class="ag-card"
                :class="entry.ag.status_presenca"
                @click="editarAgendamento(entry.ag)"
              >
                <div class="ag-header">
                  <div>
                    <h4 class="ag-pet">{{ entry.ag.pet_nome }}</h4>
                    <p class="ag-cliente">{{ entry.ag.cliente_nome }}</p>
                  </div>
                  <span class="status-badge" :class="`status-${entry.ag.status_presenca}`">
                    {{ entry.ag.status_presenca.toUpperCase() }}
                  </span>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title"><span class="card-title-bar"></span>📦 Pacotes em Aberto</div>
      <div v-if="pacotesEmAberto.length === 0" class="empty-state">
        Nenhum pacote em aberto
      </div>
      <div class="grid-3" v-else>
        <PacoteCard
          v-for="pacote in pacotesEmAberto.slice(0, 6)"
          :key="pacote.id"
          :pacote="pacote"
          @pagar="abrirPagamento"
          @detalhes="verDetalhes"
        />
      </div>
    </div>

    <PagamentoForm
      :show="showPagamento"
      :pacote="pacoteSelecionado"
      @close="showPagamento = false"
      @confirmar="confirmarPagamento"
    />

    <!-- Modal Editar Agendamento -->
    <div v-if="showModalEdit" class="modal-overlay" @click="showModalEdit = false">
      <div class="modal" @click.stop>
        <h3 class="modal-title">Editar Status — {{ agEdit.pet_nome }}</h3>
        <div class="form-group">
          <label for="edit-status">Status</label>
          <select id="edit-status" v-model="agEdit.status_presenca">
            <option value="pendente">🟡 Pendente</option>
            <option value="concluido">🟢 Concluído</option>
            <option value="faltou">🔴 Faltou</option>
          </select>
        </div>
        <div class="form-group">
          <label for="edit-turno">Turno</label>
          <select id="edit-turno" v-model="agEdit.turno">
            <option value="manha">Manhã</option>
            <option value="tarde">Tarde</option>
          </select>
        </div>
        <div class="form-group">
          <label for="edit-info">Itens Extra / Descrição</label>
          <input id="edit-info" v-model="agEdit.extras.info" placeholder="Ex: Tosa higiênica, Shampoo especial..." />
        </div>
        <div class="form-group">
          <label for="edit-valor-extra">Valor Extra (R$)</label>
          <input
            id="edit-valor-extra"
            type="number"
            step="0.01"
            v-model.number="agEdit.extras.valor_extra"
          />
        </div>
        <div class="modal-actions">
          <button @click="showModalEdit = false" class="btn btn-cancelar">Cancelar</button>
          <button @click="salvarAgendamento" class="btn btn-primario">Salvar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useClientesStore } from '../stores/clientes'
import { usePacotesStore } from '../stores/pacotes'
import PacoteCard from '../components/PacoteCard.vue'
import BanhoItem from '../components/BanhoItem.vue'
import CalendarioMes from '../components/CalendarioMes.vue'
import PagamentoForm from '../components/PagamentoForm.vue'
import { useAgendamentosStore } from '../stores/agendamentos.js'

const clientesStore = useClientesStore()
const pacotesStore = usePacotesStore()
const agendamentosStore = useAgendamentosStore()
const router = useRouter()

const dataSelecionada = ref(new Date().toISOString().split('T')[0])
const showModalEdit = ref(false)
const agEdit = ref(null)
const showPagamento = ref(false)
const pacoteSelecionado = ref(null)
const turnoFiltro = ref('todos')

// Quando o filtro é "todos", agrupa manhã primeiro e tarde depois, com um
// separador entre os dois grupos (sem separador se algum grupo estiver vazio).
const agendamentosExibicao = computed(() => {
  const lista = agendamentosStore.agendamentosDashboard
  if (turnoFiltro.value !== 'todos') {
    return lista.map(ag => ({ tipo: 'item', ag }))
  }
  const manha = lista.filter(ag => ag.turno !== 'tarde')
  const tarde = lista.filter(ag => ag.turno === 'tarde')
  const resultado = manha.map(ag => ({ tipo: 'item', ag }))
  if (manha.length && tarde.length) {
    resultado.push({ tipo: 'divider', turno: 'tarde' })
  }
  resultado.push(...tarde.map(ag => ({ tipo: 'item', ag })))
  return resultado
})

// Filtro de período dos cards de estatística do topo
const statsFiltro = ref('mes')
const statsPeriodoInicio = ref('')
const statsPeriodoFim = ref('')

const statsRange = computed(() => {
  const hoje = new Date()
  hoje.setHours(0, 0, 0, 0)

  if (statsFiltro.value === 'dia') {
    const fim = new Date(hoje)
    fim.setHours(23, 59, 59, 999)
    return { inicio: hoje, fim }
  }
  if (statsFiltro.value === 'semana') {
    const diaSemana = hoje.getDay()
    const offsetSegunda = diaSemana === 0 ? 6 : diaSemana - 1
    const inicio = new Date(hoje)
    inicio.setDate(hoje.getDate() - offsetSegunda)
    const fim = new Date(inicio)
    fim.setDate(inicio.getDate() + 6)
    fim.setHours(23, 59, 59, 999)
    return { inicio, fim }
  }
  if (statsFiltro.value === 'ano') {
    return {
      inicio: new Date(hoje.getFullYear(), 0, 1),
      fim: new Date(hoje.getFullYear(), 11, 31, 23, 59, 59, 999)
    }
  }
  if (statsFiltro.value === 'periodo') {
    const inicio = statsPeriodoInicio.value ? new Date(`${statsPeriodoInicio.value}T00:00:00`) : new Date(0)
    const fim = statsPeriodoFim.value ? new Date(`${statsPeriodoFim.value}T23:59:59`) : new Date()
    return { inicio, fim }
  }
  // mes (padrão)
  return {
    inicio: new Date(hoje.getFullYear(), hoje.getMonth(), 1),
    fim: new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0, 23, 59, 59, 999)
  }
})

function dentroDoPeriodo(dataStr) {
  if (!dataStr) return false
  // O backend envia timestamps UTC sem sufixo de fuso (ex.: "2026-07-04T03:43:49"),
  // que o JS interpretaria como hora local por padrão. Forçamos UTC para comparar corretamente.
  const temFuso = /Z$|[+-]\d{2}:\d{2}$/.test(dataStr)
  const d = new Date(temFuso ? dataStr : `${dataStr}Z`)
  return d >= statsRange.value.inicio && d <= statsRange.value.fim
}

const totalClientesFiltrado = computed(() =>
  clientesStore.clientes.filter(c => dentroDoPeriodo(c.criado_em)).length
)
const totalCachorrosFiltrado = computed(() =>
  clientesStore.clientes.reduce(
    (sum, c) => sum + (c.cachorros || []).filter(cc => dentroDoPeriodo(cc.criado_em)).length,
    0
  )
)
const pacotesAtivosFiltrados = computed(() =>
  pacotesStore.pacotesAtivos.filter(p => dentroDoPeriodo(p.criado_em))
)
const receitaPrevistaFiltrada = computed(() =>
  pacotesAtivosFiltrados.value.reduce((sum, p) => sum + (Number(p.valor_cobrado) || 0), 0)
)

const pacotesEmAberto = computed(() =>
  pacotesStore.pacotes.filter(p => p.ativo && (
    p.status_pagamento === 'em_aberto' ||
    p.status_pagamento === 'fechado' ||
    p.status_pagamento === 'atrasado'
  ))
)
const banhosRecentes = computed(() => {
  const banhos = []
  pacotesStore.pacotes.forEach(p => {
    if (p.banhos) banhos.push(...p.banhos.map(b => ({ ...b, pacote_id: p.id })))
  })
  return banhos.sort((a, b) => new Date(b.data_banho) - new Date(a.data_banho)).slice(0, 5)
})

function formatarValor(valor) {
  return Number(valor || 0).toFixed(2).replace('.', ',')
}
function abrirPagamento(pacote) {
  pacoteSelecionado.value = pacote
  showPagamento.value = true
}
function verDetalhes(pacote) {
  router.push(`/pacotes/${pacote.id}`)
}
async function confirmarPagamento(dados) {
  try {
    await pacotesStore.registrarPagamento(dados.pacote_id, {
      valor_pago: dados.valor_pago,
      data_pagamento: dados.data_pagamento,
      tipo_pagamento: 'pix',
      fechar_pacote: false
    })
    showPagamento.value = false
    alert('Pagamento registrado com sucesso!')
  } catch (err) {
    alert('Erro ao registrar pagamento: ' + err)
  }
}
async function carregarAgendamentos() {
  try {
    const turno = turnoFiltro.value === 'todos' ? null : turnoFiltro.value
    await agendamentosStore.fetchDashboard(dataSelecionada.value, turno)
  } catch (err) {
    alert('Erro ao carregar agendamentos: ' + err.message)
  }
}
function onDataSelecionada(data) {
  dataSelecionada.value = data
  carregarAgendamentos()
}
function formatarData(dataStr) {
  return new Date(dataStr).toLocaleDateString('pt-BR')
}
function editarAgendamento(ag) {
  // Garante que 'extras' seja um objeto com as chaves esperadas
  const extras = ag.extras || {}
  agEdit.value = {
    ...ag,
    turno: ag.turno || 'manha',
    extras: {
      info: extras.info || '',
      valor_extra: extras.valor_extra || 0
    }
  }
  showModalEdit.value = true
}
async function salvarAgendamento() {
  try {
    await agendamentosStore.updateStatus(agEdit.value.id, {
      status_presenca: agEdit.value.status_presenca,
      turno: agEdit.value.turno,
      extras: agEdit.value.extras
    })
    showModalEdit.value = false
    alert('Agendamento atualizado!')
  } catch (err) {
    alert('Erro ao salvar: ' + err.response?.data?.detail || err.message)
  }
}
onMounted(async () => {
  clientesStore.fetchClientes()
  pacotesStore.fetchPacotes({ incluir_inativos: true })
  await carregarAgendamentos()
})
</script>

<style scoped>
/* ── VARIÁVEIS DO TEMA RECANTO ── */
.dashboard {
  --marrom:        #3b2a1a;
  --marrom-medio:  #5a3e28;
  --marrom-claro:  #8b6340;
  --dourado:       #d4a843;
  --dourado-claro: #f5e4a8;
  --dourado-bg:    #fdf6e3;
  --verde:         #6b8f4e;
  --verde-claro:   #a8c47a;
  --verde-bg:      #eef4e6;
  --creme:         #faf6ef;
  --creme-escuro:  #f0e8d8;
  --text:          #2e1e0f;
  --text-muted:    #7a6251;
  --white:         #ffffff;
  --radius:        10px;
  --shadow:        0 2px 12px rgba(59,42,26,0.1);
}

.page-header {
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.page-title {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--marrom);
  border-left: 5px solid var(--dourado);
  padding-left: 0.75rem;
}

.periodo-filtro {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.periodo-filtro label {
  font-weight: 700;
  font-size: 0.85rem;
  color: var(--marrom);
}
.periodo-filtro select,
.periodo-filtro .periodo-data {
  padding: 0.5rem 0.75rem;
  border: 2px solid var(--creme-escuro);
  border-radius: 7px;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--marrom);
  background: var(--creme);
  transition: border-color 0.15s;
}
.periodo-filtro select:focus,
.periodo-filtro .periodo-data:focus {
  border-color: var(--dourado);
  outline: none;
}
.periodo-ate { font-size: 0.85rem; color: var(--text-muted); font-weight: 600; }

/* LAYOUT PRINCIPAL: KPIs + Calendário à esquerda, Agendamentos à direita (altura total) */
.dashboard-main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.2rem;
  margin-bottom: 1.2rem;
  align-items: stretch;
}
.dashboard-col-left {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}
.dashboard-col-right {
  display: flex;
  flex-direction: column;
}
.dashboard-col-left .card,
.dashboard-col-right .card {
  margin-bottom: 0;
}
.card-agendamentos {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 480px;
}
.card-agendamentos .empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* STATS (compactos, 2 por linha) */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}
.stat-card {
  background: var(--white);
  border-radius: var(--radius);
  padding: 0.9rem 0.7rem;
  text-align: center;
  box-shadow: var(--shadow);
  border-top: 4px solid var(--dourado);
  transition: transform 0.2s;
}
.stat-card:nth-child(2) { border-top-color: var(--verde); }
.stat-card:nth-child(3) { border-top-color: var(--marrom-claro); }
.stat-card:nth-child(4) { border-top-color: var(--verde-claro); }
.stat-card:hover { transform: translateY(-3px); }
.stat-icon { font-size: 1.3rem; margin-bottom: 0.25rem; }
.stat-value { font-size: 1.25rem; font-weight: 800; color: var(--marrom); line-height: 1.1; }
.stat-label { color: var(--text-muted); font-size: 0.68rem; font-weight: 700; margin-top: 3px; text-transform: uppercase; letter-spacing: 0.4px; }

/* GRID */
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }

/* CARD */
.card {
  background: var(--white);
  border-radius: var(--radius);
  padding: 1.4rem;
  box-shadow: var(--shadow);
  margin-bottom: 1.2rem;
}
.card-title {
  font-size: 1rem;
  font-weight: 800;
  color: var(--marrom);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 8px;
}
.card-title-bar {
  display: inline-block;
  width: 4px; height: 16px;
  background: var(--dourado);
  border-radius: 2px;
  flex-shrink: 0;
}
.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-bottom: 1rem;
}

/* AÇÕES DO CARD DE AGENDAMENTOS */
.ag-header-actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  gap: 0.6rem;
}
.select-turno {
  padding: 0.5rem 0.75rem;
  border: 2px solid var(--creme-escuro);
  border-radius: 7px;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--marrom);
  background: var(--creme);
  transition: border-color 0.15s;
}
.select-turno:focus {
  border-color: var(--dourado);
  outline: none;
}

/* BOTÃO REFRESH */
.btn-refresh {
  background: var(--creme-escuro);
  border: 1px solid var(--creme-escuro);
  color: var(--marrom);
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-refresh:hover { background: var(--dourado-claro); }

/* EMPTY */
.empty-state {
  text-align: center;
  color: var(--text-muted);
  padding: 2rem;
  font-style: italic;
  font-size: 0.95rem;
}

/* AGENDAMENTOS */
.agendamentos-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}
.turno-divider {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin: 0.2rem 0;
  color: var(--text-muted);
  font-size: 0.78rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.turno-divider::before,
.turno-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--creme-escuro);
}
.ag-card {
  background: var(--creme);
  border: 1px solid var(--creme-escuro);
  border-radius: var(--radius);
  padding: 1rem 1.2rem;
  border-left: 4px solid var(--dourado);
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}
.ag-card:hover { transform: translateY(-2px); box-shadow: var(--shadow); }
.ag-card.pendente  { border-left-color: #d4a843; }
.ag-card.concluido { border-left-color: var(--verde); background: var(--verde-bg); }
.ag-card.faltou    { border-left-color: #b94040; background: #fdf0f0; }
.ag-header { display: flex; justify-content: space-between; align-items: flex-start; }
.ag-pet { font-size: 1rem; font-weight: 800; color: var(--marrom); margin: 0; }
.ag-cliente { color: var(--text-muted); font-size: 0.85rem; margin: 2px 0 0; }

.status-badge {
  padding: 3px 10px;
  border-radius: 5px;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.5px;
}
.status-pendente  { background: var(--dourado-claro); color: #6b4c00; }
.status-concluido { background: var(--verde-bg); color: var(--verde); }
.status-faltou    { background: #fdeaea; color: #b94040; }

/* MODAL */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal {
  background: var(--white);
  padding: 2rem;
  border-radius: var(--radius);
  max-width: 480px; width: 90%;
  max-height: 80vh; overflow-y: auto;
  border-top: 5px solid var(--dourado);
  box-shadow: 0 8px 32px rgba(59,42,26,0.2);
}
.modal-title { font-size: 1.1rem; font-weight: 800; color: var(--marrom); margin-bottom: 1.2rem; }

.form-group { margin-bottom: 1rem; }
.form-group label {
  display: block; margin-bottom: 0.3rem;
  font-weight: 700; font-size: 0.9rem; color: var(--marrom);
}
.form-group select,
.form-group input,
.form-group textarea {
  width: 100%; padding: 0.6rem 0.75rem;
  border: 2px solid var(--creme-escuro);
  border-radius: 7px; font-size: 0.95rem;
  color: var(--text); background: var(--creme);
  transition: border-color 0.15s, box-shadow 0.15s;
  box-sizing: border-box;
}
.form-group select:focus,
.form-group textarea:focus { border-color: var(--dourado); outline: none; }
.field-hint { font-size: 0.78rem; color: var(--text-muted); margin-top: 4px; display: block; }

.modal-actions { display: flex; gap: 0.75rem; margin-top: 1.5rem; }
.btn { padding: 0.65rem 1.2rem; border: none; border-radius: 7px; font-weight: 700; cursor: pointer; font-size: 0.95rem; transition: all 0.15s; }
.btn-primario { background: var(--marrom); color: var(--dourado); flex: 1; }
.btn-primario:hover { background: var(--marrom-medio); }
.btn-cancelar { background: var(--creme-escuro); color: var(--marrom); flex: 1; }
.btn-cancelar:hover { background: #e0d5c2; }

@media (max-width: 900px) {
  .dashboard-main-grid { grid-template-columns: 1fr; }
  .card-agendamentos { min-height: 320px; }
}
</style>
