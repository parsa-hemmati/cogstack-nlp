<template>
  <v-card
    :class="{ 'elevation-8': isHovered }"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
  >
    <!-- Project Status Badge -->
    <v-chip
      :color="statusColor"
      size="small"
      class="position-absolute"
      style="top: 12px; right: 12px; z-index: 1"
    >
      {{ project.status }}
    </v-chip>

    <v-card-title>
      <v-icon color="primary" class="mr-2">mdi-folder</v-icon>
      {{ project.name }}
    </v-card-title>

    <v-card-subtitle v-if="project.description">
      {{ truncateText(project.description, 100) }}
    </v-card-subtitle>

    <v-card-text>
      <!-- Tags -->
      <div v-if="project.tags && project.tags.length > 0" class="mb-3">
        <v-chip
          v-for="tag in project.tags.slice(0, 3)"
          :key="tag"
          size="x-small"
          color="primary"
          variant="tonal"
          class="mr-1"
        >
          {{ tag }}
        </v-chip>
        <v-chip
          v-if="project.tags.length > 3"
          size="x-small"
          variant="text"
        >
          +{{ project.tags.length - 3 }}
        </v-chip>
      </div>

      <!-- Project Info -->
      <div class="text-caption text-grey mb-2">
        <v-icon size="x-small" class="mr-1">mdi-calendar</v-icon>
        {{ formatDateRange(project.startDate, project.endDate) }}
      </div>

      <!-- Members -->
      <div class="d-flex align-center mb-3">
        <v-avatar-group max="4" density="compact">
          <v-avatar
            v-for="member in project.members"
            :key="member.userId"
            size="28"
            :color="getAvatarColor(member.userId)"
          >
            <span class="text-caption">
              {{ getInitials(member.user) }}
            </span>
          </v-avatar>
        </v-avatar-group>
        <span class="text-caption text-grey ml-2">
          {{ project.members.length }} {{ project.members.length === 1 ? 'member' : 'members' }}
        </span>
      </div>

      <!-- Stats -->
      <v-row v-if="stats" dense>
        <v-col cols="6">
          <div class="text-center">
            <div class="text-h6 font-weight-bold">{{ stats.totalTasks }}</div>
            <div class="text-caption text-grey">Tasks</div>
          </div>
        </v-col>
        <v-col cols="6">
          <div class="text-center">
            <div class="text-h6 font-weight-bold">
              {{ Math.round(stats.completionRate * 100) }}%
            </div>
            <div class="text-caption text-grey">Complete</div>
          </div>
        </v-col>
      </v-row>

      <!-- Loading skeleton for stats -->
      <v-skeleton-loader
        v-else
        type="list-item-two-line"
        class="mt-2"
      />
    </v-card-text>

    <v-divider />

    <v-card-actions>
      <v-btn
        variant="text"
        size="small"
        prepend-icon="mdi-eye"
        @click="$emit('view', project)"
      >
        View
      </v-btn>
      <v-spacer />
      <v-btn
        icon="mdi-pencil"
        variant="text"
        size="small"
        @click="$emit('edit', project)"
        aria-label="Edit project"
      />
      <v-btn
        icon="mdi-account-plus"
        variant="text"
        size="small"
        @click="$emit('manage-members', project)"
        aria-label="Manage members"
      />
      <v-btn
        icon="mdi-delete"
        variant="text"
        size="small"
        color="error"
        @click="$emit('delete', project)"
        aria-label="Delete project"
      />
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProjectsStore } from '@/stores/projects'
import type { Project, User } from '@/types'

// Props
const props = defineProps<{
  project: Project
}>()

// Emits
defineEmits<{
  view: [project: Project]
  edit: [project: Project]
  'manage-members': [project: Project]
  delete: [project: Project]
}>()

// Stores
const projectsStore = useProjectsStore()

// Data
const isHovered = ref(false)
const stats = ref<{
  totalTasks: number
  completedTasks: number
  completionRate: number
} | null>(null)

// Computed
const statusColor = computed(() => {
  const colors: Record<string, string> = {
    active: 'success',
    draft: 'warning',
    archived: 'grey'
  }
  return colors[props.project.status] || 'default'
})

// Methods
function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

function formatDateRange(start?: string, end?: string): string {
  if (!start && !end) return 'No timeline set'

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  if (start && !end) return `Started ${formatDate(start)}`
  if (!start && end) return `Due ${formatDate(end)}`
  return `${formatDate(start)} - ${formatDate(end)}`
}

function getInitials(user?: User): string {
  if (!user) return '?'
  if (user.firstName && user.lastName) {
    return `${user.firstName[0]}${user.lastName[0]}`.toUpperCase()
  }
  return user.username.substring(0, 2).toUpperCase()
}

function getAvatarColor(userId: string): string {
  // Generate a consistent color based on user ID
  const colors = ['primary', 'secondary', 'success', 'warning', 'error', 'info']
  const index = userId.charCodeAt(0) % colors.length
  return colors[index]
}

// Lifecycle
onMounted(async () => {
  // Fetch project stats
  try {
    const projectStats = await projectsStore.getProjectStats(props.project.id)
    if (projectStats) {
      stats.value = {
        totalTasks: projectStats.totalTasks,
        completedTasks: projectStats.completedTasks,
        completionRate: projectStats.completionRate
      }
    }
  } catch (error) {
  }
})
</script>

<style scoped>
.position-absolute {
  position: absolute;
}
</style>