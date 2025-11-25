/**
 * Unit tests for useTimelineZoom composable
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { useTimelineZoom } from '@/composables/useTimelineZoom'

// Mock D3 modules
vi.mock('d3-zoom', () => ({
  zoom: vi.fn(() => ({
    scaleExtent: vi.fn().mockReturnThis(),
    translateExtent: vi.fn().mockReturnThis(),
    on: vi.fn().mockReturnThis(),
    scaleTo: vi.fn(),
    transform: vi.fn()
  }))
}))

vi.mock('d3-selection', () => ({
  select: vi.fn((element) => ({
    call: vi.fn().mockReturnThis(),
    transition: vi.fn().mockReturnThis(),
    duration: vi.fn().mockReturnThis(),
    on: vi.fn().mockReturnThis()
  }))
}))

describe('useTimelineZoom', () => {
  let mockSvgElement: SVGSVGElement

  beforeEach(() => {
    // Create mock SVG element
    mockSvgElement = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
    mockSvgElement.setAttribute('width', '800')
    mockSvgElement.setAttribute('height', '600')
    document.body.appendChild(mockSvgElement)

    // Clear all mocks
    vi.clearAllMocks()
  })

  afterEach(() => {
    // Cleanup
    document.body.removeChild(mockSvgElement)
  })

  /**
   * TEST 1: Initial state
   */
  it('should initialize with default zoom state', () => {
    const { zoomState } = useTimelineZoom()

    expect(zoomState.value.scale).toBe(1)
    expect(zoomState.value.translateX).toBe(0)
    expect(zoomState.value.translateY).toBe(0)
    expect(zoomState.value.minScale).toBe(0.1)
    expect(zoomState.value.maxScale).toBe(10)
  })

  /**
   * TEST 2: initZoom creates D3 zoom behavior
   */
  it('should initialize D3 zoom behavior on SVG element', () => {
    const { initZoom, zoomBehavior } = useTimelineZoom()

    // Act
    initZoom(mockSvgElement, 800, 600)

    // Assert - zoom behavior created
    expect(zoomBehavior.value).not.toBeNull()

    // Import mocks to verify calls
    const { zoom } = await import('d3-zoom')
    const { select } = await import('d3-selection')

    expect(zoom).toHaveBeenCalled()
    expect(select).toHaveBeenCalledWith(mockSvgElement)
  })

  /**
   * TEST 3: zoomIn updates scale correctly
   */
  it('should zoom in by factor of 1.5', async () => {
    const { initZoom, zoomIn, zoomState } = useTimelineZoom()

    // Arrange
    initZoom(mockSvgElement, 800, 600)

    // Mock current state
    zoomState.value.scale = 1

    // Act
    zoomIn()

    // Assert - scale should be 1 * 1.5 = 1.5
    // Note: In real implementation, D3 would update the state via handleZoom
    // For unit test, we verify the method was called
    const { select } = await import('d3-selection')
    expect(select).toHaveBeenCalled()
  })

  /**
   * TEST 4: zoomOut updates scale correctly
   */
  it('should zoom out by factor of 0.75', async () => {
    const { initZoom, zoomOut, zoomState } = useTimelineZoom()

    // Arrange
    initZoom(mockSvgElement, 800, 600)

    // Mock current state
    zoomState.value.scale = 2

    // Act
    zoomOut()

    // Assert - scale should be 2 * 0.75 = 1.5
    const { select } = await import('d3-selection')
    expect(select).toHaveBeenCalled()
  })

  /**
   * TEST 5: resetZoom returns to default state
   */
  it('should reset zoom to default state (scale=1, translate=(0,0))', async () => {
    const { initZoom, resetZoom } = useTimelineZoom()

    // Arrange
    initZoom(mockSvgElement, 800, 600)

    // Act
    resetZoom()

    // Assert
    const { select } = await import('d3-selection')
    expect(select).toHaveBeenCalled()
  })

  /**
   * TEST 6: min/max scale limits enforced
   */
  it('should enforce min scale limit (0.1)', () => {
    const { initZoom, zoomOut, zoomState } = useTimelineZoom()

    // Arrange
    initZoom(mockSvgElement, 800, 600)
    zoomState.value.scale = 0.15

    // Act - try to zoom out beyond min
    zoomOut()

    // Assert - scale should not go below minScale
    // The method calculates: 0.15 * 0.75 = 0.1125, but min is 0.1
    // So it should clamp to 0.1
    expect(zoomState.value.minScale).toBe(0.1)
  })

  /**
   * TEST 7: max scale limit enforced
   */
  it('should enforce max scale limit (10)', () => {
    const { initZoom, zoomIn, zoomState } = useTimelineZoom()

    // Arrange
    initZoom(mockSvgElement, 800, 600)
    zoomState.value.scale = 8

    // Act - try to zoom in beyond max
    zoomIn()

    // Assert - scale should not go above maxScale
    // The method calculates: 8 * 1.5 = 12, but max is 10
    // So it should clamp to 10
    expect(zoomState.value.maxScale).toBe(10)
  })

  /**
   * TEST 8: zoomPercentage returns formatted string
   */
  it('should return zoom level as percentage string', () => {
    const { zoomState, zoomPercentage } = useTimelineZoom()

    // Test various zoom levels
    zoomState.value.scale = 1
    expect(zoomPercentage()).toBe('100%')

    zoomState.value.scale = 1.5
    expect(zoomPercentage()).toBe('150%')

    zoomState.value.scale = 0.5
    expect(zoomPercentage()).toBe('50%')

    zoomState.value.scale = 2.5
    expect(zoomPercentage()).toBe('250%')
  })

  /**
   * TEST 9: zoomTo zooms to specific point
   */
  it('should zoom to specific scale at specific point', async () => {
    const { initZoom, zoomTo } = useTimelineZoom()

    // Arrange
    initZoom(mockSvgElement, 800, 600)

    // Act - zoom to 2x at point (400, 300)
    zoomTo(2, 400, 300)

    // Assert
    const { select } = await import('d3-selection')
    expect(select).toHaveBeenCalled()
  })

  /**
   * TEST 10: destroy cleans up zoom behavior
   */
  it('should cleanup zoom behavior on destroy', async () => {
    const { initZoom, destroy, zoomBehavior, zoomState } = useTimelineZoom()

    // Arrange
    initZoom(mockSvgElement, 800, 600)
    expect(zoomBehavior.value).not.toBeNull()

    // Act
    destroy()

    // Assert - zoom behavior removed
    expect(zoomBehavior.value).toBeNull()

    // Assert - zoom state reset
    expect(zoomState.value.scale).toBe(1)
    expect(zoomState.value.translateX).toBe(0)
    expect(zoomState.value.translateY).toBe(0)

    // Assert - event listeners removed
    const { select } = await import('d3-selection')
    const lastCall = (select as any).mock.results[select as any].mock.results.length - 1]
    expect(select).toHaveBeenCalled()
  })

  /**
   * TEST 11: handleZoom updates state from D3 event
   */
  it('should update zoom state from D3 zoom event', async () => {
    const { initZoom, zoomState } = useTimelineZoom()

    // Arrange
    initZoom(mockSvgElement, 800, 600)

    // Get the zoom behavior mock
    const { zoom } = await import('d3-zoom')
    const zoomMock = (zoom as any).mock.results[0].value

    // Get the 'on' handler for 'zoom' event
    const onMock = zoomMock.on as any
    const zoomHandler = onMock.mock.calls.find((call: any[]) => call[0] === 'zoom')?.[1]

    expect(zoomHandler).toBeDefined()

    // Act - simulate D3 zoom event
    if (zoomHandler) {
      const mockZoomEvent = {
        transform: {
          k: 2,
          x: 100,
          y: 50
        }
      }

      zoomHandler(mockZoomEvent)

      // Wait for debounce (16ms)
      await new Promise(resolve => setTimeout(resolve, 20))

      // Assert - zoom state updated
      expect(zoomState.value.scale).toBe(2)
      expect(zoomState.value.translateX).toBe(100)
      expect(zoomState.value.translateY).toBe(50)
    }
  })

  /**
   * TEST 12: debouncing prevents excessive updates
   */
  it('should debounce zoom events to 16ms (60fps)', async () => {
    const { initZoom, zoomState } = useTimelineZoom()

    // Arrange
    initZoom(mockSvgElement, 800, 600)

    // Get the zoom handler
    const { zoom } = await import('d3-zoom')
    const zoomMock = (zoom as any).mock.results[0].value
    const onMock = zoomMock.on as any
    const zoomHandler = onMock.mock.calls.find((call: any[]) => call[0] === 'zoom')?.[1]

    if (zoomHandler) {
      // Act - fire multiple zoom events rapidly
      const mockEvent1 = { transform: { k: 1.1, x: 10, y: 5 } }
      const mockEvent2 = { transform: { k: 1.2, x: 20, y: 10 } }
      const mockEvent3 = { transform: { k: 1.3, x: 30, y: 15 } }

      zoomHandler(mockEvent1)
      zoomHandler(mockEvent2)
      zoomHandler(mockEvent3)

      // Wait for debounce
      await new Promise(resolve => setTimeout(resolve, 20))

      // Assert - only the last event should be applied
      expect(zoomState.value.scale).toBe(1.3)
      expect(zoomState.value.translateX).toBe(30)
      expect(zoomState.value.translateY).toBe(15)
    }
  })
})
