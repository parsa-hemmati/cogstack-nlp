<template>
  <v-card>
    <v-card-title>
      {{ isEdit ? 'Edit Project' : 'Create New Project' }}
    </v-card-title>

    <v-card-text>
      <v-form ref="form" v-model="isFormValid" @submit.prevent="handleSubmit">
        <v-container>
          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="formData.name"
                label="Project Name"
                prepend-icon="mdi-folder"
                :rules="[rules.required, rules.projectName]"
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
              <v-text-field
                v-model="formData.startDate"
                label="Start Date"
                prepend-icon="mdi-calendar-start"
                type="date"
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="formData.endDate"
                label="End Date"
                prepend-icon="mdi-calendar-end"
                type="date"
                :rules="[endDateRule]"
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

            <v-col v-if="isEdit" cols="12">
              <v-select
                v-model="formData.status"
                label="Status"
                prepend-icon="mdi-information"
                :items="statusOptions"
                variant="outlined"
                density="comfortable"
              />
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
import { ref, reactive, onMounted } from 'vue'
import { useProjectsStore } from '@/stores/projects'
import type { Project, CreateProjectRequest, UpdateProjectRequest } from '@/types'

// Props
const props = defineProps<{
  project?: Project | null
  isEdit?: boolean
}>()

// Emits
const emit = defineEmits<{
  submit: [project: Project]
  cancel: []
}>()

// Stores
const projectsStore = useProjectsStore()

// Refs
const form = ref()
const isFormValid = ref(false)
const isSubmitting = ref(false)

// Data
const formData = reactive({
  name: '',
  description: '',
  startDate: '',
  endDate: '',
  tags: [] as string[],
  status: 'active' as 'active' | 'archived' | 'draft'
})

const statusOptions = [
  { title: 'Active', value: 'active' },
  { title: 'Draft', value: 'draft' },
  { title: 'Archived', value: 'archived' }
]

// Validation rules
const rules = {
  required: (v: string) => !!v || 'This field is required',
  projectName: (v: string) => {
    if (v.length < 3) return 'Project name must be at least 3 characters'
    if (v.length > 100) return 'Project name must be less than 100 characters'
    return true
  }
}

const endDateRule = (v: string) => {
  if (!v || !formData.startDate) return true
  return new Date(v) >= new Date(formData.startDate) || 'End date must be after start date'
}

// Methods
async function handleSubmit() {
  const { valid } = await form.value.validate()
  if (!valid) return

  isSubmitting.value = true

  try {
    let result: Project

    if (props.isEdit && props.project) {
      const updateData: UpdateProjectRequest = {
        name: formData.name,
        description: formData.description || undefined,
        status: formData.status,
        startDate: formData.startDate || undefined,
        endDate: formData.endDate || undefined,
        tags: formData.tags.length > 0 ? formData.tags : undefined
      }
      result = await projectsStore.updateProject(props.project.id, updateData)
    } else {
      const createData: CreateProjectRequest = {
        name: formData.name,
        description: formData.description || undefined,
        startDate: formData.startDate || undefined,
        endDate: formData.endDate || undefined,
        tags: formData.tags.length > 0 ? formData.tags : undefined
      }
      result = await projectsStore.createProject(createData)
    }

    emit('submit', result)
  } catch (error) {
  } finally {
    isSubmitting.value = false
  }
}

// Lifecycle
onMounted(() => {
  // Populate form if editing
  if (props.isEdit && props.project) {
    formData.name = props.project.name
    formData.description = props.project.description || ''
    formData.startDate = props.project.startDate || ''
    formData.endDate = props.project.endDate || ''
    formData.tags = props.project.tags || []
    formData.status = props.project.status
  }
})
</script>