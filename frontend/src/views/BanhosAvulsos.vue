<template>
  <div class="avulsos-view">
    <div class="page-header">
      <h1 class="page-title">🛁 Banhos Avulsos</h1>
    </div>

    <div class="form-card">
      <div class="card-title"><span class="card-title-bar"></span>Novo Banho Avulso</div>
      <form @submit.prevent="registrar" class="form-grid">
        <div class="form-group">
          <label for="av-cachorro">Nome do Cachorro</label>
          <input id="av-cachorro" v-model="form.pet_nome_avulso" placeholder="Ex: Rex" required />
        </div>
        <div class="form-group">
          <label for="av-cliente">Nome do Cliente</label>
          <input id="av-cliente" v-model="form.cliente_nome_avulso" placeholder="Ex: Maria Silva" required />
        </div>
        <div class="form-group">
          <label for="av-data">Data do Banho</label>
          <input id="av-data" v-model="form.data_banho" type="date" required />
        </div>
        <div class="form-group">
          <label for="av-turno">Turno</label>
          <select id="av-turno" v-model="form.turno">
            <option value="manha">🌅 Manhã</option>
            <option value="tarde">🌇 Tarde</option>
          </select>
        </div>
        <div class="form-group">
          <label for="av-valor">Valor (R$)</label>
          <input id="av-valor" v-model.number="form.valor_avulso" type="number" step="0.01" min="0" required />
        </div>
        <div class="form-group form-group-wide">
          <label for="av-obs">Observação</label>
          <input id="av-obs" v-model="form.observacao" placeholder="Ex: Tosa higiênica (deixe em branco se for só banho)" />
        </div>
        <div class="form-actions">
          <button type="submit" class="btn btn-primario" :disabled="salvando">
            {{ salvando ? 'Salvando...' : '+ Registrar Banho Avulso' }}
          </button>
        </div>
      </form>
    </div>

    <div class="lista-card">
      <div class="card-title"><span class="card-title-bar"></span>Banhos Avulsos Registrados</div>
      <div v-if="loading" class="empty-state">Carregando...</div>
      <div v-else-if="avulsos.length === 0" class="empty-state">Nenhum banho avulso registrado ainda.</div>
      <table v-else class="avulsos-table">
        <thead>
          <tr>
            <th>Cachorro / Cliente</th>
            <th>Data</th>
            <th>Turno</th>
            <th>Valor</th>
            <th>Observação</th>
            <th>Status</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ag in avulsos" :key="ag.id">
            <td>
              <strong>{{ ag.pet_nome_avulso }}</strong>
              <div class="sub">{{ ag.cliente_nome_avulso }}</div>
            </td>
            <td>{{ formatarData(ag.data_banho) }}</td>
            <td>{{ ag.turno === 'tarde' ? 'Tarde' : 'Manhã' }}</td>
            <td>R$ {{ formatarValor(ag.valor_avulso) }}</td>
            <td class="col-obs">{{ ag.extras?.info || '-' }}</td>
            <td>
              <select :value="ag.status_presenca" @change="mudarStatus(ag, $event.target.value)" class="status-select" :class="ag.status_presenca">
                <option value="pendente">🟡 Pendente</option>
                <option value="concluido">🟢 Concluído</option>
                <option value="faltou">🔴 Faltou</option>
              </select>
            </td>
            <td>
              <button @click="confirmarRemover(ag)" class="btn-acao btn-acao-perigo" title="Excluir">✕</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Confirmar Exclusão -->
    <div class="modal-overlay" v-if="removendo" @click="removendo = null">
      <div class="modal" @click.stop>
        <h3 class="modal-title">⚠️ Confirmar Exclusão</h3>
        <p class="modal-info">
          Excluir o banho avulso de <strong>{{ removendo.pet_nome_avulso }}</strong> ({{ removendo.cliente_nome_avulso }})
          em <strong>{{ formatarData(removendo.data_banho) }}</strong>?
        </p>
        <div class="modal-actions">
          <button @click="removendo = null" class="btn btn-cancelar">Cancelar</button>
          <button @click="executarRemover" class="btn btn-perigo">Excluir</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAgendamentosStore } from '../stores/agendamentos.js'
import { storeToRefs } from 'pinia'

const agendamentosStore = useAgendamentosStore()
const { avulsos } = storeToRefs(agendamentosStore)

const loading = ref(false)
const salvando = ref(false)
const removendo = ref(null)

function formDefault() {
  return {
    pet_nome_avulso: '',
    cliente_nome_avulso: '',
    data_banho: new Date().toISOString().split('T')[0],
    turno: 'manha',
    valor_avulso: 0,
    observacao: ''
  }
}

const form = ref(formDefault())

function formatarData(dataStr) {
  return new Date(dataStr + 'T00:00:00').toLocaleDateString('pt-BR')
}
function formatarValor(valor) {
  return Number(valor || 0).toFixed(2).replace('.', ',')
}

async function carregar() {
  loading.value = true
  try {
    await agendamentosStore.fetchAvulsos()
  } catch (err) {
    alert('Erro ao carregar banhos avulsos: ' + err.message)
  } finally {
    loading.value = false
  }
}

async function registrar() {
  salvando.value = true
  try {
    await agendamentosStore.criarAvulso({ ...form.value })
    form.value = formDefault()
    alert('Banho avulso registrado com sucesso!')
  } catch (err) {
    alert('Erro ao registrar banho avulso: ' + (err.response?.data?.detail || err.message))
  } finally {
    salvando.value = false
  }
}

