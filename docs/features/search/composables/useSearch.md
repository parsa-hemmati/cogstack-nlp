# usePatientSearch Composable

## Description

The `usePatientSearch` composable provides reusable search logic for patient search functionality. It manages search state (query, results, pagination, loading/error states) and provides methods for performing searches, navigating pages, and clearing results.

This composable is the central state manager for the search module and should be imported in any component that needs search functionality.

## Location

`frontend/src/composables/usePatientSearch.ts`

## Returned State

All returned state is reactive (using Vue `ref` and `computed`):

```typescript
interface UsePatientSearchReturn {
  // State (Refs)
  results: Ref<PatientSearchResult[]>    // Array of search results
  total: Ref<number>                      // Total matching results
  page: Ref<number>                       // Current page (1-indexed)
  pageSize: Ref<number>                   // Results per page
  queryTimeMs: Ref<number>                // Search response time (ms)
  isLoading: Ref<boolean>                 // Search in progress
  error: Ref<string | null>               // Error message (if any)
  lastSearchConcept: Ref<string>          // Last searched concept

  // Computed properties
  totalPages: ComputedRef<number>         // Calculated: ceil(total / pageSize)
  hasResults: ComputedRef<boolean>        // true if results.length > 0
  isEmpty: ComputedRef<boolean>           // true if no results and query was entered

  // Methods
  search: Function                        // Perform search
  nextPage: Function                      // Go to next page
  previousPage: Function                  // Go to previous page
  goToPage: Function                      // Go to specific page
  clearResults: Function                  // Clear all results and state
  clearError: Function                    // Clear error message
}
```

## Usage

### Basic Search

```typescript
import { usePatientSearch } from '@/composables/usePatientSearch'

export default {
  setup() {
    const { results, isLoading, search } = usePatientSearch()

    const handleSearch = async (concept: string) => {
      await search(concept)
      console.log(`Found ${results.value.length} results`)
    }

    return { results, isLoading, handleSearch }
  }
}
```

### In Composition API

```typescript
import { usePatientSearch } from '@/composables/usePatientSearch'

export default {
  setup() {
    const {
      results,
      total,
      page,
      pageSize,
      isLoading,
      error,
      search,
      nextPage,
      previousPage,
      clearResults
    } = usePatientSearch()

    return {
      results,
      total,
      page,
      pageSize,
      isLoading,
      error,
      search,
      nextPage,
      previousPage,
      clearResults
    }
  }
}
```

### In `<script setup>`

```typescript
import { usePatientSearch } from '@/composables/usePatientSearch'

const {
  results,
  total,
  page,
  pageSize,
  isLoading,
  error,
  totalPages,
  hasResults,
  isEmpty,
  search,
  nextPage,
  previousPage,
  goToPage,
  clearResults,
  clearError
} = usePatientSearch()
```

## Returned State Details

### State Properties

#### `results: Ref<PatientSearchResult[]>`

Array of search results from the current page.

**Type**:
```typescript
type PatientSearchResult = {
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
```

**Example**:
```typescript
const { results } = usePatientSearch()
// results.value = [
//   {
//     id: 'doc-123',
//     title: 'Discharge Summary',
//     content: 'Patient was discharged in stable condition',
//     document_type: 'note',
//     author: 'Dr. Smith',
//     date: '2024-01-15',
//     score: 95.5,
//     highlights: {
//       title: ['<mark>discharge</mark> summary'],
//       content: ['Patient was <mark>discharged</mark> in stable condition']
//     }
//   }
// ]
```

#### `total: Ref<number>`

Total number of results matching the search query (may be larger than results array).

**Example**:
```typescript
const { total } = usePatientSearch()
// If searching for 'diabetes' returns 150 total results
// But only 20 displayed on current page
total.value = 150
```

#### `page: Ref<number>`

Current page number (1-indexed, not 0-indexed).

**Example**:
```typescript
const { page } = usePatientSearch()
page.value = 1  // First page
page.value = 2  // Second page
```

#### `pageSize: Ref<number>`

Number of results per page (default: 20).

