import { defineStore } from 'pinia'
import axios from 'axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  actions: {
    async login(email, password) {
      try {
        const formData = new FormData()
        formData.append('username', email)
        formData.append('password', password)

        const response = await axios.post('http://localhost:8000/api/v1/auth/login', formData)
        this.token = response.data.access_token
        localStorage.setItem('token', this.token)
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        return true
      } catch (error) {
        console.error('Falha no login:', error.response?.data?.detail || error.message)
        throw error
      }
    },
    
    async register(userData) {
      await axios.post('http://localhost:8000/api/v1/auth/register', userData)
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      delete axios.defaults.headers.common['Authorization']
    }
  }
})