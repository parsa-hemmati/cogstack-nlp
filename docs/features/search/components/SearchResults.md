# SearchResults Component

## Description

The `SearchResults` component displays a paginated list of search results from Elasticsearch with sorting capabilities, loading states, error handling, and empty state messaging. It uses Vuetify for styling and manages pagination through props.

The component is designed to work with the `usePatientSearch` composable and displays `SearchResultItem` components for each result.

## Props

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `results` | `SearchResult[]` | `[]` | No | Array of search result objects to display |
| `query` | `string` | `''` | No | Current search query (displayed in header) |
| `loading` | `boolean` | `false` | No | Whether results are currently loading |
| `error` | `string` | `''` | No | Error message to display (if any) |
| `total` | `number` | `0` | No | Total number of results matching query |
| `page` | `number` | `1` | No | Current page number (1-indexed) |
| `pageSize` | `number` | `20` | No | Number of results per page |

## Events

| Name | Payload | Description |
|------|---------|-------------|
| `update:page` | `number` | Emitted when user navigates to a different page |
| `update:sort` | `string` | Emitted when user changes sort order |
| `result-click` | `SearchResult` | Emitted when user clicks on a result |

## Slots

| Name | Props | Description |
|------|-------|-------------|
| (default) | None | Not used - results are rendered via SearchResultItem |

## TypeScript Interfaces

```typescript
interface SearchResult {
  id: string                              // Unique result ID
  title: string                           // Document title
  content: string                         // Document content/excerpt
  document_type: string                   // Type: 'note', 'lab', 'imaging', etc.
  author: string                          // Document author name
  date: string                            // Document date (ISO 8601)
  score: number                           // Relevance score (0-100)
  highlights?: {
    title?: string[]                      // HTML snippet with <mark> tags
    content?: string[]                    // HTML snippet with <mark> tags
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
```

## Usage Examples

### Basic Usage

```vue
<template>
  <SearchResults
    :results="searchResults"
    :loading="isLoading"
    :error="searchError"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SearchResults from '@/components/search/SearchResults.vue'
import { usePatientSearch } from '@/composables/usePatientSearch'

const { results: searchResults, isLoading, error: searchError } = usePatientSearch()
</script>
```

### With Query Display and Pagination

```vue
<template>
  <SearchResults
    :results="results"
    :query="currentQuery"
    :loading="isLoading"
    :error="error"
    :total="total"
    :page="page"
    :page-size="pageSize"
    @update:page="handlePageChange"
    @update:sort="handleSortChange"
    @result-click="handleResultClick"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SearchResults from '@/components/search/SearchResults.vue'

const results = ref([])
const currentQuery = ref('diabetes')
const isLoading = ref(false)
const error = ref('')
const total = ref(150)
const page = ref(1)
const pageSize = ref(20)

const handlePageChange = (newPage: number) => {
  page.value = newPage
  // Fetch new page of results
  console.log(`Navigating to page ${newPage}`)
}

const handleSortChange = (sortOption: string) => {
  console.log(`Sort changed to: ${sortOption}`)
  // Update results with new sort order
}

const handleResultClick = (result) => {
  console.log('Clicked result:', result.id)
  // Navigate to detail view or open modal
}
</script>
```

## Computed Properties

```typescript
// Number of results to display
resultsCount = computed(() => props.total || props.results.length)

// Number of pages needed for pagination
totalPages = computed(() => Math.ceil(props.total / props.pageSize))
```

## Component States

### Loading State

Displays skeleton loaders while results are being fetched:

```vue
<v-skeleton-loader
  v-for="i in 3"
  :key="i"
  type="article"
  class="mb-4"
/>
```

**When to show**: `loading === true`

### Error State

Displays error message in alert:

```vue
<v-alert
  v-else-if="error"
  type="error"
  variant="tonal"
  class="mb-4"
>
  {{ error }}
</v-alert>
```

**When to show**: `error !== '' && !loading`

### Empty State

Displays empty state message:

```vue
<v-alert
  v-else-if="!loading && results.length === 0"
  type="info"
  variant="tonal"
  class="mb-4"
>
  No results found. Try adjusting your search query or filters.
</v-alert>
```

**When to show**: `!loading && results.length === 0 && query !== ''`

### Results State

Displays results list with pagination:

```vue
<SearchResultItem
  v-for="(result, index) in results"
  :key="result.id"
  :result="result"
  :index="index"
  @click="handleResultClick(result)"
/>
```

**When to show**: `results.length > 0`

## Sorting Options

The component provides the following sort options:

| Option | Value | Description |
|--------|-------|-------------|
| Relevance | `relevance` | Sort by Elasticsearch score (default) |
| Date (Newest) | `date_desc` | Most recent documents first |
| Date (Oldest) | `date_asc` | Oldest documents first |
| Title (A-Z) | `title_asc` | Alphabetical title order |
| Title (Z-A) | `title_desc` | Reverse alphabetical order |

## Pagination

- **Current page**: Controlled via `page` prop (1-indexed)
- **Page size**: Configurable via `pageSize` prop (default: 20)
- **Total results**: Passed via `total` prop
- **Page navigation**: Uses Vuetify's `v-pagination` component
- **Visible pages**: Shows up to 7 page numbers in pagination control

## Accessibility

- ✅ **Semantic HTML**: Uses proper heading hierarchy (`<h2>` for results count)
- ✅ **ARIA labels**: Sort select and pagination have implicit labels
- ✅ **Keyboard navigation**:
  - Tab through sort dropdown
  - Tab through pagination
  - Enter to select page
  - Space to expand options
