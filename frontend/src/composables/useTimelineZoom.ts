/**
 * useTimelineZoom Composable
 *
 * Manages zoom and pan state for the timeline visualization using D3 zoom behavior.
 * Provides reactive zoom/pan state, D3 zoom behavior integration, and helper methods.
 *
 * @phase 5.5 - Zoom, Pan, and Temporal Analysis
 */

import { ref, type Ref } from 'vue'
import { zoom, type ZoomBehavior, type D3ZoomEvent } from 'd3-zoom'
import { select } from 'd3-selection'

/**
 * Zoom state interface
 */
export interface ZoomState {
  scale: number // Current zoom scale (1 = 100%, 2 = 200%, etc.)
  translateX: number // Horizontal pan offset
  translateY: number // Vertical pan offset
  minScale: number // Minimum zoom level (0.1 = 10%)
  maxScale: number // Maximum zoom level (10 = 1000%)
}

/**
 * Default zoom state
 */
const DEFAULT_ZOOM_STATE: ZoomState = {
  scale: 1,
  translateX: 0,
  translateY: 0,
  minScale: 0.1,
  maxScale: 10
}

/**
 * D3 Zoom event type
 */
type ZoomEvent = D3ZoomEvent<SVGSVGElement, unknown>

/**
 * Composable for managing timeline zoom and pan
 *
 * @returns Zoom state and methods
 */
export function useTimelineZoom() {
  // Reactive zoom state
  const zoomState: Ref<ZoomState> = ref({ ...DEFAULT_ZOOM_STATE })

  // D3 zoom behavior instance
  const zoomBehavior: Ref<ZoomBehavior<SVGSVGElement, unknown> | null> = ref(null)

  // SVG element reference
  let svgElement: SVGSVGElement | null = null

  // Debounce timer for zoom events
  let debounceTimer: ReturnType<typeof setTimeout> | null = null

  /**
   * Handle D3 zoom event
   * Updates zoom state from D3 zoom transform
   *
   * @param event - D3 zoom event
   */
  const handleZoom = (event: ZoomEvent) => {
    // Clear previous debounce timer
    if (debounceTimer) {
      clearTimeout(debounceTimer)
    }

    // Debounce zoom updates to 16ms (60fps)
    debounceTimer = setTimeout(() => {
      const transform = event.transform

      zoomState.value = {
        ...zoomState.value,
        scale: transform.k,
        translateX: transform.x,
        translateY: transform.y
      }
    }, 16)
  }

  /**
   * Initialize D3 zoom behavior on SVG element
   *
   * @param svg - SVG element to attach zoom to
   * @param width - SVG width
   * @param height - SVG height
   */
  const initZoom = (svg: SVGSVGElement, width: number, height: number) => {
    svgElement = svg

    // Create D3 zoom behavior
    const zoomBehaviorInstance = zoom<SVGSVGElement, unknown>()
      .scaleExtent([zoomState.value.minScale, zoomState.value.maxScale])
      .translateExtent([
        [0, 0],
        [width, height]
      ])
      .on('zoom', handleZoom)

    // Apply zoom behavior to SVG
    select(svg).call(zoomBehaviorInstance)

    zoomBehavior.value = zoomBehaviorInstance
  }

  /**
   * Zoom in by factor of 1.5
   */
  const zoomIn = () => {
    if (!svgElement || !zoomBehavior.value) return

    const newScale = Math.min(
      zoomState.value.scale * 1.5,
      zoomState.value.maxScale
    )

    select(svgElement)
      .transition()
      .duration(300)
      .call(zoomBehavior.value.scaleTo, newScale)
  }

  /**
   * Zoom out by factor of 0.75
   */
  const zoomOut = () => {
    if (!svgElement || !zoomBehavior.value) return

    const newScale = Math.max(
      zoomState.value.scale * 0.75,
      zoomState.value.minScale
    )

    select(svgElement)
      .transition()
      .duration(300)
      .call(zoomBehavior.value.scaleTo, newScale)
  }

  /**
   * Reset zoom to default (scale=1, translate=(0,0))
   */
  const resetZoom = () => {
    if (!svgElement || !zoomBehavior.value) return

    select(svgElement)
      .transition()
      .duration(300)
      .call(
        zoomBehavior.value.transform,
        { k: 1, x: 0, y: 0 } as any // D3 identity transform
      )
  }

  /**
   * Zoom to specific scale at specific point
   *
   * @param scale - Target scale
   * @param centerX - X coordinate of zoom center
   * @param centerY - Y coordinate of zoom center
   */
  const zoomTo = (scale: number, centerX: number, centerY: number) => {
    if (!svgElement || !zoomBehavior.value) return

    // Clamp scale to min/max
    const clampedScale = Math.max(
      zoomState.value.minScale,
      Math.min(scale, zoomState.value.maxScale)
    )

    // Calculate transform to zoom to specific point
    const currentTransform = {
      k: zoomState.value.scale,
      x: zoomState.value.translateX,
      y: zoomState.value.translateY
    }

    const newTransform = {
      k: clampedScale,
      x: centerX - (centerX - currentTransform.x) * (clampedScale / currentTransform.k),
      y: centerY - (centerY - currentTransform.y) * (clampedScale / currentTransform.k)
    }

    select(svgElement)
      .transition()
      .duration(300)
      .call(zoomBehavior.value.transform, newTransform as any)
  }

  /**
   * Get current zoom level as percentage string
   *
   * @returns Zoom percentage (e.g., "100%", "150%")
   */
  const zoomPercentage = (): string => {
    return `${Math.round(zoomState.value.scale * 100)}%`
  }

  /**
   * Cleanup zoom behavior on component unmount
   */
  const destroy = () => {
    if (svgElement && zoomBehavior.value) {
      select(svgElement).on('.zoom', null)
    }

    svgElement = null
    zoomBehavior.value = null

    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }

    // Reset zoom state
    zoomState.value = { ...DEFAULT_ZOOM_STATE }
  }

  return {
    zoomState,
    zoomBehavior,
    initZoom,
    zoomIn,
    zoomOut,
    resetZoom,
    zoomTo,
    zoomPercentage,
    destroy
  }
}
