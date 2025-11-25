<template>
  <v-container fluid>
    <!-- Results Header -->
    <v-row>
      <v-col>
        <div class="d-flex justify-space-between align-center mb-4">
          <h2 class="text-h5">
            {{ resultsCount }} {{ resultsCount === 1 ? 'result' : 'results' }}
            <span v-if="query" class="text-subtitle-1 text-medium-emphasis">
              for "{{ query }}"
            </span>
          </h2>

          <v-select
            v-model="selectedSort"
            :items="sortOptions"
            label="Sort by"
            density="compact"
            variant="outlined"
            style="max-width: 200px"
            @update:model-value="handleSortChange"
          />
        </div>
      </v-col>
    </v-row>

    <!-- Loading State -->
    <v-row v-if="loading">
      <v-col>
        <v-skeleton-loader
          v-for="i in 3"
          :key="i"
          type="article"
          class="mb-4"
        />
      </v-col>
    </v-row>

    <!-- Error State -->
    <v-alert
      v-else-if="error"
      type="error"
      variant="tonal"
      class="mb-4"
    >
      {{ error }}
    </v-alert>

    <!-- Empty State -->
    <v-alert
      v-else-if="!loading && results.length === 0"
      type="info"
      variant="tonal"
      class="mb-4"
    >
      No results found. Try adjusting your search query or filters.
    </v-alert>

    <!-- Results List -->
    <v-row v-else>
      <v-col>
        <div
          v-for="(result, index) in results"
          :key="result.id"
          class="mb-4"
        >
          <SearchResultItem
            :result="result"
            :index="index"
            @click="handleResultClick(result)"
          />
        </div>

        <!-- Pagination -->
        <v-pagination
          v-if="totalPages > 1"
          v-model="currentPage"
          :length="totalPages"
          :total-visible="7"
          class="mt-6"
          @update:model-value="handlePageChange"
        />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import SearchResultItem from './SearchResultItem.vue'

interface SearchResult {
  id: string
  title: string
  content: string
  document_type: string
  author: string
  date: string
  score: number
  highlights?: {
    title?: string[]
    content?: string[]
  }
}

interface Props {
  results: SearchResult[]
  query?: string
  loading?: boolean
  error?: string
  total?: number
  page?: number
  pageSize?: number
}

const props = withDefaults(defineProps<Props>(), {
  results: () => [],
  query: '',
  loading: false,
  error: '',
  total: 0,
  page: 1,
  pageSize: 20
})

const emit = defineEmits<{
  'update:page': [page: number]
  'update:sort': [sort: string]
  'result-click': [result: SearchResult]
}>()

// Sort options
const sortOptions = [
  { title: 'Relevance', value: 'relevance' },
  { title: 'Date (Newest)', value: 'date_desc' },
  { title: 'Date (Oldest)', value: 'date_asc' },
  { title: 'Title (A-Z)', value: 'title_asc' },
  { title: 'Title (Z-A)', value: 'title_desc' }
]

const selectedSort = ref('relevance')
const currentPage = ref(props.page)

// Computed
const resultsCount = computed(() => props.total || props.results.length)
const totalPages = computed(() => Math.ceil(props.total / props.pageSize))

// Methods
const handleSortChange = (sort: string) => {
  emit('update:sort', sort)
}

const handlePageChange = (page: number) => {
  emit('update:page', page)
}

const handleResultClick = (result: SearchResult) => {
  emit('result-click', result)
}
</script>

<style scoped>
.search-results-container {
  min-height: 400px;
}
</style>
