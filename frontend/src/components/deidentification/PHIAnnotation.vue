<template>
  <v-card>
    <v-card-title>Manual PHI Annotation</v-card-title>
    <v-card-subtitle>Select text to annotate PHI entities</v-card-subtitle>

    <v-card-text>
      <!-- Annotation text area -->
      <div
        ref="textArea"
        class="annotation-text pa-4 mb-4"
        @mouseup="handleTextSelection"
        v-html="highlightedText"
      ></div>

      <!-- Annotation toolbar (appears on selection) -->
      <v-menu
        v-model="showToolbar"
        :position-x="toolbarX"
        :position-y="toolbarY"
        absolute
        offset-y
        :close-on-content-click="false"
      >
        <v-card>
          <v-card-title class="text-subtitle-2">Add PHI Annotation</v-card-title>
          <v-card-text>
            <v-select
              v-model="selectedEntityType"
              :items="entityTypes"
              label="PHI Entity Type"
              dense
              class="mb-2"
            ></v-select>

            <v-slider
              v-model="confidence"
              label="Confidence"
              :min="0"
              :max="1"
              :step="0.1"
              thumb-label
              class="mb-2"
            ></v-slider>

            <v-btn
              @click="saveAnnotation"
              color="primary"
              block
              :disabled="!selectedEntityType"
            >
              Save Annotation
            </v-btn>
          </v-card-text>
        </v-card>
      </v-menu>

      <!-- Current annotations list -->
      <v-card variant="outlined" class="mt-4">
        <v-card-title class="text-subtitle-1">
          Manual Annotations ({{ annotations.length }})
        </v-card-title>
        <v-list v-if="annotations.length > 0">
          <v-list-item
            v-for="ann in annotations"
            :key="ann.annotation_id"
          >
            <template #prepend>
              <v-chip :color="getEntityColor(ann.entity_type)" size="small">
                {{ ann.entity_type }}
              </v-chip>
            </template>

            <v-list-item-title>{{ ann.text }}</v-list-item-title>
            <v-list-item-subtitle>
              Confidence: {{ ann.confidence.toFixed(2) }} | Offsets: {{ ann.start_offset }}-{{ ann.end_offset }}
            </v-list-item-subtitle>

            <template #append>
              <v-btn
                icon="mdi-delete"
                size="small"
                variant="text"
                @click="deleteAnnotation(ann.annotation_id)"
              ></v-btn>
            </template>
          </v-list-item>
        </v-list>
        <v-card-text v-else class="text-center text-grey">
          No annotations yet. Select text to add annotations.
        </v-card-text>
      </v-card>
    </v-card-text>

    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn
        @click="$emit('close')"
        variant="text"
      >
        Cancel
      </v-btn>
      <v-btn
        @click="reRunDeidentification"
        color="primary"
        :disabled="annotations.length === 0"
      >
        Re-run De-identification
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAnnotations } from '@/composables/useAnnotations'
import { sanitizeHtml } from '@/utils/sanitize'

interface Props {
  noteId: string
  noteText: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  rerun: []
}>()

// Entity types (18 PHI categories)
const entityTypes = ref([
  'NAME', 'DOB', 'AGE', 'MRN', 'SSN', 'PHONE', 'FAX', 'EMAIL',
  'ADDRESS', 'CITY', 'STATE', 'ZIP', 'HOSPITAL', 'PHYSICIAN',
  'DATE', 'DEVICE_ID', 'LICENSE', 'OTHER'
])

// Text selection state
const textArea = ref<HTMLElement | null>(null)
const showToolbar = ref(false)
const toolbarX = ref(0)
const toolbarY = ref(0)
const selectedText = ref('')
const selectedStart = ref(0)
const selectedEnd = ref(0)

// Annotation state
const selectedEntityType = ref<string>('')
const confidence = ref(1.0)
const annotations = ref<any[]>([])

// Use composable for API calls
const { createAnnotation, getAnnotations, deleteAnnotation: deleteAnnotationApi } = useAnnotations()

