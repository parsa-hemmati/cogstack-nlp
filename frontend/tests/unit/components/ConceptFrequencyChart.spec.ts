import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ConceptFrequencyChart from '@/components/ConceptFrequencyChart.vue'
import type { TimelineConcept } from '@/types/timeline'

// Mock D3 modules
vi.mock('d3', async () => {
  const actual = await vi.importActual('d3')
  return {
    ...actual,
    select: vi.fn(() => ({
      selectAll: vi.fn().mockReturnThis(),
      remove: vi.fn().mockReturnThis(),
      data: vi.fn().mockReturnThis(),
      join: vi.fn().mockReturnThis(),
      attr: vi.fn().mockReturnThis(),
      call: vi.fn().mockReturnThis(),
      style: vi.fn().mockReturnThis(),
      on: vi.fn().mockReturnThis()
    }))
  }
})

describe('ConceptFrequencyChart.vue', () => {
  const mockConcepts: TimelineConcept[] = [
    {
      conceptCui: 'C0011849',
      conceptName: 'Diabetes Mellitus',
      conceptType: 'condition',
      firstMentionDate: '2024-01-15',
      mentionCount: 3,
      mentions: [
        {
          conceptCui: 'C0011849',
          conceptName: 'Diabetes Mellitus',
          conceptType: 'condition',
          documentId: 'doc-1',
          date: '2024-01-15',
          confidence: 0.95,
          metaAnnotations: {
            Negation: 'Affirmed',
            Temporality: 'Recent',
            Experiencer: 'Patient',
            Certainty: 'High'
          },
          sentence: 'Patient diagnosed with diabetes.',
          isFirstMention: true
        },
        {
          conceptCui: 'C0011849',
          conceptName: 'Diabetes Mellitus',
          conceptType: 'condition',
          documentId: 'doc-2',
          date: '2024-02-20',
          confidence: 0.92,
          metaAnnotations: {
            Negation: 'Affirmed',
            Temporality: 'Current',
            Experiencer: 'Patient',
            Certainty: 'High'
          },
          sentence: 'Diabetes management ongoing.',
          isFirstMention: false
        },
        {
          conceptCui: 'C0011849',
          conceptName: 'Diabetes Mellitus',
          conceptType: 'condition',
          documentId: 'doc-3',
          date: '2024-03-10',
          confidence: 0.89,
          metaAnnotations: {
            Negation: 'Affirmed',
            Temporality: 'Current',
            Experiencer: 'Patient',
            Certainty: 'High'
          },
          sentence: 'Follow-up for diabetes.',
          isFirstMention: false
        }
      ]
    },
    {
      conceptCui: 'C0025598',
      conceptName: 'Metformin',
      conceptType: 'medication',
      firstMentionDate: '2024-02-20',
      mentionCount: 2,
      mentions: [
        {
          conceptCui: 'C0025598',
          conceptName: 'Metformin',
          conceptType: 'medication',
          documentId: 'doc-2',
          date: '2024-02-20',
          confidence: 0.98,
          metaAnnotations: {
            Negation: 'Affirmed',
            Temporality: 'Recent',
            Experiencer: 'Patient',
            Certainty: 'High'
          },
          sentence: 'Started on metformin 500mg.',
          isFirstMention: true
        },
        {
          conceptCui: 'C0025598',
          conceptName: 'Metformin',
          conceptType: 'medication',
          documentId: 'doc-3',
          date: '2024-03-10',
          confidence: 0.96,
          metaAnnotations: {
            Negation: 'Affirmed',
            Temporality: 'Current',
            Experiencer: 'Patient',
            Certainty: 'High'
          },
          sentence: 'Metformin continued.',
          isFirstMention: false
        }
      ]
    }
  ]

  const defaultProps = {
    concepts: mockConcepts,
    dateRange: {
      start: new Date('2024-01-01'),
      end: new Date('2024-04-01')
    },
    width: 800,
    height: 150,
    binSize: 'month' as const
  }

  /**
   * TEST 1: Frequency aggregation - mentions grouped by month
   */
  it('aggregates concept mentions by month correctly', () => {
    const wrapper = mount(ConceptFrequencyChart, {
      props: defaultProps
    })

    // Check that component computes aggregated data
    const vm = wrapper.vm as any
    expect(vm.aggregatedData).toBeDefined()
    expect(vm.aggregatedData.length).toBeGreaterThan(0)

    // January should have 1 mention (Diabetes)
    const jan2024 = vm.aggregatedData.find((d: any) => d.bin === '2024-01')
    expect(jan2024).toBeDefined()
    expect(jan2024.condition).toBe(1)
    expect(jan2024.total).toBe(1)

    // February should have 2 mentions (Diabetes + Metformin)
    const feb2024 = vm.aggregatedData.find((d: any) => d.bin === '2024-02')
    expect(feb2024).toBeDefined()
    expect(feb2024.condition).toBe(1)
    expect(feb2024.medication).toBe(1)
    expect(feb2024.total).toBe(2)

    // March should have 2 mentions (Diabetes + Metformin)
    const mar2024 = vm.aggregatedData.find((d: any) => d.bin === '2024-03')
    expect(mar2024).toBeDefined()
    expect(mar2024.condition).toBe(1)
    expect(mar2024.medication).toBe(1)
    expect(mar2024.total).toBe(2)
  })

  /**
   * TEST 2: Bar chart rendering - correct number of bars/bins
   */
  it('renders SVG chart with correct structure', () => {
    const wrapper = mount(ConceptFrequencyChart, {
      props: defaultProps
    })

    // Check SVG element exists
    const svg = wrapper.find('.frequency-chart-svg')
    expect(svg.exists()).toBe(true)
    expect(svg.attributes('width')).toBe('800')
    expect(svg.attributes('height')).toBe('150')

    // Check axis groups exist
    expect(wrapper.find('.x-axis').exists()).toBe(true)
    expect(wrapper.find('.y-axis').exists()).toBe(true)

    // Check bars group exists
    expect(wrapper.find('.bars').exists()).toBe(true)
  })

  /**
   * TEST 3: Concept types identified correctly
   */
  it('identifies unique concept types from data', () => {
    const wrapper = mount(ConceptFrequencyChart, {
      props: defaultProps
    })

    const vm = wrapper.vm as any
    expect(vm.conceptTypes).toContain('condition')
    expect(vm.conceptTypes).toContain('medication')
    expect(vm.conceptTypes.length).toBe(2)
  })

  /**
   * TEST 4: Tooltip display (not shown initially)
   */
  it('tooltip is hidden by default', () => {
    const wrapper = mount(ConceptFrequencyChart, {
      props: defaultProps
    })

    const tooltip = wrapper.find('.chart-tooltip')
    expect(tooltip.exists()).toBe(false)
  })

  /**
   * TEST 5: Bin size change (month → quarter)
   */
  it('re-aggregates data when bin size changes', async () => {
    const wrapper = mount(ConceptFrequencyChart, {
      props: defaultProps
    })

    const vmBefore = wrapper.vm as any
    const monthlyBins = vmBefore.aggregatedData.length

    // Change to quarterly bins
    await wrapper.setProps({ binSize: 'quarter' })

    const vmAfter = wrapper.vm as any
    const quarterlyBins = vmAfter.aggregatedData.length

    // Quarterly bins should be fewer than monthly bins
    expect(quarterlyBins).toBeLessThan(monthlyBins)

    // Check bin format changed to "YYYY-QN"
    const firstBin = vmAfter.aggregatedData[0]
    expect(firstBin.bin).toMatch(/^\d{4}-Q[1-4]$/)
  })

  /**
   * TEST 6: Empty data handling
   */
  it('handles empty concepts gracefully', () => {
    const wrapper = mount(ConceptFrequencyChart, {
      props: {
        ...defaultProps,
        concepts: []
      }
    })

    const vm = wrapper.vm as any
    expect(vm.aggregatedData).toEqual([])
    expect(vm.conceptTypes).toEqual([])

    // Should not crash or throw errors
    expect(wrapper.find('.frequency-chart-svg').exists()).toBe(true)
  })

  /**
   * TEST 7: Bin key generation and parsing
   */
  it('generates and parses bin keys correctly', () => {
    const wrapper = mount(ConceptFrequencyChart, {
      props: defaultProps
    })

    const vm = wrapper.vm as any

    // Month format
    const monthKey = vm.getBinKey(new Date('2024-03-15'))
    expect(monthKey).toBe('2024-03')
    const monthDate = vm.parseBinKey(monthKey)
    expect(monthDate.getFullYear()).toBe(2024)
    expect(monthDate.getMonth()).toBe(2) // March (0-indexed)

    // Quarter format (requires binSize='quarter')
    wrapper.setProps({ binSize: 'quarter' })
    const quarterKey = vm.getBinKey(new Date('2024-03-15'))
    expect(quarterKey).toBe('2024-Q1')
    const quarterDate = vm.parseBinKey(quarterKey)
    expect(quarterDate.getFullYear()).toBe(2024)
    expect(quarterDate.getMonth()).toBe(0) // Q1 starts in January

    // Year format (requires binSize='year')
    wrapper.setProps({ binSize: 'year' })
    const yearKey = vm.getBinKey(new Date('2024-03-15'))
    expect(yearKey).toBe('2024')
    const yearDate = vm.parseBinKey(yearKey)
    expect(yearDate.getFullYear()).toBe(2024)
  })
})
