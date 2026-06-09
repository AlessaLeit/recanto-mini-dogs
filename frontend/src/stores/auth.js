import { defineStore } from 'pinia'
import api from '../api/index'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user')) || null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token
  },
  actions: {
    async login(email, password) {
      try {
        const response = await api.post('/auth/login', {
          username: email,
          password: password
        })
        this.token = response.data.access_token
        this.user = response.data.user
        
        // Persistência
        localStorage.setItem('token', this.token)
        localStorage.setItem('user', JSON.stringify(this.user))
        
        // O interceptor em api/index.js usará o novo token automaticamente
        return true
      } catch (error) {
        const errorMsg = error.response?.data?.detail || 'E-mail ou senha inválidos'
        console.error('Falha no login:', errorMsg)
        throw errorMsg
      }
    },
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      
      // Limpa o estado e força o redirecionamento
      // window.location.href é preferível ao router.push no logout para limpar estados residuais de memória
      globalThis.location.href = '/login'
    }
  }
})