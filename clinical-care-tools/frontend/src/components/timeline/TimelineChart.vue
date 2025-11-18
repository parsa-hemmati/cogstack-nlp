<template>
  <div class="timeline-chart" ref="chartContainer">
    <!-- Chart will be rendered here by D3 -->
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import type { TimelineResponse, ViewMode } from '@/types/timeline'
import { useTimelineChart, DEFAULT_CHART_OPTIONS } from '@/composables/useTimelineChart'
import * as d3 from 'd3'

// Props
interface Props {
  timelineData: TimelineResponse
  viewMode: ViewMode
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  selectDocument: [documentId: string]
  selectConcept: [conceptCui: string]
}>()

// Refs
const chartContainer = ref<HTMLDivElement | null>(null)

// D3 chart composable
const {
  createSvg,
  createTimeScale,
  createYScale,
  renderXAxis,
  renderDocuments,
  renderConcepts,
  addZoomBehavior,
} = useTimelineChart()

// Chart state
let svg: d3.Selection<SVGSVGElement, unknown, null, undefined> | null = null
let xScale: d3.ScaleTime<number, number> | null = null
let yScale: d3.ScaleLinear<number, number> | null = null
let currentTransform: d3.ZoomTransform = d3.zoomIdentity

// Initialize chart on mount
onMounted(() => {
  nextTick(() => {
    initializeChart()
  })
})

// Watch for data changes
watch(() => props.timelineData, () => {
  updateChart()
}, { deep: true })

// Watch for view mode changes
watch(() => props.viewMode, () => {
  updateChart()
})

/**
 * Initialize chart structure
 */
const initializeChart = () => {
  if (!chartContainer.value) return

  // Get container dimensions
  const containerRect = chartContainer.value.getBoundingClientRect()
  const options = {
    ...DEFAULT_CHART_OPTIONS,
    width: containerRect.width,
    height: Math.max(containerRect.height, 500),
  }

  // Create SVG
  svg = createSvg(chartContainer.value, options)

  // Create scales
  if (props.timelineData) {
    xScale = createTimeScale(
      props.timelineData,
      options.width,
      options.margin
    )
    yScale = createYScale(options.height, options.margin)

    // Render chart
    renderChart()
  }
}

/**
 * Update chart with new data
 */
const updateChart = () => {
  if (!svg || !chartContainer.value) {
    initializeChart()
    return
  }

  // Clear existing content
  svg.selectAll('*').remove()

  // Recreate scales with new data
  const containerRect = chartContainer.value.getBoundingClientRect()
  const options = {
    ...DEFAULT_CHART_OPTIONS,
    width: containerRect.width,
    height: Math.max(containerRect.height, 500),
  }

  xScale = createTimeScale(
    props.timelineData,
    options.width,
    options.margin
  )
  yScale = createYScale(options.height, options.margin)

  // Render chart
  renderChart()
}

/**
 * Render chart elements
 */
const renderChart = () => {
  if (!svg || !xScale || !yScale || !chartContainer.value) return

  const containerRect = chartContainer.value.getBoundingClientRect()
  const options = {
    ...DEFAULT_CHART_OPTIONS,
    width: containerRect.width,
    height: Math.max(containerRect.height, 500),
  }

  // Render X-axis
  renderXAxis(svg, xScale, options.height, options.margin)

  // Render based on view mode
  const showDocuments = props.viewMode === 'documents' || props.viewMode === 'combined'
  const showConcepts = props.viewMode === 'concepts' || props.viewMode === 'combined'

  // Document markers position
  const documentY = 100

  // Concept bars position
  const conceptStartY = 200
  const conceptBarHeight = 20

  if (showDocuments && props.timelineData.documents.length > 0) {
    renderDocuments(
      svg,
      props.timelineData.documents,
      xScale,
      documentY,
      handleDocumentSelect
    )

    // Add document label
    svg
      .append('text')
      .attr('x', options.margin.left - 10)
      .attr('y', documentY)
      .attr('text-anchor', 'end')
      .attr('alignment-baseline', 'middle')
      .style('font-size', '12px')
      .style('font-weight', 'bold')
      .text('Documents')
  }

  if (showConcepts && props.timelineData.concepts.length > 0) {
    renderConcepts(
      svg,
      props.timelineData.concepts,
      xScale,
      conceptStartY,
      conceptBarHeight,
      handleConceptSelect
    )

    // Add concept labels
    const conceptTypes = ['condition', 'medication', 'procedure', 'observation']
    conceptTypes.forEach((type, index) => {
      const y = conceptStartY + index * (conceptBarHeight + 5)
      svg!
        .append('text')
        .attr('x', options.margin.left - 10)
        .attr('y', y + conceptBarHeight / 2)
        .attr('text-anchor', 'end')
        .attr('alignment-baseline', 'middle')
        .style('font-size', '11px')
        .style('font-weight', 'bold')
        .style('text-transform', 'capitalize')
        .text(type)
    })
  }

  // Add zoom behavior
  addZoomBehavior(svg, xScale, handleZoom)

  // Add title
  svg
    .append('text')
    .attr('x', options.width / 2)
    .attr('y', options.margin.top / 2)
    .attr('text-anchor', 'middle')
    .style('font-size', '16px')
    .style('font-weight', 'bold')
    .text('Patient Timeline')

  // Add legend
  renderLegend(svg, options)
}

