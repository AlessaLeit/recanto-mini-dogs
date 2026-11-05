/**
 * API endpoints para Créditos do cliente (pagamento adiantado).
 */
import api from "./index";

export const creditoApi = {
  obterPorCliente: (clienteId) =>
    api.get("/creditos/", { params: { cliente_id: clienteId } }),
  registrar: (data) => api.post("/creditos/", data),
};

export default creditoApi;
