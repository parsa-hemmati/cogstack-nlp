import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { useTimelineFilters } from '@/composables/useTimelineFilters'
import { useRouter, useRoute } from 'vue-router'
import { timelineApi } from '@/api/timeline'

// Mock vue-router
vi.mock('vue-router', () => ({
  useRouter: vi.fn(),
  useRoute: vi.fn()
}))

// Mock timeline API
vi.mock('@/api/timeline', () => ({
  timelineApi: {
    getPatientTimeline: vi.fn()
  }
}))

describe('useTimelineFilters', () => {
  let mockRouter: any
  let mockRoute: any

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks()

    // Mock router
    mockRouter = {
      push: vi.fn().mockResolvedValue(undefined)
    }
    vi.mocked(useRouter).mockReturnValue(mockRouter)

    // Mock route
    mockRoute = {
      query: {}
    }
    vi.mocked(useRoute).mockReturnValue(mockRoute)
  })

  it('initializes with default filters', () => {
    const patientId = ref('patient-123')
    const { filters, hasActiveFilters, activeFilterCount } = useTimelineFilters(patientId)

    expect(filters.value.conceptCuis).toEqual([])
    expect(filters.value.dateFrom).toBeNull()
    expect(filters.value.dateTo).toBeNull()
    expect(filters.value.metaAnnotations).toEqual({
      Negation: 'Affirmed',
      Experiencer: 'Patient',
      Temporality: ['Current', 'Recent']
    })
    expect(filters.value.documentTypes).toEqual([])
    expect(filters.value.includeDocuments).toBe(true)
    expect(filters.value.includeConcepts).toBe(true)
    expect(hasActiveFilters.value).toBe(false)
    expect(activeFilterCount.value).toBe(0)
  })

  it('setConceptFilter updates concept CUIs', () => {
    const patientId = ref('patient-123')
    const { filters, setConceptFilter, hasActiveFilters, activeFilterCount } = useTimelineFilters(patientId)

    setConceptFilter(['C0011849', 'C0020538'])

    expect(filters.value.conceptCuis).toEqual(['C0011849', 'C0020538'])
    expect(hasActiveFilters.value).toBe(true)
    expect(activeFilterCount.value).toBe(1)
  })

  it('addConcept adds a concept to the filter', () => {
    const patientId = ref('patient-123')
    const { filters, addConcept } = useTimelineFilters(patientId)

    addConcept('C0011849')
    expect(filters.value.conceptCuis).toEqual(['C0011849'])

    addConcept('C0020538')
    expect(filters.value.conceptCuis).toEqual(['C0011849', 'C0020538'])

    // Should not add duplicate
    addConcept('C0011849')
    expect(filters.value.conceptCuis).toEqual(['C0011849', 'C0020538'])
  })

  it('removeConcept removes a concept from the filter', () => {
    const patientId = ref('patient-123')
    const { filters, setConceptFilter, removeConcept } = useTimelineFilters(patientId)

    setConceptFilter(['C0011849', 'C0020538', 'C0004238'])
    removeConcept('C0020538')

    expect(filters.value.conceptCuis).toEqual(['C0011849', 'C0004238'])
  })

  it('setDateRange updates date filters', () => {
    const patientId = ref('patient-123')
    const { filters, setDateRange, hasActiveFilters, activeFilterCount } = useTimelineFilters(patientId)

    const from = new Date('2023-01-01')
    const to = new Date('2023-12-31')
    setDateRange(from, to)

    expect(filters.value.dateFrom).toEqual(from)
    expect(filters.value.dateTo).toEqual(to)
    expect(hasActiveFilters.value).toBe(true)
    expect(activeFilterCount.value).toBe(1)
  })

  it('setMetaAnnotationFilter updates meta-annotation filters', () => {
    const patientId = ref('patient-123')
    const { filters, setMetaAnnotationFilter } = useTimelineFilters(patientId)

    // Single value
    setMetaAnnotationFilter('Negation', 'Negated')
    expect(filters.value.metaAnnotations.Negation).toBe('Negated')

    // Array value
    setMetaAnnotationFilter('Temporality', ['Historical'])
    expect(filters.value.metaAnnotations.Temporality).toEqual(['Historical'])
  })

  it('setDocumentTypeFilter updates document type filters', () => {
    const patientId = ref('patient-123')
    const { filters, setDocumentTypeFilter, hasActiveFilters, activeFilterCount } = useTimelineFilters(patientId)

    setDocumentTypeFilter(['clinical_note', 'discharge_summary'])

    expect(filters.value.documentTypes).toEqual(['clinical_note', 'discharge_summary'])
    expect(hasActiveFilters.value).toBe(true)
    expect(activeFilterCount.value).toBe(1)
  })

  it('clearFilters resets all filters to defaults', () => {
    const patientId = ref('patient-123')
    const { filters, setConceptFilter, setDateRange, setDocumentTypeFilter, clearFilters, hasActiveFilters } = useTimelineFilters(patientId)

    // Set some filters
    setConceptFilter(['C0011849'])
    setDateRange(new Date('2023-01-01'), new Date('2023-12-31'))
    setDocumentTypeFilter(['clinical_note'])

    expect(hasActiveFilters.value).toBe(true)

    // Clear filters
    clearFilters()

    expect(filters.value.conceptCuis).toEqual([])
    expect(filters.value.dateFrom).toBeNull()
    expect(filters.value.dateTo).toBeNull()
    expect(filters.value.metaAnnotations).toEqual({
      Negation: 'Affirmed',
      Experiencer: 'Patient',
      Temporality: ['Current', 'Recent']
    })
    expect(filters.value.documentTypes).toEqual([])
    expect(hasActiveFilters.value).toBe(false)
  })

  it('applyFilters calls API with correct filters', async () => {
    const patientId = ref('patient-123')
    const mockTimeline = {
      patient_id: 'patient-123',
      documents: [],
      concepts: [],
      date_range: { start: new Date(), end: new Date() },
      filters_applied: {}
    }

    vi.mocked(timelineApi.getPatientTimeline).mockResolvedValue(mockTimeline)

    const { setConceptFilter, applyFilters, isLoading, timeline } = useTimelineFilters(patientId)

    setConceptFilter(['C0011849'])
    await applyFilters()

    expect(isLoading.value).toBe(false)
    expect(timeline.value).toEqual(mockTimeline)
    expect(timelineApi.getPatientTimeline).toHaveBeenCalledWith(
      'patient-123',
      expect.objectContaining({
        conceptCuis: ['C0011849']
      })
    )
  })

  it('applyFilters handles API errors gracefully', async () => {
    const patientId = ref('patient-123')
    vi.mocked(timelineApi.getPatientTimeline).mockRejectedValue(new Error('Network error'))

    const { applyFilters, error, isLoading } = useTimelineFilters(patientId)

    await applyFilters()

    expect(isLoading.value).toBe(false)
    expect(error.value).toBe('Network error')
  })

  it('syncFiltersToURL updates router query params', () => {
    const patientId = ref('patient-123')
    const { setConceptFilter, setDateRange, syncFiltersToURL } = useTimelineFilters(patientId)

    setConceptFilter(['C0011849', 'C0020538'])
    setDateRange(new Date('2023-01-01'), new Date('2023-12-31'))
    syncFiltersToURL()

    expect(mockRouter.push).toHaveBeenCalledWith({
      query: expect.objectContaining({
        concepts: 'C0011849,C0020538',
        from: '2023-01-01',
        to: '2023-12-31'
      })
    })
  })

  it('loadFiltersFromURL deserializes URL query params', () => {
    mockRoute.query = {
      concepts: 'C0011849,C0020538',
      from: '2023-01-01',
      to: '2023-12-31',
      meta_negation: 'Affirmed',
      meta_experiencer: 'Patient',
      meta_temporality: 'Current,Recent',
      types: 'clinical_note,discharge_summary'
    }

    const patientId = ref('patient-123')
    const { filters, loadFiltersFromURL } = useTimelineFilters(patientId)

    loadFiltersFromURL()

    expect(filters.value.conceptCuis).toEqual(['C0011849', 'C0020538'])
    expect(filters.value.dateFrom).toEqual(new Date('2023-01-01'))
    expect(filters.value.dateTo).toEqual(new Date('2023-12-31'))
    expect(filters.value.metaAnnotations.Negation).toBe('Affirmed')
    expect(filters.value.metaAnnotations.Experiencer).toBe('Patient')
    expect(filters.value.metaAnnotations.Temporality).toEqual(['Current', 'Recent'])
    expect(filters.value.documentTypes).toEqual(['clinical_note', 'discharge_summary'])
  })

  it('handles invalid URL query params gracefully', () => {
    mockRoute.query = {
      concepts: '',
      from: 'invalid-date',
      types: ''
    }

    const patientId = ref('patient-123')
    const { filters, loadFiltersFromURL } = useTimelineFilters(patientId)

    // Should not throw error
    expect(() => loadFiltersFromURL()).not.toThrow()

    // Should use defaults for invalid values
    expect(filters.value.conceptCuis).toEqual([])
    expect(filters.value.dateFrom).toBeNull()
    expect(filters.value.documentTypes).toEqual([])
  })

  it('activeFilterCount counts active filters correctly', () => {
    const patientId = ref('patient-123')
    const { activeFilterCount, setConceptFilter, setDateRange, setDocumentTypeFilter, setMetaAnnotationFilter } = useTimelineFilters(patientId)

    expect(activeFilterCount.value).toBe(0)

    setConceptFilter(['C0011849'])
    expect(activeFilterCount.value).toBe(1)

    setDateRange(new Date('2023-01-01'), new Date('2023-12-31'))
    expect(activeFilterCount.value).toBe(2)

    setDocumentTypeFilter(['clinical_note'])
    expect(activeFilterCount.value).toBe(3)

    setMetaAnnotationFilter('Negation', 'Negated')
    expect(activeFilterCount.value).toBe(4)
  })

  it('hasActiveFilters returns false when only default meta-annotations are set', () => {
    const patientId = ref('patient-123')
    const { hasActiveFilters } = useTimelineFilters(patientId)

    // Only default meta-annotations (Negation: Affirmed, Experiencer: Patient, Temporality: [Current, Recent])
    expect(hasActiveFilters.value).toBe(false)
  })

  it('hasActiveFilters returns true when meta-annotations differ from defaults', () => {
    const patientId = ref('patient-123')
    const { hasActiveFilters, setMetaAnnotationFilter } = useTimelineFilters(patientId)

    setMetaAnnotationFilter('Negation', 'Negated')
    expect(hasActiveFilters.value).toBe(true)
  })
})
