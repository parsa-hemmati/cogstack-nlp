<template>
  <v-card class="timeline-filters" :class="{ 'timeline-filters--mobile': isMobile }">
    <v-card-title>
      <v-icon class="mr-2">mdi-filter</v-icon>
      Timeline Filters
    </v-card-title>

    <v-card-text>
      <!-- Date Range Filter -->
      <div class="filter-section">
        <h3 class="filter-label">Date Range</h3>

        <!-- Date Range Presets -->
        <v-btn-toggle
          v-model="datePreset"
          class="mb-3"
          density="compact"
          mandatory
          @update:model-value="applyDatePreset"
        >
          <v-btn value="last30days" data-test="preset-last-30-days">Last 30 Days</v-btn>
          <v-btn value="last3months">3 Months</v-btn>
          <v-btn value="last1year">1 Year</v-btn>
          <v-btn value="all">All</v-btn>
          <v-btn value="custom">Custom</v-btn>
        </v-btn-toggle>

        <!-- Custom Date Pickers (shown when "Custom" preset selected) -->
        <div v-if="datePreset === 'custom'" class="date-pickers mt-3">
          <v-text-field
            v-model="internalDateRange.start"
            label="Start Date"
            type="date"
            density="compact"
            hide-details
            class="mb-2"
          />
          <v-text-field
            v-model="internalDateRange.end"
            label="End Date"
            type="date"
            density="compact"
            hide-details
          />
        </div>
      </div>

      <!-- Event Types Filter -->
      <div class="filter-section mt-4">
        <h3 class="filter-label">Event Types</h3>
        <v-select
          v-model="internalEventTypes"
          :items="eventTypeOptionsWithCounts"
          label="Select event types"
          multiple
          chips
          density="compact"
          hide-details
        >
          <template #chip="{ item, props: chipProps }">
            <v-chip v-bind="chipProps" size="small">
              {{ item.title }}
              <span v-if="eventCounts && eventCounts[item.value]" class="ml-1">
                ({{ eventCounts[item.value] }})
              </span>
            </v-chip>
          </template>
        </v-select>
      </div>

      <!-- Specialty Filter -->
      <div class="filter-section mt-4">
        <h3 class="filter-label">Specialty</h3>
        <v-select
          v-model="internalSpecialty"
          :items="specialtyOptions"
          label="Select specialty (optional)"
          clearable
          density="compact"
          hide-details
        />
      </div>

      <!-- Loading Indicator -->
      <v-progress-linear
        v-if="isLoading"
        indeterminate
        class="mt-4"
        data-test="loading-indicator"
      />

      <!-- Error Message -->
      <v-alert
        v-if="error"
        type="error"
        class="mt-4"
        closable
        data-test="error-message"
        @click:close="error = null"
      >
        {{ error }}
      </v-alert>
    </v-card-text>

    <v-card-actions>
      <v-btn
        color="primary"
        @click="applyFilters"
      >
        Apply Filters
      </v-btn>
      <v-btn
        variant="text"
        data-test="reset-filters"
        @click="resetFilters"
      >
        Reset
      </v-btn>
      <v-spacer />
      <v-btn
        icon="mdi-close"
        size="small"
        @click="$emit('close')"
      />
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDisplay } from 'vuetify'
import { debounce } from 'lodash-es'

interface TimelineFilters {
  dateRange: {
    start: string
    end: string
  }
  eventTypes: string[]
  specialty: string | null
}

interface Props {
  modelValue: TimelineFilters
  eventCounts?: Record<string, number>
  autoApply?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  eventCounts: undefined,
  autoApply: true
})

const emit = defineEmits<{
  'update:modelValue': [value: TimelineFilters]
  'close': []
}>()

const router = useRouter()
const route = useRoute()
const { mobile } = useDisplay()

const isMobile = computed(() => mobile.value)

// Internal state
const datePreset = ref<string>('all')
const internalDateRange = ref({ ...props.modelValue.dateRange })
const internalEventTypes = ref([...props.modelValue.eventTypes])
const internalSpecialty = ref(props.modelValue.specialty)
const isLoading = ref(false)
const error = ref<string | null>(null)

// Event type options
const eventTypeOptions = [
  'diagnosis',
  'procedure',
  'medication',
  'lab',
  'visit'
]

const eventTypeOptionsWithCounts = computed(() => {
  return eventTypeOptions.map(type => ({
    value: type,
    title: type.charAt(0).toUpperCase() + type.slice(1)
  }))
})

