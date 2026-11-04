<template>
  <div class="admin-container">
    <div class="admin-card">
      <div class="logo">
        <div class="logo-icon">🔐</div>
        <h1 class="logo-titulo">Administração de contas</h1>
        <p class="logo-sub">Recanto Mini Dogs</p>
      </div>

      <!-- Passo 1: chave mestra -->
      <form v-if="!chave" @submit.prevent="entrar" class="form">
        <div class="form-group">
          <label for="chave">Chave de administração</label>
          <input id="chave" v-model="chaveDigitada" type="password" autocomplete="off" placeholder="••••••••" required />
          <small class="dica">É o valor de ADMIN_PASSWORD no arquivo .env do servidor.</small>
        </div>
        <div v-if="erro" class="msg erro">⚠️ {{ erro }}</div>
        <button type="submit" class="btn-submit" :disabled="carregando">
          {{ carregando ? '⏳ Verificando...' : 'Acessar' }}
        </button>
      </form>

      <!-- Passo 2: gerenciamento -->
      <template v-else>
        <div v-if="erro" class="msg erro">⚠️ {{ erro }}</div>
        <div v-if="sucesso" class="msg ok">✅ {{ sucesso }}</div>

        <h2 class="secao">Contas</h2>
        <ul class="lista">
          <li v-for="u in usuarios" :key="u.id" :class="{ inativo: !u.ativo }">
            <div class="linha-topo">
              <span class="email">{{ u.email }}</span>
              <span class="tag" :class="u.ativo ? 'tag-ativo' : 'tag-inativo'">{{ u.ativo ? 'ativa' : 'desativada' }}</span>
            </div>
            <div class="acoes">
              <button class="btn-mini" @click="abrirSenha(u)">Alterar senha</button>
              <button class="btn-mini" @click="alternarAtivo(u)">{{ u.ativo ? 'Desativar' : 'Ativar' }}</button>
              <button class="btn-mini perigo" @click="excluir(u)">Excluir</button>
            </div>
            <form v-if="editando === u.id" @submit.prevent="salvarSenha(u)" class="form-inline">
              <input v-model="novaSenha" type="password" autocomplete="new-password" minlength="8" placeholder="Nova senha (mín. 8)" required />
              <button type="submit" class="btn-mini">Salvar</button>
              <button type="button" class="btn-mini" @click="editando = null">Cancelar</button>
            </form>
          </li>
          <li v-if="!usuarios.length" class="vazio">Nenhuma conta cadastrada.</li>
        </ul>

        <h2 class="secao">Nova conta</h2>
        <form @submit.prevent="criar" class="form">
          <div class="form-group">
            <label for="novo-email">E-mail</label>
            <input id="novo-email" v-model="novo.email" type="email" autocomplete="off" required />
          </div>
          <div class="form-group">
            <label for="novo-senha">Senha</label>
            <input id="novo-senha" v-model="novo.senha" type="password" autocomplete="new-password" minlength="8" placeholder="Mínimo 8 caracteres" required />
          </div>
          <button type="submit" class="btn-submit" :disabled="carregando">Criar conta</button>
        </form>

        <button class="btn-sair" @click="sair">Sair do painel</button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'

// Cliente próprio: não usa o JWT do sistema nem o redirecionamento para /login.
// A chave mestra fica só em memória (some ao recarregar ou fechar a aba).
const http = axios.create({ baseURL: '/api/v1/admin-canil', timeout: 15000 })

const chaveDigitada = ref('')
const chave = ref('')
const usuarios = ref([])
const carregando = ref(false)
const erro = ref('')
const sucesso = ref('')
const editando = ref(null)
const novaSenha = ref('')
const novo = reactive({ email: '', senha: '' })

function cabecalho() {
  return { headers: { 'X-Admin-Key': chave.value } }
}

function mensagemDe(e) {
  const d = e.response?.data?.detail
  if (Array.isArray(d)) return d.map((x) => x.msg?.replace(/^Value error, /, '')).join('; ')
  if (e.response?.status === 429) return 'Muitas tentativas. Aguarde um minuto.'
  return d || 'Não foi possível concluir a operação.'
}

function limparMensagens() {
  erro.value = ''
  sucesso.value = ''
}

async function carregar() {
  const r = await http.get('/usuarios', cabecalho())
  usuarios.value = r.data
}

async function entrar() {
  limparMensagens()
  carregando.value = true
  chave.value = chaveDigitada.value
  try {
    await carregar()
    chaveDigitada.value = ''
  } catch (e) {
    chave.value = ''
    erro.value = e.response?.status === 403 ? 'Chave inválida.' : mensagemDe(e)
  } finally {
    carregando.value = false
  }
}

async function executar(acao, textoSucesso) {
  limparMensagens()
  carregando.value = true
  try {
    await acao()
    await carregar()
    sucesso.value = textoSucesso
    return true
  } catch (e) {
    erro.value = mensagemDe(e)
    return false
  } finally {
    carregando.value = false
  }
}

async function criar() {
  const ok = await executar(
    () => http.post('/usuarios', { email: novo.email, senha: novo.senha }, cabecalho()),
    'Conta criada.',
  )
  if (ok) {
    novo.email = ''
    novo.senha = ''
  }
}

