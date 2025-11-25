<template>
  <v-card>
    <v-card-title>De-identification Results</v-card-title>

    <v-card-text>
      <!-- Job Summary -->
      <v-alert v-if="jobStatus" type="info" variant="tonal" class="mb-4">
        <div class="d-flex align-center justify-space-between">
          <div>
            <strong>Job ID:</strong> {{ jobId }}<br />
            <strong>Total Notes:</strong> {{ jobStatus.total_notes.toLocaleString() }}<br />
            <strong>Processed:</strong> {{ jobStatus.processed_notes.toLocaleString() }}<br />
            <strong>Status:</strong> {{ getStatusLabel(jobStatus.status) }}
          </div>
          <v-chip
            :color="getStatusColor(jobStatus.status)"
            variant="flat"
            size="large"
          >
            {{ getStatusLabel(jobStatus.status) }}
          </v-chip>
        </div>
      </v-alert>

      <!-- Search and Filter Controls -->
      <v-row class="mb-4">
        <v-col cols="12" md="6">
          <v-text-field
            v-model="search"
            label="Search in results"
            prepend-icon="mdi-magnify"
            clearable
            hide-details
          />
        </v-col>
        <v-col cols="12" md="3">
          <v-select
            v-model="confidenceFilter"
            :items="confidenceFilterItems"
            label="Confidence Filter"
            hide-details
          />
        </v-col>
        <v-col cols="12" md="3">
          <v-select
            v-model="reviewFilter"
            :items="reviewFilterItems"
            label="Review Status"
            hide-details
          />
        </v-col>
      </v-row>

      <!-- Results Table -->
      <v-data-table
        :headers="resultHeaders"
        :items="filteredResults"
        :search="search"
        :items-per-page="50"
        :loading="isJobResultsLoading"
        class="elevation-1"
      >
        <!-- Note ID Column -->
        <template #item.note_id="{ item }">
          <code class="text-primary">{{ item.note_id }}</code>
        </template>

        <!-- Confidence Column -->
        <template #item.confidence_score="{ item }">
          <v-chip
            :color="getConfidenceColor(item.confidence_score)"
            variant="flat"
            size="small"
          >
            {{ (item.confidence_score * 100).toFixed(0) }}%
          </v-chip>
        </template>

        <!-- Entities Count Column -->
        <template #item.entities_count="{ item }">
          <v-chip variant="outlined" size="small">
            {{ item.entities_removed.length }} entities
          </v-chip>
        </template>

        <!-- Review Required Column -->
        <template #item.review_required="{ item }">
          <v-chip
            v-if="item.review_required"
            color="warning"
            variant="flat"
            size="small"
          >
            <v-icon left size="small">mdi-flag</v-icon>
            Review
          </v-chip>
          <v-chip v-else color="success" variant="outlined" size="small">
            <v-icon left size="small">mdi-check</v-icon>
            OK
          </v-chip>
        </template>

        <!-- Method Column -->
        <template #item.method_used="{ item }">
          <v-chip variant="outlined" size="small">
            {{ getMethodLabel(item.method_used) }}
          </v-chip>
        </template>

        <!-- Created At Column -->
        <template #item.created_at="{ item }">
          {{ formatDateTime(item.created_at) }}
        </template>
      </v-data-table>

      <!-- Download Section -->
      <v-divider class="my-4" />

      <div class="text-h6 mb-4">Download Options</div>

      <v-row>
        <v-col cols="12" md="4">
          <v-btn
            block
            color="primary"
            variant="elevated"
            :loading="downloadingFormat === 'csv'"
            @click="handleDownload('csv')"
          >
            <v-icon left>mdi-file-delimited</v-icon>
            Download CSV
          </v-btn>
        </v-col>
        <v-col cols="12" md="4">
          <v-btn
            block
            color="primary"
            variant="elevated"
            :loading="downloadingFormat === 'json'"
            @click="handleDownload('json')"
          >
            <v-icon left>mdi-code-json</v-icon>
            Download JSON
          </v-btn>
        </v-col>
        <v-col cols="12" md="4">
          <v-btn
            block
            color="secondary"
            variant="elevated"
            :loading="downloadingAudit"
            @click="handleDownloadAudit"
          >
            <v-icon left>mdi-file-pdf-box</v-icon>
            Download Audit Report (PDF)
          </v-btn>
        </v-col>
      </v-row>

      <!-- Error Display -->
      <v-alert v-if="jobResultsError" type="error" class="mt-4">
        {{ jobResultsError }}
      </v-alert>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useDeidentification } from '@/composables/useDeidentification'
