<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon left>mdi-clipboard-list</v-icon>
            Task Management
            <v-spacer></v-spacer>
            <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
              Create Task
            </v-btn>
          </v-card-title>

          <v-card-text>
            <!-- Project Selector -->
            <v-select
              v-model="selectedProjectId"
              :items="projectOptions"
              label="Select Project"
              prepend-icon="mdi-folder"
              @update:model-value="onProjectChange"
              class="mb-4"
            ></v-select>

            <!-- Filters -->
            <v-row class="mb-4">
              <v-col cols="12" md="3">
                <v-select
                  v-model="localStatusFilter"
                  :items="statusOptions"
                  label="Filter by Status"
                  clearable
                  prepend-icon="mdi-filter"
                  @update:model-value="taskStore.setStatusFilter($event)"
                ></v-select>
              </v-col>

              <v-col cols="12" md="3">
                <v-select
                  v-model="localPriorityFilter"
                  :items="priorityOptions"
                  label="Filter by Priority"
                  clearable
                  prepend-icon="mdi-filter"
                  @update:model-value="taskStore.setPriorityFilter($event)"
                ></v-select>
              </v-col>

              <v-col cols="12" md="3">
                <v-text-field
                  v-model="localAssignedToFilter"
                  label="Filter by Assigned To (User ID)"
                  clearable
                  prepend-icon="mdi-account"
                  @update:model-value="taskStore.setAssignedToFilter($event)"
                ></v-text-field>
              </v-col>

              <v-col cols="12" md="3" class="d-flex align-center">
                <v-btn @click="clearAllFilters" prepend-icon="mdi-filter-remove" variant="outlined">
                  Clear Filters
                </v-btn>
              </v-col>
            </v-row>

            <!-- Loading State -->
            <v-progress-linear
              v-if="taskStore.loading"
              indeterminate
              color="primary"
            ></v-progress-linear>

            <!-- Error Alert -->
            <v-alert
              v-if="taskStore.error"
              type="error"
              closable
              @click:close="taskStore.clearError()"
              class="mb-4"
            >
              {{ taskStore.error }}
            </v-alert>

            <!-- Tasks Data Table -->
            <v-data-table
              :headers="headers"
              :items="taskStore.filteredTasks"
              :loading="taskStore.loading"
              :items-per-page="15"
              class="elevation-1"
            >
              <!-- Title with overdue indicator -->
              <template v-slot:item.title="{ item }">
                <div class="d-flex align-center">
                  <v-icon
                    v-if="isOverdue(item)"
                    color="error"
                    size="small"
                    class="mr-2"
                  >
                    mdi-alert-circle
                  </v-icon>
                  {{ item.title }}
                </div>
              </template>

              <!-- Status Chip -->
              <template v-slot:item.status="{ item }">
                <v-chip :color="getStatusColor(item.status)" size="small">
                  {{ formatStatus(item.status) }}
                </v-chip>
              </template>

              <!-- Priority Chip -->
              <template v-slot:item.priority="{ item }">
                <v-chip :color="getPriorityColor(item.priority)" size="small">
                  {{ item.priority }}
                </v-chip>
              </template>

              <!-- Due Date with overdue highlighting -->
              <template v-slot:item.due_date="{ item }">
                <span :class="{ 'text-error font-weight-bold': isOverdue(item) }">
                  {{ formatDueDate(item.due_date) }}
                </span>
              </template>

              <!-- Actions -->
              <template v-slot:item.actions="{ item }">
                <v-btn icon size="small" @click="openEditDialog(item)" class="mr-2">
                  <v-icon>mdi-pencil</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create/Edit Task Dialog -->
    <v-dialog v-model="taskDialog" max-width="700px" persistent>
      <v-card>
        <v-card-title>
          <span class="text-h5">{{ editingTask ? 'Edit Task' : 'Create Task' }}</span>
        </v-card-title>

        <v-card-text>
          <v-form ref="taskForm" v-model="taskFormValid">
            <!-- Title -->
            <v-text-field
              v-model="taskFormData.title"
              label="Title"
              :rules="[rules.required]"
              required
              prepend-icon="mdi-text"
            ></v-text-field>

            <!-- Description -->
            <v-textarea
              v-model="taskFormData.description"
              label="Description"
              rows="3"
              prepend-icon="mdi-text-box"
            ></v-textarea>

            <!-- Status -->
            <v-select
              v-model="taskFormData.status"
              :items="statusOptions"
              label="Status"
              prepend-icon="mdi-progress-check"
            ></v-select>

            <!-- Priority -->
            <v-select
              v-model="taskFormData.priority"
              :items="priorityOptions"
              label="Priority"
              prepend-icon="mdi-flag"
            ></v-select>

            <!-- Assigned To -->
            <v-text-field
              v-model="taskFormData.assigned_to"
              label="Assigned To (User ID)"
              prepend-icon="mdi-account"
              hint="Leave empty for unassigned"
            ></v-text-field>

            <!-- Due Date -->
            <v-text-field
              v-model="taskFormData.due_date"
              label="Due Date (YYYY-MM-DD)"
              type="date"
              prepend-icon="mdi-calendar"
            ></v-text-field>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="closeTaskDialog">Cancel</v-btn>
          <v-btn
            color="primary"
            :disabled="!taskFormValid || taskStore.loading || !selectedProjectId"
            :loading="taskStore.loading"
            @click="saveTask"
          >
            {{ editingTask ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Success Snackbar -->
    <v-snackbar v-model="snackbar" :color="snackbarColor" :timeout="3000">
      {{ snackbarMessage }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTaskStore } from '../stores/task'
import { useProjectStore } from '../stores/project'
import type { Task, TaskCreate, TaskUpdate } from '../services/tasks'

const taskStore = useTaskStore()
const projectStore = useProjectStore()

// Project selection
const selectedProjectId = ref<string | null>(null)
const projectOptions = ref<Array<{ title: string; value: string }>>([])

// Data table headers
const headers = [
  { title: 'Title', key: 'title', align: 'start' as const },
  { title: 'Status', key: 'status', align: 'center' as const },
  { title: 'Priority', key: 'priority', align: 'center' as const },
  { title: 'Due Date', key: 'due_date', align: 'center' as const },
  { title: 'Actions', key: 'actions', align: 'center' as const, sortable: false },
]

// Filter state
const localStatusFilter = ref<string | null>(null)
const localPriorityFilter = ref<string | null>(null)
const localAssignedToFilter = ref<string | null>(null)

// Status and priority options
const statusOptions = [
  { title: 'Pending', value: 'pending' },
  { title: 'In Progress', value: 'in_progress' },
  { title: 'Completed', value: 'completed' },
  { title: 'Blocked', value: 'blocked' },
]

const priorityOptions = [
  { title: 'Low', value: 'low' },
  { title: 'Medium', value: 'medium' },
  { title: 'High', value: 'high' },
  { title: 'Urgent', value: 'urgent' },
]

// Task dialog state
const taskDialog = ref(false)
const taskFormValid = ref(false)
const editingTask = ref<Task | null>(null)

// Task form data
const taskFormData = ref<Partial<TaskCreate & TaskUpdate>>({
  title: '',
  description: '',
  status: 'pending',
  priority: 'medium',
  assigned_to: '',
  due_date: '',
})

// Form validation rules
const rules = {
  required: (value: string) => !!value || 'Required',
}

// Snackbar state
const snackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

/**
 * Format status for display
 */
function formatStatus(status: string): string {
  return status.replace('_', ' ').toUpperCase()
}

/**
 * Get color for status chip
 */
function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'grey',
    in_progress: 'primary',
    completed: 'success',
    blocked: 'error',
  }
  return colors[status] || 'grey'
}

