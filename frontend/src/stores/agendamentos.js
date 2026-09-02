import { defineStore } from "pinia";
import agendamentosApi from "../api/agendamentos.js";

export const useAgendamentosStore = defineStore("agendamentos", {
  state: () => ({
    agendamentosDashboard: [],
    avulsos: [],
  }),

  actions: {
    async fetchAvulsos() {
      try {
        const response = await agendamentosApi.listarAvulsos();
        this.avulsos = Array.isArray(response.data) ? response.data : [];
        return this.avulsos;
      } catch (error) {
        console.error("Erro ao carregar banhos avulsos:", error);
        this.avulsos = [];
        throw error;
      }
    },

    async criarAvulso(dados) {
      try {
        const response = await agendamentosApi.criarAvulso(dados);
        this.avulsos.unshift(response.data);
        return response.data;
      } catch (error) {
        console.error("Erro ao criar banho avulso:", error);
        throw error;
      }
    },

    async atualizarAvulso(agendamentoId, dados) {
      try {
        const response = await agendamentosApi.atualizarStatus(
          agendamentoId,
          dados,
        );
        const index = this.avulsos.findIndex((a) => a.id === agendamentoId);
        if (index !== -1) {
          this.avulsos[index] = { ...this.avulsos[index], ...response.data };
        }
        return response.data;
      } catch (error) {
        console.error("Erro ao atualizar banho avulso:", error);
        throw error;
      }
    },

    async deletarAvulso(agendamentoId) {
      try {
        await agendamentosApi.deletarAgendamento(agendamentoId);
        this.avulsos = this.avulsos.filter((a) => a.id !== agendamentoId);
      } catch (error) {
        console.error("Erro ao excluir banho avulso:", error);
        throw error;
      }
    },

    async fetchDashboard(data = null, turno = null) {
      try {
        const response = await agendamentosApi.listarDashboard(data, turno);
        // Ensure array even if API returns unexpected data
        this.agendamentosDashboard = Array.isArray(response.data)
          ? response.data
          : [];
        console.log(
          "Dashboard agendamentos loaded:",
          this.agendamentosDashboard.length,
        );
        return this.agendamentosDashboard;
      } catch (error) {
        console.error("Erro ao carregar agendamentos:", error);
        this.agendamentosDashboard = [];
        throw error;
      }
    },

    async updateStatus(agendamentoId, dados) {
      try {
        const response = await agendamentosApi.atualizarStatus(
          agendamentoId,
          dados,
        );
        // Atualizar localmente, preservando pet_nome/cliente_nome (o PUT não os retorna)
        const index = this.agendamentosDashboard.findIndex(
          (a) => a.id === agendamentoId,
        );
        if (index !== -1) {
          const atualizado = Array.isArray(response.data)
            ? response.data[0]
            : response.data;
          this.agendamentosDashboard[index] = {
            ...this.agendamentosDashboard[index],
            ...atualizado,
          };
        }
        return response.data;
      } catch (error) {
        console.error("Erro ao atualizar agendamento:", error);
        throw error;
      }
    },

    // Excluir agendamento do dia (interligado com Pacotes)
    async deletarAgendamento(agendamentoId) {
      try {
        await agendamentosApi.deletarAgendamento(agendamentoId);
        // Remover localmente
        this.agendamentosDashboard = this.agendamentosDashboard.filter(
          (a) => a.id !== agendamentoId,
        );
      } catch (error) {
        console.error("Erro ao deletar agendamento:", error);
        throw error;
      }
    },
  },
});
