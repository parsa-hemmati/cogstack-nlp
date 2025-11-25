<template>
  <v-container fluid class="pa-4 bg-grey-lighten-4">
    <!-- Loading State -->
    <v-row v-if="isLoading" class="py-8">
      <v-col cols="12" class="text-center">
        <v-progress-circular
          indeterminate
          color="primary"
          size="64"
        />
        <p class="text-body-2 text-grey mt-4">Loading concept highlights...</p>
      </v-col>
    </v-row>

    <!-- Error State -->
    <v-row v-else-if="error">
      <v-col cols="12">
        <v-alert type="error" variant="tonal">
          <v-alert-title>Failed to load highlights</v-alert-title>
          {{ error }}
        </v-alert>
      </v-col>
    </v-row>

    <!-- Empty State -->
    <v-row v-else-if="documents.length === 0">
      <v-col cols="12" class="text-center py-8">
        <v-icon size="48" color="grey-lighten-1">mdi-file-search-outline</v-icon>
        <p class="text-body-2 text-grey mt-2">No documents found with this concept</p>
      </v-col>
    </v-row>

    <!-- Documents List -->
    <v-row v-else>
      <v-col cols="12">
        <p class="text-subtitle-2 mb-4">
          <v-icon class="mr-1">mdi-file-document-multiple</v-icon>
          <strong>{{ documents.length }}</strong> document{{ documents.length !== 1 ? 's' : '' }} containing "<strong>{{ concept }}</strong>"
        </p>

        <v-list lines="three" class="bg-transparent">
          <v-list-item
            v-for="(doc, index) in documents"
            :key="doc.documentId"
            class="mb-3 bg-white rounded elevation-1"
            @click="openDocument(doc)"
          >
            <!-- Document Icon -->
            <template #prepend>
              <v-avatar color="primary" size="40">
                <v-icon color="white">mdi-file-document</v-icon>
              </v-avatar>
            </template>

            <!-- Document Title & Date -->
            <v-list-item-title class="text-subtitle-1 font-weight-medium">
              {{ doc.title || `Document ${index + 1}` }}
            </v-list-item-title>

            <v-list-item-subtitle class="text-caption mb-2">
              <v-icon size="14" class="mr-1">mdi-calendar</v-icon>
              {{ formatDate(doc.date) }}
            </v-list-item-subtitle>

            <!-- Snippet (with concept highlighted) -->
            <v-list-item-subtitle class="text-body-2 mt-2">
              <div class="snippet-container" v-html="sanitizeHtml(doc.snippet)"></div>
            </v-list-item-subtitle>

            <!-- Meta-Annotations Chips -->
            <template #append>
              <div class="d-flex flex-column ga-1">
                <v-chip
                  size="x-small"
                  :color="getMetaColor(doc.metaAnnotations.Negation)"
                  :variant="doc.metaAnnotations.Negation === 'Affirmed' ? 'flat' : 'outlined'"
                >
                  <v-icon start size="14">{{ getMetaIcon('Negation', doc.metaAnnotations.Negation) }}</v-icon>
                  {{ doc.metaAnnotations.Negation }}
                </v-chip>

                <v-chip
                  size="x-small"
                  :color="getMetaColor(doc.metaAnnotations.Temporality)"
                  :variant="doc.metaAnnotations.Temporality === 'Current' ? 'flat' : 'outlined'"
                >
                  <v-icon start size="14">{{ getMetaIcon('Temporality', doc.metaAnnotations.Temporality) }}</v-icon>
                  {{ doc.metaAnnotations.Temporality }}
                </v-chip>

                <v-chip
                  size="x-small"
                  :color="getMetaColor(doc.metaAnnotations.Experiencer)"
                  :variant="doc.metaAnnotations.Experiencer === 'Patient' ? 'flat' : 'outlined'"
                >
                  <v-icon start size="14">{{ getMetaIcon('Experiencer', doc.metaAnnotations.Experiencer) }}</v-icon>
                  {{ doc.metaAnnotations.Experiencer }}
                </v-chip>

                <v-chip
                  size="x-small"
                  :color="getMetaColor(doc.metaAnnotations.Certainty)"
                  variant="outlined"
                >
                  <v-icon start size="14">{{ getMetaIcon('Certainty', doc.metaAnnotations.Certainty) }}</v-icon>
                  {{ doc.metaAnnotations.Certainty }}
                </v-chip>
              </div>
            </template>
          </v-list-item>
        </v-list>
      </v-col>
    </v-row>

    <!-- Document Modal -->
    <DocumentModal
      v-if="selectedDocument"
      v-model="showModal"
      :document="selectedDocument"
    />
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getConceptHighlights } from '@/api/patientSearch'
import { sanitizeHtml } from '@/utils/sanitize'
import DocumentModal from './DocumentModal.vue'
import type { SearchFilters, DocumentHighlight } from '@/api/patientSearch'

// Props
const props = defineProps<{
  patientId: string
  concept: string
  filters: SearchFilters
}>()

// State
const documents = ref<DocumentHighlight[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)
const selectedDocument = ref<DocumentHighlight | null>(null)
const showModal = ref(false)

// Lifecycle
onMounted(async () => {
  await fetchHighlights()
})

// Methods
const fetchHighlights = async () => {
  isLoading.value = true
  error.value = null

  try {
    const response = await getConceptHighlights(
      props.patientId,
      props.concept,
      props.filters
    )
    documents.value = response.documents
  } catch (err: any) {
    error.value = err.message || 'Failed to load concept highlights'
    console.error('Error fetching concept highlights:', err)
  } finally {
    isLoading.value = false
  }
}

const openDocument = (doc: DocumentHighlight) => {
  selectedDocument.value = doc
  showModal.value = true
}

const formatDate = (isoDate: string): string => {
  return new Date(isoDate).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

/**
 * Get color for meta-annotation chip
 * Green = Affirmed/Current/Patient (high confidence, relevant)
 * Red = Negated/Historical/Family (low confidence, less relevant)
 * Grey = Other
 */
const getMetaColor = (value: string): string => {
  // Positive/relevant annotations
  if (value === 'Affirmed' || value === 'Current' || value === 'Patient') {
    return 'green'
  }

  // Negative/less relevant annotations
  if (value === 'Negated' || value === 'Historical' || value === 'Family') {
    return 'red'
  }

  // Neutral
  return 'grey'
}

/**
 * Get icon for meta-annotation type and value
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
.snippet-container {
  line-height: 1.6;
  color: rgba(0, 0, 0, 0.7);
}

.snippet-container :deep(b) {
  color: #1976d2;
  background-color: #e3f2fd;
  padding: 2px 4px;
  border-radius: 4px;
  font-weight: 600;
}

.v-list-item {
  cursor: pointer;
  transition: all 0.2s ease;
}

.v-list-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
}
</style>
