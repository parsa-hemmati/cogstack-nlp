<template>
  <v-container fluid class="task-board">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center mb-4">
          <div>
            <h1 class="text-h4 font-weight-bold mb-1">Task Board</h1>
            <p class="text-body-1 text-grey">Manage and track your tasks</p>
          </div>
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            variant="elevated"
            @click="openCreateDialog"
          >
            New Task
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Stats Row -->
    <v-row class="mb-4">
      <v-col v-for="stat in stats" :key="stat.title" cols="12" sm="6" md="2">
        <v-card>
          <v-card-text class="pa-3">
            <div class="d-flex align-center justify-space-between">
              <div>
                <p class="text-caption text-grey mb-1">{{ stat.title }}</p>
                <h4 class="text-h5 font-weight-bold">{{ stat.value }}</h4>
              </div>
              <v-icon :color="stat.color" size="30">{{ stat.icon }}</v-icon>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Main Content -->
    <v-row>
      <!-- Filters Sidebar -->
      <v-col cols="12" md="3" lg="2">
        <TaskFilters />
      </v-col>

      <!-- Kanban Board -->
      <v-col cols="12" md="9" lg="10">
        <div class="kanban-board">
          <v-row>
            <v-col
              v-for="column in columns"
              :key="column.status"
              cols="12"
              sm="6"
              md="3"
              class="kanban-column"
            >
              <v-card
                class="column-card"
                :class="{ 'drag-over': dragOverColumn === column.status }"
                @dragover.prevent="handleDragOver(column.status)"
                @dragleave="handleDragLeave"
                @drop="handleDrop($event, column.status)"
              >
                <v-card-title class="column-header">
                  <v-icon :color="column.color" class="mr-2">{{ column.icon }}</v-icon>
                  <span>{{ column.title }}</span>
                  <v-chip size="small" variant="tonal" class="ml-2">
                    {{ getTasksForStatus(column.status).length }}
                  </v-chip>
                </v-card-title>

                <v-divider />

                <v-card-text class="column-content">
                  <v-container v-if="tasksStore.isLoading" class="pa-0">
                    <v-skeleton-loader
                      v-for="i in 3"
                      :key="`skeleton-${column.status}-${i}`"
                      type="card"
                      class="mb-2"
                    />
                  </v-container>

                  <draggable
                    v-else
                    v-model="getTasksForStatus(column.status)"
                    :group="{ name: 'tasks' }"
                    item-key="id"
                    class="task-list"
                    :animation="200"
                    @change="handleDragChange"
                  >
                    <template #item="{ element }">
                      <div class="mb-2">
                        <TaskCard
                          :task="element"
                          @click="openTaskDialog"
                          @edit="openEditDialog"
                          @comment="openCommentDialog"
                          @delete="openDeleteDialog"
                        />
                      </div>
                    </template>
                  </draggable>

                  <!-- Empty State -->
                  <div
                    v-if="!tasksStore.isLoading && getTasksForStatus(column.status).length === 0"
                    class="text-center py-4"
                  >
                    <v-icon size="48" color="grey-lighten-2">mdi-clipboard-text-outline</v-icon>
                    <p class="text-caption text-grey mt-2">No tasks</p>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </div>
      </v-col>
    </v-row>

    <!-- Create/Edit Task Dialog -->
    <v-dialog v-model="formDialog" max-width="800px" persistent>
      <TaskForm
        :task="selectedTask"
        :is-edit="isEditMode"
        @submit="handleFormSubmit"
        @cancel="closeFormDialog"
      />
    </v-dialog>

    <!-- Task Details Dialog -->
    <v-dialog v-model="taskDialog" max-width="800px">
      <v-card v-if="selectedTask">
        <v-card-title>
          <v-icon class="mr-2">mdi-clipboard-text</v-icon>
          Task Details
        </v-card-title>
        <v-card-text>
          <h3 class="text-h6 mb-2">{{ selectedTask.title }}</h3>
          <p v-if="selectedTask.description" class="text-body-2 mb-4">
            {{ selectedTask.description }}
          </p>

          <v-row>
            <v-col cols="12" sm="6">
              <div class="mb-3">
                <label class="text-caption text-grey">Status</label>
                <div>
                  <v-chip :color="getStatusColor(selectedTask.status)">
                    {{ selectedTask.status }}
                  </v-chip>
                </div>
              </div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="mb-3">
                <label class="text-caption text-grey">Priority</label>
                <div>
                  <v-chip :color="getPriorityColor(selectedTask.priority)">
                    {{ selectedTask.priority }}
                  </v-chip>
                </div>
              </div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="mb-3">
                <label class="text-caption text-grey">Assignee</label>
                <div v-if="selectedTask.assignee">
                  <v-chip>
                    <v-avatar start :color="getAvatarColor(selectedTask.assigneeId)">
                      <span class="text-caption">{{ getInitials(selectedTask.assignee) }}</span>
                    </v-avatar>
                    {{ getDisplayName(selectedTask.assignee) }}
                  </v-chip>
                </div>
                <div v-else class="text-grey">Unassigned</div>
              </div>
            </v-col>
            <v-col cols="12" sm="6">
              <div class="mb-3">
                <label class="text-caption text-grey">Due Date</label>
                <div v-if="selectedTask.dueDate">
                  {{ formatDate(selectedTask.dueDate) }}
                </div>
                <div v-else class="text-grey">No due date</div>
              </div>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-btn
            variant="text"
            prepend-icon="mdi-pencil"
            @click="editFromDetails"
          >
            Edit
          </v-btn>
          <v-spacer />
          <v-btn variant="text" @click="closeTaskDialog">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="500px">
      <v-card>
        <v-card-title>
          <v-icon color="error" class="mr-2">mdi-alert</v-icon>
          Delete Task
        </v-card-title>
        <v-card-text>
          Are you sure you want to delete task <strong>{{ selectedTask?.title }}</strong>?
          This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeDeleteDialog">Cancel</v-btn>
          <v-btn
            color="error"
            variant="elevated"
            @click="confirmDelete"
            :loading="isDeleting"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar
      v-model="snackbar"
      :color="snackbarColor"
      :timeout="3000"
      location="top"
    >
      {{ snackbarMessage }}
      <template #actions>
        <v-btn variant="text" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import draggable from 'vuedraggable'
