/**
 * Timeline Chart Composable using D3.js
 * Provides utilities for rendering timeline visualizations
 */

import * as d3 from 'd3'
import type { TimelineResponse, TimelineDocument, TimelineConcept, ViewMode } from '@/types/timeline'

export interface TimelineChartOptions {
  width: number
  height: number
  margin: {
    top: number
    right: number
    bottom: number
    left: number
  }
}

export interface TimelineScale {
  x: d3.ScaleTime<number, number>
  y: d3.ScaleLinear<number, number>
}

export const DEFAULT_CHART_OPTIONS: TimelineChartOptions = {
  width: 1000,
  height: 500,
  margin: {
    top: 40,
    right: 40,
    bottom: 60,
    left: 80,
  },
}

export function useTimelineChart() {
  /**
   * Create SVG canvas
   */
  const createSvg = (
    container: HTMLElement,
    options: TimelineChartOptions = DEFAULT_CHART_OPTIONS
  ): d3.Selection<SVGSVGElement, unknown, null, undefined> => {
    // Remove any existing SVG
    d3.select(container).selectAll('svg').remove()

    // Create new SVG
    const svg = d3
      .select(container)
      .append('svg')
      .attr('width', options.width)
      .attr('height', options.height)
      .attr('viewBox', `0 0 ${options.width} ${options.height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')

    return svg
  }

  /**
   * Create time scale from timeline data
   */
  const createTimeScale = (
    data: TimelineResponse,
    width: number,
    margin: { left: number; right: number }
  ): d3.ScaleTime<number, number> => {
    const startDate = new Date(data.dateRange.start)
    const endDate = new Date(data.dateRange.end)

    // Add padding to date range (5% on each side)
    const padding = (endDate.getTime() - startDate.getTime()) * 0.05
    const paddedStart = new Date(startDate.getTime() - padding)
    const paddedEnd = new Date(endDate.getTime() + padding)

    return d3
      .scaleTime()
      .domain([paddedStart, paddedEnd])
      .range([margin.left, width - margin.right])
      .nice()
  }

  /**
   * Create y scale for vertical positioning
   */
  const createYScale = (
    height: number,
    margin: { top: number; bottom: number }
  ): d3.ScaleLinear<number, number> => {
    return d3
      .scaleLinear()
      .domain([0, 100])
      .range([height - margin.bottom, margin.top])
  }

  /**
   * Render X-axis with date labels
   */
  const renderXAxis = (
    svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
    scale: d3.ScaleTime<number, number>,
    height: number,
    margin: { bottom: number }
  ): void => {
    const axis = d3
      .axisBottom(scale)
      .ticks(10)
      .tickFormat((d) => d3.timeFormat('%b %Y')(d as Date))

    svg
      .append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0, ${height - margin.bottom})`)
      .call(axis)
      .selectAll('text')
      .attr('transform', 'rotate(-45)')
      .style('text-anchor', 'end')
      .style('font-size', '11px')
  }

  /**
   * Render Y-axis (optional for timeline)
   */
  const renderYAxis = (
    svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
    scale: d3.ScaleLinear<number, number>,
    margin: { left: number }
  ): void => {
    const axis = d3.axisLeft(scale).ticks(5)

    svg
      .append('g')
      .attr('class', 'y-axis')
      .attr('transform', `translate(${margin.left}, 0)`)
      .call(axis)
  }

  /**
   * Render document markers as circles
   */
  const renderDocuments = (
    svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
    documents: TimelineDocument[],
    xScale: d3.ScaleTime<number, number>,
    yPosition: number,
    onSelect?: (doc: TimelineDocument) => void
  ): void => {
    const documentGroup = svg
      .append('g')
      .attr('class', 'documents-layer')

    documentGroup
      .selectAll('.document-marker')
      .data(documents)
      .enter()
      .append('circle')
      .attr('class', 'document-marker')
      .attr('cx', (d) => xScale(new Date(d.date)))
      .attr('cy', yPosition)
      .attr('r', 8)
      .attr('fill', (d) => getDocumentColor(d.documentType))
      .attr('stroke', '#333')
      .attr('stroke-width', 1.5)
      .attr('cursor', 'pointer')
      .attr('opacity', 0.8)
      .on('mouseover', function (event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', 12)
          .attr('opacity', 1)

        // Show tooltip
        showTooltip(event, d.title, d.date)
      })
      .on('mouseout', function () {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', 8)
          .attr('opacity', 0.8)

        hideTooltip()
      })
      .on('click', (event, d) => {
        if (onSelect) onSelect(d)
      })
  }

  /**
   * Render concept event bars
   */
  const renderConcepts = (
    svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
    concepts: TimelineConcept[],
    xScale: d3.ScaleTime<number, number>,
    yPosition: number,
    barHeight: number,
    onSelect?: (concept: TimelineConcept) => void
  ): void => {
    const conceptGroup = svg
      .append('g')
      .attr('class', 'concepts-layer')

    // Stack concepts by type to avoid overlap
    const stackedConcepts = stackConceptsByType(concepts)

    Object.entries(stackedConcepts).forEach(([type, concepts], index) => {
      const typeY = yPosition + index * (barHeight + 5)

      conceptGroup
        .selectAll(`.concept-marker-${type}`)
        .data(concepts)
        .enter()
        .append('rect')
        .attr('class', `concept-marker concept-${type}`)
        .attr('x', (d) => xScale(new Date(d.firstMentioned)))
        .attr('y', typeY)
        .attr('width', (d) => {
          const start = xScale(new Date(d.firstMentioned))
          const end = xScale(new Date(d.lastMentioned))
          return Math.max(end - start, 4) // Minimum width of 4px
        })
        .attr('height', barHeight)
        .attr('fill', (d) => getConceptColor(d.conceptType))
        .attr('stroke', '#333')
        .attr('stroke-width', 1)
        .attr('opacity', 0.7)
        .attr('cursor', 'pointer')
        .attr('rx', 3)
        .on('mouseover', function (event, d) {
          d3.select(this)
            .transition()
            .duration(200)
            .attr('opacity', 1)
            .attr('stroke-width', 2)

          // Show tooltip
          showTooltip(event, d.preferredName, `${d.occurrenceCount} occurrence(s)`)
        })
        .on('mouseout', function () {
          d3.select(this)
            .transition()
            .duration(200)
            .attr('opacity', 0.7)
            .attr('stroke-width', 1)

          hideTooltip()
        })
        .on('click', (event, d) => {
          if (onSelect) onSelect(d)
        })
    })
  }

  /**
   * Stack concepts by type to avoid overlap
   */
  const stackConceptsByType = (concepts: TimelineConcept[]): Record<string, TimelineConcept[]> => {
    const stacked: Record<string, TimelineConcept[]> = {}

    concepts.forEach((concept) => {
      const type = concept.conceptType
      if (!stacked[type]) {
        stacked[type] = []
      }
      stacked[type].push(concept)
    })

    return stacked
  }

  /**
   * Get document color by type
   */
  const getDocumentColor = (type: string): string => {
    const colors: Record<string, string> = {
      clinical_note: '#3498db', // Blue
      lab_result: '#2ecc71', // Green
      discharge_summary: '#e74c3c', // Red
      radiology_report: '#f39c12', // Orange
      default: '#95a5a6', // Gray
    }
    return colors[type] || colors.default
  }

  /**
   * Get concept color by type
   */
  const getConceptColor = (type: string): string => {
    const colors: Record<string, string> = {
      condition: '#e74c3c', // Red
      medication: '#3498db', // Blue
      procedure: '#2ecc71', // Green
      observation: '#f39c12', // Orange
      default: '#9b59b6', // Purple
    }
    return colors[type] || colors.default
  }

  /**
   * Show tooltip
   */
  const showTooltip = (event: MouseEvent, title: string, subtitle: string): void => {
    const tooltip = d3
      .select('body')
      .append('div')
      .attr('class', 'timeline-tooltip')
      .style('position', 'absolute')
      .style('background-color', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('padding', '8px 12px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', '1000')
      .html(`<strong>${title}</strong><br/>${subtitle}`)

    tooltip
      .style('left', `${event.pageX + 10}px`)
      .style('top', `${event.pageY - 10}px`)
  }

  /**
   * Hide tooltip
   */
  const hideTooltip = (): void => {
    d3.selectAll('.timeline-tooltip').remove()
  }

  /**
   * Add zoom behavior
   */
  const addZoomBehavior = (
    svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
    xScale: d3.ScaleTime<number, number>,
    onZoom: (transform: d3.ZoomTransform) => void
  ): void => {
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([1, 10])
      .on('zoom', (event) => {
        onZoom(event.transform)
      })

    svg.call(zoom)
  }

  return {
    createSvg,
    createTimeScale,
    createYScale,
    renderXAxis,
    renderYAxis,
    renderDocuments,
    renderConcepts,
    addZoomBehavior,
    getDocumentColor,
    getConceptColor,
  }
}
