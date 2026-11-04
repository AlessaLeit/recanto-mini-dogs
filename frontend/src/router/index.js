/**
 * Configuração do Vue Router.
 * Define rotas para todas as views da aplicação.
 */
import { createRouter, createWebHistory } from "vue-router";
import Dashboard from "../views/Dashboard.vue";
import Pacotes from "../views/Pacotes.vue";
import Clientes from "../views/Clientes.vue";
import Relatorios from "../views/Relatorios.vue";
import Login from "../views/Login.vue";
import AdminCanil from "../views/AdminCanil.vue";
import PacoteDetail from "../views/PacoteDetail.vue";
import BanhosAvulsos from "../views/BanhosAvulsos.vue";
import ClienteDetail from "../views/ClienteDetail.vue";
import WhatsAppConfig from "../views/WhatsAppConfig.vue";
import ComandasImpressao from "../views/ComandasImpressao.vue";
import { useAuthStore } from "../stores/auth";

const routes = [
  {
    path: "/",
    name: "Dashboard",
    component: Dashboard,
  },
  {
    path: "/login",
    name: "Login",
    component: Login,
    meta: { hideHeader: true },
  },
  {
    // Painel oculto de contas: sem link no menu e fora do login normal
    // (protegido pela chave mestra no backend)
    path: "/ale_admin_canil",
    name: "AdminCanil",
    component: AdminCanil,
    meta: { hideHeader: true, publicPage: true },
  },
  {
    path: "/pacotes",
    name: "Pacotes",
    component: Pacotes,
  },
  {
    path: "/clientes",
    name: "Clientes",
    component: Clientes,
  },
  {
    path: "/relatorios",
    name: "Relatorios",
    component: Relatorios,
  },
  {
    path: "/banhos-avulsos",
    name: "BanhosAvulsos",
    component: BanhosAvulsos,
  },
  {
    path: "/pacotes/:id",
    name: "PacoteDetail",
    component: PacoteDetail,
  },
  {
    path: "/clientes/:id",
    name: "ClienteDetail",
    component: ClienteDetail,
  },
  {
    path: "/whatsapp",
    name: "WhatsAppConfig",
    component: WhatsAppConfig,
  },
  {
    path: "/comandas-impressao",
    name: "ComandasImpressao",
    component: ComandasImpressao,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  // Evita divergência entre store e localStorage.
  // Mesmo que o store demore/ falhe em inicializar, o guard usa o token persistido.
  const token = localStorage.getItem("token");
  const isAuthenticated = !!token;

  if (to.meta.publicPage) {
    next();
  } else if (to.path !== "/login" && !isAuthenticated) {
    next("/login");
  } else if (to.path === "/login" && isAuthenticated) {
    next("/");
  } else {
    next();
  }
});

export default router;
