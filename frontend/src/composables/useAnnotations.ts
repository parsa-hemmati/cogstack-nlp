/**
 * Manual Annotations Composable
 *
 * Provides functions for managing manual PHI annotations.
 */
import { ref } from 'vue'
import type { Ref } from 'vue'

interface ManualAnnotation {
  annotation_id: string
  note_id: string
  user_id: string
  text: string
  start_offset: number
  end_offset: number
  entity_type: string
  confidence: number
  created_at: string
  updated_at: string
  is_active: boolean
}

interface ManualAnnotationCreate {
  note_id: string
  text: string
  start_offset: number
  end_offset: number
  entity_type: string
  confidence: number
}

interface ManualAnnotationList {
  annotations: ManualAnnotation[]
  total: number
}

export function useAnnotations() {
  const loading: Ref<boolean> = ref(false)
  const error: Ref<string | null> = ref(null)

  /**
   * Create a new manual annotation
   */
  const createAnnotation = async (annotation: ManualAnnotationCreate): Promise<ManualAnnotation | null> => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch('/api/v1/deidentify/annotations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify(annotation)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      return data as ManualAnnotation
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create annotation'
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Get all annotations for a note
   */
  const getAnnotations = async (noteId: string, includeInactive = false): Promise<ManualAnnotationList | null> => {
    loading.value = true
    error.value = null

    try {
      const url = new URL('/api/v1/deidentify/annotations/' + noteId, window.location.origin)
      if (includeInactive) {
        url.searchParams.append('include_inactive', 'true')
      }

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      return data as ManualAnnotationList
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to get annotations'
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Update an existing annotation
   */
  const updateAnnotation = async (
    annotationId: string,
    updates: Partial<Pick<ManualAnnotation, 'text' | 'entity_type' | 'confidence'>>
  ): Promise<ManualAnnotation | null> => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/v1/deidentify/annotations/${annotationId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify(updates)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      return data as ManualAnnotation
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update annotation'
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete an annotation
   */
  const deleteAnnotation = async (annotationId: string, hardDelete = false): Promise<boolean> => {
    loading.value = true
    error.value = null

    try {
      const url = new URL(`/api/v1/deidentify/annotations/${annotationId}`, window.location.origin)
      if (hardDelete) {
        url.searchParams.append('hard_delete', 'true')
      }

      const response = await fetch(url.toString(), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete annotation'
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Get authentication token from local storage
   */
  const getAuthToken = (): string => {
    // This should be replaced with your actual auth token retrieval logic
    return localStorage.getItem('authToken') || ''
  }

  return {
    loading,
    error,
    createAnnotation,
    getAnnotations,
    updateAnnotation,
    deleteAnnotation
  }
}
