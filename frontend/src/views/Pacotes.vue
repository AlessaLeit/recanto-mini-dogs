<template>
  <div class="pacotes-view">
    <div class="page-header">
      <div>
        <h1 class="page-title" v-if="cachorroId">Pacotes de {{ cachorroSelecionado?.nome || 'Cachorro' }}</h1>
        <h1 class="page-title" v-else>Gerenciamento de Pacotes</h1>
      </div>
      <div class="header-btns">
        <button @click="abrirNovoPacote" class="btn btn-primario" v-if="!cachorroId || (cachorroId && cachorros.length)">
          + Novo Pacote
        </button>
        <button v-if="cachorroId" @click="voltarTodosPacotes" class="btn btn-ghost">
          ← Todos os Pacotes
        </button>
      </div>
    </div>

    <div class="filters-bar" v-if="!cachorroId">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input
          v-model="buscaCliente"
          type="text"
          class="search-input"
          placeholder="Buscar por cliente..."
          aria-label="Buscar por cliente"
        />
        <button v-if="buscaCliente" @click="buscaCliente = ''" class="search-clear" title="Limpar busca">✕</button>
      </div>
      <select v-model="filtroStatus" class="filter-select" aria-label="Filtrar por status do pacote">
        <option value="ativos">Pacotes Ativos</option>
        <option value="inativos">Pacotes Inativos</option>
        <option value="todos">Todos</option>
      </select>
      <select v-model="filtroPagamento" class="filter-select" aria-label="Filtrar por status de pagamento">
        <option value="todos">Todos os Status</option>
        <option value="em_aberto">Em Aberto</option>
        <option value="parcial">Parcial</option>
        <option value="atrasado">Atrasado</option>
        <option value="fechado">Fechado (Aguardando)</option>
        <option value="pago">Pago</option>
      </select>
    </div>

    <div class="grid-3">
      <PacoteCard
        v-for="pacote in pacotesFiltrados"
        :key="pacote.id"
        :pacote="pacote"
        @pagar="abrirPagamento"
        @detalhes="verDetalhes"
      />
      <div v-if="pacotesFiltrados.length === 0" class="empty-state">
        <p v-if="cachorroId">Nenhum pacote encontrado para este cachorro.</p>
        <p v-else-if="buscaCliente">Nenhum pacote encontrado para "{{ buscaCliente }}".</p>
        <p v-else>Nenhum pacote cadastrado.</p>
      </div>
    </div>

    <!-- Modal Novo Pacote -->
    <div class="modal-wrap" v-if="showNovoPacote">
      <div class="modal-overlay" @click="showNovoPacote = false"></div>
      <div class="modal-content">
        <h3 class="modal-title" v-if="cachorroId">Novo Pacote — {{ cachorroSelecionado?.nome }}</h3>
        <h3 class="modal-title" v-else>Novo Pacote</h3>
        <form @submit.prevent="criarPacote">
          <div class="form-group" v-if="cachorroId">
            <label for="novo-cachorro">Cachorro</label>
            <input id="novo-cachorro" :value="`${cachorroSelecionado?.nome || ''} (pré-selecionado)`" disabled />
          </div>
          <div class="form-group" v-else>
            <label for="novo-cachorro">Cachorro</label>
            <div class="autocomplete">
              <input
                id="novo-cachorro"
                v-model="buscaCachorroNovo"
                type="text"
                autocomplete="off"
                placeholder="Digite o nome do cachorro ou do cliente..."
                @focus="mostrarListaCachorro = true"
                @input="onDigitarCachorroNovo"
                @blur="onBlurCachorroNovo"
                required
              />
              <div v-if="mostrarListaCachorro" class="autocomplete-lista">
                <div
                  v-for="cachorro in cachorrosFiltradosNovo"
                  :key="cachorro.id"
                  class="autocomplete-item"
                  @mousedown.prevent="selecionarCachorroNovo(cachorro)"
                >
                  {{ cachorro.nome }} <span class="autocomplete-sub">({{ cachorro.cliente?.nome }})</span>
                </div>
                <div v-if="cachorrosFiltradosNovo.length === 0" class="autocomplete-empty">Nenhum cachorro encontrado</div>
              </div>
            </div>
          </div>
          <div class="form-group" v-if="outrosCachorrosDoCliente.length">
            <label>Outros cachorros do mesmo cliente (opcional)</label>
            <div class="checkbox-lista">
              <label v-for="cachorro in outrosCachorrosDoCliente" :key="cachorro.id" class="checkbox-item">
                <input
                  type="checkbox"
                  :value="cachorro.id"
                  v-model="novoPacote.cachorros_adicionais_ids"
                  @change="calcularSugeridoNovo"
                />
                {{ cachorro.nome }}
              </label>
            </div>
          </div>
          <div class="form-group" v-for="cachorro in cachorrosAdicionaisSelecionados" :key="'valor-' + cachorro.id">
            <label :for="'novo-valor-extra-' + cachorro.id">Valor do banho — {{ cachorro.nome }} (opcional)</label>
            <input
              :id="'novo-valor-extra-' + cachorro.id"
              v-model.number="valoresAdicionais[cachorro.id]"
              type="number"
              step="0.01"
              placeholder="Se vazio, dobra o valor base"
              @input="calcularSugeridoNovo"
            />
          </div>
          <div class="form-group">
            <label for="novo-tipo-plano">Tipo de Plano</label>
            <select id="novo-tipo-plano" v-model="novoPacote.tipo_plano" @change="calcularSugeridoNovo" required>
              <option value="semanal">Semanal (4 banhos/mês)</option>
              <option value="quinzenal">Quinzenal (2 banhos/mês)</option>
              <option value="mensal">Mensal (1 banho/mês)</option>
            </select>
          </div>
          <div class="form-group">
            <label for="novo-dia-semana">Dia da Semana</label>
            <select id="novo-dia-semana" v-model="novoPacote.dia_da_semana" required>
              <option value="terca">Terça-feira</option>
              <option value="quarta">Quarta-feira</option>
              <option value="quinta">Quinta-feira</option>
              <option value="sexta">Sexta-feira</option>
              <option value="sabado">Sábado</option>
            </select>
          </div>
          <div class="form-group">
            <label for="novo-valor-base">Valor Base do Banho (R$)</label>
            <input id="novo-valor-base" v-model.number="novoPacote.valor_banho_base" type="number" step="0.01" @input="calcularSugeridoNovo" required />
          </div>
          <div class="form-group">
            <label for="novo-valor-transporte">Transporte Total (R$)</label>
            <input id="novo-valor-transporte" v-model.number="novoPacote.valor_transporte" type="number" step="0.01" @input="calcularSugeridoNovo" />
          </div>
          <div class="form-group">
            <label for="novo-valor-cobrado">Valor Total Cobrado (R$)</label>
            <input id="novo-valor-cobrado" v-model.number="novoPacote.valor_cobrado" type="number" step="0.01" required style="font-weight: 800; background: var(--dourado-bg);" />
          </div>
          <div class="form-actions">
            <button type="button" @click="showNovoPacote = false" class="btn btn-cancelar">Cancelar</button>
            <button type="submit" class="btn btn-primario">Criar Pacote</button>
          </div>
        </form>
      </div>
    </div>

    <PagamentoForm
      :show="showPagamento"
      :pacote="pacoteSelecionado"
      @close="showPagamento = false"
      @confirmar="confirmarPagamento"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePacotesStore } from '../stores/pacotes'
