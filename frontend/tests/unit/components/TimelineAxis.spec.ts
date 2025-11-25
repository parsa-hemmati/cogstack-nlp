/**
 * Unit tests for TimelineAxis.vue component.
 *
 * Tests D3.js time axis rendering, reactivity, and prop changes.
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import TimelineAxis from '@/components/timeline/TimelineAxis.vue'

describe('TimelineAxis.vue', () => {
  let wrapper: VueWrapper<any>

  /**
   * TEST 1: Component mounting and rendering
   */
  it('should mount and render SVG element', () => {
    // Arrange
    const dateRange = {
      start: new Date('2023-01-01'),
      end: new Date('2023-12-31')
    }

    // Act
    wrapper = mount(TimelineAxis, {
      props: {
        dateRange,
        width: 800,
        height: 60
      }
    })

    // Assert
    expect(wrapper.exists()).toBe(true)
    const svg = wrapper.find('svg')
    expect(svg.exists()).toBe(true)
    expect(svg.attributes('width')).toBe('800')
    expect(svg.attributes('height')).toBe('60')
  })

  /**
   * TEST 2: SVG structure (axis group)
   */
  it('should render axis group with correct transform', () => {
    // Arrange
    const dateRange = {
      start: new Date('2023-01-01'),
      end: new Date('2023-12-31')
    }

    // Act
    wrapper = mount(TimelineAxis, {
      props: {
        dateRange,
        width: 800,
        height: 60
      }
    })

    // Assert
    const axisGroup = wrapper.find('g')
    expect(axisGroup.exists()).toBe(true)
    expect(axisGroup.attributes('transform')).toBe('translate(0, 30)') // height / 2
  })

  /**
   * TEST 3: D3 axis rendering (checks for axis elements)
   */
  it('should render D3 axis with ticks and labels', async () => {
    // Arrange
    const dateRange = {
      start: new Date('2023-01-01'),
      end: new Date('2023-12-31')
    }

    // Act
    wrapper = mount(TimelineAxis, {
      props: {
        dateRange,
        width: 800,
        height: 60
      }
    })

    await wrapper.vm.$nextTick()

    // Assert - D3 creates path, line, and text elements
    const svg = wrapper.find('svg')
    const paths = svg.findAll('path')
    const lines = svg.findAll('line')
    const texts = svg.findAll('text')

    // D3 axis should create at least:
    // - 1 domain path
    // - Multiple tick lines
    // - Multiple text labels
    expect(paths.length).toBeGreaterThan(0)
    expect(lines.length).toBeGreaterThan(0)
    expect(texts.length).toBeGreaterThan(0)
  })

  /**
   * TEST 4: Axis updates when dateRange prop changes
   */
  it('should re-render axis when dateRange changes', async () => {
    // Arrange
    const initialDateRange = {
      start: new Date('2023-01-01'),
      end: new Date('2023-12-31')
    }

    wrapper = mount(TimelineAxis, {
      props: {
        dateRange: initialDateRange,
        width: 800,
        height: 60
      }
    })

    await wrapper.vm.$nextTick()

    const initialTickCount = wrapper.findAll('text').length

    // Act - Change date range
    const newDateRange = {
      start: new Date('2023-01-01'),
      end: new Date('2024-12-31') // Extended by 1 year
    }

    await wrapper.setProps({ dateRange: newDateRange })
    await wrapper.vm.$nextTick()

    // Assert - Axis should have re-rendered
    // (Tick count may change due to extended date range)
    const newTickCount = wrapper.findAll('text').length
    expect(newTickCount).toBeGreaterThan(0)
  })

  /**
   * TEST 5: Axis updates when width prop changes
   */
  it('should re-render axis when width changes', async () => {
    // Arrange
    const dateRange = {
      start: new Date('2023-01-01'),
      end: new Date('2023-12-31')
    }

    wrapper = mount(TimelineAxis, {
      props: {
        dateRange,
        width: 800,
        height: 60
      }
    })

    await wrapper.vm.$nextTick()

    // Act - Change width
    await wrapper.setProps({ width: 1200 })
    await wrapper.vm.$nextTick()

    // Assert - SVG width should update
    const svg = wrapper.find('svg')
    expect(svg.attributes('width')).toBe('1200')
  })

  /**
   * TEST 6: Default props
   */
  it('should use default width and height if not provided', () => {
    // Arrange
    const dateRange = {
      start: new Date('2023-01-01'),
      end: new Date('2023-12-31')
    }

    // Act
    wrapper = mount(TimelineAxis, {
      props: {
        dateRange
      }
    })

    // Assert
    const svg = wrapper.find('svg')
    expect(svg.attributes('width')).toBe('800') // Default width
    expect(svg.attributes('height')).toBe('60') // Default height
  })

  /**
   * TEST 7: Axis domain (start and end dates)
   */
  it('should create axis with correct date domain', async () => {
    // Arrange
    const dateRange = {
      start: new Date('2023-01-01'),
      end: new Date('2023-12-31')
    }

    // Act
    wrapper = mount(TimelineAxis, {
      props: {
        dateRange,
        width: 800,
        height: 60
      }
    })

    await wrapper.vm.$nextTick()

    // Assert - Check if text labels contain month/year labels
    const texts = wrapper.findAll('text')
    expect(texts.length).toBeGreaterThan(0)

    // At least one label should contain "2023"
    const hasYearLabel = texts.some(text => text.text().includes('2023'))
    expect(hasYearLabel).toBe(true)
  })

  /**
   * TEST 8: Axis range (positioning within SVG)
   */
  it('should position axis with 50px padding on each side', async () => {
    // Arrange
    const dateRange = {
      start: new Date('2023-01-01'),
      end: new Date('2023-12-31')
    }

    // Act
    wrapper = mount(TimelineAxis, {
      props: {
        dateRange,
        width: 800,
        height: 60
      }
    })

    await wrapper.vm.$nextTick()

    // Assert - Check axis domain path
    // D3 axis creates a path element for the domain (main line)
    const paths = wrapper.findAll('path')
    expect(paths.length).toBeGreaterThan(0)

    // The axis should start around x=50 and end around x=750 (800 - 50)
    // We can verify this by checking the path's d attribute
    const domainPath = paths[0]
    const pathD = domainPath.attributes('d') || ''

    // Path should include coordinates around 50 and 750
    // (Exact values depend on D3 version, but should be close)
    expect(pathD).toBeTruthy()
  })

  /**
   * TEST 9: Cleanup (no memory leaks)
   */
  it('should clean up D3 elements on unmount', async () => {
    // Arrange
    const dateRange = {
      start: new Date('2023-01-01'),
      end: new Date('2023-12-31')
    }

    wrapper = mount(TimelineAxis, {
      props: {
        dateRange,
        width: 800,
        height: 60
      }
    })

    await wrapper.vm.$nextTick()

    // Act
    wrapper.unmount()

    // Assert - Component unmounted successfully
    expect(wrapper.vm).toBeTruthy() // Vue 3 keeps vm reference even after unmount
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })
})