import {
  getConfidenceColor,
  getMethodLabel,
  getStatusLabel,
  getStatusColor,
  DeidentificationMethod
} from '@/types/deidentification'
import type { DownloadFormat } from '@/types/deidentification'

const route = useRoute()
const jobId = computed(() => route.params.jobId as string)

const {
  jobResults,
  isJobResultsLoading,
  jobResultsError,
  jobStatus,
  fetchJobResults,
  fetchJobStatus,
  downloadJobResults,
  downloadAudit
} = useDeidentification()

// Filter state
const search = ref<string>('')
const confidenceFilter = ref<string>('All')
const reviewFilter = ref<string>('All')

// Download state
const downloadingFormat = ref<DownloadFormat | null>(null)
const downloadingAudit = ref(false)

// Filter items
const confidenceFilterItems = [
  { title: 'All Confidence Levels', value: 'All' },
  { title: 'High (≥90%)', value: '>0.9' },
  { title: 'Medium (≥80%)', value: '>0.8' },
  { title: 'Low (<80%)', value: '<0.8' }
]

const reviewFilterItems = [
  { title: 'All Notes', value: 'All' },
  { title: 'Needs Review', value: 'review' },
  { title: 'OK', value: 'ok' }
]

// Results table headers
const resultHeaders = [
  { title: 'Note ID', key: 'note_id', align: 'start' },
  { title: 'Confidence', key: 'confidence_score', align: 'center', sortable: true },
  { title: 'Entities', key: 'entities_count', align: 'center' },
  { title: 'Method', key: 'method_used', align: 'center' },
  { title: 'Review', key: 'review_required', align: 'center', sortable: true },
  { title: 'Created', key: 'created_at', align: 'center', sortable: true }
]

// Computed: Filtered results
const filteredResults = computed(() => {
  let results = jobResults.value

  // Apply confidence filter
  if (confidenceFilter.value !== 'All') {
    const threshold = parseFloat(confidenceFilter.value.replace('>', '').replace('<', ''))
    const operator = confidenceFilter.value.startsWith('>') ? 'gte' : 'lt'

    results = results.filter(result => {
      if (operator === 'gte') {
        return result.confidence_score >= threshold
      } else {
        return result.confidence_score < threshold
      }
    })
  }

  // Apply review filter
  if (reviewFilter.value !== 'All') {
    results = results.filter(result => {
      if (reviewFilter.value === 'review') {
        return result.review_required === true
      } else {
        return result.review_required === false
      }
    })
  }

  return results
})

/**
 * Format date/time for display
 */
function formatDateTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString()
}

/**
 * Handle download in specified format
 */
async function handleDownload(format: DownloadFormat) {
  downloadingFormat.value = format

  try {
    const success = await downloadJobResults(jobId.value, format)
    if (success) {
      // Success feedback (file downloaded)
    }
  } finally {
    downloadingFormat.value = null
  }
}

/**
 * Handle download audit report
 */
async function handleDownloadAudit() {
  downloadingAudit.value = true

  try {
    const success = await downloadAudit(jobId.value)
    if (success) {
      // Success feedback (file downloaded)
    }
  } finally {
    downloadingAudit.value = false
  }
}

// Lifecycle: Fetch data on mount
onMounted(async () => {
  if (jobId.value) {
    // Fetch job status
    await fetchJobStatus(jobId.value)

    // Fetch all results (up to 1000)
    await fetchJobResults(jobId.value, 1000, 0)
  }
})
</script>

<style scoped>
.v-card-title {
  background-color: rgb(var(--v-theme-primary));
  color: white;
}
</style>