/**
 * Get color for priority chip
 */
function getPriorityColor(priority: string): string {
  const colors: Record<string, string> = {
    low: 'info',
    medium: 'primary',
    high: 'warning',
    urgent: 'error',
  }
  return colors[priority] || 'grey'
}

/**
 * Format due date
 */
function formatDueDate(dueDate: string | null): string {
  if (!dueDate) return 'No due date'
  return new Date(dueDate).toLocaleDateString()
}

/**
 * Check if task is overdue
 */
function isOverdue(task: Task): boolean {
  if (!task.due_date || task.status === 'completed') return false
  return new Date(task.due_date) < new Date()
}

/**
 * Handle project change
 */
async function onProjectChange() {
  if (!selectedProjectId.value) return

  try {
    await taskStore.fetchTasks(selectedProjectId.value)
  } catch (error) {
    snackbarMessage.value = 'Failed to load tasks'
    snackbarColor.value = 'error'
    snackbar.value = true
  }
}

/**
 * Clear all filters
 */
function clearAllFilters() {
  localStatusFilter.value = null
  localPriorityFilter.value = null
  localAssignedToFilter.value = null
  taskStore.clearFilters()
}

/**
 * Open create task dialog
 */
function openCreateDialog() {
  if (!selectedProjectId.value) {
    snackbarMessage.value = 'Please select a project first'
    snackbarColor.value = 'warning'
    snackbar.value = true
    return
  }

  editingTask.value = null
  taskFormData.value = {
    title: '',
    description: '',
    status: 'pending',
    priority: 'medium',
    assigned_to: '',
    due_date: '',
  }
  taskDialog.value = true
}

