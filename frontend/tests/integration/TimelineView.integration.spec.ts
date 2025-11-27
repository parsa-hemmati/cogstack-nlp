/**
 * Integration tests for TimelineView component.
 *
 * Tests full timeline rendering workflow with API integration.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import axios from 'axios'
import MockAdapter from 'axios-mock-adapter'
import TimelineView from '@/views/TimelineView.vue'
import type { PatientTimeline } from '@/types/timeline'

// Create axios mock
const mockAxios = new MockAdapter(axios)

describe('Timeline View Integration', () => {
  let router: any

  const mockTimeline: PatientTimeline = {
    patientId: 'patient-uuid-123',
    documents: [
      {
        documentId: 'doc-1',
        title: 'Clinical Note 2023-03-15',
        documentType: 'clinical_note',
        date: '2023-03-15T10:30:00Z',
        author: 'Dr. Smith',
        concepts: ['C0011849', 'C0020538']
      },
      {
        documentId: 'doc-2',
        title: 'Lab Results 2023-06-20',
        documentType: 'lab_results',
        date: '2023-06-20T14:00:00Z',
        author: 'Dr. Johnson',
        concepts: ['C0005767']
      },
      {
        documentId: 'doc-3',
        title: 'Discharge Summary 2023-09-10',
        documentType: 'discharge_summary',
        date: '2023-09-10T09:00:00Z',
        author: 'Dr. Lee',
        concepts: ['C0011849']
      },
      {
        documentId: 'doc-4',
        title: 'Follow-up Note 2023-11-15',
        documentType: 'clinical_note',
        date: '2023-11-15T15:00:00Z',
        author: 'Dr. Smith',
        concepts: ['C0020538']
      },
      {
        documentId: 'doc-5',
        title: 'Imaging Report 2023-12-01',
        documentType: 'imaging_report',
        date: '2023-12-01T11:00:00Z',
        author: null,
        concepts: []
      }
    ],
    concepts: [
      {
        conceptCui: 'C0011849',
        conceptName: 'Diabetes Mellitus',
        conceptType: 'condition',
        firstMentionDate: '2023-03-15T10:30:00Z',
        mentionCount: 2,
        mentions: []
      },
      {
        conceptCui: 'C0020538',
        conceptName: 'Hypertension',
        conceptType: 'condition',
        firstMentionDate: '2023-03-15T10:30:00Z',
        mentionCount: 2,
        mentions: []
      },
      {
        conceptCui: 'C0005767',
        conceptName: 'Blood Test',
        conceptType: 'procedure',
        firstMentionDate: '2023-06-20T14:00:00Z',
        mentionCount: 1,
        mentions: []
      }
    ],
    dateRange: {
      start: '2023-01-01T00:00:00Z',
      end: '2023-12-31T23:59:59Z'
    },
    filtersApplied: {}
  }

  beforeEach(() => {
    // Reset axios mocks
    mockAxios.reset()

    // Create router with timeline route
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
  })

  /**
   * TEST 1: Full timeline rendering workflow
   */
  it('should render timeline with documents and axis', async () => {
    // Arrange
    mockAxios.onGet('/api/v1/timeline/patient-uuid-123').reply(200, mockTimeline)

    router.push('/timeline/patient-uuid-123')
    await router.isReady()

    // Act
    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    // Wait for API call and component updates
    await flushPromises()
    await wrapper.vm.$nextTick()

    // Assert - Timeline container rendered
    const timelineContainer = wrapper.find('.timeline-container')
    expect(timelineContainer.exists()).toBe(true)

    // Assert - SVG rendered
    const svg = wrapper.find('svg.timeline-svg')
    expect(svg.exists()).toBe(true)

    // Assert - TimelineAxis rendered
    const axis = wrapper.find('.timeline-axis')
    expect(axis.exists()).toBe(true)

    // Assert - TimelineDocuments rendered with correct number of markers
    const markers = wrapper.findAll('.document-marker')
    expect(markers.length).toBe(5)
  })

  /**
   * TEST 2: API error handling
   */
  it('should display error message when API fails', async () => {
    // Arrange
    mockAxios.onGet('/api/v1/timeline/patient-uuid-123').reply(500, {
      detail: 'Internal server error'
    })

    router.push('/timeline/patient-uuid-123')
    await router.isReady()

    // Act
    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Assert
    const alert = wrapper.find('.v-alert')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).toContain('Internal server error')
  })

  /**
   * TEST 3: Loading state during API call
   */
  it('should show loading indicator during API call', async () => {
    // Arrange
    let resolveRequest: (value: any) => void
    mockAxios.onGet('/api/v1/timeline/patient-uuid-123').reply(() => {
      return new Promise(resolve => {
        resolveRequest = () => resolve([200, mockTimeline])
      })
    })

    router.push('/timeline/patient-uuid-123')
    await router.isReady()

    // Act
    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    await wrapper.vm.$nextTick()

    // Assert - Loading indicator should be visible
    const loader = wrapper.find('.v-progress-linear')
    expect(loader.exists()).toBe(true)

    // Complete the request
    resolveRequest!()
    await flushPromises()
    await wrapper.vm.$nextTick()

    // Assert - Loading indicator should be gone
    expect(wrapper.find('.v-progress-linear').exists()).toBe(false)
  })

  /**
   * TEST 4: Document click interaction
   */
  it('should show document details when marker is clicked', async () => {
    // Arrange
    mockAxios.onGet('/api/v1/timeline/patient-uuid-123').reply(200, mockTimeline)

    router.push('/timeline/patient-uuid-123')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Act - Click first document marker
    const firstMarker = wrapper.findAll('.document-marker')[0]
    await firstMarker.trigger('click')
    await wrapper.vm.$nextTick()

    // Assert - Document details card should be visible
    const card = wrapper.find('.v-card')
    expect(card.exists()).toBe(true)
    expect(card.text()).toContain('Clinical Note 2023-03-15')
    expect(card.text()).toContain('clinical_note')
    expect(card.text()).toContain('Dr. Smith')
  })

  /**
   * TEST 5: Empty timeline (patient with no documents)
   */
  it('should show empty state when patient has no documents', async () => {
    // Arrange
    const emptyTimeline: PatientTimeline = {
      patientId: 'patient-uuid-456',
      documents: [],
      concepts: [],
      dateRange: {
        start: '2023-01-01T00:00:00Z',
        end: '2023-12-31T23:59:59Z'
      },
      filtersApplied: {}
    }

    mockAxios.onGet('/api/v1/timeline/patient-uuid-456').reply(200, emptyTimeline)

    router.push('/timeline/patient-uuid-456')
    await router.isReady()

    // Act
    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Assert - Empty state message
    const alert = wrapper.find('.v-alert')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).toContain('No timeline data available')

    // Assert - No document markers
    const markers = wrapper.findAll('.document-marker')
    expect(markers.length).toBe(0)
  })

  /**
   * TEST 6: Date range conversion
   */
  it('should correctly convert API date strings to Date objects', async () => {
    // Arrange
    mockAxios.onGet('/api/v1/timeline/patient-uuid-123').reply(200, mockTimeline)

    router.push('/timeline/patient-uuid-123')
    await router.isReady()

    // Act
    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Assert - Date range converted
    const vm = wrapper.vm as any
    expect(vm.dateRange.start).toBeInstanceOf(Date)
    expect(vm.dateRange.end).toBeInstanceOf(Date)
    expect(vm.dateRange.start.getFullYear()).toBe(2023)
    expect(vm.dateRange.end.getFullYear()).toBe(2023)
  })

  /**
   * TEST 7: 404 error (patient not found)
   */
  it('should handle 404 error gracefully', async () => {
    // Arrange
    mockAxios.onGet('/api/v1/timeline/patient-uuid-999').reply(404, {
      detail: 'Patient not found'
    })

    router.push('/timeline/patient-uuid-999')
    await router.isReady()

    // Act
    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Assert
    const alert = wrapper.find('.v-alert')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).toContain('Patient not found')
  })
})
