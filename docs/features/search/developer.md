# Search Module Developer Guide

## Overview

This guide is for developers who want to extend or modify the search module. It covers architecture, patterns, and best practices for adding new features.

## Architecture

### Component Hierarchy

```
SearchPage (Consumer)
├── SearchBar
│   └── Emits: search, update:modelValue, clear, focus, blur, clear-error
│
├── SearchFilters (optional)
│   └── Emits: update:filters
│
└── SearchResults
    ├── Renders SearchResultItem[] (via v-for)
    ├── Pagination controls (v-pagination)
    ├── Sort dropdown (v-select)
    └── Loading skeleton / Error alert / Empty state
```

### Data Flow

```
User Input (SearchBar)
    ↓
usePatientSearch (Composable State Management)
    ├── Manages: query, results, page, filters, sort, error, isLoading
    ├── Caches: SearchCache (last 10 searches)
    └── Validates: Query length, empty check
    ↓
Search API (FastAPI Backend)
    ├── POST /api/v1/patients/search
    ├── Authentication: JWT token (RBAC)
    ├── Audit Logging: All searches logged with user ID
    └── Returns: SearchResponse with results, total, highlights
    ↓
Elasticsearch
    ├── Multi-match query on title, content
    ├── Boosting: title^10, content^1
    ├── Filtering: document types, authors, dates
    ├── Highlighting: <mark> tags on matches
    └── Pagination: search_after (cursor-based)
    ↓
Frontend Display
    ├── SearchResults renders results
    ├── Sanitization: DOMPurify removes XSS
    ├── Highlighting: Preserved in SearchResultItem
    └── Pagination: Click to fetch next page
```

### State Management Pattern

Using Vue 3 Composition API with `usePatientSearch` composable:

```typescript
// Central state machine in composable
const query = ref<string>('')
const results = ref<SearchResult[]>([])
const page = ref<number>(1)
const isLoading = ref<boolean>(false)
const error = ref<string | null>(null)

// Computed properties for derived state
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))
const isEmpty = computed(() => !isLoading && results.length === 0 && query.trim() !== '')

// Methods for state transitions
const search = async (query?: string): Promise<void> => {
  // 1. Validate input
  // 2. Check cache
  // 3. Set loading = true
  // 4. Call API
  // 5. Update results, total, page
  // 6. Set error or clear error
  // 7. Set loading = false
}
```

## Adding New Features

### Scenario 1: Add Search Filter

**Goal**: Add filtering by document type (note, lab, imaging, discharge, etc.)

**Steps**:

#### Step 1: Create Filter Component

```vue
<!-- frontend/src/components/search/SearchFilters.vue -->
<template>
  <v-card class="mb-4">
    <v-card-title>Filters</v-card-title>
    <v-card-text>
      <!-- Document Type Filter -->
      <v-label class="mb-2">Document Type</v-label>
      <v-checkbox
        v-for="type in documentTypes"
        :key="type"
        :label="type"
        :model-value="selectedTypes.includes(type)"
        @update:model-value="toggleType(type)"
      />

      <!-- Date Range Filter -->
      <v-label class="mb-2 mt-4">Date Range</v-label>
      <v-date-input
        v-model="dateRange"
        range
      />
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  selectedDocumentTypes?: string[]
  selectedDateRange?: [Date, Date]
}

const props = withDefaults(defineProps<Props>(), {
  selectedDocumentTypes: () => [],
  selectedDateRange: () => [new Date(2020, 0, 1), new Date()]
})

const emit = defineEmits<{
  'update:documentTypes': [types: string[]]
  'update:dateRange': [range: [Date, Date]]
}>()

const documentTypes = ['note', 'lab', 'imaging', 'discharge', 'letter']
const selectedTypes = ref<string[]>(props.selectedDocumentTypes)
const dateRange = ref<[Date, Date]>(props.selectedDateRange)

const toggleType = (type: string) => {
  const idx = selectedTypes.value.indexOf(type)
  if (idx > -1) {
    selectedTypes.value.splice(idx, 1)
  } else {
    selectedTypes.value.push(type)
  }
  emit('update:documentTypes', selectedTypes.value)
}

watch(dateRange, (newRange) => {
  emit('update:dateRange', newRange)
}, { deep: true })
</script>
```

