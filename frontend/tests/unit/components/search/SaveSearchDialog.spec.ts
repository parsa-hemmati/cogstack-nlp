/**
 * SaveSearchDialog Component Tests
 *
 * Tests for the save search dialog component that allows users to
 * save their current search query with a name and description.
 *
 * Test Coverage:
 * - Rendering and display (3 tests)
 * - Form validation (4 tests)
 * - Save functionality (3 tests)
 * - Error handling (2 tests)
 * - Accessibility (2 tests)
 *
 * Total: 14 tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import SaveSearchDialog from '@/components/search/SaveSearchDialog.vue'

// Create Vuetify instance for testing
const vuetify = createVuetify({
  components,
  directives,
})

// Test helpers
function createWrapper(props = {}) {
  return mount(SaveSearchDialog, {
    props: {
      modelValue: false,
      query: '',
      filters: {},
      ...props,
    },
    global: {
      plugins: [vuetify],
    },
  })
}

describe('SaveSearchDialog Component', () => {
  let wrapper: VueWrapper<any>

  beforeEach(() => {
    wrapper = createWrapper({ modelValue: true, query: 'diabetes' })
  })

  // ============================================================================
  // Rendering and Display Tests (3 tests)
  // ============================================================================

  describe('Rendering and Display', () => {
    it('renders dialog when modelValue is true', () => {
      expect(wrapper.find('[data-testid="save-search-dialog"]').exists()).toBe(true)
    })

    it('does not render dialog when modelValue is false', () => {
      const closedWrapper = createWrapper({ modelValue: false })
      expect(closedWrapper.find('[data-testid="save-search-dialog"]').isVisible()).toBe(false)
    })

    it('renders name and description inputs', () => {
      expect(wrapper.find('[data-testid="name-input"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="description-input"]').exists()).toBe(true)
    })
  })

  // ============================================================================
  // Form Validation Tests (4 tests)
  // ============================================================================

  describe('Form Validation', () => {
    it('shows error when name is empty', async () => {
      const nameInput = wrapper.find('[data-testid="name-input"]')
      await nameInput.setValue('')
      await wrapper.vm.$nextTick()

      const saveBtn = wrapper.find('[data-testid="save-btn"]')
      await saveBtn.trigger('click')
      await wrapper.vm.$nextTick()

      // Should show validation error
      expect(wrapper.vm.nameError).toBeTruthy()
    })

    it('requires name to be at least 3 characters', async () => {
      const nameInput = wrapper.find('[data-testid="name-input"]')
      await nameInput.setValue('ab')
      await wrapper.vm.$nextTick()

      const saveBtn = wrapper.find('[data-testid="save-btn"]')
      await saveBtn.trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.nameError).toBeTruthy()
    })

    it('description is optional', async () => {
      const nameInput = wrapper.find('[data-testid="name-input"]')
      await nameInput.setValue('My Search')
      await wrapper.vm.$nextTick()

      // Description can be empty
      const descriptionInput = wrapper.find('[data-testid="description-input"]')
      await descriptionInput.setValue('')
      await wrapper.vm.$nextTick()

      // Should not show error for empty description
      expect(wrapper.vm.descriptionError).toBeFalsy()
    })

    it('disables save button when form is invalid', async () => {
      const nameInput = wrapper.find('[data-testid="name-input"]')
      await nameInput.setValue('')
      await wrapper.vm.$nextTick()

      const saveBtn = wrapper.find('[data-testid="save-btn"]')
      expect(saveBtn.attributes('disabled')).toBeDefined()
    })
  })

  // ============================================================================
  // Save Functionality Tests (3 tests)
  // ============================================================================

  describe('Save Functionality', () => {
    it('emits saved event with form data when save clicked', async () => {
      const nameInput = wrapper.find('[data-testid="name-input"]')
      await nameInput.setValue('Diabetes Search')

      const descriptionInput = wrapper.find('[data-testid="description-input"]')
      await descriptionInput.setValue('Search for diabetes notes')
      await wrapper.vm.$nextTick()

      const saveBtn = wrapper.find('[data-testid="save-btn"]')
      await saveBtn.trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.emitted('saved')).toBeTruthy()
      const savedData = wrapper.emitted('saved')![0][0]
      expect(savedData).toMatchObject({
        name: 'Diabetes Search',
        description: 'Search for diabetes notes',
        query: 'diabetes',
      })
    })

    it('includes filters in saved data', async () => {
      const wrapperWithFilters = createWrapper({
        modelValue: true,
        query: 'diabetes',
        filters: { document_types: ['clinical_note'] },
      })

      const nameInput = wrapperWithFilters.find('[data-testid="name-input"]')
      await nameInput.setValue('Diabetes Notes')
      await wrapperWithFilters.vm.$nextTick()

      const saveBtn = wrapperWithFilters.find('[data-testid="save-btn"]')
      await saveBtn.trigger('click')
      await wrapperWithFilters.vm.$nextTick()

      const savedData = wrapperWithFilters.emitted('saved')![0][0]
      expect(savedData.filters).toEqual({ document_types: ['clinical_note'] })
    })

    it('clears form after successful save', async () => {
      const nameInput = wrapper.find('[data-testid="name-input"]')
      await nameInput.setValue('My Search')
      await wrapper.vm.$nextTick()

      const saveBtn = wrapper.find('[data-testid="save-btn"]')
      await saveBtn.trigger('click')
      await wrapper.vm.$nextTick()

      // Form should be cleared
      expect(wrapper.vm.name).toBe('')
      expect(wrapper.vm.description).toBe('')
    })
  })

  // ============================================================================
  // Error Handling Tests (2 tests)
  // ============================================================================

  describe('Error Handling', () => {
    it('shows error message when save fails', async () => {
      // Simulate error by setting error prop
      wrapper.vm.error = 'Failed to save search'
      await wrapper.vm.$nextTick()

      const errorAlert = wrapper.find('[data-testid="error-alert"]')
      expect(errorAlert.exists()).toBe(true)
      expect(errorAlert.text()).toContain('Failed to save search')
    })

    it('clears error when dialog is closed', async () => {
      wrapper.vm.error = 'Some error'
      await wrapper.vm.$nextTick()

      const closeBtn = wrapper.find('[data-testid="close-btn"]')
      await closeBtn.trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.error).toBe('')
    })
  })

  // ============================================================================
  // Accessibility Tests (2 tests)
  // ============================================================================

  describe('Accessibility', () => {
    it('has appropriate labels on form inputs', () => {
      const nameInput = wrapper.find('[data-testid="name-input"]')
      const descriptionInput = wrapper.find('[data-testid="description-input"]')

      expect(nameInput.attributes('label')).toBeDefined()
      expect(descriptionInput.attributes('label')).toBeDefined()
    })

    it('has aria-label on dialog', () => {
      const dialog = wrapper.find('[data-testid="save-search-dialog"]')
      expect(dialog.attributes('aria-label') || dialog.attributes('aria-labelledby')).toBeDefined()
    })
  })
})
