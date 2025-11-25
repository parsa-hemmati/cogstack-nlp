/**
 * Documents API Service
 *
 * API calls for document upload and management endpoints.
 */

import api from './api'

export interface DocumentUploadResponse {
  id: string
  filename: string
  content_hash: string
  file_size: number
  file_type: string
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  uploaded_by: string
  uploaded_at: string
  project_id: string
  message?: string
}

export interface DocumentDuplicateResponse {
  message: string
  existing_document_id: string
  original_upload_date: string
  uploaded_by: string
}

/**
 * Upload RTF document to project
 *
 * @param file - RTF file to upload
 * @param projectId - Project ID to associate document with
 * @returns Upload response (201 for new, 200 for duplicate)
 */
export async function uploadDocument(
  file: File,
  projectId: string
): Promise<DocumentUploadResponse | DocumentDuplicateResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('project_id', projectId)

  const response = await api.post<DocumentUploadResponse | DocumentDuplicateResponse>(
    '/documents/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )

  return response.data
}

/**
 * Type guard to check if response is duplicate
 */
export function isDuplicateResponse(
  response: DocumentUploadResponse | DocumentDuplicateResponse
): response is DocumentDuplicateResponse {
  return 'existing_document_id' in response
}
