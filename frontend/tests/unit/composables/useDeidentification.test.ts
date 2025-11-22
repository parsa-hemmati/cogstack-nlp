/**
 * Tests for useDeidentification composable
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useDeidentification } from '@/composables/useDeidentification'
import * as deidentificationApi from '@/api/deidentification'
import { DeidentificationMethod, JobStatus } from '@/types/deidentification'
import type {
  DeidentifyResponse,
  BatchDeidentifyResponse,
  DeidentificationJobStatus
} from '@/types/deidentification'

// Mock the API module
vi.mock('@/api/deidentification')

describe('useDeidentification', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  describe('deidentifyNote', () => {
    it('should de-identify a single note successfully', async () => {
      // Arrange
      const mockResponse: DeidentifyResponse = {
        deidentified_text: 'Patient [NAME] was admitted on [DATE]',
        entities_removed: [
          { type: 'NAME', text: 'John Doe', start: 8, end: 16, confidence: 0.95 },
          { type: 'DATE', text: '01/15/2024', start: 30, end: 40, confidence: 0.92 }
        ],
        method_used: DeidentificationMethod.REPLACEMENT,
        confidence_score: 0.935,
        review_required: false,
        processing_time_ms: 450
      }

      vi.mocked(deidentificationApi.deidentifySingleNote).mockResolvedValue(mockResponse)

      const { deidentifyNote, singleNoteResult, isSingleNoteLoading } = useDeidentification()

      // Act
      const result = await deidentifyNote(
        'Patient John Doe was admitted on 01/15/2024',
        DeidentificationMethod.REPLACEMENT
      )

      // Assert
      expect(result).toEqual(mockResponse)
      expect(singleNoteResult.value).toEqual(mockResponse)
      expect(isSingleNoteLoading.value).toBe(false)
      expect(deidentificationApi.deidentifySingleNote).toHaveBeenCalledWith({
        text: 'Patient John Doe was admitted on 01/15/2024',
        method: DeidentificationMethod.REPLACEMENT,
        return_entities: true
      })
    })

    it('should handle de-identification errors', async () => {
      // Arrange
      const error = new Error('API Error')
      vi.mocked(deidentificationApi.deidentifySingleNote).mockRejectedValue(error)

      const { deidentifyNote, singleNoteError } = useDeidentification()

      // Act
      const result = await deidentifyNote('Test text', DeidentificationMethod.REMOVAL)

      // Assert
      expect(result).toBeNull()
      expect(singleNoteError.value).toBe('API Error')
    })

    it('should set loading state during de-identification', async () => {
      // Arrange
      vi.mocked(deidentificationApi.deidentifySingleNote).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      const { deidentifyNote, isSingleNoteLoading } = useDeidentification()

      // Act
      const promise = deidentifyNote('Test text', DeidentificationMethod.REMOVAL)
      expect(isSingleNoteLoading.value).toBe(true)

      await promise
      expect(isSingleNoteLoading.value).toBe(false)
    })
  })

  describe('uploadCSV', () => {
    it('should upload CSV file successfully', async () => {
      // Arrange
      const mockJob: BatchDeidentifyResponse = {
        job_id: '550e8400-e29b-41d4-a716-446655440000',
        status: JobStatus.PENDING,
        total_notes: 100,
        created_at: '2024-01-15T10:00:00Z',
        estimated_completion: '2024-01-15T11:00:00Z'
      }

      vi.mocked(deidentificationApi.uploadCSVForDeidentification).mockResolvedValue(mockJob)

      const { uploadCSV, currentJob } = useDeidentification()
      const mockFile = new File(['note1,Patient data'], 'notes.csv', { type: 'text/csv' })

      // Act
      const result = await uploadCSV(mockFile, DeidentificationMethod.REPLACEMENT, 'test@example.com')

      // Assert
      expect(result).toEqual(mockJob)
      expect(currentJob.value).toEqual(mockJob)
      expect(deidentificationApi.uploadCSVForDeidentification).toHaveBeenCalledWith(
        mockFile,
        DeidentificationMethod.REPLACEMENT,
        'test@example.com'
      )
    })

    it('should handle CSV upload errors', async () => {
      // Arrange
      const error = new Error('File too large')
      vi.mocked(deidentificationApi.uploadCSVForDeidentification).mockRejectedValue(error)

      const { uploadCSV, batchUploadError } = useDeidentification()
      const mockFile = new File(['data'], 'notes.csv', { type: 'text/csv' })

      // Act
      const result = await uploadCSV(mockFile, DeidentificationMethod.REPLACEMENT)

      // Assert
      expect(result).toBeNull()
      expect(batchUploadError.value).toBe('File too large')
    })
  })

  describe('fetchJobStatus', () => {
    it('should fetch job status successfully', async () => {
      // Arrange
      const mockStatus: DeidentificationJobStatus = {
        job_id: '550e8400-e29b-41d4-a716-446655440000',
        status: JobStatus.PROCESSING,
        total_notes: 100,
        processed_notes: 50,
        progress_percentage: 50,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:30:00Z',
        estimated_completion: '2024-01-15T11:00:00Z',
        errors: []
      }

      vi.mocked(deidentificationApi.getJobStatus).mockResolvedValue(mockStatus)

      const { fetchJobStatus, jobStatus } = useDeidentification()

      // Act
      const result = await fetchJobStatus('550e8400-e29b-41d4-a716-446655440000')

      // Assert
      expect(result).toEqual(mockStatus)
      expect(jobStatus.value).toEqual(mockStatus)
    })

    it('should handle job status errors', async () => {
      // Arrange
      const error = new Error('Job not found')
      vi.mocked(deidentificationApi.getJobStatus).mockRejectedValue(error)

      const { fetchJobStatus, jobStatusError } = useDeidentification()

      // Act
      const result = await fetchJobStatus('invalid-id')

      // Assert
      expect(result).toBeNull()
      expect(jobStatusError.value).toBe('Job not found')
    })
  })

  describe('startPolling and stopPolling', () => {
    it('should poll job status every 5 seconds', async () => {
      // Arrange
      vi.useFakeTimers()

      const mockStatus: DeidentificationJobStatus = {
        job_id: '550e8400-e29b-41d4-a716-446655440000',
        status: JobStatus.PROCESSING,
        total_notes: 100,
        processed_notes: 25,
        progress_percentage: 25,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:30:00Z',
        estimated_completion: '2024-01-15T11:00:00Z',
        errors: []
      }

      vi.mocked(deidentificationApi.getJobStatus).mockResolvedValue(mockStatus)

      const { startPolling, isPolling } = useDeidentification()

      // Act
      startPolling('550e8400-e29b-41d4-a716-446655440000')

      // Assert
      expect(isPolling.value).toBe(true)
      expect(deidentificationApi.getJobStatus).toHaveBeenCalledTimes(1)

      // Fast-forward 5 seconds
      await vi.advanceTimersByTimeAsync(5000)
      expect(deidentificationApi.getJobStatus).toHaveBeenCalledTimes(2)

      // Fast-forward another 5 seconds
      await vi.advanceTimersByTimeAsync(5000)
      expect(deidentificationApi.getJobStatus).toHaveBeenCalledTimes(3)

      vi.useRealTimers()
    })

    it('should stop polling when job is completed', async () => {
      // Arrange
      vi.useFakeTimers()

      const mockStatusProcessing: DeidentificationJobStatus = {
        job_id: '550e8400-e29b-41d4-a716-446655440000',
        status: JobStatus.PROCESSING,
        total_notes: 100,
        processed_notes: 90,
        progress_percentage: 90,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:45:00Z',
        estimated_completion: '2024-01-15T11:00:00Z',
        errors: []
      }

      const mockStatusCompleted: DeidentificationJobStatus = {
        ...mockStatusProcessing,
        status: JobStatus.COMPLETED,
        processed_notes: 100,
        progress_percentage: 100
      }

      vi.mocked(deidentificationApi.getJobStatus)
        .mockResolvedValueOnce(mockStatusProcessing)
        .mockResolvedValueOnce(mockStatusCompleted)

      const { startPolling, isPolling } = useDeidentification()

      // Act
      startPolling('550e8400-e29b-41d4-a716-446655440000')

      // Assert
      expect(isPolling.value).toBe(true)

      // Fast-forward 5 seconds
      await vi.advanceTimersByTimeAsync(5000)

      // Should stop polling after job completes
      expect(isPolling.value).toBe(false)

      vi.useRealTimers()
    })

    it('should manually stop polling', async () => {
      // Arrange
      vi.useFakeTimers()

      const mockStatus: DeidentificationJobStatus = {
        job_id: '550e8400-e29b-41d4-a716-446655440000',
        status: JobStatus.PROCESSING,
        total_notes: 100,
        processed_notes: 50,
        progress_percentage: 50,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:30:00Z',
        estimated_completion: '2024-01-15T11:00:00Z',
        errors: []
      }

      vi.mocked(deidentificationApi.getJobStatus).mockResolvedValue(mockStatus)

      const { startPolling, stopPolling, isPolling } = useDeidentification()

      // Act
      startPolling('550e8400-e29b-41d4-a716-446655440000')
      expect(isPolling.value).toBe(true)

      stopPolling()

      // Assert
      expect(isPolling.value).toBe(false)

      // Fast-forward 10 seconds - should not make additional calls
      await vi.advanceTimersByTimeAsync(10000)
      expect(deidentificationApi.getJobStatus).toHaveBeenCalledTimes(1) // Only initial call

      vi.useRealTimers()
    })
  })

  describe('downloadJobResults', () => {
    it('should download results as CSV', async () => {
      // Arrange
      const mockBlob = new Blob(['data'], { type: 'text/csv' })
      vi.mocked(deidentificationApi.downloadResults).mockResolvedValue(mockBlob)

      // Mock DOM methods
      const createElementSpy = vi.spyOn(document, 'createElement')
      const appendChildSpy = vi.spyOn(document.body, 'appendChild')
      const removeChildSpy = vi.spyOn(document.body, 'removeChild')

      const mockLink = {
        href: '',
        download: '',
        click: vi.fn()
      } as any

      createElementSpy.mockReturnValue(mockLink)

      const { downloadJobResults } = useDeidentification()

      // Act
      const success = await downloadJobResults('job-123', 'csv')

      // Assert
      expect(success).toBe(true)
      expect(deidentificationApi.downloadResults).toHaveBeenCalledWith('job-123', 'csv')
      expect(mockLink.download).toBe('deidentified_job-123.csv')
      expect(mockLink.click).toHaveBeenCalled()

      // Cleanup
      createElementSpy.mockRestore()
      appendChildSpy.mockRestore()
      removeChildSpy.mockRestore()
    })

    it('should handle download errors', async () => {
      // Arrange
      const error = new Error('Download failed')
      vi.mocked(deidentificationApi.downloadResults).mockRejectedValue(error)

      const { downloadJobResults, jobStatusError } = useDeidentification()

      // Act
      const success = await downloadJobResults('job-123', 'json')

      // Assert
      expect(success).toBe(false)
      expect(jobStatusError.value).toBe('Download failed')
    })
  })

  describe('reset', () => {
    it('should reset all state', async () => {
      // Arrange
      const mockResponse: DeidentifyResponse = {
        deidentified_text: 'Text',
        entities_removed: [],
        method_used: DeidentificationMethod.REMOVAL,
        confidence_score: 0.9,
        review_required: false,
        processing_time_ms: 100
      }

      vi.mocked(deidentificationApi.deidentifySingleNote).mockResolvedValue(mockResponse)

      const {
        deidentifyNote,
        reset,
        singleNoteResult,
        singleNoteError,
        currentJob,
        jobStatus
      } = useDeidentification()

      // Act - Add some state
      await deidentifyNote('Test', DeidentificationMethod.REMOVAL)
      expect(singleNoteResult.value).not.toBeNull()

      // Reset
      reset()

      // Assert
      expect(singleNoteResult.value).toBeNull()
      expect(singleNoteError.value).toBeNull()
      expect(currentJob.value).toBeNull()
      expect(jobStatus.value).toBeNull()
    })
  })
})