async function mudarStatus(ag, novoStatus) {
  try {
    await agendamentosStore.updateStatus(ag.id, { status_presenca: novoStatus })
    ag.status_presenca = novoStatus
  } catch (err) {
    alert('Erro ao atualizar status: ' + err.message)
  }
}

function confirmarRemover(ag) {
  removendo.value = ag
}

async function executarRemover() {
  if (!removendo.value) return
  try {
    await agendamentosStore.deletarAvulso(removendo.value.id)
    removendo.value = null
  } catch (err) {
    alert('Erro ao excluir: ' + err.message)
  }
}

onMounted(carregar)
</script>

<style scoped>
.avulsos-view {
  --marrom:        #3b2a1a;
  --marrom-medio:  #5a3e28;
  --dourado:       #d4a843;
  --dourado-claro: #f5e4a8;
  --verde:         #6b8f4e;
  --verde-bg:      #eef4e6;
  --creme:         #faf6ef;
  --creme-escuro:  #f0e8d8;
  --text:          #2e1e0f;
  --text-muted:    #7a6251;
  --white:         #ffffff;
  --radius:        10px;
  --shadow:        0 2px 12px rgba(59,42,26,0.1);
}

.page-header { margin-bottom: 1.2rem; }
.page-title {
  font-size: 1.6rem; font-weight: 800; color: var(--marrom);
  border-left: 5px solid var(--dourado); padding-left: 0.75rem;
}

.form-card,
.lista-card {
  background: var(--white); border-radius: var(--radius);
  padding: 1.4rem; box-shadow: var(--shadow); margin-bottom: 1.2rem;
}
.card-title {
  font-size: 1rem; font-weight: 800; color: var(--marrom);
  margin-bottom: 1rem; display: flex; align-items: center; gap: 8px;
}
.card-title-bar { display: inline-block; width: 4px; height: 16px; background: var(--dourado); border-radius: 2px; }

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}
.form-group-wide { grid-column: 1 / -1; }
.form-group label { display: block; margin-bottom: 0.3rem; font-weight: 700; font-size: 0.88rem; color: var(--marrom); }
.form-group input,
.form-group select {
  width: 100%; padding: 0.6rem 0.75rem;
  border: 2px solid var(--creme-escuro); border-radius: 7px;
  font-size: 0.95rem; color: var(--text); background: var(--creme);
  transition: border-color 0.15s; box-sizing: border-box;
}
.form-group input:focus,
.form-group select:focus { border-color: var(--dourado); outline: none; }

.form-actions { grid-column: 1 / -1; display: flex; justify-content: flex-end; }

.empty-state { text-align: center; padding: 2rem; color: var(--text-muted); font-style: italic; }

/* TABELA */
.avulsos-table { width: 100%; border-collapse: collapse; }
.avulsos-table th {
  padding: 0.85rem 0.9rem; text-align: left; background: var(--creme);
  font-weight: 800; color: var(--text-muted); font-size: 0.78rem;
  text-transform: uppercase; letter-spacing: 0.5px;
  border-bottom: 2px solid var(--creme-escuro);
}
.avulsos-table td {
  padding: 0.85rem 0.9rem; border-bottom: 1px solid var(--creme-escuro);
  font-size: 0.9rem; color: var(--text); vertical-align: middle;
}
.avulsos-table tbody tr:last-child td { border-bottom: none; }
.avulsos-table tbody tr:hover td { background: var(--creme); }
.sub { color: var(--text-muted); font-size: 0.82rem; margin-top: 2px; }
.col-obs { color: var(--text-muted); max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.status-select {
  padding: 0.4rem 0.6rem; border-radius: 6px; border: 2px solid var(--creme-escuro);
  font-size: 0.82rem; font-weight: 700; cursor: pointer; background: var(--white);
}
.status-select.pendente  { color: #6b4c00; border-color: var(--dourado-claro); }
.status-select.concluido { color: var(--verde); border-color: var(--verde); }
.status-select.faltou    { color: #b94040; border-color: #f5c0c0; }

.btn-acao {
  border: none; padding: 0.38rem 0.7rem; border-radius: 6px; cursor: pointer;
  font-size: 0.9rem; font-weight: 700; transition: all 0.15s; line-height: 1;
}
.btn-acao-perigo { background: #fdeaea; color: #b94040; border: 1px solid #f5c0c0; }
.btn-acao-perigo:hover { background: #f8c8c8; }

/* MODAL */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal {
  background: var(--white); padding: 2rem; border-radius: var(--radius);
  max-width: 440px; width: 90%; border-top: 5px solid var(--dourado);
  box-shadow: 0 8px 32px rgba(59,42,26,0.2);
}
.modal-title { font-size: 1.1rem; font-weight: 800; color: var(--marrom); margin-bottom: 1rem; }
.modal-info { font-size: 0.95rem; color: var(--text); margin-bottom: 1.5rem; line-height: 1.5; }
.modal-actions { display: flex; gap: 0.75rem; }
.btn { padding: 0.65rem 1.2rem; border: none; border-radius: 7px; font-weight: 700; cursor: pointer; font-size: 0.95rem; transition: all 0.15s; flex: 1; }
.btn-primario { background: var(--marrom); color: var(--dourado); }
.btn-primario:hover { background: var(--marrom-medio); }
.btn-primario:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-cancelar { background: var(--creme-escuro); color: var(--marrom); }
.btn-cancelar:hover { background: #e0d5c2; }
.btn-perigo { background: #fdeaea; color: #b94040; }
.btn-perigo:hover { background: #f8c8c8; }

@media (max-width: 800px) {
  .form-grid { grid-template-columns: 1fr; }
}
</style>
