<template>
  <div class="pagamento-modal" v-if="show">
    <div class="modal-overlay" @click="$emit('close')"></div>
    <div class="modal-content">
      <h3>Registrar Pagamento</h3>
      <p class="pacote-info">
        Pacote {{ pacote?.tipo_plano }} - 
        Valor cobrado: R$ {{ formatarValor(pacote?.valor_cobrado) }}
      </p>
      
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>Valor Pago (R$)</label>
          <input 
            v-model.number="form.valor_pago" 
            type="number" 
            step="0.01"
            min="0"
            required
          />
        </div>
        
        <div class="form-group">
          <label>Data do Pagamento</label>
          <input 
            v-model="form.data_pagamento" 
            type="date"
            required
          />
        </div>
        
        <div class="form-actions">
          <button type="button" @click="$emit('close')" class="btn">
            Cancelar
          </button>
          <button type="submit" class="btn btn-success">
            Confirmar Pagamento
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  show: Boolean,
  pacote: Object
})

const emit = defineEmits(['close', 'confirmar'])

const form = ref({
  valor_pago: 0,
  data_pagamento: new Date().toISOString().split('T')[0]
})

watch(() => props.pacote, (novo) => {
  if (novo) {
    // 'valor_cobrado' já deve vir calculado no backend (base * quantidade do plano)
    form.value.valor_pago = novo.valor_cobrado
  }
})


function handleSubmit() {
  emit('confirmar', {
    pacote_id: props.pacote.id,
    ...form.value
  })
}

function formatarValor(valor) {
  return Number(valor || 0).toFixed(2).replace('.', ',')
}
</script>

<style scoped>
.pagamento-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  width: 90%;
  max-width: 400px;
  position: relative;
  z-index: 1001;
}

.pacote-info {
  color: #718096;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
}

.form-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1.5rem;
}

.form-actions .btn {
  flex: 1;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn {
  background: #e2e8f0;
  color: #4a5568;
}

.btn-success {
  background: #48bb78;
  color: white;
}
</style>