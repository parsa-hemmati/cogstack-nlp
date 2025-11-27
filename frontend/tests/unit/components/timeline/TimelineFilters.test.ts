/**
 * Unit tests for TimelineFilters component (Task #004).
 *
 * Tests filter controls, filter application, and URL state persistence.
 *
 * PRD Specification: .claude/ccpm/epics/timeline-module/004.md
 * Test Coverage: TimelineFilters component
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import TimelineFilters from '@/components/timeline/TimelineFilters.vue'

// Create Vuetify instance for tests
const vuetify = createVuetify({
  components,
  directives,
})

// Mock router
const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/timeline/:patientId', component: { template: '<div>Timeline</div>' } }
  ]
})

describe('TimelineFilters.vue', () => {
  let wrapper: VueWrapper<any>

  beforeEach(() => {
    wrapper = mount(TimelineFilters, {
      global: {
        plugins: [vuetify, router]
      },
      props: {
        modelValue: {
          dateRange: { start: '2023-01-01', end: '2023-12-31' },
          eventTypes: ['diagnosis', 'medication'],
          specialty: null
        }
      }
    })
  })

  it('renders filter controls', () => {
    // Verify component renders
    expect(wrapper.exists()).toBe(true)

    // Verify date range picker exists
    expect(wrapper.find('.timeline-filters').exists()).toBe(true)

    // Verify event type multi-select exists
    const eventTypeSelect = wrapper.findComponent({ name: 'v-select' })
    expect(eventTypeSelect.exists()).toBe(true)
  })

  it('emits update:modelValue when filters change', async () => {
    // Trigger filter change
    await wrapper.vm.applyFilters()

    // Verify emit
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })

  it('shows all event type options', () => {
    const eventTypes = wrapper.vm.eventTypeOptions
    expect(eventTypes).toContain('diagnosis')
    expect(eventTypes).toContain('procedure')
    expect(eventTypes).toContain('medication')
    expect(eventTypes).toContain('lab')
    expect(eventTypes).toContain('visit')
  })

  it('date range filter updates correctly', async () => {
    const newDateRange = { start: '2024-01-01', end: '2024-12-31' }

    await wrapper.setProps({
      modelValue: {
        ...wrapper.props('modelValue'),
        dateRange: newDateRange
      }
    })

    expect(wrapper.vm.dateRange).toEqual(newDateRange)
  })

  it('event type multi-select works', async () => {
    const newEventTypes = ['diagnosis', 'procedure', 'lab']

    await wrapper.setProps({
      modelValue: {
        ...wrapper.props('modelValue'),
        eventTypes: newEventTypes
      }
    })

    expect(wrapper.vm.eventTypes).toEqual(newEventTypes)
  })

  it('specialty filter works', async () => {
    const newSpecialty = 'cardiology'

    await wrapper.setProps({
      modelValue: {
        ...wrapper.props('modelValue'),
        specialty: newSpecialty
      }
    })

    expect(wrapper.vm.specialty).toBe(newSpecialty)
  })

  it('reset filters button clears all filters', async () => {
    const resetButton = wrapper.find('[data-test="reset-filters"]')
    await resetButton.trigger('click')

    const emitted = wrapper.emitted('update:modelValue')
    expect(emitted).toBeTruthy()

    if (emitted) {
      const lastEmit = emitted[emitted.length - 1][0] as any
      expect(lastEmit.eventTypes).toHaveLength(5) // All event types
      expect(lastEmit.specialty).toBeNull()
    }
  })

  it('filter state persisted in URL query params', async () => {
    await router.push({
      path: '/timeline/patient-123',
      query: {
        dateStart: '2023-01-01',
        dateEnd: '2023-12-31',
        eventTypes: 'diagnosis,medication',
        specialty: 'cardiology'
      }
    })

    // Component should read from URL query params
    wrapper = mount(TimelineFilters, {
      global: {
        plugins: [vuetify, router]
      }
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.vm.dateRange.start).toBe('2023-01-01')
    expect(wrapper.vm.dateRange.end).toBe('2023-12-31')
    expect(wrapper.vm.eventTypes).toContain('diagnosis')
    expect(wrapper.vm.eventTypes).toContain('medication')
    expect(wrapper.vm.specialty).toBe('cardiology')
  })

  it('shows event count for each filter option', () => {
    // Assuming eventCounts prop is passed
    const wrapperWithCounts = mount(TimelineFilters, {
      global: {
        plugins: [vuetify, router]
      },
      props: {
        modelValue: {
          dateRange: { start: '2023-01-01', end: '2023-12-31' },
          eventTypes: ['diagnosis'],
          specialty: null
        },
        eventCounts: {
          diagnosis: 42,
          procedure: 18,
          medication: 25,
          lab: 67,
          visit: 12
        }
      }
    })

    expect(wrapperWithCounts.vm.eventCounts.diagnosis).toBe(42)
    expect(wrapperWithCounts.vm.eventCounts.procedure).toBe(18)
  })

  it('filter changes debounced to 300ms', async () => {
    vi.useFakeTimers()

    const applyFiltersSpy = vi.spyOn(wrapper.vm, 'applyFilters')

    // Trigger multiple rapid changes
    wrapper.vm.dateRange = { start: '2023-06-01', end: '2023-12-31' }
    wrapper.vm.dateRange = { start: '2023-07-01', end: '2023-12-31' }
    wrapper.vm.dateRange = { start: '2023-08-01', end: '2023-12-31' }

    // Should not call applyFilters yet
    expect(applyFiltersSpy).not.toHaveBeenCalled()

    // Advance timers by 300ms
    vi.advanceTimersByTime(300)

    // Should have called applyFilters once (debounced)
    expect(applyFiltersSpy).toHaveBeenCalledTimes(1)

    vi.useRealTimers()
  })

  it('shows loading state during filter application', async () => {
    wrapper.vm.isLoading = true
    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-test="loading-indicator"]').exists()).toBe(true)
  })

  it('handles filter request errors gracefully', async () => {
    // Simulate error
    wrapper.vm.error = 'Failed to apply filters'
    await wrapper.vm.$nextTick()

    const errorMessage = wrapper.find('[data-test="error-message"]')
    expect(errorMessage.exists()).toBe(true)
    expect(errorMessage.text()).toContain('Failed to apply filters')
  })

  it('responsive design on mobile', async () => {
    // Set viewport to mobile
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375
    })

    wrapper = mount(TimelineFilters, {
      global: {
        plugins: [vuetify, router]
      }
    })

    // Verify mobile-specific classes or layout
    expect(wrapper.find('.timeline-filters--mobile').exists()).toBe(true)
  })

  it('date range presets work correctly', async () => {
    const presetButton = wrapper.find('[data-test="preset-last-30-days"]')
    await presetButton.trigger('click')

    const emitted = wrapper.emitted('update:modelValue')
    expect(emitted).toBeTruthy()

    if (emitted) {
      const lastEmit = emitted[emitted.length - 1][0] as any
      const start = new Date(lastEmit.dateRange.start)
      const end = new Date(lastEmit.dateRange.end)
      const diff = end.getTime() - start.getTime()
      const days = diff / (1000 * 60 * 60 * 24)
      expect(days).toBeCloseTo(30, 0)
    }
  })
})
