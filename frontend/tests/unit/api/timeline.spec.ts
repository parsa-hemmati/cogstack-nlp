/**
 * Unit tests for Timeline API client.
 *
 * Tests API methods with mocked axios instance.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getPatientTimeline } from '@/api/timeline'
import type { PatientTimeline, TimelineFilters } from '@/types/timeline'
import api from '@/services/api'

// Mock the API client
vi.mock('@/services/api')

describe('Timeline API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  /**
   * TEST 1: Basic timeline retrieval (no filters)
   */
  it('should fetch patient timeline without filters', async () => {
    // Arrange
    const patientId = 'patient-uuid-123'
    const mockResponse: PatientTimeline = {
      patientId,
      documents: [
        {
          documentId: 'doc-1',
          title: 'Clinical Note',
          documentType: 'clinical_note',
          date: '2023-01-15T10:30:00Z',
          author: 'Dr. Smith',
          concepts: ['C0011849', 'C0020538']
        }
      ],
      concepts: [
        {
          conceptCui: 'C0011849',
          conceptName: 'Diabetes Mellitus',
          conceptType: 'condition',
          firstMentionDate: '2023-01-15T10:30:00Z',
          mentionCount: 2,
          mentions: []
        }
      ],
      dateRange: {
        start: '2023-01-15T10:30:00Z',
        end: '2023-02-20T14:15:00Z'
      },
      filtersApplied: {}
    }

    vi.mocked(api.get).mockResolvedValue({ data: mockResponse })

    // Act
    const result = await getPatientTimeline(patientId)

    // Assert
    expect(api.get).toHaveBeenCalledWith(`/api/v1/timeline/${patientId}`)
    expect(result).toEqual(mockResponse)
    expect(result.documents).toHaveLength(1)
    expect(result.concepts).toHaveLength(1)
  })

  /**
   * TEST 2: Timeline with concept filter
   */
  it('should encode concept filter correctly', async () => {
    // Arrange
    const patientId = 'patient-uuid-123'
    const filters: TimelineFilters = {
      concepts: ['C0011849', 'C0020538']
    }

    vi.mocked(api.get).mockResolvedValue({ data: {} as PatientTimeline })

    // Act
    await getPatientTimeline(patientId, filters)

    // Assert
    expect(api.get).toHaveBeenCalledWith(
      `/api/v1/timeline/${patientId}?concepts=C0011849%2CC0020538`
    )
  })

  /**
   * TEST 3: Timeline with date range filter
   */
  it('should encode date range filter correctly', async () => {
    // Arrange
    const patientId = 'patient-uuid-123'
    const dateStart = new Date('2023-01-01T00:00:00Z')
    const dateEnd = new Date('2023-12-31T23:59:59Z')
    const filters: TimelineFilters = {
      dateRange: {
        start: dateStart,
        end: dateEnd
      }
    }

    vi.mocked(api.get).mockResolvedValue({ data: {} as PatientTimeline })

    // Act
    await getPatientTimeline(patientId, filters)

    // Assert
    const expectedUrl = `/api/v1/timeline/${patientId}?date_start=${dateStart.toISOString()}&date_end=${dateEnd.toISOString()}`
    expect(api.get).toHaveBeenCalledWith(expectedUrl)
  })

  /**
   * TEST 4: Timeline with meta-annotation filters (single values)
   */
  it('should encode meta-annotation filters correctly (single values)', async () => {
    // Arrange
    const patientId = 'patient-uuid-123'
    const filters: TimelineFilters = {
      metaAnnotations: {
        Negation: 'Affirmed',
        Experiencer: 'Patient',
        Temporality: 'Current',
        Certainty: 'High'
      }
    }

    vi.mocked(api.get).mockResolvedValue({ data: {} as PatientTimeline })

    // Act
    await getPatientTimeline(patientId, filters)

    // Assert
    const call = vi.mocked(api.get).mock.calls[0][0]
    expect(call).toContain('meta_negation=Affirmed')
    expect(call).toContain('meta_experiencer=Patient')
    expect(call).toContain('meta_temporality=Current')
    expect(call).toContain('meta_certainty=High')
  })

  /**
   * TEST 5: Timeline with meta-annotation filters (Temporality as array - OR logic)
   */
  it('should encode Temporality array as comma-separated list', async () => {
    // Arrange
    const patientId = 'patient-uuid-123'
    const filters: TimelineFilters = {
      metaAnnotations: {
        Temporality: ['Current', 'Recent', 'Historical']
      }
    }

    vi.mocked(api.get).mockResolvedValue({ data: {} as PatientTimeline })

    // Act
    await getPatientTimeline(patientId, filters)

    // Assert
    const call = vi.mocked(api.get).mock.calls[0][0]
    expect(call).toContain('meta_temporality=Current%2CRecent%2CHistorical')
  })

  /**
   * TEST 6: Timeline with document types filter
   */
  it('should encode document types filter correctly', async () => {
    // Arrange
    const patientId = 'patient-uuid-123'
    const filters: TimelineFilters = {
      documentTypes: ['clinical_note', 'lab_result']
    }

    vi.mocked(api.get).mockResolvedValue({ data: {} as PatientTimeline })

    // Act
    await getPatientTimeline(patientId, filters)

    // Assert
    const call = vi.mocked(api.get).mock.calls[0][0]
    expect(call).toContain('document_types=clinical_note%2Clab_result')
  })

  /**
   * TEST 7: Timeline with combined filters
   */
  it('should combine all filters correctly', async () => {
    // Arrange
    const patientId = 'patient-uuid-123'
    const filters: TimelineFilters = {
      concepts: ['C0011849'],
      dateRange: {
        start: new Date('2023-01-01T00:00:00Z'),
        end: new Date('2023-12-31T23:59:59Z')
      },
      metaAnnotations: {
        Negation: 'Affirmed',
        Experiencer: 'Patient',
        Temporality: ['Current', 'Recent']
      },
      documentTypes: ['clinical_note']
    }

    vi.mocked(api.get).mockResolvedValue({ data: {} as PatientTimeline })

    // Act
    await getPatientTimeline(patientId, filters)

    // Assert
    const call = vi.mocked(api.get).mock.calls[0][0]
    expect(call).toContain('concepts=C0011849')
    expect(call).toContain('date_start=')
    expect(call).toContain('date_end=')
    expect(call).toContain('meta_negation=Affirmed')
    expect(call).toContain('meta_experiencer=Patient')
    expect(call).toContain('meta_temporality=Current%2CRecent')
    expect(call).toContain('document_types=clinical_note')
  })

  /**
   * TEST 8: Empty filters should not append query parameters
   */
  it('should not append empty filters to URL', async () => {
    // Arrange
    const patientId = 'patient-uuid-123'
    const filters: TimelineFilters = {
      concepts: [],
      documentTypes: []
    }

    vi.mocked(api.get).mockResolvedValue({ data: {} as PatientTimeline })

    // Act
    await getPatientTimeline(patientId, filters)

    // Assert
    expect(api.get).toHaveBeenCalledWith(`/api/v1/timeline/${patientId}`)
  })

  /**
   * TEST 9: API error handling
   */
  it('should propagate API errors', async () => {
    // Arrange
    const patientId = 'patient-uuid-123'
    const errorMessage = 'Failed to load timeline'
    vi.mocked(api.get).mockRejectedValue(new Error(errorMessage))

    // Act & Assert
    await expect(getPatientTimeline(patientId)).rejects.toThrow(errorMessage)
  })

  /**
   * TEST 10: Undefined filters should be handled gracefully
   */
  it('should handle undefined filters', async () => {
    // Arrange
    const patientId = 'patient-uuid-123'

    vi.mocked(api.get).mockResolvedValue({ data: {} as PatientTimeline })

    // Act
    await getPatientTimeline(patientId, undefined)

    // Assert
    expect(api.get).toHaveBeenCalledWith(`/api/v1/timeline/${patientId}`)
  })
})
