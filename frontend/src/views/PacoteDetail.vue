<template>
  <div class="pacote-detail">

    <!-- Header -->
    <div class="header">
      <button @click="voltar" class="btn-back">← Voltar</button>
      <div class="header-info">
        <h1>{{ pacote?.pet_nome || 'Pacote' }}</h1>
        <p class="subheader">{{ pacote?.cliente_nome }}</p>
      </div>
      <div class="status-pill" :class="pacote?.status_pagamento" style="margin-right: 1rem;">
        {{ pacote?.status_pagamento?.toUpperCase() || 'EM ABERTO' }}
      </div>
    </div>

    <!-- Info Cards -->
    <div class="info-cards">
      <div class="info-card clickable" @click="abrirEditarPacote" title="Clique para editar plano">
        <span class="info-label">Plano</span>
        <span class="info-value">{{ pacote?.tipo_plano?.toUpperCase() }}</span>
        <span class="info-sub">{{ pacote?.limite_banhos_mes }} banhos/mês</span>
      </div>

      <div class="info-card clickable" @click="abrirEditarPacote" title="Clique para editar dia">
        <span class="info-label">Dia da Semana</span>
        <span class="info-value">{{ formatarDiaSemana(pacote?.dia_da_semana) }}</span>
        <span class="info-sub">Datas geradas automaticamente</span>
      </div>

      <div class="info-card clickable" @click="abrirEditarPacote" title="Clique para editar valores">
        <span class="info-label">Valor Base do Banho</span>
        <span class="info-value">R$ {{ formatarValor(pacote?.valor_banho_base || 0) }}</span>
        <span class="info-sub" v-if="qtdCachorros > 1">
          {{ qtdCachorros }} cachorros = R$ {{ formatarValor(valorBanhoEquivalente) }}/dia
        </span>
      </div>

      <div class="info-card clickable" @click="abrirEditarPacote" title="Clique para editar valores">
        <span class="info-label">Valor Cobrado (Pacote)</span>
        <span class="info-value">R$ {{ formatarValor(pacote?.valor_cobrado) }}</span>
      </div>

      <div class="info-card status-pago">
        <span class="info-label">Total Pago</span>
        <span class="info-value">R$ {{ formatarValor(pacote?.valor_pago || 0) }}</span>
        <span class="info-sub" v-if="valorRestante > 0" style="color: #b94040; font-weight: 700;">
          Resta: R$ {{ formatarValor(valorRestante) }}
        </span>
        <span class="info-sub" v-else style="color: var(--verde); font-weight: 700;">
          Pacote Quitado
        </span>
      </div>


      <div class="info-card clickable" @click="abrirEditarPacote" title="Clique para editar transporte">
        <span class="info-label">Transporte</span>
        <span class="info-value">R$ {{ formatarValor(pacote?.valor_transporte || 0) }}</span>
        <span class="info-sub">Clique para alterar</span>
      </div>

      <div class="info-card">
        <span class="info-label">Qtd. Agendamentos</span>
        <span class="info-value">{{ pacote?.total_agendamentos || 0 }}</span>
      </div>
    </div>

    <!-- Ações -->
    <div class="actions-bar">
      <button v-if="!pacote?.fechado" @click="showAddExtra = true" class="btn btn-primario">
        + Adicionar Banho Extra
      </button>
      <div v-else class="pacote-fechado-aviso">
        🔒 Pacote fechado — os banhos não podem ser alterados.
        <button @click="reabrirPacoteAction" class="btn btn-ghost" :disabled="reabrindoPacote">
          {{ reabrindoPacote ? 'Reabrindo...' : '🔓 Reabrir Pacote' }}
        </button>
      </div>
    </div>

    <!-- Tabela de Agendamentos -->
    <div class="agendamentos-section">
      <h3 class="section-title"><span class="section-title-bar"></span> Agendamentos do Pacote</h3>

      <table class="agendamentos-table" v-if="agendamentos.length">
        <thead>
          <tr>
            <th>Data</th>
            <th>Status</th>
            <th>Itens Extras</th>
            <th>Valor Banho</th>
            <th>Valor Extra</th>
            <th v-if="!pacote?.fechado">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ag in agendamentos" :key="ag.id" :class="ag.status_presenca">
            <td><strong>{{ formatarData(ag.data_banho) }}</strong></td>
            <td :class="{ 'clickable-cell': !pacote?.fechado }" @click="!pacote?.fechado && abrirEditarExtras(ag)">
              <!-- Pacote multi-cachorro: mostra o status de cada pet do dia -->
              <template v-if="qtdCachorros > 1">
                <span
                  v-for="cachorro in cachorrosDoPacote"
                  :key="cachorro.id"
                  class="status-badge status-badge-pet"
                  :class="statusDoCachorro(ag, cachorro.id)"
                >
                  {{ cachorro.nome }}: {{ statusDoCachorro(ag, cachorro.id).toUpperCase() }}
                </span>
              </template>
              <span v-else class="status-badge" :class="ag.status_presenca">
                {{ ag.status_presenca?.toUpperCase() }}
              </span>
            </td>
            <td :class="{ 'clickable-cell': !pacote?.fechado }" @click="!pacote?.fechado && abrirEditarExtras(ag)">{{ ag.extras?.info || '-' }}</td>
            <td>R$ {{ formatarValor(valorBanhoDia(ag)) }}</td>
            <td :class="{ 'clickable-cell': !pacote?.fechado }" @click="!pacote?.fechado && abrirEditarExtras(ag)">R$ {{ formatarValor(ag.extras?.valor_extra || 0) }}</td>
            <td v-if="!pacote?.fechado">
              <div class="acoes">
                <button @click="abrirEditarExtras(ag)" class="btn-acao btn-acao-verde" title="Adicionar Item Extra">+</button>
                <button @click="abrirEditarData(ag)" class="btn-acao btn-acao-ghost" title="Editar data">📅</button>
                <button @click="confirmarRemover(ag)" class="btn-acao btn-acao-perigo" title="Remover">🗑️</button>
              </div>
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr class="total-row">
            <td colspan="3" style="text-align:right"><strong>Total do Pacote (Banhos + Extras):</strong></td>
            <td colspan="3"><strong>R$ {{ formatarValor(totalPacote) }}</strong></td>
          </tr>
        </tfoot>
      </table>

      <div v-else class="empty-state">
        Nenhum agendamento encontrado.
      </div>
    </div>

    <!-- Histórico de Pagamentos -->
    <div class="pagamentos-section" v-if="pacote?.pagamentos?.length">
      <h3 class="section-title"><span class="section-title-bar"></span> Histórico de Pagamentos</h3>
      <table class="pagamentos-table">
        <thead>
          <tr>
            <th>Data</th>
            <th>Valor Pago</th>
            <th>Método</th>
            <th>Observação</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pg in pacote.pagamentos" :key="pg.id">
            <td><strong>{{ formatarData(pg.data_pagamento) }}</strong></td>
            <td>R$ {{ formatarValor(pg.valor_pago) }}</td>
            <td>{{ formatarTipoPagamento(pg.tipo_pagamento) }}</td>
            <td class="col-observacao">{{ pg.observacao || '-' }}</td>
            <td>
              <div class="acoes">
                <button @click="abrirEditarPagamento(pg)" class="btn-acao btn-acao-ghost" title="Editar pagamento">✏️</button>
                <button @click="confirmarRemoverPagamento(pg)" class="btn-acao btn-acao-perigo" title="Excluir pagamento">✕</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>


      <!-- Seção de Exclusão: Movida para o final do card de agendamentos -->
      <div class="footer-danger-zone">
        <button @click="confirmarDeletarPacote" class="btn btn-perigo" title="Excluir este pacote">🗑️ Excluir Pacote</button>
        <div class="footer-actions">
          <button
            v-if="pacote?.cliente_envio_comanda === 'whatsapp'"
            @click="enviarComandaWhatsapp"
            class="btn btn-ghost"
            style="border-color: var(--verde); color: var(--verde);"
            :disabled="enviandoComanda"
          >
            {{ enviandoComanda ? 'Enviando...' : '💬 Enviar Comanda' }}
          </button>
          <button
            v-if="!pacote?.fechado"
            @click="fecharPacoteAction"
            class="btn btn-ghost"
            style="border-color: var(--dourado); color: var(--marrom); margin-left: 0.5rem;"
            :disabled="!todosBanhosResolvidos || fechandoPacote"
            :title="todosBanhosResolvidos ? '' : 'Marque todos os banhos como concluído ou faltou antes de fechar'"
          >
            {{ fechandoPacote ? 'Fechando...' : '🔒 Fechar Pacote' }}
          </button>
          <button v-if="pacote?.status_pagamento !== 'pago'" @click="abrirPagamento()" class="btn btn-primario" style="margin-left: 0.5rem;">💰 Registrar Pagamento</button>
        </div>
      </div>
      
    <!-- ── MODAL: Editar Data ── -->
    <div class="modal" v-if="showEditData">
      <div class="modal-overlay" @click="showEditData = false"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>Editar Data</h3>
          <p class="modal-sub">🐶 {{ pacote?.pet_nome }}</p>
        </div>
        <p class="modal-info">Agendamento atual: <strong>{{ formatarData(agEditando?.data_banho) }}</strong></p>
        <div class="form-group">
          <label for="nova-data">Selecione a Nova Data</label>
          <input id="nova-data" type="date" v-model="novaData" required />
        </div>
        <div class="modal-actions">
          <button @click="showEditData = false" class="btn btn-cancelar">Cancelar</button>
          <button @click="salvarNovaData" class="btn btn-primario" :disabled="!novaData">Salvar</button>
        </div>
      </div>
    </div>

    <!-- ── MODAL: Confirmar Exclusão do Pacote Inteiro ── -->
    <div class="modal" v-if="showConfirmDeletePacote">
      <div class="modal-overlay" @click="showConfirmDeletePacote = false"></div>
      <div class="modal-content">
        <div class="modal-header modal-header-danger">
          <h3>⚠️ Confirmar Exclusão</h3>
        </div>
        <p class="modal-info">Tem certeza que deseja excluir o pacote de <strong>{{ pacote?.pet_nome }}</strong>?</p>
        <p class="warning-text">Isso desativará o pacote e removerá todos os agendamentos pendentes. Esta ação não pode ser desfeita.</p>
        <div class="modal-actions">
          <button @click="showConfirmDeletePacote = false" class="btn btn-cancelar">Cancelar</button>
          <button @click="executarDeletarPacote" class="btn btn-perigo">Excluir Permanentemente</button>
        </div>
      </div>
    </div>

    <!-- ── MODAL: Editar Dados do Pacote ── -->
    <div class="modal" v-if="showModalEditPacote">
      <div class="modal-overlay" @click="showModalEditPacote = false"></div>
      <div class="modal-content modal-wide">
        <div class="modal-header">
          <h3>Configurações do Pacote</h3>
          <p class="modal-sub">⚙️ {{ pacote?.pet_nome }}</p>
        </div>

        <div class="grid-form">
          <div class="form-group">
            <label for="tipo-plano">Tipo de Plano</label>
            <select id="tipo-plano" v-model="formPacote.tipo_plano" @change="handleInputMudanca">
              <option value="semanal">Semanal (4 banhos)</option>
              <option value="quinzenal">Quinzenal (2 banhos)</option>
              <option value="mensal">Mensal (1 banho)</option>
            </select>
          </div>
          <div class="form-group">
            <label for="dia-semana">Dia da Semana</label>
            <select id="dia-semana" v-model="formPacote.dia_da_semana">
              <option value="terca">Terça-feira</option>
              <option value="quarta">Quarta-feira</option>
              <option value="quinta">Quinta-feira</option>
              <option value="sexta">Sexta-feira</option>
              <option value="sabado">Sábado</option>
            </select>
          </div>
        </div>

        <div class="grid-form" v-if="cachorrosAdicionaisPacote.length === 0">
          <div class="form-group">
            <label for="valor-base">Valor Base Banho (R$)</label>
            <input id="valor-base" type="number" step="0.01" v-model.number="formPacote.valor_banho_base" @input="handleInputMudanca" />
          </div>
          <div class="form-group">
            <label for="transporte">Transporte Total (R$)</label>
            <input id="transporte" type="number" step="0.01" v-model.number="formPacote.valor_transporte" @input="handleInputMudanca" />
          </div>
        </div>

        <template v-else>
          <div class="grid-form">
            <div class="form-group">
              <label for="valor-base">Valor do Banho — {{ cachorroPrincipalPacote?.nome }} (R$)</label>
              <input id="valor-base" type="number" step="0.01" v-model.number="formPacote.valor_banho_base" @input="handleInputMudanca" />
            </div>
            <div class="form-group" v-for="cachorro in cachorrosAdicionaisPacote" :key="cachorro.id">
              <label :for="'valor-extra-' + cachorro.id">Valor do Banho — {{ cachorro.nome }} (R$)</label>
              <input
                :id="'valor-extra-' + cachorro.id"
                type="number"
                step="0.01"
                v-model.number="formValoresCachorros[cachorro.id]"
                @input="handleInputMudanca"
              />
            </div>
          </div>
          <div class="grid-form">
            <div class="form-group">
              <label for="transporte">Transporte Total (R$)</label>
              <input id="transporte" type="number" step="0.01" v-model.number="formPacote.valor_transporte" @input="handleInputMudanca" />
            </div>
          </div>
        </template>

        <div class="form-group form-highlight">
          <label for="valor-cobrado">Valor Total Cobrado (R$)</label>
          <input id="valor-cobrado" type="number" step="0.01" v-model.number="formPacote.valor_cobrado" />
          <small v-if="sugestaoVisivel" class="helper-text">
            Sugerido pelo plano: R$ {{ formatarValor(valorSugerido) }}
          </small>
        </div>

        <div class="modal-actions">
          <button @click="showModalEditPacote = false" class="btn btn-cancelar">Cancelar</button>
          <button @click="salvarDadosPacote" class="btn btn-primario">Salvar Alterações</button>
        </div>
      </div>
    </div>

    <!-- ── MODAL: Editar Extras ── -->
    <div class="modal" v-if="showModalExtras">
      <div class="modal-overlay" @click="showModalExtras = false"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>Editar Agendamento</h3>
          <p class="modal-sub">✨ {{ pacote?.pet_nome }}</p>
        </div>
        <!-- Pacote com 1 cachorro: um único status para o dia -->
        <div class="form-group" v-if="qtdCachorros === 1">
          <label for="edit-status">Status de Presença</label>
          <select id="edit-status" v-model="formExtras.status_presenca">
            <option value="pendente">🟡 PENDENTE</option>
            <option value="concluido">🟢 CONCLUÍDO</option>
            <option value="faltou">🔴 FALTOU / CANCELADO</option>
          </select>
        </div>

        <!-- Pacote multi-cachorro: um status por pet, pois cada um pode
             faltar individualmente no mesmo dia. -->
        <div class="form-group" v-else>
          <label>Status de Presença</label>
          <div class="presencas-grid">
            <div class="presenca-pet" v-for="cachorro in cachorrosDoPacote" :key="cachorro.id">
              <div class="presenca-pet-topo">
                <span class="presenca-pet-nome">🐶 {{ cachorro.nome }}</span>
                <span class="presenca-pet-valor">R$ {{ formatarValor(valorDoCachorro(cachorro.id)) }}</span>
              </div>
              <select :id="'status-pet-' + cachorro.id" v-model="formExtras.presencas[cachorro.id]">
                <option value="pendente">🟡 PENDENTE</option>
                <option value="concluido">🟢 CONCLUÍDO</option>
                <option value="faltou">🔴 FALTOU / CANCELADO</option>
              </select>
            </div>
          </div>
          <small class="helper-text">
            Banho do dia: R$ {{ formatarValor(valorBanhoFormExtras) }} — só os pets concluídos são cobrados.
          </small>
        </div>
        <div class="form-group">
          <label for="edit-info">Itens Extra / Descrição</label>
          <input id="edit-info" v-model="formExtras.info" placeholder="Ex: Tosa higiênica, Shampoo especial..." />
        </div>
        <div class="form-group">
          <label for="edit-valor-extra">Valor Extra (R$)</label>
          <input id="edit-valor-extra" type="number" step="0.01" v-model.number="formExtras.valor_extra" />
        </div>
        <div class="modal-actions">
          <button @click="showModalExtras = false" class="btn btn-cancelar">Cancelar</button>
          <button @click="salvarExtras" class="btn btn-primario">Salvar</button>
        </div>
      </div>
    </div>

    <!-- ── MODAL: Adicionar Extra ── -->
    <div class="modal" v-if="showAddExtra">
      <div class="modal-overlay" @click="showAddExtra = false"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>Banho Extra</h3>
          <p class="modal-sub">➕ {{ pacote?.pet_nome }}</p>
        </div>
        <p class="modal-info">Adicione um banho avulso fora do cronograma do plano.</p>
        <div class="form-group">
          <label for="data-extra">Data do Banho</label>
          <input id="data-extra" type="date" v-model="dataExtra" required />
        </div>
        <div class="modal-actions">
          <button @click="showAddExtra = false" class="btn btn-cancelar">Cancelar</button>
          <button @click="salvarExtra" class="btn btn-primario" :disabled="!dataExtra">Adicionar</button>
        </div>
      </div>
    </div>

    <!-- ── MODAL: Registrar/Editar Pagamento ── -->
    <div class="modal" v-if="showModalPagamento">
      <div class="modal-overlay" @click="showModalPagamento = false"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ pagamentoEditando ? 'Editar Pagamento' : 'Registrar Pagamento' }}</h3>
          <p class="modal-sub">💰 {{ pacote?.pet_nome }}</p>
        </div>
        <div class="form-group">
          <label for="pagamento-valor">Valor Pago (R$)</label>
          <input id="pagamento-valor" type="number" step="0.01" v-model.number="formPagamento.valor_pago" />
        </div>
        <div class="form-group">
            <label for="pagamento-tipo">Método de Pagamento</label>
            <select id="pagamento-tipo" v-model="formPagamento.tipo_pagamento">
              <option value="pix">Pix</option>
              <option value="dinheiro">Dinheiro</option>
              <option value="cartao_debito">Cartão de Débito</option>
              <option value="cartao_credito">Cartão de Crédito</option>
              <option value="outro">Outro</option>
            </select>
          </div>
        <div class="form-group">
          <label for="pagamento-data">Data do Pagamento</label>
          <input id="pagamento-data" type="date" v-model="formPagamento.data_pagamento" />
        </div>
        <div class="form-group">
          <label for="pagamento-observacao">Observação (opcional)</label>
          <textarea id="pagamento-observacao" v-model="formPagamento.observacao" rows="2" placeholder="Ex: pagamento referente à segunda parcela"></textarea>
        </div>
        <div class="modal-actions">
          <button @click="showModalPagamento = false" class="btn btn-cancelar">Cancelar</button>
          <button @click="confirmarPagamento" class="btn btn-primario">{{ pagamentoEditando ? 'Salvar Alterações' : 'Confirmar Recebimento' }}</button>
        </div>
      </div>
    </div>

    <!-- ── MODAL: Confirmar Exclusão de Pagamento ── -->
    <div class="modal" v-if="showConfirmRemovePagamento">
      <div class="modal-overlay" @click="showConfirmRemovePagamento = false"></div>
      <div class="modal-content">
        <div class="modal-header modal-header-danger">
          <h3>⚠️ Confirmar Exclusão</h3>
        </div>
        <p class="modal-info">
          Excluir o pagamento de <strong>R$ {{ formatarValor(pagamentoRemovendo?.valor_pago) }}</strong>
          em <strong>{{ formatarData(pagamentoRemovendo?.data_pagamento) }}</strong>?
        </p>
        <p class="warning-text">O status de pagamento do pacote será recalculado. Esta ação não pode ser desfeita.</p>
        <div class="modal-actions">
          <button @click="showConfirmRemovePagamento = false" class="btn btn-cancelar">Cancelar</button>
          <button @click="executarRemoverPagamento" class="btn btn-perigo">Excluir</button>
        </div>
      </div>
    </div>

    <!-- ── MODAL: Confirmar Remoção ── -->
    <div class="modal" v-if="showConfirmRemove">
      <div class="modal-overlay" @click="showConfirmRemove = false"></div>
      <div class="modal-content">
        <div class="modal-header modal-header-danger">
          <h3>⚠️ Confirmar Remoção</h3>
        </div>
        <p class="modal-info">Tem certeza que deseja remover o agendamento de <strong>{{ formatarData(agRemovendo?.data_banho) }}</strong>?</p>
        <p class="warning-text">Esta ação não pode ser desfeita.</p>
        <div class="modal-actions">
          <button @click="showConfirmRemove = false" class="btn btn-cancelar">Cancelar</button>
          <button @click="executarRemover" class="btn btn-perigo">Remover</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePacotesStore } from '../stores/pacotes.js'

