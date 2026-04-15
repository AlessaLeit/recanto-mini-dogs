/**
 * Ponto de entrada da aplicação Vue 3.
 * Configura Pinia, Router e monta o app.
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

const app = createApp(App)

// Configura Pinia para estado global
app.use(createPinia())

// Configura Vue Router
app.use(router)

// Monta a aplicação
app.mount('#app')