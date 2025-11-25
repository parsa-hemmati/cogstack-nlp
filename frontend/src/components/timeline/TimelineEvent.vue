<template>
  <circle
    :cx="xPosition"
    :cy="yPosition"
    :r="radiusFromConfidence"
    :fill="colorFromType"
    :class="['event-marker', {
      'event-marker--hover': isHovered,
      'event-marker--selected': isSelected
    }]"
    role="button"
    :aria-label="`${event.type}: ${event.name} on ${formatDate(event.date)}`"
    tabindex="0"
    @click="handleClick"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
  >
    <title>{{ tooltipText }}</title>
  </circle>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

/**
 * TimelineEvent Component
 *
 * Individual event marker on the patient timeline.
 * - Color-coded by event type (diagnosis=red, procedure=blue, medication=green, lab=amber, visit=purple)
 * - Size indicates confidence (larger = higher confidence)
 * - Click to emit event-click
 * - Hover to emit event-hover
 *
 * @example
 * <TimelineEvent
 *   :event="{ id: '1', type: 'diagnosis', name: 'Diabetes', date: '2023-06-15', confidence: 0.95 }"
 *   :x-position="100"
 *   :y-position="50"
 *   @event-click="handleEventClick"
 *   @event-hover="handleEventHover"
 * />
 */

export interface TimelineEventData {
  id: string
  type: 'diagnosis' | 'procedure' | 'medication' | 'lab' | 'visit' | string
  name: string
  date: string  // ISO 8601 timestamp
  confidence: number  // 0-1 range
}

interface Props {
  event: TimelineEventData
  xPosition: number
  yPosition: number
  isSelected?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isSelected: false
})

const emit = defineEmits<{
  'event-click': [event: TimelineEventData]
  'event-hover': [event: TimelineEventData | null, mouseEvent?: MouseEvent | null]
}>()

// Local hover state for visual feedback
const isHovered = ref(false)

/**
 * Event type color mapping
 * As specified in task requirements
 */
const eventColors: Record<string, string> = {
  diagnosis: '#ef4444',    // red
  procedure: '#3b82f6',    // blue
  medication: '#10b981',   // green
  lab: '#f59e0b',          // amber
  visit: '#8b5cf6',        // purple
}

/**
 * Get color for event type
 * Returns default gray for unknown types
 */
const colorFromType = computed(() => {
  return eventColors[props.event.type] || '#6b7280'  // gray for unknown
})

/**
 * Get radius based on confidence level
 * - High confidence (>0.9): 8px
 * - Medium confidence (0.7-0.9): 6px
 * - Low confidence (<0.7): 4px
 */
const radiusFromConfidence = computed(() => {
  const confidence = props.event.confidence
  if (confidence > 0.9) return 8
  if (confidence >= 0.7) return 6
  return 4
})

/**
 * Format date for display
 * Example: "Jun 15, 2023"
 */
const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

/**
 * Tooltip text for accessibility and visual tooltip
 */
const tooltipText = computed(() => {
  const date = formatDate(props.event.date)
  const confidence = Math.round(props.event.confidence * 100)
  return `${props.event.name}\n${date}\n${confidence}% confidence\n(${props.event.type})`
})

/**
 * Handle click event
 */
const handleClick = (e?: Event) => {
  // Prevent default for keyboard events (especially space)
  if (e) {
    e.preventDefault()
  }
  emit('event-click', props.event)
}

/**
 * Handle mouse enter
 */
const handleMouseEnter = (e: MouseEvent) => {
  isHovered.value = true
  emit('event-hover', props.event, e)
}

/**
 * Handle mouse leave
 */
const handleMouseLeave = () => {
  isHovered.value = false
  emit('event-hover', null, null)
}
</script>

<style scoped>
.event-marker {
  cursor: pointer;
  stroke: #fff;
  stroke-width: 2;
  transition: all 0.2s ease;
}

.event-marker:hover {
  stroke-width: 3;
  filter: brightness(1.1);
}

.event-marker:focus {
  outline: none;
  stroke: #000;
  stroke-width: 3;
}

.event-marker--hover {
  stroke-width: 3;
  filter: brightness(1.1);
}

.event-marker--selected {
  stroke: #000;
  stroke-width: 3;
  filter: brightness(1.2);
}
</style>
