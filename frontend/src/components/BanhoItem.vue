<template>
  <div class="banho-item">
    <div class="banho-icon">🛁</div>
    <div class="banho-content">
      <div class="banho-date">{{ formatarData(banho.data_banho) }}</div>
      <div class="banho-obs" v-if="banho.observacao">
        {{ banho.observacao }}
      </div>
      <div class="banho-meta" v-if="showPacote">
        Pacote #{{ banho.pacote_id }}
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  banho: {
    type: Object,
    required: true
  },
  showPacote: {
    type: Boolean,
    default: false
  }
})

function formatarData(data) {
  return new Date(data).toLocaleDateString('pt-BR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short'
  })
}
</script>

<style scoped>
.banho-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f7fafc;
  border-radius: 6px;
  margin-bottom: 0.5rem;
}

.banho-icon {
  font-size: 1.5rem;
}

.banho-content {
  flex: 1;
}

.banho-date {
  font-weight: 600;
  color: #2d3748;
}

.banho-obs {
  font-size: 0.85rem;
  color: #4a5568;
  margin-top: 0.25rem;
  font-style: italic;
}

.banho-meta {
  font-size: 0.75rem;
  color: #718096;
  margin-top: 0.25rem;
}
</style>