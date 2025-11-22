<template>
  <v-card>
    <v-card-title>
      <v-icon class="mr-2">mdi-filter</v-icon>
      Filters
    </v-card-title>

    <v-card-text>
      <!-- Search -->
      <v-text-field
        v-model="searchQuery"
        label="Search tasks..."
        prepend-inner-icon="mdi-magnify"
        variant="outlined"
        density="compact"
        clearable
        hide-details
        class="mb-4"
        @input="handleSearch"
      />

      <!-- My Tasks Toggle -->
      <v-switch
        v-model="showMyTasks"
        label="My Tasks Only"
        color="primary"
        hide-details
        class="mb-4"
        @change="handleMyTasksToggle"
      />

      <v-divider class="mb-4" />

      <!-- Project Filter -->
      <div class="mb-4">
        <label class="text-caption text-grey">Project</label>
        <v-select
          v-model="selectedProject"
          :items="projectOptions"
          item-title="name"
          item-value="id"
          variant="outlined"
          density="compact"
          clearable
          hide-details
          @update:model-value="handleProjectFilter"
        />
      </div>

      <!-- Status Filter -->
      <div class="mb-4">
        <label class="text-caption text-grey">Status</label>
        <v-select
          v-model="selectedStatus"
          :items="statusOptions"
          variant="outlined"
          density="compact"
          clearable
          hide-details
          @update:model-value="handleStatusFilter"
        />
      </div>

      <!-- Priority Filter -->
      <div class="mb-4">
        <label class="text-caption text-grey">Priority</label>
        <v-select
          v-model="selectedPriority"
          :items="priorityOptions"
          variant="outlined"
          density="compact"
          clearable
          hide-details
          @update:model-value="handlePriorityFilter"
        >
          <template #item="{ props: itemProps, item }">
            <v-list-item v-bind="itemProps">
              <template #prepend>
                <v-icon :color="getPriorityColor(item.value)">
                  mdi-flag
                </v-icon>
              </template>
            </v-list-item>
          </template>
        </v-select>
      </div>

      <!-- Assignee Filter -->
      <div class="mb-4">
        <label class="text-caption text-grey">Assignee</label>
        <v-autocomplete
          v-model="selectedAssignee"
          :items="userOptions"
          item-title="display"
          item-value="id"
          variant="outlined"
          density="compact"
          clearable
          hide-details
          @update:model-value="handleAssigneeFilter"
        >
          <template #item="{ props: itemProps, item }">
            <v-list-item v-bind="itemProps">
              <template #prepend>
                <v-avatar size="28" :color="getAvatarColor(item.raw.id)">
                  <span class="text-caption">
                    {{ getInitials(item.raw) }}
                  </span>
                </v-avatar>
              </template>
            </v-list-item>
          </template>
        </v-autocomplete>
      </div>

      <!-- Quick Filters -->
      <div>
        <label class="text-caption text-grey">Quick Filters</label>
        <v-chip-group
          v-model="selectedQuickFilter"
          column
          @update:model-value="handleQuickFilter"
        >
          <v-chip
            value="overdue"
            filter
            variant="outlined"
            prepend-icon="mdi-alert"
            color="error"
          >
            Overdue
          </v-chip>
          <v-chip
            value="unassigned"
            filter
            variant="outlined"
            prepend-icon="mdi-account-off"
          >
            Unassigned
          </v-chip>
          <v-chip
            value="urgent"
            filter
            variant="outlined"
            prepend-icon="mdi-flag"
            color="purple"
          >
            Urgent
          </v-chip>
          <v-chip
            value="completed"
            filter
            variant="outlined"
            prepend-icon="mdi-check-circle"
            color="success"
          >
            Completed
          </v-chip>
        </v-chip-group>
      </div>
    </v-card-text>

    <v-card-actions>
      <v-btn
        variant="text"
        @click="clearFilters"
        :disabled="!hasActiveFilters"
      >
        Clear All
      </v-btn>
      <v-spacer />
      <v-chip size="small" color="primary" v-if="activeFilterCount > 0">
        {{ activeFilterCount }} {{ activeFilterCount === 1 ? 'filter' : 'filters' }}
      </v-chip>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTasksStore } from '@/stores/tasks'
import { useProjectsStore } from '@/stores/projects'
import { useUsersStore } from '@/stores/users'
import { useAuthStore } from '@/stores/auth'
import type { TaskStatus, TaskPriority, User } from '@/types'

