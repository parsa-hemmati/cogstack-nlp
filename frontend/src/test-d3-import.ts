/**
 * Test file to verify D3.js imports work correctly
 * This file can be deleted after verification
 */

import * as d3 from 'd3'

// Test basic D3 imports
const testD3Import = () => {
  // Test selection
  const selection = d3.select('body')

  // Test scale
  const xScale = d3.scaleTime()

  // Test axis
  const yAxis = d3.axisLeft(d3.scaleLinear())

  // Test data structures
  const data = [1, 2, 3, 4, 5]
  const sum = d3.sum(data)

  return { selection, xScale, yAxis, sum }
}

export { testD3Import }