/**
 * Open edit task dialog
 */
function openEditDialog(task: Task) {
  editingTask.value = task
  taskFormData.value = {
    title: task.title,
    description: task.description,
    status: task.status,
    priority: task.priority,
    assigned_to: task.assigned_to || '',
    due_date: task.due_date ? task.due_date.split('T')[0] : '',
  }
  taskDialog.value = true
}

/**
 * Close task dialog
 */
function closeTaskDialog() {
  taskDialog.value = false
  editingTask.value = null
  taskFormData.value = {}
}

/**
 * Save task (create or update)
 */
async function saveTask() {
  if (!selectedProjectId.value) return

  try {
    // Prepare data (remove empty strings)
    const data: any = { ...taskFormData.value }
    if (!data.assigned_to) data.assigned_to = null
    if (!data.description) data.description = null
    if (!data.due_date) data.due_date = null

    if (editingTask.value) {
      // Update existing task
      const updateData: TaskUpdate = {
        title: data.title,
        description: data.description,
        status: data.status,
        priority: data.priority,
        assigned_to: data.assigned_to,
        due_date: data.due_date,
      }
      await taskStore.updateTask(editingTask.value.id, updateData)
      snackbarMessage.value = 'Task updated successfully'
    } else {
      // Create new task
      const createData: TaskCreate = {
        title: data.title,
        description: data.description,
        status: data.status,
        priority: data.priority,
        assigned_to: data.assigned_to,
        due_date: data.due_date,
      }
      await taskStore.createTask(selectedProjectId.value, createData)
      snackbarMessage.value = 'Task created successfully'
    }

    snackbarColor.value = 'success'
    snackbar.value = true
    closeTaskDialog()
  } catch (error) {
    snackbarMessage.value = 'Operation failed. Please try again.'
    snackbarColor.value = 'error'
    snackbar.value = true
  }
}

/**
 * Load projects on mount
 */
onMounted(async () => {
  try {
    await projectStore.fetchProjects()
    projectOptions.value = projectStore.projects.map((p) => ({
      title: p.name,
      value: p.id,
    }))

    // Auto-select first project if available
    if (projectOptions.value.length > 0) {
      selectedProjectId.value = projectOptions.value[0].value
      await onProjectChange()
    }
  } catch (error) {
    snackbarMessage.value = 'Failed to load projects'
    snackbarColor.value = 'error'
    snackbar.value = true
  }
})
</script>
