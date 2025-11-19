/**
 * Frontend component tests for DocumentHighlights.vue
 *
 * Tests expandable highlights panel with meta-annotation chips and modal.
 *
 * PRD Specification: .specify/tasks/patient-search-tasks.md (Task 4.5)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper, flushPromises } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import DocumentHighlights from '@/components/DocumentHighlights.vue'
import type { DocumentHighlight, SearchFilters, ConceptHighlightResponse } from '@/api/patientSearch'

// Create Vuetify instance for tests
const vuetify = createVuetify({
  components,
  directives,
})

// Mock API module
vi.mock('@/api/patientSearch', () => ({
  getConceptHighlights: vi.fn(),
}))

describe('DocumentHighlights.vue', () => {
  let wrapper: VueWrapper<any>
  let mockGetConceptHighlights: any

  // Test data
  const mockPatientId = 'patient-123'
  const mockConcept = 'diabetes'
  const mockFilters: SearchFilters = {
    temporal: 'current',
    includeNegated: false,
    includeFamily: false,
  }

  const mockDocuments: DocumentHighlight[] = [
    {
      documentId: 'doc-1',
      title: 'Clinical Note 2024-01-15',
      date: '2024-01-15T10:30:00Z',
      snippet: 'Patient has <b>diabetes</b> type 2',
      metaAnnotations: {
        Negation: 'Affirmed',
        Temporality: 'Current',
        Experiencer: 'Patient',
        Certainty: 'Definite',
      },
      startChar: 13,
      endChar: 21,
    },
    {
      documentId: 'doc-2',
      title: 'Lab Results 2024-01-10',
      date: '2024-01-10T14:00:00Z',
      snippet: 'No evidence of <b>diabetes</b> complications',
      metaAnnotations: {
        Negation: 'Negated',
        Temporality: 'Current',
        Experiencer: 'Patient',
        Certainty: 'Definite',
      },
      startChar: 15,
      endChar: 23,
    },
    {
      documentId: 'doc-3',
      title: 'Family History 2024-01-05',
      date: '2024-01-05T09:00:00Z',
      snippet: 'Father has <b>diabetes</b> mellitus',
      metaAnnotations: {
        Negation: 'Affirmed',
        Temporality: 'Historical',
        Experiencer: 'Family',
        Certainty: 'Definite',
      },
      startChar: 11,
      endChar: 19,
    },
  ]

  const mockResponse: ConceptHighlightResponse = {
    documents: mockDocuments,
    totalCount: 3,
  }

  beforeEach(async () => {
    // Reset mocks before each test
    vi.clearAllMocks()

    // Import mock after clearing
    const api = await import('@/api/patientSearch')
    mockGetConceptHighlights = vi.mocked(api.getConceptHighlights)
  })

  /**
   * TEST 1: Component mounting and initial loading state
   */
  it('should mount and show loading state initially', () => {
    // Arrange
    mockGetConceptHighlights.mockResolvedValue(mockResponse)

    // Act
    wrapper = mount(DocumentHighlights, {
      props: {
        patientId: mockPatientId,
        concept: mockConcept,
        filters: mockFilters,
      },
      global: {
        plugins: [vuetify],
      },
    })

    // Assert
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.v-progress-circular').exists()).toBe(true)
  })

  /**
   * TEST 2: API call on mount with correct parameters
   */
  it('should call getConceptHighlights API on mount', async () => {
    // Arrange
    mockGetConceptHighlights.mockResolvedValue(mockResponse)

    // Act
    wrapper = mount(DocumentHighlights, {
      props: {
        patientId: mockPatientId,
        concept: mockConcept,
        filters: mockFilters,
      },
      global: {
        plugins: [vuetify],
      },
    })

    await flushPromises()

    // Assert
    expect(mockGetConceptHighlights).toHaveBeenCalledWith(
      mockPatientId,
      mockConcept,
      mockFilters
    )
    expect(mockGetConceptHighlights).toHaveBeenCalledTimes(1)
  })

  /**
   * TEST 3: Document list rendering after successful fetch
   */
  it('should render document list after successful API call', async () => {
    // Arrange
    mockGetConceptHighlights.mockResolvedValue(mockResponse)

    // Act
    wrapper = mount(DocumentHighlights, {
      props: {
        patientId: mockPatientId,
        concept: mockConcept,
        filters: mockFilters,
      },
      global: {
        plugins: [vuetify],
      },
    })

    await flushPromises()

    // Assert
    expect(wrapper.find('.v-progress-circular').exists()).toBe(false)
    expect(wrapper.find('.v-list').exists()).toBe(true)
    expect(wrapper.findAll('.v-list-item')).toHaveLength(3)
  })

  /**
   * TEST 4: Snippet with highlighted concept
   */
  it('should display snippets with bolded concept', async () => {
    // Arrange
    mockGetConceptHighlights.mockResolvedValue(mockResponse)

    // Act
    wrapper = mount(DocumentHighlights, {
      props: {
        patientId: mockPatientId,
        concept: mockConcept,
        filters: mockFilters,
      },
      global: {
        plugins: [vuetify],
      },
    })

    await flushPromises()

    // Assert
    const snippets = wrapper.findAll('.snippet-container')
    expect(snippets).toHaveLength(3)

    // Check first snippet has bolded concept
    expect(snippets[0].html()).toContain('<b>diabetes</b>')
  })

  /**
   * TEST 5: Meta-annotation chips display
   */
  it('should display meta-annotation chips for each document', async () => {
    // Arrange
    mockGetConceptHighlights.mockResolvedValue(mockResponse)

    // Act
    wrapper = mount(DocumentHighlights, {
      props: {
        patientId: mockPatientId,
        concept: mockConcept,
        filters: mockFilters,
      },
      global: {
        plugins: [vuetify],
      },
    })

    await flushPromises()

    // Assert
    const listItems = wrapper.findAll('.v-list-item')
    expect(listItems).toHaveLength(3)

    // Each document should have 4 meta-annotation chips
    const firstItemChips = listItems[0].findAll('.v-chip')
    expect(firstItemChips.length).toBeGreaterThanOrEqual(4)

    // Check chip text content
    const chipTexts = firstItemChips.map((chip) => chip.text())
    expect(chipTexts.some((text) => text.includes('Affirmed'))).toBe(true)
    expect(chipTexts.some((text) => text.includes('Current'))).toBe(true)
    expect(chipTexts.some((text) => text.includes('Patient'))).toBe(true)
    expect(chipTexts.some((text) => text.includes('Definite'))).toBe(true)
  })

  /**
   * TEST 6: Color-coded chips based on meta-annotation values
   */
  it('should apply correct colors to meta-annotation chips', async () => {
    // Arrange
    mockGetConceptHighlights.mockResolvedValue(mockResponse)

    // Act
    wrapper = mount(DocumentHighlights, {
      props: {
        patientId: mockPatientId,
        concept: mockConcept,
        filters: mockFilters,
      },
      global: {
        plugins: [vuetify],
      },
    })

    await flushPromises()

    // Assert
    const listItems = wrapper.findAll('.v-list-item')

    // First document: Affirmed (green), Current (green), Patient (green)
    const doc1Chips = listItems[0].findAll('.v-chip')
    const greenChips = doc1Chips.filter((chip) => {
      const classes = chip.classes()
      return classes.some((c) => c.includes('bg-green'))
    })
    expect(greenChips.length).toBeGreaterThan(0)

    // Second document: Negated (red)
    const doc2Chips = listItems[1].findAll('.v-chip')
    const redChips = doc2Chips.filter((chip) => {
      const classes = chip.classes()
      return classes.some((c) => c.includes('bg-red'))
    })
    expect(redChips.length).toBeGreaterThan(0)
  })

  /**
   * TEST 7: Empty state when no documents found
   */
  it('should display empty state when no documents found', async () => {
    // Arrange
    mockGetConceptHighlights.mockResolvedValue({
      documents: [],
      totalCount: 0,
    })

    // Act
    wrapper = mount(DocumentHighlights, {
      props: {
        patientId: mockPatientId,
        concept: mockConcept,
        filters: mockFilters,
      },
      global: {
        plugins: [vuetify],
      },
    })

    await flushPromises()

    // Assert
    expect(wrapper.find('.v-list').exists()).toBe(false)
    expect(wrapper.text()).toContain('No documents found')
  })

  /**
   * TEST 8: Error state when API call fails
   */
  it('should display error alert when API call fails', async () => {
    // Arrange
    const errorMessage = 'Failed to load concept highlights'
    mockGetConceptHighlights.mockRejectedValue(new Error(errorMessage))

    // Act
    wrapper = mount(DocumentHighlights, {
      props: {
        patientId: mockPatientId,
        concept: mockConcept,
        filters: mockFilters,
      },
      global: {
        plugins: [vuetify],
      },
    })

    await flushPromises()

    // Assert
    expect(wrapper.find('.v-progress-circular').exists()).toBe(false)
    expect(wrapper.find('.v-alert').exists()).toBe(true)
    expect(wrapper.text()).toContain(errorMessage)
  })

  /**
   * TEST 9: Document count display
   */
  it('should display correct document count', async () => {
    // Arrange
    mockGetConceptHighlights.mockResolvedValue(mockResponse)

    // Act
    wrapper = mount(DocumentHighlights, {
      props: {
        patientId: mockPatientId,
        concept: mockConcept,
        filters: mockFilters,
      },
      global: {
        plugins: [vuetify],
      },
    })

    await flushPromises()

    // Assert
    expect(wrapper.text()).toContain('3 documents')
    expect(wrapper.text()).toContain(`containing "${mockConcept}"`)
  })

  /**
   * TEST 10: Click document to open modal
   */
  it('should open document modal when document is clicked', async () => {
    // Arrange
    mockGetConceptHighlights.mockResolvedValue(mockResponse)

    wrapper = mount(DocumentHighlights, {
      props: {
        patientId: mockPatientId,
        concept: mockConcept,
        filters: mockFilters,
      },
      global: {
        plugins: [vuetify],
        stubs: {
          DocumentModal: true, // Stub modal to avoid nested component issues
        },
      },
    })

    await flushPromises()

    // Act - Click first document
    const firstListItem = wrapper.findAll('.v-list-item')[0]
    await firstListItem.trigger('click')

    await flushPromises()

    // Assert - Modal should be rendered (stubbed version)
    expect(wrapper.findComponent({ name: 'DocumentModal' }).exists()).toBe(true)
  })
})
