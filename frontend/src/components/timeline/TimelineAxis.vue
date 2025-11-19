<template>
  <svg ref="axisSvg" :width="width" :height="height" class="timeline-axis">
    <g ref="axisGroup" :transform="`translate(0, ${height / 2})`"></g>
  </svg>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as d3 from 'd3'

/**
 * TimelineAxis Component
 *
 * Renders a D3.js time axis for the patient timeline visualization.
 * Displays month/year labels along a horizontal timeline.
 *
 * @example
 * <TimelineAxis
 *   :date-range="{ start: new Date('2023-01-01'), end: new Date('2023-12-31') }"
 *   :width="800"
 *   :height="60"
 * />
 */

interface Props {
  dateRange: { start: Date; end: Date }
  width: number
  height: number
}

const props = withDefaults(defineProps<Props>(), {
  width: 800,
  height: 60
})

const axisSvg = ref<SVGSVGElement | null>(null)
const axisGroup = ref<SVGGElement | null>(null)

/**
 * Render the D3 time axis.
 *
 * Creates a time scale from dateRange and renders axis with month/year labels.
 * Updates existing axis if already rendered.
 */
const renderAxis = () => {
  if (!axisGroup.value) return

  // Create time scale
  const xScale = d3.scaleTime()
    .domain([props.dateRange.start, props.dateRange.end])
    .range([50, props.width - 50]) // 50px padding on each side

  // Create axis with month/year format
  const xAxis = d3.axisBottom(xScale)
    .ticks(10)
    .tickFormat(d3.timeFormat('%b %Y') as any)

  // Clear previous axis and render new one
  const axisSelection = d3.select(axisGroup.value)
  axisSelection.selectAll('*').remove()
  axisSelection.call(xAxis as any)
}

// Render axis on mount
onMounted(() => {
  renderAxis()
})

// Re-render axis when dateRange changes
watch(() => props.dateRange, renderAxis, { deep: true })

// Re-render axis when width changes
watch(() => props.width, renderAxis)
</script>

<style scoped>
.timeline-axis {
  overflow: visible;
}

.timeline-axis :deep(path),
.timeline-axis :deep(line) {
  stroke: #666;
  shape-rendering: crispEdges;
}

.timeline-axis :deep(text) {
  fill: #333;
  font-size: 12px;
  font-family: Arial, sans-serif;
}

.timeline-axis :deep(.domain) {
  stroke: #999;
}

.timeline-axis :deep(.tick line) {
  stroke: #ccc;
}
</style>
