<template>
  <g class="timeline-documents">
    <circle
      v-for="doc in documents"
      :key="doc.documentId"
      :cx="getXPosition(doc.date)"
      :cy="documentY"
      :r="5"
      class="document-marker"
      :class="{ 'document-marker--selected': selectedDocId === doc.documentId }"
      @click="handleDocumentClick(doc)"
      @mouseenter="handleMouseEnter(doc, $event)"
      @mouseleave="handleMouseLeave"
    />
  </g>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import * as d3 from 'd3'
import type { TimelineDocument } from '@/types/timeline'

/**
 * TimelineDocuments Component
 *
 * Renders document markers on the patient timeline visualization.
 * Each document is represented as a circular marker positioned by date.
 *
 * @example
 * <TimelineDocuments
 *   :documents="timelineData.documents"
 *   :date-range="{ start: new Date('2023-01-01'), end: new Date('2023-12-31') }"
 *   :width="800"
 *   :document-y="50"
 *   @document-click="handleClick"
 *   @document-hover="handleHover"
 * />
 */

interface Props {
  documents: TimelineDocument[]
  dateRange: { start: Date; end: Date }
  width: number
  documentY: number
}

const props = withDefaults(defineProps<Props>(), {
  documentY: 50
})

const emit = defineEmits<{
  documentClick: [doc: TimelineDocument]
  documentHover: [doc: TimelineDocument | null, event: MouseEvent | null]
}>()

const selectedDocId = ref<string | null>(null)

/**
 * D3 time scale for positioning documents by date.
 * Maps date domain to pixel range with 50px padding.
 */
const xScale = computed(() => {
  return d3.scaleTime()
    .domain([props.dateRange.start, props.dateRange.end])
    .range([50, props.width - 50])
})

/**
 * Get X position for a document based on its date.
 *
 * @param dateStr - ISO 8601 date string
 * @returns X coordinate in pixels
 */
const getXPosition = (dateStr: string): number => {
  const date = new Date(dateStr)
  return xScale.value(date)
}

/**
 * Handle document marker click.
 * Emits documentClick event and sets selected state.
 */
const handleDocumentClick = (doc: TimelineDocument) => {
  selectedDocId.value = doc.documentId
  emit('documentClick', doc)
}

/**
 * Handle mouse enter on document marker.
 * Emits documentHover event with document and mouse event.
 */
const handleMouseEnter = (doc: TimelineDocument, event: MouseEvent) => {
  emit('documentHover', doc, event)
}

/**
 * Handle mouse leave on document marker.
 * Emits documentHover event with null to hide tooltip.
 */
const handleMouseLeave = () => {
  emit('documentHover', null, null)
}
</script>

<style scoped>
.timeline-documents {
  /* No additional styles needed for group */
}

.document-marker {
  fill: #1976d2;
  cursor: pointer;
  transition: all 0.2s ease;
}

.document-marker:hover {
  fill: #1565c0;
  r: 7;
}

.document-marker--selected {
  fill: #0d47a1;
  stroke: #fff;
  stroke-width: 2;
}
</style>
