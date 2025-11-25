# SearchBar Component

## Description

The `SearchBar` component provides a reusable search input field with debouncing, loading states, error handling, and accessibility support. It emits search events when the user submits a query and supports placeholder text customization.

The component is designed to be simple and focused on input handling, delegating actual search logic to parent components or the `usePatientSearch` composable.

## Props

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `modelValue` | `string` | `''` | No | Current search query (v-model binding) |
| `placeholder` | `string` | `'Search documents...'` | No | Placeholder text in input |
| `loading` | `boolean` | `false` | No | Whether search is in progress |
| `error` | `string` | `''` | No | Error message to display |
| `debounce` | `number` | `300` | No | Debounce delay in milliseconds |
| `disabled` | `boolean` | `false` | No | Disable input while searching |

## Events

| Name | Payload | Description |
|------|---------|-------------|
| `update:modelValue` | `string` | Emitted when user types (with debounce) |
| `search` | `string` | Emitted when user presses Enter or submits |
| `clear` | None | Emitted when user clears the input |
| `error` | `string` | Emitted when search fails (error prop provided) |
| `focus` | None | Emitted when input receives focus |
| `blur` | None | Emitted when input loses focus |

## Slots

| Name | Props | Description |
|------|-------|-------------|
| `prepend-icon` | None | Custom icon before input (default: search icon) |
| `append-icon` | None | Custom icon after input (default: clear icon) |
| `hint` | None | Hint text below input (default: empty) |

## TypeScript Interfaces

```typescript
interface Props {
  modelValue?: string        // Current search query
  placeholder?: string       // Placeholder text
  loading?: boolean          // Loading state
  error?: string            // Error message
  debounce?: number         // Debounce delay (ms)
  disabled?: boolean        // Disabled state
}

interface Emits {
  'update:modelValue': [value: string]
  'search': [value: string]
  'clear': []
  'error': [message: string]
  'focus': []
  'blur': []
}
```

## Usage Examples

### Basic Search

```vue
<template>
  <SearchBar
    v-model="searchQuery"
    @search="handleSearch"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SearchBar from '@/components/search/SearchBar.vue'

const searchQuery = ref('')

const handleSearch = async (query: string) => {
  console.log('Searching for:', query)
  // Perform search
}
</script>
```

### With Loading State

```vue
<template>
  <SearchBar
    v-model="searchQuery"
    :loading="isLoading"
    :error="searchError"
    @search="handleSearch"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SearchBar from '@/components/search/SearchBar.vue'

const searchQuery = ref('')
const isLoading = ref(false)
const searchError = ref('')

const handleSearch = async (query: string) => {
  if (!query.trim()) {
    searchError.value = 'Please enter a search term'
    return
  }

  isLoading.value = true
  searchError.value = ''

  try {
    // Perform search
    console.log('Searching:', query)
  } catch (err) {
    searchError.value = 'Search failed. Please try again.'
  } finally {
    isLoading.value = false
  }
}
</script>
```

### With Debounce

```vue
<template>
  <SearchBar
    v-model="searchQuery"
    :debounce="500"
    @update:modelValue="handleQueryChange"
    @search="handleSearch"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SearchBar from '@/components/search/SearchBar.vue'

const searchQuery = ref('')

const handleQueryChange = (query: string) => {
  // Fires after 500ms of inactivity
  console.log('Query changed:', query)
}

const handleSearch = (query: string) => {
  // Fires when user presses Enter
  console.log('Search submitted:', query)
}
</script>
```

### With usePatientSearch Composable

```vue
<template>
  <div>
    <SearchBar
      v-model="currentQuery"
      :loading="isLoading"
      :error="error"
      @search="handleSearch"
      @clear="clearSearch"
    />
    <SearchResults
      :results="results"
      :loading="isLoading"
      :error="error"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SearchBar from '@/components/search/SearchBar.vue'
import SearchResults from '@/components/search/SearchResults.vue'
import { usePatientSearch } from '@/composables/usePatientSearch'

const currentQuery = ref('')
const { results, isLoading, error, search, clearResults } = usePatientSearch()

const handleSearch = async (query: string) => {
  currentQuery.value = query
  await search(query)
}

const clearSearch = () => {
  currentQuery.value = ''
  clearResults()
}
</script>
```

### Advanced: Custom Placeholder and Icons

```vue
<template>
  <SearchBar
    v-model="searchQuery"
    placeholder="Search by patient name, condition, or date..."
    @search="handleSearch"
  >
    <template #prepend-icon>
      <v-icon color="primary">mdi-magnify</v-icon>
    </template>
    <template #hint>
      Try searching for "diabetes" or "heart failure"
    </template>
  </SearchBar>
</template>

<script setup lang="ts">
import SearchBar from '@/components/search/SearchBar.vue'

const searchQuery = ref('')

const handleSearch = (query: string) => {
  console.log('Advanced search:', query)
}
</script>
```

