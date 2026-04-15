<template>
  <div class="pacote-card">
    <div class="pacote-header">
      <div class="pacote-info">
        <h3 class="pacote-nome">{{ pacote.cachorro?.nome || 'Pacote' }} - {{ pacote.tipo_plano?.toUpperCase() }}</h3>
        <p class="pacote-cliente">{{ pacote.cachorro?.cliente?.nome }}</p>
      </div>
      <div class="pacote-status" :class="statusClass">
        {{ statusLabel }}
      </div>
    </div>
    
    <div class="pacote-body">
      <div class="pacote-metrics">
        <div class="metric">
          <span class="metric-label">Valor:</span>
          <span class="metric-value">R$ {{ formatarValor(pacote.valor_cobrado) }}</span>
        </div>
        <div class="metric" v-if="pacote.valor_pago">
          <span class="metric-label">Pago:</span>
          <span class="metric-value">R$ {{ formatarValor(pacote.valor_pago) }}</span>
        </div>
        <div class="metric">
<span class="metric-label">Agendamentos:</span>
          <span class="metric-value">{{ totalAgendamentos }}/{{ banhosMensais }}</span>
        </div>
      </div>
      
      <div class="pacote-actions">
        <button v-if="isAberto" @click="$emit('pagar', pacote)" class="btn btn-warning">
          💰 Pagar
        </button>
        <button @click="$emit('detalhes', pacote)" class="btn btn-secondary">
          Detalhes
        </button>
      </div>
    </div>
    
    <div class="pacote-footer" v-if="pacote.observacoes">
      <small>{{ pacote.observacoes }}</small>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  pacote: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['pagar', 'detalhes'])

const banhosMensais = computed(() => {
  const map = { semanal: 4, quinzenal: 2, mensal: 1 }
  return map[props.pacote.tipo_plano] || 0
})

const totalAgendamentos = computed(() => props.pacote.total_agendamentos || props.pacote.agendamentos?.length || 0)

const statusLabel = computed(() => {
  if (!props.pacote.ativo) return 'Inativo'
  if (!props.pacote.valor_pago) return '❌ Em Aberto'
  return '✅ Pago'
})

const statusClass = computed(() => {
  if (!props.pacote.ativo) return 'status-inativo'
  if (!props.pacote.valor_pago) return 'status-aberto'
  return 'status-pago'
})

const isAberto = computed(() => props.pacote.status_pagamento === 'em_aberto')

function formatarValor(valor) {
  return Number(valor || 0).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}
</script>

<style scoped>
.pacote-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  padding: 1.5rem;
  transition: transform 0.2s, box-shadow 0.2s;
}

.pacote-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}

.pacote-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  border-bottom: 2px solid #f7fafc;
  padding-bottom: 1rem;
}

.pacote-nome {
  margin: 0 0 0.25rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #2d3748;
}

.pacote-cliente {
  margin: 0;
  color: #718096;
  font-size: 0.9rem;
}

.pacote-status {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-aberto {
  background: #fed7d7;
  color: #c53030;
}

.status-pago {
  background: #c6f6d5;
  color: #22543d;
}

.status-inativo {
  background: #e2e8f0;
  color: #4a5568;
}

.pacote-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.metric {
  display: flex;
  justify-content: space-between;
}

.metric-label {
  color: #718096;
  font-size: 0.85rem;
}

.metric-value {
  font-weight: 600;
  color: #2d3748;
}

.pacote-actions {
  display: flex;
  gap: 0.5rem;
}

.btn {
  flex: 1;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #4299e1;
  color: white;
}

.btn-warning {
  background: #ed8936;
  color: white;
}

.btn-secondary {
  background: #a0aec0;
  color: #2d3748;
}

.btn:hover {
  transform: translateY(-1px);
}

.pacote-footer {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.pacote-footer small {
  color: #a0aec0;
  font-style: italic;
}
</style>
