/**
 * Configuração do Vue Router.
 * Define rotas para todas as views da aplicação.
 */
import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Pacotes from '../views/Pacotes.vue'
import Clientes from '../views/Clientes.vue'
import Relatorios from '../views/Relatorios.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/pacotes',
    name: 'Pacotes',
    component: Pacotes
  },
  {
    path: '/clientes',
    name: 'Clientes',
    component: Clientes
  },
  {
    path: '/relatorios',
    name: 'Relatorios',
    component: Relatorios
  },
  {
    path: '/pacotes/:id',
    name: 'PacoteDetail',
    component: () => import('../views/PacoteDetail.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router