#### Step 2: Update Composable to Accept Filters

```typescript
// frontend/src/composables/usePatientSearch.ts

interface SearchFilters {
  documentTypes?: string[]
  authors?: string[]
  dateFrom?: Date
  dateTo?: Date
}

const filters = ref<SearchFilters>()

const search = async (
  searchQuery?: string,
  searchFilters?: SearchFilters,
  pageNum: number = 1
): Promise<void> => {
  // Include filters in API request
  const response = await searchApi({
    query: q.trim(),
    filters: searchFilters,  // Send to API
    page: pageNum,
    page_size: pageSize.value,
    sort: sort.value,
  })
}
```

#### Step 3: Update API Handler to Use Filters

```python
# backend/app/services/search_service.py

class SearchService:
  async def search_documents(
    self,
    request: SearchRequest,
    user: User,
    ip_address: str
  ) -> SearchResponse:
    # Build Elasticsearch query with filters
    query_filters = []

    if request.filters and request.filters.document_types:
      query_filters.append({
        "terms": {
          "document_type": request.filters.document_types
        }
      })

    if request.filters and request.filters.date_from:
      query_filters.append({
        "range": {
          "date": {"gte": request.filters.date_from}
        }
      })

    # Execute search with filters
    results = await self.es_client.search(
      index="documents",
      body={
        "query": {
          "bool": {
            "must": [
              {"multi_match": {"query": request.query, "fields": [...]}}
            ],
            "filter": query_filters
          }
        }
      }
    )
```

#### Step 4: Update SearchResults Component to Show Filters

```vue
<template>
  <v-container>
    <v-row>
      <v-col cols="12" md="3">
        <SearchFilters
          :selected-document-types="selectedFilters.documentTypes"
          :selected-date-range="selectedFilters.dateRange"
          @update:documentTypes="handleFilterChange"
          @update:dateRange="handleFilterChange"
        />
      </v-col>

      <v-col cols="12" md="9">
        <!-- Results display -->
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
const { search } = usePatientSearch()

const selectedFilters = ref({
  documentTypes: [],
  dateRange: [new Date(), new Date()]
})

const handleFilterChange = async () => {
  // Re-search with new filters
  await search(currentQuery.value, selectedFilters.value, 1)
}
</script>
```

### Scenario 2: Add Custom Result Template

**Goal**: Display custom content for different result types (notes vs labs vs imaging)

**Steps**:

#### Step 1: Create Result Type Components

```vue
<!-- frontend/src/components/search/results/NoteResult.vue -->
<template>
  <v-card class="mb-4">
    <v-card-title>
      {{ result.title }}
      <v-chip size="small" class="ml-2">Note</v-chip>
    </v-card-title>
    <v-card-subtitle>
      {{ result.author }} - {{ formatDate(result.date) }}
    </v-card-subtitle>
    <v-card-text>
      <!-- Clinical note specific layout -->
      <div class="note-content" v-html="sanitizeHtml(result.highlights?.content[0])"></div>
      <v-divider class="my-2"></v-divider>
      <div class="text-caption text-medium-emphasis">
        Confidence: {{ result.score }}
      </div>
    </v-card-text>
  </v-card>
</template>
```

#### Step 2: Update SearchResultItem to Use Template Selector

