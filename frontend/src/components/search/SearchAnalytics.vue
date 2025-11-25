<template>
  <v-container fluid data-testid="analytics-dashboard">
    <!-- Header with title and actions -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center mb-4">
          <h1 class="text-h4">Search Analytics</h1>
          <div class="d-flex gap-2">
            <v-btn
              @click="refresh"
              :loading="isLoading"
              prepend-icon="mdi-refresh"
              color="primary"
              variant="tonal"
              data-testid="refresh-button"
            >
              Refresh
            </v-btn>
            <v-btn
              @click="exportToCSV"
              :disabled="!hasData"
              prepend-icon="mdi-download"
              color="success"
              variant="tonal"
              data-testid="export-csv-button"
            >
              Export CSV
            </v-btn>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Date Range Picker -->
    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Date Range Filter</v-card-title>
          <v-card-text>
            <div class="d-flex gap-2 align-center" data-testid="date-range-picker" tabindex="0">
              <v-text-field
                v-model="startDate"
                type="date"
                label="Start Date"
                density="compact"
                hide-details
              />
              <span>to</span>
              <v-text-field
                v-model="endDate"
                type="date"
                label="End Date"
                density="compact"
                hide-details
              />
              <v-btn
                @click="applyDateRange"
                :disabled="!startDate || !endDate"
                color="primary"
                size="small"
              >
                Apply
              </v-btn>
              <v-btn
                @click="clearDateRange"
                :disabled="!startDate && !endDate"
                color="error"
                size="small"
                data-testid="clear-date-range"
              >
                Clear
              </v-btn>
            </div>
            <v-alert
              v-if="dateRangeError"
              type="error"
              density="compact"
              class="mt-2"
            >
              {{ dateRangeError }}
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Loading State -->
    <v-row v-if="isLoading">
      <v-col cols="12" class="text-center py-12">
        <v-progress-circular
          indeterminate
          color="primary"
          size="64"
          data-testid="loading-spinner"
          aria-live="polite"
          aria-label="Loading analytics data"
        />
        <p class="mt-4 text-body-1">Loading analytics...</p>
      </v-col>
    </v-row>

    <!-- Error State -->
    <v-row v-else-if="error">
      <v-col cols="12">
        <v-alert
          type="error"
          variant="tonal"
          closable
          data-testid="error-alert"
        >
          {{ error }}
        </v-alert>
      </v-col>
    </v-row>

    <!-- Empty State -->
    <v-row v-else-if="!hasData">
      <v-col cols="12" class="text-center py-12" data-testid="empty-state">
        <v-icon size="96" color="grey-lighten-2">mdi-chart-bar</v-icon>
        <h2 class="text-h5 mt-4">No Analytics Data</h2>
        <p class="text-body-1 mt-2">Click Refresh to load analytics data</p>
      </v-col>
    </v-row>

    <!-- Analytics Data -->
    <template v-else-if="analytics">
      <!-- Top Queries -->
      <v-row>
        <v-col cols="12" md="6">
          <v-card>
            <v-card-title>Top Queries</v-card-title>
            <v-card-text>
              <div data-testid="top-queries-chart" aria-label="Top 10 most frequent queries">
                <v-list v-if="analytics.top_queries.length > 0">
                  <v-list-item
                    v-for="(item, index) in analytics.top_queries.slice(0, 10)"
                    :key="index"
                    :data-testid="`top-query-${index}`"
                  >
                    <template #prepend>
                      <v-chip color="primary" size="small" class="mr-2">{{ index + 1 }}</v-chip>
                    </template>
                    <v-list-item-title>{{ item.query }}</v-list-item-title>
                    <template #append>
                      <v-chip color="success" size="small">{{ item.count }}</v-chip>
                    </template>
                  </v-list-item>
                </v-list>
                <v-alert v-else type="info" variant="tonal">
                  No top queries data available
                </v-alert>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Zero Result Queries -->
        <v-col cols="12" md="6">
          <v-card>
            <v-card-title>Zero Result Queries</v-card-title>
            <v-card-text>
              <div data-testid="zero-result-table">
                <v-data-table
                  v-if="analytics.zero_result_queries.length > 0"
                  :headers="zeroResultHeaders"
                  :items="analytics.zero_result_queries"
                  density="compact"
                  :items-per-page="5"
                  :items-per-page-options="[5, 10, 25]"
                >
                  <template #item.count="{ item }">
                    <v-chip color="warning" size="small">{{ item.count }}</v-chip>
                  </template>
                </v-data-table>
                <v-alert v-else type="success" variant="tonal">
                  No zero-result queries found
                </v-alert>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Search Trends -->
      <v-row v-if="analytics.trends.length > 0">
        <v-col cols="12">
          <v-card>
            <v-card-title>Search Volume Trends</v-card-title>
            <v-card-text>
              <div data-testid="trends-chart" aria-label="Daily search volume trends">
                <v-data-table
                  :headers="trendsHeaders"
                  :items="analytics.trends"
                  density="compact"
                  :items-per-page="10"
                  :items-per-page-options="[10, 25, 50]"
                >
                  <template #item.count="{ item }">
                    <v-chip color="info" size="small">{{ item.count }}</v-chip>
                  </template>
                </v-data-table>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Slow Queries -->
      <v-row>
        <v-col cols="12">
          <v-card>
            <v-card-title>Slow Queries (>2000ms)</v-card-title>
            <v-card-text>
              <div data-testid="slow-queries-table">
                <v-data-table
                  v-if="analytics.slow_queries.length > 0"
                  :headers="slowQueriesHeaders"
                  :items="analytics.slow_queries"
                  density="compact"
                  :items-per-page="10"
                  :items-per-page-options="[10, 25, 50]"
                >
                  <template #item.execution_time_ms="{ item }">
                    <v-chip color="error" size="small">{{ item.execution_time_ms }}ms</v-chip>
                  </template>
                  <template #item.avg_execution_time_ms="{ item }">
                    <v-chip color="warning" size="small">{{ item.avg_execution_time_ms }}ms</v-chip>
                  </template>
                  <template #item.count="{ item }">
                    <v-chip color="info" size="small">{{ item.count }}</v-chip>
                  </template>
                </v-data-table>
                <v-alert v-else type="success" variant="tonal">
                  No slow queries detected
                </v-alert>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAnalytics } from '@/composables/useAnalytics'