const route = useRoute()
const router = useRouter()
const pacotesStore = usePacotesStore()

const pacote = ref(null)
const agendamentos = ref([])
const loading = ref(false)
const enviandoComanda = ref(false)
const fechandoPacote = ref(false)
const reabrindoPacote = ref(false)

// Modais
const showEditData = ref(false)
const showAddExtra = ref(false)
const showConfirmRemove = ref(false)
const showConfirmDeletePacote = ref(false)
const showModalExtras = ref(false)
const showModalEditPacote = ref(false)
const showModalPagamento = ref(false)
const showConfirmRemovePagamento = ref(false)

// Dados dos modais
const agEditando = ref(null)
const novaData = ref('')
const dataExtra = ref('')
const agRemovendo = ref(null)
const pagamentoEditando = ref(null)
const pagamentoRemovendo = ref(null)
const agExtras = ref(null)
// presencas: status por cachorro (id -> pendente/concluido/faltou) usado em
// pacotes multi-cachorro, onde um pet pode faltar e o outro não no mesmo dia.
const formExtras = ref({ info: '', valor_extra: 0, status_presenca: 'pendente', presencas: {} })
const formPacote = ref({ tipo_plano: '', dia_da_semana: '', valor_banho_base: 0, valor_cobrado: 0, valor_transporte: 0 });
// Valor do banho por cachorro adicional (pacotes multi-cachorro), keyed por id do cachorro.
const formValoresCachorros = reactive({})
const formPagamento = ref({ valor_pago: 0, data_pagamento: '', tipo_pagamento: 'pix', fechar_pacote: false, observacao: '' });
const valorSugerido = ref(0)
const sugestaoVisivel = ref(false)

