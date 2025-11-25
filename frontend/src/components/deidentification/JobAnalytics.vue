<template>
  <v-container>
    <v-row>
      <!-- Summary cards -->
      <v-col cols="12" md="3">
        <v-card>
          <v-card-title class="text-subtitle-2">Total Jobs</v-card-title>
          <v-card-text>
            <h2>{{ analytics.total_jobs }}</h2>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-title class="text-subtitle-2">Success Rate</v-card-title>
          <v-card-text>
            <h2>{{ analytics.success_rate }}%</h2>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-title class="text-subtitle-2">Avg. Processing Time</v-card-title>
          <v-card-text>
            <h2>{{ formatTime(analytics.avg_processing_time) }}</h2>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-title class="text-subtitle-2">Total Notes</v-card-title>
          <v-card-text>
            <h2>{{ analytics.total_notes.toLocaleString() }}</h2>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <!-- PHI Distribution -->
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title class="text-subtitle-1">PHI Entity Distribution</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item
                v-for="item in analytics.phi_distribution"
                :key="item.entity_type"
              >
                <template #prepend>
                  <v-chip size="small" color="primary">
                    {{ item.entity_type }}
                  </v-chip>
                </template>
                <v-list-item-title>{{ item.count }} entities</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Confidence by Type -->
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title class="text-subtitle-1">Average Confidence by Type</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item
                v-for="item in analytics.confidence_by_type"
                :key="item.entity_type"
              >
                <template #prepend>
                  <v-chip size="small" color="success">
                    {{ item.entity_type }}
                  </v-chip>
                </template>
                <v-list-item-title>{{ (item.avg_confidence * 100).toFixed(1) }}%</v-list-item-title>
                <template #append>
                  <v-progress-linear
                    :model-value="item.avg_confidence * 100"
                    color="success"
                    height="8"
                    class="ml-4"
                    style="width: 100px;"
                  ></v-progress-linear>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Export button -->
    <v-row>
      <v-col>
        <v-btn
          @click="exportAnalytics"
          prepend-icon="mdi-download"
          color="primary"
        >
          Export Analytics
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Analytics {
  total_jobs: number
  success_rate: number
  avg_processing_time: number
  total_notes: number
  jobs_over_time: Array<{ date: string; count: number }>
  phi_distribution: Array<{ entity_type: string; count: number }>
  confidence_by_type: Array<{ entity_type: string; avg_confidence: number }>
}

const analytics = ref<Analytics>({
  total_jobs: 0,
  success_rate: 0,
  avg_processing_time: 0,
  total_notes: 0,
  jobs_over_time: [],
  phi_distribution: [],
  confidence_by_type: []
})

const loading = ref(false)

const loadAnalytics = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/v1/deidentify/analytics', {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
    if (response.ok) {
      analytics.value = await response.json()
    }
  } catch (error) {
    console.error('Failed to load analytics:', error)
  } finally {
    loading.value = false
  }
}

const formatTime = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${minutes}m ${secs}s`
}

const exportAnalytics = () => {
  const csvContent = generateCSV(analytics.value)
  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `analytics_${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  window.URL.revokeObjectURL(url)
}

const generateCSV = (data: Analytics): string => {
  let csv = 'Metric,Value\n'
  csv += `Total Jobs,${data.total_jobs}\n`
  csv += `Success Rate,${data.success_rate}%\n`
  csv += `Avg Processing Time,${data.avg_processing_time}s\n`
  csv += `Total Notes,${data.total_notes}\n`
  csv += '\nPHI Distribution\n'
  csv += 'Entity Type,Count\n'
  data.phi_distribution.forEach(item => {
    csv += `${item.entity_type},${item.count}\n`
  })
  return csv
}

const getAuthToken = (): string => {
  return localStorage.getItem('authToken') || ''
}

onMounted(() => {
  loadAnalytics()
})
</script>