```vue
<!-- frontend/src/components/search/SearchResultItem.vue -->
<template>
  <!-- Route to appropriate result template -->
  <component
    :is="getResultComponent(result.document_type)"
    :result="result"
    :index="index"
    @click="$emit('click')"
  />
</template>

<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import NoteResult from './results/NoteResult.vue'
import LabResult from './results/LabResult.vue'
import ImagingResult from './results/ImagingResult.vue'

const resultComponents = {
  'note': NoteResult,
  'lab': LabResult,
  'imaging': ImagingResult
}

const getResultComponent = (type: string) => {
  return resultComponents[type] || NoteResult
}
</script>
```

### Scenario 3: Add Search History & Saved Searches

**Goal**: Store recent searches and allow saving queries for reuse

**Steps**:

#### Step 1: Create Storage Service

```typescript
// frontend/src/services/searchStorage.ts

export interface SavedSearch {
  id: string
  name: string
  query: string
  filters: SearchFilters
  createdAt: Date
  lastUsedAt: Date
}

export class SearchStorageService {
  private storageKey = 'search_history'
  private savedSearchesKey = 'saved_searches'

  // Store recent search in localStorage
  saveSearchHistory(query: string, filters?: SearchFilters): void {
    const history = this.getSearchHistory()
    history.unshift({ query, filters, timestamp: Date.now() })
    // Keep last 10
    history.splice(10)
    localStorage.setItem(this.storageKey, JSON.stringify(history))
  }

  getSearchHistory(): Array<{query: string, filters?: SearchFilters, timestamp: number}> {
    const data = localStorage.getItem(this.storageKey)
    return data ? JSON.parse(data) : []
  }

  // Save search for reuse
  saveSearch(name: string, query: string, filters?: SearchFilters): SavedSearch {
    const saved: SavedSearch = {
      id: generateId(),
      name,
      query,
      filters,
      createdAt: new Date(),
      lastUsedAt: new Date()
    }

    const searches = this.getSavedSearches()
    searches.push(saved)
    localStorage.setItem(this.savedSearchesKey, JSON.stringify(searches))
    return saved
  }

  getSavedSearches(): SavedSearch[] {
    const data = localStorage.getItem(this.savedSearchesKey)
    return data ? JSON.parse(data) : []
  }
}
```

#### Step 2: Create Search History Component

```vue
<!-- frontend/src/components/search/SearchHistory.vue -->
<template>
  <v-menu>
    <template #activator="{ props }">
      <v-btn
        icon="mdi-history"
        v-bind="props"
        variant="text"
      />
    </template>

    <v-list>
      <v-list-subheader>Recent Searches</v-list-subheader>
      <v-list-item
        v-for="item in recentSearches"
        :key="item.timestamp"
        @click="selectSearch(item.query, item.filters)"
      >
        {{ item.query }}
        <template #append>
          <v-btn
            icon="mdi-close"
            size="x-small"
            @click.stop="deleteSearch(item.timestamp)"
          />
        </template>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { SearchStorageService } from '@/services/searchStorage'

const storage = new SearchStorageService()
const recentSearches = ref([])

onMounted(() => {
  recentSearches.value = storage.getSearchHistory()
})

const selectSearch = async (query: string, filters: any) => {
  emit('select-search', { query, filters })
}
</script>
```

## Testing Guide

### Unit Testing Components

```typescript
// frontend/src/components/search/__tests__/SearchBar.spec.ts
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import SearchBar from '../SearchBar.vue'

describe('SearchBar.vue', () => {
  it('emits search event when Enter pressed', async () => {
    const wrapper = mount(SearchBar)
    const input = wrapper.find('input')

    await input.setValue('diabetes')
    await input.trigger('keydown.enter')

    expect(wrapper.emitted('search')).toBeTruthy()
    expect(wrapper.emitted('search')[0]).toEqual(['diabetes'])
  })

  it('sanitizes malicious input', async () => {
    const wrapper = mount(SearchBar)
    const maliciousInput = '<script>alert("xss")</script>'

    await wrapper.find('input').setValue(maliciousInput)

    // Component should render safely
    expect(wrapper.html()).not.toContain('<script>')
  })
})
```