const pacoteId = computed(() => Number.parseInt(route.params.id, 10))

const valorRestante = computed(() => {
  if (!pacote.value) return 0;
  return (pacote.value.valor_cobrado || 0) - (pacote.value.valor_pago || 0);
});

// Quantidade de cachorros do pacote (principal + adicionais). Pacotes com mais
// de um cachorro banham juntos no mesmo dia, então o valor do dia soma o valor
// de cada cachorro (calculado no backend em valor_banho_equivalente).
const qtdCachorros = computed(() => pacote.value?.cachorros?.length || 1)

const valorBanhoEquivalente = computed(() => pacote.value?.valor_banho_equivalente ?? (pacote.value?.valor_banho_base || 0))

const cachorrosDoPacote = computed(() => pacote.value?.cachorros || [])

// Valor do banho de cada cachorro (id -> valor), vindo do backend.
function valorDoCachorro(cachorroId) {
  const mapa = pacote.value?.valor_banho_por_cachorro || {}
  const valor = mapa[String(cachorroId)]
  return typeof valor === 'number' ? valor : (pacote.value?.valor_banho_base || 0)
}

// Status de um pet num agendamento: usa o status individual quando existe,
// senão cai no status geral do dia (agendamentos antigos e pacotes de 1 pet).
function statusDoCachorro(ag, cachorroId) {
  return ag?.presencas?.[String(cachorroId)] || ag?.status_presenca || 'pendente'
}

