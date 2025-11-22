<template>
  <div class="timeline-chart-container">
    <div v-if="loading" class="loading-state">
      <v-progress-circular indeterminate color="primary" />
      <p>Loading timeline...</p>
    </div>

    <div v-else-if="!timeline" class="empty-state">
      <p>No timeline data available</p>
    </div>

    <div v-else class="timeline-chart">
      <svg
        ref="svgRef"
        :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
        :height="height"
        class="timeline-svg"
      >
        <!-- X-axis (time) -->
        <g ref="xAxisRef" class="x-axis" :transform="`translate(0, ${svgHeight - margin.bottom})`" />

        <!-- Y-axis (document types) -->
        <g ref="yAxisRef" class="y-axis" :transform="`translate(${margin.left}, 0)`" />

        <!-- Zoom container -->
        <g ref="zoomGroupRef" class="zoom-group">
          <!-- Document markers -->
          <circle
            v-for="doc in timeline.documents"
            :key="doc.id"
            :cx="xScale(new Date(doc.document_date))"
            :cy="yScale(doc.type)"
            :r="6"
            :fill="documentColor"
            class="document-marker"
            @click="handleDocumentClick(doc)"
            @mouseenter="showTooltip(doc.title, $event)"
            @mouseleave="hideTooltip()"
          />

          <!-- Concept markers -->
          <circle
            v-for="concept in timeline.concepts"
            :key="concept.concept_cui"
            :cx="xScale(new Date(concept.first_mention_date))"
            :cy="yScale(getConceptType(concept))"
            :r="4"
            :fill="getConceptColor(concept.type)"
            class="concept-marker"
            @click="handleConceptClick(concept)"
            @mouseenter="showTooltip(concept.name, $event)"
            @mouseleave="hideTooltip()"
          />
        </g>
      </svg>

      <!-- Legend -->
      <div class="legend">
        <div v-for="type in conceptTypes" :key="type" class="legend-item">
          <span class="legend-color" :style="{ backgroundColor: getConceptColor(type) }" />
          <span class="legend-label">{{ type }}</span>
        </div>
      </div>

      <!-- Tooltip -->
      <div
        v-if="tooltipVisible"
        class="tooltip"
        :style="{
          left: `${tooltipPosition.x}px`,
          top: `${tooltipPosition.y}px`,
        }"
      >
        {{ tooltipText }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import {
  scaleTime,
  scaleBand,
  axisBottom,
  axisLeft,
  select,
  zoom as d3Zoom,
  zoomIdentity,
  type ZoomBehavior,
} from 'd3'
import type { PatientTimeline, TimelineConcept, TimelineDocument } from '@/types/timeline'

// Props
interface Props {
  timeline: PatientTimeline | null
  loading?: boolean
  height?: number
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  height: 400,
})

// Emits
const emit = defineEmits<{
  'concept-click': [concept: TimelineConcept]
  'document-click': [document: TimelineDocument]
}>()

// Refs
const svgRef = ref<SVGSVGElement | null>(null)
const xAxisRef = ref<SVGGElement | null>(null)
const yAxisRef = ref<SVGGElement | null>(null)
const zoomGroupRef = ref<SVGGElement | null>(null)

// Tooltip state
const tooltipVisible = ref(false)
const tooltipText = ref('')
const tooltipPosition = ref({ x: 0, y: 0 })

// SVG dimensions
const svgWidth = 1000
const svgHeight = computed(() => props.height)
const margin = { top: 20, right: 20, bottom: 50, left: 60 }

// Color scheme for concept types
const conceptColorMap: Record<string, string> = {
  Disease: '#e74c3c',
  Medication: '#3498db',
  Procedure: '#2ecc71',
  Symptom: '#f39c12',
  Test: '#9b59b6',
  Diagnosis: '#e67e22',
  default: '#95a5a6',
}

const documentColor = '#34495e'

// Scales
const xScale = computed(() => {
  if (!props.timeline) return scaleTime()

  const dates = [
    new Date(props.timeline.date_range[0]),
    new Date(props.timeline.date_range[1]),
  ]

  return scaleTime()
    .domain(dates)
    .range([margin.left, svgWidth - margin.right])
})

const yScale = computed(() => {
  if (!props.timeline) return scaleBand()

  const types = Array.from(
    new Set([
      ...props.timeline.documents.map((d) => d.type),
      ...props.timeline.concepts.map((c) => c.type),
    ])
  )

  return scaleBand()
    .domain(types)
    .range([margin.top, svgHeight.value - margin.bottom])
    .padding(0.1)
})

// Computed properties
const conceptTypes = computed(() => {
  if (!props.timeline) return []
  return Array.from(new Set(props.timeline.concepts.map((c) => c.type)))
})

// Methods
function getConceptColor(type: string): string {
  return conceptColorMap[type] || conceptColorMap.default
}

function getConceptType(concept: TimelineConcept): string {
  return concept.type
}

function handleDocumentClick(doc: TimelineDocument) {
  emit('document-click', doc)
}

function handleConceptClick(concept: TimelineConcept) {
  emit('concept-click', concept)
}

function showTooltip(text: string, event: MouseEvent) {
  tooltipText.value = text
  tooltipPosition.value = {
    x: event.clientX + 10,
    y: event.clientY + 10,
  }
  tooltipVisible.value = true
}

function hideTooltip() {
  tooltipVisible.value = false
}

function renderAxes() {
  if (!xAxisRef.value || !yAxisRef.value) return

  // Render X-axis
  select(xAxisRef.value).call(axisBottom(xScale.value).ticks(6))

  // Render Y-axis
  select(yAxisRef.value).call(axisLeft(yScale.value))
}

function setupZoom() {
  if (!svgRef.value || !zoomGroupRef.value) return

  const zoomBehavior: ZoomBehavior<SVGSVGElement, unknown> = d3Zoom<
    SVGSVGElement,
    unknown
  >()
    .scaleExtent([0.5, 10])
    .on('zoom', (event) => {
      if (zoomGroupRef.value) {
        select(zoomGroupRef.value).attr('transform', event.transform)
      }
    })

  select(svgRef.value).call(zoomBehavior).call(zoomBehavior.transform, zoomIdentity)
}

function renderTimeline() {
  nextTick(() => {
    renderAxes()
    setupZoom()
  })
}

// Lifecycle
onMounted(() => {
  if (props.timeline) {
    renderTimeline()
  }
})

// Watch for timeline changes
watch(
  () => props.timeline,
  (newTimeline) => {
    if (newTimeline) {
      renderTimeline()
    }
  },
  { deep: true }
)
</script>

<style scoped>
.timeline-chart-container {
  position: relative;
  width: 100%;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.timeline-svg {
  width: 100%;
  border: 1px solid #ddd;
  background: #fff;
}

.document-marker,
.concept-marker {
  cursor: pointer;
  transition: r 0.2s;
}

.document-marker:hover,
.concept-marker:hover {
  r: 8;
}

.x-axis,
.y-axis {
  font-size: 12px;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 16px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
}

.legend-label {
  font-size: 14px;
}

.tooltip {
  position: fixed;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 14px;
  pointer-events: none;
  z-index: 1000;
  max-width: 300px;
  word-wrap: break-word;
}
</style>
