<template>
  <v-container>
    <v-row>
      <!-- Project Header -->
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-btn icon @click="goBack" class="mr-3">
              <v-icon>mdi-arrow-left</v-icon>
            </v-btn>
            <v-icon left>mdi-folder</v-icon>
            {{ project?.name || 'Loading...' }}
          </v-card-title>

          <v-card-text v-if="project">
            <p class="text-body-1">{{ project.description || 'No description' }}</p>
            <div class="text-caption text-grey">
              Created: {{ formatDate(project.created_at) }} | Members: {{ project.members.length }}
            </div>
          </v-card-text>

          <!-- Loading State -->
          <v-card-text v-if="loading">
            <v-progress-linear indeterminate color="primary"></v-progress-linear>
          </v-card-text>

          <!-- Error State -->
          <v-card-text v-if="error">
            <v-alert type="error" closable @click:close="error = null">
              {{ error }}
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Document Upload Section -->
      <v-col cols="12" md="6">
        <DocumentUpload
          v-if="projectId"
          :project-id="projectId"
          @uploaded="handleDocumentUploaded"
          @duplicate="handleDocumentDuplicate"
        />
      </v-col>

      <!-- Recent Documents (Placeholder) -->
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon left>mdi-file-document-multiple</v-icon>
            Recent Documents
          </v-card-title>

          <v-card-text>
            <v-alert type="info" variant="tonal">
              Recent documents will be displayed here after upload.
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Snackbar for notifications -->
      <v-snackbar
        v-model="snackbar"
        :color="snackbarColor"
        :timeout="3000"
        location="top"
      >
        {{ snackbarMessage }}
        <template v-slot:actions>
          <v-btn variant="text" @click="snackbar = false">Close</v-btn>
        </template>
      </v-snackbar>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchProject, type Project } from '@/services/projects'
import { type DocumentUploadResponse, type DocumentDuplicateResponse } from '@/services/documents'
import DocumentUpload from '@/components/DocumentUpload.vue'

// Router
const route = useRoute()
const router = useRouter()

// State
const projectId = ref<string>(route.params.id as string)
const project = ref<Project | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const snackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

// Lifecycle
onMounted(async () => {
  await loadProject()
})

// Methods
async function loadProject() {
  if (!projectId.value) {
    error.value = 'Project ID is required'
    return
  }

  loading.value = true
  error.value = null

  try {
    project.value = await fetchProject(projectId.value)
  } catch (err: any) {
    console.error('Failed to load project:', err)
    error.value = err.response?.data?.detail || 'Failed to load project'
  } finally {
    loading.value = false
  }
}

function handleDocumentUploaded(response: DocumentUploadResponse) {
  snackbarMessage.value = `Document "${response.filename}" uploaded successfully!`
  snackbarColor.value = 'success'
  snackbar.value = true

  // TODO: Refresh recent documents list
}

function handleDocumentDuplicate(response: DocumentDuplicateResponse) {
  snackbarMessage.value = 'Duplicate document detected'
  snackbarColor.value = 'warning'
  snackbar.value = true
}

function goBack() {
  router.push({ name: 'projects' })
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}
</script>

<style scoped>
/* View-specific styles */
</style>
