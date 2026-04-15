import { defineStore } from 'pinia'
import agendamentosApi from '../api/agendamentos.js'

export const useAgendamentosStore = defineStore('agendamentos', {
  state: () => ({
    agendamentosDashboard: []
  }),
  
  actions: {
    async fetchDashboard(data = null) {
      try {
        const response = await agendamentosApi.listarDashboard(data)
        this.agendamentosDashboard = response.data
        return response.data
      } catch (error) {
        console.error('Erro ao carregar agendamentos:', error)
        this.agendamentosDashboard = []
        throw error
      }
    },
    
    async updateStatus(agendamentoId, dados) {
      try {
        const response = await agendamentosApi.atualizarStatus(agendamentoId, dados)
        // Atualizar localmente
        const index = this.agendamentosDashboard.findIndex(a => a.id === agendamentoId)
        if (index !== -1) {
          this.agendamentosDashboard[index] = response.data
        }
        return response.data
      } catch (error) {
        console.error('Erro ao atualizar agendamento:', error)
        throw error
      }
    }
  }
})

