<template>
  <v-container fluid>
    <!-- Loading State -->
    <v-progress-linear
      v-if="isJobResultsLoading"
      indeterminate
      color="primary"
      class="mb-4"
    />

    <!-- Error State -->
    <v-alert v-if="jobResultsError" type="error" class="mb-4">
      {{ jobResultsError }}
    </v-alert>

    <!-- Results Navigation -->
    <v-card v-if="jobResults.length > 0" class="mb-4">
      <v-card-text>
        <div class="d-flex align-center justify-space-between">
          <div>
            <span class="text-h6">
              Note {{ currentIndex + 1 }} of {{ jobResults.length }}
            </span>
          </div>
          <div>
            <v-btn
              icon
              :disabled="currentIndex === 0"
              @click="previousNote"
            >
              <v-icon>mdi-chevron-left</v-icon>
            </v-btn>
            <v-btn
              icon
              :disabled="currentIndex === jobResults.length - 1"
              @click="nextNote"
            >
              <v-icon>mdi-chevron-right</v-icon>
            </v-btn>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- Side-by-Side Comparison -->
    <v-row v-if="currentNote">
      <!-- Original Note (PHI) -->
      <v-col cols="12" md="6">
        <v-card class="fill-height">
          <v-card-title class="bg-warning text-white">
            <v-icon left>mdi-alert</v-icon>
            Original Note (Contains PHI)
          </v-card-title>
          <v-card-text>
            <div class="note-content" v-html="highlightedOriginal" />
          </v-card-text>
        </v-card>
      </v-col>

      <!-- De-identified Note -->
      <v-col cols="12" md="6">
        <v-card class="fill-height">
          <v-card-title class="bg-success text-white">
            <v-icon left>mdi-shield-check</v-icon>
            De-identified Note
          </v-card-title>
          <v-card-text>
            <div class="note-content">
              {{ currentNote.deidentified_text }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Entities Removed Table -->
    <v-card v-if="currentNote" class="mt-4">
      <v-card-title>
        PHI Entities Removed ({{ currentNote.entities_removed.length }})
      </v-card-title>
      <v-card-text>
        <v-data-table
          :headers="entityHeaders"
          :items="currentNote.entities_removed"
          :items-per-page="10"
          class="elevation-1"
        >
          <!-- Confidence Column with Color Chip -->
          <template #item.confidence="{ item }">
            <v-chip
              :color="getConfidenceColor(item.confidence)"
              variant="flat"
              size="small"
            >
              {{ (item.confidence * 100).toFixed(0) }}%
            </v-chip>
          </template>

          <!-- Type Column with Icon -->
          <template #item.type="{ item }">
            <v-chip variant="outlined" size="small">
              <v-icon left size="small">{{ getTypeIcon(item.type) }}</v-icon>
              {{ item.type }}
            </v-chip>
          </template>

          <!-- Text Column (PHI) -->
          <template #item.text="{ item }">
            <code class="text-warning font-weight-bold">{{ item.text }}</code>
          </template>
        </v-data-table>

        <!-- Overall Confidence Score -->
        <v-alert
          v-if="currentNote"
          :type="getConfidenceAlertType(currentNote.confidence_score)"
          class="mt-4"
          variant="tonal"
        >
          <div class="d-flex align-center">
            <div class="flex-grow-1">
              <strong>Overall Confidence:</strong>
              {{ (currentNote.confidence_score * 100).toFixed(1) }}%
            </div>
            <v-chip
              v-if="currentNote.review_required"
              color="warning"
              variant="flat"
            >
              <v-icon left>mdi-flag</v-icon>
              Manual Review Required
            </v-chip>
          </div>
        </v-alert>
      </v-card-text>
    </v-card>

    <!-- Action Buttons -->
    <v-card v-if="currentNote" class="mt-4">
      <v-card-actions>
        <v-spacer />
        <v-btn
          color="success"
          variant="elevated"
          @click="approveNote"
        >
          <v-icon left>mdi-check-circle</v-icon>
          Approve De-identification
        </v-btn>
        <v-btn
          color="warning"
          variant="outlined"
          @click="flagForReview"
        >
          <v-icon left>mdi-flag</v-icon>
          Flag for Manual Review
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- Empty State -->
    <v-alert v-if="!isJobResultsLoading && jobResults.length === 0" type="info">
      No results available for this job.
    </v-alert>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useDeidentification } from '@/composables/useDeidentification'