/**
 * Render legend
 */
const renderLegend = (
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  options: typeof DEFAULT_CHART_OPTIONS
) => {
  const legendData = [
    { type: 'clinical_note', label: 'Clinical Note', color: '#3498db' },
    { type: 'lab_result', label: 'Lab Result', color: '#2ecc71' },
    { type: 'discharge_summary', label: 'Discharge Summary', color: '#e74c3c' },
    { type: 'radiology_report', label: 'Radiology Report', color: '#f39c12' },
  ]

  const legend = svg
    .append('g')
    .attr('class', 'legend')
    .attr('transform', `translate(${options.width - options.margin.right - 200}, ${options.margin.top})`)

  legendData.forEach((item, index) => {
    const legendItem = legend
      .append('g')
      .attr('transform', `translate(0, ${index * 20})`)

    legendItem
      .append('circle')
      .attr('cx', 0)
      .attr('cy', 0)
      .attr('r', 6)
      .attr('fill', item.color)

    legendItem
      .append('text')
      .attr('x', 12)
      .attr('y', 0)
      .attr('alignment-baseline', 'middle')
      .style('font-size', '11px')
      .text(item.label)
  })
}

/**
 * Handle zoom event
 */
const handleZoom = (transform: d3.ZoomTransform) => {
  if (!svg || !xScale) return

  currentTransform = transform

  // Update x-scale with zoom transform
  const newXScale = transform.rescaleX(xScale)

  // Re-render X-axis
  svg.select('.x-axis').remove()
  if (chartContainer.value) {
    const containerRect = chartContainer.value.getBoundingClientRect()
    const options = {
      ...DEFAULT_CHART_OPTIONS,
      width: containerRect.width,
      height: Math.max(containerRect.height, 500),
    }
    renderXAxis(svg, newXScale, options.height, options.margin)
  }

  // Update document positions
  svg
    .selectAll('.document-marker')
    .attr('cx', (d: any) => newXScale(new Date(d.date)))

  // Update concept bar positions and widths
  svg
    .selectAll('.concept-marker')
    .attr('x', (d: any) => newXScale(new Date(d.firstMentioned)))
    .attr('width', (d: any) => {
      const start = newXScale(new Date(d.firstMentioned))
      const end = newXScale(new Date(d.lastMentioned))
      return Math.max(end - start, 4)
    })
}

/**
 * Handle document selection
 */
const handleDocumentSelect = (document: any) => {
  emit('selectDocument', document.id)
}

/**
 * Handle concept selection
 */
const handleConceptSelect = (concept: any) => {
  emit('selectConcept', concept.cui)
}
</script>

<style scoped>
.timeline-chart {
  width: 100%;
  height: 100%;
  min-height: 500px;
  background-color: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

/* D3 axis styling */
:deep(.x-axis) path,
:deep(.x-axis) line {
  stroke: #666;
}

:deep(.x-axis) text {
  fill: #666;
}

:deep(.y-axis) path,
:deep(.y-axis) line {
  stroke: #666;
}

:deep(.y-axis) text {
  fill: #666;
}

/* Marker styling */
:deep(.document-marker) {
  transition: all 0.2s;
}

:deep(.concept-marker) {
  transition: all 0.2s;
}
</style>
