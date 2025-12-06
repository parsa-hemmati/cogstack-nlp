<template>
  <div class="document-list">
    <div v-if="!documents.length" class="text-center py-4 text-grey">
      No documents found for this period.
    </div>

    <v-card
      v-for="doc in sortedDocuments"
      :key="doc.id"
      class="mb-3"
      :variant="selectedId === doc.id ? 'tonal' : 'outlined'"
      :color="selectedId === doc.id ? 'primary' : undefined"
      hover
      @click="$emit('select', doc)"
    >
      <v-card-item>
        <template v-slot:prepend>
          <v-icon
            :color="getDocumentColor(doc.documentType)"
            size="small"
            icon="mdi-file-document"
          ></v-icon>
        </template>
        <v-card-title class="text-subtitle-2">{{ doc.title }}</v-card-title>
        <v-card-subtitle class="text-caption">
          {{ formatDate(doc.date) }}
        </v-card-subtitle>
      </v-card-item>
      <v-card-text class="py-1">
         <v-chip size="x-small" label class="mr-2">{{ doc.documentType }}</v-chip>
         <v-chip size="x-small" variant="text" v-if="doc.annotationCount > 0">
           {{ doc.annotationCount }} entities
         </v-chip>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TimelineDocument } from '@/types/timeline'

const props = defineProps<{
  documents: TimelineDocument[]
  selectedId?: string | null
}>()

const emit = defineEmits(['select'])

const sortedDocuments = computed(() => {
  return [...props.documents].sort((a, b) => 
    new Date(b.date).getTime() - new Date(a.date).getTime()
  )
})

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

function getDocumentColor(type: string) {
  if (type.includes('Discharge')) return 'error'
  if (type.includes('Radiology')) return 'warning'
  return 'primary'
}
</script>