// Load existing annotations
const loadAnnotations = async () => {
  const result = await getAnnotations(props.noteId)
  if (result) {
    annotations.value = result.annotations
  }
}

// Highlighted text with annotations
const highlightedText = computed(() => {
  // SECURITY: Sanitize noteText FIRST to prevent XSS
  let text = sanitizeHtml(props.noteText)
  const sortedAnnotations = [...annotations.value].sort((a, b) => b.start_offset - a.start_offset)

  for (const ann of sortedAnnotations) {
    const before = text.substring(0, ann.start_offset)
    const highlighted = text.substring(ann.start_offset, ann.end_offset)
    const after = text.substring(ann.end_offset)
    // Note: getEntityColor returns hex color codes (safe, not user input)
    text = `${before}<span class="annotation-highlight" style="background-color: ${getEntityColor(ann.entity_type)}33;">${highlighted}</span>${after}`
  }

  // SECURITY: Sanitize final HTML to allow only safe tags (span with style)
  return sanitizeHtml(text)
})

// Handle text selection
const handleTextSelection = () => {
  const selection = window.getSelection()
  if (!selection || selection.isCollapsed) return

  selectedText.value = selection.toString()
  const range = selection.getRangeAt(0)

  // Calculate offsets
  const container = textArea.value
  if (!container) return

  const preRange = document.createRange()
  preRange.selectNodeContents(container)
  preRange.setEnd(range.startContainer, range.startOffset)
  selectedStart.value = preRange.toString().length

  selectedEnd.value = selectedStart.value + selectedText.value.length

  // Show toolbar
  const rect = range.getBoundingClientRect()
  toolbarX.value = rect.left
  toolbarY.value = rect.top - 10
  showToolbar.value = true
}

// Save annotation
const saveAnnotation = async () => {
  if (!selectedEntityType.value) return

  const annotation = {
    note_id: props.noteId,
    text: selectedText.value,
    start_offset: selectedStart.value,
    end_offset: selectedEnd.value,
    entity_type: selectedEntityType.value,
    confidence: confidence.value
  }

  const result = await createAnnotation(annotation)
  if (result) {
    annotations.value.push(result)
    showToolbar.value = false
    selectedEntityType.value = ''
    confidence.value = 1.0
  }
}

// Delete annotation
const deleteAnnotation = async (annotationId: string) => {
  const success = await deleteAnnotationApi(annotationId)
  if (success) {
    annotations.value = annotations.value.filter(a => a.annotation_id !== annotationId)
  }
}

// Re-run de-identification with manual annotations
const reRunDeidentification = () => {
  emit('rerun')
}

// Get entity type color
const getEntityColor = (entityType: string): string => {
  const colors: Record<string, string> = {
    NAME: '#FF5722',
    DOB: '#2196F3',
    AGE: '#4CAF50',
    MRN: '#9C27B0',
    SSN: '#F44336',
    PHONE: '#00BCD4',
    FAX: '#009688',
    EMAIL: '#FFC107',
    ADDRESS: '#FF9800',
    CITY: '#8BC34A',
    STATE: '#CDDC39',
    ZIP: '#FFEB3B',
    HOSPITAL: '#3F51B5',
    PHYSICIAN: '#673AB7',
    DATE: '#E91E63',
    DEVICE_ID: '#795548',
    LICENSE: '#607D8B',
    OTHER: '#9E9E9E'
  }
  return colors[entityType] || '#9E9E9E'
}

// Load annotations on mount
loadAnnotations()
</script>

<style scoped>
.annotation-text {
  border: 1px solid #ddd;
  border-radius: 4px;
  min-height: 200px;
  font-family: monospace;
  line-height: 1.6;
  cursor: text;
  user-select: text;
}

.annotation-highlight {
  padding: 2px 4px;
  border-radius: 3px;
  cursor: pointer;
}

.annotation-highlight:hover {
  opacity: 0.8;
}
</style>
