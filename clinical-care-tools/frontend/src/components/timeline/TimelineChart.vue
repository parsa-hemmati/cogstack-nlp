<template>
  <v-card variant="outlined" class="mb-4">
    <v-card-title class="text-subtitle-1">Activity Overview</v-card-title>
    <v-card-text>
      <div v-if="!chartData.length" class="text-center py-4 text-grey">
        No activity data available
      </div>
      
      <div v-else class="chart-container d-flex align-end justify-space-between px-2 pt-4 pb-2">
        <div 
           v-for="(item, idx) in chartData" 
           :key="idx" 
           class="bar-group d-flex flex-column align-center"
           style="flex: 1; min-width: 40px;"
        >
          <div 
             class="bar bg-primary rounded-t" 
             :style="{ height: `${item.percent}%`, width: '20px', minHeight: '4px' }"
             :title="`${item.count} documents in ${item.label}`"
          ></div>
          <div class="label text-caption text-grey mt-1 text-truncate" style="max-width: 60px;">
            {{ item.label }}
          </div>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TimelineDocument } from '@/types/timeline'

const props = defineProps<{
  documents: TimelineDocument[]
}>()

const chartData = computed(() => {
  if (!props.documents || !props.documents.length) return []

  // Find min and max date
  const dates = props.documents.map(d => new Date(d.date).getTime())
  const minDate = Math.min(...dates)
  const maxDate = Math.max(...dates)
  
  if (minDate === Infinity) return []

  const stats: { label: string, count: number, date: number }[] = []
  
  // Buckets by month
  let current = new Date(minDate)
  current.setDate(1) // Start of month
  const end = new Date(maxDate)
  
  while (current <= end || (current.getMonth() === end.getMonth() && current.getFullYear() === end.getFullYear())) {
      const key = current.toLocaleString('default', { month: 'short', year: '2-digit' })
      // Count docs in this month
      // Note: working with dates in JS is tricky for strict equality, checking Month/Year is safer
      const currentMonth = current.getMonth()
      const currentYear = current.getFullYear()
      
      const count = props.documents.filter(d => {
          const docDate = new Date(d.date)
          return docDate.getMonth() === currentMonth && docDate.getFullYear() === currentYear
      }).length
      
      stats.push({ label: key, count, date: current.getTime() })
      
      // Next month
      current.setMonth(current.getMonth() + 1)
  }
  
  const maxCount = Math.max(...stats.map(s => s.count)) || 1
  
  return stats.map(s => ({
      ...s,
      percent: (s.count / maxCount) * 100
  }))
})
</script>

<style scoped>
.chart-container {
    height: 150px;
    border-bottom: 1px solid #e0e0e0;
    overflow-x: auto;
}
.bar {
    transition: height 0.3s ease;
}
.bar:hover {
    opacity: 0.8;
}
</style>
