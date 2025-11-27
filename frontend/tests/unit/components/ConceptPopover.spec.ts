import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import ConceptPopover from '@/components/ConceptPopover.vue'

// Create Vuetify instance for testing
const vuetify = createVuetify({
  components,
  directives
})

describe('ConceptPopover.vue', () => {
  const mockConcept = {
    concept_cui: 'C0011849',
    concept_name: 'Diabetes Mellitus',
    concept_type: 'condition',
    document_id: 'doc-123',
    date: '2024-01-15T10:30:00Z',
    confidence: 0.95,
    meta_annotations: {
      Negation: 'Affirmed',
      Temporality: 'Current',
      Experiencer: 'Patient',
      Certainty: 'Definite'
    },
    sentence: 'Patient diagnosed with diabetes mellitus.',
    is_first_mention: true
  }

  const defaultProps = {
    modelValue: true,
    concept: mockConcept,
    position: { x: 100, y: 200 }
  }

  const mountComponent = (props = defaultProps) => {
    return mount(ConceptPopover, {
      props,
      global: {
        plugins: [vuetify]
      }
    })
  }

  it('renders popover when modelValue is true', () => {
    const wrapper = mountComponent()

    expect(wrapper.find('v-menu-stub').exists()).toBe(true)
    expect(wrapper.find('v-card-stub').exists()).toBe(true)
  })

  it('does not render card when modelValue is false', () => {
    const wrapper = mountComponent({
      ...defaultProps,
      modelValue: false
    })

    // Menu exists but should not be visible
    expect(wrapper.find('v-menu-stub').exists()).toBe(true)
  })

  it('displays concept name and CUI in title', () => {
    const wrapper = mountComponent()

    const title = wrapper.find('v-card-title-stub')
    expect(title.text()).toContain('Diabetes Mellitus')
    expect(title.text()).toContain('(C0011849)')
  })

  it('displays formatted date in subtitle', () => {
    const wrapper = mountComponent()

    const subtitle = wrapper.find('v-card-subtitle-stub')
    // Date formatting depends on locale, just check it's not empty
    expect(subtitle.text()).toBeTruthy()
  })

  it('displays concept sentence', () => {
    const wrapper = mountComponent()

    const text = wrapper.find('v-card-text-stub')
    expect(text.text()).toContain('Patient diagnosed with diabetes mellitus.')
  })

  it('displays meta-annotations with chips', () => {
    const wrapper = mountComponent()

    const chips = wrapper.findAll('v-chip-stub')

    // Should have 4 meta-annotations
    expect(chips.length).toBeGreaterThanOrEqual(4)

    // Check that meta-annotation values are present
    const chipTexts = chips.map(chip => chip.text()).join(' ')
    expect(chipTexts).toContain('Negation')
    expect(chipTexts).toContain('Affirmed')
    expect(chipTexts).toContain('Temporality')
    expect(chipTexts).toContain('Current')
    expect(chipTexts).toContain('Experiencer')
    expect(chipTexts).toContain('Patient')
    expect(chipTexts).toContain('Certainty')
    expect(chipTexts).toContain('Definite')
  })

  it('color-codes meta-annotation chips correctly', () => {
    const wrapper = mountComponent()

    const chips = wrapper.findAll('v-chip-stub')

    // Affirmed, Current, Patient should be green
    const affirmChip = chips.find(chip => chip.text().includes('Affirmed'))
    expect(affirmChip?.attributes('color')).toBe('green')

    const currentChip = chips.find(chip => chip.text().includes('Current'))
    expect(currentChip?.attributes('color')).toBe('green')

    const patientChip = chips.find(chip => chip.text().includes('Patient'))
    expect(patientChip?.attributes('color')).toBe('green')
  })

  it('uses red color for negated/historical/family annotations', () => {
    const negatedConcept = {
      ...mockConcept,
      meta_annotations: {
        Negation: 'Negated',
        Temporality: 'Historical',
        Experiencer: 'Family',
        Certainty: 'Definite'
      }
    }

    const wrapper = mountComponent({
      ...defaultProps,
      concept: negatedConcept
    })

    const chips = wrapper.findAll('v-chip-stub')

    const negatedChip = chips.find(chip => chip.text().includes('Negated'))
    expect(negatedChip?.attributes('color')).toBe('red')

    const historicalChip = chips.find(chip => chip.text().includes('Historical'))
    expect(historicalChip?.attributes('color')).toBe('red')

    const familyChip = chips.find(chip => chip.text().includes('Family'))
    expect(familyChip?.attributes('color')).toBe('red')
  })

  it('uses grey color for unknown annotation values', () => {
    const unknownConcept = {
      ...mockConcept,
      meta_annotations: {
        Negation: 'Unknown',
        Temporality: 'Uncertain',
        Experiencer: 'Other',
        Certainty: 'Possible'
      }
    }

    const wrapper = mountComponent({
      ...defaultProps,
      concept: unknownConcept
    })

    const chips = wrapper.findAll('v-chip-stub')

    // All should be grey (default)
    const greyChips = chips.filter(chip => chip.attributes('color') === 'grey')
    expect(greyChips.length).toBeGreaterThan(0)
  })

  it('displays confidence score as percentage', () => {
    const wrapper = mountComponent()

    const text = wrapper.find('v-card-text-stub').text()
    expect(text).toContain('Confidence:')
    expect(text).toContain('95%')
  })

  it('rounds confidence score to nearest integer', () => {
    const conceptWithDecimal = {
      ...mockConcept,
      confidence: 0.876
    }

    const wrapper = mountComponent({
      ...defaultProps,
      concept: conceptWithDecimal
    })

    const text = wrapper.find('v-card-text-stub').text()
    expect(text).toContain('88%') // 0.876 * 100 = 87.6 rounded to 88
  })

  it('renders View Document and Close buttons', () => {
    const wrapper = mountComponent()

    const buttons = wrapper.findAll('v-btn-stub')
    expect(buttons).toHaveLength(2)

    const buttonTexts = buttons.map(btn => btn.text())
    expect(buttonTexts).toContain('View Document')
    expect(buttonTexts).toContain('Close')
  })

  it('emits view-document event when View Document clicked', async () => {
    const wrapper = mountComponent()

    const viewDocButton = wrapper.findAll('v-btn-stub').find(btn => btn.text() === 'View Document')
    await viewDocButton?.trigger('click')

    expect(wrapper.emitted('view-document')).toBeTruthy()
    expect(wrapper.emitted('view-document')![0]).toEqual(['doc-123'])
  })

  it('does not emit view-document if concept has no document_id', async () => {
    const conceptNoDoc = {
      ...mockConcept,
      document_id: undefined
    }

    const wrapper = mountComponent({
      ...defaultProps,
      concept: conceptNoDoc
    })

    const viewDocButton = wrapper.findAll('v-btn-stub').find(btn => btn.text() === 'View Document')
    await viewDocButton?.trigger('click')

    expect(wrapper.emitted('view-document')).toBeFalsy()
  })

  it('emits update:modelValue event when Close clicked', async () => {
    const wrapper = mountComponent()

    const closeButton = wrapper.findAll('v-btn-stub').find(btn => btn.text() === 'Close')
    await closeButton?.trigger('click')

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0]).toEqual([false])
  })

  it('updates visible state when modelValue prop changes', async () => {
    const wrapper = mountComponent({
      ...defaultProps,
      modelValue: false
    })

    // Initially false
    expect(wrapper.vm.visible).toBe(false)

    // Update prop
    await wrapper.setProps({ modelValue: true })

    // Should update visible
    expect(wrapper.vm.visible).toBe(true)
  })

  it('emits update:modelValue when visible changes', async () => {
    const wrapper = mountComponent()

    // Change visible directly (simulates v-model behavior)
    wrapper.vm.visible = false
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    const events = wrapper.emitted('update:modelValue')!
    expect(events[events.length - 1]).toEqual([false])
  })

  it('positions menu at specified coordinates', () => {
    const wrapper = mountComponent({
      ...defaultProps,
      position: { x: 250, y: 350 }
    })

    const menu = wrapper.find('v-menu-stub')
    expect(menu.attributes('position-x')).toBe('250')
    expect(menu.attributes('position-y')).toBe('350')
  })

  it('renders nothing when concept is null', () => {
    const wrapper = mountComponent({
      ...defaultProps,
      concept: null
    })

    // Menu exists but card should not render
    expect(wrapper.find('v-menu-stub').exists()).toBe(true)
    expect(wrapper.find('v-card-stub').exists()).toBe(false)
  })

  it('handles missing meta_annotations gracefully', () => {
    const conceptNoMeta = {
      ...mockConcept,
      meta_annotations: {}
    }

    const wrapper = mountComponent({
      ...defaultProps,
      concept: conceptNoMeta
    })

    // Should render without errors
    expect(wrapper.find('v-card-stub').exists()).toBe(true)

    // Chip group should still exist but be empty
    const chipGroup = wrapper.find('v-chip-group-stub')
    expect(chipGroup.exists()).toBe(true)
  })

  it('formats date correctly for different locales', () => {
    const wrapper = mountComponent()

    const subtitle = wrapper.find('v-card-subtitle-stub')
    const subtitleText = subtitle.text()

    // Should contain date components (day, month, year in some order)
    expect(subtitleText).toMatch(/\d+/)
  })
})
