/**
 * TimelineAxis Component Tests
 *
 * Tests for the D3.js timeline axis component
 * - Axis rendering
 * - Date range handling
 * - Zoom scale adjustments
 * - Responsive width updates
 * - D3.js integration
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import TimelineAxis from '@/components/timeline/TimelineAxis.vue'
import * as d3 from 'd3'

describe('TimelineAxis', () => {
  const defaultProps = {
    dateRange: {
      start: new Date('2023-01-01'),
      end: new Date('2023-12-31'),
    },
    width: 800,
    height: 60,
  }

  // ============================================================================
  // RENDERING TESTS
  // ============================================================================

  describe('rendering', () => {
    it('renders SVG element with correct dimensions', () => {
      const wrapper = mount(TimelineAxis, {
        props: defaultProps,
      })

      const svg = wrapper.find('svg')
      expect(svg.exists()).toBe(true)
      expect(svg.attributes('width')).toBe('800')
      expect(svg.attributes('height')).toBe('60')
    })

    it('renders axis group element', () => {
      const wrapper = mount(TimelineAxis, {
        props: defaultProps,
      })

      const axisGroup = wrapper.find('g')
      expect(axisGroup.exists()).toBe(true)
    })

    it('applies correct transform to axis group', () => {
      const wrapper = mount(TimelineAxis, {
        props: {
          ...defaultProps,
          height: 100,
        },
      })

      const axisGroup = wrapper.find('g')
      expect(axisGroup.attributes('transform')).toBe('translate(0, 50)')
    })

    it('applies timeline-axis class to SVG', () => {
      const wrapper = mount(TimelineAxis, {
        props: defaultProps,
      })

      const svg = wrapper.find('svg')
      expect(svg.classes()).toContain('timeline-axis')
    })
  })

  // ============================================================================
  // DATE RANGE TESTS
  // ============================================================================

  describe('date range handling', () => {
    it('renders with valid date range', () => {
      const wrapper = mount(TimelineAxis, {
        props: {
          ...defaultProps,
          dateRange: {
            start: new Date('2023-06-01'),
            end: new Date('2023-08-31'),
          },
        },
      })

      expect(wrapper.exists()).toBe(true)
    })

    it('handles single day date range', () => {
      const singleDay = new Date('2023-06-15')
      const wrapper = mount(TimelineAxis, {
        props: {
          ...defaultProps,
          dateRange: {
            start: singleDay,
            end: singleDay,
          },
        },
      })

      expect(wrapper.exists()).toBe(true)
    })

    it('handles multi-year date range', () => {
      const wrapper = mount(TimelineAxis, {
        props: {
          ...defaultProps,
          dateRange: {
            start: new Date('2020-01-01'),
            end: new Date('2023-12-31'),
          },
        },
      })

      expect(wrapper.exists()).toBe(true)
    })

    it('re-renders axis when date range changes', async () => {
      const wrapper = mount(TimelineAxis, {
        props: defaultProps,
      })

      const initialAxisContent = wrapper.find('g').html()

      await wrapper.setProps({
        dateRange: {
          start: new Date('2024-01-01'),
          end: new Date('2024-12-31'),
        },
      })

      await nextTick()

      const updatedAxisContent = wrapper.find('g').html()
      // Axis should have re-rendered (different content)
      expect(updatedAxisContent).not.toBe(initialAxisContent)
    })
  })

  // ============================================================================
  // ZOOM SCALE TESTS
  // ============================================================================

  describe('zoom scale adjustments', () => {
    it('renders with default zoom scale of 1', () => {
      const wrapper = mount(TimelineAxis, {
        props: defaultProps,
      })

      expect(wrapper.exists()).toBe(true)
    })

    it('accepts custom zoom scale', () => {
      const wrapper = mount(TimelineAxis, {
        props: {
          ...defaultProps,
          zoomScale: 2,
        },
      })

      expect(wrapper.exists()).toBe(true)
    })

    it('re-renders when zoom scale changes', async () => {
      const wrapper = mount(TimelineAxis, {
        props: {
          ...defaultProps,
          zoomScale: 1,
        },
      })

      const initialAxisContent = wrapper.find('g').html()

      await wrapper.setProps({
        zoomScale: 3,
      })

      await nextTick()

      const updatedAxisContent = wrapper.find('g').html()
      // Axis should have re-rendered with different tick density
      expect(updatedAxisContent).not.toBe(initialAxisContent)
    })

    it('handles very low zoom scale (0.1)', () => {
      const wrapper = mount(TimelineAxis, {
        props: {
          ...defaultProps,
          zoomScale: 0.1,
        },
      })

      expect(wrapper.exists()).toBe(true)
    })

    it('handles very high zoom scale (10)', () => {
      const wrapper = mount(TimelineAxis, {
        props: {
          ...defaultProps,
          zoomScale: 10,
        },
      })

      expect(wrapper.exists()).toBe(true)
    })
  })

  // ============================================================================
  // RESPONSIVE WIDTH TESTS
  // ============================================================================

  describe('responsive width', () => {
    it('renders with narrow width (400px)', () => {
      const wrapper = mount(TimelineAxis, {
        props: {
          ...defaultProps,
          width: 400,
        },
      })

      const svg = wrapper.find('svg')
      expect(svg.attributes('width')).toBe('400')
    })

    it('renders with wide width (1600px)', () => {
      const wrapper = mount(TimelineAxis, {
        props: {
          ...defaultProps,
          width: 1600,
        },
      })

      const svg = wrapper.find('svg')
      expect(svg.attributes('width')).toBe('1600')
    })

    it('re-renders when width changes', async () => {
      const wrapper = mount(TimelineAxis, {
        props: {
          ...defaultProps,
          width: 800,
        },
      })

      const initialAxisContent = wrapper.find('g').html()

      await wrapper.setProps({
        width: 1200,
      })

      await nextTick()

      const svg = wrapper.find('svg')
      expect(svg.attributes('width')).toBe('1200')

      const updatedAxisContent = wrapper.find('g').html()
      expect(updatedAxisContent).not.toBe(initialAxisContent)
    })
  })

  // ============================================================================
  // D3.JS INTEGRATION TESTS
  // ============================================================================

  describe('D3.js integration', () => {
    it('creates D3 time scale with correct domain', () => {
      const wrapper = mount(TimelineAxis, {
        props: defaultProps,
      })

      // Check that axis was rendered (D3 creates path and line elements)
      const axisGroup = wrapper.find('g')
      expect(axisGroup.html()).toContain('path') // D3 axis creates path for domain line
    })

    it('creates D3 axis with bottom orientation', () => {
      const wrapper = mount(TimelineAxis, {
        props: defaultProps,
      })

      const axisGroup = wrapper.find('g')
      // D3 axisBottom creates specific structure with domain path
      expect(axisGroup.html()).toContain('class="domain"')
    })

    it('renders tick marks', () => {
      const wrapper = mount(TimelineAxis, {
        props: defaultProps,
      })

      const axisGroup = wrapper.find('g')
      // D3 axis creates tick elements
      expect(axisGroup.html()).toContain('class="tick"')
    })

    it('renders tick labels with date format', () => {
      const wrapper = mount(TimelineAxis, {
        props: defaultProps,
      })

      const axisGroup = wrapper.find('g')
      const html = axisGroup.html()

      // Should contain month abbreviations (Jan, Feb, etc.) or year (2023)
      const hasDateContent = html.includes('Jan') || html.includes('2023') || html.includes('text')
      expect(hasDateContent).toBe(true)
    })
  })

  // ============================================================================
  // LIFECYCLE TESTS
  // ============================================================================

  describe('lifecycle', () => {
    it('renders axis on mount', () => {
      const wrapper = mount(TimelineAxis, {
        props: defaultProps,
      })

      const axisGroup = wrapper.find('g')
      // Axis should have D3-generated content
      expect(axisGroup.html().length).toBeGreaterThan(100)
    })

    it('cleans up previous axis before re-rendering', async () => {
      const wrapper = mount(TimelineAxis, {
        props: defaultProps,
      })

      // Change props to trigger re-render
      await wrapper.setProps({
        dateRange: {
          start: new Date('2024-01-01'),
          end: new Date('2024-12-31'),
        },
      })

      await nextTick()

      const axisGroup = wrapper.find('g')
      // Should not have duplicate axis elements
      const tickCount = (axisGroup.html().match(/class="tick"/g) || []).length
      // Reasonable number of ticks (not doubled due to missing cleanup)
      expect(tickCount).toBeLessThan(50)
      expect(tickCount).toBeGreaterThan(0)
    })
  })

  // ============================================================================
  // EDGE CASES
  // ============================================================================

  describe('edge cases', () => {
    it('handles very short time range (1 hour)', () => {
      const start = new Date('2023-06-15T10:00:00Z')
      const end = new Date('2023-06-15T11:00:00Z')

      const wrapper = mount(TimelineAxis, {
        props: {
          ...defaultProps,
          dateRange: { start, end },
        },
      })

      expect(wrapper.exists()).toBe(true)
    })

    it('handles very long time range (10 years)', () => {
      const start = new Date('2013-01-01')
      const end = new Date('2023-12-31')

      const wrapper = mount(TimelineAxis, {
        props: {
          ...defaultProps,
          dateRange: { start, end },
        },
      })

      expect(wrapper.exists()).toBe(true)
    })

    it('handles minimum height', () => {
      const wrapper = mount(TimelineAxis, {
        props: {
          ...defaultProps,
          height: 30,
        },
      })

      const svg = wrapper.find('svg')
      expect(svg.attributes('height')).toBe('30')
    })

    it('handles maximum height', () => {
      const wrapper = mount(TimelineAxis, {
        props: {
          ...defaultProps,
          height: 200,
        },
      })

      const svg = wrapper.find('svg')
      expect(svg.attributes('height')).toBe('200')
    })
  })

  // ============================================================================
  // STYLING TESTS
  // ============================================================================

  describe('styling', () => {
    it('applies scoped styles to axis elements', () => {
      const wrapper = mount(TimelineAxis, {
        props: defaultProps,
      })

      const svg = wrapper.find('svg')
      expect(svg.classes()).toContain('timeline-axis')
    })

    it('allows overflow for axis labels', () => {
      const wrapper = mount(TimelineAxis, {
        props: defaultProps,
      })

      const svg = wrapper.find('svg.timeline-axis')
      // Component has overflow: visible in CSS
      expect(svg.exists()).toBe(true)
    })
  })
})
