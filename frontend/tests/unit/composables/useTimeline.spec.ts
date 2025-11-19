/**
 * Unit tests for useTimeline composable.
 *
 * Tests timeline state management, API calls, loading/error states.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useTimeline } from '@/composables/useTimeline'
import { getPatientTimeline } from '@/api/timeline'
import type { PatientTimeline, TimelineFilters } from '@/types/timeline'

// Mock the timeline API
vi.mock('@/api/timeline')

describe('useTimeline Composable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  /**
   * TEST 1: Initial state
   */
  it('should initialize with correct default state', () => {
    // Arrange & Act
    const { timeline, isLoading, error, hasTimeline, isEmpty, documentCount, conceptCount } = useTimeline()

    // Assert
    expect(timeline.value).toBeNull()
    expect(isLoading.value).toBe(false)
    expect(error.value).toBeNull()
    expect(hasTimeline.value).toBe(false)
    expect(isEmpty.value).toBe(false) // No timeline loaded yet
    expect(documentCount.value).toBe(0)
    expect(conceptCount.value).toBe(0)
  })

  /**
   * TEST 2: Successful timeline fetch
   */
  it('should fetch timeline and update state', async () => {
    // Arrange
    const mockTimeline: PatientTimeline = {
      patientId: 'patient-uuid-123',
      documents: [
        {
          documentId: 'doc-1',
          title: 'Clinical Note',
          documentType: 'clinical_note',
          date: '2023-01-15T10:30:00Z',
          author: 'Dr. Smith',
          concepts: ['C0011849']
        }
      ],
      concepts: [
        {
          conceptCui: 'C0011849',
          conceptName: 'Diabetes Mellitus',
          conceptType: 'condition',
          firstMentionDate: '2023-01-15T10:30:00Z',
          mentionCount: 1,
          mentions: []
        }
      ],
      dateRange: {
        start: '2023-01-15T10:30:00Z',
        end: '2023-01-15T10:30:00Z'
      },
      filtersApplied: {}
    }

    vi.mocked(getPatientTimeline).mockResolvedValue(mockTimeline)

    // Act
    const { timeline, isLoading, error, hasTimeline, documentCount, conceptCount, fetchTimeline } = useTimeline()
    await fetchTimeline('patient-uuid-123')

    // Assert
    expect(getPatientTimeline).toHaveBeenCalledWith('patient-uuid-123', undefined)
    expect(timeline.value).toEqual(mockTimeline)
    expect(isLoading.value).toBe(false)
    expect(error.value).toBeNull()
    expect(hasTimeline.value).toBe(true)
    expect(documentCount.value).toBe(1)
    expect(conceptCount.value).toBe(1)
  })

  /**
   * TEST 3: Timeline fetch with filters
   */
  it('should pass filters to API call', async () => {
    // Arrange
    const mockTimeline: PatientTimeline = {
      patientId: 'patient-uuid-123',
      documents: [],
      concepts: [],
      dateRange: {
        start: '2023-01-01T00:00:00Z',
        end: '2023-12-31T23:59:59Z'
      },
      filtersApplied: { concepts: ['C0011849'] }
    }

    const filters: TimelineFilters = {
      concepts: ['C0011849'],
      dateRange: {
        start: new Date('2023-01-01'),
        end: new Date('2023-12-31')
      }
    }

    vi.mocked(getPatientTimeline).mockResolvedValue(mockTimeline)

    // Act
    const { fetchTimeline } = useTimeline()
    await fetchTimeline('patient-uuid-123', filters)

    // Assert
    expect(getPatientTimeline).toHaveBeenCalledWith('patient-uuid-123', filters)
  })

  /**
   * TEST 4: Loading state management
   */
  it('should manage loading state correctly', async () => {
    // Arrange
    const mockTimeline: PatientTimeline = {
      patientId: 'patient-uuid-123',
      documents: [],
      concepts: [],
      dateRange: {
        start: '2023-01-01T00:00:00Z',
        end: '2023-12-31T23:59:59Z'
      },
      filtersApplied: {}
    }

    let resolveFetch: (value: PatientTimeline) => void
    const fetchPromise = new Promise<PatientTimeline>((resolve) => {
      resolveFetch = resolve
    })

    vi.mocked(getPatientTimeline).mockReturnValue(fetchPromise)

    // Act
    const { isLoading, fetchTimeline } = useTimeline()

    const fetchPromiseResult = fetchTimeline('patient-uuid-123')

    // Assert - during fetch
    expect(isLoading.value).toBe(true)

    // Complete fetch
    resolveFetch!(mockTimeline)
    await fetchPromiseResult

    // Assert - after fetch
    expect(isLoading.value).toBe(false)
  })

  /**
   * TEST 5: Error handling
   */
  it('should handle API errors', async () => {
    // Arrange
    const errorMessage = 'Failed to load timeline'
    vi.mocked(getPatientTimeline).mockRejectedValue(new Error(errorMessage))

    // Act
    const { timeline, error, isLoading, fetchTimeline } = useTimeline()
    await fetchTimeline('patient-uuid-123')

    // Assert
    expect(timeline.value).toBeNull()
    expect(error.value).toBe(errorMessage)
    expect(isLoading.value).toBe(false)
  })

  /**
   * TEST 6: Error handling with response detail
   */
  it('should extract error detail from response', async () => {
    // Arrange
    const errorDetail = 'Timeline not found for patient'
    vi.mocked(getPatientTimeline).mockRejectedValue({
      response: {
        data: {
          detail: errorDetail
        }
      }
    })

    // Act
    const { error, fetchTimeline } = useTimeline()
    await fetchTimeline('patient-uuid-123')

    // Assert
    expect(error.value).toBe(errorDetail)
  })

  /**
   * TEST 7: Empty patient ID validation
   */
  it('should validate patient ID before fetch', async () => {
    // Act
    const { timeline, error, fetchTimeline } = useTimeline()
    await fetchTimeline('')

    // Assert
    expect(getPatientTimeline).not.toHaveBeenCalled()
    expect(error.value).toBe('Patient ID is required')
    expect(timeline.value).toBeNull()
  })

  /**
   * TEST 8: Clear timeline
   */
  it('should clear timeline data', async () => {
    // Arrange
    const mockTimeline: PatientTimeline = {
      patientId: 'patient-uuid-123',
      documents: [],
      concepts: [],
      dateRange: {
        start: '2023-01-01T00:00:00Z',
        end: '2023-12-31T23:59:59Z'
      },
      filtersApplied: {}
    }

    vi.mocked(getPatientTimeline).mockResolvedValue(mockTimeline)

    // Act
    const { timeline, fetchTimeline, clearTimeline, lastPatientId } = useTimeline()
    await fetchTimeline('patient-uuid-123')

    expect(timeline.value).not.toBeNull()
    expect(lastPatientId.value).toBe('patient-uuid-123')

    clearTimeline()

    // Assert
    expect(timeline.value).toBeNull()
    expect(lastPatientId.value).toBe('')
  })

  /**
   * TEST 9: Clear error
   */
  it('should clear error state', async () => {
    // Arrange
    vi.mocked(getPatientTimeline).mockRejectedValue(new Error('Test error'))

    // Act
    const { error, fetchTimeline, clearError } = useTimeline()
    await fetchTimeline('patient-uuid-123')

    expect(error.value).not.toBeNull()

    clearError()

    // Assert
    expect(error.value).toBeNull()
  })

  /**
   * TEST 10: Refresh timeline
   */
  it('should refresh timeline with same filters', async () => {
    // Arrange
    const mockTimeline: PatientTimeline = {
      patientId: 'patient-uuid-123',
      documents: [],
      concepts: [],
      dateRange: {
        start: '2023-01-01T00:00:00Z',
        end: '2023-12-31T23:59:59Z'
      },
      filtersApplied: { concepts: ['C0011849'] }
    }

    vi.mocked(getPatientTimeline).mockResolvedValue(mockTimeline)

    const filters: TimelineFilters = { concepts: ['C0011849'] }

    // Act
    const { fetchTimeline, refreshTimeline } = useTimeline()
    await fetchTimeline('patient-uuid-123', filters)

    vi.clearAllMocks()

    await refreshTimeline()

    // Assert
    expect(getPatientTimeline).toHaveBeenCalledWith('patient-uuid-123', { concepts: ['C0011849'] })
  })

  /**
   * TEST 11: Refresh without previous fetch should show error
   */
  it('should handle refresh without previous fetch', async () => {
    // Act
    const { error, refreshTimeline } = useTimeline()
    await refreshTimeline()

    // Assert
    expect(error.value).toBe('No patient ID available for refresh')
  })

  /**
   * TEST 12: isEmpty computed property
   */
  it('should compute isEmpty correctly', async () => {
    // Arrange
    const mockTimeline: PatientTimeline = {
      patientId: 'patient-uuid-123',
      documents: [],
      concepts: [],
      dateRange: {
        start: '2023-01-01T00:00:00Z',
        end: '2023-12-31T23:59:59Z'
      },
      filtersApplied: {}
    }

    vi.mocked(getPatientTimeline).mockResolvedValue(mockTimeline)

    // Act
    const { isEmpty, fetchTimeline } = useTimeline()

    expect(isEmpty.value).toBe(false) // No timeline loaded

    await fetchTimeline('patient-uuid-123')

    // Assert
    expect(isEmpty.value).toBe(true) // Timeline loaded but empty
  })

  /**
   * TEST 13: hasTimeline computed property
   */
  it('should compute hasTimeline correctly', async () => {
    // Arrange
    const mockTimeline: PatientTimeline = {
      patientId: 'patient-uuid-123',
      documents: [],
      concepts: [],
      dateRange: {
        start: '2023-01-01T00:00:00Z',
        end: '2023-12-31T23:59:59Z'
      },
      filtersApplied: {}
    }

    vi.mocked(getPatientTimeline).mockResolvedValue(mockTimeline)

    // Act
    const { hasTimeline, fetchTimeline } = useTimeline()

    expect(hasTimeline.value).toBe(false)

    await fetchTimeline('patient-uuid-123')

    // Assert
    expect(hasTimeline.value).toBe(true)
  })
})
