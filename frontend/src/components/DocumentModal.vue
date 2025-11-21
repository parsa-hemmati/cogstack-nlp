<template>
  <v-dialog
    :model-value="modelValue"
    max-width="900"
    scrollable
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card>
      <!-- Header -->
      <v-card-title class="d-flex align-center bg-primary text-white pa-4">
        <v-icon class="mr-2">mdi-file-document</v-icon>
        <div class="flex-grow-1">
          <div class="text-h6">{{ document.title || 'Document' }}</div>
          <div class="text-caption">
            <v-icon size="14" class="mr-1">mdi-calendar</v-icon>
            {{ formatDate(document.date) }}
          </div>
        </div>
        <v-btn
          icon
          variant="text"
          color="white"
          @click="$emit('update:modelValue', false)"
        >
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <!-- Meta-Annotations Bar -->
      <v-card-subtitle class="pa-4 bg-grey-lighten-4">
        <div class="d-flex flex-wrap ga-2">
          <v-chip
            size="small"
            :color="getMetaColor(document.metaAnnotations.Negation)"
            :variant="document.metaAnnotations.Negation === 'Affirmed' ? 'flat' : 'outlined'"
          >
            <v-icon start size="16">{{ getMetaIcon('Negation', document.metaAnnotations.Negation) }}</v-icon>
            Negation: {{ document.metaAnnotations.Negation }}
          </v-chip>

          <v-chip
            size="small"
            :color="getMetaColor(document.metaAnnotations.Temporality)"
            :variant="document.metaAnnotations.Temporality === 'Current' ? 'flat' : 'outlined'"
          >
            <v-icon start size="16">{{ getMetaIcon('Temporality', document.metaAnnotations.Temporality) }}</v-icon>
            Temporality: {{ document.metaAnnotations.Temporality }}
          </v-chip>

          <v-chip
            size="small"
            :color="getMetaColor(document.metaAnnotations.Experiencer)"
            :variant="document.metaAnnotations.Experiencer === 'Patient' ? 'flat' : 'outlined'"
          >
            <v-icon start size="16">{{ getMetaIcon('Experiencer', document.metaAnnotations.Experiencer) }}</v-icon>
            Experiencer: {{ document.metaAnnotations.Experiencer }}
          </v-chip>

          <v-chip
            size="small"
            :color="getMetaColor(document.metaAnnotations.Certainty)"
            variant="outlined"
          >
            <v-icon start size="16">{{ getMetaIcon('Certainty', document.metaAnnotations.Certainty) }}</v-icon>
            Certainty: {{ document.metaAnnotations.Certainty }}
          </v-chip>
        </div>
      </v-card-subtitle>

      <!-- Document Content -->
      <v-card-text class="pa-6" style="max-height: 600px; overflow-y: auto;">
        <div class="document-content" v-html="sanitizeHtml(document.snippet)"></div>
      </v-card-text>

      <!-- Footer with Actions -->
      <v-divider />
      <v-card-actions class="pa-4">
        <v-chip size="small" variant="outlined" class="mr-2">
          <v-icon start size="14">mdi-identifier</v-icon>
          Document ID: {{ truncateId(document.documentId) }}
        </v-chip>

        <v-spacer />

        <v-btn
          color="grey"
          variant="text"
          @click="$emit('update:modelValue', false)"
        >
          Close
        </v-btn>

        <v-btn
          color="primary"
          variant="tonal"
          prepend-icon="mdi-download"
          @click="downloadDocument"
        >
          Download
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { sanitizeHtml } from '@/utils/sanitize'
import type { DocumentHighlight } from '@/api/patientSearch'

// Props
defineProps<{
  modelValue: boolean
  document: DocumentHighlight
}>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

// Methods
const formatDate = (isoDate: string): string => {
  return new Date(isoDate).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const truncateId = (id: string): string => {
  return id.length > 12 ? `${id.substring(0, 12)}...` : id
}

const downloadDocument = () => {
  // Future: Implement document download functionality (tracked in technical debt)
  alert('Document download coming soon!')
}

/**
 * Get color for meta-annotation chip (matching DocumentHighlights.vue)
 */
const getMetaColor = (value: string): string => {
  if (value === 'Affirmed' || value === 'Current' || value === 'Patient') {
    return 'green'
  }
  if (value === 'Negated' || value === 'Historical' || value === 'Family') {
    return 'red'
  }
  return 'grey'
}

/**
 * Get icon for meta-annotation type and value (matching DocumentHighlights.vue)
 */
const getMetaIcon = (type: string, value: string): string => {
  switch (type) {
    case 'Negation':
      return value === 'Affirmed' ? 'mdi-check-circle' : 'mdi-cancel'
    case 'Temporality':
      return value === 'Current' ? 'mdi-clock' : 'mdi-history'
    case 'Experiencer':
      return value === 'Patient' ? 'mdi-account' : 'mdi-account-group'
    case 'Certainty':
      return value === 'Definite' ? 'mdi-check-bold' : 'mdi-help-circle'
    default:
      return 'mdi-information'
  }
}
</script>

<style scoped>
.document-content {
  line-height: 1.8;
  font-size: 15px;
  color: rgba(0, 0, 0, 0.87);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.document-content :deep(b) {
  color: #1976d2;
  background-color: #e3f2fd;
  padding: 3px 6px;
  border-radius: 4px;
  font-weight: 700;
  border-bottom: 2px solid #1976d2;
}

/* Improve scrollbar appearance */
.v-card-text::-webkit-scrollbar {
  width: 8px;
}

.v-card-text::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.v-card-text::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.v-card-text::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