**Example**:
```typescript
const { pageSize } = usePatientSearch()
pageSize.value = 20  // Default
pageSize.value = 50  // Custom page size
```

#### `queryTimeMs: Ref<number>`

Time taken for the search API to respond (in milliseconds).

**Example**:
```typescript
const { queryTimeMs } = usePatientSearch()
// After search completes
console.log(`Search took ${queryTimeMs.value}ms`)
```

#### `isLoading: Ref<boolean>`

Whether a search is currently in progress.

**Example**:
```typescript
const { isLoading } = usePatientSearch()

watch(isLoading, (loading) => {
  if (loading) {
    console.log('Searching...')
  } else {
    console.log('Search complete!')
  }
})
```

#### `error: Ref<string | null>`

Error message from the last search (or `null` if no error).

**Example**:
```typescript
const { error } = usePatientSearch()
// error.value = null (no error)
// error.value = 'Search failed. Please try again.' (error occurred)
```

#### `lastSearchConcept: Ref<string>`

The last concept that was searched for (for tracking/analytics).

**Example**:
```typescript
const { lastSearchConcept } = usePatientSearch()
// After searching 'diabetes'
lastSearchConcept.value = 'diabetes'
```

### Computed Properties

#### `totalPages: ComputedRef<number>`

Calculated number of pages based on total results and page size.

**Formula**: `Math.ceil(total / pageSize)`

**Example**:
```typescript
const { total, pageSize, totalPages } = usePatientSearch()
// total = 150, pageSize = 20
// totalPages = ceil(150 / 20) = 8
```

**Use case**: Displaying pagination controls

```typescript
<v-pagination
  :length="totalPages"
  v-model="page"
/>
```

#### `hasResults: ComputedRef<boolean>`

Whether the current search has any results.

**Logic**: `results.length > 0`

**Example**:
```typescript
const { results, hasResults } = usePatientSearch()
<div v-if="hasResults">
  Results found!
</div>
```

#### `isEmpty: ComputedRef<boolean>`

Whether the search is empty (no results and a query was entered).

**Logic**: `!isLoading && results.length === 0 && lastSearchConcept !== ''`

**Example**:
```typescript
const { isEmpty } = usePatientSearch()
<v-alert v-if="isEmpty" type="info">
  No results found. Try adjusting your search.
</v-alert>
```

## Returned Methods

All methods are async (return Promises) and automatically update state.

### `search(concept, filters?, pageNum?, size?): Promise<void>`

Perform a search with optional filters and pagination.

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `concept` | `string` | - | Medical concept to search (required) |
| `filters` | `SearchFilters` | `{}` | Meta-annotation filters (optional) |
| `pageNum` | `number` | `1` | Page number to fetch (optional) |
| `size` | `number` | `20` | Results per page (optional) |

**Types**:
```typescript
type SearchFilters = {
  Negation?: 'Affirmed' | 'Negated'
  Experiencer?: 'Patient' | 'Family' | 'Other'
  Temporality?: 'Current' | 'Recent' | 'Historical' | 'Future'
  Certainty?: 'Certain' | 'Possible' | 'Hypothetical'
}
```

**Returns**: `Promise<void>` - Resolves when search completes

**Side effects**:
- Sets `isLoading = true` while fetching
- Updates `results` with search results
- Updates `total` with result count
- Updates `page` and `pageSize`
- Updates `queryTimeMs` with response time
- Sets `error = null` on success
- Sets `error` to error message on failure

**Example**:
```typescript
const { search, results, isLoading } = usePatientSearch()

// Simple search
await search('diabetes')
console.log(`Found ${results.value.length} results`)

// Search with filters
await search('diabetes', {
  Negation: 'Affirmed',
  Experiencer: 'Patient'
})

// Search with pagination
await search('diabetes', {}, 2, 50)
// Page 2, 50 results per page
```

### `nextPage(concept, filters?): Promise<void>`

Go to the next page of results.

**Parameters**:
- `concept` (string, required): The search concept to use
- `filters` (SearchFilters, optional): Meta-annotation filters

**Precondition**: `page < totalPages`