// Stores
const tasksStore = useTasksStore()
const projectsStore = useProjectsStore()
const usersStore = useUsersStore()
const authStore = useAuthStore()

// Data
const searchQuery = ref('')
const showMyTasks = ref(false)
const selectedProject = ref<string | null>(null)
const selectedStatus = ref<TaskStatus | null>(null)
const selectedPriority = ref<TaskPriority | null>(null)
const selectedAssignee = ref<string | null>(null)
const selectedQuickFilter = ref<string | null>(null)

// Computed
const projectOptions = computed(() => {
  return projectsStore.projects.filter(p => p.status === 'active')
})

const userOptions = computed(() => {
  return usersStore.users.map(user => ({
    id: user.id,
    display: getDisplayName(user),
    ...user
  }))
})

const statusOptions = [
  { title: 'Pending', value: 'pending' },
  { title: 'In Progress', value: 'in_progress' },
  { title: 'Completed', value: 'completed' },
  { title: 'Blocked', value: 'blocked' },
  { title: 'Cancelled', value: 'cancelled' }
]

const priorityOptions = [
  { title: 'Low', value: 'low' },
  { title: 'Medium', value: 'medium' },
  { title: 'High', value: 'high' },
  { title: 'Urgent', value: 'urgent' }
]

const hasActiveFilters = computed(() => {
  return !!(
    searchQuery.value ||
    showMyTasks.value ||
    selectedProject.value ||
    selectedStatus.value ||
    selectedPriority.value ||
    selectedAssignee.value ||
    selectedQuickFilter.value
  )
})

const activeFilterCount = computed(() => {
  let count = 0
  if (searchQuery.value) count++
  if (showMyTasks.value) count++
  if (selectedProject.value) count++
  if (selectedStatus.value) count++
  if (selectedPriority.value) count++
  if (selectedAssignee.value) count++
  if (selectedQuickFilter.value) count++
  return count
})

// Methods
function getPriorityColor(priority: string): string {
  const colors: Record<string, string> = {
    low: 'success',
    medium: 'warning',
    high: 'error',
    urgent: 'purple'
  }
  return colors[priority] || 'grey'
}

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

function getAvatarColor(userId: string): string {
  const colors = ['primary', 'secondary', 'success', 'warning', 'error', 'info']
  const index = userId.charCodeAt(0) % colors.length
  return colors[index]
}

function handleSearch() {
  tasksStore.setSearchQuery(searchQuery.value)
}

function handleMyTasksToggle() {
  if (showMyTasks.value) {
    // Set current user ID for filtering
    tasksStore.setCurrentUserId(authStore.user?.id || '')
  }
  tasksStore.toggleMyTasksOnly()
}

function handleProjectFilter() {
  tasksStore.setProjectFilter(selectedProject.value)
}

function handleStatusFilter() {
  tasksStore.setStatusFilter(selectedStatus.value)
}

function handlePriorityFilter() {
  tasksStore.setPriorityFilter(selectedPriority.value)
}

function handleAssigneeFilter() {
  tasksStore.setAssigneeFilter(selectedAssignee.value)
}

function handleQuickFilter() {
  // Reset other filters when using quick filter
  switch (selectedQuickFilter.value) {
    case 'overdue':
      // Show overdue tasks
      tasksStore.clearFilters()
      // This would need a custom filter in the store
      break
    case 'unassigned':
      // Show unassigned tasks
      tasksStore.clearFilters()
      tasksStore.setAssigneeFilter('unassigned')
      break
    case 'urgent':
      // Show urgent priority tasks
      tasksStore.clearFilters()
      tasksStore.setPriorityFilter('urgent' as TaskPriority)
      break
    case 'completed':
      // Show completed tasks
      tasksStore.clearFilters()
      tasksStore.setStatusFilter('completed' as TaskStatus)
      break
  }
}

function clearFilters() {
  searchQuery.value = ''
  showMyTasks.value = false
  selectedProject.value = null
  selectedStatus.value = null
  selectedPriority.value = null
  selectedAssignee.value = null
  selectedQuickFilter.value = null
  tasksStore.clearFilters()
}

// Lifecycle
onMounted(async () => {
  // Fetch data for filters
  await projectsStore.fetchProjects()
  await usersStore.fetchUsers(1, 100)

  // Set current user ID
  if (authStore.user) {
    tasksStore.setCurrentUserId(authStore.user.id)
  }
})
</script>