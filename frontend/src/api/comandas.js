/**
 * API endpoints para a fila de comandas impressas.
 */
import api from "./index";

export const comandasApi = {
  listarPendentes: () => api.get("/comandas-impressao/pendentes"),
  gerarPdf: () => api.get("/comandas-impressao/pdf", { responseType: "blob" }),
  visualizarModelo: () =>
    api.get("/comandas-impressao/pdf/exemplo", { responseType: "blob" }),
};

export default comandasApi;
