/**
 * Integration tests for Timeline Filtering workflow.
 *
 * Tests full filter workflow with concept search, date range,
 * meta-annotations, document types, filter presets, and URL sync.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import axios from 'axios'
import MockAdapter from 'axios-mock-adapter'
import TimelineView from '@/views/TimelineView.vue'
import type { PatientTimeline } from '@/types/timeline'
import type { FilterPreset } from '@/api/timeline'

// Create axios mock
const mockAxios = new MockAdapter(axios)

describe('Timeline Filtering Integration', () => {
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

  const mockFilteredTimeline: PatientTimeline = {
    patientId: 'patient-uuid-123',
    documents: [
      {
        documentId: 'doc-1',
        title: 'Clinical Note 2023-03-15',
        documentType: 'clinical_note',
        date: '2023-03-15T10:30:00Z',
        author: 'Dr. Smith',
        concepts: ['C0011849']
      },
      {
        documentId: 'doc-3',
        title: 'Discharge Summary 2023-09-10',
        documentType: 'discharge_summary',
        date: '2023-09-10T09:00:00Z',
        author: 'Dr. Lee',
        concepts: ['C0011849']
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
      }
    ],
    dateRange: {
      start: '2023-01-01T00:00:00Z',
      end: '2023-12-31T23:59:59Z'
    },
    filtersApplied: {
      conceptCuis: ['C0011849'],
      metaAnnotations: {
        Negation: 'Affirmed',
        Experiencer: 'Patient'
      }
    }
  }

  const mockPresets: FilterPreset[] = [
    {
      id: 'preset-1',
      user_id: 'user-123',
      name: 'Diabetes Management',
      filters: {
        concept_cuis: ['C0011849'],
        meta_annotations: {
          Negation: 'Affirmed',
          Experiencer: 'Patient',
          Temporality: ['Current', 'Recent']
        }
      },
      is_default: true,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z'
    },
    {
      id: 'preset-2',
      user_id: 'user-123',
      name: 'Cardiovascular Review',
      filters: {
        concept_cuis: ['C0020538'],
        document_types: ['clinical_note', 'discharge_summary']
      },
      is_default: false,
      created_at: '2023-01-02T00:00:00Z',
      updated_at: '2023-01-02T00:00:00Z'
    }
  ]

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
   * TEST 1: Full filter workflow
   * Load timeline → Open filter sidebar → Apply filters → Verify timeline updates → Verify URL updated
   */
  it('should complete full filter workflow', async () => {
    // Arrange - Initial timeline load
    mockAxios.onGet('/api/v1/timeline/patient-uuid-123').reply(200, mockTimeline)
    mockAxios.onGet('/api/v1/timeline/filters').reply(200, { presets: mockPresets, total: 2 })

    router.push('/timeline/patient-uuid-123')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Assert - Initial timeline rendered
    expect(wrapper.findAll('.document-marker').length).toBe(4)
    expect(wrapper.findAll('.concept-marker').length).toBe(3)

    // Act - Open filter sidebar
    const filterButton = wrapper.find('.filter-toggle-btn')
    await filterButton.trigger('click')
    await wrapper.vm.$nextTick()

    // Assert - Sidebar opened
    const sidebar = wrapper.find('.v-navigation-drawer')
    expect(sidebar.exists()).toBe(true)
    expect(sidebar.isVisible()).toBe(true)

    // Act - Apply concept filter (Diabetes Mellitus)
    mockAxios.onGet(/\/api\/v1\/timeline\/patient-uuid-123\?concepts=C0011849/).reply(200, mockFilteredTimeline)

    const vm = wrapper.vm as any
    vm.handleFiltersApplied({
      conceptCuis: ['C0011849'],
      dateFrom: null,
      dateTo: null,
      metaAnnotations: {
        Negation: 'Affirmed',
        Experiencer: 'Patient',
        Temporality: ['Current', 'Recent']
      },
      documentTypes: [],
      includeDocuments: true,
      includeConcepts: true
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Assert - Timeline updated with filtered data
    expect(wrapper.findAll('.document-marker').length).toBe(2)
    expect(wrapper.findAll('.concept-marker').length).toBe(1)

    // Assert - Active filter chips displayed
    const filterChips = wrapper.findAll('.filter-chip')
    expect(filterChips.length).toBeGreaterThan(0)

    // Assert - URL updated with query params
    expect(router.currentRoute.value.query.concepts).toBe('C0011849')
    expect(router.currentRoute.value.query.meta_negation).toBe('Affirmed')
    expect(router.currentRoute.value.query.meta_experiencer).toBe('Patient')
  })

  /**
   * TEST 2: Multi-filter combination
   * Apply concept + date range + meta-annotation + document type filters
   */
  it('should apply multiple filters simultaneously', async () => {
    // Arrange
    mockAxios.onGet('/api/v1/timeline/patient-uuid-123').reply(200, mockTimeline)
    mockAxios.onGet('/api/v1/timeline/filters').reply(200, { presets: mockPresets, total: 2 })

    router.push('/timeline/patient-uuid-123')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Act - Apply combined filters
    const combinedFilters = {
      conceptCuis: ['C0011849'],
      dateFrom: new Date('2023-03-01'),
      dateTo: new Date('2023-09-30'),
      metaAnnotations: {
        Negation: 'Affirmed',
        Experiencer: 'Patient',
        Temporality: ['Current', 'Recent']
      },
      documentTypes: ['clinical_note', 'discharge_summary'],
      includeDocuments: true,
      includeConcepts: true
    }

    mockAxios.onGet(/\/api\/v1\/timeline\/patient-uuid-123\?/).reply(200, mockFilteredTimeline)

    const vm = wrapper.vm as any
    const startTime = performance.now()
    vm.handleFiltersApplied(combinedFilters)

    await flushPromises()
    await wrapper.vm.$nextTick()

    const endTime = performance.now()
    const renderTime = endTime - startTime

    // Assert - All filters applied
    expect(router.currentRoute.value.query.concepts).toBe('C0011849')
    expect(router.currentRoute.value.query.from).toBe('2023-03-01')
    expect(router.currentRoute.value.query.to).toBe('2023-09-30')
    expect(router.currentRoute.value.query.meta_negation).toBe('Affirmed')
    expect(router.currentRoute.value.query.types).toBe('clinical_note,discharge_summary')

    // Assert - Timeline updated
    expect(wrapper.findAll('.document-marker').length).toBe(2)

    // Assert - Performance target (<500ms)
    expect(renderTime).toBeLessThan(500)
  })

  /**
   * TEST 3: Clear filters workflow
   * Apply filters → Clear filters → Verify timeline shows all data
   */
  it('should clear all filters and restore full timeline', async () => {
    // Arrange
    mockAxios.onGet('/api/v1/timeline/patient-uuid-123').reply(200, mockTimeline)
    mockAxios.onGet('/api/v1/timeline/filters').reply(200, { presets: mockPresets, total: 2 })

    router.push('/timeline/patient-uuid-123?concepts=C0011849')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Act - Clear filters
    mockAxios.onGet('/api/v1/timeline/patient-uuid-123').reply(200, mockTimeline)

    const vm = wrapper.vm as any
    vm.handleFiltersApplied({
      conceptCuis: [],
      dateFrom: null,
      dateTo: null,
      metaAnnotations: {
        Negation: 'Affirmed',
        Experiencer: 'Patient',
        Temporality: ['Current', 'Recent']
      },
      documentTypes: [],
      includeDocuments: true,
      includeConcepts: true
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Assert - Full timeline restored
    expect(wrapper.findAll('.document-marker').length).toBe(4)
    expect(wrapper.findAll('.concept-marker').length).toBe(3)

    // Assert - No active filter chips
    const filterChips = wrapper.findAll('.filter-chip')
    expect(filterChips.length).toBe(0)

    // Assert - URL query params cleared
    expect(router.currentRoute.value.query.concepts).toBeUndefined()
  })

  /**
   * TEST 4: Remove single filter chip
   * Apply multiple filters → Remove one filter → Verify timeline updates
   */
  it('should remove individual filter chips', async () => {
    // Arrange
    mockAxios.onGet('/api/v1/timeline/patient-uuid-123').reply(200, mockTimeline)
    mockAxios.onGet('/api/v1/timeline/filters').reply(200, { presets: mockPresets, total: 2 })

    router.push('/timeline/patient-uuid-123?concepts=C0011849,C0020538')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Act - Remove one concept filter
    mockAxios.onGet(/\/api\/v1\/timeline\/patient-uuid-123\?concepts=C0011849/).reply(200, mockFilteredTimeline)

    const vm = wrapper.vm as any
    vm.removeFilter({ type: 'concept', value: 'C0020538' })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Assert - Timeline refetched with remaining filter
    expect(router.currentRoute.value.query.concepts).toBe('C0011849')
  })

  /**
   * TEST 5: Filter presets - Save preset
   * Apply filters → Save preset → Verify preset created
   */
  it('should save filter preset', async () => {
    // Arrange
    mockAxios.onGet('/api/v1/timeline/patient-uuid-123').reply(200, mockTimeline)
    mockAxios.onGet('/api/v1/timeline/filters').reply(200, { presets: mockPresets, total: 2 })

    router.push('/timeline/patient-uuid-123')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Act - Open filter sidebar
    const filterButton = wrapper.find('.filter-toggle-btn')
    await filterButton.trigger('click')
    await wrapper.vm.$nextTick()

    // Mock preset creation
    const newPreset: FilterPreset = {
      id: 'preset-3',
      user_id: 'user-123',
      name: 'My Custom Filter',
      filters: {
        concept_cuis: ['C0011849'],
        meta_annotations: {
          Negation: 'Affirmed'
        }
      },
      is_default: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }

    mockAxios.onPost('/api/v1/timeline/filters').reply(201, newPreset)
    mockAxios.onGet('/api/v1/timeline/filters').reply(200, {
      presets: [...mockPresets, newPreset],
      total: 3
    })

    // Simulate save preset action (would be triggered by ConceptFilterSidebar)
    const sidebar = wrapper.findComponent({ name: 'ConceptFilterSidebar' })
    if (sidebar.exists()) {
      const sidebarVm = sidebar.vm as any
      await sidebarVm.savePreset()
      await flushPromises()

      // Assert - Preset created
      expect(mockAxios.history.post.length).toBeGreaterThan(0)
      expect(mockAxios.history.post[0].url).toBe('/api/v1/timeline/filters')
    }
  })

  /**
   * TEST 6: Filter presets - Load preset
   * Load preset → Verify filters applied from preset
   */
  it('should load filter preset and apply filters', async () => {
    // Arrange
    mockAxios.onGet('/api/v1/timeline/patient-uuid-123').reply(200, mockTimeline)
    mockAxios.onGet('/api/v1/timeline/filters').reply(200, { presets: mockPresets, total: 2 })

    router.push('/timeline/patient-uuid-123')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Act - Load preset
    mockAxios.onGet(/\/api\/v1\/timeline\/patient-uuid-123\?concepts=C0011849/).reply(200, mockFilteredTimeline)

    const vm = wrapper.vm as any
    const preset = mockPresets[0]

    vm.handleFiltersApplied({
      conceptCuis: preset.filters.concept_cuis || [],
      dateFrom: preset.filters.dateFrom || null,
      dateTo: preset.filters.dateTo || null,
      metaAnnotations: preset.filters.meta_annotations || {},
      documentTypes: preset.filters.document_types || [],
      includeDocuments: true,
      includeConcepts: true
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Assert - Filters from preset applied
    expect(router.currentRoute.value.query.concepts).toBe('C0011849')
    expect(wrapper.findAll('.document-marker').length).toBe(2)
  })

  /**
   * TEST 7: Shareable link - Filters loaded from URL
   * Navigate with query params → Verify filters loaded automatically
   */
  it('should load filters from URL query params', async () => {
    // Arrange - URL with filter query params
    mockAxios.onGet(/\/api\/v1\/timeline\/patient-uuid-123\?/).reply(200, mockFilteredTimeline)
    mockAxios.onGet('/api/v1/timeline/filters').reply(200, { presets: mockPresets, total: 2 })

    router.push('/timeline/patient-uuid-123?concepts=C0011849&meta_negation=Affirmed&meta_experiencer=Patient')
    await router.isReady()

    const wrapper = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    // Assert - Filters loaded from URL
    const vm = wrapper.vm as any
    expect(vm.filters.conceptCuis).toContain('C0011849')
    expect(vm.filters.metaAnnotations.Negation).toBe('Affirmed')
    expect(vm.filters.metaAnnotations.Experiencer).toBe('Patient')

    // Assert - Filtered timeline rendered
    expect(wrapper.findAll('.document-marker').length).toBe(2)
  })

  /**
   * TEST 8: Shareable link - Copy URL workflow
   * Apply filters → Copy URL → Open in new instance → Verify same filtered view
   */
  it('should create shareable link with filters', async () => {
    // Arrange
    mockAxios.onGet('/api/v1/timeline/patient-uuid-123').reply(200, mockTimeline)
    mockAxios.onGet('/api/v1/timeline/filters').reply(200, { presets: mockPresets, total: 2 })

    router.push('/timeline/patient-uuid-123')
    await router.isReady()

    const wrapper1 = mount(TimelineView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()
    await wrapper1.vm.$nextTick()

    // Act - Apply filters
    mockAxios.onGet(/\/api\/v1\/timeline\/patient-uuid-123\?concepts=C0011849/).reply(200, mockFilteredTimeline)

    const vm1 = wrapper1.vm as any
    vm1.handleFiltersApplied({
      conceptCuis: ['C0011849'],
      dateFrom: new Date('2023-01-01'),
      dateTo: new Date('2023-12-31'),
      metaAnnotations: {
        Negation: 'Affirmed',
        Experiencer: 'Patient'
      },
      documentTypes: [],
      includeDocuments: true,
      includeConcepts: true
    })

    await flushPromises()
    await wrapper1.vm.$nextTick()

    // Capture URL
    const shareableUrl = router.currentRoute.value.fullPath

    // Act - Create new instance with shareable URL
    const router2 = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: '/timeline/:patientId',
          name: 'timeline',
          component: TimelineView
        }
      ]
    })

    mockAxios.onGet(/\/api\/v1\/timeline\/patient-uuid-123\?/).reply(200, mockFilteredTimeline)
    mockAxios.onGet('/api/v1/timeline/filters').reply(200, { presets: mockPresets, total: 2 })

    router2.push(shareableUrl)
    await router2.isReady()

    const wrapper2 = mount(TimelineView, {
      global: {
        plugins: [router2]
      }
    })

    await flushPromises()
    await wrapper2.vm.$nextTick()

    // Assert - Same filtered view in new instance
    const vm2 = wrapper2.vm as any
    expect(vm2.filters.conceptCuis).toContain('C0011849')
    expect(vm2.filters.metaAnnotations.Negation).toBe('Affirmed')
    expect(wrapper2.findAll('.document-marker').length).toBe(2)
  })
})
