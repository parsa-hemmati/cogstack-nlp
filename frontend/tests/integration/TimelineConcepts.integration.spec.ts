/**
 * Integration tests for Timeline Concepts rendering.
 *
 * Tests full concept visualization workflow with TimelineConcepts and ConceptPopover.
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import axios from 'axios'
import MockAdapter from 'axios-mock-adapter'
import TimelineView from '@/views/TimelineView.vue'
import type { PatientTimeline } from '@/types/timeline'

// Create vuetify instance
const vuetify = createVuetify({
  components,
  directives
})

// Create axios mock
const mockAxios = new MockAdapter(axios)

describe('Timeline Concepts Integration', () => {
  let router: any

  const mockTimelineWithConcepts: PatientTimeline = {
    patientId: 'patient-123',
    documents: [
      {
        documentId: 'doc-1',
        title: 'Clinical Note 2024-01-15',
        documentType: 'clinical_note',
        date: '2024-01-15T10:30:00Z',
        author: 'Dr. Smith',
        concepts: ['C0011849', 'C0025598']
      },
      {
        documentId: 'doc-2',
        title: 'Follow-up Note 2024-02-20',
        documentType: 'clinical_note',
        date: '2024-02-20T14:00:00Z',
        author: 'Dr. Smith',
        concepts: ['C0011849', 'C0025598']
      }
    ],
    concepts: [
      {
        conceptCui: 'C0011849',
        conceptName: 'Diabetes Mellitus',
        conceptType: 'condition',
        firstMentionDate: '2024-01-15T10:30:00Z',
        mentionCount: 3,
        mentions: [
          {
            documentId: 'doc-1',
            date: '2024-01-15T10:30:00Z',
            confidence: 0.95,
            metaAnnotations: {
              Negation: 'Affirmed',
              Temporality: 'Recent',
              Experiencer: 'Patient',
              Certainty: 'Definite'
            },
            sentence: 'Patient diagnosed with diabetes mellitus.',
            conceptCui: 'C0011849',
            conceptName: 'Diabetes Mellitus',
            conceptType: 'condition'
          },
          {
            documentId: 'doc-2',
            date: '2024-02-20T14:00:00Z',
            confidence: 0.92,
            metaAnnotations: {
              Negation: 'Affirmed',
              Temporality: 'Current',
              Experiencer: 'Patient',
              Certainty: 'Definite'
            },
            sentence: 'Diabetes mellitus management ongoing.',
            conceptCui: 'C0011849',
            conceptName: 'Diabetes Mellitus',
            conceptType: 'condition'
          },
          {
            documentId: 'doc-2',
            date: '2024-02-20T14:00:00Z',
            confidence: 0.89,
            metaAnnotations: {
              Negation: 'Affirmed',
              Temporality: 'Current',
              Experiencer: 'Patient',
              Certainty: 'Definite'
            },
            sentence: 'Follow-up for diabetes mellitus.',
            conceptCui: 'C0011849',
            conceptName: 'Diabetes Mellitus',
            conceptType: 'condition'
          }
        ]
      },
      {
        conceptCui: 'C0025598',
        conceptName: 'Metformin',
        conceptType: 'medication',
        firstMentionDate: '2024-01-20T10:30:00Z',
        mentionCount: 2,
        mentions: [
          {
            documentId: 'doc-1',
            date: '2024-01-20T10:30:00Z',
            confidence: 0.98,
            metaAnnotations: {
              Negation: 'Affirmed',
              Temporality: 'Recent',
              Experiencer: 'Patient',
              Certainty: 'Definite'
            },
            sentence: 'Started on metformin 500mg.',
            conceptCui: 'C0025598',
            conceptName: 'Metformin',
            conceptType: 'medication'
          },
          {
            documentId: 'doc-2',
            date: '2024-02-20T14:00:00Z',
            confidence: 0.96,
            metaAnnotations: {
              Negation: 'Affirmed',
              Temporality: 'Current',
              Experiencer: 'Patient',
              Certainty: 'Definite'
            },
            sentence: 'Metformin continued.',
            conceptCui: 'C0025598',
            conceptName: 'Metformin',
            conceptType: 'medication'
          }
        ]
      }
    ],
    dateRange: {
      start: '2024-01-01T00:00:00Z',
      end: '2024-03-01T00:00:00Z'
    },
    filtersApplied: {}
  }

  beforeEach(() => {
    // Reset axios mocks
    mockAxios.reset()

    // Create router
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: '/timeline/:patientId',
          name: 'timeline',
          component: TimelineView
        }
      ]
    })

    // Push to timeline route
    router.push('/timeline/patient-123')
  })

  it('should render concept markers and show popover on click', async () => {
    // Mock API response
    mockAxios.onGet('/api/v1/timeline/patient-123').reply(200, mockTimelineWithConcepts)

    // Mount component
    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router, vuetify]
      }
    })

    // Wait for API call and rendering
    await flushPromises()
    await wrapper.vm.$nextTick()

    // Check concept markers rendered
    const markers = wrapper.findAll('.concept-marker')
    expect(markers.length).toBeGreaterThan(0)
    expect(markers.length).toBe(5) // 3 diabetes + 2 metformin mentions

    // Click first marker (first diabetes mention)
    await markers[0].trigger('click')
    await wrapper.vm.$nextTick()

    // Check popover is visible (v-menu renders outside wrapper)
    // Instead of checking visibility, check that selectedConcept is set
    expect(wrapper.vm.selectedConcept).toBeTruthy()
    expect(wrapper.vm.selectedConcept.conceptName).toBe('Diabetes Mellitus')
    expect(wrapper.vm.selectedConcept.conceptCui).toBe('C0011849')
    expect(wrapper.vm.showConceptPopover).toBe(true)
  })

  it('should render correct number of concept markers for each concept', async () => {
    mockAxios.onGet('/api/v1/timeline/patient-123').reply(200, mockTimelineWithConcepts)

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router, vuetify]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Total mentions: 3 diabetes + 2 metformin = 5 markers
    const markers = wrapper.findAll('.concept-marker')
    expect(markers).toHaveLength(5)
  })

  it('should pass concept data correctly to popover on click', async () => {
    mockAxios.onGet('/api/v1/timeline/patient-123').reply(200, mockTimelineWithConcepts)

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router, vuetify]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    const markers = wrapper.findAll('.concept-marker')
    await markers[0].trigger('click')
    await wrapper.vm.$nextTick()

    // Check selected concept has all required fields
    expect(wrapper.vm.selectedConcept).toMatchObject({
      conceptCui: 'C0011849',
      conceptName: 'Diabetes Mellitus',
      conceptType: 'condition',
      documentId: 'doc-1',
      sentence: 'Patient diagnosed with diabetes mellitus.',
      confidence: 0.95
    })

    // Check meta-annotations are present
    expect(wrapper.vm.selectedConcept.metaAnnotations).toMatchObject({
      Negation: 'Affirmed',
      Temporality: 'Recent',
      Experiencer: 'Patient',
      Certainty: 'Definite'
    })
  })

  it('should handle API errors gracefully', async () => {
    mockAxios.onGet('/api/v1/timeline/patient-123').reply(500, {
      detail: 'Internal server error'
    })

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router, vuetify]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // No markers should render
    const markers = wrapper.findAll('.concept-marker')
    expect(markers).toHaveLength(0)

    // Error message should be displayed
    expect(wrapper.vm.error).toBeTruthy()
  })

  it('should handle timeline with no concepts', async () => {
    const timelineNoConcepts = {
      ...mockTimelineWithConcepts,
      concepts: []
    }

    mockAxios.onGet('/api/v1/timeline/patient-123').reply(200, timelineNoConcepts)

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router, vuetify]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // No concept markers should render
    const markers = wrapper.findAll('.concept-marker')
    expect(markers).toHaveLength(0)

    // Documents should still render
    const docMarkers = wrapper.findAll('.document-marker')
    expect(docMarkers.length).toBeGreaterThan(0)
  })

  it('should distinguish first mention from recurring mentions by size', async () => {
    mockAxios.onGet('/api/v1/timeline/patient-123').reply(200, mockTimelineWithConcepts)

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router, vuetify]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    const markers = wrapper.findAll('.concept-marker')

    // First diabetes mention (index 0) should be larger (r=8)
    expect(markers[0].attributes('r')).toBe('8')

    // Recurring mentions should be smaller (r=4)
    expect(markers[1].attributes('r')).toBe('4')
    expect(markers[2].attributes('r')).toBe('4')
  })

  it('should color-code markers by concept type', async () => {
    mockAxios.onGet('/api/v1/timeline/patient-123').reply(200, mockTimelineWithConcepts)

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router, vuetify]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    const markers = wrapper.findAll('.concept-marker')

    // Diabetes (condition) - red
    expect(markers[0].attributes('fill')).toBe('#f44336')
    expect(markers[1].attributes('fill')).toBe('#f44336')
    expect(markers[2].attributes('fill')).toBe('#f44336')

    // Metformin (medication) - blue
    expect(markers[3].attributes('fill')).toBe('#2196f3')
    expect(markers[4].attributes('fill')).toBe('#2196f3')
  })
})
