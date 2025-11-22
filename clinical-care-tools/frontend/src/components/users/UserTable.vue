<template>
  <v-data-table
    :headers="headers"
    :items="users"
    :loading="loading"
    :search="search"
    :items-per-page="itemsPerPage"
    :sort-by="[{ key: 'createdAt', order: 'desc' }]"
    class="elevation-1"
  >
    <!-- Top slot for search and actions -->
    <template #top>
      <v-toolbar flat>
        <v-text-field
          v-model="search"
          prepend-icon="mdi-magnify"
          label="Search users..."
          single-line
          hide-details
          clearable
          density="compact"
          class="mx-4"
        />
        <v-spacer />
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          @click="$emit('create')"
        >
          Add User
        </v-btn>
      </v-toolbar>
    </template>

    <!-- User column with avatar -->
    <template #item.user="{ item }">
      <div class="d-flex align-center py-2">
        <v-avatar size="32" color="primary" class="mr-2">
          <span class="text-h6">
            {{ getInitials(item) }}
          </span>
        </v-avatar>
        <div>
          <div class="font-weight-medium">{{ getDisplayName(item) }}</div>
          <div class="text-caption text-grey">{{ item.username }}</div>
        </div>
      </div>
    </template>

    <!-- Email column -->
    <template #item.email="{ item }">
      <a :href="`mailto:${item.email}`" class="text-decoration-none">
        {{ item.email }}
      </a>
    </template>

    <!-- Roles column -->
    <template #item.roles="{ item }">
      <div class="py-1">
        <v-chip
          v-for="role in item.roles"
          :key="role"
          :color="getRoleColor(role)"
          size="small"
          variant="elevated"
          class="ma-1"
        >
          {{ role }}
        </v-chip>
      </div>
    </template>

    <!-- Status column -->
    <template #item.isActive="{ item }">
      <v-chip
        :color="item.isActive ? 'success' : 'error'"
        :prepend-icon="item.isActive ? 'mdi-check-circle' : 'mdi-close-circle'"
        variant="flat"
        size="small"
      >
        {{ item.isActive ? 'Active' : 'Inactive' }}
      </v-chip>
    </template>

    <!-- Last login column -->
    <template #item.lastLogin="{ item }">
      <span v-if="item.lastLogin" class="text-caption">
        {{ formatDate(item.lastLogin) }}
      </span>
      <span v-else class="text-caption text-grey">
        Never
      </span>
    </template>

    <!-- Actions column -->
    <template #item.actions="{ item }">
      <v-btn
        icon="mdi-pencil"
        size="small"
        variant="text"
        @click="$emit('edit', item)"
        aria-label="Edit user"
      />
      <v-btn
        icon="mdi-key"
        size="small"
        variant="text"
        @click="$emit('reset-password', item)"
        aria-label="Reset password"
      />
      <v-btn
        :icon="item.isActive ? 'mdi-lock' : 'mdi-lock-open'"
        size="small"
        variant="text"
        @click="$emit('toggle-status', item)"
        :aria-label="item.isActive ? 'Deactivate user' : 'Activate user'"
      />
      <v-btn
        icon="mdi-delete"
        size="small"
        variant="text"
        color="error"
        @click="$emit('delete', item)"
        aria-label="Delete user"
      />
    </template>

    <!-- Loading slot -->
    <template #loading>
      <v-skeleton-loader
        v-for="i in 5"
        :key="i"
        type="table-row"
        class="my-2"
      />
    </template>

    <!-- No data slot -->
    <template #no-data>
      <v-container>
        <v-row justify="center">
          <v-col cols="12" sm="8" md="6" class="text-center">
            <v-icon size="64" color="grey">mdi-account-group</v-icon>
            <h3 class="text-h5 mt-4 mb-2">No Users Found</h3>
            <p class="text-body-2 text-grey">
              {{ search ? 'No users match your search criteria' : 'No users have been created yet' }}
            </p>
            <v-btn
              v-if="!search"
              color="primary"
              prepend-icon="mdi-plus"
              @click="$emit('create')"
              class="mt-4"
            >
              Add First User
            </v-btn>
          </v-col>
        </v-row>
      </v-container>
    </template>
  </v-data-table>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { User } from '@/types'

// Props
defineProps<{
  users: User[]
  loading?: boolean
}>()

// Emits
defineEmits<{
  create: []
  edit: [user: User]
  delete: [user: User]
  'reset-password': [user: User]
  'toggle-status': [user: User]
}>()

// Data
const search = ref('')
const itemsPerPage = ref(10)

// Table headers
const headers = computed(() => [
  {
    title: 'User',
    key: 'user',
    sortable: false
  },
  {
    title: 'Email',
    key: 'email',
    sortable: true
  },
  {
    title: 'Roles',
    key: 'roles',
    sortable: false
  },
  {
    title: 'Status',
    key: 'isActive',
    sortable: true
  },
  {
    title: 'Last Login',
    key: 'lastLogin',
    sortable: true
  },
  {
    title: 'Actions',
    key: 'actions',
    sortable: false,
    align: 'center'
  }
])

// Methods
function getInitials(user: User): string {
  if (user.firstName && user.lastName) {
    return `${user.firstName[0]}${user.lastName[0]}`.toUpperCase()
  }
  return user.username.substring(0, 2).toUpperCase()
}

function getDisplayName(user: User): string {
  if (user.firstName || user.lastName) {
    return `${user.firstName || ''} ${user.lastName || ''}`.trim()
  }
  return user.username
}

function getRoleColor(role: string): string {
  const colors: Record<string, string> = {
    admin: 'red',
    clinician: 'blue',
    researcher: 'green',
    viewer: 'grey'
  }
  return colors[role] || 'default'
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) {
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    if (diffHours === 0) {
      const diffMinutes = Math.floor(diffMs / (1000 * 60))
      return `${diffMinutes} minutes ago`
    }
    return `${diffHours} hours ago`
  } else if (diffDays === 1) {
    return 'Yesterday'
  } else if (diffDays < 7) {
    return `${diffDays} days ago`
  } else {
    return date.toLocaleDateString()
  }
}
</script>