import { useClientesStore } from '../stores/clientes'
import PacoteCard from '../components/PacoteCard.vue'
import PagamentoForm from '../components/PagamentoForm.vue'

const route = useRoute()
const router = useRouter()
const pacotesStore = usePacotesStore()
const clientesStore = useClientesStore()

const showNovoPacote = ref(false)
const showPagamento = ref(false)
const pacoteSelecionado = ref(null)
const filtroStatus = ref('ativos')
const filtroPagamento = ref('todos')
const buscaCliente = ref('')
const buscaCachorroNovo = ref('')
const mostrarListaCachorro = ref(false)

const novoPacote = ref({
  cachorro_id: null,
  cachorros_adicionais_ids: [],
  tipo_plano: 'semanal',
  dia_da_semana: 'terca',
  valor_banho_base: 0,
  valor_transporte: 0,
  valor_cobrado: 0
})

// Valor do banho por cachorro adicional (opcional). Se não informado para um
// cachorro adicional, assume-se o mesmo valor do cachorro principal (dobra o valor).
const valoresAdicionais = reactive({})

const cachorroId = computed(() => {
  const id = Number.parseInt(route.query.cachorro_id, 10)
  if (id && !novoPacote.value.cachorro_id) novoPacote.value.cachorro_id = id
  return id || null
})