## Component Structure

```
SearchBar (v-container)
├── Input Row (v-row)
│   └── Input Column (v-col)
│       └── v-text-field
│           ├── Prepend icon (search icon)
│           ├── Input field
│           ├── Append icon (clear button)
│           └── Loading indicator (circular progress)
└── Error Row (v-row, if error)
    └── v-col
        └── v-alert (type="error")
            └── Error message
```

## Visual States

### Default State

```
┌─────────────────────────────────┐
│ 🔍 Search documents...          │
└─────────────────────────────────┘
```

### Focused State

```
┌─────────────────────────────────┐
│ 🔍 Search documents...          │ (outline visible)
└─────────────────────────────────┘
```

### With Input

```
┌─────────────────────────────────┐
│ 🔍 diabetes                     ✕│
└─────────────────────────────────┘
```

### Loading State

```
┌──────────────────────────────────┐
│ 🔍 diabetes            ⟲ (spinning)│
└──────────────────────────────────┘
```

### With Error

```
┌─────────────────────────────────┐
│ 🔍 Search documents...          │
└─────────────────────────────────┘
⚠ Search failed. Please try again.
```

## Input Handling

### Text Input

```typescript
@update:modelValue="handleQueryChange"
// Fires when user types (debounced)
// Payload: updated query string
```

### Submit (Enter Key)

```typescript
@search="handleSearch"
// Fires when user presses Enter
// Fires when user clicks search/submit button
// Payload: current query value
```

### Clear Button

```typescript
@clear="handleClear"
// Fires when user clicks clear (X) icon
// Automatically clears input
```

## Debouncing Strategy

The component includes built-in debouncing to prevent excessive API calls:

- **Default delay**: 300ms
- **Customizable**: Pass `debounce` prop
- **Implementation**: `useDebounceFn` from VueUse

```typescript
// Without debounce - fires on every keystroke
// "d" → "di" → "dia" → "diab" → "diabe" → "diabet" → "diabete" → "diabetes"
// 8 API calls!

// With debounce=300ms - fires after user stops typing
// User types "diabetes"... pauses... 1 API call!
```

### Debounce Examples

```vue
<!-- Fast response (100ms) -->
<SearchBar :debounce="100" />

<!-- Default (300ms) -->
<SearchBar />

<!-- Slower response (1s) -->
<SearchBar :debounce="1000" />
```

## Styling

### CSS Classes

```vue
<style scoped>
.search-bar-container {
  padding: 16px 0;
}

.search-input {
  border-radius: 4px;
}

.search-input:focus {
  box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1);
}

.search-error {
  color: #d32f2f;
  margin-top: 8px;
}
</style>
```

### Vuetify Classes Used

- `v-container` - Responsive container
- `v-row` / `v-col` - Grid layout
- `v-text-field` - Text input
- `v-icon` - Icons (search, clear)
- `v-circular-progress` - Loading indicator
- `v-alert` - Error message

### Customization

Override styles with CSS:

```vue
<style scoped>
:deep(.v-text-field) {
  font-size: 16px;
  background-color: #f5f5f5;
}

:deep(.v-text-field__input) {
  color: #333;
  padding: 12px 16px;
}
</style>
```

## Accessibility

### WCAG 2.1 Compliance

- ✅ **Label association**: Input has implicit label from placeholder
- ✅ **Keyboard navigation**:
  - Tab to focus input
  - Type to enter query
  - Enter to submit search
  - Shift+Tab to focus clear button
- ✅ **Focus indication**: Clear focus outline visible
- ✅ **Color contrast**: Text meets WCAG AA standards
- ✅ **Screen reader support**: Loading and error states announced

### Accessibility Features

1. **Semantic HTML**:
   ```html
   <v-text-field
     type="search"
     aria-label="Search documents"
     role="searchbox"
   />
   ```

2. **Clear Button Accessible**:
   ```html
   <v-icon
     aria-label="Clear search"
     role="button"
   >
     mdi-close
   </v-icon>
   ```

3. **Error Announcement**:
   ```html
   <v-alert
     role="alert"
     aria-live="polite"
   >
     {{ error }}
   </v-alert>
   ```

### Tips for Better Accessibility

1. **Provide aria-label**:
   ```vue
   <SearchBar aria-label="Search patients and documents" />
   ```

2. **Announce results when ready**:
   ```typescript
   watch(isLoading, (loading) => {
     if (!loading) {
       // Announce to screen readers
       console.log(`${results.length} results found`)
     }
   })
   ```

