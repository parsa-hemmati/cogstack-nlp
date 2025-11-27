# Search Module Troubleshooting Guide

Common issues and solutions for the search module.

---

## Issue 1: Search Results Not Displaying

### Symptoms

- Search completes but results list is empty
- No error message shown
- No loading spinner
- Components appear to be mounted

### Possible Causes

1. **Results array not reactive**
   - Using plain array instead of `ref`
   - Results not properly assigned from composable

2. **API endpoint not found**
   - Search API endpoint `/api/v1/patients/search` not responding
   - Wrong API URL configured

3. **Empty results from API**
   - Search query doesn't match any documents
   - Results count is 0 but no error shown

4. **Component prop issues**
   - Props not properly passed to `SearchResults`
   - Results binding not working

### Solutions

**Solution 1: Check reactivity**

```typescript
// ❌ Wrong
const results = []  // Plain array, not reactive

// ✅ Correct
const { results } = usePatientSearch()  // Returns ref
// OR
const results = ref([])
```

**Solution 2: Verify API endpoint**

```bash
# Test API directly
curl -X POST http://localhost:8000/api/v1/patients/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "concept": "diabetes",
    "pagination": {"page": 1, "pageSize": 20}
  }'

# Check response - should have structure:
# {
#   "results": [...],
#   "pagination": {...},
#   "performance": {...}
# }
```

**Solution 3: Handle empty results gracefully**

```vue
<!-- Add empty state message -->
<v-alert
  v-if="!isLoading && results.length === 0 && searchQuery"
  type="info"
>
  No results found for "{{ searchQuery }}". Try a different search term.
</v-alert>
```

**Solution 4: Debug component binding**

```typescript
// Add console logging
watch(results, (newResults) => {
  console.log('Results updated:', newResults)
}, { deep: true })

// In template, add:
{{ results }}  <!-- Show raw data in template -->
```

**Debugging Checklist**

- [ ] Open Vue DevTools, inspect SearchResults component props
- [ ] Check Network tab - see request/response to `/api/v1/patients/search`
- [ ] Verify API response has `results` array
- [ ] Check browser console for JavaScript errors
- [ ] Verify authentication token is valid

---

## Issue 2: Highlights Not Showing

### Symptoms

- Search results display but text highlights (`<mark>` tags) not visible
- Text appears plain without yellow background
- Snippet shows full text without emphasis

### Possible Causes

1. **Highlights not in API response**
   - API not returning highlights
   - Query doesn't have matching search terms

2. **HTML not rendering**
   - Using `{{ }}` text binding instead of `v-html`
   - Highlights are present but not rendered

3. **XSS sanitization removing highlights**
   - `sanitizeHtml` stripping valid `<mark>` tags

4. **CSS not applied**
   - Highlight styling missing or overridden

### Solutions

**Solution 1: Check API response**

```bash
# Test with verbose logging
curl -X POST http://localhost:8000/api/v1/patients/search \
  -d '{"concept": "diabetes"}' \
  | jq '.results[0].highlights'

# Should see:
# {
#   "title": ["Patient with <mark>diabetes</mark> mellitus"],
#   "content": ["Type 2 <mark>diabetes</mark> diagnosed in 2020"]
# }
```

**Solution 2: Use v-html with sanitization**

```vue
<!-- ❌ Wrong: Text binding doesn't render HTML -->
<div>{{ result.highlights.title[0] }}</div>
<!-- Output: Patient <mark>diabetes</mark> mellitus -->

<!-- ✅ Correct: v-html renders HTML -->
<div v-html="sanitizeHtml(result.highlights.title[0])" />
<!-- Output: Patient <mark>diabetes</mark> mellitus (with yellow highlight) -->
```

**Solution 3: Verify sanitization preserves marks**

```typescript
import { sanitizeHtml } from '@/utils/sanitize'

const input = 'Patient <mark>diabetes</mark> mellitus'
const output = sanitizeHtml(input)
console.log(output)  // Should output: 'Patient <mark>diabetes</mark> mellitus'

// If different, sanitizeHtml is stripping marks
```

**Solution 4: Add highlight CSS**

```vue
<style scoped>
:deep(mark) {
  background-color: yellow;
  font-weight: 600;
  padding: 0 2px;
}
</style>
```

