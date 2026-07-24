<template>
  <div class="comandas-view">
    <div class="page-header">
      <h1 class="page-title">🖨️ Comandas para Imprimir</h1>
      <button @click="visualizarModelo" class="btn btn-ghost" :disabled="visualizando">
        {{ visualizando ? 'Gerando...' : '👁️ Visualizar Modelo A4' }}
      </button>
    </div>

    <div class="info-card">
      <div v-if="loading" class="empty-state">Carregando...</div>
      <template v-else>
        <p class="resumo">
          <strong>{{ pendentes.length }}</strong>
          comanda{{ pendentes.length === 1 ? '' : 's' }} pendente{{ pendentes.length === 1 ? '' : 's' }} de impressão
        </p>
        <button
          @click="baixarPdf"
          class="btn btn-primario"
          :disabled="pendentes.length === 0 || gerando"
        >
          {{ gerando ? 'Gerando PDF...' : '📄 Gerar PDF (4 por folha A4)' }}
        </button>
      </template>
    </div>

    <div class="lista-card" v-if="!loading && pendentes.length">
      <div class="card-title"><span class="card-title-bar"></span>Fila</div>
      <table class="comandas-table">
        <thead>
          <tr>
            <th>Cliente / Pet</th>
            <th>Pacote fechado em</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in pendentes" :key="item.id">
            <td>
              <strong>{{ item.cliente_nome }}</strong>
              <div class="sub">{{ item.pet_nome }}</div>
            </td>
            <td>{{ formatarData(item.criado_em) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="!loading" class="empty-state">
      Nenhuma comanda pendente de impressão no momento.
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import comandasApi from '../api/comandas'

const pendentes = ref([])
const loading = ref(false)
const gerando = ref(false)
const visualizando = ref(false)

function formatarData(dataStr) {
  return new Date(dataStr).toLocaleString('pt-BR')
}

async function carregar() {
  loading.value = true
  try {
    const response = await comandasApi.listarPendentes()
    pendentes.value = response.data
  } catch (err) {
    alert('Erro ao carregar comandas pendentes: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

async function baixarPdf() {
  gerando.value = true
  try {
    const response = await comandasApi.gerarPdf()
    if (response.status === 204) {
      alert('Não há comandas pendentes para imprimir.')
      return
    }
    const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
    const link = document.createElement('a')
    link.href = url
    link.download = `comandas-${new Date().toISOString().split('T')[0]}.pdf`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    await carregar()
  } catch (err) {
    alert('Erro ao gerar PDF: ' + (err.response?.data?.detail || err.message))
  } finally {
    gerando.value = false
  }
}

async function visualizarModelo() {
  visualizando.value = true
  try {
    const response = await comandasApi.visualizarModelo()
    const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
    window.open(url, '_blank')
  } catch (err) {
    alert('Erro ao gerar modelo: ' + (err.response?.data?.detail || err.message))
  } finally {
    visualizando.value = false
  }
}

onMounted(carregar)
</script>

<style scoped>
.comandas-view {
  --marrom:        #3b2a1a;
  --marrom-medio:  #5a3e28;
  --dourado:       #d4a843;
  --creme:         #faf6ef;
  --creme-escuro:  #f0e8d8;
  --text:          #2e1e0f;
  --text-muted:    #7a6251;
  --white:         #ffffff;
  --radius:        10px;
  --shadow:        0 2px 12px rgba(59,42,26,0.1);
}

.page-header {
  margin-bottom: 1.2rem; display: flex; align-items: center;
  justify-content: space-between; gap: 1rem; flex-wrap: wrap;
}
.page-title {
  font-size: 1.6rem; font-weight: 800; color: var(--marrom);
  border-left: 5px solid var(--dourado); padding-left: 0.75rem;
}

.info-card,
.lista-card {
  background: var(--white); border-radius: var(--radius);
  padding: 1.4rem; box-shadow: var(--shadow); margin-bottom: 1.2rem;
}
.resumo { font-size: 1.05rem; color: var(--text); margin-bottom: 1rem; }

.card-title {
  font-size: 1rem; font-weight: 800; color: var(--marrom);
  margin-bottom: 1rem; display: flex; align-items: center; gap: 8px;
}
.card-title-bar { display: inline-block; width: 4px; height: 16px; background: var(--dourado); border-radius: 2px; }

.empty-state { text-align: center; padding: 2rem; color: var(--text-muted); font-style: italic; }

.comandas-table { width: 100%; border-collapse: collapse; }
.comandas-table th {
  padding: 0.7rem 0.9rem; text-align: left; background: var(--creme);
  font-weight: 800; color: var(--text-muted); font-size: 0.78rem;
  text-transform: uppercase; letter-spacing: 0.5px;
  border-bottom: 2px solid var(--creme-escuro);
}
.comandas-table td {
  padding: 0.7rem 0.9rem; border-bottom: 1px solid var(--creme-escuro);
  font-size: 0.9rem; color: var(--text);
}
.comandas-table tbody tr:last-child td { border-bottom: none; }
.sub { color: var(--text-muted); font-size: 0.82rem; margin-top: 2px; }

.btn {
  padding: 0.65rem 1.2rem; border: none; border-radius: 7px;
  font-weight: 700; cursor: pointer; font-size: 0.95rem; transition: all 0.15s;
}
.btn-primario { background: var(--marrom); color: var(--dourado); }
.btn-primario:hover:not(:disabled) { background: var(--marrom-medio); }
.btn-primario:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-ghost {
  background: var(--white); color: var(--marrom); border: 2px solid var(--creme-escuro);
}
.btn-ghost:hover:not(:disabled) { border-color: var(--dourado); }
.btn-ghost:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
