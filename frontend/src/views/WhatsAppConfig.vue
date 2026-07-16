<template>
  <div class="whatsapp-config">
    <div class="page-header">
      <h1 class="page-title">💬 Conexão com WhatsApp</h1>
    </div>

    <div class="status-card">
      <div v-if="carregando" class="empty-state">Verificando conexão...</div>

      <template v-else>
        <div class="status-linha" :class="conectado ? 'ok' : 'pendente'">
          <span class="status-dot"></span>
          <span v-if="conectado">Conectado — comandas por WhatsApp estão ativas</span>
          <span v-else-if="erro">{{ erro }}</span>
          <span v-else>Não conectado — escaneie o QR code abaixo com o WhatsApp do celular usado pelo canil</span>
        </div>

        <div v-if="!conectado && !erro" class="qrcode-wrap">
          <img v-if="qrcode" :src="qrcode" alt="QR Code do WhatsApp" class="qrcode-img" />
          <div v-else class="empty-state">Gerando QR code...</div>
          <p class="qrcode-hint">
            No WhatsApp do celular: Menu (⋮) → Aparelhos conectados → Conectar um aparelho, e aponte a câmera para este QR code.
          </p>
        </div>

        <button @click="atualizar" class="btn btn-primario" :disabled="carregando">
          ↻ Atualizar
        </button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import whatsappApi from '../api/whatsapp'

const carregando = ref(true)
const conectado = ref(false)
const qrcode = ref(null)
const erro = ref(null)
let intervalo = null

async function atualizar() {
  carregando.value = true
  erro.value = null
  try {
    const statusResp = await whatsappApi.obterStatus()
    conectado.value = statusResp.data.state === 'open'

    if (!conectado.value) {
      const qrResp = await whatsappApi.obterQrCode()
      qrcode.value = qrResp.data.qrcode_base64 || null
      // Se o QR code veio vazio mas o estado não é "open", pode já estar conectado
      // (Evolution API não retorna QR quando já autenticado).
      if (!qrcode.value && qrResp.data.raw?.instance) {
        conectado.value = true
      }
    } else {
      qrcode.value = null
    }
  } catch (err) {
    erro.value = err.response?.data?.detail || 'Não foi possível conectar à integração do WhatsApp.'
  } finally {
    carregando.value = false
  }
}

onMounted(() => {
  atualizar()
  // Atualiza sozinho a cada 10s até conectar (o QR code expira periodicamente).
  intervalo = setInterval(() => {
    if (!conectado.value) atualizar()
  }, 10000)
})

onUnmounted(() => {
  if (intervalo) clearInterval(intervalo)
})
</script>

<style scoped>
.whatsapp-config {
  --marrom:        #3b2a1a;
  --marrom-medio:  #5a3e28;
  --dourado:       #d4a843;
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

.status-card {
  background: var(--white); border-radius: var(--radius);
  padding: 1.6rem; box-shadow: var(--shadow); max-width: 480px;
  display: flex; flex-direction: column; align-items: center; gap: 1.2rem;
}

.status-linha {
  display: flex; align-items: center; gap: 0.6rem; width: 100%;
  font-weight: 700; font-size: 0.95rem; padding: 0.7rem 1rem; border-radius: 8px;
}
.status-linha.ok { background: var(--verde-bg); color: var(--verde); }
.status-linha.pendente { background: var(--creme); color: var(--text-muted); }
.status-dot { width: 10px; height: 10px; border-radius: 50%; background: currentColor; flex-shrink: 0; }

.qrcode-wrap { display: flex; flex-direction: column; align-items: center; gap: 0.8rem; }
.qrcode-img { width: 260px; height: 260px; border: 2px solid var(--creme-escuro); border-radius: 8px; }
.qrcode-hint { font-size: 0.85rem; color: var(--text-muted); text-align: center; max-width: 360px; }

.empty-state { color: var(--text-muted); font-style: italic; padding: 1rem; }

.btn {
  padding: 0.65rem 1.4rem; border: none; border-radius: 7px;
  font-weight: 700; cursor: pointer; font-size: 0.95rem; transition: all 0.15s;
}
.btn-primario { background: var(--marrom); color: var(--dourado); }
.btn-primario:hover { background: var(--marrom-medio); }
.btn-primario:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
