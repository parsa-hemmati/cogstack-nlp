<template>
  <div class="timeline-view">
    <PatientHeader
      v-if="patient"
      :patient="patient"
    />

    <div class="timeline-container">
      <TimelineControls
        :loading="loading"
        :patient-id="patientId"
        @filter-change="handleFilterChange"
        @view-mode-change="handleViewModeChange"
        @export="handleExport"
      />

      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading timeline data...</p>
      </div>

      <div v-else-if="error" class="error-state">
        <p class="error-message">{{ error }}</p>
        <button @click="retryLoad">Retry</button>
      </div>

      <TimelineChart
        v-else-if="timelineData"
        :timeline-data="timelineData"
        :view-mode="viewMode"
        @select-document="handleSelectDocument"
        @select-concept="handleSelectConcept"
      />

      <div v-else class="empty-state">
        <p>No timeline data available for this patient.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useTimelineStore } from '@/stores/timeline'
import { timelineApi } from '@/api/timeline'
import PatientHeader from '@/components/timeline/PatientHeader.vue'
import TimelineControls from '@/components/timeline/TimelineControls.vue'
import TimelineChart from '@/components/timeline/TimelineChart.vue'
import type { TimelineFilters, ViewMode } from '@/types/timeline'

const route = useRoute()
const timelineStore = useTimelineStore()

// Get patient ID from route
const patientId = computed(() => route.params.id as string)

// Component state
const viewMode = ref<ViewMode>('combined')

// Store state
const timelineData = computed(() => timelineStore.timelineData)
const loading = computed(() => timelineStore.loading)
const error = computed(() => timelineStore.error)
const patient = computed(() => timelineStore.patient)

// Load timeline data on mount
onMounted(async () => {
  await timelineStore.fetchTimeline(patientId.value)
})

// Event handlers
const handleFilterChange = async (filters: TimelineFilters) => {
  await timelineStore.applyFilters(patientId.value, filters)
}

const handleViewModeChange = (mode: ViewMode) => {
  viewMode.value = mode
}

const handleSelectDocument = (documentId: string) => {
  console.log('Document selected:', documentId)
  // TODO: Implement document detail view
}

const handleSelectConcept = (conceptCui: string) => {
  console.log('Concept selected:', conceptCui)
  // TODO: Implement concept detail view
}

const handleExport = async (format: 'pdf' | 'json' | 'fhir') => {
  try {
    const blob = await timelineApi.exportTimeline(
      patientId.value,
      format,
      timelineStore.currentFilters
    )

    // Create download link
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    const extension = format === 'fhir' ? 'json' : format
    const filename = `timeline_${patientId.value}_${new Date().toISOString().split('T')[0]}.${extension}`
    link.setAttribute('download', filename)

    document.body.appendChild(link)
    link.click()

    // Cleanup
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Export failed:', err)
    alert(`Failed to export timeline: ${err}`)
  }
}

const retryLoad = async () => {
  await timelineStore.fetchTimeline(patientId.value)
}
</script>

<style scoped>
.timeline-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 1rem;
}

.timeline-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow: hidden;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  flex: 1;
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #e74c3c;
  margin-bottom: 1rem;
}

button {
  padding: 0.5rem 1rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #2980b9;
}
</style>
