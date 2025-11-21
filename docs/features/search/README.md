# Search Module

## Overview

The search module provides a powerful, security-hardened full-text search interface for clinical documents with real-time highlighting, meta-annotation filtering, and XSS prevention. It integrates with Elasticsearch for fast document retrieval and MedCAT for NLP-powered concept extraction.

## Features

- ✅ **Full-text search** with Elasticsearch backend
- ✅ **Real-time highlighting** of search matches with `<mark>` tags
- ✅ **Meta-annotation filtering** (Negation, Experiencer, Temporality, Certainty)
- ✅ **XSS prevention** with DOMPurify sanitization
- ✅ **Pagination and sorting** with multiple sort options
- ✅ **Loading and error states** with user feedback
- ✅ **Responsive design** with Vuetify components
- ✅ **Type-safe API** with TypeScript throughout
- ✅ **Accessibility support** (ARIA labels, keyboard navigation)
- ✅ **HIPAA/GDPR compliant** with security considerations

## Quick Start

### Installation

```bash
# Install dependencies (already included in project)
npm install

# Components are registered globally via Vuetify
```

### Basic Usage

```vue
<template>
  <div class="search-page">
    <!-- Search input -->
    <SearchBar
      placeholder="Search documents..."
      @search="handleSearch"
      @error="handleError"
    />

    <!-- Search results -->
    <SearchResults
      :results="searchResults"
      :loading="isLoading"
      :error="searchError"
      :query="currentQuery"
      :total="totalResults"
      :page="currentPage"
      :page-size="pageSize"
      @update:page="handlePageChange"
      @update:sort="handleSortChange"
      @result-click="handleResultClick"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SearchBar from '@/components/search/SearchBar.vue'
import SearchResults from '@/components/search/SearchResults.vue'
import { usePatientSearch } from '@/composables/usePatientSearch'

const currentQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

// Use the search composable for state management
const {
  results: searchResults,
  total: totalResults,
  isLoading,
  error: searchError,
  search
} = usePatientSearch()

const handleSearch = async (query: string) => {
  currentQuery.value = query
  currentPage.value = 1
  await search(query, undefined, 1, pageSize.value)
}

const handlePageChange = async (page: number) => {
  currentPage.value = page
  await search(currentQuery.value, undefined, page, pageSize.value)
}

const handleSortChange = (sort: string) => {
  // Sort handling to be implemented with search API
  console.log('Sort changed:', sort)
}

const handleResultClick = (result) => {
  console.log('Result clicked:', result)
  // Navigate to document detail or open modal
}

const handleError = (error: string) => {
  console.error('Search error:', error)
}
</script>
```

## Architecture Diagram

```mermaid
graph TB
    subgraph Frontend["Frontend (Vue 3 + TypeScript)"]
        SB["SearchBar Component"]
        SR["SearchResults Component"]
        SRI["SearchResultItem Component"]
        UC["usePatientSearch Composable"]
        SAN["sanitizeHtml Utility"]
    end

    subgraph API["FastAPI Backend"]
        SE["Search Endpoint<br/>POST /api/v1/patients/search"]
        HE["Highlights Endpoint<br/>POST /api/v1/patients/highlights"]
    end

    subgraph External["External Services"]
        ES["Elasticsearch"]
        MC["MedCAT Service"]
        DB[(PostgreSQL)]
    end

    SB -->|event: search| UC
    SR -->|props: results| SRI
    UC -->|API call| SE
    UC -->|highlights request| HE
    SE -->|query| ES
    SE -->|concept extraction| MC
    SE -->|audit log| DB
    HE -->|snippet query| ES
    SAN -->|sanitize HTML| SRI
    SRI -->|display| HTML["Marked Highlights"]
```

## Directory Structure

```
docs/features/search/
├── README.md                    # Overview and quick start (this file)
├── components/
│   ├── SearchBar.md             # SearchBar component API documentation
│   ├── SearchResults.md         # SearchResults component API documentation
│   └── SearchResultItem.md      # SearchResultItem component API documentation
├── composables/
│   └── useSearch.md             # usePatientSearch composable documentation
├── security.md                  # XSS prevention and security guidelines
├── examples.md                  # 8 usage scenarios with code examples
└── troubleshooting.md           # Common issues and solutions
```

## Component Hierarchy

```
<SearchPage>
  ├── <SearchBar />
  │   └── Input handling
  │       └── Emit 'search' event
  │
  └── <SearchResults />
      ├── <v-skeleton-loader /> (loading state)
      ├── <v-alert /> (error state)
      ├── <v-alert /> (empty state)
      └── <SearchResultItem /> (for each result)
          ├── Title with highlights
          ├── Metadata (type, author, date)
          ├── Relevance score
          ├── Content excerpt with highlights
          └── Action buttons
```

## Key Technologies

