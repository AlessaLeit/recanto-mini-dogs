<template>
  <div class="pacote-detail">
    <!-- Header -->
    <div class="header">
      <button @click="voltar" class="btn-back">← Voltar</button>
      <div class="header-info">
        <h1>{{ pacote?.pet_nome || 'Pacote' }}</h1>
        <p class="subheader">{{ pacote?.cliente_nome }}</p>
      </div>
      <div class="status" :class="pacote?.status_pagamento">
        {{ pacote?.status_pagamento?.toUpperCase() || 'EM ABERTO' }}
      </div>
    </div>

    <!-- Info Cards -->
    <div class="info-cards">
      <div class="info-card clickable" @click="abrirEditarPacote" title="Clique para editar plano">
        <span class="label">Plano</span>
        <span class="value">{{ pacote?.tipo_plano?.toUpperCase() }}</span>
        <span class="sub">{{ pacote?.limite_banhos_mes }} banhos/mês</span>
      </div>

      <div class="info-card clickable" @click="abrirEditarPacote" title="Clique para editar dia">
        <span class="label">Dia da Semana</span>
        <span class="value">{{ formatarDiaSemana(pacote?.dia_da_semana) }}</span>
        <span class="sub">Datas geradas automaticamente</span>
      </div>

      <div class="info-card clickable" @click="abrirEditarPacote" title="Clique para editar valores">
        <span class="label">Valor Base do Banho</span>
        <span class="value">R$ {{ formatarValor(pacote?.valor_banho_base || 0) }}</span>
      </div>

      <div class="info-card clickable" @click="abrirEditarPacote" title="Clique para editar valores">
        <span class="label">Valor Cobrado (Pacote)</span>
        <span class="value">R$ {{ formatarValor(pacote?.valor_cobrado) }}</span>
      </div>

      <div class="info-card clickable" @click="abrirEditarPacote" title="Clique para editar transporte">
        <span class="label">Transporte</span>
        <span class="value">R$ {{ formatarValor(pacote?.valor_transporte || 0) }}</span>
        <span class="sub">Clique para alterar</span>
      </div>

      <div class="info-card">
        <span class="label">Qtd. Agendamentos</span>
        <span class="value">{{ pacote?.total_agendamentos || 0 }}</span>
      </div>
    </div>

    <!-- Ações -->
    <div class="actions-bar">
      <button @click="showAddExtra = true" class="btn btn-primary">
        + Adicionar Banho Extra
      </button>
    </div>

    <!-- Tabela de Agendamentos -->
    <div class="agendamentos-section">
      <h3 class="section-title">📅 Agendamentos do Pacote</h3>
      <table class="agendamentos-table" v-if="agendamentos.length">
        <thead>
          <tr>
            <th>Data</th>
            <th>Valor Banho</th>
            <th>Itens Extra</th>
            <th>Valor Extra</th>
            <th>Status</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ag in agendamentos" :key="ag.id" :class="ag.status_presenca">
            <td><strong>{{ formatarData(ag.data_banho) }}</strong></td>
            <td>R$ {{ formatarValor(pacote?.valor_banho_base || 0) }}</td>
            <td class="clickable" @click="abrirEditarExtras(ag)">{{ ag.extras?.info || '-' }}</td>
            <td class="clickable" @click="abrirEditarExtras(ag)">R$ {{ formatarValor(ag.extras?.valor_extra || 0) }}</td>
            <td class="clickable" @click="abrirEditarExtras(ag)">
              <span class="status-badge" :class="ag.status_presenca">
                {{ ag.status_presenca?.toUpperCase() }}
              </span>
            </td>
            <td class="acoes">
              <button @click="abrirEditarExtras(ag)" class="btn-add-extra" title="Adicionar Item Extra">
                +
              </button>
              <button @click="abrirEditarData(ag)" class="btn-edit" title="Editar data">
                📅
              </button>
              <button @click="confirmarRemover(ag)" class="btn-delete" title="Remover">
                🗑️
              </button>
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr class="total-row">
            <td colspan="3" style="text-align: right;"><strong>Total do Pacote (Banhos + Extras):</strong></td>
            <td colspan="3"><strong>R$ {{ formatarValor(totalPacote) }}</strong></td>
          </tr>
        </tfoot>
      </table>
      <div v-else class="empty">
        Nenhum agendamento encontrado.
      </div>
    </div>

    <!-- Modal: Editar Data -->
    <div class="modal" v-if="showEditData">
      <div class="modal-overlay" @click="showEditData = false"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>Editar Data</h3>
          <p class="pet-name-modal">🐶 {{ pacote?.pet_nome }}</p>
        </div>
        <p class="modal-info">Agendamento atual: <strong>{{ formatarData(agEditando?.data_banho) }}</strong></p>
        <div class="form-group">
          <label>Selecione a Nova Data</label>
          <input 
            type="date" 
            v-model="novaData" 
            required
          />
        </div>
        <div class="modal-actions">
          <button @click="showEditData = false" class="btn-secondary">Cancelar</button>
          <button @click="salvarNovaData" class="btn btn-primary" :disabled="!novaData">
            Salvar
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Editar Dados do Pacote -->
    <div class="modal" v-if="showModalEditPacote">
      <div class="modal-overlay" @click="showModalEditPacote = false"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>Configurações do Pacote</h3>
          <p class="pet-name-modal">⚙️ {{ pacote?.pet_nome }}</p>
        </div>

        <div class="grid-form">
          <div class="form-group">
            <label>Tipo de Plano</label>
            <select v-model="formPacote.tipo_plano" class="form-control" @change="recalcularSugerido">
              <option value="semanal">Semanal (4 banhos)</option>
              <option value="quinzenal">Quinzenal (2 banhos)</option>
              <option value="mensal">Mensal (1 banho)</option>
            </select>
          </div>

          <div class="form-group">
            <label>Dia da Semana</label>
            <select v-model="formPacote.dia_da_semana" class="form-control">
              <option value="terca">Terça-feira</option>
              <option value="quarta">Quarta-feira</option>
              <option value="quinta">Quinta-feira</option>
              <option value="sexta">Sexta-feira</option>
              <option value="sabado">Sábado</option>
            </select>
          </div>
        </div>

        <div class="grid-form">
          <div class="form-group">
            <label>Valor Base Banho (R$)</label>
            <input 
              type="number" step="0.01"
              v-model.number="formPacote.valor_banho_base"
              class="form-control"
              @input="recalcularSugerido"
            />
          </div>

          <div class="form-group">
            <label>Transporte Total (R$)</label>
            <input 
              type="number" step="0.01"
              v-model.number="formPacote.valor_transporte"
              class="form-control"
            />
          </div>
        </div>

        <div class="form-group highlight">
          <label>Valor Total Cobrado (R$)</label>
          <input 
            type="number" step="0.01"
            v-model.number="formPacote.valor_cobrado"
            class="form-control"
          />
          <small v-if="sugestaoVisivel" class="helper-text">
            Sugerido pelo plano: R$ {{ formatarValor(valorSugerido) }}
          </small>
        </div>

        <div class="modal-actions">
          <button @click="showModalEditPacote = false" class="btn-secondary">Cancelar</button>
          <button @click="salvarDadosPacote" class="btn-primary">Salvar Alterações</button>
        </div>
      </div>
    </div>

    <!-- Modal: Editar Extras -->
    <div class="modal" v-if="showModalExtras">
      <div class="modal-overlay" @click="showModalExtras = false"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>Editar Agendamento</h3>
          <p class="pet-name-modal">✨ {{ pacote?.pet_nome }}</p>
        </div>
        <div class="form-group">
          <label>Status de Presença</label>
          <select v-model="formExtras.status_presenca" class="form-control">
            <option value="pendente">🟡 PENDENTE</option>
            <option value="concluido">🟢 CONCLUÍDO</option>
            <option value="faltou">🔴 FALTOU / CANCELADO</option>
          </select>
        </div>

        <div class="form-group">
          <label>Itens Extra / Descrição</label>
          <input 
            v-model="formExtras.info" 
            placeholder="Ex: Tosa higiênica, Shampoo especial..."
            class="form-control"
          />
        </div>
        <div class="form-group">
          <label>Valor Extra (R$)</label>
          <input 
            type="number" step="0.01"
            v-model.number="formExtras.valor_extra"
            class="form-control"
          />
        </div>
        <div class="modal-actions">
          <button @click="showModalExtras = false" class="btn-secondary">Cancelar</button>
          <button @click="salvarExtras" class="btn-primary">Salvar</button>
        </div>
      </div>
    </div>

    <!-- Modal: Adicionar Extra -->
    <div class="modal" v-if="showAddExtra">
      <div class="modal-overlay" @click="showAddExtra = false"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>Banho Extra</h3>
          <p class="pet-name-modal">➕ {{ pacote?.pet_nome }}</p>
        </div>
        <p class="modal-info">Adicione um banho avulso fora do cronograma do plano.</p>
        <div class="form-group">
          <label>Data do Banho</label>
          <input 
            type="date" 
            v-model="dataExtra" 
            required
          />
        </div>
        <div class="modal-actions">
          <button @click="showAddExtra = false" class="btn-secondary">Cancelar</button>
          <button @click="salvarExtra" class="btn btn-primary" :disabled="!dataExtra">
            Adicionar
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Confirmação Remover -->
    <div class="modal" v-if="showConfirmRemove">
      <div class="modal-overlay" @click="showConfirmRemove = false"></div>
      <div class="modal-content modal-confirm">
        <div class="modal-header danger">
          <h3>⚠️ Confirmar Remoção</h3>
        </div>
        <p>Tem certeza que deseja remover o agendamento de <strong>{{ formatarData(agRemovendo?.data_banho) }}</strong>?</p>
        <p class="warning">Esta ação não pode ser desfeita.</p>
        <div class="modal-actions">
          <button @click="showConfirmRemove = false" class="btn-secondary">Cancelar</button>
          <button @click="executarRemover" class="btn btn-danger">
            Remover
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePacotesStore } from '../stores/pacotes.js'

