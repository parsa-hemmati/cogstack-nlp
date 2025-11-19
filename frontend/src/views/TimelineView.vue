<template>
  <v-container fluid class="timeline-view">
    <v-row>
      <v-col cols="12">
        <!-- Toolbar with title and filter button -->
        <div class="d-flex align-center mb-4">
          <h1 class="flex-grow-1">Patient Timeline</h1>

          <v-btn
            icon
            color="primary"
            @click="showFilterSidebar = true"
          >
            <v-badge
              v-if="activeFilterCount > 0"
              :content="activeFilterCount"
              color="error"
            >
              <v-icon>mdi-filter-variant</v-icon>
            </v-badge>
            <v-icon v-else>mdi-filter-variant</v-icon>
          </v-btn>
        </div>

        <!-- Active filter chips -->
        <div v-if="hasActiveFilters" class="mb-3">
          <v-chip
            v-for="(chip, index) in activeFilterChips"
            :key="index"
            closable
            size="small"
            class="mr-2"
            @click:close="removeFilter(chip)"
          >
            {{ chip.label }}
          </v-chip>
        </div>

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
              <TimelineConcepts
                v-if="timeline.concepts"
                :concepts="timeline.concepts"
                :date-range="dateRange"
                :width="svgWidth"
                @concept-click="handleConceptClick"
              />
            </g>
          </svg>

          <!-- Concept popover (shown when concept marker is clicked) -->
          <ConceptPopover
            v-model="showConceptPopover"
            :concept="selectedConcept"
            :position="conceptPopoverPosition"
            @view-document="handleViewDocument"
          />

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

        <!-- Filter Sidebar -->
        <ConceptFilterSidebar
          v-model="showFilterSidebar"
          :patient-id="patientId"
          @filters-applied="handleFiltersApplied"
        />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTimeline } from '@/composables/useTimeline'
import { useTimelineFilters } from '@/composables/useTimelineFilters'
import TimelineAxis from '@/components/timeline/TimelineAxis.vue'
import TimelineDocuments from '@/components/timeline/TimelineDocuments.vue'
import TimelineConcepts from '@/components/TimelineConcepts.vue'
import ConceptPopover from '@/components/ConceptPopover.vue'
import ConceptFilterSidebar from '@/components/ConceptFilterSidebar.vue'
import type { TimelineDocument } from '@/types/timeline'
import type { TimelineFilters } from '@/composables/useTimelineFilters'

/**
 * TimelineView Component
 *
 * Main patient timeline visualization view with integrated filtering.
 * Displays document and concept markers on a temporal axis.
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

// Filter sidebar state
const showFilterSidebar = ref(false)

// Filter composable (for tracking active filters and generating chips)
const patientIdRef = computed(() => patientId.value)
const {
  filters,
  hasActiveFilters,
  activeFilterCount,
  clearFilters,
  setConceptFilter,
  setDateRange,
  setMetaAnnotationFilter,
  setDocumentTypeFilter
} = useTimelineFilters(patientIdRef)

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

// Selected concept (for popover)
const selectedConcept = ref<any>(null)
const showConceptPopover = ref(false)
const conceptPopoverPosition = ref({ x: 0, y: 0 })

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
 * Active filter chips for display.
 * Converts current filters into user-friendly chips.
 */
const activeFilterChips = computed(() => {
  const chips: Array<{ label: string; type: string; value: any }> = []

  // Concept filters
  if (filters.value.conceptCuis.length > 0) {
    for (const cui of filters.value.conceptCuis) {
      chips.push({
        label: `Concept: ${cui}`,
        type: 'concept',
        value: cui
      })
    }
  }

  // Date range filter
  if (filters.value.dateFrom || filters.value.dateTo) {
    const fromStr = filters.value.dateFrom?.toISOString().split('T')[0] || '...'
    const toStr = filters.value.dateTo?.toISOString().split('T')[0] || '...'
    chips.push({
      label: `Date: ${fromStr} to ${toStr}`,
      type: 'dateRange',
      value: null
    })
  }

  // Document type filters
  if (filters.value.documentTypes.length > 0) {
    for (const docType of filters.value.documentTypes) {
      chips.push({
        label: `Type: ${docType.replace('_', ' ')}`,
        type: 'documentType',
        value: docType
      })
    }
  }

  // Meta-annotation filters (only if different from defaults)
  const defaultMeta = { Negation: 'Affirmed', Experiencer: 'Patient', Temporality: ['Current', 'Recent'] }
  if (JSON.stringify(filters.value.metaAnnotations) !== JSON.stringify(defaultMeta)) {
    chips.push({
      label: 'Custom meta-annotations',
      type: 'metaAnnotations',
      value: null
    })
  }

  return chips
})

/**
 * Remove a specific filter chip.
 */
function removeFilter(chip: { label: string; type: string; value: any }) {
  if (chip.type === 'concept') {
    setConceptFilter(filters.value.conceptCuis.filter(c => c !== chip.value))
  } else if (chip.type === 'dateRange') {
    setDateRange(null, null)
  } else if (chip.type === 'documentType') {
    setDocumentTypeFilter(filters.value.documentTypes.filter(t => t !== chip.value))
  } else if (chip.type === 'metaAnnotations') {
    // Reset to defaults
    clearFilters()
  }

  // Re-fetch timeline with updated filters
  refetchTimeline()
}

/**
 * Handle filters applied from sidebar.
 */
async function handleFiltersApplied(appliedFilters: TimelineFilters) {
  // Update filter state
  setConceptFilter(appliedFilters.conceptCuis)
  setDateRange(appliedFilters.dateFrom, appliedFilters.dateTo)
  setDocumentTypeFilter(appliedFilters.documentTypes)

  // Update meta-annotations
  for (const [key, value] of Object.entries(appliedFilters.metaAnnotations)) {
    setMetaAnnotationFilter(key, value)
  }

  // Fetch filtered timeline
  await refetchTimeline()
}

/**
 * Refetch timeline with current filters.
 */
async function refetchTimeline() {
  if (patientId.value) {
    // Build query params from filters
    const params: any = {}

    if (filters.value.conceptCuis.length > 0) {
      params.concepts = filters.value.conceptCuis.join(',')
    }

    if (filters.value.dateFrom) {
      params.date_start = filters.value.dateFrom.toISOString()
    }

    if (filters.value.dateTo) {
      params.date_end = filters.value.dateTo.toISOString()
    }

    // Meta-annotations
    for (const [key, value] of Object.entries(filters.value.metaAnnotations)) {
      const paramKey = `meta_${key.toLowerCase()}`
      params[paramKey] = Array.isArray(value) ? value.join(',') : value
    }

    if (filters.value.documentTypes.length > 0) {
      params.document_types = filters.value.documentTypes.join(',')
    }

    // Fetch with params (useTimeline should be updated to accept params)
    // For now, just refetch
    await fetchTimeline(patientId.value)
  }
}

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
 * Handle concept marker click.
 * Shows popover with concept details.
 */
const handleConceptClick = (mention: any, event: MouseEvent) => {
  selectedConcept.value = mention
  conceptPopoverPosition.value = {
    x: event.clientX,
    y: event.clientY
  }
  showConceptPopover.value = true
}

/**
 * Handle view document request from concept popover.
 * Shows document details in card below timeline.
 */
const handleViewDocument = (documentId: string) => {
  // Find the document in timeline.documents
  if (timeline.value) {
    const doc = timeline.value.documents.find(d => d.documentId === documentId)
    if (doc) {
      selectedDocument.value = doc
      showConceptPopover.value = false
    }
  }
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