**Debugging Checklist**

- [ ] Check Network tab for `/api/v1/patients/search` response
- [ ] Verify `highlights` field exists in response
- [ ] Check if using `v-html` not `{{ }}`
- [ ] Test `sanitizeHtml()` in console
- [ ] Verify CSS styles are applied (inspect element)

---

## Issue 3: XSS Warnings in Console

### Symptoms

- Vue warns about "v-html" usage
- Console shows security-related messages
- Page works but shows warnings

### Possible Causes

1. **Not using sanitizeHtml**
   - Rendering unsanitized HTML directly
   - Vue warning about potentially unsafe v-html

2. **Browser extension warning**
   - Security-focused browser extension warning
   - Not an actual app issue

### Solutions

**Solution 1: Always sanitize before v-html**

```vue
<!-- ❌ Wrong: Vue warns about this -->
<div v-html="result.highlights.title[0]" />

<!-- ✅ Correct: Sanitize first -->
<div v-html="sanitizeHtml(result.highlights.title[0])" />
```

**Solution 2: Test sanitization**

```typescript
import { sanitizeHtml } from '@/utils/sanitize'

// This should NOT produce warnings
const safe = sanitizeHtml(unsafeHtml)
console.log(safe)  // Should be clean
```

**Solution 3: Suppress Vue warnings (if legitimate)**

Only if you've verified the HTML is safe:

```typescript
// In component
const props = withDefaults(defineProps<Props>(), {
  // Tell Vue this content is sanitized
})

// OR disable for specific v-html
// (Not recommended)
```

**Debugging Checklist**

- [ ] Search codebase for all `v-html` usage
- [ ] Verify each `v-html` uses `sanitizeHtml()`
- [ ] Test suspicious inputs in console
- [ ] Check for browser extension warnings (disable temporarily)

---

## Issue 4: Slow Search Performance

### Symptoms

- Search API takes >1 second to respond
- Page feels sluggish during search
- Results take long time to render

### Possible Causes

1. **Large Elasticsearch index**
   - Index not properly tuned
   - Missing indexes on fields

2. **Network latency**
   - API server far from client
   - Network connection slow

3. **No pagination**
   - Fetching all results instead of paginating
   - Rendering hundreds of results

4. **Client-side performance**
   - Too many components rendering
   - Virtual scrolling not implemented

### Solutions

**Solution 1: Optimize Elasticsearch**

```bash
# Check index health
curl http://localhost:9200/_cat/indices?v

# Check query performance
curl -X GET "localhost:9200/documents/_explain" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": { "match": { "concept": "diabetes" } }
  }'

# Add indexes if needed
curl -X PUT "localhost:9200/documents/_mapping" \
  -H 'Content-Type: application/json' \
  -d '{
    "properties": {
      "concept": { "type": "keyword" },
      "date": { "type": "date" }
    }
  }'
```

**Solution 2: Use pagination**

```vue
<!-- Always limit results -->
<SearchResults
  :results="results"
  :page="page"
  :page-size="20"  <!-- Don't fetch all -->
/>
```

**Solution 3: Implement debouncing**

```typescript
import { useDebounceFn } from '@vueuse/core'

const debouncedSearch = useDebounceFn(async (query) => {
  await search(query)
}, 500)  // Wait 500ms before searching

watch(searchQuery, debouncedSearch)
```

**Solution 4: Monitor performance**

```typescript
const { queryTimeMs } = usePatientSearch()

watch(queryTimeMs, (time) => {
  if (time > 500) {
    console.warn(`Slow search: ${time}ms`)
  }
})
```

**Benchmarks to Target**

| Operation | Target | Status |
|-----------|--------|--------|
| API response | <500ms | ✅ |
| Component render | <100ms | ✅ |
| Highlighting | <50ms | ✅ |

**Debugging Checklist**

- [ ] Check Network tab: what's the total request time?
- [ ] Check DevTools Performance: where is time spent?
- [ ] Count results returned: >100?
- [ ] Check Elasticsearch logs for slow queries

---

## Issue 5: Pagination Not Working

### Symptoms