const route = useRoute()
const router = useRouter()
const pacotesStore = usePacotesStore()

const pacote = ref(null)
const agendamentos = ref([])
const loading = ref(false)

// Modais
const showEditData = ref(false)
const showAddExtra = ref(false)
const showConfirmRemove = ref(false)
const showModalExtras = ref(false)
const showModalEditPacote = ref(false)

// Dados dos modais
const agEditando = ref(null)
const novaData = ref('')
const dataExtra = ref('')
const agRemovendo = ref(null)
const agExtras = ref(null)
const formExtras = ref({ info: '', valor_extra: 0, status_presenca: 'pendente' })
const formPacote = ref({ tipo_plano: '', dia_da_semana: '', valor_banho_base: 0, valor_cobrado: 0, valor_transporte: 0 })
const valorSugerido = ref(0)
const sugestaoVisivel = ref(false)

const pacoteId = computed(() => parseInt(route.params.id))

// Computed: total do pacote (soma Valor Base + Valor Extra de cada agendamento)
const totalPacote = computed(() => {
  if (!pacote.value) return 0
  const valorBase = pacote.value.valor_banho_base || 0
  const transporte = pacote.value.valor_transporte || 0
  const agendamentosTotal = agendamentos.value.reduce((sum, ag) => {
    const valorExtra = ag.extras?.valor_extra || 0
    return sum + valorBase + valorExtra
  }, 0)
  return agendamentosTotal + transporte
})