// Specialty options
const specialtyOptions = [
  'cardiology',
  'oncology',
  'neurology',
  'endocrinology',
  'gastroenterology',
  'pulmonology',
  'nephrology',
  'rheumatology',
  'dermatology',
  'psychiatry'
]

// Date preset handler
const applyDatePreset = (preset: string) => {
  const today = new Date()
  let start: Date
  let end: Date = today

  switch (preset) {
    case 'last30days':
      start = new Date(today)
      start.setDate(today.getDate() - 30)
      internalDateRange.value = {
        start: start.toISOString().split('T')[0],
        end: end.toISOString().split('T')[0]
      }
      if (props.autoApply) {
        debouncedApplyFilters()
      }
      break

    case 'last3months':
      start = new Date(today)
      start.setMonth(today.getMonth() - 3)
      internalDateRange.value = {
        start: start.toISOString().split('T')[0],
        end: end.toISOString().split('T')[0]
      }
      if (props.autoApply) {
        debouncedApplyFilters()
      }
      break

    case 'last1year':
      start = new Date(today)
      start.setFullYear(today.getFullYear() - 1)
      internalDateRange.value = {
        start: start.toISOString().split('T')[0],
        end: end.toISOString().split('T')[0]
      }
      if (props.autoApply) {
        debouncedApplyFilters()
      }
      break

    case 'all':
      // Set to a wide date range (e.g., last 10 years)
      start = new Date(today)
      start.setFullYear(today.getFullYear() - 10)
      internalDateRange.value = {
        start: start.toISOString().split('T')[0],
        end: end.toISOString().split('T')[0]
      }
      if (props.autoApply) {
        debouncedApplyFilters()
      }
      break

    case 'custom':
      // Don't auto-apply for custom dates
      break
  }
}

// Apply filters
const applyFilters = () => {
  const newFilters: TimelineFilters = {
    dateRange: { ...internalDateRange.value },
    eventTypes: [...internalEventTypes.value],
    specialty: internalSpecialty.value
  }

  emit('update:modelValue', newFilters)

  // Update URL query params
  updateUrlQueryParams(newFilters)
}

// Debounced apply filters (300ms debounce)
const debouncedApplyFilters = debounce(applyFilters, 300)

// Reset filters
const resetFilters = () => {
  datePreset.value = 'all'
  internalEventTypes.value = [...eventTypeOptions] // All event types
  internalSpecialty.value = null

  applyDatePreset('all')
  applyFilters()
}

// Update URL query params
const updateUrlQueryParams = (filters: TimelineFilters) => {
  router.replace({
    query: {
      ...route.query,
      dateStart: filters.dateRange.start,
      dateEnd: filters.dateRange.end,
      eventTypes: filters.eventTypes.join(','),
      specialty: filters.specialty || undefined
    }
  })
}

// Read filters from URL query params on mount
const readFiltersFromUrl = () => {
  const { dateStart, dateEnd, eventTypes, specialty } = route.query

  if (dateStart && typeof dateStart === 'string') {
    internalDateRange.value.start = dateStart
  }

  if (dateEnd && typeof dateEnd === 'string') {
    internalDateRange.value.end = dateEnd
  }

  if (eventTypes && typeof eventTypes === 'string') {
    internalEventTypes.value = eventTypes.split(',')
  }

  if (specialty && typeof specialty === 'string') {
    internalSpecialty.value = specialty
  }
}

// Watch for changes and auto-apply if enabled
watch([internalDateRange, internalEventTypes, internalSpecialty], () => {
  if (props.autoApply && datePreset.value !== 'custom') {
    debouncedApplyFilters()
  }
}, { deep: true })

// Initialize from URL on mount
onMounted(() => {
  readFiltersFromUrl()
})
</script>

<style scoped>
.timeline-filters {
  width: 100%;
  max-width: 400px;
}

.timeline-filters--mobile {
  max-width: 100%;
}

.filter-section {
  margin-bottom: 16px;
}

.filter-label {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: rgba(0, 0, 0, 0.87);
}

.date-pickers {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.v-btn-toggle) {
  width: 100%;
}

:deep(.v-btn-toggle .v-btn) {
  flex: 1;
  font-size: 11px;
  padding: 0 8px;
}

@media (max-width: 600px) {
  .timeline-filters {
    padding: 12px;
  }

  .filter-label {
    font-size: 13px;
  }

  :deep(.v-btn-toggle .v-btn) {
    font-size: 10px;
    padding: 0 4px;
  }
}
</style>
