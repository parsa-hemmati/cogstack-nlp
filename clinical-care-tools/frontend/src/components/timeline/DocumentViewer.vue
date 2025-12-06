<template>
  <v-card class="fill-height d-flex flex-column">
    <v-toolbar density="compact" color="white" border>
      <v-btn icon="mdi-close" variant="text" size="small" @click="$emit('close')"></v-btn>
      <v-toolbar-title class="text-subtitle-1">{{ doc?.title || 'Document Viewer' }}</v-toolbar-title>
      <v-spacer></v-spacer>
    </v-toolbar>

    <div class="flex-grow-1 overflow-y-auto pa-4 position-relative">
      <div v-if="loading" class="d-flex justify-center align-center fill-height">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
      </div>
      
      <div v-else-if="error" class="text-center text-error pa-4">
        {{ error }}
      </div>

      <div v-else-if="doc" class="document-content">
        <!-- Metadata Header -->
        <div class="mb-4 pb-4 border-b">
           <div class="text-caption text-grey">Date</div>
           <div class="text-body-2 mb-2">{{ formatDate(doc.date) }}</div>
           
           <div class="text-caption text-grey">Type</div>
           <div class="text-body-2 mb-2">{{ doc.documentType }}</div>
           
           <div class="text-caption text-grey">Author</div>
           <div class="text-body-2">{{ doc.author || 'Unknown' }}</div>
        </div>

        <!-- Rendered Content with Highlights -->
        <div class="text-body-1 content-text" v-html="highlightedContent"></div>
      </div>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { timelineApi } from '@/api/timeline'
import type { DocumentDetail, Annotation } from '@/types/timeline'

const props = defineProps<{
  documentId: string | null
}>()

const emit = defineEmits(['close'])

const doc = ref<DocumentDetail | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

watch(() => props.documentId, async (newId) => {
  if (!newId) {
    doc.value = null
    return
  }
  
  loading.value = true
  error.value = null
  try {
    doc.value = await timelineApi.getDocument(newId)
  } catch (err) {
    console.error(err)
    error.value = "Failed to load document content."
  } finally {
    loading.value = false
  }
}, { immediate: true })

function formatDate(iso: string) {
  return new Date(iso).toLocaleString()
}

const highlightedContent = computed(() => {
  if (!doc.value) return ''
  const text = doc.value.content
  const annotations = doc.value.annotations || []
  
  if (!annotations.length) return text.replace(/\n/g, '<br>')

  // Sort annotations by start char descending to simpler replacement without shifting indices
  // Limitation: Overlapping annotations not handled perfectly by this simple replacement
  const sortedAnns = [...annotations].sort((a, b) => b.startChar - a.startChar)
  
  let html = text
  
  sortedAnns.forEach(ann => {
      if (ann.startChar < 0 || ann.endChar > text.length) return
      
      const before = html.substring(0, ann.startChar)
      const chunk = html.substring(ann.startChar, ann.endChar)
      const after = html.substring(ann.endChar)
      
      // Determine color based on meta-annotations
      let bgClass = 'bg-green-lighten-4' // Default affirmed
      if (ann.metaAnnotations?.negation === 'Negated') {
          bgClass = 'bg-red-lighten-4 text-decoration-line-through'
      } else if (ann.metaAnnotations?.temporality === 'Historical') {
          bgClass = 'bg-grey-lighten-2'
      }
      
      // Validation to ensure we don't break HTML tags if text contains them (unlikely for raw clinical text)
      // But we should escape the chunk content if we weren't doing this on raw text.
      // Assuming raw text input:
      const mark = `<mark class="${bgClass} rounded px-1 cursor-pointer" title="${ann.preferredName} (${ann.metaAnnotations?.negation || 'Affirmed'})">${chunk}</mark>`
      
      html = before + mark + after
  })
  
  return html.replace(/\n/g, '<br>')
})
</script>

<style scoped>
.content-text {
    line-height: 1.6;
    font-family: 'Roboto Mono', monospace;
    white-space: pre-wrap;
}
</style>
