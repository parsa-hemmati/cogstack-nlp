<template>
  <v-app-bar
    elevation="1"
    color="primary"
    dark
  >
    <v-app-bar-nav-icon @click="drawer = !drawer" />

    <v-app-bar-title>
      Clinical Care Tools
    </v-app-bar-title>

    <v-spacer />

    <!-- Search -->
    <v-text-field
      v-model="searchQuery"
      prepend-inner-icon="mdi-magnify"
      placeholder="Search..."
      variant="solo"
      density="compact"
      hide-details
      single-line
      class="mx-4"
      style="max-width: 300px"
      @keyup.enter="handleSearch"
    />

    <!-- Notifications -->
    <v-menu>
      <template v-slot:activator="{ props }">
        <v-btn icon v-bind="props">
          <v-badge
            :content="unreadNotifications"
            :value="unreadNotifications > 0"
            color="error"
          >
            <v-icon>mdi-bell</v-icon>
          </v-badge>
        </v-btn>
      </template>

      <v-list max-width="350">
        <v-list-item>
          <v-list-item-title>Notifications</v-list-item-title>
        </v-list-item>
        <v-divider />
        <v-list-item
          v-for="notification in notifications"
          :key="notification.id"
        >
          <template v-slot:prepend>
            <v-icon :color="notification.color">{{ notification.icon }}</v-icon>
          </template>
          <v-list-item-title>{{ notification.title }}</v-list-item-title>
          <v-list-item-subtitle>{{ notification.message }}</v-list-item-subtitle>
        </v-list-item>
        <v-divider />
        <v-list-item>
          <v-btn block variant="text">View All Notifications</v-btn>
        </v-list-item>
      </v-list>
    </v-menu>

    <!-- User Menu -->
    <v-menu>
      <template v-slot:activator="{ props }">
        <v-btn icon v-bind="props">
          <v-avatar size="32" color="secondary">
            {{ userInitials }}
          </v-avatar>
        </v-btn>
      </template>

      <v-list>
        <v-list-item>
          <v-list-item-title>{{ authStore.displayName }}</v-list-item-title>
          <v-list-item-subtitle>{{ authStore.user?.email }}</v-list-item-subtitle>
        </v-list-item>
        <v-divider />
        <v-list-item to="/profile" prepend-icon="mdi-account">
          <v-list-item-title>Profile</v-list-item-title>
        </v-list-item>
        <v-list-item to="/settings" prepend-icon="mdi-cog">
          <v-list-item-title>Settings</v-list-item-title>
        </v-list-item>
        <v-list-item @click="handleThemeToggle" prepend-icon="mdi-theme-light-dark">
          <v-list-item-title>Toggle Theme</v-list-item-title>
        </v-list-item>
        <v-divider />
        <v-list-item @click="handleLogout" prepend-icon="mdi-logout">
          <v-list-item-title>Logout</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
  </v-app-bar>
</template>

<script setup lang="ts">
import { ref, computed, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const theme = useTheme()
const authStore = useAuthStore()
const notify = inject<(message: string, color?: string) => void>('notify')

// Drawer state (shared with AppSidebar)
const drawer = ref(true)

// Search
const searchQuery = ref('')

// Notifications
const unreadNotifications = ref(3)
const notifications = ref([
  {
    id: 1,
    icon: 'mdi-check-circle',
    color: 'success',
    title: 'Processing Complete',
    message: 'Batch processing completed successfully'
  },
  {
    id: 2,
    icon: 'mdi-alert',
    color: 'warning',
    title: 'Review Required',
    message: '5 documents require manual review'
  },
  {
    id: 3,
    icon: 'mdi-information',
    color: 'info',
    title: 'System Update',
    message: 'New features available in version 2.1.0'
  }
])

// User initials for avatar
const userInitials = computed(() => {
  const user = authStore.user
  if (!user) return '?'
  const first = user.firstName?.[0] || ''
  const last = user.lastName?.[0] || ''
  return (first + last).toUpperCase() || user.username?.[0]?.toUpperCase() || '?'
})

// Methods
function handleSearch() {
  if (searchQuery.value.trim()) {
    router.push({
      path: '/search',
      query: { q: searchQuery.value }
    })
    searchQuery.value = ''
  }
}

function handleThemeToggle() {
  const newTheme = theme.global.current.value.dark ? 'light' : 'dark'
  theme.global.name.value = newTheme
  localStorage.setItem('theme', newTheme)
  notify?.(`Theme changed to ${newTheme} mode`, 'success')
}

async function handleLogout() {
  try {
    await authStore.logout()
    notify?.('Logged out successfully', 'success')
    router.push('/login')
  } catch (error) {
    notify?.('Error during logout', 'error')
  }
}

// Export drawer state for AppSidebar
defineExpose({ drawer })
</script>