// Valor de banho cobrado no dia: soma só os pets que realmente tomaram banho.
function valorBanhoDia(ag) {
  if (qtdCachorros.value === 1) {
    return ag?.status_presenca === 'concluido' ? valorBanhoEquivalente.value : 0
  }
  return cachorrosDoPacote.value.reduce((soma, c) => (
    statusDoCachorro(ag, c.id) === 'concluido' ? soma + valorDoCachorro(c.id) : soma
  ), 0)
}

// Prévia do valor do dia enquanto o usuário edita as presenças no modal.
const valorBanhoFormExtras = computed(() =>
  cachorrosDoPacote.value.reduce((soma, c) => (
    formExtras.value.presencas?.[c.id] === 'concluido' ? soma + valorDoCachorro(c.id) : soma
  ), 0)
)

const cachorroPrincipalPacote = computed(() =>
  pacote.value?.cachorros?.find(c => c.id === pacote.value.cachorro_id)
)

const cachorrosAdicionaisPacote = computed(() =>
  (pacote.value?.cachorros || []).filter(c => c.id !== pacote.value?.cachorro_id)
)

// Só permite fechar o pacote quando todos os banhos do ciclo já foram
// resolvidos (concluído ou faltou — nenhum pendente).
const todosBanhosResolvidos = computed(() =>
  agendamentos.value.length > 0 && agendamentos.value.every(ag => ag.status_presenca !== 'pendente')
)

