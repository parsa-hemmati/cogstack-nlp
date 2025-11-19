<template>
  <div class="concept-frequency-chart">
    <svg ref="chartSvg" :width="width" :height="height" class="frequency-chart-svg">
      <g ref="chartGroup" class="chart-content">
        <!-- Bars will be rendered here by D3 -->
        <g class="bars"></g>

        <!-- X-axis -->
        <g ref="xAxisGroup" class="x-axis" :transform="`translate(0, ${height - margin.bottom})`"></g>

        <!-- Y-axis -->
        <g ref="yAxisGroup" class="y-axis" :transform="`translate(${margin.left}, 0)`"></g>
      </g>
    </svg>

    <!-- Tooltip -->
    <div
      v-if="tooltip.show"
      class="chart-tooltip"
      :style="{
        left: `${tooltip.x}px`,
        top: `${tooltip.y}px`
      }"
    >
      <div class="tooltip-title">{{ tooltip.title }}</div>
      <div class="tooltip-details">
        <div v-for="(item, index) in tooltip.items" :key="index" class="tooltip-item">
          <span class="tooltip-color" :style="{ backgroundColor: item.color }"></span>
          {{ item.label }}: {{ item.count }}
        </div>
      </div>
      <div class="tooltip-total">Total: {{ tooltip.total }} mentions</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import * as d3 from 'd3'
import type { TimelineConcept } from '@/types/timeline'

/**
 * ConceptFrequencyChart Component
 *
 * Renders a D3.js stacked bar chart showing concept mention frequency over time.
 * Aggregates mentions into time bins (month/quarter/year) and visualizes patterns.
 *
 * @example
 * <ConceptFrequencyChart
 *   :concepts="timelineConcepts"
 *   :date-range="{ start: new Date('2023-01-01'), end: new Date('2023-12-31') }"
 *   :width="800"
 *   :height="150"
 *   bin-size="month"
 * />
 */

interface Props {
  concepts: TimelineConcept[]
  dateRange: { start: Date; end: Date }
  width: number
  height?: number
  binSize?: 'month' | 'quarter' | 'year'
}

const props = withDefaults(defineProps<Props>(), {
  height: 150,
  binSize: 'month'
})

const chartSvg = ref<SVGSVGElement | null>(null)
const chartGroup = ref<SVGGElement | null>(null)
const xAxisGroup = ref<SVGGElement | null>(null)
const yAxisGroup = ref<SVGGElement | null>(null)

const margin = { top: 20, right: 20, bottom: 40, left: 50 }

const tooltip = ref({
  show: false,
  x: 0,
  y: 0,
  title: '',
  items: [] as Array<{ label: string; count: number; color: string }>,
  total: 0
})

/**
 * Aggregate concept mentions into time bins
 */
const aggregatedData = computed(() => {
  if (!props.concepts || props.concepts.length === 0) return []

  // Create time bins based on binSize
  const bins: Map<string, Map<string, number>> = new Map()

  // Extract all mentions from all concepts
  for (const concept of props.concepts) {
    for (const mention of concept.mentions) {
      const date = new Date(mention.date)
      const binKey = getBinKey(date)

      if (!bins.has(binKey)) {
        bins.set(binKey, new Map())
      }

      const typeCounts = bins.get(binKey)!
      const currentCount = typeCounts.get(concept.concept_type) || 0
      typeCounts.set(concept.concept_type, currentCount + 1)
    }
  }

  // Convert to array format for D3
  const result = Array.from(bins.entries()).map(([binKey, typeCounts]) => {
    const binData: any = {
      bin: binKey,
      date: parseBinKey(binKey),
      total: 0
    }

    // Add counts for each concept type
    for (const [type, count] of typeCounts.entries()) {
      binData[type] = count
      binData.total += count
    }

    return binData
  })

  // Sort by date
  result.sort((a, b) => a.date.getTime() - b.date.getTime())

  return result
})

/**
 * Get unique concept types from data
 */
const conceptTypes = computed(() => {
  const types = new Set<string>()
  for (const concept of props.concepts) {
    types.add(concept.concept_type)
  }
  return Array.from(types)
})

/**
 * Get bin key for a date based on binSize
 */
const getBinKey = (date: Date): string => {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const quarter = Math.ceil(month / 3)

  switch (props.binSize) {
    case 'year':
      return `${year}`
    case 'quarter':
      return `${year}-Q${quarter}`
    case 'month':
    default:
      return `${year}-${String(month).padStart(2, '0')}`
  }
}

/**
 * Parse bin key back to Date
 */
const parseBinKey = (binKey: string): Date => {
  if (binKey.includes('Q')) {
    // Quarter format: "2023-Q1"
    const [year, quarter] = binKey.split('-Q')
    const month = (parseInt(quarter) - 1) * 3
    return new Date(parseInt(year), month, 1)
  } else if (binKey.includes('-')) {
    // Month format: "2023-01"
    const [year, month] = binKey.split('-')
    return new Date(parseInt(year), parseInt(month) - 1, 1)
  } else {
    // Year format: "2023"
    return new Date(parseInt(binKey), 0, 1)
  }
}