- Pagination controls visible but clicking does nothing
- Page number doesn't change
- Results don't update when changing pages

### Possible Causes

1. **Event handlers not connected**
   - `@update:page` event not bound
   - Handler function not defined

2. **State not updating**
   - Page ref not changing
   - Composable methods not called

3. **API not supporting pagination**
   - `page` and `pageSize` parameters not sent
   - API endpoint doesn't support pagination

### Solutions

**Solution 1: Verify event binding**

```vue
<!-- ✅ Correct -->
<SearchResults
  :page="page"
  :page-size="pageSize"
  @update:page="handlePageChange"  <!-- Connected -->
/>

<!-- ❌ Wrong - event not bound -->
<SearchResults
  :page="page"
  :page-size="pageSize"
/>
```

**Solution 2: Implement handler**

```typescript
const handlePageChange = async (newPage: number) => {
  console.log('Changing to page:', newPage)
  // Actually fetch new page
  await search(currentQuery.value, undefined, newPage, pageSize.value)
}
```

**Solution 3: Check API supports pagination**

```bash
# Test API with pagination
curl -X POST http://localhost:8000/api/v1/patients/search \
  -d '{
    "concept": "diabetes",
    "pagination": {
      "page": 2,
      "pageSize": 20
    }
  }' | jq '.pagination'

# Should return:
# {
#   "page": 2,
#   "pageSize": 20,
#   "totalResults": 150
# }
```

**Solution 4: Debug pagination state**

```typescript
watch(page, (newPage) => {
  console.log('Page changed to:', newPage)
})

watch(results, (newResults) => {
  console.log('Results updated, count:', newResults.length)
})
```

**Debugging Checklist**

- [ ] Check console for `@update:page` event
- [ ] Verify `handlePageChange` function exists
- [ ] Check Network tab for pagination parameters
- [ ] Verify API returns correct page in response

---

## Issue 6: TypeScript Errors

### Symptoms

- TypeScript compiler errors about types
- `result is not assignable to type`
- `Property 'X' does not exist`

### Possible Causes

1. **Missing or incorrect types**
   - Composable types not exported
   - Component props missing type definitions

2. **Import path errors**
   - Importing from wrong path
   - Module not found

3. **Version mismatches**
   - Vue version incompatible
   - Composable API changed

### Solutions

**Solution 1: Check imports**

```typescript
// ✅ Correct
import { usePatientSearch } from '@/composables/usePatientSearch'
import SearchBar from '@/components/search/SearchBar.vue'
import type { SearchResult } from '@/api/patientSearch'

// ❌ Wrong
import { usePatientSearch } from 'composables/usePatientSearch'  // Missing @
import SearchBar from './components/SearchBar'  // Wrong path
```

**Solution 2: Add type annotations**

```typescript
// ✅ Correct
const results: Ref<PatientSearchResult[]> = ref([])
const { search }: UsePatientSearchReturn = usePatientSearch()

// ❌ Wrong
const results = ref([])
const { search } = usePatientSearch()
```

**Solution 3: Import type correctly**

```typescript
// Import both value and type
import { usePatientSearch } from '@/composables/usePatientSearch'
import type { PatientSearchResult, SearchFilters } from '@/api/patientSearch'

// Use in component
const { results }: { results: Ref<PatientSearchResult[]> } = usePatientSearch()
```

**Debugging Checklist**

- [ ] Check import paths (use @/ alias)
- [ ] Verify types are exported from source
- [ ] Run `npm run type-check` or `tsc --noEmit`
- [ ] Check tsconfig.json paths

---

## Issue 7: Accessibility Issues

### Symptoms

- Screen readers not announcing results
- Can't navigate with keyboard
- Focus indicators not visible

### Possible Causes

1. **Missing ARIA labels**
   - Interactive elements without aria-label
   - No role attributes

2. **Keyboard navigation not implemented**
   - Tab order incorrect
   - Enter/Space not handled

3. **Color contrast too low**
   - Text hard to read
   - Highlight colors not contrasting

### Solutions

**Solution 1: Add ARIA labels**

```vue
<!-- ✅ Good accessibility -->
<div role="region" aria-label="Search results">
  <SearchResults />
</div>

<v-btn aria-label="Clear search">
  <v-icon>mdi-close</v-icon>
</v-btn>
```