const totalPacote = computed(() => {
  if (!pacote.value) return 0
  const transporte = pacote.value.valor_transporte || 0
  const agendamentosTotal = agendamentos.value.reduce((sum, ag) => {
    // Regra: só soma o banho dos pets que compareceram (em pacotes com mais de
    // um cachorro, cada pet conta individualmente) e os extras do dia quando
    // pelo menos um pet tomou banho.
    const valorBanhoSomado = valorBanhoDia(ag)
    const valorExtraSomado = ag.status_presenca === 'concluido' ? (ag.extras?.valor_extra || 0) : 0

    return sum + valorBanhoSomado + valorExtraSomado
  }, 0)

  // Transporte é fixo do mês/roteiro, então sempre soma.
  return agendamentosTotal + transporte
})

async function carregarPacote() {
  loading.value = true
  try {
    const data = await pacotesStore.fetchPacote(pacoteId.value)
    pacote.value = data
    agendamentos.value = data.agendamentos || []
  } catch (err) {
  } finally {
    loading.value = false
  }
}

function voltar() { router.push('/pacotes') }

function formatarData(isoDate) {
  if (!isoDate) return '-'
  return new Date(isoDate + 'T00:00:00').toLocaleDateString('pt-BR')
}

function formatarValor(valor) {
  return Number(valor || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatarDiaSemana(dia) {
  const map = { terca: 'Terça', quarta: 'Quarta', quinta: 'Quinta', sexta: 'Sexta', sabado: 'Sábado' }
  return map[dia] || '-'
}

function formatarTipoPagamento(tipo) {
  const map = { pix: 'Pix', dinheiro: 'Dinheiro', cartao_debito: 'Débito', cartao_credito: 'Crédito', outro: 'Outro' };
  return map[tipo] || tipo;
}

function abrirEditarData(ag) {
  agEditando.value = ag
  novaData.value = ag.data_banho
  showEditData.value = true
}

async function salvarNovaData() {
  if (!novaData.value || !agEditando.value) return
  try {
    await pacotesStore.updateAgendamentoData(agEditando.value.id, novaData.value)
    showEditData.value = false
    agEditando.value = null
    novaData.value = ''
  } catch (err) {}
}

function abrirPagamento() {
  pagamentoEditando.value = null
  formPagamento.value = {
    valor_pago: valorRestante.value > 0 ? valorRestante.value : pacote.value.valor_cobrado,
    data_pagamento: new Date().toISOString().split('T')[0],
    tipo_pagamento: 'pix',
    fechar_pacote: false,
    observacao: ''
  };
  showModalPagamento.value = true
}

async function fecharPacoteAction() {
  fechandoPacote.value = true
  try {
    await pacotesStore.fecharPacote(pacoteId.value)
    await carregarPacote()
  } catch (err) {
    alert('Erro ao fechar pacote: ' + (err.response?.data?.detail || err.message || err))
  } finally {
    fechandoPacote.value = false
  }
}

async function reabrirPacoteAction() {
  reabrindoPacote.value = true
  try {
    await pacotesStore.reabrirPacote(pacoteId.value)
    await carregarPacote()
  } catch (err) {
    alert('Erro ao reabrir pacote: ' + (err.response?.data?.detail || err.message || err))
  } finally {
    reabrindoPacote.value = false
  }
}

function abrirEditarPagamento(pg) {
  pagamentoEditando.value = pg
  formPagamento.value = {
    valor_pago: pg.valor_pago,
    data_pagamento: pg.data_pagamento,
    tipo_pagamento: pg.tipo_pagamento,
    fechar_pacote: false,
    observacao: pg.observacao || ''
  };
  showModalPagamento.value = true
}

async function confirmarPagamento() {
  try {
    if (pagamentoEditando.value) {
      await pacotesStore.atualizarPagamento(pacoteId.value, pagamentoEditando.value.id, {
        valor_pago: formPagamento.value.valor_pago,
        data_pagamento: formPagamento.value.data_pagamento,
        tipo_pagamento: formPagamento.value.tipo_pagamento,
        observacao: formPagamento.value.observacao
      })
      showModalPagamento.value = false
      await carregarPacote()
      alert('Pagamento atualizado com sucesso!')
    } else {
      // A store agora lida com o fechamento se necessário
      await pacotesStore.registrarPagamento(pacoteId.value, { ...formPagamento.value });
      showModalPagamento.value = false
      await carregarPacote()
      alert('Pagamento registrado com sucesso!')
    }
  } catch (err) { alert('Erro ao registrar pagamento: ' + err) }
}

function confirmarRemoverPagamento(pg) {
  pagamentoRemovendo.value = pg
  showConfirmRemovePagamento.value = true
}

async function executarRemoverPagamento() {
  if (!pagamentoRemovendo.value) return
  try {
    await pacotesStore.deletarPagamento(pacoteId.value, pagamentoRemovendo.value.id)
    showConfirmRemovePagamento.value = false
    pagamentoRemovendo.value = null
    await carregarPacote()
  } catch (err) {
    alert('Erro ao excluir pagamento: ' + err)
  }
}

function abrirEditarPacote() {
  formPacote.value = {
    tipo_plano: pacote.value.tipo_plano,
    dia_da_semana: pacote.value.dia_da_semana,
    valor_banho_base: pacote.value.valor_banho_base,
    valor_cobrado: pacote.value.valor_cobrado,
    valor_transporte: pacote.value.valor_transporte || 0
  }

  // Preenche um input de valor por cachorro adicional, usando o valor já
  // customizado (valores_cachorros) ou o valor base como padrão editável.
  Object.keys(formValoresCachorros).forEach(key => delete formValoresCachorros[key])
  cachorrosAdicionaisPacote.value.forEach(c => {
    const valorCustom = pacote.value.valores_cachorros?.[c.id]
    formValoresCachorros[c.id] = valorCustom ?? pacote.value.valor_banho_base
  })

  // Define o valor sugerido apenas como referência inicial sem alterar o valor_cobrado salvo
  calcularValorSugerido()
  sugestaoVisivel.value = true
  showModalEditPacote.value = true
}

function handleInputMudanca() {
  recalcularSugerido()
}

// Calcula apenas o valor sugerido (texto de referência), sem alterar formPacote.valor_cobrado.
function calcularValorSugerido() {
  const qtd = formPacote.value.tipo_plano === 'semanal' ? 4 : (formPacote.value.tipo_plano === 'quinzenal' ? 2 : 1)
  const valorBase = formPacote.value.valor_banho_base || 0
  const transporte = formPacote.value.valor_transporte || 0

  // Cada cachorro adicional soma seu próprio valor por banho; se vazio/inválido,
  // assume o valor base do cachorro principal.
  const valorPorBanho = cachorrosAdicionaisPacote.value.reduce((total, c) => {
    const valorExtra = formValoresCachorros[c.id]
    return total + (typeof valorExtra === 'number' && !Number.isNaN(valorExtra) ? valorExtra : valorBase)
  }, valorBase)

  valorSugerido.value = (valorPorBanho * qtd) + transporte
}

// Recalcula o sugerido E atualiza o valor final que será gravado (chamado quando o usuário edita).
function recalcularSugerido() {
  calcularValorSugerido()
  formPacote.value.valor_cobrado = valorSugerido.value
  sugestaoVisivel.value = true
}

async function salvarDadosPacote() {
  try {
    const valoresCachorros = Object.fromEntries(
      Object.entries(formValoresCachorros).filter(([, v]) => typeof v === 'number' && !Number.isNaN(v))
    )
    const payload = { ...formPacote.value }
    if (cachorrosAdicionaisPacote.value.length > 0) {
      payload.valores_cachorros = valoresCachorros
    }
    await pacotesStore.atualizarPacote(pacoteId.value, payload)
    showModalEditPacote.value = false
    await carregarPacote()
  } catch (err) {
    console.error('Erro ao atualizar pacote:', err)
    alert('Erro ao salvar as alterações do pacote: ' + (err.response?.data?.detail || err.message || err))
  }
}

function abrirEditarExtras(ag) {
  agExtras.value = ag
  const info = ag.extras?.info || (typeof ag.extras === 'string' ? ag.extras : '')
  const valor = ag.extras?.valor_extra || 0

  // Em pacotes multi-cachorro, cada pet começa com o status individual já
  // salvo; sem registro individual, herda o status geral do dia.
  const presencas = {}
  cachorrosDoPacote.value.forEach(c => {
    presencas[c.id] = statusDoCachorro(ag, c.id)
  })

  formExtras.value = {
    info,
    valor_extra: valor,
    status_presenca: ag.status_presenca || 'pendente',
    presencas
  }
  showModalExtras.value = true
}

async function salvarExtras() {
  try {
    const payload = {
      extras: { info: formExtras.value.info, valor_extra: formExtras.value.valor_extra }
    }

    if (qtdCachorros.value > 1) {
      // O backend deriva o status_presenca do dia a partir das presenças.
      payload.presencas = { ...formExtras.value.presencas }
    } else {
      payload.status_presenca = formExtras.value.status_presenca
    }

    await pacotesStore.updateAgendamento(agExtras.value.id, payload)
    showModalExtras.value = false
    await carregarPacote()
  } catch (err) {}
}

async function salvarExtra() {
  if (!dataExtra.value) return
  try {
    await pacotesStore.adicionarExtra(pacoteId.value, dataExtra.value)
    showAddExtra.value = false
    dataExtra.value = ''
  } catch (err) {}
}

function confirmarRemover(ag) {
  agRemovendo.value = ag
  showConfirmRemove.value = true
}

function confirmarDeletarPacote() {
  showConfirmDeletePacote.value = true
}

async function enviarComandaWhatsapp() {
  if (!pacote.value?.cliente_whatsapp) {
    alert('Este cliente não tem WhatsApp cadastrado. Adicione o número na tela de Clientes.')
    return
  }
  enviandoComanda.value = true
  try {
    await pacotesStore.enviarComanda(pacoteId.value)
    alert('Comanda enviada por WhatsApp com sucesso!')
  } catch (err) {
    alert('Erro ao enviar comanda: ' + (err.response?.data?.detail || err.message))
  } finally {
    enviandoComanda.value = false
  }
}

async function executarDeletarPacote() {
  try {
    await pacotesStore.deletarPacote(pacoteId.value)
    alert('Pacote excluído com sucesso!')
    router.push('/pacotes')
  } catch (err) {
    alert('Erro ao excluir pacote: ' + err)
  }
}

async function executarRemover() {
  if (!agRemovendo.value) return
  try {
    await pacotesStore.removerAgendamento(agRemovendo.value.id)
    showConfirmRemove.value = false
    agRemovendo.value = null
  } catch (err) {}
}

onMounted(carregarPacote)
</script>

<style scoped>
/* ── VARIÁVEIS ── */
.pacote-detail {
  --marrom:        #3b2a1a;
  --marrom-medio:  #5a3e28;
  --marrom-claro:  #8b6340;
  --dourado:       #d4a843;
  --dourado-claro: #f5e4a8;
  --dourado-bg:    #fdf6e3;
  --verde:         #6b8f4e;
  --verde-bg:      #eef4e6;
  --creme:         #faf6ef;
  --creme-escuro:  #f0e8d8;
  --text:          #2e1e0f;
  --text-muted:    #7a6251;
  --white:         #ffffff;
  --radius:        10px;
  --shadow:        0 2px 12px rgba(59,42,26,0.1);
  --shadow-md:     0 4px 20px rgba(59,42,26,0.15);

  max-width: 1100px;
  margin: 0 auto;
  padding: 1.5rem;
}

/* ── HEADER ── */
.header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.75rem;
  padding-bottom: 1.25rem;
  border-bottom: 2px solid var(--creme-escuro);
}

.btn-back {
  background: var(--creme-escuro);
  border: none;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--marrom);
  cursor: pointer;
  padding: 0.55rem 1rem;
  border-radius: 8px;
  transition: background 0.15s;
  white-space: nowrap;
}
.btn-back:hover { background: var(--dourado-claro); }

