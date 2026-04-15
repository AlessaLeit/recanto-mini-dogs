<template>
  <div class="pacote-detail">
    <div class="header">
      <button @click="voltar" class="btn-back">← Voltar</button>
      <h1>Pacote {{ pacote?.id }} - {{ pacote?.pet_nome }}</h1>
      <div class="status" :class="pacote?.status_pagamento">
        {{ pacote?.status_pagamento?.toUpperCase() || 'EM ABERTO' }}
      </div>
    </div>

    <div class="metrics">
      <span>Tipo: {{ pacote?.tipo_plano?.toUpperCase() }} ({{ pacote?.limite_banhos_mes }} agend./mês)</span>
      <span>Total agendamentos: {{ pacote?.total_agendamentos || 0 }}</span>
      <button @click="gerarAgendamentos" class="btn-gerar" v-if="podeGerar">
        Gerar Agendamentos Pendentes
      </button>
    </div>

    <div class="agendamentos-list">
      <h3>Agendamentos ({{ agendamentos.length }})</h3>
      <div class="list">
        <div v-for="ag in agendamentos" :key="ag.id" class="ag-item" :class="ag.status_presenca">
          <div class="ag-info">
            <strong>{{ formatDate(ag.data_banho) }}</strong>
            <span class="status-badge">{{ ag.status_presenca.toUpperCase() }}</span>
          </div>
          <div class="ag-extras" v-if="ag.extras && Object.keys(ag.extras).length">
            {{ Object.entries(ag.extras).map(([k,v]) => `${k}: ${v}`).join(', ') }}
          </div>
          <button @click="editarAgendamento(ag)" class="btn-edit">Editar</button>
        </div>
        <div v-if="agendamentos.length === 0" class="empty">
          Nenhum agendamento. Clique em "Gerar" para criar automáticos.
        </div>
      </div>
    </div>

    <!-- Modal Editar -->
    <div class="modal" v-if="showModal">
      <div class="modal-overlay" @click="showModal = false"></div>
      <div class="modal-content">
        <h3>Editar Agendamento - {{ formatDate(editAg?.data_banho) }}</h3>
        <form @submit.prevent="salvarEdicao">
          <div class="form-group">
            <label>Status</label>
            <select v-model="editForm.status_presenca" required>
              <option value="pendente">Pendente (cinza)</option>
              <option value="concluido">Concluído (verde)</option>
              <option value="faltou">Faltou (vermelho)</option>
            </select>
          </div>
          <div class="form-group">
            <label>Extras JSON</label>
            <textarea v-model="editForm.extrasJson" rows="4" placeholder='{"remedio": "nome", "obs": "texto"}'></textarea>
          </div>
          <div class="form-actions">
            <button type="button" @click="showModal = false" class="btn-cancel">Cancelar</button>
            <button type="submit" class="btn-save">Salvar</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePacotesStore } from '../stores/pacotes.js'

const route = useRoute()
const router = useRouter()
const pacotesStore = usePacotesStore()

const pacote = ref(null)
const agendamentos = ref([])
const showModal = ref(false)
const editAg = ref(null)
const editForm = ref({ status_presenca: 'pendente', extrasJson: '{}' })
const loading = ref(false)

const pacoteId = computed(() => parseInt(route.params.id))

async function carregarPacote() {
  loading.value = true
  try {
    await pacotesStore.fetchPacote(pacoteId.value)
    pacote.value = pacotesStore.pacoteAtual
    agendamentos.value = pacote.value?.agendamentos || []
  } catch (err) {
    alert('Erro ao carregar: ' + err)
  } finally {
    loading.value = false
  }
}

function voltar() {
  router.push('/pacotes')
}

function podeGerar() {
  return agendamentos.value.length < (pacote.value?.limite_banhos_mes * 3 || 0)
}

async function gerarAgendamentos() {
  if (!confirm('Gerar agendamentos automáticos por 3 meses?')) return
  try {
    // Chama API opcional
    // await pacotesStore.gerarAgendamentos(pacoteId.value)
    alert('Funcionalidade em desenvolvimento - simule criando manualmente')
    await carregarPacote()
  } catch (err) {
    alert('Erro: ' + err)
  }
}

function editarAgendamento(ag) {
  editAg.value = ag
  editForm.value.status_presenca = ag.status_presenca
  editForm.value.extrasJson = JSON.stringify(ag.extras || {}, null, 2)
  showModal.value = true
}

async function salvarEdicao() {
  try {
    let extras = {}
    try {
      extras = JSON.parse(editForm.value.extrasJson)
    } catch {
      alert('JSON inválido nos extras')
      return
    }
    
    await pacotesStore.updateAgendamento(editAg.value.id, {
      status_presenca: editForm.value.status_presenca,
      extras
    })
    
    showModal.value = false
    await carregarPacote()
    alert('Agendamento atualizado!')
  } catch (err) {
    alert('Erro: ' + err)
  }
}

function formatDate(isoDate) {
  return new Date(isoDate).toLocaleDateString('pt-BR')
}

onMounted(carregarPacote)
</script>

<style scoped>
.pacote-detail {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

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
  font-size: 1.5rem;
  cursor: pointer;
}

.status {
  margin-left: auto;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 500;
}

.status.em_aberto { background: #fed7d7; color: #c53030; }
.status.pago { background: #c6f6d5; color: #22543d; }
.status.parcial { background: #feebc8; color: #744210; }

.metrics {
  display: flex;
  gap: 2rem;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.btn-gerar {
  background: #48bb78;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
}

.agendamentos-list h3 {
  margin-bottom: 1rem;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.ag-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 8px;
  border-left: 4px solid;
}

.ag-item.pendente { border-left-color: #a0aec0; background: #f7fafc; }
.ag-item.concluido { border-left-color: #48bb78; background: #f0fff4; }
.ag-item.faltou { border-left-color: #f56565; background: #fff5f5; }

.ag-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
}

.ag-extras {
  font-size: 0.9rem;
  color: #718096;
  max-width: 200px;
}

.btn-edit {
  background: #4299e1;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
}

.empty {
  text-align: center;
  padding: 3rem;
  color: #718096;
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-overlay {
  position: absolute;
  inset: 0;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

select, textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-family: monospace;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-cancel {
  flex: 1;
  background: #a0aec0;
  color: white;
  border: none;
  padding: 0.75rem;
  border-radius: 6px;
  cursor: pointer;
}

.btn-save {
  flex: 1;
  background: #48bb78;
  color: white;
  border: none;
  padding: 0.75rem;
  border-radius: 6px;
  cursor: pointer;
}
</style>