3. **Clear button should be easy to find**:
   ```html
   <!-- Good: Clear button visible when text entered -->
   <v-icon v-if="searchQuery">mdi-close</v-icon>
   ```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Tab` | Focus input |
| `Shift+Tab` | Blur input / Focus previous |
| `Enter` | Submit search |
| `Ctrl+A` | Select all text |
| `Ctrl+X` | Cut text |
| `Ctrl+C` | Copy text |
| `Ctrl+V` | Paste text |

## Error Handling

### Input Validation

```typescript
const handleSearch = (query: string) => {
  // Check if empty
  if (!query || query.trim() === '') {
    setError('Please enter a search term')
    return
  }

  // Check length
  if (query.length > 200) {
    setError('Search query too long (max 200 characters)')
    return
  }

  // Looks good, search
  search(query)
}
```

### API Error Handling

```typescript
try {
  await search(query)
} catch (err: any) {
  if (err.status === 408) {
    setError('Request timed out. Check your connection.')
  } else if (err.status === 429) {
    setError('Too many requests. Please wait a moment.')
  } else if (err.status === 500) {
    setError('Server error. Please try again later.')
  } else {
    setError(err.message || 'Search failed. Please try again.')
  }
}
```

## Integration with usePatientSearch

The SearchBar pairs perfectly with the `usePatientSearch` composable:

```typescript
const { search, isLoading, error, clearResults } = usePatientSearch()

const handleSearch = async (query: string) => {
  await search(query)
}

const handleClear = () => {
  clearResults()
}
```

## Performance

### Optimization Strategies

1. **Debounce to reduce API calls**:
   ```vue
   <SearchBar :debounce="500" />
   <!-- Prevents search on every keystroke -->
   ```

2. **Memoize search results**:
   ```typescript
   const searchCache = new Map()

   const handleSearch = (query: string) => {
     if (searchCache.has(query)) {
       results.value = searchCache.get(query)
       return
     }
     // Fetch and cache
   }
   ```

3. **Lazy load suggestions** (future):
   ```vue
   <v-autocomplete
     v-model="searchQuery"
     :items="suggestions"
     @update:search-input="loadSuggestions"
   />
   ```

### Benchmarks

| Operation | Target | Notes |
|-----------|--------|-------|
| Type a character | <5ms | No debounce delay |
| Debounce delay | 300ms | Configurable |
| Clear input | <2ms | Instant feedback |
| Submit search | <500ms | Includes API call |
| Error display | <50ms | Update error prop |

## Testing

### Unit Tests Example

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SearchBar from '@/components/search/SearchBar.vue'

describe('SearchBar.vue', () => {
  it('updates modelValue on input', async () => {
    const wrapper = mount(SearchBar)
    const input = wrapper.find('input')
    await input.setValue('diabetes')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })

  it('emits search on Enter key', async () => {
    const wrapper = mount(SearchBar)
    const input = wrapper.find('input')
    await input.setValue('diabetes')
    await input.trigger('keydown.enter')
    expect(wrapper.emitted('search')).toBeTruthy()
    expect(wrapper.emitted('search')[0]).toEqual(['diabetes'])
  })

  it('displays error message', async () => {
    const wrapper = mount(SearchBar, {
      props: { error: 'Search failed' }
    })
    expect(wrapper.find('.v-alert').text()).toContain('Search failed')
  })

  it('shows loading indicator', async () => {
    const wrapper = mount(SearchBar, {
      props: { loading: true }
    })
    expect(wrapper.find('.v-progress-circular').exists()).toBe(true)
  })

  it('clears input and emits clear event', async () => {
    const wrapper = mount(SearchBar, {
      props: { modelValue: 'diabetes' }
    })
    await wrapper.find('.mdi-close').trigger('click')
    expect(wrapper.emitted('clear')).toBeTruthy()
  })
})
```

## Best Practices

### ✅ DO

- Use debouncing to reduce API calls
- Show loading state during search
- Display clear error messages
- Validate input before searching
- Clear previous results on new search
- Announce results to screen readers
- Use v-model for two-way binding

### ❌ DON'T

- Search on every keystroke (without debounce)
- Show generic "An error occurred" messages
- Leave input disabled during search
- Ignore validation errors silently
- Autocomplete without user consent
- Make clear button hard to find

## Migration Guide

If updating from previous versions:

### v0.x to v1.0

- `search` event renamed from `submit`
- `loading` prop added (was state-only before)
- Debounce now built-in (was external)
- Error display now integrated

```vue
<!-- Old (v0.x) -->
<SearchBar @submit="handleSearch" />

<!-- New (v1.0) -->
<SearchBar @search="handleSearch" />
```

---

**Last Updated**: 2025-11-21
**Component Version**: 1.0.0
