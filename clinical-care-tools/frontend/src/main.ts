import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import './plugins/axios'

// Styles
import '@mdi/font/css/materialdesignicons.css'
import './assets/styles/main.scss'

// Create Vue app
const app = createApp(App)

// Create Pinia store with persistence
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

// Use plugins
app.use(pinia)
app.use(router)
app.use(vuetify)

// Global error handler
app.config.errorHandler = (error, instance, info) => {
  // NOTE: Send to error tracking service
}

// Mount app
app.mount('#app')