async function carregarPacote() {
  loading.value = true
  try {
    const data = await pacotesStore.fetchPacote(pacoteId.value)
    pacote.value = data
    agendamentos.value = data.agendamentos || []
  } catch (err) {

  } finally {
    loading.value = false
  }
}


function voltar() {
  router.push('/pacotes')
}

function formatarData(isoDate) {
  if (!isoDate) return '-'
  return new Date(isoDate + 'T00:00:00').toLocaleDateString('pt-BR')
}

function formatarValor(valor) {
  return Number(valor || 0).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

function formatarDiaSemana(dia) {
  const map = {
    terca: 'Terça',
    quarta: 'Quarta',
    quinta: 'Quinta',
    sexta: 'Sexta',
    sabado: 'Sábado'
  }
  return map[dia] || '-' 
}


// Editar Data
function abrirEditarData(ag) {
  agEditando.value = ag
  novaData.value = ag.data_banho
  showEditData.value = true
}

async function salvarNovaData() {
  if (!novaData.value || !agEditando.value) return
  try {
    await pacotesStore.updateAgendamentoData(agEditando.value.id, novaData.value)
    showEditData.value = false
    agEditando.value = null
    novaData.value = ''

  } catch (err) {

  }
}

// Edição do Pacote (Info Cards)
function abrirEditarPacote() {
  formPacote.value = {
    tipo_plano: pacote.value.tipo_plano,
    dia_da_semana: pacote.value.dia_da_semana,
    valor_banho_base: pacote.value.valor_banho_base,
    valor_cobrado: pacote.value.valor_cobrado,
    valor_transporte: pacote.value.valor_transporte || 0
  }
  recalcularSugerido()
  sugestaoVisivel.value = false // Reseta o aviso ao abrir
  showModalEditPacote.value = true
}

function recalcularSugerido() {
  const qtd = formPacote.value.tipo_plano === 'semanal' ? 4 : formPacote.value.tipo_plano === 'quinzenal' ? 2 : 1
  valorSugerido.value = (formPacote.value.valor_banho_base || 0) * qtd
  formPacote.value.valor_cobrado = valorSugerido.value
  sugestaoVisivel.value = true
}

async function salvarDadosPacote() {
  try {
    // Usando atualizarPacote para manter o padrão da Store
    await pacotesStore.atualizarPacote(pacoteId.value, { ...formPacote.value })
    
    showModalEditPacote.value = false
    await carregarPacote() // Recarrega os dados para atualizar os cards e o total
  } catch (err) {
    console.error("Erro ao atualizar pacote:", err)
    alert("Erro ao salvar as alterações do pacote.")
  }
}

// Extras
function abrirEditarExtras(ag) {
  agExtras.value = ag
  const info = ag.extras?.info || (typeof ag.extras === 'string' ? ag.extras : '')
  const valor = ag.extras?.valor_extra || 0
  
  formExtras.value = {
    info: info,
    valor_extra: valor,
    status_presenca: ag.status_presenca || 'pendente'
  }
  showModalExtras.value = true
}

async function salvarExtras() {
  try {
    await pacotesStore.updateAgendamento(agExtras.value.id, { 
      status_presenca: formExtras.value.status_presenca,
      extras: { 
        info: formExtras.value.info, 
        valor_extra: formExtras.value.valor_extra 
      } 
    })
    showModalExtras.value = false
    await carregarPacote()
  } catch (err) {}
}

// Adicionar Extra
async function salvarExtra() {
  if (!dataExtra.value) return
  try {
    await pacotesStore.adicionarExtra(pacoteId.value, dataExtra.value)
    showAddExtra.value = false
    dataExtra.value = ''

  } catch (err) {

  }
}

// Remover
function confirmarRemover(ag) {
  agRemovendo.value = ag
  showConfirmRemove.value = true
}

async function executarRemover() {
  if (!agRemovendo.value) return
  try {
    await pacotesStore.removerAgendamento(agRemovendo.value.id)
    showConfirmRemove.value = false
    agRemovendo.value = null

  } catch (err) {

  }
}

onMounted(carregarPacote)
</script>

<style scoped>
.pacote-detail {
  max-width: 1100px;
  margin: 0 auto;
  padding: 1.5rem;
}

/* Header */
.header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e2e8f0;
}

