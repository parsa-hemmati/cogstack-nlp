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
/**
 * SearchResultItem Component
 *
 * Displays a single search result as a card with document metadata,
 * relevance score, and content excerpt with highlighting.
 *
 * Features:
 * - XSS-safe highlighting using sanitizeHtml()
 * - Color-coded relevance scores (red/yellow/green)
 * - Formatted dates using locale-specific formatting
 * - Hover effects and interactive states
 * - Action buttons for document operations
 *
 * @component
 *
 * @example
 * ```vue
 * <SearchResultItem
 *   :result="searchResult"
 *   :index="0"
 *   @click="handleResultClick"
 * />
 * ```
 *
 * @example
 * ```vue
 * <!-- In a list -->
 * <div v-for="(result, index) in results" :key="result.id">
 *   <SearchResultItem
 *     :result="result"
 *     :index="index"
 *     @click="openDocumentModal(result)"
 *   />
 * </div>
 * ```
 *
 * @see {@link ../../../docs/features/search/components/SearchResultItem.md} for detailed documentation
 * @see {@link ../../../docs/features/search/security.md} for XSS prevention details
 */
import { sanitizeHtml } from '@/utils/sanitize'

/**
 * Search result data structure
 * @typedef {Object} SearchResult
 * @property {string} id - Unique result identifier
 * @property {string} title - Document title
 * @property {string} content - Document content/excerpt
 * @property {string} document_type - Type: 'note', 'lab', 'imaging', 'discharge', etc.
 * @property {string} author - Document author/creator name
 * @property {string} date - Document date in ISO 8601 format
 * @property {number} score - Relevance score (0-100)
 * @property {Object} [highlights] - Elasticsearch highlights
 * @property {string[]} [highlights.title] - Title highlights with <mark> tags
 * @property {string[]} [highlights.content] - Content highlights with <mark> tags
 */

/**
 * Component props
 * @typedef {Object} Props
 * @property {SearchResult} result - The search result to display (required)
 * @property {number} index - Index of result in list (for tracking) (required)
 * @property {boolean} [hoverable=true] - Enable hover effects
 */
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

/**
 * Component events
 * - 'click': Emitted when result card is clicked
 */
const props = withDefaults(defineProps<Props>(), {
  hoverable: true
})

const emit = defineEmits<{
  click: []
}>()

/**
 * Format ISO 8601 date to locale-specific string
 *
 * Converts dates like "2024-01-15T14:30:00Z" to "15 Jan 2024"
 * Uses en-GB locale for consistent formatting across environments
 *
 * @param {string} dateString - Date in ISO 8601 format
 * @returns {string} Formatted date (e.g., "15 Jan 2024")
 *
 * @example
 * formatDate('2024-01-15')           // "15 Jan 2024"
 * formatDate('2024-01-15T14:30:00Z') // "15 Jan 2024"
 */
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-GB', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

/**
 * Truncate content to maximum length with ellipsis
 *
 * @param {string} content - Full content text
 * @param {number} maxLength - Maximum length before truncation
 * @returns {string} Truncated content with "..." if over limit
 *
 * @example
 * truncateContent('Very long text here...', 20) // "Very long text h..."
 * truncateContent('Short', 20)                  // "Short"
 */
const truncateContent = (content: string, maxLength: number): string => {
  if (content.length <= maxLength) return content
  return content.substring(0, maxLength) + '...'
}

/**
 * Get Vuetify color for relevance score
 *
 * Maps numeric scores to semantic colors for visual feedback:
 * - 80-100: Green (highly relevant)
 * - 60-79:  Orange (moderately relevant)
 * - 0-59:   Red (low relevance)
 *
 * @param {number} score - Relevance score (0-100)
 * @returns {string} Vuetify color name ('success', 'warning', 'error')
 *
 * @example
 * getScoreColor(95)  // 'success'
 * getScoreColor(70)  // 'warning'
 * getScoreColor(40)  // 'error'
 */
const getScoreColor = (score: number): string => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'error'
}

/**
 * Handle card click event
 *
 * Emits 'click' event when user clicks anywhere on the result card
 * Parent component should handle navigation or modal opening
 *
 * @emits click - No payload, parent identifies result from context
 */
const handleClick = () => {
  emit('click')
}
</script>

<style scoped>
/**
 * Result item container styles
 *
 * Applies hover effects and transitions for better UX
 */
.search-result-item {
  cursor: pointer;
  transition: all 0.2s ease;
}

/**
 * Hover state with elevation and transform
 *
 * Only applied when hoverable={true}
 * Provides visual feedback that item is interactive
 */
.search-result-item--hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/**
 * Content excerpt styling
 *
 * - Line height for readability
 * - Muted text color for secondary content
 * - Deep selector to style nested <mark> tags from v-html
 */
.search-result-excerpt {
  line-height: 1.6;
  color: rgba(0, 0, 0, 0.7);
}

/**
 * Highlight styling
 *
 * Applied to <mark> tags from Elasticsearch highlights
 * Yellow background with bold text for visibility
 *
 * Use :deep() to style elements from v-html binding
 */
.search-result-excerpt :deep(mark) {
  background-color: yellow;
  font-weight: 600;
  padding: 0 2px;
}
</style>
