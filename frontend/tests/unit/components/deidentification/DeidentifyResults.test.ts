/**
 * Tests for DeidentifyResults component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import DeidentifyResults from '@/components/deidentification/DeidentifyResults.vue'
import { DeidentificationMethod, JobStatus } from '@/types/deidentification'
import type { DeidentifiedNoteResult, DeidentificationJobStatus } from '@/types/deidentification'

// Mock route
const mockRoute = {
  params: {
    jobId: 'job-123'
  }
}

vi.mock('vue-router', () => ({
  useRoute: () => mockRoute
}))

// Mock composable
const mockFetchJobResults = vi.fn()
const mockFetchJobStatus = vi.fn()
const mockDownloadJobResults = vi.fn()
const mockDownloadAudit = vi.fn()
const mockJobResults = vi.fn<[], DeidentifiedNoteResult[]>()
const mockJobStatus = vi.fn<[], DeidentificationJobStatus | null>()

vi.mock('@/composables/useDeidentification', () => ({
  useDeidentification: () => ({
    jobResults: { value: mockJobResults() },
    isJobResultsLoading: false,
    jobResultsError: null,
    jobStatus: { value: mockJobStatus() },
    fetchJobResults: mockFetchJobResults,
    fetchJobStatus: mockFetchJobStatus,
    downloadJobResults: mockDownloadJobResults,
    downloadAudit: mockDownloadAudit
  })
}))

const vuetify = createVuetify({
  components,
  directives
})

describe('DeidentifyResults.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render results table', () => {
    // Arrange
    const results: DeidentifiedNoteResult[] = [
      {
        job_id: 'job-123',
        note_id: 'note-1',
        deidentified_text: 'Text 1',
        entities_removed: [
          { type: 'NAME', text: 'John', start: 0, end: 4, confidence: 0.95 }
        ],
        method_used: DeidentificationMethod.REPLACEMENT,
        confidence_score: 0.95,
        review_required: false,
        created_at: '2024-01-15T10:00:00Z'
      }
    ]

    const status: DeidentificationJobStatus = {
      job_id: 'job-123',
      status: JobStatus.COMPLETED,
      total_notes: 1,
      processed_notes: 1,
      progress_percentage: 100,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:01:00Z',
      estimated_completion: '2024-01-15T10:01:00Z',
      errors: []
    }

    mockJobResults.mockReturnValue(results)
    mockJobStatus.mockReturnValue(status)

    // Act
    const wrapper = mount(DeidentifyResults, {
      global: {
        plugins: [vuetify]
      }
    })

    // Assert
    expect(wrapper.text()).toContain('De-identification Results')
    expect(wrapper.text()).toContain('note-1')
  })

  it('should filter results by confidence score', () => {
    // Arrange
    const results: DeidentifiedNoteResult[] = [
      {
        job_id: 'job-123',
        note_id: 'note-1',
        deidentified_text: 'High confidence',
        entities_removed: [],
        method_used: DeidentificationMethod.REMOVAL,
        confidence_score: 0.95, // High
        review_required: false,
        created_at: '2024-01-15T10:00:00Z'
      },
      {
        job_id: 'job-123',
        note_id: 'note-2',
        deidentified_text: 'Medium confidence',
        entities_removed: [],
        method_used: DeidentificationMethod.REMOVAL,
        confidence_score: 0.85, // Medium
        review_required: false,
        created_at: '2024-01-15T10:01:00Z'
      },
      {
        job_id: 'job-123',
        note_id: 'note-3',
        deidentified_text: 'Low confidence',
        entities_removed: [],
        method_used: DeidentificationMethod.REMOVAL,
        confidence_score: 0.75, // Low
        review_required: true,
        created_at: '2024-01-15T10:02:00Z'
      }
    ]

    mockJobResults.mockReturnValue(results)
    mockJobStatus.mockReturnValue(null)

    const wrapper = mount(DeidentifyResults, {
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Act & Assert - Filter for high confidence (>=90%)
    vm.confidenceFilter = '>0.9'
    expect(vm.filteredResults).toHaveLength(1)
    expect(vm.filteredResults[0].note_id).toBe('note-1')

    // Act & Assert - Filter for medium confidence (>=80%)
    vm.confidenceFilter = '>0.8'
    expect(vm.filteredResults).toHaveLength(2)

    // Act & Assert - Filter for low confidence (<80%)
    vm.confidenceFilter = '<0.8'
    expect(vm.filteredResults).toHaveLength(1)
    expect(vm.filteredResults[0].note_id).toBe('note-3')

    // Act & Assert - All
    vm.confidenceFilter = 'All'
    expect(vm.filteredResults).toHaveLength(3)
  })

  it('should filter results by review status', () => {
    // Arrange
    const results: DeidentifiedNoteResult[] = [
      {
        job_id: 'job-123',
        note_id: 'note-1',
        deidentified_text: 'Needs review',
        entities_removed: [],
        method_used: DeidentificationMethod.REMOVAL,
        confidence_score: 0.75,
        review_required: true,
        created_at: '2024-01-15T10:00:00Z'
      },
      {
        job_id: 'job-123',
        note_id: 'note-2',
        deidentified_text: 'OK',
        entities_removed: [],
        method_used: DeidentificationMethod.REMOVAL,
        confidence_score: 0.95,
        review_required: false,
        created_at: '2024-01-15T10:01:00Z'
      }
    ]

    mockJobResults.mockReturnValue(results)
    mockJobStatus.mockReturnValue(null)

    const wrapper = mount(DeidentifyResults, {
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Act & Assert - Filter for review required
    vm.reviewFilter = 'review'
    expect(vm.filteredResults).toHaveLength(1)
    expect(vm.filteredResults[0].review_required).toBe(true)

    // Act & Assert - Filter for OK
    vm.reviewFilter = 'ok'
    expect(vm.filteredResults).toHaveLength(1)
    expect(vm.filteredResults[0].review_required).toBe(false)

    // Act & Assert - All
    vm.reviewFilter = 'All'
    expect(vm.filteredResults).toHaveLength(2)
  })

  it('should download results as CSV', async () => {
    // Arrange
    mockDownloadJobResults.mockResolvedValue(true)

    const wrapper = mount(DeidentifyResults, {
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Act
    await vm.handleDownload('csv')

    // Assert
    expect(mockDownloadJobResults).toHaveBeenCalledWith('job-123', 'csv')
  })

  it('should download audit report as PDF', async () => {
    // Arrange
    mockDownloadAudit.mockResolvedValue(true)

    const wrapper = mount(DeidentifyResults, {
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Act
    await vm.handleDownloadAudit()

    // Assert
    expect(mockDownloadAudit).toHaveBeenCalledWith('job-123')
  })

  it('should fetch job status and results on mount', () => {
    // Arrange & Act
    mount(DeidentifyResults, {
      global: {
        plugins: [vuetify]
      }
    })

    // Assert
    expect(mockFetchJobStatus).toHaveBeenCalledWith('job-123')
    expect(mockFetchJobResults).toHaveBeenCalledWith('job-123', 1000, 0)
  })
})
