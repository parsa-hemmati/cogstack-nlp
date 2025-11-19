<template>
  <g class="concepts">
    <circle
      v-for="(mention, index) in allMentions"
      :key="`${mention.concept_cui}-${index}`"
      :cx="xScale(new Date(mention.date))"
      :cy="conceptY(mention.concept_type)"
      :r="mention.is_first_mention ? 8 : 4"
      :fill="conceptColor(mention.concept_type)"
      class="concept-marker"
      @click="$emit('concept-click', mention, $event)"
    />
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as d3 from 'd3'
import type { TimelineConcept } from '@/types/timeline'

const props = defineProps<{
  concepts: TimelineConcept[]
  dateRange: { start: Date; end: Date }
  width: number
}>()

const emit = defineEmits<{
  conceptClick: [mention: any, event: MouseEvent]
}>()

const xScale = computed(() => {
  return d3.scaleTime()
    .domain([props.dateRange.start, props.dateRange.end])
    .range([50, props.width - 50])
})

const allMentions = computed(() => {
  const mentions = []
  for (const concept of props.concepts) {
    for (let i = 0; i < concept.mentions.length; i++) {
      mentions.push({
        ...concept.mentions[i],
        concept_cui: concept.concept_cui,
        concept_name: concept.concept_name,
        concept_type: concept.concept_type,
        is_first_mention: i === 0
      })
    }
  }
  return mentions
})

const conceptY = (conceptType: string) => {
  const yPositions: Record<string, number> = {
    condition: 300,
    medication: 350,
    procedure: 400,
    symptom: 450,
    lab_result: 500
  }
  return yPositions[conceptType] || 400
}

const conceptColor = (conceptType: string) => {
  const colors: Record<string, string> = {
    condition: '#f44336',
    medication: '#2196f3',
    procedure: '#4caf50',
    symptom: '#ffeb3b',
    lab_result: '#9c27b0'
  }
  return colors[conceptType] || '#757575'
}
</script>

<style scoped>
.concept-marker {
  cursor: pointer;
  stroke: #fff;
  stroke-width: 1;
}
.concept-marker:hover {
  stroke-width: 2;
}
</style>
