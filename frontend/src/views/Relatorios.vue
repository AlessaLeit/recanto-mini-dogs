<template>
  <div class="relatorios-view">
    <h1>Relatórios Mensais</h1>
    
    <div class="card filtros">
      <div class="form-group">
        <label>Mês</label>
        <select v-model="mes">
          <option v-for="(nome, index) in meses" :key="index" :value="index + 1">
            {{ nome }}
          </option>
        </select>
      </div>
      <div class="form-group">
        <label>Ano</label>
        <input v-model.number="ano" type="number" min="2020" max="2030" />
      </div>
      <button @click="gerarRelatorio" class="btn btn-primary" :disabled="loading">
        {{ loading ? 'Gerando...' : 'Gerar Relatório' }}
      </button>
    </div>
    
    <div v-if="relatorio" class="relatorio-resultado">
      <h2>Resumo de {{ relatorio.periodo.nome_mes }}/{{ relatorio.periodo.ano }}</h2>
      
      <div class="grid grid-4 resumo-cards">
        <div class="resumo-card">
          <div class="resumo-valor">{{ relatorio.resumo.total_banhos_realizados }}</div>
          <div class="resumo-label">Banhos Realizados</div>
        </div>
        
        <div class="resumo-card receita">
          <div class="resumo-valor">R$ {{ formatarValor(relatorio.resumo.receita_prevista) }}</div>
          <div class="resumo-label">Receita Prevista</div>
        </div>
        
        <div class="resumo-card receita-recebida">
          <div class="resumo-valor">R$ {{ formatarValor(relatorio.resumo.receita_recebida) }}</div>
          <div class="resumo-label">Receita Recebida</div>
        </div>
        
        <div class="resumo-card pendente">
          <div class="resumo-valor">R$ {{ formatarValor(relatorio.resumo.receita_pendente) }}</div>
          <div class="resumo-label">Pendente</div>
        </div>
      </div>
      
      <div class="taxa-recebimento">
        Taxa de Recebimento: <strong>{{ relatorio.resumo.taxa_recebimento }}%</strong>
      </div>
      
      <div class="grid grid-2 detalhes-section">
        <div class="card" v-if="relatorio.detalhes.pacotes_em_aberto.length">
          <h3>📋 Pacotes em Aberto ({{ relatorio.detalhes.pacotes_em_aberto.length }})</h3>
          <div class="lista-itens">
            <div 
              v-for="item in relatorio.detalhes.pacotes_em_aberto" 
              :key="item.pacote_id"
              class="item-lista"
            >
              <div class="item-titulo">
                {{ item.cachorro.nome }} - {{ item.cliente.nome }}
              </div>
              <div class="item-sub">
                {{ item.tipo_plano }} • R$ {{ formatarValor(item.valor_cobrado) }}
              </div>
              <div class="item-contato" v-if="item.cliente.telefone">
                📞 {{ item.cliente.telefone }}
              </div>
            </div>
          </div>
        </div>
        
        <div class="card" v-if="relatorio.detalhes.banhos_com_observacoes.length">
          <h3>📝 Banhos com Observações</h3>
          <div class="lista-itens">
            <div 
              v-for="item in relatorio.detalhes.banhos_com_observacoes" 
              :key="item.banho_id"
              class="item-lista"
            >
              <div class="item-titulo">
                {{ item.cachorro.nome }} - {{ formatarData(item.data_banho) }}
              </div>
              <div class="item-obs">{{ item.observacao }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api'

const meses = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

const hoje = new Date()
const mes = ref(hoje.getMonth() + 1)
const ano = ref(hoje.getFullYear())
const loading = ref(false)
const relatorio = ref(null)

async function gerarRelatorio() {
  loading.value = true
  try {
    const response = await api.get('/relatorios/mensal', {
      params: { ano: ano.value, mes: mes.value }
    })
    relatorio.value = response.data
  } catch (err) {
    alert('Erro ao gerar relatório: ' + (err.response?.data?.detail || err))
  } finally {
    loading.value = false
  }
}

function formatarValor(valor) {
  return Number(valor || 0).toFixed(2).replace('.', ',')
}

function formatarData(data) {
  return new Date(data).toLocaleDateString('pt-BR')
}
</script>

<style scoped>
.filtros {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
  margin-bottom: 2rem;
}

.filtros .form-group {
  flex: 1;
  margin-bottom: 0;
}

.filtros select,
.filtros input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
}

.resumo-cards {
  margin: 1.5rem 0;
}

.resumo-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 8px;
  text-align: center;
}

.resumo-card.receita {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
}

.resumo-card.receita-recebida {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
}

.resumo-card.pendente {
  background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
}

.resumo-valor {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.resumo-label {
  font-size: 0.9rem;
  opacity: 0.9;
}

.taxa-recebimento {
  text-align: center;
  padding: 1rem;
  background: #f7fafc;
  border-radius: 8px;
  margin-bottom: 2rem;
  font-size: 1.1rem;
  color: #4a5568;
}

.detalhes-section {
  margin-top: 2rem;
}

.lista-itens {
  max-height: 400px;
  overflow-y: auto;
}

.item-lista {
  padding: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.item-lista:last-child {
  border-bottom: none;
}

.item-titulo {
  font-weight: 600;
  color: #2d3748;
}

.item-sub {
  font-size: 0.85rem;
  color: #718096;
  margin-top: 0.25rem;
}

.item-contato {
  font-size: 0.85rem;
  color: #48bb78;
  margin-top: 0.25rem;
}

.item-obs {
  font-size: 0.9rem;
  color: #4a5568;
  margin-top: 0.5rem;
  font-style: italic;
  background: #f7fafc;
  padding: 0.5rem;
  border-radius: 4px;
}
</style>