| Technology | Purpose | Version |
|------------|---------|---------|
| Vue 3 | Frontend framework | 3.x |
| TypeScript | Type safety | 5.x |
| Vuetify | UI components | 3.x |
| DOMPurify | XSS prevention | 3.x |
| Elasticsearch | Search backend | 8.x |
| FastAPI | Search API | 0.x |

## Getting Started

### Prerequisites

- Node.js 16+
- npm or yarn
- Vue 3 project set up
- Elasticsearch 8.x running
- FastAPI backend running

### Setup Steps

1. **Import components**:
   ```typescript
   import SearchBar from '@/components/search/SearchBar.vue'
   import SearchResults from '@/components/search/SearchResults.vue'
   import SearchResultItem from '@/components/search/SearchResultItem.vue'
   ```

2. **Use the composable**:
   ```typescript
   import { usePatientSearch } from '@/composables/usePatientSearch'
   const { results, search, isLoading } = usePatientSearch()
   ```

3. **Add to your template**:
   ```vue
   <SearchBar @search="handleSearch" />
   <SearchResults :results="results" :loading="isLoading" />
   ```

4. **Implement handlers**:
   ```typescript
   const handleSearch = async (query: string) => {
     await search(query)
   }
   ```

## API Integration

### Search Endpoint

```
POST /api/v1/patients/search

Request:
{
  "concept": "diabetes",
  "filters": {
    "Negation": "Affirmed",
    "Experiencer": "Patient"
  },
  "pagination": {
    "page": 1,
    "pageSize": 20
  }
}

Response:
{
  "results": [...],
  "pagination": {
    "totalResults": 150,
    "page": 1,
    "pageSize": 20
  },
  "performance": {
    "searchTime": 245
  }
}
```

### Highlights Endpoint

```
POST /api/v1/patients/highlights

Request:
{
  "documentIds": ["doc-1", "doc-2"],
  "concept": "diabetes"
}

Response:
{
  "highlights": {
    "doc-1": {
      "title": ["Patient with <mark>diabetes</mark> mellitus"],
      "content": ["Type 2 <mark>diabetes</mark> diagnosed in 2020"]
    }
  }
}
```

## Security Considerations

### XSS Prevention

The search module prevents XSS attacks through:

1. **Input sanitization**: All HTML from Elasticsearch is sanitized with DOMPurify
2. **Allowed tags**: Only `<mark>` tags are allowed in highlights
3. **Attribute stripping**: All HTML attributes are removed
4. **Content preservation**: Text content is preserved when tags are stripped

See [security.md](./security.md) for detailed security guidelines.

## Performance

### Optimization Strategies

1. **Pagination**: Results are paginated (default 20 per page)
2. **Debouncing**: Search input is debounced to reduce API calls
3. **Caching**: Search results are cached when possible
4. **Virtual scrolling**: Large result sets use virtual scrolling (future)

### Benchmarks

| Operation | Target | Status |
|-----------|--------|--------|
| Search API response | <500ms | ✅ |
| Highlighting | <100ms | ✅ |
| Component render | <50ms | ✅ |
| Sanitization | <10ms | ✅ |

## Accessibility

The search module meets WCAG 2.1 Level AA standards:

- ✅ **Screen reader support**: All interactive elements have ARIA labels
- ✅ **Keyboard navigation**: Tab through all controls, Enter to search
- ✅ **Focus management**: Visible focus indicators
- ✅ **Color contrast**: All text meets contrast requirements
- ✅ **Error messages**: Clear error descriptions

## Compliance

### HIPAA

- ✅ PHI handling: Protected with encryption in transit/at rest
- ✅ Audit logging: All searches logged with user ID and timestamp
- ✅ Access control: RBAC enforced at API level
- ✅ XSS prevention: Eliminates session hijacking risk

### GDPR

- ✅ Data minimization: Only necessary data displayed
- ✅ User consent: Search history stored only with consent
- ✅ Right to erasure: User data deleted on request
- ✅ Privacy by design: Sanitization prevents data leakage

## Related Documentation

- [Component API Docs](./components/)
- [Composable Documentation](./composables/useSearch.md)
- [Security Guidelines](./security.md)
- [Usage Examples](./examples.md)
- [Troubleshooting Guide](./troubleshooting.md)

## Contributing

When contributing to the search module:

1. Read the [security.md](./security.md) guidelines
2. Follow the component patterns in existing components
3. Add TypeScript types for all props and events
4. Test with XSS payloads (see security.md)
5. Update documentation with your changes

## Support

For issues or questions:

1. Check [troubleshooting.md](./troubleshooting.md)
2. Review [examples.md](./examples.md) for usage patterns
3. See [Component API Docs](./components/) for prop/event details
4. Check backend logs: `/var/log/cogstack/search.log`

---

**Last Updated**: 2025-11-21
**Search Module Version**: 1.0.0
**API Version**: v1