.btn-back {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: background 0.2s;
}

.btn-back:hover {
  background: #f7fafc;
}

.header-info {
  flex: 1;
}

.header-info h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #2d3748;
}

.subheader {
  margin: 0.25rem 0 0 0;
  color: #718096;
  font-size: 0.9rem;
}

.status {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.85rem;
}

.status.em_aberto { background: #fed7d7; color: #c53030; }
.status.pago { background: #c6f6d5; color: #22543d; }
.status.parcial { background: #feebc8; color: #744210; }

/* Info Cards */
.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.info-card {
  background: white;
  border-radius: 12px;
  padding: 1.25rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  border-bottom: 4px solid #667eea;
}

.info-card.clickable {
  cursor: pointer;
  transition: transform 0.1s, box-shadow 0.1s;
}

.info-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px -2px rgba(0, 0, 0, 0.15);
  border-color: #4299e1;
  background-color: #f8faff;
}

.info-card .label {
  font-size: 0.8rem;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.5rem;
}

.info-card .value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #2d3748;
}

.info-card .sub {
  font-size: 0.85rem;
  color: #a0aec0;
  margin-top: 0.25rem;
}

/* Actions Bar */
.actions-bar {
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: flex-end;
}

/* Agendamentos Section */
.agendamentos-section {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.section-title {
  margin: 0 0 1.25rem 0;
  color: #2d3748;
  font-size: 1.1rem;
}

.agendamentos-table {
  width: 100%;
  border-collapse: collapse;
}

.agendamentos-table th,
.agendamentos-table td {
  padding: 1rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

.agendamentos-table th {
  background: #f7fafc;
  font-weight: 600;
  color: #4a5568;
  font-size: 0.85rem;
  text-transform: uppercase;
}

.agendamentos-table tr:hover {
  background: #f7fafc;
}

.agendamentos-table tr.pendente { opacity: 0.85; }
.agendamentos-table tr.concluido { background: #f0fff4; }
.agendamentos-table tr.faltou { background: #fff5f5; }

.status-badge {
  padding: 0.3rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.pendente { background: #fef3c7; color: #92400e; }
.status-badge.concluido { background: #d1fae5; color: #065f46; }
.status-badge.faltou { background: #fee2e2; color: #991b1b; }

.acoes {
  display: flex;
  gap: 0.5rem;
}

.btn-add-extra {
  background: #48bb78;
  color: white;
  border: none;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-add-extra:hover {
  background: #38a169;
}

.btn-edit, .btn-delete {
  background: none;
  border: 1px solid #e2e8f0;
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.btn-edit:hover {
  background: #ebf8ff;
  border-color: #4299e1;
}

.btn-delete:hover {
  background: #fff5f5;
  border-color: #f56565;
}

.clickable {
  cursor: pointer;
  text-decoration: underline dotted #cbd5e0;
}

/* Total Row */
.total-row {
  background: #e6fffa !important;
  font-size: 1.1rem;
}

.total-row td {
  padding: 1rem 0.75rem;
  border-top: 2px solid #38b2ac;
}

.total-row strong {
  color: #22543d;
}

/* Empty State */
.empty {
  text-align: center;
  padding: 3rem;
  color: #718096;
  font-style: italic;
}

/* Buttons */
.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.btn-primary {
  background: #4299e1;
  color: white;
}

.btn-primary:hover {
  background: #3182ce;
}

.btn-secondary {
  background: #edf2f7;
  color: #4a5568;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

.btn-danger {
  background: #f56565;
  color: white;
}

.btn-danger:hover {
  background: #e53e3e;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal */
.modal {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.5);
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  width: 90%;
  max-width: 450px;
  position: relative;
  z-index: 1001;
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
}

.modal-content h3 {
  margin: 0 0 0.5rem 0;
  color: #2d3748;
}

.modal-content p {
  color: #718096;
  margin-bottom: 1.5rem;
}

.modal-confirm .warning {
  color: #c53030;
  font-size: 0.85rem;
  margin-top: 0.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.4rem;
  font-weight: 600;
  color: #4a5568;
  font-size: 0.9rem;
}

.grid-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.highlight .form-control {
  border-color: #667eea;
  background-color: #f8faff;
  font-weight: bold;
  font-size: 1.1rem;
}

.helper-text {
  color: #718096;
  font-size: 0.75rem;
  margin-top: 0.25rem;
  display: block;
}

.form-group input[type="date"] {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 1rem;
  box-sizing: border-box;
}

.form-control {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 1rem;
}
</style>
