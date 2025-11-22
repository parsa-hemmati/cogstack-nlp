<template>
  <v-card
    :class="['task-card', { 'elevation-8': isDragging }]"
    :draggable="draggable"
    @dragstart="handleDragStart"
    @dragend="handleDragEnd"
    @click="$emit('click', task)"
  >
    <!-- Priority Indicator -->
    <div
      :class="['priority-indicator', `priority-${task.priority}`]"
    />

    <v-card-text class="pb-2">
      <!-- Title -->
      <h4 class="text-subtitle-2 font-weight-medium mb-1">
        {{ task.title }}
      </h4>

      <!-- Description (truncated) -->
      <p v-if="task.description" class="text-caption text-grey mb-2">
        {{ truncateText(task.description, 60) }}
      </p>

      <!-- Tags -->
      <div v-if="task.tags && task.tags.length > 0" class="mb-2">
        <v-chip
          v-for="tag in task.tags.slice(0, 2)"
          :key="tag"
          size="x-small"
          variant="tonal"
          class="mr-1"
        >
          {{ tag }}
        </v-chip>
        <span v-if="task.tags.length > 2" class="text-caption text-grey">
          +{{ task.tags.length - 2 }}
        </span>
      </div>

      <!-- Meta Info -->
      <div class="d-flex align-center justify-space-between">
        <!-- Assignee -->
        <div class="d-flex align-center">
          <v-avatar
            v-if="task.assignee"
            size="24"
            :color="getAvatarColor(task.assigneeId)"
            class="mr-2"
          >
            <span class="text-caption">
              {{ getInitials(task.assignee) }}
            </span>
          </v-avatar>
          <v-icon
            v-else
            size="small"
            color="grey"
            class="mr-2"
          >
            mdi-account-off
          </v-icon>
        </div>

        <!-- Due Date -->
        <div v-if="task.dueDate" class="text-caption">
          <v-icon
            size="x-small"
            :color="getDueDateColor()"
            class="mr-1"
          >
            mdi-calendar-clock
          </v-icon>
          <span :class="getDueDateClass()">
            {{ formatDueDate(task.dueDate) }}
          </span>
        </div>
      </div>

      <!-- Comments and Attachments -->
      <div class="d-flex align-center mt-2">
        <div v-if="task.comments && task.comments.length > 0" class="mr-3">
          <v-icon size="x-small" color="grey" class="mr-1">
            mdi-comment
          </v-icon>
          <span class="text-caption text-grey">
            {{ task.comments.length }}
          </span>
        </div>
        <div v-if="task.attachments && task.attachments.length > 0">
          <v-icon size="x-small" color="grey" class="mr-1">
            mdi-paperclip
          </v-icon>
          <span class="text-caption text-grey">
            {{ task.attachments.length }}
          </span>
        </div>
      </div>
    </v-card-text>

    <!-- Quick Actions -->
    <v-card-actions v-if="showActions" class="pt-0">
      <v-btn
        icon="mdi-pencil"
        size="x-small"
        variant="text"
        @click.stop="$emit('edit', task)"
      />
      <v-btn
        icon="mdi-comment-plus"
        size="x-small"
        variant="text"
        @click.stop="$emit('comment', task)"
      />
      <v-spacer />
      <v-btn
        icon="mdi-delete"
        size="x-small"
        variant="text"
        color="error"
        @click.stop="$emit('delete', task)"
      />
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Task, User } from '@/types'

// Props
const props = withDefaults(defineProps<{
  task: Task
  draggable?: boolean
  showActions?: boolean
}>(), {
  draggable: true,
  showActions: false
})

// Emits
const emit = defineEmits<{
  click: [task: Task]
  edit: [task: Task]
  comment: [task: Task]
  delete: [task: Task]
  dragStart: [task: Task]
  dragEnd: [task: Task]
}>()

// Data
const isDragging = ref(false)

// Methods
function handleDragStart(event: DragEvent) {
  isDragging.value = true
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('task', JSON.stringify(props.task))
  }
  emit('dragStart', props.task)
}

function handleDragEnd() {
  isDragging.value = false
  emit('dragEnd', props.task)
}

function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

function getInitials(user: User): string {
  if (user.firstName && user.lastName) {
    return `${user.firstName[0]}${user.lastName[0]}`.toUpperCase()
  }
  return user.username.substring(0, 2).toUpperCase()
}

function getAvatarColor(userId?: string): string {
  if (!userId) return 'grey'
  const colors = ['primary', 'secondary', 'success', 'warning', 'error', 'info']
  const index = userId.charCodeAt(0) % colors.length
  return colors[index]
}

function formatDueDate(date: string): string {
  const dueDate = new Date(date)
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)

  // Reset time for date comparison
  const dueDateOnly = new Date(dueDate.toDateString())
  const todayOnly = new Date(today.toDateString())
  const tomorrowOnly = new Date(tomorrow.toDateString())

  if (dueDateOnly.getTime() === todayOnly.getTime()) {
    return 'Today'
  } else if (dueDateOnly.getTime() === tomorrowOnly.getTime()) {
    return 'Tomorrow'
  } else if (dueDateOnly < todayOnly) {
    const daysOverdue = Math.floor((todayOnly.getTime() - dueDateOnly.getTime()) / (1000 * 60 * 60 * 24))
    return `${daysOverdue}d overdue`
  } else {
    return dueDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }
}

function getDueDateColor(): string {
  if (!props.task.dueDate) return 'grey'

  const dueDate = new Date(props.task.dueDate)
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)

  if (dueDate < today) {
    return 'error'
  } else if (dueDate <= tomorrow) {
    return 'warning'
  }
  return 'grey'
}

function getDueDateClass(): string {
  const color = getDueDateColor()
  if (color === 'error') return 'text-error'
  if (color === 'warning') return 'text-warning'
  return 'text-grey'
}
</script>

<style scoped>
.task-card {
  cursor: move;
  position: relative;
  transition: all 0.2s;
}

.task-card:hover {
  transform: translateY(-2px);
}

.priority-indicator {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  border-radius: 4px 4px 0 0;
}

.priority-low {
  background-color: #4CAF50;
}

.priority-medium {
  background-color: #FF9800;
}

.priority-high {
  background-color: #F44336;
}

.priority-urgent {
  background-color: #9C27B0;
}
</style>