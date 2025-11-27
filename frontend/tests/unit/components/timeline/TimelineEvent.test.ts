/**
 * TimelineEvent Component Tests
 *
 * Tests for individual event markers on the timeline
 * - Event type color coding (diagnosis=red, medication=blue, etc.)
 * - Confidence-based sizing
 * - Click handlers
 * - Hover tooltips
 * - Accessibility
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import TimelineEvent from '@/components/timeline/TimelineEvent.vue'

describe('TimelineEvent', () => {
  // ============================================================================
  // EVENT TYPE COLOR CODING TESTS
  // ============================================================================

  describe('event type color coding', () => {
    it('renders diagnosis event with red color', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Type 2 Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      expect(circle.attributes('fill')).toBe('#ef4444') // red
    })

    it('renders procedure event with blue color', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '2',
            type: 'procedure',
            name: 'Coronary Angiography',
            date: '2023-07-20',
            confidence: 0.88,
          },
          xPosition: 200,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      expect(circle.attributes('fill')).toBe('#3b82f6') // blue
    })

    it('renders medication event with green color', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '3',
            type: 'medication',
            name: 'Metformin 500mg',
            date: '2023-08-01',
            confidence: 0.92,
          },
          xPosition: 300,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      expect(circle.attributes('fill')).toBe('#10b981') // green
    })

    it('renders lab event with amber color', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '4',
            type: 'lab',
            name: 'HbA1c Test',
            date: '2023-09-10',
            confidence: 0.99,
          },
          xPosition: 400,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      expect(circle.attributes('fill')).toBe('#f59e0b') // amber
    })

    it('renders visit event with purple color', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '5',
            type: 'visit',
            name: 'Cardiology Consultation',
            date: '2023-10-05',
            confidence: 0.85,
          },
          xPosition: 500,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      expect(circle.attributes('fill')).toBe('#8b5cf6') // purple
    })

    it('renders unknown event type with default gray color', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '6',
            type: 'unknown',
            name: 'Other Event',
            date: '2023-11-01',
            confidence: 0.75,
          },
          xPosition: 600,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      expect(circle.attributes('fill')).toBe('#6b7280') // gray
    })
  })

  // ============================================================================
  // CONFIDENCE-BASED SIZING TESTS
  // ============================================================================

  describe('confidence-based sizing', () => {
    it('renders large marker for high confidence (>0.9)', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Hypertension',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      expect(parseFloat(circle.attributes('r') || '0')).toBe(8)
    })

    it('renders medium marker for moderate confidence (0.7-0.9)', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '2',
            type: 'medication',
            name: 'Aspirin',
            date: '2023-07-20',
            confidence: 0.8,
          },
          xPosition: 200,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      expect(parseFloat(circle.attributes('r') || '0')).toBe(6)
    })

    it('renders small marker for low confidence (<0.7)', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '3',
            type: 'procedure',
            name: 'Possible Surgery',
            date: '2023-08-01',
            confidence: 0.6,
          },
          xPosition: 300,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      expect(parseFloat(circle.attributes('r') || '0')).toBe(4)
    })

    it('handles edge case confidence values (0 and 1)', () => {
      const wrapper1 = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Event 1',
            date: '2023-06-15',
            confidence: 0,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const wrapper2 = mount(TimelineEvent, {
        props: {
          event: {
            id: '2',
            type: 'diagnosis',
            name: 'Event 2',
            date: '2023-06-16',
            confidence: 1,
          },
          xPosition: 200,
          yPosition: 50,
        },
      })

      const circle1 = wrapper1.find('circle')
      const circle2 = wrapper2.find('circle')

      expect(parseFloat(circle1.attributes('r') || '0')).toBe(4) // Low confidence
      expect(parseFloat(circle2.attributes('r') || '0')).toBe(8) // High confidence
    })
  })

  // ============================================================================
  // POSITIONING TESTS
  // ============================================================================

  describe('positioning', () => {
    it('positions event at specified x and y coordinates', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 150,
          yPosition: 75,
        },
      })

      const circle = wrapper.find('circle')
      expect(circle.attributes('cx')).toBe('150')
      expect(circle.attributes('cy')).toBe('75')
    })

    it('updates position when props change', async () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      await wrapper.setProps({ xPosition: 200, yPosition: 100 })

      const circle = wrapper.find('circle')
      expect(circle.attributes('cx')).toBe('200')
      expect(circle.attributes('cy')).toBe('100')
    })
  })

  // ============================================================================
  // CLICK HANDLER TESTS
  // ============================================================================

  describe('click handling', () => {
    it('emits event-click when clicked', async () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      await circle.trigger('click')

      expect(wrapper.emitted('event-click')).toBeTruthy()
      expect(wrapper.emitted('event-click')![0]).toEqual([
        {
          id: '1',
          type: 'diagnosis',
          name: 'Diabetes',
          date: '2023-06-15',
          confidence: 0.95,
        },
      ])
    })

    it('emits click event multiple times', async () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      await circle.trigger('click')
      await circle.trigger('click')
      await circle.trigger('click')

      expect(wrapper.emitted('event-click')!.length).toBe(3)
    })
  })

  // ============================================================================
  // HOVER HANDLER TESTS
  // ============================================================================

  describe('hover handling', () => {
    it('emits event-hover on mouseenter', async () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      await circle.trigger('mouseenter')

      expect(wrapper.emitted('event-hover')).toBeTruthy()
      expect(wrapper.emitted('event-hover')![0][0]).toEqual({
        id: '1',
        type: 'diagnosis',
        name: 'Diabetes',
        date: '2023-06-15',
        confidence: 0.95,
      })
    })

    it('emits null event on mouseleave', async () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      await circle.trigger('mouseleave')

      expect(wrapper.emitted('event-hover')).toBeTruthy()
      expect(wrapper.emitted('event-hover')![0][0]).toBeNull()
    })

    it('includes mouse event in hover emission', async () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      await circle.trigger('mouseenter')

      expect(wrapper.emitted('event-hover')![0][1]).toBeTruthy()
      expect(wrapper.emitted('event-hover')![0][1]).toBeInstanceOf(MouseEvent)
    })
  })

  // ============================================================================
  // TOOLTIP TESTS
  // ============================================================================

  describe('tooltip', () => {
    it('renders SVG title element for screen readers', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Type 2 Diabetes Mellitus',
            date: '2023-06-15T14:30:00Z',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const title = wrapper.find('title')
      expect(title.exists()).toBe(true)
      expect(title.text()).toContain('Type 2 Diabetes Mellitus')
      expect(title.text()).toContain('Jun 15, 2023')
      expect(title.text()).toContain('95%')
    })

    it('formats tooltip with event details', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '2',
            type: 'medication',
            name: 'Metformin 500mg',
            date: '2023-08-01T10:15:00Z',
            confidence: 0.88,
          },
          xPosition: 200,
          yPosition: 50,
        },
      })

      const title = wrapper.find('title')
      expect(title.text()).toContain('Metformin 500mg')
      expect(title.text()).toContain('Aug 1, 2023')
      expect(title.text()).toContain('88%')
      expect(title.text()).toContain('medication')
    })
  })

  // ============================================================================
  // ACCESSIBILITY TESTS
  // ============================================================================

  describe('accessibility', () => {
    it('renders with proper ARIA role', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      expect(circle.attributes('role')).toBe('button')
    })

    it('renders with aria-label containing event details', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Type 2 Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      const ariaLabel = circle.attributes('aria-label')
      expect(ariaLabel).toContain('diagnosis')
      expect(ariaLabel).toContain('Type 2 Diabetes')
    })

    it('is keyboard accessible with tabindex', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      expect(circle.attributes('tabindex')).toBe('0')
    })

    it('handles keyboard enter key like click', async () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      await circle.trigger('keydown.enter')

      expect(wrapper.emitted('event-click')).toBeTruthy()
    })

    it('handles keyboard space key like click', async () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      await circle.trigger('keydown.space')

      expect(wrapper.emitted('event-click')).toBeTruthy()
    })
  })

  // ============================================================================
  // VISUAL STATE TESTS
  // ============================================================================

  describe('visual states', () => {
    it('applies hover class on mouseenter', async () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      await circle.trigger('mouseenter')

      expect(circle.classes()).toContain('event-marker--hover')
    })

    it('removes hover class on mouseleave', async () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      await circle.trigger('mouseenter')
      await circle.trigger('mouseleave')

      expect(circle.classes()).not.toContain('event-marker--hover')
    })

    it('applies selected class when isSelected prop is true', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
          isSelected: true,
        },
      })

      const circle = wrapper.find('circle')
      expect(circle.classes()).toContain('event-marker--selected')
    })
  })

  // ============================================================================
  // PROP VALIDATION TESTS
  // ============================================================================

  describe('prop validation', () => {
    it('accepts optional isSelected prop', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
          isSelected: false,
        },
      })

      expect(wrapper.exists()).toBe(true)
    })

    it('defaults isSelected to false when not provided', () => {
      const wrapper = mount(TimelineEvent, {
        props: {
          event: {
            id: '1',
            type: 'diagnosis',
            name: 'Diabetes',
            date: '2023-06-15',
            confidence: 0.95,
          },
          xPosition: 100,
          yPosition: 50,
        },
      })

      const circle = wrapper.find('circle')
      expect(circle.classes()).not.toContain('event-marker--selected')
    })
  })
})
