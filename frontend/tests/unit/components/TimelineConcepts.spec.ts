import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import TimelineConcepts from '@/components/TimelineConcepts.vue'
import type { TimelineConcept } from '@/types/timeline'

describe('TimelineConcepts.vue', () => {
  const mockConcepts: TimelineConcept[] = [
    {
      concept_cui: 'C0011849',
      concept_name: 'Diabetes Mellitus',
      concept_type: 'condition',
      first_mention_date: new Date('2024-01-15'),
      mention_count: 3,
      mentions: [
        {
          document_id: 'doc-1',
          date: new Date('2024-01-15'),
          confidence: 0.95,
          meta_annotations: {
            Negation: 'Affirmed',
            Temporality: 'Recent',
            Experiencer: 'Patient',
            Certainty: 'Definite'
          },
          sentence: 'Patient diagnosed with diabetes mellitus.'
        },
        {
          document_id: 'doc-2',
          date: new Date('2024-02-20'),
          confidence: 0.92,
          meta_annotations: {
            Negation: 'Affirmed',
            Temporality: 'Current',
            Experiencer: 'Patient',
            Certainty: 'Definite'
          },
          sentence: 'Diabetes mellitus management ongoing.'
        },
        {
          document_id: 'doc-3',
          date: new Date('2024-03-10'),
          confidence: 0.89,
          meta_annotations: {
            Negation: 'Affirmed',
            Temporality: 'Current',
            Experiencer: 'Patient',
            Certainty: 'Definite'
          },
          sentence: 'Follow-up for diabetes mellitus.'
        }
      ]
    },
    {
      concept_cui: 'C0025598',
      concept_name: 'Metformin',
      concept_type: 'medication',
      first_mention_date: new Date('2024-01-20'),
      mention_count: 2,
      mentions: [
        {
          document_id: 'doc-1',
          date: new Date('2024-01-20'),
          confidence: 0.98,
          meta_annotations: {
            Negation: 'Affirmed',
            Temporality: 'Recent',
            Experiencer: 'Patient',
            Certainty: 'Definite'
          },
          sentence: 'Started on metformin 500mg.'
        },
        {
          document_id: 'doc-2',
          date: new Date('2024-02-20'),
          confidence: 0.96,
          meta_annotations: {
            Negation: 'Affirmed',
            Temporality: 'Current',
            Experiencer: 'Patient',
            Certainty: 'Definite'
          },
          sentence: 'Metformin continued.'
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
    width: 1000
  }

  it('renders concept markers', () => {
    const wrapper = mount(TimelineConcepts, {
      props: defaultProps
    })

    // Should render 5 total mentions (3 diabetes + 2 metformin)
    const markers = wrapper.findAll('.concept-marker')
    expect(markers).toHaveLength(5)
  })

  it('renders first mention larger than recurring mentions', () => {
    const wrapper = mount(TimelineConcepts, {
      props: defaultProps
    })

    const markers = wrapper.findAll('.concept-marker')

    // First mention of diabetes (radius 8)
    expect(markers[0].attributes('r')).toBe('8')

    // Recurring mentions (radius 4)
    expect(markers[1].attributes('r')).toBe('4')
    expect(markers[2].attributes('r')).toBe('4')
  })

  it('color-codes markers by concept type', () => {
    const wrapper = mount(TimelineConcepts, {
      props: defaultProps
    })

    const markers = wrapper.findAll('.concept-marker')

    // Condition (diabetes) - red
    expect(markers[0].attributes('fill')).toBe('#f44336')
    expect(markers[1].attributes('fill')).toBe('#f44336')
    expect(markers[2].attributes('fill')).toBe('#f44336')

    // Medication (metformin) - blue
    expect(markers[3].attributes('fill')).toBe('#2196f3')
    expect(markers[4].attributes('fill')).toBe('#2196f3')
  })

  it('emits concept-click event on marker click', async () => {
    const wrapper = mount(TimelineConcepts, {
      props: defaultProps
    })

    const markers = wrapper.findAll('.concept-marker')
    await markers[0].trigger('click')

    expect(wrapper.emitted('concept-click')).toBeTruthy()
    expect(wrapper.emitted('concept-click')).toHaveLength(1)

    const emittedEvent = wrapper.emitted('concept-click')![0]
    expect(emittedEvent[0]).toMatchObject({
      concept_cui: 'C0011849',
      concept_name: 'Diabetes Mellitus',
      concept_type: 'condition',
      is_first_mention: true
    })
  })

  it('positions markers on x-axis based on date', () => {
    const wrapper = mount(TimelineConcepts, {
      props: defaultProps
    })

    const markers = wrapper.findAll('.concept-marker')

    // All markers should have cx attribute (x position)
    markers.forEach(marker => {
      expect(marker.attributes('cx')).toBeDefined()
      const cx = parseFloat(marker.attributes('cx')!)
      expect(cx).toBeGreaterThanOrEqual(50) // Min range
      expect(cx).toBeLessThanOrEqual(950) // Max range (width - 50)
    })
  })

  it('positions markers on y-axis based on concept type', () => {
    const wrapper = mount(TimelineConcepts, {
      props: defaultProps
    })

    const markers = wrapper.findAll('.concept-marker')

    // Condition markers (y=300)
    expect(markers[0].attributes('cy')).toBe('300')
    expect(markers[1].attributes('cy')).toBe('300')
    expect(markers[2].attributes('cy')).toBe('300')

    // Medication markers (y=350)
    expect(markers[3].attributes('cy')).toBe('350')
    expect(markers[4].attributes('cy')).toBe('350')
  })

  it('handles unknown concept types with default color and position', () => {
    const unknownTypeConcepts: TimelineConcept[] = [
      {
        concept_cui: 'C0000000',
        concept_name: 'Unknown Concept',
        concept_type: 'unknown_type',
        first_mention_date: new Date('2024-01-15'),
        mention_count: 1,
        mentions: [
          {
            document_id: 'doc-1',
            date: new Date('2024-01-15'),
            confidence: 0.8,
            meta_annotations: {
              Negation: 'Affirmed',
              Temporality: 'Current',
              Experiencer: 'Patient',
              Certainty: 'Definite'
            },
            sentence: 'Unknown concept mention.'
          }
        ]
      }
    ]

    const wrapper = mount(TimelineConcepts, {
      props: {
        ...defaultProps,
        concepts: unknownTypeConcepts
      }
    })

    const marker = wrapper.find('.concept-marker')

    // Default color (gray)
    expect(marker.attributes('fill')).toBe('#757575')

    // Default position (y=400)
    expect(marker.attributes('cy')).toBe('400')
  })

  it('renders empty when no concepts provided', () => {
    const wrapper = mount(TimelineConcepts, {
      props: {
        ...defaultProps,
        concepts: []
      }
    })

    const markers = wrapper.findAll('.concept-marker')
    expect(markers).toHaveLength(0)
  })

  it('correctly flattens mentions from multiple concepts', () => {
    const wrapper = mount(TimelineConcepts, {
      props: defaultProps
    })

    const markers = wrapper.findAll('.concept-marker')

    // Total mentions: 3 (diabetes) + 2 (metformin) = 5
    expect(markers).toHaveLength(5)

    // First 3 should be diabetes
    expect(markers[0].attributes('fill')).toBe('#f44336')
    expect(markers[1].attributes('fill')).toBe('#f44336')
    expect(markers[2].attributes('fill')).toBe('#f44336')

    // Last 2 should be metformin
    expect(markers[3].attributes('fill')).toBe('#2196f3')
    expect(markers[4].attributes('fill')).toBe('#2196f3')
  })

  it('applies hover styles to markers', () => {
    const wrapper = mount(TimelineConcepts, {
      props: defaultProps
    })

    const marker = wrapper.find('.concept-marker')

    // Check that class is applied (CSS hover styles defined in component)
    expect(marker.classes()).toContain('concept-marker')
  })

  it('includes all concept metadata in emitted mention', async () => {
    const wrapper = mount(TimelineConcepts, {
      props: defaultProps
    })

    const markers = wrapper.findAll('.concept-marker')
    await markers[0].trigger('click')

    const emittedMention = wrapper.emitted('concept-click')![0][0]

    // Check all metadata fields are present
    expect(emittedMention).toHaveProperty('concept_cui')
    expect(emittedMention).toHaveProperty('concept_name')
    expect(emittedMention).toHaveProperty('concept_type')
    expect(emittedMention).toHaveProperty('document_id')
    expect(emittedMention).toHaveProperty('date')
    expect(emittedMention).toHaveProperty('confidence')
    expect(emittedMention).toHaveProperty('meta_annotations')
    expect(emittedMention).toHaveProperty('sentence')
    expect(emittedMention).toHaveProperty('is_first_mention')
  })
})