function abrirSenha(u) {
  limparMensagens()
  editando.value = u.id
  novaSenha.value = ''
}

async function salvarSenha(u) {
  const ok = await executar(
    () => http.put(`/usuarios/${u.id}/senha`, { nova_senha: novaSenha.value }, cabecalho()),
    `Senha de ${u.email} alterada. Sessões abertas dessa conta foram encerradas.`,
  )
  if (ok) {
    editando.value = null
    novaSenha.value = ''
  }
}

function alternarAtivo(u) {
  return executar(
    () => http.patch(`/usuarios/${u.id}`, { ativo: !u.ativo }, cabecalho()),
    u.ativo ? 'Conta desativada.' : 'Conta ativada.',
  )
}

function excluir(u) {
  if (!window.confirm(`Excluir a conta ${u.email}? Isso não pode ser desfeito.`)) return
  return executar(() => http.delete(`/usuarios/${u.id}`, cabecalho()), 'Conta excluída.')
}

function sair() {
  chave.value = ''
  usuarios.value = []
  limparMensagens()
}
</script>

<style scoped>
.admin-container {
  --marrom: #3b2a1a;
  --marrom-medio: #5a3e28;
  --dourado: #d4a843;
  --creme: #faf6ef;
  --creme-escuro: #f0e8d8;
  --text: #2e1e0f;
  --text-muted: #7a6251;

  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  overflow-y: auto;
  padding: 1.5rem 1rem;
  background-color: var(--marrom);
}

.admin-card {
  background: #fff;
  padding: 2rem 1.75rem 1.5rem;
  border-radius: 18px;
  box-shadow: 0 8px 32px rgba(59, 42, 26, 0.18);
  width: 100%;
  max-width: 520px;
  border-top: 6px solid var(--dourado);
  box-sizing: border-box;
}

.logo { text-align: center; margin-bottom: 1.25rem; }
.logo-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 60px; height: 60px; background: var(--marrom); border-radius: 50%;
  font-size: 1.6rem; border: 4px solid var(--dourado); margin-bottom: 0.6rem;
}
.logo-titulo { font-size: 1.25rem; font-weight: 800; color: var(--marrom); margin: 0 0 0.2rem; }
.logo-sub { font-size: 0.75rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }

.secao { font-size: 1rem; color: var(--marrom); margin: 1.25rem 0 0.6rem; }

.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.85rem; font-weight: 700; color: var(--marrom); margin-bottom: 0.35rem; }
input {
  width: 100%; padding: 0.65rem 0.85rem; border: 2px solid var(--creme-escuro);
  border-radius: 8px; font-size: 0.95rem; color: var(--text); background: var(--creme);
  box-sizing: border-box; outline: none;
}
input:focus { border-color: var(--dourado); background: #fff; }
.dica { display: block; margin-top: 0.3rem; font-size: 0.75rem; color: var(--text-muted); }

.btn-submit {
  width: 100%; padding: 0.75rem; background: var(--marrom); color: var(--dourado);
  border: none; border-radius: 8px; font-size: 0.95rem; font-weight: 800; cursor: pointer;
}
.btn-submit:hover:not(:disabled) { background: var(--marrom-medio); }
.btn-submit:disabled { opacity: 0.65; cursor: not-allowed; }

.msg { border-radius: 8px; font-size: 0.85rem; font-weight: 600; padding: 0.6rem 0.85rem; margin-bottom: 0.75rem; text-align: center; }
.msg.erro { background: #fdeaea; border: 1px solid #f5c0c0; color: #b94040; }
.msg.ok { background: #eef4e6; border: 1px solid #c5dba8; color: #4b6b30; }

.lista { list-style: none; padding: 0; margin: 0; }
.lista li { border: 1px solid var(--creme-escuro); border-radius: 10px; padding: 0.7rem 0.85rem; margin-bottom: 0.5rem; background: var(--creme); }
.lista li.inativo { opacity: 0.7; }
.lista li.vazio { text-align: center; color: var(--text-muted); }
.linha-topo { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.email { font-weight: 700; color: var(--text); word-break: break-all; }
.tag { font-size: 0.7rem; font-weight: 800; padding: 0.15rem 0.5rem; border-radius: 99px; }
.tag-ativo { background: #eef4e6; color: #4b6b30; }
.tag-inativo { background: #f0e8d8; color: var(--text-muted); }
.acoes { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.55rem; }
.btn-mini {
  padding: 0.35rem 0.7rem; font-size: 0.8rem; font-weight: 700; border-radius: 6px; cursor: pointer;
  border: 1px solid var(--marrom-medio); background: #fff; color: var(--marrom);
}
.btn-mini:hover { background: var(--creme-escuro); }
.btn-mini.perigo { border-color: #b94040; color: #b94040; }
.form-inline { display: flex; gap: 0.4rem; margin-top: 0.6rem; flex-wrap: wrap; }
.form-inline input { flex: 1 1 180px; width: auto; }

.btn-sair { margin-top: 1.25rem; width: 100%; background: none; border: none; color: var(--text-muted); font-weight: 700; cursor: pointer; text-decoration: underline; }
</style>
