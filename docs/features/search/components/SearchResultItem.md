# SearchResultItem Component

## Description

The `SearchResultItem` component displays a single search result as a card with the document title, metadata (type, author, date), content excerpt, relevance score, and action buttons. It includes XSS-safe highlighting of search terms using the `sanitizeHtml` utility.

## Props

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `result` | `SearchResult` | - | Yes | Search result object to display |
| `index` | `number` | - | Yes | Index of result in list (for tracking/analytics) |
| `hoverable` | `boolean` | `true` | No | Enable hover effects and elevation change |

## Events

| Name | Payload | Description |
|------|---------|-------------|
| `click` | None | Emitted when result card is clicked |

## Slots

| Name | Props | Description |
|------|-------|-------------|
| (default) | None | Not used - content is rendered from props |

## TypeScript Interfaces

```typescript
interface SearchResult {
  id: string                              // Unique result ID
  title: string                           // Document title
  content: string                         // Document content/excerpt
  document_type: string                   // Type: 'note', 'lab', 'imaging', etc.
  author: string                          // Document author/creator
  date: string                            // Document date (ISO 8601)
  score: number                           // Relevance score (0-100)
  highlights?: {
    title?: string[]                      // HTML with <mark> tags (sanitized)
    content?: string[]                    // HTML with <mark> tags (sanitized)
  }
}

interface Props {
  result: SearchResult
  index: number
  hoverable?: boolean
}
```

## Usage Examples

### Basic Usage (Standalone)

```vue
<template>
  <SearchResultItem
    :result="singleResult"
    :index="0"
    @click="handleClick"
  />
</template>

<script setup lang="ts">
import SearchResultItem from '@/components/search/SearchResultItem.vue'

const singleResult = {
  id: 'doc-123',
  title: 'Patient Discharge Summary',
  content: 'Patient discharged with stable condition...',
  document_type: 'note',
  author: 'Dr. Smith',
  date: '2024-01-15',
  score: 95.5,
  highlights: {
    title: ['Patient <mark>discharge</mark> summary'],
    content: ['Patient <mark>discharged</mark> with stable condition']
  }
}

const handleClick = () => {
  console.log('Result clicked')
}
</script>
```

### In a List (Typical Usage)

```vue
<template>
  <div v-for="(result, index) in results" :key="result.id">
    <SearchResultItem
      :result="result"
      :index="index"
      :hoverable="true"
      @click="handleResultClick(result)"
    />
  </div>
</template>

<script setup lang="ts">
import SearchResultItem from '@/components/search/SearchResultItem.vue'

const results = ref([
  { id: '1', title: 'Doc 1', /* ... */ },
  { id: '2', title: 'Doc 2', /* ... */ },
  // ...
])

const handleResultClick = (result) => {
  console.log('Selected result:', result.id)
  // Navigate to document detail or open modal
}
</script>
```

### With Document Modal

```vue
<template>
  <SearchResultItem
    :result="result"
    :index="index"
    @click="openDocumentModal(result)"
  />

  <!-- Modal for full document -->
  <DocumentModal
    v-if="selectedDocument"
    :document="selectedDocument"
    @close="selectedDocument = null"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SearchResultItem from '@/components/search/SearchResultItem.vue'
import DocumentModal from '@/components/DocumentModal.vue'

const selectedDocument = ref(null)

const openDocumentModal = (result) => {
  selectedDocument.value = result
}
</script>
```

## Component Structure

```
SearchResultItem (v-card)
├── v-card-title
│   ├── Title with highlights (XSS-safe)
│   ├── Metadata
│   │   ├── Document type chip
│   │   ├── Author with icon
│   │   └── Date with icon
│   └── Relevance score chip (with tooltip)
├── v-card-text
│   ├── Content excerpt with highlights
│   └── Truncation if too long
└── v-card-actions
    ├── View Document button
    ├── Spacer
    ├── Bookmark button
    └── Share button
```

## Display Details

### Title Display

The component intelligently displays the title with highlights if available:

```typescript
// With highlights (Elasticsearch returned matched terms)
if (result.highlights?.title) {
  // Display: Patient <mark>discharged</mark> on 2024-01-15
  v-html="sanitizeHtml(result.highlights.title[0])"
} else {
  // Display: Patient Discharged on 2024-01-15
  {{ result.title }}
}
```

### Metadata Display

```
[document_type_chip]  [icon] author_name  [icon] formatted_date
```