const cachorros = computed(() => {
  const lista = []
  clientesStore.clientes.forEach(c => {
    if (c.cachorros) lista.push(...c.cachorros.map(dog => ({ ...dog, cliente: c })))
  })
  return lista
})
const cachorroSelecionado = computed(() => cachorros.value.find(d => d.id === cachorroId.value))

// Outros cachorros do mesmo cliente do cachorro principal escolhido (pré-selecionado
// via rota ou pelo autocomplete), para permitir fechar um único pacote para vários pets.
const outrosCachorrosDoCliente = computed(() => {
  const principal = cachorros.value.find(d => d.id === novoPacote.value.cachorro_id)
  if (!principal || !principal.cliente) return []
  return cachorros.value.filter(d => d.cliente?.id === principal.cliente.id && d.id !== principal.id)
})

const cachorrosAdicionaisSelecionados = computed(() =>
  outrosCachorrosDoCliente.value.filter(c => novoPacote.value.cachorros_adicionais_ids.includes(c.id))
)
const pacotesFiltrados = computed(() => {
  let lista = pacotesStore.pacotes
  if (filtroStatus.value === 'ativos') lista = lista.filter(p => p.ativo)
  else if (filtroStatus.value === 'inativos') lista = lista.filter(p => !p.ativo)
  if (filtroPagamento.value !== 'todos') lista = lista.filter(p => p.status_pagamento === filtroPagamento.value)
  const busca = buscaCliente.value.trim().toLowerCase()
  if (busca) lista = lista.filter(p => p.cliente_nome?.toLowerCase().includes(busca))
  return lista
})

const cachorrosFiltradosNovo = computed(() => {
  const termo = buscaCachorroNovo.value.trim().toLowerCase()
  if (!termo) return cachorros.value
  return cachorros.value.filter(c =>
    c.nome.toLowerCase().includes(termo) || (c.cliente?.nome || '').toLowerCase().includes(termo)
  )
})

function limparValoresAdicionais() {
  Object.keys(valoresAdicionais).forEach(key => delete valoresAdicionais[key])
}

function abrirNovoPacote() {
  buscaCachorroNovo.value = ''
  mostrarListaCachorro.value = false
  novoPacote.value.cachorros_adicionais_ids = []
  limparValoresAdicionais()
  showNovoPacote.value = true
}

function selecionarCachorroNovo(cachorro) {
  novoPacote.value.cachorro_id = cachorro.id
  novoPacote.value.cachorros_adicionais_ids = []
  limparValoresAdicionais()
  buscaCachorroNovo.value = `${cachorro.nome} (${cachorro.cliente?.nome || ''})`
  mostrarListaCachorro.value = false
}

function onDigitarCachorroNovo() {
  // Se o texto foi alterado, invalida a seleção até escolher um item da lista de novo.
  novoPacote.value.cachorro_id = null
  novoPacote.value.cachorros_adicionais_ids = []
  limparValoresAdicionais()
  mostrarListaCachorro.value = true
}

function onBlurCachorroNovo() {
  // Pequeno atraso para permitir que o clique num item da lista seja processado antes de fechar.
  setTimeout(() => { mostrarListaCachorro.value = false }, 150)
}

