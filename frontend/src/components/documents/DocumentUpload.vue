<template>
  <v-card>
    <v-card-title>
      <v-icon class="mr-2">mdi-file-upload</v-icon>
      Upload Clinical Document
    </v-card-title>

    <v-card-text>
      <v-alert v-if="uploadSuccess" type="success" variant="tonal" class="mb-4">
        <v-alert-title>Upload Successful</v-alert-title>
        <div v-if="uploadResult?.is_duplicate">
          Duplicate document detected. Existing document ID: {{ uploadResult.document_id }}
        </div>
        <div v-else>
          Document uploaded successfully. ID: {{ uploadResult?.document_id }}
        </div>
        <div class="mt-2">
          <strong>Status:</strong> {{ uploadResult?.status }}<br />
          <strong>File:</strong> {{ uploadResult?.filename }}<br />
          <strong>Size:</strong> {{ formatFileSize(uploadResult?.file_size) }}<br />
          <strong>Hash:</strong> {{ uploadResult?.content_hash?.substring(0, 16) }}...
        </div>
      </v-alert>

      <v-alert v-if="uploadError" type="error" variant="tonal" class="mb-4" closable @click:close="uploadError = null">
        <v-alert-title>Upload Failed</v-alert-title>
        {{ uploadError }}
      </v-alert>

      <v-file-input
        v-model="selectedFile"
        label="Select RTF Document"
        accept=".rtf"
        prepend-icon="mdi-file-document"
        :disabled="isUploading"
        :rules="[fileRequiredRule, fileTypeRule]"
        show-size
        clearable
        @update:model-value="resetStatus"
      />

      <v-progress-linear
        v-if="isUploading"
        indeterminate
        color="primary"
        class="mb-4"
      />

      <div class="d-flex justify-end">
        <v-btn
          color="primary"
          :disabled="!selectedFile || isUploading"
          :loading="isUploading"
          @click="uploadDocument"
        >
          <v-icon start>mdi-upload</v-icon>
          Upload Document
        </v-btn>
      </div>

      <v-divider class="my-4" />

      <div class="text-caption text-medium-emphasis">
        <p>
          <v-icon size="small" class="mr-1">mdi-information</v-icon>
          <strong>Supported Format:</strong> RTF (Rich Text Format) only
        </p>
        <p>
          <v-icon size="small" class="mr-1">mdi-shield-check</v-icon>
          <strong>Security:</strong> Documents are encrypted before storage (AES-256-GCM)
        </p>
        <p>
          <v-icon size="small" class="mr-1">mdi-content-duplicate</v-icon>
          <strong>Deduplication:</strong> Duplicate documents are automatically detected
        </p>
        <p>
          <v-icon size="small" class="mr-1">mdi-robot</v-icon>
          <strong>Processing:</strong> Clinical entities and PHI are extracted in the background
        </p>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { uploadDocument as apiUploadDocument } from '@/api/documents'
import type { DocumentUploadResponse } from '@/types/document'

// Component state
const selectedFile = ref<File[]>([])
const isUploading = ref(false)
const uploadSuccess = ref(false)
const uploadError = ref<string | null>(null)
const uploadResult = ref<DocumentUploadResponse | null>(null)

// Validation rules
const fileRequiredRule = (value: File[]) => {
  return value && value.length > 0 || 'File is required'
}

const fileTypeRule = (value: File[]) => {
  if (!value || value.length === 0) return true
  const file = value[0]
  return file.name.toLowerCase().endsWith('.rtf') || 'Only RTF files are supported'
}

// Reset upload status
const resetStatus = () => {
  uploadSuccess.value = false
  uploadError.value = null
  uploadResult.value = null
}

// Format file size for display
const formatFileSize = (bytes: number | undefined): string => {
  if (!bytes) return 'Unknown'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// Upload document
const uploadDocument = async () => {
  if (!selectedFile.value || selectedFile.value.length === 0) {
    uploadError.value = 'Please select a file to upload'
    return
  }

  const file = selectedFile.value[0]

  // Reset state
  resetStatus()
  isUploading.value = true

  try {
    // Call API
    const response = await apiUploadDocument(file)

    // Success
    uploadSuccess.value = true
    uploadResult.value = response

    // Clear file input
    selectedFile.value = []
  } catch (error: any) {
    // Error
    uploadError.value = error.response?.data?.detail || error.message || 'Upload failed'
  } finally {
    isUploading.value = false
  }
}
</script>

<style scoped>
.text-caption {
  line-height: 1.6;
}

.text-caption p {
  margin-bottom: 0.5rem;
}
</style>
