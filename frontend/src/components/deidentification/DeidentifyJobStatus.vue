<template>
  <v-card>
    <v-card-title>
      <div class="d-flex align-center justify-space-between w-100">
        <span>Job {{ jobId }} - {{ statusText }}</span>
        <v-chip
          :color="statusColor"
          variant="flat"
          label
        >
          {{ statusText }}
        </v-chip>
      </div>
    </v-card-title>

    <v-card-text>
      <!-- Loading State -->
      <v-progress-linear
        v-if="isJobStatusLoading && !jobStatus"
        indeterminate
        color="primary"
        class="mb-4"
      />

      <!-- Error State -->
      <v-alert v-if="jobStatusError" type="error" class="mb-4">
        {{ jobStatusError }}
      </v-alert>

      <!-- Job Status Display -->
      <div v-if="jobStatus">
        <!-- Progress Bar -->
        <v-progress-linear
          :model-value="jobStatus.progress_percentage"
          :color="statusColor"
          height="30"
          class="mb-4"
        >
          <template #default="{ value }">
            <strong>{{ Math.ceil(value) }}%</strong>
          </template>
        </v-progress-linear>

        <!-- Status Table -->
        <v-table>
          <tbody>
            <tr>
              <td class="font-weight-bold">Total Notes</td>
              <td>{{ jobStatus.total_notes.toLocaleString() }}</td>
            </tr>
            <tr>
              <td class="font-weight-bold">Processed</td>
              <td>
                {{ jobStatus.processed_notes.toLocaleString() }} /
                {{ jobStatus.total_notes.toLocaleString() }}
              </td>
            </tr>
            <tr v-if="jobStatus.error_count && jobStatus.error_count > 0">
              <td class="font-weight-bold text-error">Errors</td>
              <td class="text-error">{{ jobStatus.error_count }}</td>
            </tr>
            <tr>
              <td class="font-weight-bold">Created</td>
              <td>{{ formatDateTime(jobStatus.created_at) }}</td>
            </tr>
            <tr>
              <td class="font-weight-bold">Last Updated</td>
              <td>{{ formatDateTime(jobStatus.updated_at) }}</td>
            </tr>
            <tr v-if="!isJobTerminal">
              <td class="font-weight-bold">Estimated Completion</td>
              <td>{{ formatDateTime(jobStatus.estimated_completion) }}</td>
            </tr>
            <tr v-if="timeRemaining">
              <td class="font-weight-bold">Time Remaining</td>
              <td>{{ timeRemaining }}</td>
            </tr>
          </tbody>
        </v-table>

        <!-- Error List -->
        <v-expansion-panels v-if="jobStatus.errors && jobStatus.errors.length > 0" class="mt-4">
          <v-expansion-panel>
            <v-expansion-panel-title>
              <v-icon left color="error">mdi-alert-circle</v-icon>
              Errors ({{ jobStatus.errors.length }})
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-list>
                <v-list-item
                  v-for="(error, index) in jobStatus.errors"
                  :key="index"
                >
                  <v-list-item-title>Note ID: {{ error.note_id }}</v-list-item-title>
                  <v-list-item-subtitle class="text-error">
                    {{ error.error }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>

        <!-- Polling Indicator -->
        <v-alert v-if="isPolling && !isJobTerminal" type="info" class="mt-4" variant="tonal">
          <v-icon left>mdi-refresh</v-icon>
          Auto-refreshing every 5 seconds...
        </v-alert>
      </div>
    </v-card-text>

    <v-card-actions>
      <v-spacer />

      <!-- Cancel Button -->
      <v-btn
        v-if="canCancelJob"
        color="error"
        variant="outlined"
        @click="handleCancelJob"
      >
        <v-icon left>mdi-cancel</v-icon>
        Cancel Job
      </v-btn>

      <!-- Review Results Button -->
      <v-btn
        v-if="canDownloadResults"
        color="primary"
        @click="handleReviewResults"
      >
        <v-icon left>mdi-eye</v-icon>
        Review Results
      </v-btn>

      <!-- Refresh Button -->
      <v-btn
        color="primary"
        variant="outlined"
        :loading="isJobStatusLoading"
        @click="handleRefresh"
      >
        <v-icon left>mdi-refresh</v-icon>
        Refresh
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDeidentification } from '@/composables/useDeidentification'
import {
  getStatusLabel,
  getStatusColor
} from '@/types/deidentification'

interface Props {
  jobId: string
}

const props = defineProps<Props>()
const router = useRouter()

const {
  jobStatus,
  isJobStatusLoading,
  jobStatusError,
  isPolling,
  isJobTerminal,
  canCancelJob,
  canDownloadResults,
  fetchJobStatus,
  startPolling,
  stopPolling,
  cancelCurrentJob
} = useDeidentification()

// Computed: Status text
const statusText = computed(() => {
  if (!jobStatus.value) return 'Loading...'
  return getStatusLabel(jobStatus.value.status)
})

// Computed: Status color
const statusColor = computed(() => {
  if (!jobStatus.value) return 'grey'
  return getStatusColor(jobStatus.value.status)
})

// Computed: Time remaining estimate
const timeRemaining = computed(() => {
  if (!jobStatus.value || isJobTerminal.value) return null

  const { processed_notes, total_notes, created_at } = jobStatus.value

  if (processed_notes === 0) return 'Calculating...'

  const now = new Date()
  const created = new Date(created_at)
  const elapsed = now.getTime() - created.getTime()
  const rate = processed_notes / (elapsed / 1000) // notes per second
  const remaining = total_notes - processed_notes
  const remainingSeconds = remaining / rate

  if (remainingSeconds < 60) {
    return `${Math.ceil(remainingSeconds)} seconds`
  } else if (remainingSeconds < 3600) {
    return `${Math.ceil(remainingSeconds / 60)} minutes`
  } else {
    const hours = Math.floor(remainingSeconds / 3600)
    const minutes = Math.ceil((remainingSeconds % 3600) / 60)
    return `${hours}h ${minutes}m`
  }
})

/**
 * Format date/time for display
 */
function formatDateTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString()
}

/**
 * Handle cancel job
 */
async function handleCancelJob() {
  const confirmed = confirm('Are you sure you want to cancel this job?')
  if (!confirmed) return

  const success = await cancelCurrentJob(props.jobId)
  if (success) {
    // Status will be updated by next poll
  }
}

/**
 * Handle review results
 */
function handleReviewResults() {
  router.push(`/deidentify/jobs/${props.jobId}/review`)
}

/**
 * Handle manual refresh
 */
async function handleRefresh() {
  await fetchJobStatus(props.jobId)
}

// Lifecycle: Start polling on mount
onMounted(() => {
  startPolling(props.jobId)
})

// Lifecycle: Stop polling on unmount
onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.v-card-title {
  background-color: rgb(var(--v-theme-surface-variant));
}

.w-100 {
  width: 100%;
}
</style>
