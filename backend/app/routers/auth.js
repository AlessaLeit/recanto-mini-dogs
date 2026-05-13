import { defineStore } from 'pinia'
import axios from 'axios'

const API_URL = 'http://localhost:8000/api/v1/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: null,
    loading: false,
    error: null
  }),
  getters: {
    isAuthenticated: (state) => !!state.token
  },
  actions: {
    async login(email, password) {
      this.loading = true
      this.error = null
      try {
        const formData = new FormData()
        formData.append('username', email)
        formData.append('password', password)
        
        const response = await axios.post(`${API_URL}/login`, formData)
        this.token = response.data.access_token
        localStorage.setItem('token', this.token)
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        return true
      } catch (err) {
        this.error = err.response?.data?.detail || 'Erro ao fazer login'
        throw this.error
      } finally {
        this.loading = false
      }
    },
    async register(userData) {
      try {
        await axios.post(`${API_URL}/register`, userData)
        return true
      } catch (err) {
        throw err.response?.data?.detail || 'Erro ao cadastrar'
      }
    },
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      delete axios.defaults.headers.common['Authorization']
      window.location.href = '/login'
    },
    initAuth() {
      if (this.token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
      }
    }
  }
})