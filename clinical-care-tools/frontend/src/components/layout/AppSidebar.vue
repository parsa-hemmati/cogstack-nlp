<template>
  <v-navigation-drawer
    v-model="drawer"
    app
    color="grey-lighten-4"
    :rail="rail"
  >
    <v-list nav density="compact">
      <v-list-item
        v-for="item in navigationItems"
        :key="item.title"
        :to="item.to"
        :prepend-icon="item.icon"
        :value="item.title"
      >
        <v-list-item-title>{{ item.title }}</v-list-item-title>
        <template v-slot:append v-if="item.badge">
          <v-badge
            :content="item.badge"
            color="error"
            inline
          />
        </template>
      </v-list-item>
    </v-list>

    <template v-slot:append>
      <v-divider />
      <v-list nav density="compact">
        <v-list-item @click="rail = !rail">
          <template v-slot:prepend>
            <v-icon>{{ rail ? 'mdi-chevron-right' : 'mdi-chevron-left' }}</v-icon>
          </template>
          <v-list-item-title>Collapse</v-list-item-title>
        </v-list-item>
      </v-list>
    </template>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// Drawer state
const drawer = ref(true)
const rail = ref(false)

// Navigation items based on user permissions
const navigationItems = computed(() => {
  const items = [
    {
      icon: 'mdi-view-dashboard',
      title: 'Dashboard',
      to: '/dashboard'
    }
  ]

  // Add items based on permissions
  if (authStore.hasPermission('view_patients')) {
    items.push({
      icon: 'mdi-account-group',
      title: 'Patients',
      to: '/patients'
    })
  }

  if (authStore.hasPermission('search_patients')) {
    items.push({
      icon: 'mdi-magnify',
      title: 'Search',
      to: '/search'
    })
  }

  if (authStore.hasPermission('view_documents')) {
    items.push({
      icon: 'mdi-file-document-multiple',
      title: 'Documents',
      to: '/documents'
    })
  }

  if (authStore.hasPermission('view_timeline')) {
    items.push({
      icon: 'mdi-timeline',
      title: 'Timeline',
      to: '/timeline'
    })
  }

  if (authStore.hasPermission('view_annotations')) {
    items.push({
      icon: 'mdi-tag-multiple',
      title: 'Annotations',
      to: '/annotations',
      badge: '5'  // Example badge
    })
  }

  if (authStore.hasPermission('view_reports')) {
    items.push({
      icon: 'mdi-chart-box',
      title: 'Reports',
      to: '/reports'
    })
  }

  if (authStore.hasPermission('admin')) {
    items.push(
      {
        icon: 'mdi-account-supervisor',
        title: 'Users',
        to: '/admin/users'
      },
      {
        icon: 'mdi-brain',
        title: 'Models',
        to: '/admin/models'
      }
    )
  }

  // Always show settings
  items.push({
    icon: 'mdi-cog',
    title: 'Settings',
    to: '/settings'
  })

  return items
})
</script>