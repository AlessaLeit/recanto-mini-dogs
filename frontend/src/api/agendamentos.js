/**
 * API endpoints para Agendamentos (Dashboard).
 */
import api from './index'

export const agendamentosApi = {
  // Dashboard: listar por data específica, opcionalmente filtrando por turno (manha/tarde)
  listarDashboard: (data = null, turno = null) => {
    // Garante que sempre envie uma data no formato YYYY-MM-DD para evitar 404
    const dateParam = data || new Date().toISOString().split('T')[0]
    const endpoint = `/agendamentos/dashboard/${dateParam}`
    const params = turno ? { turno } : {}
    return api.get(endpoint, { params })
  },
  
  // Editar status/extras
  atualizarStatus: (id, dados) => api.put(`/agendamentos/${id}`, dados),

  // Excluir agendamento do dia
  deletarAgendamento: (id) => api.delete(`/agendamentos/${id}`),

  // Banhos avulsos (sem pacote vinculado)
  criarAvulso: (dados) => api.post('/agendamentos/avulso', dados),
  listarAvulsos: () => api.get('/agendamentos/avulsos')
}


export default agendamentosApi