function calcularSugeridoNovo() {
  const qtd = novoPacote.value.tipo_plano === 'semanal' ? 4 : (novoPacote.value.tipo_plano === 'quinzenal' ? 2 : 1)
  const base = novoPacote.value.valor_banho_base || 0
  const transporte = novoPacote.value.valor_transporte || 0

  // Cada cachorro adicional soma seu próprio valor por banho; se não informado,
  // assume o mesmo valor do cachorro principal (dobra o valor do banho).
  const valorPorBanho = novoPacote.value.cachorros_adicionais_ids.reduce((total, id) => {
    const valorExtra = valoresAdicionais[id]
    return total + (valorExtra || base)
  }, base)

  novoPacote.value.valor_cobrado = (valorPorBanho * qtd) + transporte
}

function voltarTodosPacotes() { router.push('/pacotes') }
function abrirPagamento(pacote) { pacoteSelecionado.value = pacote; showPagamento.value = true }
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
  } catch (err) { alert('Erro: ' + err) }
}
async function criarPacote() {
  if (!novoPacote.value.cachorro_id) {
    alert('Selecione um cachorro válido na lista.')
    return
  }
  if (novoPacote.value.valor_cobrado <= 0 || novoPacote.value.valor_banho_base <= 0) {
    alert('O valor do banho e o valor total devem ser maiores que zero.')
    return
  }

  try {
    const valoresAdicionaisValidos = Object.fromEntries(
      Object.entries(valoresAdicionais).filter(([, v]) => typeof v === 'number' && !Number.isNaN(v))
    )
    await pacotesStore.criarPacote({ ...novoPacote.value, valores_adicionais: valoresAdicionaisValidos })
    showNovoPacote.value = false
    // Resetar formulário
    novoPacote.value = { cachorro_id: null, cachorros_adicionais_ids: [], tipo_plano: 'semanal', dia_da_semana: 'terca', valor_banho_base: 0, valor_transporte: 0, valor_cobrado: 0 }
    limparValoresAdicionais()
    buscaCachorroNovo.value = ''
  } catch (err) { alert('Erro ao criar pacote: ' + err) }
}
function verDetalhes(pacote) { router.push(`/pacotes/${pacote.id}`) }

onMounted(async () => {
  if (cachorroId.value) {
    await pacotesStore.fetchPacotes({ cachorro_id: cachorroId.value, incluir_inativos: true })
  } else {
    await pacotesStore.fetchPacotes({ incluir_inativos: true })
  }
  await clientesStore.fetchClientes()
})
</script>

<style scoped>
.pacotes-view {
  --marrom:        #3b2a1a;
  --marrom-medio:  #5a3e28;
  --dourado:       #d4a843;
  --dourado-claro: #f5e4a8;
  --verde:         #6b8f4e;
  --creme:         #faf6ef;
  --creme-escuro:  #f0e8d8;
  --text:          #2e1e0f;
  --text-muted:    #7a6251;
  --white:         #ffffff;
  --radius:        10px;
  --shadow:        0 2px 12px rgba(59,42,26,0.1);
}

.page-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 1.2rem;
}
.page-title {
  font-size: 1.6rem; font-weight: 800; color: var(--marrom);
  border-left: 5px solid var(--dourado); padding-left: 0.75rem;
}
.header-btns { display: flex; gap: 0.6rem; }

/* FILTROS */
.filters-bar { display: flex; gap: 0.75rem; margin-bottom: 1.2rem; flex-wrap: wrap; }
.filter-select {
  padding: 0.6rem 0.9rem;
  border: 2px solid var(--creme-escuro); border-radius: 8px;
  background: var(--creme); color: var(--text); font-size: 0.9rem; font-weight: 600;
  cursor: pointer; transition: border-color 0.15s;
}
.filter-select:focus { border-color: var(--dourado); outline: none; }