/**
 * Get color for concept type
 */
const getConceptColor = (conceptType: string): string => {
  const colors: Record<string, string> = {
    condition: '#f44336',
    medication: '#2196f3',
    procedure: '#4caf50',
    symptom: '#ffeb3b',
    lab_result: '#9c27b0'
  }
  return colors[conceptType] || '#757575'
}

/**
 * Format bin label for X-axis
 */
const formatBinLabel = (binKey: string): string => {
  if (binKey.includes('Q')) {
    return binKey // "2023-Q1"
  } else if (binKey.includes('-')) {
    const [year, month] = binKey.split('-')
    const date = new Date(parseInt(year), parseInt(month) - 1, 1)
    return d3.timeFormat('%b %Y')(date) // "Jan 2023"
  } else {
    return binKey // "2023"
  }
}

/**
 * Render the bar chart using D3
 */
const renderChart = () => {
  if (!chartGroup.value || !xAxisGroup.value || !yAxisGroup.value) return
  if (aggregatedData.value.length === 0) return

  const chartWidth = props.width - margin.left - margin.right
  const chartHeight = props.height - margin.top - margin.bottom

  // Create scales
  const xScale = d3.scaleBand()
    .domain(aggregatedData.value.map(d => d.bin))
    .range([margin.left, props.width - margin.right])
    .padding(0.2)

  const yScale = d3.scaleLinear()
    .domain([0, d3.max(aggregatedData.value, d => d.total) || 0])
    .range([chartHeight, margin.top])
    .nice()

  // Create stack generator
  const stack = d3.stack()
    .keys(conceptTypes.value)
    .value((d: any, key: string) => d[key] || 0)

  const stackedData = stack(aggregatedData.value)

  // Render bars
  const barsGroup = d3.select(chartGroup.value).select('.bars')
  barsGroup.selectAll('*').remove()

  // Create a group for each concept type
  const layers = barsGroup.selectAll('.layer')
    .data(stackedData)
    .join('g')
    .attr('class', 'layer')
    .attr('fill', d => getConceptColor(d.key))

  // Create rectangles for each bar segment
  layers.selectAll('rect')
    .data(d => d)
    .join('rect')
    .attr('x', (d: any) => xScale(d.data.bin) || 0)
    .attr('y', d => yScale(d[1]))
    .attr('height', d => yScale(d[0]) - yScale(d[1]))
    .attr('width', xScale.bandwidth())
    .on('mouseenter', (event, d: any) => {
      // Calculate tooltip data
      const binData = d.data
      const items = conceptTypes.value
        .filter(type => binData[type] > 0)
        .map(type => ({
          label: type.replace('_', ' ').charAt(0).toUpperCase() + type.slice(1).replace('_', ' '),
          count: binData[type],
          color: getConceptColor(type)
        }))

      tooltip.value = {
        show: true,
        x: event.clientX + 10,
        y: event.clientY - 10,
        title: formatBinLabel(binData.bin),
        items,
        total: binData.total
      }
    })
    .on('mouseleave', () => {
      tooltip.value.show = false
    })

  // Render X-axis
  const xAxis = d3.axisBottom(xScale)
    .tickFormat(formatBinLabel)

  d3.select(xAxisGroup.value)
    .selectAll('*')
    .remove()

  d3.select(xAxisGroup.value)
    .call(xAxis as any)
    .selectAll('text')
    .attr('transform', 'rotate(-45)')
    .style('text-anchor', 'end')

  // Render Y-axis
  const yAxis = d3.axisLeft(yScale)
    .ticks(5)

  d3.select(yAxisGroup.value)
    .selectAll('*')
    .remove()

  d3.select(yAxisGroup.value)
    .call(yAxis as any)
}

// Render chart on mount and when data changes
onMounted(async () => {
  await nextTick()
  renderChart()
})

watch([() => props.concepts, () => props.dateRange, () => props.binSize, () => props.width, () => props.height],
  async () => {
    await nextTick()
    renderChart()
  },
  { deep: true }
)
</script>

<style scoped>
.concept-frequency-chart {
  position: relative;
  background: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 10px;
}

.frequency-chart-svg {
  overflow: visible;
}

.frequency-chart-svg :deep(.x-axis path),
.frequency-chart-svg :deep(.y-axis path) {
  stroke: #666;
}

.frequency-chart-svg :deep(.x-axis line),
.frequency-chart-svg :deep(.y-axis line) {
  stroke: #ccc;
}

.frequency-chart-svg :deep(.x-axis text),
.frequency-chart-svg :deep(.y-axis text) {
  fill: #333;
  font-size: 11px;
}

.frequency-chart-svg :deep(.bars rect) {
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.frequency-chart-svg :deep(.bars rect:hover) {
  opacity: 0.8;
}

.chart-tooltip {
  position: fixed;
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 8px 12px;
  pointer-events: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 150px;
}

.tooltip-title {
  font-weight: 600;
  margin-bottom: 6px;
  font-size: 12px;
}

.tooltip-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  margin-bottom: 2px;
}

.tooltip-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.tooltip-total {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid #e0e0e0;
  font-weight: 600;
  font-size: 11px;
}
</style>
