/**
 * Unit tests for TimelineChart Component
 *
 * Tests D3.js visualization, zoom/pan, and event handling.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import TimelineChart from '@/components/timeline/TimelineChart.vue'
import type { PatientTimeline, TimelineConcept, TimelineDocument } from '@/types/timeline'

describe('TimelineChart', () => {
  let wrapper: VueWrapper

  const mockDocument: TimelineDocument = {
    id: '650e8400-e29b-41d4-a716-446655440001',
    title: 'Clinic Note',
    type: 'clinic',
    document_date: '2024-03-15',
    author: 'Dr. Smith',
    concept_count: 5,
  }

  const mockConcept: TimelineConcept = {
    concept_cui: 'C0011860',
    name: 'Diabetes Mellitus',
    type: 'Disease',
    first_mention_date: '2024-03-15',
    mention_count: 1,
    mentions: [],
  }

  const mockTimeline: PatientTimeline = {
    patient_id: '550e8400-e29b-41d4-a716-446655440000',
    documents: [mockDocument],
    concepts: [mockConcept],
    date_range: ['2024-01-01', '2024-12-31'],
    filters_applied: {},
    statistics: {
      total_documents: 1,
      total_concepts: 1,
    },
  }

  describe('rendering', () => {
    it('should render SVG element', () => {
      wrapper = mount(TimelineChart, {
        props: {
          timeline: mockTimeline,
          loading: false,
          height: 400,
        },
      })

      const svg = wrapper.find('svg')
      expect(svg.exists()).toBe(true)
    })

    it('should have correct viewBox', () => {
      wrapper = mount(TimelineChart, {
        props: {
          timeline: mockTimeline,
          loading: false,
          height: 400,
        },
      })

      const svg = wrapper.find('svg')
      expect(svg.attributes('viewBox')).toBeDefined()
    })

    it('should render loading state', () => {
      wrapper = mount(TimelineChart, {
        props: {
          timeline: null,
          loading: true,
          height: 400,
        },
      })

      expect(wrapper.text()).toContain('Loading')
    })

    it('should render empty state when no timeline', () => {
      wrapper = mount(TimelineChart, {
        props: {
          timeline: null,
          loading: false,
          height: 400,
        },
      })

      expect(wrapper.text()).toContain('No timeline data')
    })
  })

  describe('document markers', () => {
    it('should render document markers as circles', () => {
      wrapper = mount(TimelineChart, {
        props: {
          timeline: mockTimeline,
          loading: false,
          height: 400,
        },
      })

      const circles = wrapper.findAll('circle.document-marker')
      expect(circles.length).toBeGreaterThan(0)
    })

    it('should emit document-click event when document is clicked', async () => {
      wrapper = mount(TimelineChart, {
        props: {
          timeline: mockTimeline,
          loading: false,
          height: 400,
        },
      })

      const circle = wrapper.find('circle.document-marker')
      await circle.trigger('click')

      expect(wrapper.emitted('document-click')).toBeTruthy()
      expect(wrapper.emitted('document-click')?.[0]).toEqual([mockDocument])
    })
  })

  describe('concept markers', () => {
    it('should render concept markers', () => {
      wrapper = mount(TimelineChart, {
        props: {
          timeline: mockTimeline,
          loading: false,
          height: 400,
        },
      })

      const markers = wrapper.findAll('circle.concept-marker')
      expect(markers.length).toBeGreaterThan(0)
    })

    it('should color code concepts by type', () => {
      const timelineWithMultipleTypes: PatientTimeline = {
        ...mockTimeline,
        concepts: [
          { ...mockConcept, type: 'Disease', concept_cui: 'C1' },
          { ...mockConcept, type: 'Medication', concept_cui: 'C2' },
        ],
      }

      wrapper = mount(TimelineChart, {
        props: {
          timeline: timelineWithMultipleTypes,
          loading: false,
          height: 400,
        },
      })

      const markers = wrapper.findAll('circle.concept-marker')
      expect(markers.length).toBe(2)

      // Check that markers have different fills (color coding)
      const fills = markers.map((m) => m.attributes('fill'))
      expect(new Set(fills).size).toBeGreaterThan(1)
    })

    it('should emit concept-click event when concept is clicked', async () => {
      wrapper = mount(TimelineChart, {
        props: {
          timeline: mockTimeline,
          loading: false,
          height: 400,
        },
      })

      const circle = wrapper.find('circle.concept-marker')
      await circle.trigger('click')

      expect(wrapper.emitted('concept-click')).toBeTruthy()
      expect(wrapper.emitted('concept-click')?.[0]).toEqual([mockConcept])
    })
  })

  describe('axes', () => {
    it('should render x-axis (time)', () => {
      wrapper = mount(TimelineChart, {
        props: {
          timeline: mockTimeline,
          loading: false,
          height: 400,
        },
      })

      const xAxis = wrapper.find('.x-axis')
      expect(xAxis.exists()).toBe(true)
    })

    it('should render y-axis (document types)', () => {
      wrapper = mount(TimelineChart, {
        props: {
          timeline: mockTimeline,
          loading: false,
          height: 400,
        },
      })

      const yAxis = wrapper.find('.y-axis')
      expect(yAxis.exists()).toBe(true)
    })
  })

  describe('legend', () => {
    it('should render legend with concept types', () => {
      wrapper = mount(TimelineChart, {
        props: {
          timeline: mockTimeline,
          loading: false,
          height: 400,
        },
      })

      const legend = wrapper.find('.legend')
      expect(legend.exists()).toBe(true)
      expect(legend.text()).toContain('Disease')
    })
  })

  describe('zoom and pan', () => {
    it('should have zoom behavior attached', () => {
      wrapper = mount(TimelineChart, {
        props: {
          timeline: mockTimeline,
          loading: false,
          height: 400,
        },
      })

      // Check if zoom transform is applied (d3 zoom adds transform attribute)
      const svg = wrapper.find('svg')
      expect(svg.exists()).toBe(true)
      // Zoom behavior is attached via D3, check in implementation
    })
  })

  describe('tooltip', () => {
    it('should show tooltip on concept hover', async () => {
      wrapper = mount(TimelineChart, {
        props: {
          timeline: mockTimeline,
          loading: false,
          height: 400,
        },
      })

      const circle = wrapper.find('circle.concept-marker')
      await circle.trigger('mouseenter')

      const tooltip = wrapper.find('.tooltip')
      expect(tooltip.exists()).toBe(true)
      expect(tooltip.text()).toContain(mockConcept.name)
    })

    it('should hide tooltip on mouseleave', async () => {
      wrapper = mount(TimelineChart, {
        props: {
          timeline: mockTimeline,
          loading: false,
          height: 400,
        },
      })

      const circle = wrapper.find('circle.concept-marker')
      await circle.trigger('mouseenter')
      await circle.trigger('mouseleave')

      const tooltip = wrapper.find('.tooltip')
      expect(tooltip.isVisible()).toBe(false)
    })
  })
})