import { getConfidenceColor } from '@/types/deidentification'
import type { PHIEntityType } from '@/types/deidentification'

const route = useRoute()
const jobId = computed(() => route.params.jobId as string)

const {
  jobResults,
  isJobResultsLoading,
  jobResultsError,
  fetchJobResults
} = useDeidentification()

// Current note index
const currentIndex = ref(0)

// Computed: Current note
const currentNote = computed(() => {
  if (jobResults.value.length === 0) return null
  return jobResults.value[currentIndex.value]
})

// Computed: Highlighted original text
const highlightedOriginal = computed(() => {
  if (!currentNote.value) return ''

  let text = currentNote.value.deidentified_text // We don't store original PHI
  const entities = currentNote.value.entities_removed

  // Sort entities by start position (descending) to avoid offset issues
  const sortedEntities = [...entities].sort((a, b) => b.start - a.start)

  // Highlight each entity
  for (const entity of sortedEntities) {
    const before = text.substring(0, entity.start)
    const highlighted = text.substring(entity.start, entity.end)
    const after = text.substring(entity.end)

    const color = getEntityColor(entity.type)
    text = `${before}<mark class="entity-highlight" style="background-color: ${color}; padding: 2px 4px; border-radius: 3px;">${highlighted}</mark>${after}`
  }

  return text
})

// Entity table headers
const entityHeaders = [
  { title: 'Type', key: 'type', align: 'start' },
  { title: 'Text', key: 'text', align: 'start' },
  { title: 'Confidence', key: 'confidence', align: 'center' },
  { title: 'Position', key: 'start', align: 'center' }
]

/**
 * Get color for entity type
 */
function getEntityColor(type: PHIEntityType): string {
  const colors: Record<string, string> = {
    NAME: '#FFEB3B',
    LOCATION: '#FF9800',
    DATE: '#2196F3',
    AGE: '#9C27B0',
    PHONE: '#4CAF50',
    EMAIL: '#00BCD4',
    SSN: '#F44336',
    MRN: '#E91E63',
    DEFAULT: '#FFC107'
  }
  return colors[type] || colors.DEFAULT
}

/**
 * Get icon for entity type
 */
function getTypeIcon(type: PHIEntityType): string {
  const icons: Record<string, string> = {
    NAME: 'mdi-account',
    LOCATION: 'mdi-map-marker',
    DATE: 'mdi-calendar',
    AGE: 'mdi-numeric',
    PHONE: 'mdi-phone',
    EMAIL: 'mdi-email',
    SSN: 'mdi-card-account-details',
    MRN: 'mdi-identifier',
    DEFAULT: 'mdi-shield-alert'
  }
  return icons[type] || icons.DEFAULT
}

/**
 * Get confidence alert type
 */
function getConfidenceAlertType(confidence: number): string {
  if (confidence >= 0.9) return 'success'
  if (confidence >= 0.8) return 'warning'
  return 'error'
}

/**
 * Navigate to previous note
 */
function previousNote() {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

/**
 * Navigate to next note
 */
function nextNote() {
  if (currentIndex.value < jobResults.value.length - 1) {
    currentIndex.value++
  }
}

/**
 * Approve current note
 */
function approveNote() {
  alert('Note approved! (Backend integration pending)')
  // TODO: Call API to mark note as approved
  nextNote()
}

/**
 * Flag current note for manual review
 */
function flagForReview() {
  alert('Note flagged for review! (Backend integration pending)')
  // TODO: Call API to flag note for review
  nextNote()
}

// Lifecycle: Fetch results on mount
onMounted(() => {
  if (jobId.value) {
    fetchJobResults(jobId.value, 100, 0) // Fetch first 100 results
  }
})
</script>

<style scoped>
.note-content {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  padding: 16px;
  background-color: #f5f5f5;
  border-radius: 4px;
  max-height: 500px;
  overflow-y: auto;
}

.bg-warning {
  background-color: rgb(var(--v-theme-warning)) !important;
}

.bg-success {
  background-color: rgb(var(--v-theme-success)) !important;
}

.fill-height {
  height: 100%;
}

.entity-highlight {
  font-weight: bold;
  cursor: help;
}
</style>
