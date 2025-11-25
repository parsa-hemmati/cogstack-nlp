/**
 * Clinical Care Tools - Frontend Application
 *
 * Main entry point for the Vue 3 application.
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'

// Import global styles
import './styles/main.scss'

const app = createApp(App)

// Register plugins
app.use(createPinia())
app.use(router)
app.use(vuetify)

// Mount application
app.mount('#app')