import { useTasksStore } from '@/stores/tasks'
import { useAuthStore } from '@/stores/auth'
import TaskCard from '@/components/tasks/TaskCard.vue'
import TaskForm from '@/components/tasks/TaskForm.vue'
import TaskFilters from '@/components/tasks/TaskFilters.vue'
import type { Task, TaskStatus, User } from '@/types'

// Stores
const tasksStore = useTasksStore()
const authStore = useAuthStore()

// Refs
const formDialog = ref(false)
const taskDialog = ref(false)
const deleteDialog = ref(false)
const selectedTask = ref<Task | null>(null)
const isEditMode = ref(false)
const isDeleting = ref(false)
const dragOverColumn = ref<string | null>(null)

// Snackbar
const snackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

// Kanban columns configuration
const columns = [
  {
    status: 'pending',
    title: 'Pending',
    icon: 'mdi-clock-outline',
    color: 'grey'
  },
  {
    status: 'in_progress',
    title: 'In Progress',
    icon: 'mdi-progress-clock',
    color: 'blue'
  },
  {
    status: 'completed',
    title: 'Completed',
    icon: 'mdi-check-circle',
    color: 'success'
  },
  {
    status: 'blocked',
    title: 'Blocked',
    icon: 'mdi-alert-octagon',
    color: 'error'
  }
]

// Computed
const stats = computed(() => {
  const taskStats = tasksStore.taskStats
  return [
    {
      title: 'Total',
      value: taskStats.total,
      icon: 'mdi-sigma',
      color: 'primary'
    },
    {
      title: 'Pending',
      value: taskStats.pending,
      icon: 'mdi-clock-outline',
      color: 'grey'
    },
    {
      title: 'In Progress',
      value: taskStats.inProgress,
      icon: 'mdi-progress-clock',
      color: 'blue'
    },
    {
      title: 'Completed',
      value: taskStats.completed,
      icon: 'mdi-check-circle',
      color: 'success'
    },
    {
      title: 'Overdue',
      value: taskStats.overdue,
      icon: 'mdi-alert',
      color: 'error'
    },
    {
      title: 'Urgent',
      value: taskStats.urgent,
      icon: 'mdi-flag',
      color: 'purple'
    }
  ]
})