**Document Type**: Color-coded chip showing document category:
- `note` - Clinical note
- `lab` - Lab result
- `imaging` - Imaging report
- `discharge` - Discharge summary
- etc.

**Author**: Author/creator of the document

**Date**: Formatted as "Jan 15, 2024" (locale: en-GB)

### Relevance Score

- **Color-coded chip**:
  - Green (success): Score ≥ 80 (highly relevant)
  - Orange (warning): Score 60-79 (moderately relevant)
  - Red (error): Score < 60 (low relevance)
- **Tooltip**: "Relevance score (0-100)"
- **Precision**: Shown to 2 decimal places

### Content Excerpt

- **With highlights**: Shows first 250 characters with `<mark>` tags
- **Without highlights**: Shows first 250 characters of plain text
- **Truncation**: Adds "..." if content exceeds max length
- **Line height**: 1.6 for readability

### Highlight Styling

```css
.search-result-excerpt :deep(mark) {
  background-color: yellow;
  font-weight: 600;
  padding: 0 2px;
}
```

**Visual indicators**:
- Yellow background for matches
- Bold text for emphasis
- Small padding for clarity

## Methods

### `formatDate(dateString: string): string`

Formats ISO 8601 date to locale-specific format.

```typescript
// Input: "2024-01-15T14:30:00Z"
// Output: "15 Jan 2024"
formatDate('2024-01-15')  // Returns: "15 Jan 2024"
```

**Locale**: en-GB
**Format**: "numeric month short day"

### `truncateContent(content: string, maxLength: number): string`

Truncates text to maximum length with ellipsis.

```typescript
truncateContent('Very long content...', 250)
// Returns: "Very long content..." if < 250 chars
// Returns: "Very long con..." if > 250 chars
```

### `getScoreColor(score: number): string`

Returns Vuetify color based on relevance score.

```typescript
getScoreColor(95)   // Returns: 'success'
getScoreColor(70)   // Returns: 'warning'
getScoreColor(40)   // Returns: 'error'
```

**Color mapping**:
- `score >= 80` → `'success'` (green)
- `score 60-79` → `'warning'` (orange)
- `score < 60` → `'error'` (red)

## Styling

### CSS Classes

```css
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
```

### Vuetify Components Used

- `v-card` - Container with elevation
- `v-card-title` - Title section
- `v-card-text` - Content section
- `v-card-actions` - Action buttons
- `v-chip` - Type and score badges
- `v-icon` - Metadata icons
- `v-tooltip` - Score explanation
- `v-btn` - Action buttons
- `v-spacer` - Space filler in actions

### Customization

Override styles with CSS modules:

```vue
<style scoped>
.search-result-item {
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.search-result-item:hover {
  border-color: #1976d2;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.1);
}
</style>
```

## XSS Prevention

The component uses the `sanitizeHtml` utility to prevent XSS attacks:

```typescript
// Unsafe HTML from Elasticsearch
const unsafe = 'Patient <script>alert("XSS")</script> discharged'

// Sanitized output (safe for v-html)
const safe = sanitizeHtml(unsafe)
// Result: 'Patient  discharged'

// v-html only allows <mark> tags
v-html="sanitizeHtml(result.highlights.title[0])"
// Only <mark> tags are preserved, all others stripped
```

See [security.md](../security.md) for detailed XSS prevention documentation.

## Accessibility

### WCAG 2.1 Compliance

- ✅ **Semantic HTML**: Using `<h3>` for title (proper heading hierarchy)
- ✅ **Color contrast**: Text meets WCAG AA standards
- ✅ **Icon labels**: Icons have descriptive text next to them
- ✅ **Focus indication**: Card elevates on focus/hover
- ✅ **Keyboard navigation**: Entire card is clickable with Enter key

### Accessibility Features

1. **Semantic Structure**:
   ```html
   <v-card role="article" @click="handleClick" tabindex="0">
     <h3>Title</h3>
     <p>Content</p>
   </v-card>
   ```

2. **Icon with Text**:
   ```html
   <v-icon>mdi-account</v-icon>
   {{ result.author }}  <!-- Text provides label -->
   ```

3. **Tooltip for Score**:
   ```html
   <v-tooltip>
     <template #activator="{ props }">
       <v-chip v-bind="props">
         {{ result.score.toFixed(2) }}
       </v-chip>
     </template>
     Relevance score (0-100)
   </v-tooltip>
   ```

### Tips for Better Accessibility

1. **Add ARIA labels to parent**:
   ```html
   <div role="region" aria-label="Search results">
     <SearchResultItem :result="result" />
   </div>
   ```

