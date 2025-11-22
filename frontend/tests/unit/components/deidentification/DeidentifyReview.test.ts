/**
 * Tests for DeidentifyReview component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import DeidentifyReview from '@/components/deidentification/DeidentifyReview.vue'
import { DeidentificationMethod } from '@/types/deidentification'
import type { DeidentifiedNoteResult } from '@/types/deidentification'

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
const mockJobResults = vi.fn<[], DeidentifiedNoteResult[]>()

vi.mock('@/composables/useDeidentification', () => ({
  useDeidentification: () => ({
    jobResults: { value: mockJobResults() },
    isJobResultsLoading: false,
    jobResultsError: null,
    fetchJobResults: mockFetchJobResults
  })
}))

const vuetify = createVuetify({
  components,
  directives
})

describe('DeidentifyReview.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render side-by-side comparison', () => {
    // Arrange
    const results: DeidentifiedNoteResult[] = [
      {
        job_id: 'job-123',
        note_id: 'note-1',
        deidentified_text: 'Patient [NAME] was admitted on [DATE]',
        entities_removed: [
          { type: 'NAME', text: 'John Doe', start: 8, end: 16, confidence: 0.95 },
          { type: 'DATE', text: '01/15/2024', start: 30, end: 40, confidence: 0.92 }
        ],
        method_used: DeidentificationMethod.REPLACEMENT,
        confidence_score: 0.935,
        review_required: false,
        created_at: '2024-01-15T10:00:00Z'
      }
    ]

    mockJobResults.mockReturnValue(results)

    // Act
    const wrapper = mount(DeidentifyReview, {
      global: {
        plugins: [vuetify]
      }
    })

    // Assert
    expect(wrapper.text()).toContain('Original Note (Contains PHI)')
    expect(wrapper.text()).toContain('De-identified Note')
    expect(wrapper.text()).toContain('Patient [NAME] was admitted on [DATE]')
  })

  it('should display entities removed table', () => {
    // Arrange
    const results: DeidentifiedNoteResult[] = [
      {
        job_id: 'job-123',
        note_id: 'note-1',
        deidentified_text: 'Text',
        entities_removed: [
          { type: 'NAME', text: 'John Doe', start: 0, end: 8, confidence: 0.95 },
          { type: 'SSN', text: '123-45-6789', start: 10, end: 21, confidence: 0.99 }
        ],
        method_used: DeidentificationMethod.REMOVAL,
        confidence_score: 0.97,
        review_required: false,
        created_at: '2024-01-15T10:00:00Z'
      }
    ]

    mockJobResults.mockReturnValue(results)

    // Act
    const wrapper = mount(DeidentifyReview, {
      global: {
        plugins: [vuetify]
      }
    })

    // Assert
    expect(wrapper.text()).toContain('PHI Entities Removed (2)')
    expect(wrapper.text()).toContain('NAME')
    expect(wrapper.text()).toContain('SSN')
  })

  it('should navigate between notes', async () => {
    // Arrange
    const results: DeidentifiedNoteResult[] = [
      {
        job_id: 'job-123',
        note_id: 'note-1',
        deidentified_text: 'First note',
        entities_removed: [],
        method_used: DeidentificationMethod.REMOVAL,
        confidence_score: 0.9,
        review_required: false,
        created_at: '2024-01-15T10:00:00Z'
      },
      {
        job_id: 'job-123',
        note_id: 'note-2',
        deidentified_text: 'Second note',
        entities_removed: [],
        method_used: DeidentificationMethod.REMOVAL,
        confidence_score: 0.95,
        review_required: false,
        created_at: '2024-01-15T10:01:00Z'
      }
    ]

    mockJobResults.mockReturnValue(results)

    const wrapper = mount(DeidentifyReview, {
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Assert initial state
    expect(vm.currentIndex).toBe(0)
    expect(vm.currentNote.note_id).toBe('note-1')

    // Act - Go to next note
    vm.nextNote()

    // Assert
    expect(vm.currentIndex).toBe(1)
    expect(vm.currentNote.note_id).toBe('note-2')

    // Act - Go back to previous note
    vm.previousNote()

    // Assert
    expect(vm.currentIndex).toBe(0)
    expect(vm.currentNote.note_id).toBe('note-1')
  })

  it('should fetch results on mount', () => {
    // Arrange & Act
    mount(DeidentifyReview, {
      global: {
        plugins: [vuetify]
      }
    })

    // Assert
    expect(mockFetchJobResults).toHaveBeenCalledWith('job-123', 100, 0)
  })

  it('should show empty state when no results', () => {
    // Arrange
    mockJobResults.mockReturnValue([])

    // Act
    const wrapper = mount(DeidentifyReview, {
      global: {
        plugins: [vuetify]
      }
    })

    // Assert
    expect(wrapper.text()).toContain('No results available')
  })

  it('should color-code confidence scores', () => {
    // Arrange
    const results: DeidentifiedNoteResult[] = [
      {
        job_id: 'job-123',
        note_id: 'note-1',
        deidentified_text: 'Text',
        entities_removed: [
          { type: 'NAME', text: 'John', start: 0, end: 4, confidence: 0.95 }, // Green
          { type: 'DATE', text: 'Jan', start: 5, end: 8, confidence: 0.85 }, // Yellow
          { type: 'AGE', text: '65', start: 9, end: 11, confidence: 0.75 }  // Red
        ],
        method_used: DeidentificationMethod.REPLACEMENT,
        confidence_score: 0.85,
        review_required: false,
        created_at: '2024-01-15T10:00:00Z'
      }
    ]

    mockJobResults.mockReturnValue(results)

    const wrapper = mount(DeidentifyReview, {
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Assert - Test confidence color function
    expect(vm.getConfidenceAlertType(0.95)).toBe('success')
    expect(vm.getConfidenceAlertType(0.85)).toBe('warning')
    expect(vm.getConfidenceAlertType(0.75)).toBe('error')
  })
})
