<template>
  <v-container fluid class="timeline-view">
    <v-row>
      <v-col cols="12">
        <h1>Patient Timeline</h1>

        <v-progress-linear v-if="isLoading" indeterminate color="primary" />

        <v-alert v-if="error" type="error" closable @click:close="clearError">
          {{ error }}
        </v-alert>

        <div v-if="timeline && !isLoading" class="timeline-container">
          <svg :width="svgWidth" :height="svgHeight" class="timeline-svg">
            <TimelineAxis
              :date-range="dateRange"
              :width="svgWidth"
              :height="axisHeight"
            />
            <g :transform="`translate(0, ${axisHeight})`">
              <TimelineDocuments
                :documents="timeline.documents"
                :date-range="dateRange"
                :width="svgWidth"
                :document-y="documentY"
                @document-click="handleDocumentClick"
                @document-hover="handleDocumentHover"
              />
            </g>
          </svg>

          <!-- Document details (shown when document is clicked) -->
          <v-card v-if="selectedDocument" class="mt-4">
            <v-card-title>{{ selectedDocument.title }}</v-card-title>
            <v-card-text>
              <p><strong>Type:</strong> {{ selectedDocument.documentType }}</p>
              <p><strong>Date:</strong> {{ formatDate(selectedDocument.date) }}</p>
              <p v-if="selectedDocument.author"><strong>Author:</strong> {{ selectedDocument.author }}</p>
              <p><strong>Concepts:</strong> {{ selectedDocument.concepts.length }}</p>
            </v-card-text>
            <v-card-actions>
              <v-btn @click="selectedDocument = null">Close</v-btn>
            </v-card-actions>
          </v-card>

          <!-- Tooltip (shown when hovering over document) -->
          <div
            v-if="hoveredDocument"
            class="document-tooltip"
            :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }"
          >
            <strong>{{ hoveredDocument.title }}</strong>
            <br />
            {{ formatDate(hoveredDocument.date) }}
          </div>
        </div>

        <v-alert v-if="isEmpty" type="info">
          No timeline data available for this patient.
        </v-alert>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTimeline } from '@/composables/useTimeline'
import TimelineAxis from '@/components/timeline/TimelineAxis.vue'
import TimelineDocuments from '@/components/timeline/TimelineDocuments.vue'
import type { TimelineDocument } from '@/types/timeline'

/**
 * TimelineView Component
 *
 * Main patient timeline visualization view.
 * Displays document markers on a temporal axis.
 *
 * Route: /timeline/:patientId
 */

const route = useRoute()
const patientId = computed(() => route.params.patientId as string)

const {
  timeline,
  isLoading,
  error,
  isEmpty,
  fetchTimeline,
  clearError
} = useTimeline()

// SVG dimensions
const svgWidth = 1200
const svgHeight = 600
const axisHeight = 100
const documentY = 50

// Selected document (for detail view)
const selectedDocument = ref<TimelineDocument | null>(null)

// Hovered document (for tooltip)
const hoveredDocument = ref<TimelineDocument | null>(null)
const tooltipX = ref(0)
const tooltipY = ref(0)

/**
 * Date range computed from timeline data.
 * Converts string dates to Date objects for components.
 */
const dateRange = computed(() => {
  if (!timeline.value) {
    return { start: new Date(), end: new Date() }
  }
  return {
    start: new Date(timeline.value.dateRange.start),
    end: new Date(timeline.value.dateRange.end)
  }
})

/**
 * Handle document marker click.
 * Shows document details in card below timeline.
 */
const handleDocumentClick = (doc: TimelineDocument) => {
  selectedDocument.value = doc
}

/**
 * Handle document marker hover.
 * Shows tooltip with document title and date.
 */
const handleDocumentHover = (doc: TimelineDocument | null, event: MouseEvent | null) => {
  hoveredDocument.value = doc
  if (event) {
    tooltipX.value = event.clientX + 10
    tooltipY.value = event.clientY + 10
  }
}

/**
 * Format date for display.
 */
const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * Fetch timeline data on mount.
 */
onMounted(async () => {
  if (patientId.value) {
    await fetchTimeline(patientId.value)
  }
})
</script>

<style scoped>
.timeline-view {
  padding: 24px;
}

.timeline-container {
  margin-top: 24px;
  position: relative;
}

.timeline-svg {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background: #fafafa;
}

.document-tooltip {
  position: fixed;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 14px;
  pointer-events: none;
  z-index: 1000;
  white-space: nowrap;
}
</style>
