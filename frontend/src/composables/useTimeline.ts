/**
 * useTimeline composable for timeline state management.
 *
 * Manages timeline events, filters, caching, and API calls.
 * Provides reactive state and methods for timeline interactions.
 *
 * Task #005: Timeline Composables & State Management
 */
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { debounce } from 'lodash-es'
import { useTimelineEvents } from './useTimelineEvents'
import { useTimelineCache } from './useTimelineCache'
import type { TimelineEvent, TimelineFilters } from '@/types/timeline'

interface UseTimelineOptions {
  autoFetch?: boolean
  cacheEnabled?: boolean
  debounceMs?: number
}

const defaultFilters: TimelineFilters = {
  dateRange: {
    start: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000), // 1 year ago
    end: new Date()
  },
  eventTypes: ['diagnosis', 'procedure', 'medication', 'lab', 'visit']
}

export function useTimeline(
  patientId: string,
  options: UseTimelineOptions = {}
) {
  const {
    autoFetch = true,
    cacheEnabled = true,
    debounceMs = 300
  } = options

  const router = useRouter()
  const route = useRoute()

  // State
  const events = ref<TimelineEvent[]>([])
  const totalEvents = ref<number>(0)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const filters = ref<TimelineFilters>({ ...defaultFilters })
  const retryCount = ref(0)
  const maxRetries = 3

  // Services
  const { getPatientTimeline } = useTimelineEvents()
  const { getCachedTimeline, setCachedTimeline, clearCache } = useTimelineCache()

  // Load filters from URL query params
  const loadFiltersFromUrl = () => {
    const { dateStart, dateEnd, eventTypes } = route.query

    if (dateStart && typeof dateStart === 'string') {
      filters.value.dateRange = {
        ...filters.value.dateRange!,
        start: new Date(dateStart)
      }
    }

    if (dateEnd && typeof dateEnd === 'string') {
      filters.value.dateRange = {
        ...filters.value.dateRange!,
        end: new Date(dateEnd)
      }
    }

    if (eventTypes && typeof eventTypes === 'string') {
      const types = eventTypes.split(',') as any[]
      if (types.length > 0) {
        filters.value.eventTypes = types
      }
    }
  }

  // Update URL query params when filters change
  const updateUrlQueryParams = (newFilters: TimelineFilters) => {
    const query: Record<string, string> = {}

    if (newFilters.dateRange) {
      query.dateStart = newFilters.dateRange.start.toISOString().split('T')[0]
      query.dateEnd = newFilters.dateRange.end.toISOString().split('T')[0]
    }

    if (newFilters.eventTypes && newFilters.eventTypes.length > 0) {
      query.eventTypes = newFilters.eventTypes.join(',')
    }

    router.replace({
      query: {
        ...route.query,
        ...query
      }
    }).catch(() => {
      // Ignore navigation errors
    })
  }

  // Fetch timeline with retry logic
  const fetchTimelineWithRetry = async (
    attemptFilters: TimelineFilters,
    attempt: number = 1
  ): Promise<{ events: TimelineEvent[]; total_events: number } | null> => {
    try {
      const response = await getPatientTimeline(patientId, attemptFilters)
      retryCount.value = 0
      return response
    } catch (err) {
      if (attempt < maxRetries) {
        const delay = Math.pow(2, attempt) * 500
        await new Promise(resolve => setTimeout(resolve, delay))
        return fetchTimelineWithRetry(attemptFilters, attempt + 1)
      }
      retryCount.value = attempt
      throw err
    }
  }

  // Fetch timeline from API or cache
  const fetchTimeline = async (useCache: boolean = cacheEnabled) => {
    isLoading.value = true
    error.value = null

    try {
      if (useCache) {
        const cached = getCachedTimeline(patientId, filters.value)
        if (cached) {
          events.value = cached.events
          totalEvents.value = cached.total_events
          isLoading.value = false
          return
        }
      }

      const response = await fetchTimelineWithRetry(filters.value)
      if (response) {
        events.value = response.events
        totalEvents.value = response.total_events
        if (cacheEnabled) {
          setCachedTimeline(patientId, filters.value, response)
        }
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch timeline'
      const cached = getCachedTimeline(patientId, filters.value, true)
      if (cached) {
        events.value = cached.events
        totalEvents.value = cached.total_events
      }
    } finally {
      isLoading.value = false
    }
  }

  const applyFilters = async (newFilters: Partial<TimelineFilters>) => {
    filters.value = { ...filters.value, ...newFilters }
    updateUrlQueryParams(filters.value)
    await fetchTimeline()
  }

  const applyFiltersDebounced = debounce(applyFilters, debounceMs)

  const refreshTimeline = async () => {
    clearCache(patientId, filters.value)
    await fetchTimeline(false)
  }

  const resetFilters = async () => {
    filters.value = { ...defaultFilters }
    updateUrlQueryParams(filters.value)
    await fetchTimeline()
  }

  watch(filters, (newFilters) => {
    applyFiltersDebounced(newFilters)
  }, { deep: true })

  onMounted(() => {
    loadFiltersFromUrl()
    if (autoFetch) {
      fetchTimeline()
    }
  })

  return {
    events: computed(() => events.value),
    totalEvents: computed(() => totalEvents.value),
    isLoading: computed(() => isLoading.value),
    error: computed(() => error.value),
    filters,
    fetchTimeline,
    applyFilters,
    applyFiltersDebounced,
    refreshTimeline,
    resetFilters
  }
}
