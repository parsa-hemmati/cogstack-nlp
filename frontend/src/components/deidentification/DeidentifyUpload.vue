<template>
  <v-card>
    <v-card-title>Upload Notes for De-identification</v-card-title>
    <v-card-text>
      <!-- Upload Method Tabs -->
      <v-tabs v-model="uploadMethod" class="mb-4">
        <v-tab value="csv">CSV Upload</v-tab>
        <v-tab value="database">Database Query</v-tab>
      </v-tabs>

      <!-- CSV Upload Tab -->
      <v-window v-model="uploadMethod">
        <v-window-item value="csv">
          <v-file-input
            v-model="csvFile"
            label="Upload CSV file"
            accept=".csv"
            :rules="csvRules"
            prepend-icon="mdi-file-delimited"
            show-size
            :error-messages="csvError"
            @change="onCsvFileChange"
          />
          <v-alert v-if="csvValidation && !csvValidation.valid" type="error" class="mt-2">
            <div v-for="(error, index) in csvValidation.errors" :key="index">
              {{ error }}
            </div>
          </v-alert>
          <v-alert v-if="csvValidation && csvValidation.valid" type="success" class="mt-2">
            Valid CSV: {{ csvValidation.row_count }} rows detected
          </v-alert>
        </v-window-item>

        <!-- Database Query Tab -->
        <v-window-item value="database">
          <v-textarea
            v-model="sqlQuery"
            label="SQL Query"
            placeholder="SELECT id, text FROM clinical_notes WHERE ..."
            :rules="queryRules"
            rows="5"
            auto-grow
            :error-messages="queryError"
            @input="onQueryChange"
          />
          <v-alert v-if="queryValidation && !queryValidation.valid" type="error" class="mt-2">
            <div v-for="(error, index) in queryValidation.errors" :key="index">
              {{ error }}
            </div>
          </v-alert>
          <v-alert
            v-if="queryValidation && queryValidation.valid && queryValidation.estimated_rows"
            type="info"
            class="mt-2"
          >
            Estimated rows: {{ queryValidation.estimated_rows }}
          </v-alert>
        </v-window-item>
      </v-window>

      <!-- Method Selection -->
      <v-select
        v-model="method"
        :items="methodItems"
        item-title="label"
        item-value="value"
        label="De-identification Method"
        prepend-icon="mdi-shield-lock"
        class="mt-4"
      />

      <!-- Email Notification -->
      <v-text-field
        v-model="email"
        label="Email notification (optional)"
        type="email"
        prepend-icon="mdi-email"
        :rules="emailRules"
        hint="Receive notification when processing completes"
        persistent-hint
      />

      <!-- Error Display -->
      <v-alert v-if="batchUploadError" type="error" class="mt-4">
        {{ batchUploadError }}
      </v-alert>
    </v-card-text>

    <v-card-actions>
      <v-spacer />
      <v-btn
        color="primary"
        :loading="isBatchUploading"
        :disabled="!canSubmit"
        @click="submitBatch"
      >
        <v-icon left>mdi-rocket-launch</v-icon>
        Start De-identification
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDeidentification } from '@/composables/useDeidentification'
import {
  DeidentificationMethod,
  getMethodLabel
} from '@/types/deidentification'
import type {
  CSVValidationResult,
  QueryValidationResult
} from '@/types/deidentification'

const router = useRouter()
const {
  uploadCSV,
  submitBatch: submitBatchApi,
  isBatchUploading,
  batchUploadError,
  currentJob
} = useDeidentification()

// Upload method
const uploadMethod = ref<'csv' | 'database'>('csv')

// CSV upload state
const csvFile = ref<File[]>([])
const csvError = ref<string | null>(null)
const csvValidation = ref<CSVValidationResult | null>(null)

// Database query state
const sqlQuery = ref<string>('')
const queryError = ref<string | null>(null)
const queryValidation = ref<QueryValidationResult | null>(null)

// Method selection
const method = ref<DeidentificationMethod>(DeidentificationMethod.REPLACEMENT)

// Email notification
const email = ref<string>('')

// Method items for dropdown
const methodItems = computed(() => [
  {
    label: getMethodLabel(DeidentificationMethod.REMOVAL),
    value: DeidentificationMethod.REMOVAL
  },
  {
    label: getMethodLabel(DeidentificationMethod.REPLACEMENT),
    value: DeidentificationMethod.REPLACEMENT
  },
  {
    label: getMethodLabel(DeidentificationMethod.GENERALIZATION),
    value: DeidentificationMethod.GENERALIZATION
  }
])

