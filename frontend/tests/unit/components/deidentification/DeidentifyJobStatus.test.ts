/**
 * Tests for DeidentifyJobStatus component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import DeidentifyJobStatus from '@/components/deidentification/DeidentifyJobStatus.vue'
import { JobStatus } from '@/types/deidentification'
import type { DeidentificationJobStatus } from '@/types/deidentification'

// Mock router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  })
}))

// Mock composable
const mockFetchJobStatus = vi.fn()
const mockStartPolling = vi.fn()
const mockStopPolling = vi.fn()
const mockCancelCurrentJob = vi.fn()

const mockJobStatus = vi.fn<[], DeidentificationJobStatus | null>()

vi.mock('@/composables/useDeidentification', () => ({
  useDeidentification: () => ({
    jobStatus: { value: mockJobStatus() },
    isJobStatusLoading: false,
    jobStatusError: null,
    isPolling: true,
    isJobTerminal: false,
    canCancelJob: true,
    canDownloadResults: false,
    fetchJobStatus: mockFetchJobStatus,
    startPolling: mockStartPolling,
    stopPolling: mockStopPolling,
    cancelCurrentJob: mockCancelCurrentJob
  })
}))

const vuetify = createVuetify({
  components,
  directives
})

describe('DeidentifyJobStatus.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render job status with progress', () => {
    // Arrange
    const status: DeidentificationJobStatus = {
      job_id: 'job-123',
      status: JobStatus.PROCESSING,
      total_notes: 1000,
      processed_notes: 450,
      progress_percentage: 45,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:30:00Z',
      estimated_completion: '2024-01-15T11:00:00Z',
      errors: []
    }

    mockJobStatus.mockReturnValue(status)

    // Act
    const wrapper = mount(DeidentifyJobStatus, {
      props: {
        jobId: 'job-123'
      },
      global: {
        plugins: [vuetify]
      }
    })

    // Assert
    expect(wrapper.text()).toContain('job-123')
    expect(wrapper.text()).toContain('1,000') // Total notes formatted
    expect(wrapper.text()).toContain('450') // Processed notes
  })

  it('should display errors when present', () => {
    // Arrange
    const status: DeidentificationJobStatus = {
      job_id: 'job-123',
      status: JobStatus.PROCESSING,
      total_notes: 100,
      processed_notes: 95,
      progress_percentage: 95,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:30:00Z',
      estimated_completion: '2024-01-15T11:00:00Z',
      errors: [
        { note_id: 'note-1', error: 'PHI detection failed' },
        { note_id: 'note-2', error: 'Timeout' }
      ],
      error_count: 2
    }

    mockJobStatus.mockReturnValue(status)

    // Act
    const wrapper = mount(DeidentifyJobStatus, {
      props: {
        jobId: 'job-123'
      },
      global: {
        plugins: [vuetify]
      }
    })

    // Assert
    expect(wrapper.text()).toContain('Errors (2)')
  })

  it('should start polling on mount', () => {
    // Arrange & Act
    mount(DeidentifyJobStatus, {
      props: {
        jobId: 'job-123'
      },
      global: {
        plugins: [vuetify]
      }
    })

    // Assert
    expect(mockStartPolling).toHaveBeenCalledWith('job-123')
  })

  it('should stop polling on unmount', () => {
    // Arrange
    const wrapper = mount(DeidentifyJobStatus, {
      props: {
        jobId: 'job-123'
      },
      global: {
        plugins: [vuetify]
      }
    })

    // Act
    wrapper.unmount()

    // Assert
    expect(mockStopPolling).toHaveBeenCalled()
  })

  it('should calculate time remaining estimate', () => {
    // Arrange
    const now = new Date()
    const created = new Date(now.getTime() - 30 * 60 * 1000) // 30 minutes ago

    const status: DeidentificationJobStatus = {
      job_id: 'job-123',
      status: JobStatus.PROCESSING,
      total_notes: 1000,
      processed_notes: 500, // 50% complete in 30 minutes = 30 minutes remaining
      progress_percentage: 50,
      created_at: created.toISOString(),
      updated_at: now.toISOString(),
      estimated_completion: '2024-01-15T11:00:00Z',
      errors: []
    }

    mockJobStatus.mockReturnValue(status)

    // Act
    const wrapper = mount(DeidentifyJobStatus, {
      props: {
        jobId: 'job-123'
      },
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Assert
    expect(vm.timeRemaining).toContain('minute') // Should show minutes remaining
  })

  it('should handle cancel job action', async () => {
    // Arrange
    const status: DeidentificationJobStatus = {
      job_id: 'job-123',
      status: JobStatus.PROCESSING,
      total_notes: 100,
      processed_notes: 50,
      progress_percentage: 50,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:30:00Z',
      estimated_completion: '2024-01-15T11:00:00Z',
      errors: []
    }

    mockJobStatus.mockReturnValue(status)
    mockCancelCurrentJob.mockResolvedValue(true)

    // Mock window.confirm
    global.confirm = vi.fn(() => true)

    const wrapper = mount(DeidentifyJobStatus, {
      props: {
        jobId: 'job-123'
      },
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Act
    await vm.handleCancelJob()

    // Assert
    expect(global.confirm).toHaveBeenCalled()
    expect(mockCancelCurrentJob).toHaveBeenCalledWith('job-123')
  })

  it('should navigate to review when clicking review results', () => {
    // Arrange
    const status: DeidentificationJobStatus = {
      job_id: 'job-123',
      status: JobStatus.COMPLETED,
      total_notes: 100,
      processed_notes: 100,
      progress_percentage: 100,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T11:00:00Z',
      estimated_completion: '2024-01-15T11:00:00Z',
      errors: []
    }

    mockJobStatus.mockReturnValue(status)

    const wrapper = mount(DeidentifyJobStatus, {
      props: {
        jobId: 'job-123'
      },
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Act
    vm.handleReviewResults()

    // Assert
    expect(mockPush).toHaveBeenCalledWith('/deidentify/jobs/job-123/review')
  })

  it('should refresh job status manually', async () => {
    // Arrange
    const status: DeidentificationJobStatus = {
      job_id: 'job-123',
      status: JobStatus.PROCESSING,
      total_notes: 100,
      processed_notes: 75,
      progress_percentage: 75,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:45:00Z',
      estimated_completion: '2024-01-15T11:00:00Z',
      errors: []
    }

    mockJobStatus.mockReturnValue(status)

    const wrapper = mount(DeidentifyJobStatus, {
      props: {
        jobId: 'job-123'
      },
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Act
    await vm.handleRefresh()

    // Assert
    expect(mockFetchJobStatus).toHaveBeenCalledWith('job-123')
  })
})
