<template>
  <div class="auth-container">
    <div class="auth-card">
      <h2>Criar Conta</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label>Nome Completo</label>
          <input v-model="form.full_name" type="text" required />
        </div>
        <div class="form-group">
          <label>E-mail</label>
          <input v-model="form.email" type="email" required />
        </div>
        <div class="form-group">
          <label>Senha</label>
          <input v-model="form.password" type="password" required />
        </div>
        <button type="submit" class="btn btn-primary">Cadastrar</button>
      </form>
      <p class="switch-auth">
        Já tem conta? <router-link to="/login">Fazer Login</router-link>
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
const form = ref({ full_name: '', email: '', password: '' })

async function handleRegister() {
  try {
    await auth.register(form.value)
    alert('Cadastro realizado! Faça login agora.')
    router.push('/login')
  } catch (err) {
    alert(err)
  }
}
</script>

<style scoped>
/* Reutiliza estilos do Login.vue */
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
  width: 100%;
  max-width: 400px;
}
.form-group { margin-bottom: 1.2rem; }
.btn-primary { width: 100%; padding: 0.75rem; }
</style>