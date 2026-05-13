<template>
  <div class="auth-container">
    <div class="auth-card">
      <h2>Login - Canil Recanto</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>E-mail</label>
          <input v-model="email" type="email" required placeholder="seu@email.com" />
        </div>
        <div class="form-group">
          <label>Senha</label>
          <input v-model="password" type="password" required placeholder="********" />
        </div>
        <p v-if="auth.error" class="error-msg">{{ auth.error }}</p>
        <button type="submit" class="btn btn-primary" :disabled="auth.loading">
          {{ auth.loading ? 'Entrando...' : 'Entrar' }}
        </button>
      </form>
      <p class="switch-auth">
        Não tem conta? <router-link to="/register">Cadastre-se</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()
const email = ref('')
const password = ref('')

async function handleLogin() {
  try {
    await auth.login(email.value, password.value)
    router.push('/')
  } catch (err) {
    // Erro tratado no store
  }
}
</script>

<style scoped>
.auth-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}
.auth-card {
  background: white;
  padding: 2.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 400px;
}
h2 { text-align: center; margin-bottom: 2rem; color: #2d3748; }
.form-group { margin-bottom: 1.5rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
.form-group input { width: 100%; padding: 0.75rem; border: 1px solid #cbd5e0; border-radius: 6px; }
.btn-primary { width: 100%; padding: 0.75rem; font-weight: 600; margin-top: 1rem; }
.error-msg { color: #e53e3e; font-size: 0.9rem; margin-bottom: 1rem; text-align: center; }
.switch-auth { text-align: center; margin-top: 1.5rem; font-size: 0.9rem; }
</style>