**Example**:
```typescript
const { page, totalPages, nextPage } = usePatientSearch()

if (page.value < totalPages.value) {
  await nextPage('diabetes')
  // page.value is now incremented by 1
}
```

### `previousPage(concept, filters?): Promise<void>`

Go to the previous page of results.

**Parameters**:
- `concept` (string, required): The search concept to use
- `filters` (SearchFilters, optional): Meta-annotation filters

**Precondition**: `page > 1`

**Example**:
```typescript
const { page, previousPage } = usePatientSearch()

if (page.value > 1) {
  await previousPage('diabetes')
  // page.value is now decremented by 1
}
```

### `goToPage(concept, filters, targetPage): Promise<void>`

Go to a specific page number.

**Parameters**:
- `concept` (string, required): The search concept
- `filters` (SearchFilters | undefined, required but can be undefined): Meta-annotation filters
- `targetPage` (number, required): The page to navigate to (1-indexed)

**Validation**: Only works if `1 <= targetPage <= totalPages`

**Example**:
```typescript
const { goToPage, totalPages } = usePatientSearch()

// Jump to page 5
await goToPage('diabetes', undefined, 5)

// With filters
await goToPage('diabetes', {
  Negation: 'Affirmed'
}, 3)
```

### `clearResults(): void`

Clear all search results and reset state.

**Clears**:
- `results = []`
- `total = 0`
- `page = 1`
- `queryTimeMs = 0`
- `error = null`
- `lastSearchConcept = ''`

**Example**:
```typescript
const { clearResults } = usePatientSearch()

// Clear results when user navigates away
onUnmounted(() => {
  clearResults()
})
```

### `clearError(): void`

Clear the error message.

**Example**:
```typescript
const { error, clearError } = usePatientSearch()

// Clear error when user acknowledges it
const handleDismissError = () => {
  clearError()
}
```

## TypeScript Types

Export these types from the composable for use in other files:

```typescript
// From API client
type PatientSearchRequest = {
  concept: string
  filters?: SearchFilters
  pagination?: {
    page: number
    pageSize: number
  }
  sort?: string
}

type PatientSearchResponse = {
  results: PatientSearchResult[]
  pagination: {
    totalResults: number
    page: number
    pageSize: number
  }
  performance: {
    searchTime: number
  }
}

type PatientSearchResult = {
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

type SearchFilters = {
  Negation?: 'Affirmed' | 'Negated'
  Experiencer?: 'Patient' | 'Family' | 'Other'
  Temporality?: 'Current' | 'Recent' | 'Historical' | 'Future'
  Certainty?: 'Certain' | 'Possible' | 'Hypothetical'
}
```

## Usage Patterns

### Pattern 1: Search Page Component

```vue
<template>
  <div>
    <SearchBar @search="handleSearch" />
    <SearchResults
      :results="results"
      :total="total"
      :page="page"
      :page-size="pageSize"
      :loading="isLoading"
      :error="error"
      @update:page="goToPage"
    />
  </div>
</template>

<script setup lang="ts">
import { usePatientSearch } from '@/composables/usePatientSearch'

const {
  results,
  total,
  page,
  pageSize,
  isLoading,
  error,
  search,
  goToPage
} = usePatientSearch()

const handleSearch = async (concept: string) => {
  await search(concept)
}
</script>
```

### Pattern 2: With Filters

```typescript
const { search, results } = usePatientSearch()

const handleFilteredSearch = async (
  concept: string,
  filters: SearchFilters
) => {
  await search(concept, filters)
  // Results are updated and only include matching filters
}
```

### Pattern 3: Watch for Changes

```typescript
const { results, lastSearchConcept } = usePatientSearch()

// React to search results
watch(results, (newResults) => {
  console.log(`Got ${newResults.length} results`)
})

// Track what was searched
watch(lastSearchConcept, (concept) => {
  analytics.track('search_performed', { concept })
})
```

### Pattern 4: Error Handling

