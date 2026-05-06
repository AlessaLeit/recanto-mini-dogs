/**
 * API endpoints para Cachorros (Pets).
 */
import api from './index'

export const cachorroApi = {
  listar: (params = {}) => api.get('/cachorros/', { params }),
  obter: (id) => api.get(`/cachorros/${id}`),
  criar: (data) => api.post('/cachorros/', data),
  atualizar: (id, data) => api.put(`/cachorros/${id}`, data),
  deletar: (id) => api.delete(`/cachorros/${id}`)
}

export default cachorroApi
