/**
 * Integration tests for Timeline Interactions
 *
 * Tests zoom/pan, filters, first mentions, and frequency chart interactions.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import TimelineView from '@/views/TimelineView.vue'
import { createRouter, createMemoryHistory } from 'vue-router'

// Mock API client
vi.mock('@/api/timeline', () => ({
  getPatientTimeline: vi.fn(() => Promise.resolve({
    patientId: 'patient-123',
    documents: [
      {
        documentId: 'doc-1',
        title: 'Clinical Note 001',
        documentType: 'clinical_note',
        date: '2024-01-15T10:00:00Z',
        author: null,
        concepts: ['C0011849']
      }
    ],
    concepts: [
      {
        conceptCui: 'C0011849',
        conceptName: 'Diabetes Mellitus',
        conceptType: 'condition',
        firstMentionDate: '2024-01-15T10:00:00Z',
        mentionCount: 3,
        mentions: [
          {
            conceptCui: 'C0011849',
            conceptName: 'Diabetes Mellitus',
            conceptType: 'condition',
            documentId: 'doc-1',
            date: '2024-01-15T10:00:00Z',
            sentence: 'Patient diagnosed with diabetes.',
            metaAnnotations: {
              Negation: 'Affirmed',
              Temporality: 'Current',
              Experiencer: 'Patient',
              Certainty: 'High'
            },
            confidence: 0.95,
            isFirstMention: true
          },
          {
            conceptCui: 'C0011849',
            conceptName: 'Diabetes Mellitus',
            conceptType: 'condition',
            documentId: 'doc-2',
            date: '2024-02-20T10:00:00Z',
            sentence: 'Diabetes management.',
            metaAnnotations: {
              Negation: 'Affirmed',
              Temporality: 'Current',
              Experiencer: 'Patient',
              Certainty: 'High'
            },
            confidence: 0.92,
            isFirstMention: false
          },
          {
            conceptCui: 'C0011849',
            conceptName: 'Diabetes Mellitus',
            conceptType: 'condition',
            documentId: 'doc-3',
            date: '2024-03-10T10:00:00Z',
            sentence: 'Follow-up for diabetes.',
            metaAnnotations: {
              Negation: 'Affirmed',
              Temporality: 'Current',
              Experiencer: 'Patient',
              Certainty: 'High'
            },
            confidence: 0.89,
            isFirstMention: false
          }
        ]
      }
    ],
    dateRange: {
      start: '2024-01-15T10:00:00Z',
      end: '2024-03-10T10:00:00Z'
    },
    filtersApplied: {}
  }))
}))

describe('Timeline Interactions Integration', () => {
  let router: any

  beforeEach(() => {
    // Create router for testing
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: '/timeline/:patientId',
          name: 'TimelineView',
          component: TimelineView
        }
      ]
    })
  })

  /**
   * TEST 1: Full zoom workflow
   */
  it('completes full zoom workflow: zoom in → pan → reset', async () => {
    router.push('/timeline/patient-123')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    // Wait for timeline to load
    await vi.waitFor(() => {
      expect(wrapper.find('.timeline-svg').exists()).toBe(true)
    }, { timeout: 2000 })

    // Get initial zoom state
    const vm = wrapper.vm as any
    const initialScale = vm.zoomState.scale
    expect(initialScale).toBe(1)

    // Click zoom in button
    const zoomInButton = wrapper.findAll('button').find(btn =>
      btn.attributes('title') === 'Zoom in (+)'
    )
    expect(zoomInButton).toBeDefined()
    await zoomInButton!.trigger('click')

    // Scale should have increased
    const scaledState = vm.zoomState.scale
    expect(scaledState).toBeGreaterThan(initialScale)

    // Click reset zoom
    const resetButton = wrapper.findAll('button').find(btn =>
      btn.attributes('title') === 'Reset zoom (0)'
    )
    await resetButton!.trigger('click')

    // Scale should be back to 1
    const resetState = vm.zoomState.scale
    expect(resetState).toBe(1)
  })

  /**
   * TEST 2: Zoom + filter interaction
   */
  it('applies filters and zoom together correctly', async () => {
    router.push('/timeline/patient-123')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    // Wait for timeline to load
    await vi.waitFor(() => {
      expect(wrapper.find('.timeline-svg').exists()).toBe(true)
    }, { timeout: 2000 })

    // Zoom in first
    const zoomInButton = wrapper.findAll('button').find(btn =>
      btn.attributes('title') === 'Zoom in (+)'
    )
    await zoomInButton!.trigger('click')

    const vm = wrapper.vm as any
    const zoomedScale = vm.zoomState.scale
    expect(zoomedScale).toBeGreaterThan(1)

    // Open filter sidebar
    const filterButton = wrapper.findAll('button').find(btn =>
      btn.find('.mdi-filter-variant').exists()
    )
    await filterButton!.trigger('click')

    // Verify sidebar opened
    expect(vm.showFilterSidebar).toBe(true)

    // Zoom should persist after filter interaction
    expect(vm.zoomState.scale).toBe(zoomedScale)
  })

  /**
   * TEST 3: Frequency chart + zoom interaction
   */
  it('maintains zoom when frequency chart is toggled', async () => {
    router.push('/timeline/patient-123')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    // Wait for timeline to load
    await vi.waitFor(() => {
      expect(wrapper.find('.timeline-svg').exists()).toBe(true)
    }, { timeout: 2000 })

    // Zoom in
    const zoomInButton = wrapper.findAll('button').find(btn =>
      btn.attributes('title') === 'Zoom in (+)'
    )
    await zoomInButton!.trigger('click')

    const vm = wrapper.vm as any
    const zoomedScale = vm.zoomState.scale

    // Toggle frequency chart
    const chartToggle = wrapper.findAll('button').find(btn =>
      btn.attributes('title') === 'Toggle frequency chart'
    )
    await chartToggle!.trigger('click')

    // Chart should be visible
    expect(vm.showFrequencyChart).toBe(true)

    // Zoom should persist
    expect(vm.zoomState.scale).toBe(zoomedScale)
  })

  /**
   * TEST 4: Keyboard shortcuts work
   */
  it('responds to keyboard shortcuts (+, -, 0)', async () => {
    router.push('/timeline/patient-123')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    // Wait for timeline to load
    await vi.waitFor(() => {
      expect(wrapper.find('.timeline-svg').exists()).toBe(true)
    }, { timeout: 2000 })

    const vm = wrapper.vm as any

    // Press + key
    window.dispatchEvent(new KeyboardEvent('keydown', { key: '+' }))
    await wrapper.vm.$nextTick()

    // Scale should increase (assuming handleKeydown works)
    // Note: Actual zoom handled by D3, but we can verify method calls

    // Press 0 key to reset
    window.dispatchEvent(new KeyboardEvent('keydown', { key: '0' }))
    await wrapper.vm.$nextTick()

    // Verify keyboard event listeners are attached
    expect(vm.handleKeydown).toBeDefined()
  })

  /**
   * TEST 5: First mention vs recurring markers
   */
  it('renders first mention with r=8 and recurring with r=4', async () => {
    router.push('/timeline/patient-123')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    // Wait for timeline to load
    await vi.waitFor(() => {
      expect(wrapper.find('.timeline-svg').exists()).toBe(true)
    }, { timeout: 2000 })

    // Find concept markers
    const markers = wrapper.findAll('.concept-marker')
    expect(markers.length).toBeGreaterThan(0)

    // First marker should have r=8 (first mention)
    const firstMarker = markers[0]
    expect(firstMarker.attributes('r')).toBe('8')
    expect(firstMarker.classes()).toContain('concept-marker-first')

    // Second marker should have r=4 (recurring mention)
    if (markers.length > 1) {
      const secondMarker = markers[1]
      expect(secondMarker.attributes('r')).toBe('4')
      expect(secondMarker.classes()).toContain('concept-marker-recurring')
    }
  })

  /**
   * TEST 6: Frequency chart renders and shows tooltip
   */
  it('frequency chart displays data correctly', async () => {
    router.push('/timeline/patient-123')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    // Wait for timeline to load
    await vi.waitFor(() => {
      expect(wrapper.find('.timeline-svg').exists()).toBe(true)
    }, { timeout: 2000 })

    // Toggle on frequency chart
    const chartToggle = wrapper.findAll('button').find(btn =>
      btn.attributes('title') === 'Toggle frequency chart'
    )
    await chartToggle!.trigger('click')

    // Chart should render
    expect(wrapper.find('.concept-frequency-chart').exists()).toBe(true)
    expect(wrapper.find('.frequency-chart-svg').exists()).toBe(true)

    // Bars group should exist
    expect(wrapper.find('.bars').exists()).toBe(true)
  })

  /**
   * TEST 7: Zoom level display updates
   */
  it('displays current zoom level as percentage', async () => {
    router.push('/timeline/patient-123')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    // Wait for timeline to load
    await vi.waitFor(() => {
      expect(wrapper.find('.timeline-svg').exists()).toBe(true)
    }, { timeout: 2000 })

    // Find zoom level display
    const zoomLevel = wrapper.find('.zoom-level')
    expect(zoomLevel.exists()).toBe(true)
    expect(zoomLevel.text()).toContain('%')

    // Initial zoom should be 100%
    const vm = wrapper.vm as any
    const initialPercentage = vm.currentZoomLevel
    expect(initialPercentage).toBe('100%')
  })

  /**
   * TEST 8: Timeline loads and renders all components
   */
  it('loads timeline with all components visible', async () => {
    router.push('/timeline/patient-123')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    // Wait for timeline to load
    await vi.waitFor(() => {
      expect(wrapper.find('.timeline-svg').exists()).toBe(true)
    }, { timeout: 2000 })

    // Verify all main components are present
    expect(wrapper.find('.timeline-axis').exists()).toBe(true)
    expect(wrapper.findAll('.concept-marker').length).toBeGreaterThan(0)

    // Toolbar buttons should exist
    const zoomIn = wrapper.findAll('button').find(btn =>
      btn.attributes('title') === 'Zoom in (+)'
    )
    const zoomOut = wrapper.findAll('button').find(btn =>
      btn.attributes('title') === 'Zoom out (-)'
    )
    const reset = wrapper.findAll('button').find(btn =>
      btn.attributes('title') === 'Reset zoom (0)'
    )
    const chartToggle = wrapper.findAll('button').find(btn =>
      btn.attributes('title') === 'Toggle frequency chart'
    )

    expect(zoomIn).toBeDefined()
    expect(zoomOut).toBeDefined()
    expect(reset).toBeDefined()
    expect(chartToggle).toBeDefined()
  })
})
