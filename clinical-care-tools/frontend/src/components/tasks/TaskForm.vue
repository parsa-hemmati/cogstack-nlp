<template>
  <v-card>
    <v-card-title>
      {{ isEdit ? 'Edit Task' : 'Create New Task' }}
    </v-card-title>

    <v-card-text>
      <v-form ref="form" v-model="isFormValid" @submit.prevent="handleSubmit">
        <v-container>
          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="formData.title"
                label="Task Title"
                prepend-icon="mdi-format-title"
                :rules="[rules.required, rules.title]"
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <v-col cols="12">
              <v-textarea
                v-model="formData.description"
                label="Description"
                prepend-icon="mdi-text"
                rows="3"
                auto-grow
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-select
                v-model="formData.projectId"
                :items="projects"
                item-title="name"
                item-value="id"
                label="Project"
                prepend-icon="mdi-folder"
                :rules="[rules.required]"
                :disabled="isEdit"
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-select
                v-model="formData.priority"
                :items="priorityOptions"
                label="Priority"
                prepend-icon="mdi-flag"
                variant="outlined"
                density="comfortable"
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
            </v-col>

            <v-col cols="12" md="6">
              <v-autocomplete
                v-model="formData.assigneeId"
                :items="users"
                item-title="display"
                item-value="id"
                label="Assignee"
                prepend-icon="mdi-account"
                clearable
                variant="outlined"
                density="comfortable"
              >
                <template #item="{ props: itemProps, item }">
                  <v-list-item v-bind="itemProps">
                    <template #prepend>
                      <v-avatar size="32" :color="getAvatarColor(item.raw.id)">
                        <span class="text-caption">
                          {{ getInitials(item.raw) }}
                        </span>
                      </v-avatar>
                    </template>
                  </v-list-item>
                </template>
              </v-autocomplete>
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="formData.dueDate"
                label="Due Date"
                prepend-icon="mdi-calendar"
                type="datetime-local"
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model.number="formData.estimatedHours"
                label="Estimated Hours"
                prepend-icon="mdi-clock-outline"
                type="number"
                min="0"
                step="0.5"
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <v-col v-if="isEdit" cols="12" md="6">
              <v-select
                v-model="formData.status"
                :items="statusOptions"
                label="Status"
                prepend-icon="mdi-information"
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <v-col cols="12">
              <v-combobox
                v-model="formData.tags"
                label="Tags"
                prepend-icon="mdi-tag-multiple"
                multiple
                chips
                closable-chips
                hint="Press Enter to add tags"
                persistent-hint
                variant="outlined"
                density="comfortable"
              >
                <template #chip="{ props: chipProps, item }">
                  <v-chip
                    v-bind="chipProps"
                    size="small"
                    color="primary"
                    variant="tonal"
                  >
                    {{ item.title }}
                  </v-chip>
                </template>
              </v-combobox>
            </v-col>
          </v-row>
        </v-container>
      </v-form>
    </v-card-text>

    <v-card-actions>
      <v-spacer />
      <v-btn
        variant="text"
        @click="$emit('cancel')"
        :disabled="isSubmitting"
      >
        Cancel
      </v-btn>
      <v-btn
        color="primary"
        variant="elevated"
        :loading="isSubmitting"
        :disabled="!isFormValid"
        @click="handleSubmit"
      >
        {{ isEdit ? 'Update' : 'Create' }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useTasksStore } from '@/stores/tasks'
import { useProjectsStore } from '@/stores/projects'
import { useUsersStore } from '@/stores/users'
import type { Task, CreateTaskRequest, UpdateTaskRequest, TaskStatus, TaskPriority, User } from '@/types'

// Props
const props = defineProps<{
  task?: Task | null
  isEdit?: boolean
  projectId?: string
}>()

// Emits
const emit = defineEmits<{
  submit: [task: Task]
  cancel: []
}>()

// Stores
const tasksStore = useTasksStore()
const projectsStore = useProjectsStore()
const usersStore = useUsersStore()

// Refs
const form = ref()
const isFormValid = ref(false)
const isSubmitting = ref(false)

// Data
const formData = reactive({
  title: '',
  description: '',
  projectId: props.projectId || '',
  priority: 'medium' as TaskPriority,
  assigneeId: null as string | null,
  dueDate: '',
  estimatedHours: null as number | null,
  tags: [] as string[],
  status: 'pending' as TaskStatus
})

// Computed
const projects = computed(() => {
  return projectsStore.projects.filter(p => p.status === 'active')
})

const users = computed(() => {
  return usersStore.users.map(user => ({
    id: user.id,
    display: `${getDisplayName(user)} (${user.email})`,
    ...user
  }))
})

// Options
const priorityOptions = [
  { title: 'Low', value: 'low' },
  { title: 'Medium', value: 'medium' },
  { title: 'High', value: 'high' },
  { title: 'Urgent', value: 'urgent' }
]

const statusOptions = [
  { title: 'Pending', value: 'pending' },
  { title: 'In Progress', value: 'in_progress' },
  { title: 'Completed', value: 'completed' },
  { title: 'Blocked', value: 'blocked' },
  { title: 'Cancelled', value: 'cancelled' }
]

// Validation rules
const rules = {
  required: (v: any) => !!v || 'This field is required',
  title: (v: string) => {
    if (v.length < 3) return 'Title must be at least 3 characters'
    if (v.length > 200) return 'Title must be less than 200 characters'
    return true
  }
}

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

async function handleSubmit() {
  const { valid } = await form.value.validate()
  if (!valid) return

  isSubmitting.value = true

  try {
    let result: Task

    if (props.isEdit && props.task) {
      const updateData: UpdateTaskRequest = {
        title: formData.title,
        description: formData.description || undefined,
        status: formData.status,
        priority: formData.priority,
        assigneeId: formData.assigneeId || undefined,
        dueDate: formData.dueDate || undefined,
        estimatedHours: formData.estimatedHours || undefined,
        tags: formData.tags.length > 0 ? formData.tags : undefined
      }
      result = await tasksStore.updateTask(props.task.id, updateData)
    } else {
      const createData: CreateTaskRequest = {
        projectId: formData.projectId,
        title: formData.title,
        description: formData.description || undefined,
        priority: formData.priority,
        assigneeId: formData.assigneeId || undefined,
        dueDate: formData.dueDate || undefined,
        estimatedHours: formData.estimatedHours || undefined,
        tags: formData.tags.length > 0 ? formData.tags : undefined
      }
      result = await tasksStore.createTask(createData)
    }

    emit('submit', result)
  } catch (error) {
  } finally {
    isSubmitting.value = false
  }
}

// Lifecycle
onMounted(async () => {
  // Fetch projects and users
  await projectsStore.fetchProjects()
  await usersStore.fetchUsers(1, 100)

  // Populate form if editing
  if (props.isEdit && props.task) {
    formData.title = props.task.title
    formData.description = props.task.description || ''
    formData.projectId = props.task.projectId
    formData.priority = props.task.priority
    formData.assigneeId = props.task.assigneeId || null
    formData.dueDate = props.task.dueDate || ''
    formData.estimatedHours = props.task.estimatedHours || null
    formData.tags = props.task.tags || []
    formData.status = props.task.status
  }
})
</script>