// Validation rules
const csvRules = [
  (value: File[]) => {
    if (!value || value.length === 0) return 'Please select a CSV file'
    const file = value[0]
    if (!file.name.endsWith('.csv')) return 'File must be a CSV'
    if (file.size > 50 * 1024 * 1024) return 'File size must be less than 50MB'
    return true
  }
]

const queryRules = [
  (value: string) => {
    if (!value || !value.trim()) return 'Please enter a SQL query'
    if (!value.toLowerCase().includes('select')) return 'Query must be a SELECT statement'
    if (value.toLowerCase().includes('drop') || value.toLowerCase().includes('delete')) {
      return 'Only SELECT queries are allowed'
    }
    return true
  }
]

const emailRules = [
  (value: string) => {
    if (!value) return true // Optional
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return pattern.test(value) || 'Invalid email address'
  }
]

// Computed: Can submit
const canSubmit = computed(() => {
  if (uploadMethod.value === 'csv') {
    return csvFile.value.length > 0 && csvValidation.value?.valid === true
  } else {
    return sqlQuery.value.trim().length > 0 && queryValidation.value?.valid === true
  }
})

/**
 * Validate CSV file
 */
function validateCSV(file: File): CSVValidationResult {
  const errors: string[] = []

  // Check file size
  if (file.size === 0) {
    errors.push('CSV file is empty')
  }

  if (file.size > 50 * 1024 * 1024) {
    errors.push('CSV file exceeds 50MB limit')
  }

  // Check extension
  if (!file.name.endsWith('.csv')) {
    errors.push('File must have .csv extension')
  }

  // Estimate row count (rough estimate: 500 bytes per row average)
  const estimatedRows = Math.floor(file.size / 500)

  if (estimatedRows > 10000) {
    errors.push('CSV file exceeds 10,000 rows limit')
  }

  if (estimatedRows === 0) {
    errors.push('CSV file appears to be empty')
  }

  return {
    valid: errors.length === 0,
    errors,
    row_count: estimatedRows
  }
}

/**
 * Validate SQL query
 */
function validateQuery(query: string): QueryValidationResult {
  const errors: string[] = []
  const lowerQuery = query.toLowerCase().trim()

  // Check if query is present
  if (!lowerQuery) {
    errors.push('Query cannot be empty')
    return { valid: false, errors }
  }

  // Must be SELECT
  if (!lowerQuery.startsWith('select')) {
    errors.push('Query must start with SELECT')
  }

  // Prevent destructive operations
  const destructiveOps = ['drop', 'delete', 'update', 'insert', 'truncate', 'alter']
  for (const op of destructiveOps) {
    if (lowerQuery.includes(op)) {
      errors.push(`Query cannot contain ${op.toUpperCase()} operation`)
    }
  }

  // Must select from clinical_notes (or similar)
  if (!lowerQuery.includes('from')) {
    errors.push('Query must include FROM clause')
  }

  // Basic validation passed
  return {
    valid: errors.length === 0,
    errors,
    estimated_rows: errors.length === 0 ? undefined : 0
  }
}

/**
 * Handle CSV file change
 */
function onCsvFileChange() {
  csvError.value = null
  csvValidation.value = null

  if (csvFile.value && csvFile.value.length > 0) {
    const file = csvFile.value[0]
    csvValidation.value = validateCSV(file)
  }
}

/**
 * Handle query change
 */
function onQueryChange() {
  queryError.value = null
  queryValidation.value = null

  if (sqlQuery.value.trim()) {
    queryValidation.value = validateQuery(sqlQuery.value)
  }
}

/**
 * Submit batch for de-identification
 */
async function submitBatch() {
  let job

  if (uploadMethod.value === 'csv') {
    // CSV upload
    if (csvFile.value.length === 0) {
      csvError.value = 'Please select a CSV file'
      return
    }

    const file = csvFile.value[0]
    job = await uploadCSV(file, method.value, email.value || undefined)
  } else {
    // Database query - Not implemented in this version
    // Would need backend support for database query execution
    queryError.value = 'Database query method not yet implemented'
    return
  }

  // Navigate to job status page if successful
  if (job) {
    router.push(`/deidentify/jobs/${job.job_id}`)
  }
}
</script>

<style scoped>
.v-card-title {
  background-color: rgb(var(--v-theme-primary));
  color: white;
}
</style>