.header-info { flex: 1; }
.header-info h1 { margin: 0; font-size: 1.45rem; font-weight: 800; color: var(--marrom); }
.subheader { margin: 0.2rem 0 0; color: var(--text-muted); font-size: 0.9rem; font-weight: 600; }

.status-pill {
  padding: 0.45rem 1.1rem;
  border-radius: 20px;
  font-weight: 800;
  font-size: 0.8rem;
  letter-spacing: 0.5px;
  white-space: nowrap;
}
.status-pill.em_aberto { background: var(--dourado-claro); color: #6b4c00; }
.status-pill.pago      { background: var(--verde-bg);      color: var(--verde); }
.status-pill.parcial   { background: #fef0e0;              color: #8b5e00; }
.status-pill.fechado   { background: #e0e0e0;              color: #424242; }
.status-pill.atrasado  { background: #fdeaea;              color: #b94040; }

/* ── INFO CARDS ── */
.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.info-card {
  background: var(--white);
  border-radius: var(--radius);
  padding: 1.2rem 1.1rem;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  gap: 3px;
  border-bottom: 4px solid var(--marrom);
  transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
}
.info-card:nth-child(2) { border-bottom-color: var(--dourado); }
.info-card:nth-child(3) { border-bottom-color: var(--verde); }
.info-card:nth-child(4) { border-bottom-color: var(--marrom-claro); }
.info-card:nth-child(5) { border-bottom-color: var(--verde); }
.info-card.status-pago { border-bottom-color: var(--marrom-claro); }

.info-card.clickable { cursor: pointer; }
.info-card.clickable:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
  background: var(--dourado-bg);
  border-bottom-color: var(--dourado);
}

.info-label {
  font-size: 0.72rem;
  font-weight: 800;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.6px;
}
.info-value {
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--marrom);
  line-height: 1.2;
}
.info-sub {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-top: 2px;
}

/* ── ACTIONS BAR ── */
.actions-bar {
  margin-bottom: 1.4rem;
  display: flex;
  justify-content: flex-end;
}

.pacote-fechado-aviso {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--text-muted);
  background: var(--creme);
  border: 2px solid var(--creme-escuro);
  border-radius: 8px;
  padding: 0.6rem 0.9rem;
}

.footer-danger-zone {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px dashed var(--creme-escuro);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.danger-text {
  color: var(--text-muted);
  font-size: 0.85rem;
  font-weight: 600;
}

/* ── AGENDAMENTOS SECTION ── */
.agendamentos-section {
  background: var(--white);
  border-radius: var(--radius);
  padding: 1.5rem;
  box-shadow: var(--shadow);
}

.section-title {
  margin: 0 0 1.2rem;
  color: var(--marrom);
  font-size: 1.05rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-title-bar {
  display: inline-block;
  width: 4px; height: 18px;
  background: var(--dourado);
  border-radius: 2px;
  flex-shrink: 0;
}

/* ── TABELA ── */
.agendamentos-table {
  width: 100%;
  border-collapse: collapse;
}

.agendamentos-table th {
  padding: 0.85rem 0.9rem;
  text-align: left;
  background: var(--creme);
  font-weight: 800;
  color: var(--text-muted);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid var(--creme-escuro);
}

.agendamentos-table td {
  padding: 0.85rem 0.9rem;
  border-bottom: 1px solid var(--creme-escuro);
  font-size: 0.9rem;
  color: var(--text);
}

.agendamentos-table tbody tr:last-child td { border-bottom: none; }
.agendamentos-table tbody tr:hover td { background: var(--creme); }

.agendamentos-table tr.pendente  td { opacity: 0.85; }
.agendamentos-table tr.concluido td { background: var(--verde-bg); }
.agendamentos-table tr.faltou    td { background: #fdf0f0; }

.clickable-cell {
  cursor: pointer;
  text-decoration: underline dotted var(--creme-escuro);
  transition: color 0.15s;
}
.clickable-cell:hover { color: var(--marrom); text-decoration-color: var(--dourado); }

/* STATUS BADGE */
.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 5px;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.4px;
}
/* Badge por pet (pacotes multi-cachorro): uma linha por cachorro */
.status-badge-pet {
  display: block;
  width: fit-content;
  font-size: 0.68rem;
  margin-bottom: 3px;
}
.status-badge-pet:last-child { margin-bottom: 0; }

.status-badge.pendente  { background: var(--dourado-claro); color: #6b4c00; }
.status-badge.concluido { background: var(--verde-bg);      color: var(--verde); }
.status-badge.faltou    { background: #fdeaea;              color: #b94040; }

/* AÇÕES DA TABELA */
.acoes { display: flex; gap: 0.4rem; }

.btn-acao {
  border: none;
  padding: 0.38rem 0.7rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 700;
  transition: all 0.15s;
  line-height: 1;
}
.btn-acao-verde  { background: var(--verde);      color: white; }
.btn-acao-verde:hover  { background: #588040; }
.btn-acao-ghost  { background: var(--creme-escuro); color: var(--marrom); border: 1px solid var(--creme-escuro); }
.btn-acao-ghost:hover  { background: var(--dourado-claro); border-color: var(--dourado); }
.btn-acao-perigo { background: #fdeaea; color: #b94040; border: 1px solid #f5c0c0; }
.btn-acao-perigo:hover { background: #f8c8c8; }

/* TOTAL ROW */
.total-row td {
  padding: 1rem 0.9rem;
  background: var(--dourado-bg);
  border-top: 2px solid var(--dourado);
  font-size: 1rem;
}
.total-row strong { color: var(--marrom); }

/* EMPTY */
.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
  font-style: italic;
}

/* Seção de Pagamentos */
.pagamentos-section {
  margin-top: 1.5rem;
  background: var(--white); border-radius: var(--radius); padding: 1.5rem; box-shadow: var(--shadow);
}
.pagamentos-table {
  width: 100%;
  border-collapse: collapse;
}
.pagamentos-table th {
  padding: 0.85rem 0.9rem;
  text-align: left;
  background: var(--creme);
  font-weight: 800;
  color: var(--text-muted);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid var(--creme-escuro);
}
.pagamentos-table td {
  padding: 0.85rem 0.9rem;
  border-bottom: 1px solid var(--creme-escuro);
  font-size: 0.9rem;
  color: var(--text);
  vertical-align: middle;
}
.pagamentos-table tbody tr:last-child td { border-bottom: none; }
.pagamentos-table tbody tr:hover td { background: var(--creme); }
.pagamentos-table .col-observacao {
  color: var(--text-muted);
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── BOTÕES GERAIS ── */
.btn {
  padding: 0.65rem 1.3rem;
  border: none;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.15s;
}
.btn-primario { background: var(--marrom); color: var(--dourado); }
.btn-primario:hover { background: var(--marrom-medio); }
.btn-primario:disabled { opacity: 0.55; cursor: not-allowed; }

.btn-cancelar { background: var(--creme-escuro); color: var(--marrom); }
.btn-cancelar:hover { background: #e0d5c2; }

.btn-perigo { background: #fdeaea; color: #b94040; border: 1px solid #f5c0c0; }
.btn-perigo:hover { background: #f8c8c8; }

/* ── MODAIS ── */
.modal {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.45);
}

.modal-content {
  background: var(--white);
  padding: 2rem;
  border-radius: var(--radius);
  width: 90%;
  max-width: 440px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  z-index: 1001;
  border-top: 5px solid var(--dourado);
  box-shadow: 0 8px 32px rgba(59,42,26,0.2);
}

.modal-wide { max-width: 560px; }

.modal-header { margin-bottom: 1.2rem; }
.modal-header h3 {
  margin: 0 0 0.25rem;
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--marrom);
}
.modal-header-danger h3 { color: #b94040; }
.modal-sub {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.88rem;
  font-weight: 600;
}
.modal-info {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 1.2rem;
  background: var(--creme);
  padding: 0.6rem 0.85rem;
  border-radius: 7px;
  border-left: 3px solid var(--dourado);
}
.modal-info strong { color: var(--marrom); }

.warning-text {
  color: #b94040;
  font-size: 0.85rem;
  font-weight: 600;
  margin-top: -0.5rem;
  margin-bottom: 1.2rem;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
}
.modal-actions .btn { flex: 1; }

/* ── FORMULÁRIOS ── */
.form-group { margin-bottom: 1.1rem; }

.form-group label {
  display: block;
  margin-bottom: 0.35rem;
  font-weight: 700;
  color: var(--marrom);
  font-size: 0.88rem;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.65rem 0.85rem;
  border: 2px solid var(--creme-escuro);
  border-radius: 7px;
  font-size: 0.95rem;
  font-family: inherit;
  color: var(--text);
  background: var(--creme);
  box-sizing: border-box;
  transition: border-color 0.15s, box-shadow 0.15s;
  outline: none;
  resize: vertical;
}
.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  border-color: var(--dourado);
  box-shadow: 0 0 0 3px rgba(212,168,67,0.12);
  background: var(--white);
}

.grid-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.9rem;
}

.form-highlight input {
  border-color: var(--dourado);
  background: var(--dourado-bg);
  font-weight: 800;
  font-size: 1.05rem;
  color: var(--marrom);
}

/* ── PRESENÇA POR PET (pacotes multi-cachorro) ── */
.presencas-grid {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.presenca-pet {
  background: var(--creme);
  border: 2px solid var(--creme-escuro);
  border-radius: 8px;
  padding: 0.7rem 0.8rem;
}

.presenca-pet-topo {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.45rem;
}

.presenca-pet-nome {
  font-weight: 800;
  font-size: 0.88rem;
  color: var(--marrom);
}

.presenca-pet-valor {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-muted);
}

.presenca-pet select { background: var(--white); }

.helper-text {
  color: var(--text-muted);
  font-size: 0.75rem;
  margin-top: 0.3rem;
  display: block;
  font-style: italic;
}
</style>