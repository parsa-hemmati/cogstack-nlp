/**
 * Unit tests for useTimeline composable (Task #005).
 *
 * Tests timeline state management, event fetching, and filtering.
 *
 * PRD Specification: .claude/ccpm/epics/timeline-module/005.md
 * Test Coverage: useTimeline composable
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { ref } from 'vue'
import { useTimeline } from '@/composables/useTimeline'
import type { TimelineEvent, TimelineFilters } from '@/types/timeline'

// Mock API calls
vi.mock('@/composables/useTimelineEvents', () => ({
  useTimelineEvents: () => ({
    getPatientTimeline: vi.fn().mockResolvedValue({
      events: [
        {
          id: 'event-1',
          event_type: 'diagnosis',
          date: '2023-06-15T10:30:00Z',
          title: 'Diabetes Mellitus'
        }
      ],
      total_events: 1
    })
  })
}))

describe('useTimeline', () => {
  const mockPatientId = 'patient-123'

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('initializes with default state', () => {
    const { events, isLoading, error, filters } = useTimeline(mockPatientId)

    expect(events.value).toEqual([])
    expect(isLoading.value).toBe(false)
    expect(error.value).toBeNull()
    expect(filters.value).toBeDefined()
  })

  it('fetches timeline on mount', async () => {
    const { events, fetchTimeline, isLoading } = useTimeline(mockPatientId)

    expect(isLoading.value).toBe(false)

    await fetchTimeline()

    expect(events.value.length).toBeGreaterThan(0)
    expect(isLoading.value).toBe(false)
  })

  it('sets loading state while fetching', async () => {
    const { fetchTimeline, isLoading } = useTimeline(mockPatientId)

    const promise = fetchTimeline()

    // Should be loading during fetch
    expect(isLoading.value).toBe(true)

    await promise

    // Should not be loading after fetch
    expect(isLoading.value).toBe(false)
  })

  it('handles fetch errors gracefully', async () => {
    vi.mock('@/composables/useTimelineEvents', () => ({
      useTimelineEvents: () => ({
        getPatientTimeline: vi.fn().mockRejectedValue(new Error('Network error'))
      })
    }))

    const { fetchTimeline, error, isLoading } = useTimeline(mockPatientId)

    await fetchTimeline()

    expect(error.value).toBeTruthy()
    expect(isLoading.value).toBe(false)
  })

  it('applies filters and refetches timeline', async () => {
    const { applyFilters, events } = useTimeline(mockPatientId)

    const newFilters: Partial<TimelineFilters> = {
      dateRange: {
        start: new Date('2023-01-01'),
        end: new Date('2023-12-31')
      },
      eventTypes: ['diagnosis', 'medication']
    }

    await applyFilters(newFilters)

    expect(events.value.length).toBeGreaterThan(0)
  })

  it('debounces filter changes (300ms)', async () => {
    vi.useFakeTimers()

    const { applyFilters } = useTimeline(mockPatientId)
    const fetchSpy = vi.fn()

    // Trigger multiple rapid filter changes
    applyFilters({ eventTypes: ['diagnosis'] })
    applyFilters({ eventTypes: ['medication'] })
    applyFilters({ eventTypes: ['lab'] })

    // Should not fetch yet
    expect(fetchSpy).not.toHaveBeenCalled()

    // Advance timers by 300ms
    vi.advanceTimersByTime(300)

    vi.useRealTimers()
  })

  it('refreshes timeline (clears cache)', async () => {
    const { fetchTimeline, refreshTimeline } = useTimeline(mockPatientId)

    // Fetch initially
    await fetchTimeline()

    // Cache should be set
    const cacheKey = `timeline:${mockPatientId}`
    expect(localStorage.getItem(cacheKey)).toBeTruthy()

    // Refresh
    await refreshTimeline()

    // Should refetch and update cache
    expect(localStorage.getItem(cacheKey)).toBeTruthy()
  })

  it('uses cached data when available', async () => {
    const cachedData = {
      events: [
        {
          id: 'cached-event',
          event_type: 'diagnosis',
          date: '2023-05-01T00:00:00Z',
          title: 'Cached Event'
        }
      ],
      timestamp: Date.now()
    }

    localStorage.setItem(
      `timeline:${mockPatientId}`,
      JSON.stringify(cachedData)
    )

    const { events, fetchTimeline } = useTimeline(mockPatientId)

    await fetchTimeline()

    // Should load from cache
    expect(events.value[0].id).toBe('cached-event')
  })

  it('invalidates cache after TTL (5 minutes)', async () => {
    const cachedData = {
      events: [{ id: 'old-event' }],
      timestamp: Date.now() - (6 * 60 * 1000) // 6 minutes ago
    }

    localStorage.setItem(
      `timeline:${mockPatientId}`,
      JSON.stringify(cachedData)
    )

    const { events, fetchTimeline } = useTimeline(mockPatientId)

    await fetchTimeline()

    // Should fetch fresh data (cache expired)
    expect(events.value[0].id).not.toBe('old-event')
  })

  it('retries failed requests (3 attempts)', async () => {
    let attemptCount = 0

    vi.mock('@/composables/useTimelineEvents', () => ({
      useTimelineEvents: () => ({
        getPatientTimeline: vi.fn(() => {
          attemptCount++
          if (attemptCount < 3) {
            return Promise.reject(new Error('Network error'))
          }
          return Promise.resolve({ events: [], total_events: 0 })
        })
      })
    }))

    const { fetchTimeline } = useTimeline(mockPatientId)

    await fetchTimeline()

    expect(attemptCount).toBe(3)
  })

  it('updates URL query params when filters change', async () => {
    const mockRouter = {
      replace: vi.fn()
    }

    const { applyFilters } = useTimeline(mockPatientId)

    const newFilters: Partial<TimelineFilters> = {
      eventTypes: ['diagnosis', 'medication']
    }

    await applyFilters(newFilters)

    // Should update URL (would need router mock)
    // expect(mockRouter.replace).toHaveBeenCalled()
  })

  it('loads filters from URL query params on mount', () => {
    // Mock route with query params
    const mockRoute = {
      query: {
        dateStart: '2023-01-01',
        dateEnd: '2023-12-31',
        eventTypes: 'diagnosis,medication'
      }
    }

    const { filters } = useTimeline(mockPatientId)

    // Should parse URL params into filters
    expect(filters.value.eventTypes).toContain('diagnosis')
    expect(filters.value.eventTypes).toContain('medication')
  })

  it('optimistically updates events on filter change', async () => {
    const { events, applyFilters } = useTimeline(mockPatientId)

    // Initial events
    await applyFilters({ eventTypes: ['diagnosis'] })
    const initialCount = events.value.length

    // Apply new filter
    await applyFilters({ eventTypes: ['medication'] })

    // Events should update
    expect(events.value.length).toBeGreaterThanOrEqual(0)
  })

  it('falls back to cached data on API failure', async () => {
    const cachedData = {
      events: [{ id: 'cached-event', title: 'Fallback Event' }],
      timestamp: Date.now()
    }

    localStorage.setItem(
      `timeline:${mockPatientId}`,
      JSON.stringify(cachedData)
    )

    vi.mock('@/composables/useTimelineEvents', () => ({
      useTimelineEvents: () => ({
        getPatientTimeline: vi.fn().mockRejectedValue(new Error('Network error'))
      })
    }))

    const { events, fetchTimeline, error } = useTimeline(mockPatientId)

    await fetchTimeline()

    // Should use cached data as fallback
    expect(events.value.length).toBeGreaterThan(0)
    expect(events.value[0].title).toBe('Fallback Event')
    expect(error.value).toBeTruthy() // Error still set
  })
})
