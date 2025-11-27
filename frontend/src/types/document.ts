/**
 * Document types for API requests/responses.
 */

export interface DocumentUploadResponse {
  document_id: string
  filename: string
  file_size: number
  content_hash: string
  status: string
  is_duplicate: boolean
  message?: string
  created_at: string
}

export interface DocumentInfo {
  id: string
  filename: string
  content_type: string
  file_size: number
  content_hash: string
  processing_status: string
  uploaded_by: string
  created_at: string
}