// Use analytics composable
const {
  analytics,
  isLoading,
  error,
  hasData,
  startDate: composableStartDate,
  endDate: composableEndDate,
  fetchAnalytics,
  setDateRange,
  clearDateRange: composableClearDateRange,
  refresh,
} = useAnalytics()

// Local date range state
const startDate = ref<string | null>(null)
const endDate = ref<string | null>(null)
const dateRangeError = ref<string | null>(null)

// Table headers
const zeroResultHeaders = [
  { title: 'Query', key: 'query', sortable: true },
  { title: 'Count', key: 'count', sortable: true, align: 'end' },
]

const slowQueriesHeaders = [
  { title: 'Query', key: 'query', sortable: true },
  { title: 'Max Time', key: 'execution_time_ms', sortable: true, align: 'end' },
  { title: 'Avg Time', key: 'avg_execution_time_ms', sortable: true, align: 'end' },
  { title: 'Count', key: 'count', sortable: true, align: 'end' },
]

const trendsHeaders = [
  { title: 'Date', key: 'date', sortable: true },
  { title: 'Searches', key: 'count', sortable: true, align: 'end' },
]

/**
 * Apply date range filter
 */
const applyDateRange = async () => {
  dateRangeError.value = null

  // Validate date range
  if (startDate.value && endDate.value) {
    const start = new Date(startDate.value)
    const end = new Date(endDate.value)

    if (start > end) {
      dateRangeError.value = 'Start date must be before end date'
      return
    }

    await setDateRange(startDate.value, endDate.value)
  }
}

/**
 * Clear date range filter
 */
const clearDateRange = async () => {
  startDate.value = null
  endDate.value = null
  dateRangeError.value = null
  await composableClearDateRange()
}

/**
 * Export analytics to CSV
 */
const exportToCSV = () => {
  if (!analytics.value) return

  const rows: string[] = []

  // Header
  rows.push('Search Analytics Export')
  rows.push(`Generated: ${new Date().toISOString()}`)
  rows.push('')

  // Top Queries
  rows.push('Top Queries')
  rows.push('Query,Count')
  analytics.value.top_queries.forEach((item) => {
    rows.push(`"${item.query}",${item.count}`)
  })
  rows.push('')

  // Zero Result Queries
  rows.push('Zero Result Queries')
  rows.push('Query,Count')
  analytics.value.zero_result_queries.forEach((item) => {
    rows.push(`"${item.query}",${item.count}`)
  })
  rows.push('')

  // Slow Queries
  rows.push('Slow Queries')
  rows.push('Query,Max Time (ms),Avg Time (ms),Count')
  analytics.value.slow_queries.forEach((item) => {
    rows.push(`"${item.query}",${item.execution_time_ms},${item.avg_execution_time_ms},${item.count}`)
  })
  rows.push('')

  // Trends
  rows.push('Search Volume Trends')
  rows.push('Date,Count')
  analytics.value.trends.forEach((item) => {
    rows.push(`${item.date},${item.count}`)
  })

  const csvContent = rows.join('\n')

  // Download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `search-analytics-${new Date().toISOString().split('T')[0]}.csv`
  link.click()

  return csvContent
}

/**
 * Load analytics on mount
 */
const loadAnalytics = async () => {
  await fetchAnalytics()
}

// Load analytics on mount
onMounted(() => {
  loadAnalytics()
})

// Expose methods for testing
defineExpose({
  analytics,
  error,
  isLoading,
  startDate,
  endDate,
  loadAnalytics,
  fetchAnalytics,
  setDateRange: applyDateRange,
  clearDateRange,
  exportToCSV,
  refresh,
})
</script>

<style scoped>
.gap-2 {
  gap: 0.5rem;
}
</style>
