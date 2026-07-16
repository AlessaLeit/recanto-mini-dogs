/**
 * API endpoints para Pacotes.
 */
import api from './index'

export const pacoteApi = {
  // CRUD básico
  listar: (params = {}) => api.get('/pacotes/', { params }),
  obter: (id) => api.get(`/pacotes/${id}`),
  criar: (data) => api.post('/pacotes/', data),
  atualizar: (id, data) => api.put(`/pacotes/${id}`, data),
  deletar: (id) => api.delete(`/pacotes/${id}`),
  
  // Ações específicas
  registrarPagamento: (id, dados) =>
    api.patch(`/pacotes/${id}/pagar`, dados),

  atualizarPagamento: (pacoteId, pagamentoId, dados) =>
    api.put(`/pacotes/${pacoteId}/pagamentos/${pagamentoId}`, dados),

  deletarPagamento: (pacoteId, pagamentoId) =>
    api.delete(`/pacotes/${pacoteId}/pagamentos/${pagamentoId}`),

  fechar: (id) => api.patch(`/pacotes/${id}/fechar`),

  enviarComanda: (id) => api.post(`/pacotes/${id}/enviar-comanda`),

  // Agendamentos 
  listarAgendamentosPacote: (pacoteId) => api.get(`/pacotes/${pacoteId}/agendamentos`),
  
  detalhesComAgendamentos: (pacoteId) => api.get(`/pacotes/${pacoteId}`),
  
  // Adicionar agendamento extra (além do limite)
  adicionarAgendamentoExtra: (pacoteId, data_banho) => 
    api.post(`/pacotes/${pacoteId}/agendamento-extra`, null, {
      params: { data_banho }
    }),
  
  // Atualizar data do agendamento
  atualizarDataAgendamento: (id, data_banho) => 
    api.put(`/agendamentos/${id}/data`, null, {
      params: { data_banho }
    }),
  
  // Deletar agendamento
  deletarAgendamento: (id) => api.delete(`/agendamentos/${id}`),
  
  // Legacy (mantém para compatibilidade)
  listarAgendamentos: (pacoteId) => api.get('/agendamentos', { params: { pacote_id: pacoteId } }),
  atualizarAgendamento: (id, data) => api.put(`/agendamentos/${id}`, data)
}

export default pacoteApi