### Integration Testing

```typescript
// frontend/src/composables/__tests__/usePatientSearch.integration.spec.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { usePatientSearch } from '../usePatientSearch'
import { mockSearchApi } from '@/api/__mocks__/search'

describe('usePatientSearch Integration', () => {
  beforeEach(() => {
    mockSearchApi.reset()
  })

  it('performs complete search flow', async () => {
    const { query, results, search, totalPages } = usePatientSearch()

    // 1. Set query
    query.value = 'diabetes'

    // 2. Perform search
    await search('diabetes')

    // 3. Verify results
    expect(results.value.length).toBeGreaterThan(0)
    expect(totalPages.value).toBeGreaterThan(0)
  })

  it('handles API errors gracefully', async () => {
    mockSearchApi.mockError()
    const { search, error, isLoading } = usePatientSearch()

    await search('invalid')

    expect(error.value).toBeTruthy()
    expect(isLoading.value).toBe(false)
  })
})
```

### E2E Testing

```typescript
// frontend/e2e/search.e2e.ts
import { describe, it, expect } from 'vitest'
import { page, browser } from '@playwright/test'

describe('Search Module E2E', () => {
  it('complete search workflow', async () => {
    // 1. Navigate to search page
    await page.goto('/search')

    // 2. Type search query
    await page.fill('input[placeholder*="Search"]', 'diabetes')

    // 3. Press Enter
    await page.press('input', 'Enter')

    // 4. Wait for results
    await page.waitForSelector('[data-testid="search-result"]')

    // 5. Verify results displayed
    const results = await page.locator('[data-testid="search-result"]')
    expect(await results.count()).toBeGreaterThan(0)

    // 6. Click pagination
    await page.click('text="2"')

    // 7. Verify new results loaded
    await page.waitForTimeout(500)
    const newResults = await page.locator('[data-testid="search-result"]')
    expect(await newResults.count()).toBeGreaterThan(0)
  })
})
```

## Performance Optimization

### Caching Strategy

The `usePatientSearch` composable includes a SearchCache that stores recent search results:

```typescript
class SearchCache {
  private cache: Map<string, CacheEntry> = new Map()
  private readonly maxSize = 10  // Store last 10 searches

  // Cache key is combination of query, filters, and sort
  private getKey(query: string, filters?: SearchFilters, sort: SortOption = 'relevance'): string {
    return `${query}::${JSON.stringify(filters)}::${sort}`
  }

  // Before calling API, check cache
  get(query: string, filters?: SearchFilters, sort: SortOption = 'relevance'): SearchResponse | null {
    return this.cache.get(this.getKey(query, filters, sort))?.response
  }

  // After API response, cache results
  set(query: string, filters: SearchFilters | undefined, sort: SortOption, response: SearchResponse): void {
    // Evict oldest entry if cache full
    if (this.cache.size >= this.maxSize) {
      const oldestKey = Array.from(this.cache.entries())
        .sort(([_, a], [__, b]) => a.timestamp - b.timestamp)[0][0]
      this.cache.delete(oldestKey)
    }
    this.cache.set(this.getKey(query, filters, sort), {
      response,
      timestamp: Date.now()
    })
  }
}
```

### Debouncing

Search input is debounced to 300ms by default to prevent excessive API calls:

```typescript
watchDebounced(
  query,
  async (newQuery) => {
    if (newQuery.trim() !== '') {
      await performSearch(newQuery)
    }
  },
  { debounce: 300 }  // Wait 300ms after user stops typing
)
```

### Pagination

Use cursor-based pagination (search_after) instead of offset for better performance:

```typescript
// In Elasticsearch query
"search_after": [last_document_sort_value],
"sort": [{ "_score": "desc" }, { "_id": "asc" }]
```

## Common Patterns

### Pattern 1: Search with Debounce

