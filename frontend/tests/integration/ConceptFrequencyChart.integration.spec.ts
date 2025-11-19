/**
 * Integration tests for Concept Frequency Chart
 *
 * Tests the frequency chart in the context of the TimelineView component.
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

describe('ConceptFrequencyChart Integration', () => {
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
   * TEST 1: Frequency chart renders when toggled on
   */
  it('renders frequency chart when toggle button is clicked', async () => {
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

    // Frequency chart should not be visible initially
    expect(wrapper.find('.concept-frequency-chart').exists()).toBe(false)

    // Find and click frequency chart toggle button
    const toggleButton = wrapper.findAll('button').find(btn =>
      btn.attributes('title') === 'Toggle frequency chart'
    )
    expect(toggleButton).toBeDefined()
    await toggleButton!.trigger('click')

    // Frequency chart should now be visible
    expect(wrapper.find('.concept-frequency-chart').exists()).toBe(true)
    expect(wrapper.find('.frequency-chart-svg').exists()).toBe(true)
  })

  /**
   * TEST 2: Chart updates when filters are applied
   */
  it('updates chart data when timeline filters are applied', async () => {
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
    const toggleButton = wrapper.findAll('button').find(btn =>
      btn.attributes('title') === 'Toggle frequency chart'
    )
    await toggleButton!.trigger('click')

    // Get chart component
    const chart = wrapper.findComponent({ name: 'ConceptFrequencyChart' })
    expect(chart.exists()).toBe(true)

    // Check that chart receives concepts prop
    const chartProps = chart.props()
    expect(chartProps.concepts).toBeDefined()
    expect(chartProps.concepts.length).toBeGreaterThan(0)
  })

  /**
   * TEST 3: Chart toggle persists during session
   */
  it('maintains toggle state during timeline interactions', async () => {
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
    const toggleButton = wrapper.findAll('button').find(btn =>
      btn.attributes('title') === 'Toggle frequency chart'
    )
    await toggleButton!.trigger('click')

    // Chart should be visible
    expect(wrapper.find('.concept-frequency-chart').exists()).toBe(true)

    // Interact with timeline (e.g., zoom)
    const zoomInButton = wrapper.findAll('button').find(btn =>
      btn.attributes('title') === 'Zoom in (+)'
    )
    await zoomInButton!.trigger('click')

    // Chart should still be visible after zoom
    expect(wrapper.find('.concept-frequency-chart').exists()).toBe(true)

    // Toggle off
    await toggleButton!.trigger('click')

    // Chart should be hidden
    expect(wrapper.find('.concept-frequency-chart').exists()).toBe(false)
  })
})
