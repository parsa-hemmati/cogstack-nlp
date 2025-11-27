/**
 * SavedSearches Component Tests
 *
 * Tests for the saved searches sidebar component that displays
 * a list of user's saved searches with execute and delete actions.
 *
 * Test Coverage:
 * - Rendering and display (4 tests)
 * - Execute saved search (3 tests)
 * - Delete saved search (3 tests)
 * - Save current search (2 tests)
 * - Accessibility (2 tests)
 *
 * Total: 14 tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import SavedSearches from '@/components/search/SavedSearches.vue'

// Create Vuetify instance for testing
const vuetify = createVuetify({
  components,
  directives,
})

// Sample saved searches data
const mockSavedSearches = [
  {
    id: '1',
    name: 'Diabetes Notes',
    query: 'diabetes',
    filters: { document_types: ['clinical_note'] },
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    name: 'Recent Lab Results',
    query: 'laboratory test',
    filters: { document_types: ['lab_result'] },
    created_at: '2024-01-02T00:00:00Z',
  },
]

// Test helpers
function createWrapper(props = {}) {
  return mount(SavedSearches, {
    props: {
      savedSearches: [],
      ...props,
    },
    global: {
      plugins: [vuetify],
    },
  })
}

describe('SavedSearches Component', () => {
  let wrapper: VueWrapper<any>

  beforeEach(() => {
    wrapper = createWrapper()
  })

  // ============================================================================
  // Rendering and Display Tests (4 tests)
  // ============================================================================

  describe('Rendering and Display', () => {
    it('renders the component', () => {
      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('[data-testid="saved-searches"]').exists()).toBe(true)
    })

    it('shows empty state when no saved searches', () => {
      expect(wrapper.find('[data-testid="empty-state"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="empty-state"]').text()).toContain('No saved searches')
    })

    it('renders list of saved searches', async () => {
      const wrapperWithData = createWrapper({ savedSearches: mockSavedSearches })
      await wrapperWithData.vm.$nextTick()

      const items = wrapperWithData.findAll('[data-testid="saved-search-item"]')
      expect(items.length).toBe(2)
      expect(items[0].text()).toContain('Diabetes Notes')
      expect(items[1].text()).toContain('Recent Lab Results')
    })

    it('displays query text for each saved search', async () => {
      const wrapperWithData = createWrapper({ savedSearches: mockSavedSearches })
      await wrapperWithData.vm.$nextTick()

      const items = wrapperWithData.findAll('[data-testid="saved-search-item"]')
      expect(items[0].text()).toContain('diabetes')
      expect(items[1].text()).toContain('laboratory test')
    })
  })

  // ============================================================================
  // Execute Saved Search Tests (3 tests)
  // ============================================================================

  describe('Execute Saved Search', () => {
    it('emits execute event when saved search clicked', async () => {
      const wrapperWithData = createWrapper({ savedSearches: mockSavedSearches })
      await wrapperWithData.vm.$nextTick()

      const firstItem = wrapperWithData.find('[data-testid="saved-search-item"]')
      await firstItem.trigger('click')
      await wrapperWithData.vm.$nextTick()

      expect(wrapperWithData.emitted('execute')).toBeTruthy()
      expect(wrapperWithData.emitted('execute')![0][0]).toEqual(mockSavedSearches[0])
    })

    it('emits correct saved search on click', async () => {
      const wrapperWithData = createWrapper({ savedSearches: mockSavedSearches })
      await wrapperWithData.vm.$nextTick()

      const items = wrapperWithData.findAll('[data-testid="saved-search-item"]')
      await items[1].trigger('click')
      await wrapperWithData.vm.$nextTick()

      expect(wrapperWithData.emitted('execute')![0][0]).toEqual(mockSavedSearches[1])
    })

    it('shows execute icon on hover', async () => {
      const wrapperWithData = createWrapper({ savedSearches: mockSavedSearches })
      await wrapperWithData.vm.$nextTick()

      const firstItem = wrapperWithData.find('[data-testid="saved-search-item"]')
      expect(firstItem.find('[data-testid="execute-icon"]').exists()).toBe(true)
    })
  })

  // ============================================================================
  // Delete Saved Search Tests (3 tests)
  // ============================================================================

  describe('Delete Saved Search', () => {
    it('shows delete button for each saved search', async () => {
      const wrapperWithData = createWrapper({ savedSearches: mockSavedSearches })
      await wrapperWithData.vm.$nextTick()

      const deleteButtons = wrapperWithData.findAll('[data-testid="delete-btn"]')
      expect(deleteButtons.length).toBe(2)
    })

    it('emits delete event when delete button clicked', async () => {
      const wrapperWithData = createWrapper({ savedSearches: mockSavedSearches })
      await wrapperWithData.vm.$nextTick()

      const deleteButton = wrapperWithData.find('[data-testid="delete-btn"]')
      await deleteButton.trigger('click')
      await wrapperWithData.vm.$nextTick()

      expect(wrapperWithData.emitted('delete')).toBeTruthy()
      expect(wrapperWithData.emitted('delete')![0][0]).toBe('1')
    })

    it('shows confirmation dialog before deleting', async () => {
      const wrapperWithData = createWrapper({ savedSearches: mockSavedSearches })
      await wrapperWithData.vm.$nextTick()

      const deleteButton = wrapperWithData.find('[data-testid="delete-btn"]')
      await deleteButton.trigger('click')
      await wrapperWithData.vm.$nextTick()

      // Dialog should appear (component should have confirmDelete state)
      expect(wrapperWithData.vm.showDeleteConfirm).toBe(true)
    })
  })

  // ============================================================================
  // Save Current Search Tests (2 tests)
  // ============================================================================

  describe('Save Current Search', () => {
    it('renders save current search button', () => {
      const saveButton = wrapper.find('[data-testid="save-current-btn"]')
      expect(saveButton.exists()).toBe(true)
      expect(saveButton.text()).toContain('Save Current Search')
    })

    it('emits save event when save button clicked', async () => {
      const saveButton = wrapper.find('[data-testid="save-current-btn"]')
      await saveButton.trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.emitted('save')).toBeTruthy()
    })
  })

  // ============================================================================
  // Accessibility Tests (2 tests)
  // ============================================================================

  describe('Accessibility', () => {
    it('has appropriate ARIA labels on buttons', async () => {
      const wrapperWithData = createWrapper({ savedSearches: mockSavedSearches })
      await wrapperWithData.vm.$nextTick()

      const deleteButton = wrapperWithData.find('[data-testid="delete-btn"]')
      expect(deleteButton.attributes('aria-label')).toBeDefined()
      expect(deleteButton.attributes('aria-label')).toContain('Delete')
    })

    it('has role="list" on saved searches list', async () => {
      const wrapperWithData = createWrapper({ savedSearches: mockSavedSearches })
      await wrapperWithData.vm.$nextTick()

      const list = wrapperWithData.find('[data-testid="saved-searches-list"]')
      expect(list.attributes('role')).toBe('list')
    })
  })
})
