/**
 * API endpoints para integração com WhatsApp (Evolution API).
 */
import api from './index'

export const whatsappApi = {
  obterQrCode: () => api.get('/whatsapp/qrcode'),
  obterStatus: () => api.get('/whatsapp/status')
}

export default whatsappApi
