/**
 * API endpoints para Pacotes.
 */
import api from './index'

export const pacoteApi = {
  // CRUD básico
  listar: (params = {}) => api.get('/pacotes', { params }),
  obter: (id) => api.get(`/pacotes/${id}`),
  criar: (data) => api.post('/pacotes', data),
  atualizar: (id, data) => api.put(`/pacotes/${id}`, data),
  deletar: (id) => api.delete(`/pacotes/${id}`),
  
  // Ações específicas
  registrarPagamento: (id, valor_pago, data_pagamento) => 
    api.post(`/pacotes/${id}/pagar`, null, {
      params: { valor_pago, data_pagamento }
    }),

  // Agendamentos
  listarAgendamentos: (pacoteId) => api.get('/agendamentos', { params: { pacote_id: pacoteId } }),
  atualizarAgendamento: (id, data) => api.put(`/agendamentos/${id}`, data)
}

export default pacoteApi