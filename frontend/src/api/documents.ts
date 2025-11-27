/**
 * Documents API client.
 */
import api from './api'
import type { DocumentUploadResponse, DocumentInfo } from '@/types/document'

/**
 * Upload clinical document.
 *
 * @param file - RTF file to upload
 * @returns Upload response with document ID and status
 *
 * @example
 * const file = document.querySelector('input[type="file"]').files[0]
 * const response = await uploadDocument(file)
 * console.log(`Document ID: ${response.document_id}`)
 */
export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post<DocumentUploadResponse>('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

/**
 * Get document by ID.
 *
 * @param documentId - Document UUID
 * @returns Document information
 */
export async function getDocument(documentId: string): Promise<DocumentInfo> {
  const response = await api.get<DocumentInfo>(`/documents/${documentId}`)
  return response.data
}

/**
 * List uploaded documents.
 *
 * @param limit - Maximum number of documents to return
 * @param offset - Number of documents to skip
 * @returns List of documents
 */
export async function listDocuments(limit: number = 20, offset: number = 0): Promise<DocumentInfo[]> {
  const response = await api.get<DocumentInfo[]>('/documents', {
    params: { limit, offset },
  })
  return response.data
}
