<template>
  <div class="pacote-card" :class="{ 'inativo': !pacote.ativo }">
    <div class="pacote-header">
      <h3>{{ tipoPlanoLabel }}</h3>
      <span class="badge" :class="statusClass">
        {{ statusPagamento }}
      </span>
    </div>
    
    <div class="pacote-body">
      <div class="info-row">
        <span class="label">Valor Cobrado:</span>
        <span class="value">R$ {{ formatarValor(pacote.valor_cobrado) }}</span>
      </div>
      
      <div class="info-row">
        <span class="label">Valor Pago:</span>
        <span class="value" :class="{ 'pendente': !pacote.valor_pago }">
          R$ {{ formatarValor(pacote.valor_pago || 0) }}
        </span>
      </div>
      
      <div class="info-row">
        <span class="label">Limite/Mês:</span>
        <span class="value">{{ pacote.limite_banhos_mes }} banhos</span>
      </div>
      
      <div class="info-row" v-if="pacote.data_pagamento">
        <span class="label">Pago em:</span>
        <span class="value">{{ formatarData(pacote.data_pagamento) }}</span>
      </div>
    </div>
    
    <div class="pacote-actions">
      <button 
        v-if="pacote.status_pagamento === 'em_aberto'"
        @click="$emit('pagar', pacote)"
        class="btn btn-success btn-sm"
      >
        Registrar Pagamento
      </button>
      <button 
        @click="$emit('detalhes', pacote)"
        class="btn btn-primary btn-sm"
      >
        Ver Detalhes
      </button>
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

defineEmits(['pagar', 'detalhes'])

const tipoPlanoLabel = computed(() => {
  const labels = {
    semanal: '📅 Semanal (4x/mês)',
    quinzenal: '📅 Quinzenal (2x/mês)',
    mensal: '📅 Mensal (1x/mês)'
  }
  return labels[props.pacote.tipo_plano] || props.pacote.tipo_plano
})

const statusPagamento = computed(() => {
  const labels = {
    em_aberto: 'Em Aberto',
    pago: 'Pago',
    parcial: 'Parcial'
  }
  return labels[props.pacote.status_pagamento] || 'Desconhecido'
})

const statusClass = computed(() => ({
  'badge-warning': props.pacote.status_pagamento === 'em_aberto',
  'badge-success': props.pacote.status_pagamento === 'pago',
  'badge-info': props.pacote.status_pagamento === 'parcial'
}))

function formatarValor(valor) {
  return Number(valor).toFixed(2).replace('.', ',')
}

function formatarData(data) {
  return new Date(data).toLocaleDateString('pt-BR')
}
</script>

<style scoped>
.pacote-card {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  border: 2px solid #e2e8f0;
  transition: all 0.3s;
}

.pacote-card:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.pacote-card.inativo {
  opacity: 0.6;
  background: #f7fafc;
}

.pacote-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.pacote-header h3 {
  font-size: 1rem;
  color: #2d3748;
}

.badge {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-warning {
  background: #fef3c7;
  color: #92400e;
}

.badge-success {
  background: #d1fae5;
  color: #065f46;
}

.badge-info {
  background: #dbeafe;
  color: #1e40af;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.label {
  color: #718096;
}

.value {
  font-weight: 600;
  color: #2d3748;
}

.value.pendente {
  color: #e53e3e;
}

.pacote-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.btn-sm {
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
  flex: 1;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-success {
  background: #48bb78;
  color: white;
}
</style>