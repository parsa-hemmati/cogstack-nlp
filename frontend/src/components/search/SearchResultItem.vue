<template>
  <v-card
    :class="['search-result-item', { 'search-result-item--hover': hoverable }]"
    :elevation="hoverable ? 2 : 1"
    @click="handleClick"
  >
    <v-card-title class="d-flex justify-space-between align-start">
      <div class="flex-grow-1">
        <!-- Title with highlights (XSS-safe) -->
        <div
          v-if="result.highlights?.title"
          class="text-h6"
          v-html="sanitizeHtml(result.highlights.title[0])"
        />
        <h3 v-else class="text-h6">
          {{ result.title }}
        </h3>

        <!-- Metadata -->
        <div class="text-caption text-medium-emphasis mt-1">
          <v-chip size="x-small" class="mr-2" variant="tonal">
            {{ result.document_type }}
          </v-chip>
          <span class="mr-3">
            <v-icon size="x-small">mdi-account</v-icon>
            {{ result.author }}
          </span>
          <span>
            <v-icon size="x-small">mdi-calendar</v-icon>
            {{ formatDate(result.date) }}
          </span>
        </div>
      </div>

      <!-- Relevance Score -->
      <v-tooltip bottom>
        <template #activator="{ props: tooltipProps }">
          <v-chip
            v-bind="tooltipProps"
            size="small"
            :color="getScoreColor(result.score)"
            variant="tonal"
          >
            {{ result.score.toFixed(2) }}
          </v-chip>
        </template>
        Relevance score (0-100)
      </v-tooltip>
    </v-card-title>

    <v-card-text>
      <!-- Content excerpt with highlights (XSS-safe) -->
      <div
        v-if="result.highlights?.content"
        class="search-result-excerpt"
        v-html="sanitizeHtml(result.highlights.content[0])"
      />
      <p v-else class="search-result-excerpt">
        {{ truncateContent(result.content, 250) }}
      </p>
    </v-card-text>

    <v-card-actions>
      <v-btn
        variant="text"
        size="small"
        prepend-icon="mdi-file-document-outline"
      >
        View Document
      </v-btn>
      <v-spacer />
      <v-btn
        icon="mdi-bookmark-outline"
        size="small"
        variant="text"
      />
      <v-btn
        icon="mdi-share-variant"
        size="small"
        variant="text"
      />
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { sanitizeHtml } from '@/utils/sanitize'

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
  result: SearchResult
  index: number
  hoverable?: boolean
}

withDefaults(defineProps<Props>(), {
  hoverable: true
})

const emit = defineEmits<{
  click: []
}>()

// Methods
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-GB', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const truncateContent = (content: string, maxLength: number): string => {
  if (content.length <= maxLength) return content
  return content.substring(0, maxLength) + '...'
}

const getScoreColor = (score: number): string => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'error'
}

const handleClick = () => {
  emit('click')
}
</script>

<style scoped>
.search-result-item {
  cursor: pointer;
  transition: all 0.2s ease;
}

.search-result-item--hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.search-result-excerpt {
  line-height: 1.6;
  color: rgba(0, 0, 0, 0.7);
}

.search-result-excerpt :deep(mark) {
  background-color: yellow;
  font-weight: 600;
  padding: 0 2px;
}
</style>
