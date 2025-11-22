<template>
  <v-app>
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>

    <!-- Global snackbar for notifications -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="snackbar.timeout"
      location="top"
      variant="flat"
    >
      {{ snackbar.message }}
      <template v-slot:actions>
        <v-btn
          variant="text"
          @click="snackbar.show = false"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script setup lang="ts">
import { onMounted, reactive, provide } from 'vue'
import { useTheme } from 'vuetify'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

// Notification system
interface Snackbar {
  show: boolean
  message: string
  color: string
  timeout: number
}

const snackbar = reactive<Snackbar>({
  show: false,
  message: '',
  color: 'success',
  timeout: 3000
})

// Provide notification method globally
const notify = (message: string, color = 'success', timeout = 3000) => {
  snackbar.message = message
  snackbar.color = color
  snackbar.timeout = timeout
  snackbar.show = true
}

provide('notify', notify)

// Theme management
const theme = useTheme()
const authStore = useAuthStore()
const router = useRouter()

onMounted(async () => {
  // Apply saved theme preference
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme) {
    theme.global.name.value = savedTheme
  }

  // Check authentication status
  if (authStore.isAuthenticated && authStore.token) {
    try {
      await authStore.validateToken()
    } catch (error) {
      await authStore.logout()
      router.push('/login')
    }
  }
})
</script>

<style lang="scss">
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// Global styles
html {
  overflow-y: auto !important;
}

// Scrollbar styling
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgb(var(--v-theme-surface));
}

::-webkit-scrollbar-thumb {
  background: rgb(var(--v-theme-primary));
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgb(var(--v-theme-primary-darken-1));
}
</style>