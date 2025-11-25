/**
 * Unit tests for TimelineDocuments.vue component.
 *
 * Tests document marker rendering, positioning, click/hover events, and D3.js integration.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import TimelineDocuments from '@/components/timeline/TimelineDocuments.vue'
import type { TimelineDocument } from '@/types/timeline'

describe('TimelineDocuments.vue', () => {
  let wrapper: VueWrapper<any>

  const mockDocuments: TimelineDocument[] = [
    {
      documentId: 'doc-1',
      title: 'Clinical Note 2023-03-15',
      documentType: 'clinical_note',
      date: '2023-03-15T10:30:00Z',
      author: 'Dr. Smith',
      concepts: ['C0011849']
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
      author: null,
      concepts: []
    }
  ]

  const dateRange = {
    start: new Date('2023-01-01'),
    end: new Date('2023-12-31')
  }

  /**
   * TEST 1: Component mounting and rendering
   */
  it('should mount and render SVG group element', () => {
    // Arrange & Act
    wrapper = mount(TimelineDocuments, {
      props: {
        documents: mockDocuments,
        dateRange,
        width: 800,
        documentY: 50
      }
    })

    // Assert
    expect(wrapper.exists()).toBe(true)
    const group = wrapper.find('g.timeline-documents')
    expect(group.exists()).toBe(true)
  })

  /**
   * TEST 2: Render correct number of document markers
   */
  it('should render one circle for each document', () => {
    // Arrange & Act
    wrapper = mount(TimelineDocuments, {
      props: {
        documents: mockDocuments,
        dateRange,
        width: 800,
        documentY: 50
      }
    })

    // Assert
    const circles = wrapper.findAll('circle.document-marker')
    expect(circles.length).toBe(3)
  })

  /**
   * TEST 3: Document markers have unique keys
   */
  it('should use documentId as key for each marker', () => {
    // Arrange & Act
    wrapper = mount(TimelineDocuments, {
      props: {
        documents: mockDocuments,
        dateRange,
        width: 800,
        documentY: 50
      }
    })

    // Assert
    const circles = wrapper.findAll('circle.document-marker')

    // Check that each circle has a unique key attribute
    const keys = circles.map(circle => circle.element.getAttribute('data-v-key'))
    expect(circles.length).toBe(3)
  })

  /**
   * TEST 4: Document markers positioned at correct Y coordinate
   */
  it('should position markers at documentY prop value', () => {
    // Arrange & Act
    wrapper = mount(TimelineDocuments, {
      props: {
        documents: mockDocuments,
        dateRange,
        width: 800,
        documentY: 75
      }
    })

    // Assert
    const circles = wrapper.findAll('circle.document-marker')
    circles.forEach(circle => {
      expect(circle.attributes('cy')).toBe('75')
    })
  })

  /**
   * TEST 5: Document markers have correct radius
   */
  it('should render markers with radius of 5', () => {
    // Arrange & Act
    wrapper = mount(TimelineDocuments, {
      props: {
        documents: mockDocuments,
        dateRange,
        width: 800,
        documentY: 50
      }
    })

    // Assert
    const circles = wrapper.findAll('circle.document-marker')
    circles.forEach(circle => {
      expect(circle.attributes('r')).toBe('5')
    })
  })

  /**
   * TEST 6: Document markers positioned by date (X coordinate)
   */
  it('should position markers based on document date using time scale', () => {
    // Arrange & Act
    wrapper = mount(TimelineDocuments, {
      props: {
        documents: mockDocuments,
        dateRange,
        width: 800,
        documentY: 50
      }
    })

    // Assert
    const circles = wrapper.findAll('circle.document-marker')

    // First document (2023-03-15) should be left of second (2023-06-20)
    const cx1 = parseFloat(circles[0].attributes('cx') || '0')
    const cx2 = parseFloat(circles[1].attributes('cx') || '0')
    const cx3 = parseFloat(circles[2].attributes('cx') || '0')

    expect(cx1).toBeGreaterThan(50) // After left padding
    expect(cx1).toBeLessThan(750)   // Before right padding
    expect(cx2).toBeGreaterThan(cx1) // June after March
    expect(cx3).toBeGreaterThan(cx2) // September after June
  })

  /**
   * TEST 7: Click on document marker emits documentClick event
   */
  it('should emit documentClick event when marker is clicked', async () => {
    // Arrange
    wrapper = mount(TimelineDocuments, {
      props: {
        documents: mockDocuments,
        dateRange,
        width: 800,
        documentY: 50
      }
    })

    // Act
    const firstCircle = wrapper.findAll('circle.document-marker')[0]
    await firstCircle.trigger('click')

    // Assert
    expect(wrapper.emitted('documentClick')).toBeTruthy()
    expect(wrapper.emitted('documentClick')![0]).toEqual([mockDocuments[0]])
  })

  /**
   * TEST 8: Hover on document marker emits documentHover event
   */
  it('should emit documentHover event on mouseenter', async () => {
    // Arrange
    wrapper = mount(TimelineDocuments, {
      props: {
        documents: mockDocuments,
        dateRange,
        width: 800,
        documentY: 50
      }
    })

    // Act
    const firstCircle = wrapper.findAll('circle.document-marker')[0]
    await firstCircle.trigger('mouseenter')

    // Assert
    expect(wrapper.emitted('documentHover')).toBeTruthy()
    const emittedEvent = wrapper.emitted('documentHover')![0]
    expect(emittedEvent[0]).toEqual(mockDocuments[0]) // Document
    expect(emittedEvent[1]).toBeInstanceOf(MouseEvent) // Mouse event
  })

  /**
   * TEST 9: Mouse leave emits documentHover with null
   */
  it('should emit documentHover with null on mouseleave', async () => {
    // Arrange
    wrapper = mount(TimelineDocuments, {
      props: {
        documents: mockDocuments,
        dateRange,
        width: 800,
        documentY: 50
      }
    })

    // Act
    const firstCircle = wrapper.findAll('circle.document-marker')[0]
    await firstCircle.trigger('mouseleave')

    // Assert
    expect(wrapper.emitted('documentHover')).toBeTruthy()
    const emittedEvent = wrapper.emitted('documentHover')![0]
    expect(emittedEvent[0]).toBeNull()
    expect(emittedEvent[1]).toBeNull()
  })

  /**
   * TEST 10: Selected document has selected class
   */
  it('should add selected class to clicked document marker', async () => {
    // Arrange
    wrapper = mount(TimelineDocuments, {
      props: {
        documents: mockDocuments,
        dateRange,
        width: 800,
        documentY: 50
      }
    })

    // Act
    const secondCircle = wrapper.findAll('circle.document-marker')[1]
    await secondCircle.trigger('click')
    await wrapper.vm.$nextTick()

    // Assert
    expect(secondCircle.classes()).toContain('document-marker--selected')
  })

  /**
   * TEST 11: Reactivity - Updates when documents prop changes
   */
  it('should update markers when documents prop changes', async () => {
    // Arrange
    wrapper = mount(TimelineDocuments, {
      props: {
        documents: mockDocuments,
        dateRange,
        width: 800,
        documentY: 50
      }
    })

    expect(wrapper.findAll('circle.document-marker').length).toBe(3)

    // Act - Change documents
    const newDocuments: TimelineDocument[] = [
      {
        documentId: 'doc-4',
        title: 'New Document',
        documentType: 'clinical_note',
        date: '2023-05-01T10:00:00Z',
        author: 'Dr. Lee',
        concepts: []
      }
    ]

    await wrapper.setProps({ documents: newDocuments })

    // Assert
    expect(wrapper.findAll('circle.document-marker').length).toBe(1)
  })

  /**
   * TEST 12: Reactivity - Updates when dateRange prop changes
   */
  it('should reposition markers when dateRange changes', async () => {
    // Arrange
    wrapper = mount(TimelineDocuments, {
      props: {
        documents: mockDocuments,
        dateRange,
        width: 800,
        documentY: 50
      }
    })

    const initialCx = parseFloat(
      wrapper.findAll('circle.document-marker')[0].attributes('cx') || '0'
    )

    // Act - Change date range (zoom in)
    const newDateRange = {
      start: new Date('2023-03-01'),
      end: new Date('2023-06-30')
    }

    await wrapper.setProps({ dateRange: newDateRange })
    await wrapper.vm.$nextTick()

    // Assert - Position should change
    const newCx = parseFloat(
      wrapper.findAll('circle.document-marker')[0].attributes('cx') || '0'
    )

    expect(newCx).not.toBe(initialCx)
  })

  /**
   * TEST 13: Reactivity - Updates when width prop changes
   */
  it('should reposition markers when width changes', async () => {
    // Arrange
    wrapper = mount(TimelineDocuments, {
      props: {
        documents: mockDocuments,
        dateRange,
        width: 800,
        documentY: 50
      }
    })

    const initialCx = parseFloat(
      wrapper.findAll('circle.document-marker')[0].attributes('cx') || '0'
    )

    // Act - Change width
    await wrapper.setProps({ width: 1200 })
    await wrapper.vm.$nextTick()

    // Assert - Position should change (scale adjusted)
    const newCx = parseFloat(
      wrapper.findAll('circle.document-marker')[0].attributes('cx') || '0'
    )

    expect(newCx).not.toBe(initialCx)
  })

  /**
   * TEST 14: Empty documents array
   */
  it('should render no markers when documents array is empty', () => {
    // Arrange & Act
    wrapper = mount(TimelineDocuments, {
      props: {
        documents: [],
        dateRange,
        width: 800,
        documentY: 50
      }
    })

    // Assert
    const circles = wrapper.findAll('circle.document-marker')
    expect(circles.length).toBe(0)
  })

  /**
   * TEST 15: Default documentY prop value
   */
  it('should use default documentY value if not provided', () => {
    // Arrange & Act
    wrapper = mount(TimelineDocuments, {
      props: {
        documents: mockDocuments,
        dateRange,
        width: 800
        // documentY not provided - should default to 50
      }
    })

    // Assert
    const circles = wrapper.findAll('circle.document-marker')
    circles.forEach(circle => {
      expect(circle.attributes('cy')).toBe('50')
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })
})
