/**
 * API endpoints para Agendamentos (Dashboard).
 */
import api from './index'

export const agendamentosApi = {
  // Dashboard: listar por data específica
  listarDashboard: (data = null) => {
    const endpoint = data ? `/agendamentos/dashboard/${data}` : '/agendamentos/dashboard'
    return api.get(endpoint)
  },
  
  // Editar status/extras
  atualizarStatus: (id, dados) => api.put(`/agendamentos/${id}`, dados)
}

export default agendamentosApi