.search-box {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1 1 240px;
  max-width: 320px;
}
.search-icon {
  position: absolute;
  left: 0.75rem;
  font-size: 0.9rem;
  opacity: 0.6;
  pointer-events: none;
}
.search-input {
  width: 100%;
  padding: 0.6rem 2rem 0.6rem 2.2rem;
  border: 2px solid var(--creme-escuro); border-radius: 8px;
  background: var(--creme); color: var(--text); font-size: 0.9rem;
  box-sizing: border-box;
  transition: border-color 0.15s;
}
.search-input:focus { border-color: var(--dourado); outline: none; }
.search-clear {
  position: absolute;
  right: 0.6rem;
  border: none; background: none; cursor: pointer;
  color: var(--text-muted); font-size: 0.85rem; font-weight: 700;
  padding: 0.2rem;
  line-height: 1;
}
.search-clear:hover { color: var(--marrom); }

/* GRID */
.grid-3 { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.2rem; }

.empty-state {
  grid-column: 1 / -1; text-align: center;
  padding: 3rem; color: var(--text-muted); font-style: italic;
}

/* BOTÕES */
.btn {
  padding: 0.6rem 1.1rem; border: none; border-radius: 8px;
  font-weight: 700; cursor: pointer; font-size: 0.9rem; transition: all 0.15s;
}
.btn-primario { background: var(--marrom); color: var(--dourado); }
.btn-primario:hover { background: var(--marrom-medio); }
.btn-ghost { background: var(--creme-escuro); color: var(--marrom); }
.btn-ghost:hover { background: var(--dourado-claro); }
.btn-cancelar { background: var(--creme-escuro); color: var(--marrom); }
.btn-cancelar:hover { background: #e0d5c2; }

/* MODAL */
.modal-wrap { position: fixed; inset: 0; display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.45); }
.modal-content {
  background: var(--white); padding: 2rem; border-radius: var(--radius);
  width: 90%; max-width: 480px; position: relative; z-index: 1001;
  border-top: 5px solid var(--dourado);
  box-shadow: 0 8px 32px rgba(59,42,26,0.2);
}
.modal-title { font-size: 1.1rem; font-weight: 800; color: var(--marrom); margin-bottom: 1.2rem; }

.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.3rem; font-weight: 700; font-size: 0.9rem; color: var(--marrom); }
.form-group input,
.form-group select {
  width: 100%; padding: 0.6rem 0.75rem;
  border: 2px solid var(--creme-escuro); border-radius: 7px;
  font-size: 0.95rem; color: var(--text); background: var(--creme);
  transition: border-color 0.15s; box-sizing: border-box;
}
.form-group input:focus,
.form-group select:focus { border-color: var(--dourado); outline: none; }
.form-group input:disabled { opacity: 0.7; cursor: not-allowed; }
.form-actions { display: flex; gap: 0.75rem; margin-top: 1.5rem; }
.form-actions .btn { flex: 1; }

/* AUTOCOMPLETE DE CACHORRO */
.autocomplete { position: relative; }
.autocomplete-lista {
  position: absolute; top: calc(100% + 4px); left: 0; right: 0;
  background: var(--white); border: 2px solid var(--creme-escuro); border-radius: 7px;
  box-shadow: 0 6px 20px rgba(59,42,26,0.18);
  max-height: 220px; overflow-y: auto; z-index: 10;
}
.autocomplete-item {
  padding: 0.6rem 0.75rem; font-size: 0.92rem; color: var(--text); cursor: pointer;
}
.autocomplete-item:hover { background: var(--dourado-claro); }
.autocomplete-sub { color: var(--text-muted); font-size: 0.82rem; }
.autocomplete-empty { padding: 0.6rem 0.75rem; font-size: 0.88rem; color: var(--text-muted); font-style: italic; }

/* CHECKBOXES DE CACHORROS ADICIONAIS */
.checkbox-lista {
  display: flex; flex-direction: column; gap: 0.4rem;
  border: 2px solid var(--creme-escuro); border-radius: 7px;
  padding: 0.6rem 0.75rem; max-height: 160px; overflow-y: auto;
}
.checkbox-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.92rem; color: var(--text); cursor: pointer; }
.checkbox-item input[type="checkbox"] { width: auto; margin: 0; }
</style>
