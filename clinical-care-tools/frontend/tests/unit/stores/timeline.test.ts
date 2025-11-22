/**
 * Unit tests for Timeline Store
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTimelineStore } from '@/stores/timeline'
import axios from 'axios'
import type {
  PatientTimeline,
  TimelineConcept,
  TimelineDocument,
  TimelineExportResponse,
  FilterPresetResponse,
  ExportFormat,
  ExportStatus,
} from '@/types/timeline'

// Mock axios
vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('Timeline Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // Sample test data
  const mockPatientId = '550e8400-e29b-41d4-a716-446655440000'

  const mockDocument: TimelineDocument = {
    id: '650e8400-e29b-41d4-a716-446655440001',
    title: 'Clinic Note - Diabetes Follow-up',
    type: 'clinic',
    document_date: '2024-03-15',
    author: 'Dr. Smith',
    concept_count: 5,
  }

  const mockConcept: TimelineConcept = {
    concept_cui: 'C0011860',
    name: 'Diabetes Mellitus',
    type: 'Disease',
    first_mention_date: '2024-03-15',
    mention_count: 1,
    mentions: [],
  }

  const mockTimeline: PatientTimeline = {
    patient_id: mockPatientId,
    documents: [mockDocument],
    concepts: [mockConcept],
    date_range: ['2024-01-01', '2024-12-31'],
    filters_applied: {},
    statistics: {
      total_documents: 1,
      total_concepts: 1,
      date_span_days: 365,
    },
  }

  const mockExportResponse: TimelineExportResponse = {
    id: '750e8400-e29b-41d4-a716-446655440002',
    patient_id: mockPatientId,
    status: ExportStatus.Processing,
    format: ExportFormat.PDF,
    expires_at: '2024-03-22T10:30:00Z',
  }

  const mockFilterPreset: FilterPresetResponse = {
    id: '850e8400-e29b-41d4-a716-446655440003',
    name: 'Active Diabetes Patients',
    description: 'Current diabetes diagnoses only',
    filters: {
      concept_cuis: ['C0011860'],
      meta_annotations: {
        negation: 'Affirmed',
        temporality: ['Current', 'Recent'],
      },
    },
    is_default: false,
    created_at: '2024-03-15T10:30:00Z',
    updated_at: '2024-03-15T10:30:00Z',
  }

  describe('fetchTimeline', () => {
    it('should call API with correct parameters', async () => {
      const store = useTimelineStore()

      mockedAxios.get.mockResolvedValueOnce({ data: mockTimeline })

      await store.fetchTimeline(mockPatientId, {
        date_start: '2024-01-01',
        date_end: '2024-12-31',
      })

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `/api/v1/timeline/${mockPatientId}`,
        {
          params: {
            date_start: '2024-01-01',
            date_end: '2024-12-31',
          },
        }
      )
    })

    it('should update state on success', async () => {
      const store = useTimelineStore()

      mockedAxios.get.mockResolvedValueOnce({ data: mockTimeline })

      await store.fetchTimeline(mockPatientId)

      expect(store.timeline).toEqual(mockTimeline)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('should handle API errors', async () => {
      const store = useTimelineStore()

      const errorMessage = 'Patient not found'
      mockedAxios.get.mockRejectedValueOnce({
        response: { data: { detail: errorMessage } },
      })

      await expect(store.fetchTimeline(mockPatientId)).rejects.toThrow()

      expect(store.timeline).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBe(errorMessage)
    })

    it('should set loading state during fetch', async () => {
      const store = useTimelineStore()

      let loadingDuringFetch = false
      mockedAxios.get.mockImplementation(() => {
        loadingDuringFetch = store.loading
        return Promise.resolve({ data: mockTimeline })
      })

      await store.fetchTimeline(mockPatientId)

      expect(loadingDuringFetch).toBe(true)
      expect(store.loading).toBe(false)
    })
  })

  describe('fetchConceptDetails', () => {
    it('should call API with correct parameters', async () => {
      const store = useTimelineStore()
      const conceptCui = 'C0011860'

      mockedAxios.get.mockResolvedValueOnce({ data: mockConcept })

      await store.fetchConceptDetails(mockPatientId, conceptCui)

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `/api/v1/timeline/${mockPatientId}/concepts/${conceptCui}`,
        { params: {} }
      )
    })

    it('should return concept data', async () => {
      const store = useTimelineStore()
      const conceptCui = 'C0011860'

      mockedAxios.get.mockResolvedValueOnce({ data: mockConcept })

      const result = await store.fetchConceptDetails(mockPatientId, conceptCui)

      expect(result).toEqual(mockConcept)
    })
  })

  describe('exportTimeline', () => {
    it('should call API with correct parameters', async () => {
      const store = useTimelineStore()

      mockedAxios.post.mockResolvedValueOnce({ data: mockExportResponse })

      await store.exportTimeline(mockPatientId, {
        format: ExportFormat.PDF,
        filters: { date_start: '2024-01-01' },
        options: { watermark: 'CONFIDENTIAL' },
      })

      expect(mockedAxios.post).toHaveBeenCalledWith(
        `/api/v1/timeline/${mockPatientId}/export`,
        {
          format: ExportFormat.PDF,
          filters: { date_start: '2024-01-01' },
          options: { watermark: 'CONFIDENTIAL' },
        }
      )
    })

    it('should return export response', async () => {
      const store = useTimelineStore()

      mockedAxios.post.mockResolvedValueOnce({ data: mockExportResponse })

      const result = await store.exportTimeline(mockPatientId, {
        format: ExportFormat.PDF,
      })

      expect(result).toEqual(mockExportResponse)
      expect(result.status).toBe(ExportStatus.Processing)
    })
  })

  describe('getExportStatus', () => {
    it('should call API with correct parameters', async () => {
      const store = useTimelineStore()
      const exportId = mockExportResponse.id

      mockedAxios.get.mockResolvedValueOnce({ data: mockExportResponse })

      await store.getExportStatus(exportId)

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `/api/v1/timeline/exports/${exportId}`
      )
    })

    it('should return export status', async () => {
      const store = useTimelineStore()
      const exportId = mockExportResponse.id

      const completedExport = { ...mockExportResponse, status: ExportStatus.Completed }
      mockedAxios.get.mockResolvedValueOnce({ data: completedExport })

      const result = await store.getExportStatus(exportId)

      expect(result.status).toBe(ExportStatus.Completed)
    })
  })

  describe('downloadExport', () => {
    it('should call API with correct parameters', async () => {
      const store = useTimelineStore()
      const exportId = mockExportResponse.id

      const mockBlob = new Blob(['pdf content'], { type: 'application/pdf' })
      mockedAxios.get.mockResolvedValueOnce({ data: mockBlob })

      // Mock DOM methods
      const createObjectURLSpy = vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:url')
      const revokeObjectURLSpy = vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {})
      const createElementSpy = vi.spyOn(document, 'createElement')
      const appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => ({} as any))
      const removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => ({} as any))

      await store.downloadExport(exportId, 'pdf')

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `/api/v1/timeline/exports/${exportId}/download`,
        { responseType: 'blob' }
      )

      // Cleanup spies
      createObjectURLSpy.mockRestore()
      revokeObjectURLSpy.mockRestore()
      createElementSpy.mockRestore()
      appendChildSpy.mockRestore()
      removeChildSpy.mockRestore()
    })
  })

  describe('saveFilterPreset', () => {
    it('should call API with correct parameters', async () => {
      const store = useTimelineStore()

      mockedAxios.post.mockResolvedValueOnce({ data: mockFilterPreset })

      await store.saveFilterPreset({
        name: 'Active Diabetes Patients',
        description: 'Current diabetes diagnoses only',
        filters: { concept_cuis: ['C0011860'] },
        is_default: false,
      })

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/timeline/filters',
        {
          name: 'Active Diabetes Patients',
          description: 'Current diabetes diagnoses only',
          filters: { concept_cuis: ['C0011860'] },
          is_default: false,
        }
      )
    })

    it('should add filter to state', async () => {
      const store = useTimelineStore()

      mockedAxios.post.mockResolvedValueOnce({ data: mockFilterPreset })

      await store.saveFilterPreset({
        name: 'Active Diabetes Patients',
        filters: { concept_cuis: ['C0011860'] },
      })

      expect(store.filterPresets).toContainEqual(mockFilterPreset)
    })
  })

  describe('loadFilterPresets', () => {
    it('should call API and update state', async () => {
      const store = useTimelineStore()

      const mockPresets = [mockFilterPreset]
      mockedAxios.get.mockResolvedValueOnce({ data: mockPresets })

      await store.loadFilterPresets()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/timeline/filters')
      expect(store.filterPresets).toEqual(mockPresets)
    })
  })

  describe('clearTimeline', () => {
    it('should reset state', async () => {
      const store = useTimelineStore()

      // Set some state
      mockedAxios.get.mockResolvedValueOnce({ data: mockTimeline })
      await store.fetchTimeline(mockPatientId)

      expect(store.timeline).not.toBeNull()

      // Clear
      store.clearTimeline()

      expect(store.timeline).toBeNull()
      expect(store.error).toBeNull()
    })
  })
})
