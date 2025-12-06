<template>
  <div class="patient-list">
    <!-- Loading State -->
    <div v-if="loading && !results.length">
      <v-skeleton-loader
        v-for="n in 3"
        :key="n"
        type="article"
        class="mb-4"
      ></v-skeleton-loader>
    </div>

    <!-- Empty State -->
    <v-alert
      v-else-if="!loading && hasSearched && !results.length"
      type="info"
      variant="tonal"
      class="mt-4"
    >
      No documents found matching your query.
    </v-alert>

    <!-- Results List -->
    <v-card
      v-for="result in results"
      :key="result.id"
      class="mb-3 search-result-card"
      variant="outlined"
      hover
      :to="`/documents/${result.source.id}`"
    >
      <v-card-item>
        <template v-slot:prepend>
          <v-icon
            :color="getDocumentIconColor(result.source.document_type)"
            icon="mdi-file-document-outline"
          ></v-icon>
        </template>
        <v-card-title class="text-subtitle-1 text-primary">
          {{ result.source.title || 'Untitled Document' }}
        </v-card-title>
        <v-card-subtitle>
          {{ formatDate(result.source.date) }} • {{ result.source.document_type }} 
          <span v-if="result.source.author">• {{ result.source.author }}</span>
        </v-card-subtitle>
      </v-card-item>

      <v-card-text class="pt-2">
        <!-- Highlights -->
        <div v-if="result.highlights && result.highlights.length" class="text-body-2 text-grey-darken-2">
          <div v-for="(highlight, idx) in result.highlights" :key="idx" class="mb-1">
             <span v-html="sanitizeHighlight(highlight.snippet)"></span>
          </div>
        </div>
        <div v-else class="text-body-2 text-truncate">
           {{ result.source.snippet || 'No preview available' }}
        </div>
      </v-card-text>
    </v-card>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="d-flex justify-center mt-6">
      <v-pagination
        v-model="currentPage"
        :length="totalPages"
        :total-visible="7"
        density="comfortable"
        @update:model-value="handlePageChange"
      ></v-pagination>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSearchStore } from '@/stores/search'
import { storeToRefs } from 'pinia'

const searchStore = useSearchStore()
const { results, loading, totalPages, page } = storeToRefs(searchStore)

// We verify "hasSearched" by checking if results were loaded or totalResults updated
// A simple proxy is checking if we have results or if loading finished (and we had a query).
const hasSearched = computed(() => searchStore.query !== '')

const currentPage = computed({
  get: () => page.value,
  set: (val) => { /* handled by event */ }
})

function handlePageChange(val: number) {
  searchStore.setPage(val)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function formatDate(isoString: string) {
  if (!isoString) return ''
  return new Date(isoString).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

function getDocumentIconColor(type?: string) {
  switch (type?.toLowerCase()) {
    case 'discharge_summary': return 'error'
    case 'pathology_report': return 'info'
    case 'radiology_report': return 'warning'
    default: return 'primary'
  }
}

// Basic safety for highlight snippets which contain <em> tags from ES
function sanitizeHighlight(snippet: string) {
  // Allow only <em> tags for highlighting
  return snippet
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/&lt;em&gt;/g, '<em class="bg-yellow-lighten-4 font-weight-bold">')
    .replace(/&lt;\/em&gt;/g, '</em>')
}
</script>

<style scoped>
.search-result-card {
  transition: transform 0.2s;
}
</style>
