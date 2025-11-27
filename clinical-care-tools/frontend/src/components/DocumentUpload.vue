<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon left>mdi-file-upload</v-icon>
      Upload Clinical Document
    </v-card-title>

    <v-card-text>
      <!-- Upload File Input -->
      <v-file-input
        v-model="selectedFile"
        label="Select RTF document"
        accept=".rtf"
        prepend-icon="mdi-file-document"
        :disabled="uploading"
        :rules="fileRules"
        show-size
        counter
        clearable
        @update:model-value="clearMessages"
      ></v-file-input>

      <!-- Upload Progress -->
      <v-progress-linear
        v-if="uploading"
        indeterminate
        color="primary"
        class="mb-4"
      >
      </v-progress-linear>

      <!-- Processing Status -->
      <v-alert
        v-if="processingStatus"
        :type="processingStatusType"
        variant="tonal"
        class="mb-4"
      >
        <div class="d-flex align-center">
          <v-icon v-if="processingStatus === 'processing'" class="mr-2">mdi-cog</v-icon>
          <v-icon v-else-if="processingStatus === 'completed'" class="mr-2">mdi-check-circle</v-icon>
          <v-icon v-else-if="processingStatus === 'failed'" class="mr-2">mdi-alert-circle</v-icon>
          <span>
            <strong>Status:</strong>
            {{ processingStatusMessage }}
          </span>
        </div>
      </v-alert>

      <!-- Duplicate Detection Message -->
      <v-alert
        v-if="duplicateMessage"
        type="warning"
        variant="tonal"
        closable
        @click:close="duplicateMessage = null"
        class="mb-4"
      >
        <div>
          <strong>Duplicate Document Detected</strong>
          <p class="mb-0 mt-2">{{ duplicateMessage }}</p>
        </div>
      </v-alert>

      <!-- Success Message -->
      <v-alert
        v-if="successMessage"
        type="success"
        variant="tonal"
        closable
        @click:close="successMessage = null"
        class="mb-4"
      >
        {{ successMessage }}
      </v-alert>

      <!-- Error Message -->
      <v-alert
        v-if="errorMessage"
        type="error"
        variant="tonal"
        closable
        @click:close="errorMessage = null"
        class="mb-4"
      >
        {{ errorMessage }}
      </v-alert>
    </v-card-text>

    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        prepend-icon="mdi-upload"
        :disabled="!selectedFile || uploading"
        :loading="uploading"
        @click="handleUpload"
      >
        Upload Document
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { uploadDocument, isDuplicateResponse, type DocumentUploadResponse, type DocumentDuplicateResponse } from '@/services/documents'

// Props
interface Props {
  projectId: string
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  uploaded: [response: DocumentUploadResponse]
  duplicate: [response: DocumentDuplicateResponse]
}>()

// State
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const processingStatus = ref<'pending' | 'processing' | 'completed' | 'failed' | null>(null)
const duplicateMessage = ref<string | null>(null)
const successMessage = ref<string | null>(null)
const errorMessage = ref<string | null>(null)

// File validation rules
const fileRules = [
  (value: File | null) => {
    if (!value) return 'File is required'
    return true
  },
  (value: File | null) => {
    if (value && !value.name.endsWith('.rtf')) {
      return 'Only RTF files are allowed'
    }
    return true
  },
  (value: File | null) => {
    if (value && value.size > 10 * 1024 * 1024) { // 10MB
      return 'File size must be less than 10MB'
    }
    return true
  },
]

// Computed
const processingStatusType = computed(() => {
  switch (processingStatus.value) {
    case 'pending':
    case 'processing':
      return 'info'
    case 'completed':
      return 'success'
    case 'failed':
      return 'error'
    default:
      return 'info'
  }
})

const processingStatusMessage = computed(() => {
  switch (processingStatus.value) {
    case 'pending':
      return 'Document queued for processing'
    case 'processing':
      return 'Extracting medical entities and PHI...'
    case 'completed':
      return 'Processing complete! Medical entities extracted successfully.'
    case 'failed':
      return 'Processing failed. Please try again or contact support.'
    default:
      return ''
  }
})

// Methods
function clearMessages() {
  duplicateMessage.value = null
  successMessage.value = null
  errorMessage.value = null
  processingStatus.value = null
}

async function handleUpload() {
  if (!selectedFile.value) {
    errorMessage.value = 'Please select a file to upload'
    return
  }

  clearMessages()
  uploading.value = true

  try {
    const response = await uploadDocument(selectedFile.value, props.projectId)

    if (isDuplicateResponse(response)) {
      // Duplicate detected
      duplicateMessage.value = `This document was previously uploaded on ${new Date(response.original_upload_date).toLocaleDateString()} by User ID: ${response.uploaded_by}`
      emit('duplicate', response)
    } else {
      // New upload successful
      successMessage.value = `Document "${response.filename}" uploaded successfully (${formatFileSize(response.file_size)})`
      processingStatus.value = response.processing_status

      // Simulate status updates (in real app, would poll API or use WebSocket)
      if (response.processing_status === 'pending') {
        setTimeout(() => {
          processingStatus.value = 'processing'
        }, 1000)
        setTimeout(() => {
          processingStatus.value = 'completed'
        }, 3000)
      }

      emit('uploaded', response)

      // Clear file input after successful upload
      selectedFile.value = null
    }
  } catch (error: any) {
    console.error('Upload error:', error)
    errorMessage.value = error.response?.data?.detail || 'Failed to upload document. Please try again.'
  } finally {
    uploading.value = false
  }
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
/* Component-specific styles */
</style>
