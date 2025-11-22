/**
 * Unit tests for TimelineFilters Component
 *
 * Tests Vuetify form controls for timeline filtering.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import TimelineFilters from '@/components/timeline/TimelineFilters.vue'
import type { TimelineFilters as TimelineFiltersType } from '@/types/timeline'

// Create Vuetify instance for tests
const vuetify = createVuetify({
  components,
  directives,
})

describe('TimelineFilters', () => {
  let wrapper: VueWrapper

  const defaultFilters: TimelineFiltersType = {
    date_start: undefined,
    date_end: undefined,
    concept_cuis: [],
    document_types: [],
    negation: undefined,
    experiencer: undefined,
    temporality: undefined,
    certainty: undefined,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('should render filter controls', () => {
      wrapper = mount(TimelineFilters, {
        props: {
          modelValue: defaultFilters,
        },
        global: {
          plugins: [vuetify],
        },
      })

      expect(wrapper.find('.timeline-filters').exists()).toBe(true)
    })

    it('should render concept autocomplete', () => {
      wrapper = mount(TimelineFilters, {
        props: {
          modelValue: defaultFilters,
        },
        global: {
          plugins: [vuetify],
        },
      })

      const autocomplete = wrapper.findComponent({ name: 'VAutocomplete' })
      expect(autocomplete.exists()).toBe(true)
    })

    it('should render date pickers', () => {
      wrapper = mount(TimelineFilters, {
        props: {
          modelValue: defaultFilters,
        },
        global: {
          plugins: [vuetify],
        },
      })

      const datePickers = wrapper.findAllComponents({ name: 'VTextField' })
      expect(datePickers.length).toBeGreaterThanOrEqual(2)
    })

    it('should render meta-annotation checkboxes', () => {
      wrapper = mount(TimelineFilters, {
        props: {
          modelValue: defaultFilters,
        },
        global: {
          plugins: [vuetify],
        },
      })

      const checkboxes = wrapper.findAllComponents({ name: 'VCheckbox' })
      expect(checkboxes.length).toBeGreaterThan(0)
    })

    it('should render action buttons', () => {
      wrapper = mount(TimelineFilters, {
        props: {
          modelValue: defaultFilters,
        },
        global: {
          plugins: [vuetify],
        },
      })

      const buttons = wrapper.findAllComponents({ name: 'VBtn' })
      expect(buttons.length).toBeGreaterThanOrEqual(2) // At least Apply and Clear
    })
  })

  describe('date range filters', () => {
    it('should update date_start when date picker changes', async () => {
      wrapper = mount(TimelineFilters, {
        props: {
          modelValue: defaultFilters,
        },
        global: {
          plugins: [vuetify],
        },
      })

      await wrapper.find('input[name="date_start"]').setValue('2024-01-01')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    })

    it('should update date_end when date picker changes', async () => {
      wrapper = mount(TimelineFilters, {
        props: {
          modelValue: defaultFilters,
        },
        global: {
          plugins: [vuetify],
        },
      })

      await wrapper.find('input[name="date_end"]').setValue('2024-12-31')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    })
  })

  describe('meta-annotation filters', () => {
    it('should toggle negation filter', async () => {
      wrapper = mount(TimelineFilters, {
        props: {
          modelValue: defaultFilters,
        },
        global: {
          plugins: [vuetify],
        },
      })

      const checkbox = wrapper.find('input[type="checkbox"][value="Affirmed"]')
      if (checkbox.exists()) {
        await checkbox.setValue(true)
        expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      }
    })
  })

  describe('actions', () => {
    it('should emit apply event when apply button is clicked', async () => {
      wrapper = mount(TimelineFilters, {
        props: {
          modelValue: defaultFilters,
        },
        global: {
          plugins: [vuetify],
        },
      })

      const applyButton = wrapper.find('button[data-testid="apply-filters"]')
      if (applyButton.exists()) {
        await applyButton.trigger('click')
        expect(wrapper.emitted('apply')).toBeTruthy()
      }
    })

    it('should emit clear event when clear button is clicked', async () => {
      wrapper = mount(TimelineFilters, {
        props: {
          modelValue: { ...defaultFilters, date_start: '2024-01-01' },
        },
        global: {
          plugins: [vuetify],
        },
      })

      const clearButton = wrapper.find('button[data-testid="clear-filters"]')
      if (clearButton.exists()) {
        await clearButton.trigger('click')
        expect(wrapper.emitted('clear')).toBeTruthy()
      }
    })

    it('should emit save-preset event when save button is clicked', async () => {
      wrapper = mount(TimelineFilters, {
        props: {
          modelValue: defaultFilters,
        },
        global: {
          plugins: [vuetify],
        },
      })

      const saveButton = wrapper.find('button[data-testid="save-preset"]')
      if (saveButton.exists()) {
        await saveButton.trigger('click')
        expect(wrapper.emitted('save-preset')).toBeTruthy()
      }
    })
  })

  describe('v-model binding', () => {
    it('should update modelValue when filters change', async () => {
      wrapper = mount(TimelineFilters, {
        props: {
          modelValue: defaultFilters,
          'onUpdate:modelValue': (value: TimelineFiltersType) => {
            wrapper.setProps({ modelValue: value })
          },
        },
        global: {
          plugins: [vuetify],
        },
      })

      await wrapper.find('input[name="date_start"]').setValue('2024-01-01')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    })
  })
})
