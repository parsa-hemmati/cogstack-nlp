<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="isOpen"
        class="document-preview-overlay"
        @click.self="close"
        @keydown.escape="close"
        role="dialog"
        aria-modal="true"
        aria-labelledby="document-preview-title"
      >
        <div
          ref="modalRef"
          class="document-preview-modal"
          tabindex="-1"
        >
          <!-- Header -->
          <header class="modal-header">
            <div class="header-content">
              <h2 id="document-preview-title" class="modal-title">
                {{ documentMetadata?.title || 'Document Preview' }}
              </h2>
              <div class="document-meta" v-if="documentMetadata">
                <span class="meta-badge type-badge">
                  {{ documentMetadata.type }}
                </span>
                <span class="meta-item">
                  <span class="meta-icon">📅</span>
                  {{ documentMetadata.date }}
                </span>
                <span class="meta-item" v-if="documentMetadata.author">
                  <span class="meta-icon">👤</span>
                  {{ documentMetadata.author }}
                </span>
                <span class="meta-item">
                  <span class="meta-icon">🏷️</span>
                  {{ documentMetadata.annotationCount }} annotations
                </span>
              </div>
            </div>
            <button
              class="close-button"
              @click="close"
              aria-label="Close preview"
            >
              ✕
            </button>
          </header>

          <!-- Loading State -->
          <div v-if="loading" class="modal-loading">
            <div class="spinner"></div>
            <p>Loading document...</p>
          </div>

          <!-- Error State -->
          <div v-else-if="error" class="modal-error">
            <p class="error-icon">⚠️</p>
            <p class="error-message">{{ error }}</p>
            <button class="retry-button" @click="retry">Try Again</button>
          </div>

          <!-- Content -->
          <div v-else class="modal-body">
            <!-- Annotation Legend -->
            <div class="annotation-legend">
              <span class="legend-title">Annotation Types:</span>
              <span
                v-for="type in legendItems"
                :key="type.name"
                class="legend-item"
              >
                <span
                  class="legend-color"
                  :style="{ backgroundColor: type.color }"
                ></span>
                {{ type.name }}
              </span>
            </div>

            <!-- Document Content with Highlights -->
            <div
              ref="contentRef"
              class="document-content"
            >
              <template v-for="(span, index) in highlightedContent" :key="index">
                <span
                  v-if="span.isHighlighted && span.annotation"
                  :id="`annotation-${span.annotation.id}`"
                  class="annotation-highlight"
                  :class="{
                    'selected': selectedAnnotationId === span.annotation.id,
                    [`type-${span.annotation.conceptType.toLowerCase()}`]: true
                  }"
                  :style="{
                    backgroundColor: getAnnotationColor(span.annotation.conceptType) + '33',
                    borderColor: getAnnotationColor(span.annotation.conceptType)
                  }"
                  @click="handleAnnotationClick(span.annotation)"
                  @mouseenter="hoveredAnnotation = span.annotation"
                  @mouseleave="hoveredAnnotation = null"
                  role="button"
                  tabindex="0"
                  :aria-label="`Annotation: ${span.annotation.preferredName}`"
                >
                  {{ span.text }}

                  <!-- Tooltip -->
                  <Transition name="tooltip">
                    <div
                      v-if="hoveredAnnotation?.id === span.annotation.id"
                      class="annotation-tooltip"
                    >
                      <div class="tooltip-header">
                        <strong>{{ span.annotation.preferredName }}</strong>
                        <span
                          class="tooltip-type"
                          :style="{ color: getAnnotationColor(span.annotation.conceptType) }"
                        >
                          {{ span.annotation.conceptType }}
                        </span>
                      </div>
                      <div class="tooltip-meta">
                        <div v-if="span.annotation.metaAnnotations.negation">
                          <span class="meta-label">Negation:</span>
                          {{ span.annotation.metaAnnotations.negation }}
                        </div>
                        <div v-if="span.annotation.metaAnnotations.temporality">
                          <span class="meta-label">Temporality:</span>
                          {{ span.annotation.metaAnnotations.temporality }}
                        </div>
                        <div v-if="span.annotation.metaAnnotations.experiencer">
                          <span class="meta-label">Experiencer:</span>
                          {{ span.annotation.metaAnnotations.experiencer }}
                        </div>
                      </div>
                      <div class="tooltip-cui">
                        CUI: {{ span.annotation.cui }}
                      </div>
                    </div>
                  </Transition>
                </span>
                <span v-else class="plain-text">{{ span.text }}</span>
              </template>
            </div>
          </div>

          <!-- Footer -->
          <footer class="modal-footer">
            <button
              class="action-button secondary"
              @click="copyDocumentText"
            >
              📋 Copy Text
            </button>
            <button
              class="action-button primary"
              @click="close"
            >
              Close
            </button>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed, onMounted, onUnmounted } from 'vue'
import { useDocumentPreview, type DocumentAnnotation } from '@/composables/useDocumentPreview'

// Props
interface Props {
  documentId?: string
  scrollToAnnotation?: string
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  close: []
  annotationClick: [annotation: DocumentAnnotation]
}>()

// Composable
const {
  isOpen,
  loading,
  error,
  document,
  selectedAnnotationId,
  highlightedContent,
  documentMetadata,
  openDocument,
  closeDocument,
  selectAnnotation,
  getAnnotationColor,
  copyToClipboard,
} = useDocumentPreview()

// Local state
const modalRef = ref<HTMLDivElement | null>(null)
const contentRef = ref<HTMLDivElement | null>(null)
const hoveredAnnotation = ref<DocumentAnnotation | null>(null)
const copyFeedback = ref(false)