// Methods
function getTasksForStatus(status: string) {
  return tasksStore.tasksByStatus[status as TaskStatus] || []
}

function handleDragOver(status: string) {
  dragOverColumn.value = status
}

function handleDragLeave() {
  dragOverColumn.value = null
}

function handleDrop(event: DragEvent, newStatus: string) {
  event.preventDefault()
  dragOverColumn.value = null

  const taskData = event.dataTransfer?.getData('task')
  if (taskData) {
    const task = JSON.parse(taskData)
    tasksStore.moveTask(task.id, newStatus as TaskStatus)
  }
}

function handleDragChange(evt: any) {
  if (evt.added) {
    // Task was moved to this column
    const task = evt.added.element
    const newStatus = columns.find(col =>
      getTasksForStatus(col.status).includes(task)
    )?.status

    if (newStatus && newStatus !== task.status) {
      tasksStore.updateTaskStatus(task.id, newStatus as TaskStatus)
    }
  }
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'grey',
    in_progress: 'blue',
    completed: 'success',
    blocked: 'error',
    cancelled: 'warning'
  }
  return colors[status] || 'default'
}

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

function getAvatarColor(userId?: string): string {
  if (!userId) return 'grey'
  const colors = ['primary', 'secondary', 'success', 'warning', 'error', 'info']
  const index = userId.charCodeAt(0) % colors.length
  return colors[index]
}

function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function openCreateDialog() {
  selectedTask.value = null
  isEditMode.value = false
  formDialog.value = true
}

function openEditDialog(task: Task) {
  selectedTask.value = task
  isEditMode.value = true
  formDialog.value = true
}

function openTaskDialog(task: Task) {
  selectedTask.value = task
  taskDialog.value = true
}

function openCommentDialog(task: Task) {
  // To be implemented - open comment dialog
  showSnackbar('Comment feature coming soon', 'info')
}

function openDeleteDialog(task: Task) {
  selectedTask.value = task
  deleteDialog.value = true
}

function closeFormDialog() {
  formDialog.value = false
  selectedTask.value = null
}

function closeTaskDialog() {
  taskDialog.value = false
  selectedTask.value = null
}

function closeDeleteDialog() {
  deleteDialog.value = false
  selectedTask.value = null
}

function editFromDetails() {
  taskDialog.value = false
  if (selectedTask.value) {
    openEditDialog(selectedTask.value)
  }
}

async function handleFormSubmit(task: Task) {
  closeFormDialog()
  showSnackbar(
    `Task ${isEditMode.value ? 'updated' : 'created'} successfully`,
    'success'
  )
  await tasksStore.fetchTasks()
}

async function confirmDelete() {
  if (!selectedTask.value) return

  isDeleting.value = true
  try {
    await tasksStore.deleteTask(selectedTask.value.id)
    showSnackbar('Task deleted successfully', 'success')
    closeDeleteDialog()
  } catch (error) {
    showSnackbar('Failed to delete task', 'error')
  } finally {
    isDeleting.value = false
  }
}

function showSnackbar(message: string, color: string) {
  snackbarMessage.value = message
  snackbarColor.value = color
  snackbar.value = true
}

// Lifecycle
onMounted(async () => {
  // Set current user ID for filtering
  if (authStore.user) {
    tasksStore.setCurrentUserId(authStore.user.id)
  }

  // Fetch tasks
  await tasksStore.fetchTasks()
})
</script>

<style scoped>
.task-board {
  height: calc(100vh - 64px);
  overflow-y: auto;
}

.kanban-board {
  min-height: 600px;
}

.kanban-column {
  height: 100%;
}

.column-card {
  height: 100%;
  min-height: 600px;
  display: flex;
  flex-direction: column;
}

.column-header {
  background-color: rgba(0, 0, 0, 0.03);
  font-weight: 600;
}

.column-content {
  flex: 1;
  overflow-y: auto;
  max-height: calc(100vh - 350px);
}

.task-list {
  min-height: 100px;
}

.drag-over {
  background-color: rgba(var(--v-theme-primary), 0.05);
  border: 2px dashed rgb(var(--v-theme-primary));
}
</style>