```typescript
const { search, error, clearError } = usePatientSearch()

const handleSearch = async (concept: string) => {
  try {
    await search(concept)
  } catch (err) {
    console.error('Search failed:', err)
    // Error is automatically set in composable.error
  }

  // Handle error UI
  if (error.value) {
    setTimeout(() => {
      clearError()
    }, 5000)
  }
}
```

### Pattern 5: Pagination Navigation

```typescript
import { computed } from 'vue'
import { usePatientSearch } from '@/composables/usePatientSearch'

const {
  page,
  totalPages,
  nextPage,
  previousPage,
  search
} = usePatientSearch()

const currentConcept = ref('diabetes')

const canGoNext = computed(() => page.value < totalPages.value)
const canGoPrev = computed(() => page.value > 1)

const handleNext = async () => {
  if (canGoNext.value) {
    await nextPage(currentConcept.value)
  }
}

const handlePrev = async () => {
  if (canGoPrev.value) {
    await previousPage(currentConcept.value)
  }
}
```

## Performance Tips

### 1. Avoid Redundant Searches

```typescript
// BAD: Searches on every re-render
const { search } = usePatientSearch()
search('diabetes')  // Every render!

// GOOD: Only search when button clicked
const handleSearch = async () => {
  await search('diabetes')
}
```

### 2. Cache Results

```typescript
const searchCache = new Map()

const searchWithCache = async (concept: string) => {
  if (searchCache.has(concept)) {
    results.value = searchCache.get(concept)
    return
  }

  await search(concept)
  searchCache.set(concept, results.value)
}
```

### 3. Debounce Search

```typescript
import { useDebounceFn } from '@vueuse/core'

const debouncedSearch = useDebounceFn(async (concept: string) => {
  await search(concept)
}, 300)

watch(searchInput, debouncedSearch)
```

### 4. Clean Up on Unmount

```typescript
import { onUnmounted } from 'vue'

const { clearResults } = usePatientSearch()

onUnmounted(() => {
  clearResults()
})
```

## Error Handling

### Common Errors

```typescript
const { error, search } = usePatientSearch()

try {
  await search('')
} catch (err) {
  // error.value = 'Please enter a concept to search'
}

try {
  // Network error
  await search('diabetes')
} catch (err) {
  // error.value = 'Search failed. Please try again.'
}
```

### Error States

The composable handles:
- Empty query validation
- Network failures
- API errors (400, 401, 403, 404, 500)
- Timeout errors
- Malformed responses

All errors are caught and stored in `error.value` for display to the user.

## Compliance & Security

### HIPAA Compliance

- ✅ All searches logged to audit trail
- ✅ Only authorized users can search
- ✅ PHI returned by API is encrypted in transit
- ✅ Search queries are never logged with identifying details

### GDPR Compliance

- ✅ User can delete their search history
- ✅ Search data is retained for max 30 days
- ✅ Search preferences respect user consent

## Related Documentation

- [SearchBar Component](../components/SearchBar.md)
- [SearchResults Component](../components/SearchResults.md)
- [SearchResultItem Component](../components/SearchResultItem.md)
- [Security Guidelines](../security.md)
- [Usage Examples](../examples.md)
- [Troubleshooting Guide](../troubleshooting.md)

## Testing

### Unit Test Example

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { usePatientSearch } from '@/composables/usePatientSearch'

describe('usePatientSearch', () => {
  let search, results, isLoading, error

  beforeEach(() => {
    const composable = usePatientSearch()
    search = composable.search
    results = composable.results
    isLoading = composable.isLoading
    error = composable.error
  })

  it('initializes with empty results', () => {
    expect(results.value).toEqual([])
    expect(isLoading.value).toBe(false)
  })

  it('sets loading state during search', async () => {
    const searchPromise = search('diabetes')
    expect(isLoading.value).toBe(true)
    await searchPromise
    expect(isLoading.value).toBe(false)
  })

  it('updates results on successful search', async () => {
    await search('diabetes')
    expect(results.value.length).toBeGreaterThan(0)
  })

  it('sets error on failed search', async () => {
    await search('')  // Empty query fails
    expect(error.value).not.toBeNull()
  })
})
```

---

**Last Updated**: 2025-11-21
**Composable Version**: 1.0.0
