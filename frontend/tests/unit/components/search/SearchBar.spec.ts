/**
 * SearchBar Component Tests
 *
 * Comprehensive unit tests for the SearchBar component including:
 * - Rendering
 * - User input handling
 * - Search trigger (Enter key)
 * - Clear functionality
 * - Loading states
 * - Props and emits
 * - Accessibility
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import SearchBar from '@/components/search/SearchBar.vue'

// Create Vuetify instance
const vuetify = createVuetify()

// Global mount options
const mountOptions = {
  global: {
    plugins: [vuetify],
  },
}

describe('SearchBar', () => {
  let wrapper: VueWrapper

  beforeEach(() => {
    wrapper = mount(SearchBar, mountOptions)
  })

  // ============================================================================
  // RENDERING TESTS
  // ============================================================================

  describe('rendering', () => {
    it('renders search input', () => {
      const input = wrapper.find('input[type="search"]')
      expect(input.exists()).toBe(true)
    })

    it('displays default placeholder text', () => {
      const input = wrapper.find('input')
      expect(input.attributes('placeholder')).toBe('Search documents...')
    })

    it('displays custom placeholder when prop provided', async () => {
      await wrapper.setProps({ placeholder: 'Custom placeholder' })
      const input = wrapper.find('input')
      expect(input.attributes('placeholder')).toBe('Custom placeholder')
    })

    it('renders magnifying glass icon', () => {
      const icon = wrapper.find('.mdi-magnify')
      expect(icon.exists()).toBe(true)
    })

    it('renders close icon when modelValue is not empty', async () => {
      await wrapper.setProps({ modelValue: 'test query' })
      const closeIcon = wrapper.find('.mdi-close')
      expect(closeIcon.exists()).toBe(true)
    })

    it('does not render close icon when modelValue is empty', () => {
      const closeIcon = wrapper.find('.mdi-close')
      expect(closeIcon.exists()).toBe(false)
    })
  })

  // ============================================================================
  // INPUT HANDLING TESTS
  // ============================================================================

  describe('input handling', () => {
    it('emits update:modelValue when user types', async () => {
      const input = wrapper.find('input')
      await input.setValue('test query')

      // Wait for debounce (300ms default)
      await new Promise(resolve => setTimeout(resolve, 350))

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['test query'])
    })

    it('debounces input updates', async () => {
      const input = wrapper.find('input')

      // Type rapidly
      await input.setValue('t')
      await input.setValue('te')
      await input.setValue('tes')
      await input.setValue('test')

      // Should not emit yet (within debounce period)
      expect(wrapper.emitted('update:modelValue')).toBeFalsy()

      // Wait for debounce
      await new Promise(resolve => setTimeout(resolve, 350))

      // Should emit only once after debounce
      expect(wrapper.emitted('update:modelValue')?.length).toBe(1)
    })

    it('uses custom debounce delay when provided', async () => {
      wrapper = mount(SearchBar, {
        ...mountOptions,
        props: { debounce: 100 },
      })

      const input = wrapper.find('input')
      await input.setValue('test')

      // Should not emit yet (within 100ms)
      expect(wrapper.emitted('update:modelValue')).toBeFalsy()

      // Wait for custom debounce
      await new Promise(resolve => setTimeout(resolve, 150))

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    })
  })

  // ============================================================================
  // SEARCH TRIGGER TESTS
  // ============================================================================

  describe('search trigger', () => {
    it('emits search event when Enter key pressed', async () => {
      await wrapper.setProps({ modelValue: 'diabetes' })
      const input = wrapper.find('input')

      await input.trigger('keydown.enter')

      expect(wrapper.emitted('search')).toBeTruthy()
      expect(wrapper.emitted('search')?.[0]).toEqual(['diabetes'])
    })

    it('trims whitespace when emitting search', async () => {
      await wrapper.setProps({ modelValue: '  diabetes  ' })
      const input = wrapper.find('input')

      await input.trigger('keydown.enter')

      expect(wrapper.emitted('search')?.[0]).toEqual(['diabetes'])
    })

    it('does not emit search when query is empty', async () => {
      await wrapper.setProps({ modelValue: '' })
      const input = wrapper.find('input')

      await input.trigger('keydown.enter')

      expect(wrapper.emitted('search')).toBeFalsy()
    })

    it('does not emit search when query is only whitespace', async () => {
      await wrapper.setProps({ modelValue: '   ' })
      const input = wrapper.find('input')

      await input.trigger('keydown.enter')

      expect(wrapper.emitted('search')).toBeFalsy()
    })
  })

  // ============================================================================
  // CLEAR FUNCTIONALITY TESTS
  // ============================================================================

  describe('clear functionality', () => {
    it('emits clear event when clear button clicked', async () => {
      await wrapper.setProps({ modelValue: 'test query' })
      const clearButton = wrapper.find('.mdi-close').element.parentElement

      await clearButton?.dispatchEvent(new Event('click'))
      await wrapper.vm.$nextTick()

      expect(wrapper.emitted('clear')).toBeTruthy()
    })

    it('emits update:modelValue with empty string when cleared', async () => {
      await wrapper.setProps({ modelValue: 'test query' })
      const clearButton = wrapper.find('.mdi-close').element.parentElement

      await clearButton?.dispatchEvent(new Event('click'))
      await wrapper.vm.$nextTick()

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      const events = wrapper.emitted('update:modelValue') as string[][]
      expect(events[events.length - 1]).toEqual([''])
    })
  })

  // ============================================================================
  // LOADING STATE TESTS
  // ============================================================================

  describe('loading state', () => {
    it('shows loading indicator when loading prop is true', async () => {
      await wrapper.setProps({ loading: true })

      // Vuetify text-field shows loading with a progress indicator
      const textField = wrapper.findComponent({ name: 'VTextField' })
      expect(textField.props('loading')).toBe(true)
    })

    it('disables input when loading', async () => {
      await wrapper.setProps({ loading: true })
      const input = wrapper.find('input')

      expect(input.attributes('disabled')).toBeDefined()
    })

    it('does not show loading indicator when loading prop is false', async () => {
      await wrapper.setProps({ loading: false })

      const textField = wrapper.findComponent({ name: 'VTextField' })
      expect(textField.props('loading')).toBe(false)
    })
  })

  // ============================================================================
  // PROPS TESTS
  // ============================================================================

  describe('props', () => {
    it('disables input when disabled prop is true', async () => {
      await wrapper.setProps({ disabled: true })
      const input = wrapper.find('input')

      expect(input.attributes('disabled')).toBeDefined()
    })

    it('enables input when disabled prop is false', async () => {
      await wrapper.setProps({ disabled: false, loading: false })
      const input = wrapper.find('input')

      expect(input.attributes('disabled')).toBeUndefined()
    })

    it('displays modelValue in input', async () => {
      await wrapper.setProps({ modelValue: 'current query' })
      const input = wrapper.find('input')

      expect(input.element.value).toBe('current query')
    })
  })

  // ============================================================================
  // ERROR HANDLING TESTS
  // ============================================================================

  describe('error handling', () => {
    it('displays error alert when error prop is provided', async () => {
      await wrapper.setProps({ error: 'Search failed' })

      const alert = wrapper.findComponent({ name: 'VAlert' })
      expect(alert.exists()).toBe(true)
      expect(alert.text()).toContain('Search failed')
    })

    it('does not display error alert when error prop is empty', () => {
      const alert = wrapper.findComponent({ name: 'VAlert' })
      expect(alert.exists()).toBe(false)
    })

    it('marks input with error state when error exists', async () => {
      await wrapper.setProps({ error: 'Search failed' })

      const textField = wrapper.findComponent({ name: 'VTextField' })
      expect(textField.props('error')).toBe(true)
    })

    it('emits clear-error event when error alert closed', async () => {
      await wrapper.setProps({ error: 'Search failed' })

      const alert = wrapper.findComponent({ name: 'VAlert' })
      await alert.vm.$emit('click:close')

      expect(wrapper.emitted('clear-error')).toBeTruthy()
    })
  })

  // ============================================================================
  // FOCUS/BLUR EVENTS TESTS
  // ============================================================================

  describe('focus and blur events', () => {
    it('emits focus event when input receives focus', async () => {
      const input = wrapper.find('input')
      await input.trigger('focus')

      expect(wrapper.emitted('focus')).toBeTruthy()
    })

    it('emits blur event when input loses focus', async () => {
      const input = wrapper.find('input')
      await input.trigger('blur')

      expect(wrapper.emitted('blur')).toBeTruthy()
    })
  })

  // ============================================================================
  // ACCESSIBILITY TESTS
  // ============================================================================

  describe('accessibility', () => {
    it('input has type="search" for semantic HTML', () => {
      const input = wrapper.find('input')
      expect(input.attributes('type')).toBe('search')
    })

    it('input has placeholder for screen readers', () => {
      const input = wrapper.find('input')
      expect(input.attributes('placeholder')).toBeTruthy()
    })

    it('supports keyboard navigation', async () => {
      const input = wrapper.find('input')

      // Should be focusable
      await input.trigger('focus')
      expect(document.activeElement).toBeTruthy()

      // Enter key should work
      await input.trigger('keydown.enter')
      // Tab key navigation is handled by browser
    })

    it('clear button is accessible', async () => {
      await wrapper.setProps({ modelValue: 'test' })
      const clearButton = wrapper.find('.mdi-close')

      // Icon should be inside a clickable element
      expect(clearButton.exists()).toBe(true)
      expect(clearButton.element.parentElement).toBeTruthy()
    })
  })

  // ============================================================================
  // SLOT TESTS
  // ============================================================================

  describe('slots', () => {
    it('renders hint slot when provided', async () => {
      wrapper = mount(SearchBar, {
        ...mountOptions,
        slots: {
          hint: '<span class="custom-hint">Search tip</span>',
        },
      })

      const hint = wrapper.find('.custom-hint')
      expect(hint.exists()).toBe(true)
      expect(hint.text()).toBe('Search tip')
    })

    it('does not render hint area when slot is empty', () => {
      // Default mount with no slots
      const hintArea = wrapper.find('.text-caption')
      expect(hintArea.exists()).toBe(false)
    })
  })

  // ============================================================================
  // INTEGRATION TESTS
  // ============================================================================

  describe('integration scenarios', () => {
    it('complete search workflow', async () => {
      const input = wrapper.find('input')

      // User types
      await input.setValue('diabetes')
      await new Promise(resolve => setTimeout(resolve, 350))

      // User presses Enter
      await input.trigger('keydown.enter')

      // Should emit both update and search
      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('search')).toBeTruthy()
      expect(wrapper.emitted('search')?.[0]).toEqual(['diabetes'])
    })

    it('error and recovery workflow', async () => {
      // Error occurs
      await wrapper.setProps({ error: 'Network error' })
      expect(wrapper.findComponent({ name: 'VAlert' }).exists()).toBe(true)

      // User clears error
      const alert = wrapper.findComponent({ name: 'VAlert' })
      await alert.vm.$emit('click:close')

      expect(wrapper.emitted('clear-error')).toBeTruthy()
    })

    it('loading state workflow', async () => {
      const input = wrapper.find('input')

      // User types
      await input.setValue('test')

      // Loading starts
      await wrapper.setProps({ loading: true })
      expect(input.attributes('disabled')).toBeDefined()

      // Loading finishes
      await wrapper.setProps({ loading: false })
      expect(input.attributes('disabled')).toBeUndefined()
    })
  })
})
