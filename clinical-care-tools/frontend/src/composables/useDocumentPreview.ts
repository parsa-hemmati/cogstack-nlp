/**
 * Document Preview Composable
 * Manages document preview state and fetching for timeline modal
 */

import { ref, computed } from 'vue'
import type { Ref } from 'vue'
import apiClient from '@/api/client'

export interface DocumentAnnotation {
  id: string
  cui: string
  preferredName: string
  conceptType: string
  startChar: number
  endChar: number
  text: string
  metaAnnotations: {
    negation?: string
    temporality?: string
    experiencer?: string
    certainty?: string
  }
}

export interface DocumentDetail {
  id: string
  title: string
  documentType: string
  date: string
  author?: string
  content: string
  annotations: DocumentAnnotation[]
}

export interface HighlightedSpan {
  text: string
  annotation?: DocumentAnnotation
  isHighlighted: boolean
}

export function useDocumentPreview() {
  // State
  const isOpen = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const document = ref<DocumentDetail | null>(null)
  const selectedAnnotationId = ref<string | null>(null)

  // Computed
  const highlightedContent = computed<HighlightedSpan[]>(() => {
    if (!document.value?.content || !document.value?.annotations) {
      return document.value?.content
        ? [{ text: document.value.content, isHighlighted: false }]
        : []
    }

    const content = document.value.content
    const annotations = [...document.value.annotations].sort(
      (a, b) => a.startChar - b.startChar
    )

    const spans: HighlightedSpan[] = []
    let lastIndex = 0

    for (const annotation of annotations) {
      // Add non-highlighted text before this annotation
      if (annotation.startChar > lastIndex) {
        spans.push({
          text: content.slice(lastIndex, annotation.startChar),
          isHighlighted: false,
        })
      }

      // Add highlighted annotation
      spans.push({
        text: content.slice(annotation.startChar, annotation.endChar),
        annotation,
        isHighlighted: true,
      })

      lastIndex = annotation.endChar
    }

    // Add remaining non-highlighted text
    if (lastIndex < content.length) {
      spans.push({
        text: content.slice(lastIndex),
        isHighlighted: false,
      })
    }

    return spans
  })

  const documentMetadata = computed(() => {
    if (!document.value) return null
    return {
      title: document.value.title,
      type: document.value.documentType.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      date: new Date(document.value.date).toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      }),
      author: document.value.author || 'Unknown',
      annotationCount: document.value.annotations?.length || 0,
    }
  })

  // Methods
  const openDocument = async (documentId: string, scrollToAnnotation?: string) => {
    isOpen.value = true
    loading.value = true
    error.value = null
    selectedAnnotationId.value = scrollToAnnotation || null

    try {
      const response = await apiClient.get<DocumentDetail>(
        `/v1/documents/${documentId}`
      )
      document.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to load document'
      console.error('Error fetching document:', err)
    } finally {
      loading.value = false
    }
  }

  const closeDocument = () => {
    isOpen.value = false
    document.value = null
    error.value = null
    selectedAnnotationId.value = null
  }

  const selectAnnotation = (annotationId: string) => {
    selectedAnnotationId.value = annotationId
  }

  const getAnnotationColor = (conceptType: string): string => {
    const colors: Record<string, string> = {
      condition: '#e74c3c',    // Red
      medication: '#3498db',   // Blue
      procedure: '#2ecc71',    // Green
      observation: '#f39c12',  // Orange
    }
    return colors[conceptType.toLowerCase()] || '#9b59b6'  // Purple default
  }

  const copyToClipboard = async (text: string): Promise<boolean> => {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch (err) {
      console.error('Failed to copy:', err)
      return false
    }
  }

  return {
    // State
    isOpen,
    loading,
    error,
    document,
    selectedAnnotationId,

    // Computed
    highlightedContent,
    documentMetadata,

    // Methods
    openDocument,
    closeDocument,
    selectAnnotation,
    getAnnotationColor,
    copyToClipboard,
  }
}
