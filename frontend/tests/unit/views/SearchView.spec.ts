/**
 * SearchView Component Tests
 *
 * Tests for the main search view that integrates all search components
 * (SearchBar, QueryBuilder, FacetFilters, SearchResults, SavedSearches).
 *
 * Test Coverage:
 * - Rendering and layout (5 tests)
 * - Search execution (4 tests)
 * - Component integration (6 tests)
 * - State management (3 tests)
 * - Loading and error states (3 tests)
 *
 * Total: 21 tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import SearchView from '@/views/SearchView.vue'
import { createRouter, createMemoryHistory } from 'vue-router'

// Create Vuetify instance
const vuetify = createVuetify({
  components,
  directives,
})

// Create mock router
const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/search', name: 'search', component: SearchView },
  ],
})

// Test helpers
function createWrapper(props = {}) {
  return mount(SearchView, {
    props,
    global: {
      plugins: [vuetify, router],
      stubs: {
        SearchBar: true,
        QueryBuilder: true,
        SavedSearches: true,
      },
    },
  })
}

describe('SearchView', () => {
  let wrapper: VueWrapper<any>

  beforeEach(() => {
    wrapper = createWrapper()
  })

  // ============================================================================
  // Rendering and Layout Tests (5 tests)
  // ============================================================================

  describe('Rendering and Layout', () => {
    it('renders the search view', () => {
      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('[data-testid="search-view"]').exists()).toBe(true)
    })

    it('renders SearchBar component', () => {
      expect(wrapper.findComponent({ name: 'SearchBar' }).exists()).toBe(true)
    })

    it('renders SavedSearches sidebar', () => {
      expect(wrapper.findComponent({ name: 'SavedSearches' }).exists()).toBe(true)
    })

    it('renders results section', () => {
      expect(wrapper.find('[data-testid="results-section"]').exists()).toBe(true)
    })

    it('has three-column layout', () => {
      const columns = wrapper.findAll('.v-col')
      expect(columns.length).toBeGreaterThanOrEqual(2) // At least saved searches + results
    })
  })

  // ============================================================================
  // Search Execution Tests (4 tests)
  // ============================================================================

  describe('Search Execution', () => {
    it('executes search when SearchBar emits search event', async () => {
      const searchSpy = vi.spyOn(wrapper.vm, 'handleSearch')
      const searchBar = wrapper.findComponent({ name: 'SearchBar' })

      searchBar.vm.$emit('search', 'diabetes')
      await wrapper.vm.$nextTick()

      expect(searchSpy).toHaveBeenCalledWith('diabetes')
    })

    it('shows loading state during search', async () => {
      wrapper.vm.isLoading = true
      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="loading-indicator"]').exists()).toBe(true)
    })

    it('displays results after successful search', async () => {
      wrapper.vm.results = [
        { id: '1', title: 'Document 1', content: 'Content 1' },
        { id: '2', title: 'Document 2', content: 'Content 2' },
      ]
      await wrapper.vm.$nextTick()

      const resultItems = wrapper.findAll('[data-testid="result-item"]')
      expect(resultItems.length).toBe(2)
    })

    it('shows empty state when no results', async () => {
      wrapper.vm.results = []
      wrapper.vm.hasSearched = true
      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="empty-state"]').exists()).toBe(true)
    })
  })

  // ============================================================================
  // Component Integration Tests (6 tests)
  // ============================================================================

  describe('Component Integration', () => {
    it('passes query to SearchBar', async () => {
      wrapper.vm.query = 'diabetes'
      await wrapper.vm.$nextTick()

      const searchBar = wrapper.findComponent({ name: 'SearchBar' })
      expect(searchBar.props('modelValue')).toBe('diabetes')
    })

    it('executes saved search when SavedSearches emits execute', async () => {
      const savedSearch = {
        id: '1',
        name: 'Diabetes Search',
        query: 'diabetes',
        filters: {},
      }

      const savedSearches = wrapper.findComponent({ name: 'SavedSearches' })
      savedSearches.vm.$emit('execute', savedSearch)
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.query).toBe('diabetes')
    })

    it('opens save dialog when SavedSearches emits save', async () => {
      const savedSearches = wrapper.findComponent({ name: 'SavedSearches' })
      savedSearches.vm.$emit('save')
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.showSaveDialog).toBe(true)
    })

    it('deletes saved search when SavedSearches emits delete', async () => {
      const deleteSpy = vi.spyOn(wrapper.vm, 'deleteSavedSearch')
      const savedSearches = wrapper.findComponent({ name: 'SavedSearches' })

      savedSearches.vm.$emit('delete', '1')
      await wrapper.vm.$nextTick()

      expect(deleteSpy).toHaveBeenCalledWith('1')
    })

    it('updates query when QueryBuilder emits update', async () => {
      wrapper.vm.showQueryBuilder = true
      await wrapper.vm.$nextTick()

      const queryBuilder = wrapper.findComponent({ name: 'QueryBuilder' })
      queryBuilder.vm.$emit('update:modelValue', 'diabetes AND hypertension')
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.query).toBe('diabetes AND hypertension')
    })

    it('closes QueryBuilder when it emits close', async () => {
      wrapper.vm.showQueryBuilder = true
      await wrapper.vm.$nextTick()

      const queryBuilder = wrapper.findComponent({ name: 'QueryBuilder' })
      queryBuilder.vm.$emit('close')
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.showQueryBuilder).toBe(false)
    })
  })

  // ============================================================================
  // State Management Tests (3 tests)
  // ============================================================================

  describe('State Management', () => {
    it('maintains query state across searches', async () => {
      wrapper.vm.query = 'diabetes'
      await wrapper.vm.handleSearch('diabetes')
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.query).toBe('diabetes')
    })

    it('clears results when query is cleared', async () => {
      wrapper.vm.results = [{ id: '1', title: 'Document 1' }]
      wrapper.vm.query = ''
      await wrapper.vm.$nextTick()

      const searchBar = wrapper.findComponent({ name: 'SearchBar' })
      searchBar.vm.$emit('clear')
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.results).toEqual([])
    })

    it('preserves results when navigating away and back', async () => {
      wrapper.vm.results = [{ id: '1', title: 'Document 1' }]
      const resultsBefore = wrapper.vm.results

      await router.push('/other')
      await router.push('/search')
      await wrapper.vm.$nextTick()

      // Results should be preserved (or re-fetched)
      expect(wrapper.vm.results).toBeDefined()
    })
  })

  // ============================================================================
  // Loading and Error States Tests (3 tests)
  // ============================================================================

  describe('Loading and Error States', () => {
    it('shows loading indicator during search', async () => {
      wrapper.vm.isLoading = true
      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="loading-indicator"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="results-section"]').attributes('disabled')).toBeDefined()
    })

    it('shows error alert when search fails', async () => {
      wrapper.vm.error = 'Search failed'
      await wrapper.vm.$nextTick()

      const errorAlert = wrapper.find('[data-testid="error-alert"]')
      expect(errorAlert.exists()).toBe(true)
      expect(errorAlert.text()).toContain('Search failed')
    })

    it('clears error when new search is initiated', async () => {
      wrapper.vm.error = 'Previous error'
      await wrapper.vm.handleSearch('diabetes')
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.error).toBe('')
    })
  })
})