**Solution 2: Test keyboard navigation**

```
1. Click in browser
2. Press Tab repeatedly
3. All interactive elements should be reachable
4. Press Enter/Space to activate
5. Focus should be visible at all times
```

**Solution 3: Check color contrast**

```bash
# Use online tool: https://webaim.org/resources/contrastchecker/
# Or install locally:
npm install -D @axe-core/cli
axe check https://yoursite.com
```

**Solution 4: Test with screen reader**

```bash
# macOS: VoiceOver (Cmd+F5)
# Windows: NVDA (free) or JAWS (commercial)
# Test these:
# - Can search query be entered?
# - Are results announced?
# - Can pages be navigated?
```

**Debugging Checklist**

- [ ] Tab through entire page - all controls reachable?
- [ ] Screen reader reads all content?
- [ ] Color contrast meets WCAG AA (4.5:1 for text)?
- [ ] Focus indicators visible?

---

## Issue 8: Search History Not Persisting

### Symptoms

- Search history clears after page reload
- Recent searches not appearing
- localStorage not working

### Possible Causes

1. **localStorage not available**
   - Private browsing mode
   - Browser doesn't support localStorage

2. **Incorrect key used**
   - Different key in save vs load
   - Key accidentally cleared

3. **Data size too large**
   - Exceeded localStorage 5MB limit
   - Can't serialize to JSON

### Solutions

**Solution 1: Check localStorage availability**

```typescript
const isLocalStorageAvailable = () => {
  try {
    const test = '__test__'
    localStorage.setItem(test, test)
    localStorage.removeItem(test)
    return true
  } catch {
    return false
  }
}

if (!isLocalStorageAvailable()) {
  console.warn('localStorage not available (private browsing?)')
}
```

**Solution 2: Use consistent key**

```typescript
const HISTORY_KEY = 'search_history'  // Define once, use everywhere

// Save
localStorage.setItem(HISTORY_KEY, JSON.stringify(history))

// Load
const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
```

**Solution 3: Handle quota exceeded**

```typescript
try {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
} catch (e) {
  if (e.name === 'QuotaExceededError') {
    console.warn('localStorage quota exceeded')
    // Clear old entries
    localStorage.removeItem(HISTORY_KEY)
  }
}
```

**Debugging Checklist**

- [ ] Open DevTools > Application > Local Storage
- [ ] Check key exists and value is valid JSON
- [ ] Try in normal browsing (not private)
- [ ] Check Data size (DevTools shows this)

---

## General Debugging Tips

### Enable Debug Logging

```typescript
// In composable or component
const debug = (message: string, data?: any) => {
  if (process.env.NODE_ENV === 'development') {
    console.log(`[Search] ${message}`, data)
  }
}

debug('Search started', { query, filters })
```

### Use Vue DevTools

1. Install [Vue DevTools browser extension](https://devtools.vuejs.org/)
2. Inspect component state
3. Watch reactive changes in real-time
4. Profile component performance

### Check Browser Console

```javascript
// In browser console:

// Check composable state
usePatientSearch()  // See returned object

// Test sanitization
sanitizeHtml('<script>alert("XSS")</script>')  // See output

// Check localStorage
localStorage.getItem('search_history')  // View history
```

### Network Debugging

```
1. Open DevTools > Network tab
2. Perform search
3. Look for POST /api/v1/patients/search
4. Check:
   - Request headers (Authorization, Content-Type)
   - Request body (concept, filters)
   - Response status (200, 400, 401, 500?)
   - Response body (results structure)
   - Timing (how long did it take?)
```

### Performance Profiling

```
1. Open DevTools > Performance tab
2. Click Record
3. Perform search
4. Click Stop
5. Look for:
   - Scripting time (JavaScript execution)
   - Rendering time (component render)
   - Network requests
```

---

## Getting Help

If none of these solutions work:

1. **Check the examples**: See [examples.md](./examples.md)
2. **Read the API docs**: See [composables/useSearch.md](./composables/useSearch.md)
3. **Review security**: See [security.md](./security.md)
4. **Check component docs**: See [components/](./components/)

---

**Last Updated**: 2025-11-21