```typescript
const query = ref<string>('')

watchDebounced(query, async (newQuery) => {
  if (newQuery.trim()) {
    await search(newQuery)
  }
}, { debounce: 300 })
```

### Pattern 2: Handle Pagination

```typescript
const handlePageChange = async (newPage: number) => {
  page.value = newPage
  await performSearch(query.value, filters.value, newPage)
}
```

### Pattern 3: Clear Results

```typescript
const handleClear = () => {
  query.value = ''
  results.value = []
  page.value = 1
  error.value = null
}
```

### Pattern 4: Error Handling

```typescript
try {
  await search(query)
} catch (err: any) {
  error.value = err.response?.data?.detail || err.message || 'Search failed'
}
```

## Security Considerations

### XSS Prevention

All HTML from Elasticsearch is sanitized with DOMPurify before rendering:

```typescript
import { sanitizeHtml } from '@/utils/sanitize'

// In template
<div v-html="sanitizeHtml(result.highlights.content[0])"></div>

// DOMPurify config
DOMPurify.sanitize(html, {
  ALLOWED_TAGS: ['mark'],      // Only allow <mark> tags
  ALLOWED_ATTR: [],             // No attributes
  KEEP_CONTENT: true            // Preserve text if tag stripped
})
```

### Input Validation

Validate search queries before sending to API:

```typescript
const validateQuery = (query: string): string | null => {
  if (!query || query.trim() === '') {
    return 'Please enter a search query'
  }
  if (query.length > 1000) {
    return 'Search query too long (max 1000 characters)'
  }
  if (query.includes('javascript:')) {
    return 'Invalid characters in search query'
  }
  return null
}
```

### Rate Limiting

API enforces rate limiting (100 requests/minute per user). Handle 429 errors:

```typescript
if (err.status === 429) {
  error.value = 'Too many requests. Please wait before searching again.'
}
```

## Debugging Tips

### Enable Vue DevTools

1. Install Vue DevTools browser extension
2. Open DevTools → Vue tab
3. Select SearchResults component
4. Inspect props and state in real-time

### Console Logging

Add logging to understand data flow:

```typescript
const search = async (query: string) => {
  console.log('🔍 Searching for:', query)

  try {
    const response = await searchApi(query)
    console.log('✅ Results:', response.results.length)
  } catch (err) {
    console.error('❌ Search error:', err)
  }
}
```

### Network Inspection

1. Open DevTools → Network tab
2. Type in search
3. Look for POST /api/v1/patients/search request
4. Inspect request body and response

### Performance Profiling

1. Open DevTools → Performance tab
2. Record while performing search
3. Check for:
   - Long-running scripts
   - Excessive re-renders
   - Slow API responses

## Troubleshooting Development Issues

### Issue: Search not returning results

**Debug steps**:
1. Check API response: `console.log(response)`
2. Verify Elasticsearch is running: `curl http://localhost:9200`
3. Check index exists: `curl http://localhost:9200/_cat/indices`
4. Test query directly: `curl -X POST http://localhost:9200/documents/_search -d '{"query": {"match_all": {}}}'`

### Issue: Highlights not showing

**Debug steps**:
1. Check highlights in API response: `console.log(result.highlights)`
2. Verify sanitization not removing HTML: `console.log(sanitizeHtml(html))`
3. Check CSS for `.mark` styling

### Issue: Pagination broken

**Debug steps**:
1. Verify total count: `console.log(total.value)`
2. Check page calculation: `console.log(totalPages.value)`
3. Verify page change event emits: `console.log(emitted('update:page'))`

## Contributing

When adding new features to the search module:

1. **Write tests first**: Use TDD approach
2. **Follow patterns**: Use existing patterns for consistency
3. **Document changes**: Update this guide and inline comments
4. **Test security**: Use XSS payload test vectors
5. **Performance test**: Benchmark API response times
6. **Update README.md**: Link to new documentation

---

**Last Updated**: 2025-11-22
**Version**: 1.0.0