2. **Make clickable**:
   ```typescript
   // Component already uses v-card which is interactive
   // Just ensure parent announces it
   ```

3. **Announce highlights**:
   ```typescript
   watch(() => result.highlights, (newHighlights) => {
     // Announce matches to screen readers
   })
   ```

## Performance

### Rendering Optimization

- **No virtual scrolling**: Component is lightweight, renders quickly
- **No watchers**: Minimal reactive state
- **CSS transitions**: Hardware-accelerated (transform, opacity)
- **Lazy loaded images**: (if added in future)

### Benchmarks

| Operation | Target | Notes |
|-----------|--------|-------|
| Mount component | <5ms | Single item in list |
| Re-render | <2ms | No state changes |
| Highlight render | <10ms | Includes sanitization |
| Hover animation | <200ms | CSS transition duration |

### Optimization Tips

1. **Use keys in lists**:
   ```vue
   <SearchResultItem
     v-for="(result, index) in results"
     :key="result.id"  <!-- Use unique ID, not index -->
     :result="result"
     :index="index"
   />
   ```

2. **Memoize expensive computations**:
   ```typescript
   const formattedDate = computed(() => formatDate(result.date))
   ```

3. **Lazy load actions**:
   ```vue
   <!-- Load bookmark/share handlers on demand -->
   <v-btn @click.stop="handleBookmark" />
   ```

## Integration Examples

### With Search Results Component

```vue
<!-- Inside SearchResults.vue -->
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
```

### With Document Modal

```typescript
const selectedDocument = ref(null)

const handleResultClick = (result) => {
  selectedDocument.value = result
  // Open modal to show full document
}
```

### With Analytics

```typescript
const handleResultClick = (result) => {
  // Log click event
  analytics.track('search_result_click', {
    result_id: result.id,
    result_index: index,
    relevance_score: result.score
  })

  // Navigate or open document
}
```

## Error Handling

### Invalid Props

The component validates props on mount:

```typescript
if (!result || !result.id) {
  console.error('SearchResultItem: result prop is required')
}
```

### Missing Highlights

If highlights are missing, component gracefully falls back to plain text:

```typescript
// No highlights - use title as-is
if (!result.highlights?.title) {
  {{ result.title }}
}
```

### Date Formatting Errors

If date is invalid, `formatDate` returns empty string or error message:

```typescript
const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-GB', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  } catch (e) {
    return 'Invalid date'
  }
}
```

## Testing

### Unit Test Example

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SearchResultItem from '@/components/search/SearchResultItem.vue'

describe('SearchResultItem.vue', () => {
  const mockResult = {
    id: 'doc-1',
    title: 'Test Document',
    content: 'Test content',
    document_type: 'note',
    author: 'Dr. Test',
    date: '2024-01-15',
    score: 85,
    highlights: {
      title: ['Test <mark>document</mark>']
    }
  }

  it('renders result data', () => {
    const wrapper = mount(SearchResultItem, {
      props: { result: mockResult, index: 0 }
    })
    expect(wrapper.text()).toContain('Test Document')
    expect(wrapper.text()).toContain('Dr. Test')
  })

  it('sanitizes HTML highlights', () => {
    const wrapper = mount(SearchResultItem, {
      props: { result: mockResult, index: 0 }
    })
    const titleHtml = wrapper.find('.text-h6').html()
    expect(titleHtml).toContain('<mark>')
    expect(titleHtml).not.toContain('<script>')
  })

  it('emits click event', async () => {
    const wrapper = mount(SearchResultItem, {
      props: { result: mockResult, index: 0 }
    })
    await wrapper.find('.v-card').trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
  })

  it('applies correct color to score', () => {
    const wrapper = mount(SearchResultItem, {
      props: { result: mockResult, index: 0 }
    })
    const chip = wrapper.find('[role="status"]')
    expect(chip.attributes('color')).toBe('success')
  })
})
```

## Migration Guide

If updating from previous versions:

### v0.x to v1.0

- `result` prop now requires `highlights` structure
- `score` now displays with 2 decimal places
- Hover effects are now enabled by default
- Sanitization is automatic (no manual escaping needed)

```vue
<!-- Old (v0.x) -->
<SearchResultItem :result="result" />

<!-- New (v1.0) - same, but with better sanitization -->
<SearchResultItem :result="result" :index="index" />
```

---

**Last Updated**: 2025-11-21
**Component Version**: 1.0.0