// Legend items
const legendItems = computed(() => [
  { name: 'Condition', color: '#e74c3c' },
  { name: 'Medication', color: '#3498db' },
  { name: 'Procedure', color: '#2ecc71' },
  { name: 'Observation', color: '#f39c12' },
])

// Watch for document ID changes
watch(() => props.documentId, (newId) => {
  if (newId) {
    openDocument(newId, props.scrollToAnnotation)
  }
}, { immediate: true })

// Watch for loading completion to scroll to annotation
watch(loading, async (isLoading) => {
  if (!isLoading && selectedAnnotationId.value) {
    await nextTick()
    scrollToSelectedAnnotation()
  }
})

// Focus trap
watch(isOpen, async (open) => {
  if (open) {
    await nextTick()
    modalRef.value?.focus()
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

// Methods
const close = () => {
  closeDocument()
  emit('close')
}

const retry = () => {
  if (props.documentId) {
    openDocument(props.documentId, props.scrollToAnnotation)
  }
}

const handleAnnotationClick = (annotation: DocumentAnnotation) => {
  selectAnnotation(annotation.id)
  emit('annotationClick', annotation)
}

const scrollToSelectedAnnotation = () => {
  if (!selectedAnnotationId.value || !contentRef.value) return

  const element = contentRef.value.querySelector(
    `#annotation-${selectedAnnotationId.value}`
  )

  if (element) {
    element.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    })
  }
}

const copyDocumentText = async () => {
  if (document.value?.content) {
    const success = await copyToClipboard(document.value.content)
    if (success) {
      copyFeedback.value = true
      setTimeout(() => {
        copyFeedback.value = false
      }, 2000)
    }
  }
}

// Keyboard handling
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && isOpen.value) {
    close()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})

// Expose open method for parent components
defineExpose({
  open: openDocument,
  close: closeDocument,
})
</script>

<style scoped>
.document-preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.document-preview-modal {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  outline: none;
}

/* Header */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
  background-color: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.header-content {
  flex: 1;
}

.modal-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  color: #2c3e50;
}

.document-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  font-size: 0.875rem;
  color: #666;
}

.meta-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  background-color: #3498db;
  color: white;
  font-weight: 500;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.meta-icon {
  font-size: 1rem;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #666;
  cursor: pointer;
  padding: 0.25rem;
  line-height: 1;
  transition: color 0.2s;
}

.close-button:hover {
  color: #333;
}

/* Loading State */
.modal-loading {
  padding: 4rem 2rem;
  text-align: center;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e0e0e0;
  border-top-color: #3498db;
  border-radius: 50%;
  margin: 0 auto 1rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error State */
.modal-error {
  padding: 4rem 2rem;
  text-align: center;
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.error-message {
  color: #e74c3c;
  margin-bottom: 1rem;
}

.retry-button {
  padding: 0.5rem 1.5rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.retry-button:hover {
  background-color: #2980b9;
}

/* Body */
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

/* Annotation Legend */
.annotation-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 0.75rem 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
  font-size: 0.875rem;
}

.legend-title {
  font-weight: 600;
  color: #333;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 3px;
}

/* Document Content */
.document-content {
  font-family: 'Georgia', serif;
  font-size: 1rem;
  line-height: 1.8;
  color: #333;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.plain-text {
  /* No special styling */
}

.annotation-highlight {
  position: relative;
  padding: 0.125rem 0.25rem;
  border-radius: 3px;
  border-bottom: 2px solid;
  cursor: pointer;
  transition: all 0.2s;
}

.annotation-highlight:hover,
.annotation-highlight.selected {
  filter: brightness(0.95);
}

.annotation-highlight:focus {
  outline: 2px solid #3498db;
  outline-offset: 2px;
}

/* Tooltip */
.annotation-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background-color: #2c3e50;
  color: white;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 0.8125rem;
  line-height: 1.4;
  white-space: nowrap;
  z-index: 10;
  margin-bottom: 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.annotation-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: #2c3e50;
}

.tooltip-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.tooltip-type {
  font-weight: 500;
  text-transform: capitalize;
}

.tooltip-meta {
  font-size: 0.75rem;
  opacity: 0.9;
}

.meta-label {
  font-weight: 600;
}

.tooltip-cui {
  font-size: 0.75rem;
  opacity: 0.7;
  margin-top: 0.5rem;
  font-family: monospace;
}

/* Footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e0e0e0;
  background-color: #f8f9fa;
  border-radius: 0 0 8px 8px;
}

.action-button {
  padding: 0.625rem 1.25rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-button.secondary {
  background-color: white;
  border: 1px solid #ddd;
  color: #333;
}

.action-button.secondary:hover {
  background-color: #f0f0f0;
}

.action-button.primary {
  background-color: #3498db;
  border: 1px solid #2980b9;
  color: white;
}

.action-button.primary:hover {
  background-color: #2980b9;
}

/* Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-active .document-preview-modal,
.modal-leave-active .document-preview-modal {
  transition: transform 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .document-preview-modal,
.modal-leave-to .document-preview-modal {
  transform: scale(0.95);
}

.tooltip-enter-active,
.tooltip-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(4px);
}

/* Responsive */
@media (max-width: 768px) {
  .document-preview-overlay {
    padding: 1rem;
  }

  .document-preview-modal {
    max-height: 95vh;
  }

  .modal-header {
    padding: 1rem;
  }

  .document-meta {
    flex-direction: column;
    gap: 0.5rem;
  }

  .annotation-legend {
    flex-direction: column;
  }
}
</style>