- ✅ **Focus management**: Focus indicators visible via Vuetify
- ✅ **Screen reader support**:
  - Results count announced
  - Error and empty states announced
  - Pagination current page announced

### Accessibility Tips

1. **Add aria-label for context**:
   ```html
   <SearchResults
     aria-label="Search results list"
     role="region"
   />
   ```

2. **Announce result changes**:
   ```typescript
   const resultCount = computed(() => props.results.length)
   watch(resultCount, (newCount) => {
     // Announce to screen readers
     console.log(`${newCount} results loaded`)
   })
   ```

3. **Add result descriptions**:
   - Title clearly indicates document content
   - Metadata provides context (type, author, date)
   - Relevance score explains confidence level

## Styling

### CSS Classes

```css
.search-results-container {
  min-height: 400px;
}
```

### Vuetify Classes Used

- `v-container` - Responsive container
- `v-row` / `v-col` - Grid layout
- `v-skeleton-loader` - Loading state
- `v-alert` - Error/empty states
- `v-pagination` - Page navigation
- `v-select` - Sort dropdown

### Customization

To customize styling, override Vuetify theme variables:

```typescript
// vuetify.config.ts
export default {
  theme: {
    variables: {
      'surface': '#ffffff',
      'primary': '#1f77b4',
      'success': '#2ca02c',
      'warning': '#ff7f0e',
      'error': '#d62728'
    }
  }
}
```

## Performance Considerations

### Optimization Strategies

1. **Virtual Scrolling**: For large result sets (100+), consider virtual scrolling:
   ```vue
   <v-virtual-scroll
     :items="results"
     height="500"
   >
     <template v-slot="{ item }">
       <SearchResultItem :result="item" />
     </template>
   </v-virtual-scroll>
   ```

2. **Lazy Loading**: Load additional results as user scrolls
   ```typescript
   const handleEndReached = async () => {
     if (page.value < totalPages.value) {
       await search(query, undefined, page.value + 1)
     }
   }
   ```

3. **Debounced Sort Changes**: Avoid excessive API calls
   ```typescript
   const debouncedSort = useDebounceFn(handleSortChange, 300)
   ```

### Benchmarks

| Operation | Target | Notes |
|-----------|--------|-------|
| Render 20 results | <100ms | Measured with Vue DevTools |
| Sort change | <300ms | Including API call |
| Page change | <500ms | Including API call |
| Pagination component | <20ms | Just UI rendering |

## Integration with usePatientSearch

The component works seamlessly with the `usePatientSearch` composable:

```typescript
import { usePatientSearch } from '@/composables/usePatientSearch'

const {
  results,          // SearchResult[]
  total,            // number
  page,             // number
  pageSize,         // number
  isLoading,        // boolean
  error,            // string | null
  search            // function
} = usePatientSearch()
```

## Error Handling

### Common Errors

1. **Search API Error**:
   ```vue
   error="Failed to fetch results. Please try again."
   ```

2. **Network Timeout**:
   ```vue
   error="Request timed out. Check your connection and try again."
   ```

3. **Invalid Query**:
   ```vue
   error="Invalid search query. Please enter a valid medical concept."
   ```

### Handling Errors

```typescript
const handleSearch = async (query: string) => {
  try {
    await search(query)
  } catch (err) {
    console.error('Search failed:', err)
    // Error automatically set in composable
    // Component displays it via error prop
  }
}
```

## Parent Component Integration

Typical parent component using SearchResults:

```vue
<template>
  <v-container>
    <SearchBar @search="handleSearch" />
    <SearchResults
      :results="results"
      :query="currentQuery"
      :loading="isLoading"
      :error="error"
      :total="total"
      :page="currentPage"
      :page-size="pageSize"
      @update:page="handlePageChange"
      @update:sort="handleSortChange"
      @result-click="handleResultClick"
    />
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SearchBar from '@/components/search/SearchBar.vue'
import SearchResults from '@/components/search/SearchResults.vue'
import { usePatientSearch } from '@/composables/usePatientSearch'

const currentQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

const { results, total, isLoading, error, search } = usePatientSearch()

const handleSearch = async (query: string) => {
  currentQuery.value = query
  currentPage.value = 1
  await search(query)
}

const handlePageChange = async (page: number) => {
  currentPage.value = page
  await search(currentQuery.value, undefined, page, pageSize.value)
}

const handleSortChange = (sort: string) => {
  console.log('Sort:', sort)
}

const handleResultClick = (result) => {
  console.log('Clicked:', result.id)
}
</script>
```

## Testing

### Unit Tests

See `tests/unit/components/search/SearchResults.spec.ts` for comprehensive test coverage:

- Props validation
- Event emission
- Computed properties
- Component states (loading, error, empty, results)
- Pagination
- Sorting

### Example Test

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SearchResults from '@/components/search/SearchResults.vue'

describe('SearchResults.vue', () => {
  it('displays loading state', () => {
    const wrapper = mount(SearchResults, {
      props: { loading: true }
    })
    expect(wrapper.find('.v-skeleton-loader').exists()).toBe(true)
  })

  it('emits update:page event', async () => {
    const wrapper = mount(SearchResults, {
      props: {
        results: [{ id: '1', title: 'Test', /* ... */ }],
        total: 40,
        pageSize: 20
      }
    })
    await wrapper.find('.v-pagination').trigger('update:model-value', 2)
    expect(wrapper.emitted('update:page')).toBeTruthy()
  })
})
```

---

**Last Updated**: 2025-11-21
**Component Version**: 1.0.0
