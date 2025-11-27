/**
 * Timeline Export Composable
 *
 * Handles timeline export operations (PDF, FHIR, JSON) with error handling.
 */

import { ref } from 'vue'
import api from '@/api/client'

export interface ExportRequest {
  format: 'pdf' | 'fhir' | 'json'
  filters?: any
  options?: {
    de_identified?: boolean
    watermark?: boolean
  }
}

export interface ExportResponse {
  export_id: string
  status: string
  format: string
  content_type: string
  data?: any  // Base64 string for PDF, dict for JSON/FHIR
  download_url?: string
  created_at: string
  expires_at?: string
}

export function useTimelineExport() {
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Export patient timeline to specified format
   */
  const exportTimeline = async (
    patientId: string,
    format: 'pdf' | 'fhir' | 'json',
    filters?: any,
    options?: any
  ): Promise<ExportResponse> => {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.post<ExportResponse>(
        `/api/v1/timeline/${patientId}/export`,
        {
          format,
          filters: filters || null,
          options: options || null
        }
      )

      return response.data
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Export failed'
      error.value = errorMessage
      throw new Error(errorMessage)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Download exported PDF (base64 decode and trigger download)
   */
  const downloadPDF = (base64Data: string, filename: string = 'timeline.pdf') => {
    try {
      // Decode base64 to binary
      const binaryString = atob(base64Data)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }

      // Create blob and download
      const blob = new Blob([bytes], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()

      // Cleanup
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      error.value = `Download failed: ${err.message}`
      throw err
    }
  }

  /**
   * Download JSON export
   */
  const downloadJSON = (data: any, filename: string = 'timeline.json') => {
    try {
      const jsonString = JSON.stringify(data, null, 2)
      const blob = new Blob([jsonString], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()

      // Cleanup
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      error.value = `Download failed: ${err.message}`
      throw err
    }
  }

  return {
    isLoading,
    error,
    exportTimeline,
    downloadPDF,
    downloadJSON
  }
}
