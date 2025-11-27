/**
 * De-identification Composable
 *
 * Provides reactive state and methods for de-identification workflow
 */
import { ref, computed, onUnmounted } from 'vue'
import type { Ref } from 'vue'
import {
  deidentifySingleNote,
  deidentifyBatch,
  uploadCSVForDeidentification,
  getJobStatus,
  cancelJob,
  downloadResults,
  getJobResults,
  downloadAuditReport
} from '@/api/deidentification'
import type {
  DeidentifyRequest,
  DeidentifyResponse,
  BatchDeidentifyRequest,
  BatchDeidentifyResponse,
  DeidentificationJobStatus,
  DeidentifiedNoteResult,
  DeidentificationMethod,
  JobStatus,
  DownloadFormat
} from '@/types/deidentification'

export function useDeidentification() {
  // Single note state
  const singleNoteResult = ref<DeidentifyResponse | null>(null)
  const isSingleNoteLoading = ref(false)
  const singleNoteError = ref<string | null>(null)

  // Batch upload state
  const currentJob = ref<BatchDeidentifyResponse | null>(null)
  const isBatchUploading = ref(false)
  const batchUploadError = ref<string | null>(null)

  // Job status state
  const jobStatus = ref<DeidentificationJobStatus | null>(null)
  const isJobStatusLoading = ref(false)
  const jobStatusError = ref<string | null>(null)

  // Job results state
  const jobResults = ref<DeidentifiedNoteResult[]>([])
  const isJobResultsLoading = ref(false)
  const jobResultsError = ref<string | null>(null)

  // Polling state
  let pollingInterval: ReturnType<typeof setInterval> | null = null
  const isPolling = ref(false)
  const pollingIntervalMs = 5000 // 5 seconds

  /**
   * Computed: Job is in terminal state (completed, failed, cancelled)
   */
  const isJobTerminal = computed(() => {
    if (!jobStatus.value) return false
    return [
      'completed' as JobStatus,
      'failed' as JobStatus,
      'cancelled' as JobStatus
    ].includes(jobStatus.value.status)
  })

  /**
   * Computed: Job can be cancelled (pending or processing)
   */
  const canCancelJob = computed(() => {
    if (!jobStatus.value) return false
    return [
      'pending' as JobStatus,
      'processing' as JobStatus
    ].includes(jobStatus.value.status)
  })

  /**
   * Computed: Job is ready for download (completed)
   */
  const canDownloadResults = computed(() => {
    return jobStatus.value?.status === ('completed' as JobStatus)
  })

  /**
   * De-identify a single note
   */
  async function deidentifyNote(
    text: string,
    method: DeidentificationMethod,
    returnEntities: boolean = true
  ): Promise<DeidentifyResponse | null> {
    isSingleNoteLoading.value = true
    singleNoteError.value = null
    singleNoteResult.value = null

    try {
      const request: DeidentifyRequest = {
        text,
        method,
        return_entities: returnEntities
      }

      const result = await deidentifySingleNote(request)
      singleNoteResult.value = result
      return result
    } catch (error: any) {
      singleNoteError.value = error.response?.data?.detail || error.message || 'Failed to de-identify note'
      console.error('De-identification error:', error)
      return null
    } finally {
      isSingleNoteLoading.value = false
    }
  }

  /**
   * Submit batch of notes for de-identification
   */
  async function submitBatch(
    request: BatchDeidentifyRequest
  ): Promise<BatchDeidentifyResponse | null> {
    isBatchUploading.value = true
    batchUploadError.value = null
    currentJob.value = null

    try {
      const job = await deidentifyBatch(request)
      currentJob.value = job
      return job
    } catch (error: any) {
      batchUploadError.value = error.response?.data?.detail || error.message || 'Failed to submit batch'
      console.error('Batch submission error:', error)
      return null
    } finally {
      isBatchUploading.value = false
    }
  }

  /**
   * Upload CSV file for batch de-identification
   */
  async function uploadCSV(
    file: File,
    method: DeidentificationMethod,
    notifyEmail?: string
  ): Promise<BatchDeidentifyResponse | null> {
    isBatchUploading.value = true
    batchUploadError.value = null
    currentJob.value = null

    try {
      const job = await uploadCSVForDeidentification(file, method, notifyEmail)
      currentJob.value = job
      return job
    } catch (error: any) {
      batchUploadError.value = error.response?.data?.detail || error.message || 'Failed to upload CSV'
      console.error('CSV upload error:', error)
      return null
    } finally {
      isBatchUploading.value = false
    }
  }

  /**
   * Fetch job status once
   */
  async function fetchJobStatus(jobId: string): Promise<DeidentificationJobStatus | null> {
    isJobStatusLoading.value = true
    jobStatusError.value = null

    try {
      const status = await getJobStatus(jobId)
      jobStatus.value = status
      return status
    } catch (error: any) {
      jobStatusError.value = error.response?.data?.detail || error.message || 'Failed to fetch job status'
      console.error('Job status error:', error)
      return null
    } finally {
      isJobStatusLoading.value = false
    }
  }

  /**
   * Start polling job status (every 5 seconds)
   */
  function startPolling(jobId: string) {
    // Stop existing polling
    stopPolling()

    // Initial fetch
    fetchJobStatus(jobId)

    // Start polling interval
    isPolling.value = true
    pollingInterval = setInterval(async () => {
      const status = await fetchJobStatus(jobId)

      // Stop polling if job is terminal
      if (status && isJobTerminal.value) {
        stopPolling()
      }
    }, pollingIntervalMs)
  }

  /**
   * Stop polling job status
   */
  function stopPolling() {
    if (pollingInterval) {
      clearInterval(pollingInterval)
      pollingInterval = null
    }
    isPolling.value = false
  }

  /**
   * Cancel a job
   */
  async function cancelCurrentJob(jobId: string): Promise<boolean> {
    try {
      await cancelJob(jobId)
      // Refresh status
      await fetchJobStatus(jobId)
      return true
    } catch (error: any) {
      jobStatusError.value = error.response?.data?.detail || error.message || 'Failed to cancel job'
      console.error('Job cancellation error:', error)
      return false
    }
  }

  /**
   * Download results in specified format
   */
  async function downloadJobResults(
    jobId: string,
    format: DownloadFormat
  ): Promise<boolean> {
    try {
      const blob = await downloadResults(jobId, format)

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `deidentified_${jobId}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      return true
    } catch (error: any) {
      jobStatusError.value = error.response?.data?.detail || error.message || 'Failed to download results'
      console.error('Download error:', error)
      return false
    }
  }

  /**
   * Download audit report (PDF)
   */
  async function downloadAudit(jobId: string): Promise<boolean> {
    try {
      const blob = await downloadAuditReport(jobId)

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `audit_report_${jobId}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      return true
    } catch (error: any) {
      jobStatusError.value = error.response?.data?.detail || error.message || 'Failed to download audit report'
      console.error('Audit download error:', error)
      return false
    }
  }

  /**
   * Fetch job results for review
   */
  async function fetchJobResults(
    jobId: string,
    limit: number = 20,
    offset: number = 0
  ): Promise<DeidentifiedNoteResult[]> {
    isJobResultsLoading.value = true
    jobResultsError.value = null

    try {
      const results = await getJobResults(jobId, limit, offset)
      jobResults.value = results
      return results
    } catch (error: any) {
      jobResultsError.value = error.response?.data?.detail || error.message || 'Failed to fetch results'
      console.error('Results fetch error:', error)
      return []
    } finally {
      isJobResultsLoading.value = false
    }
  }

  /**
   * Reset all state
   */
  function reset() {
    singleNoteResult.value = null
    singleNoteError.value = null
    isSingleNoteLoading.value = false

    currentJob.value = null
    batchUploadError.value = null
    isBatchUploading.value = false

    jobStatus.value = null
    jobStatusError.value = null
    isJobStatusLoading.value = false

    jobResults.value = []
    jobResultsError.value = null
    isJobResultsLoading.value = false

    stopPolling()
  }

  // Cleanup on unmount
  onUnmounted(() => {
    stopPolling()
  })

  return {
    // Single note state
    singleNoteResult,
    isSingleNoteLoading,
    singleNoteError,

    // Batch upload state
    currentJob,
    isBatchUploading,
    batchUploadError,

    // Job status state
    jobStatus,
    isJobStatusLoading,
    jobStatusError,

    // Job results state
    jobResults,
    isJobResultsLoading,
    jobResultsError,

    // Polling state
    isPolling,

    // Computed
    isJobTerminal,
    canCancelJob,
    canDownloadResults,

    // Methods
    deidentifyNote,
    submitBatch,
    uploadCSV,
    fetchJobStatus,
    startPolling,
    stopPolling,
    cancelCurrentJob,
    downloadJobResults,
    downloadAudit,
    fetchJobResults,
    reset
  }
}
