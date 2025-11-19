import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import ConceptFilterSidebar from '@/components/ConceptFilterSidebar.vue'

const vuetify = createVuetify({
  components,
  directives
})

global.ResizeObserver = require('resize-observer-polyfill')

describe('ConceptFilterSidebar', () => {
  let wrapper: any

  beforeEach(() => {
    wrapper = mount(ConceptFilterSidebar, {
      props: {
        modelValue: true,
        patientId: 'patient-123'
      },
      global: {
        plugins: [vuetify]
      }
    })
  })

  it('renders the sidebar when modelValue is true', () => {
    expect(wrapper.find('.v-navigation-drawer').exists()).toBe(true)
    expect(wrapper.text()).toContain('Timeline Filters')
  })

  it('emits update:modelValue when close button clicked', async () => {
    const closeBtn = wrapper.findComponent({ name: 'VBtn' })
    await closeBtn.trigger('click')

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0]).toEqual([false])
  })

  it('renders concept search autocomplete', () => {
    const autocomplete = wrapper.findComponent({ name: 'VAutocomplete' })
    expect(autocomplete.exists()).toBe(true)
    expect(autocomplete.props('label')).toBe('Search concepts')
  })

  it('renders date range controls', () => {
    const dateFields = wrapper.findAllComponents({ name: 'VTextField' })
    const dateInputs = dateFields.filter((field: any) => field.props('type') === 'date')

    expect(dateInputs.length).toBe(2) // From and To date
    expect(dateInputs[0].props('label')).toBe('From date')
    expect(dateInputs[1].props('label')).toBe('To date')
  })

  it('renders date range presets', () => {
    const select = wrapper.findComponent({ name: 'VSelect' })
    expect(select.exists()).toBe(true)
    expect(select.props('label')).toBe('Quick select')
  })

  it('applies date preset when selected', async () => {
    const vm = wrapper.vm as any

    // Apply "Last 3 months" preset
    vm.applyDatePreset('3m')

    expect(vm.dateFrom).toBeTruthy()
    expect(vm.dateTo).toBeTruthy()

    // Apply "All time" preset
    vm.applyDatePreset('all')

    expect(vm.dateFrom).toBe('')
    expect(vm.dateTo).toBe('')
  })

  it('renders meta-annotation filters with correct defaults', () => {
    const vm = wrapper.vm as any

    expect(vm.metaNegation).toBe('Affirmed')
    expect(vm.metaExperiencer).toBe('Patient')
    expect(vm.metaTemporality).toEqual(['Current', 'Recent'])
    expect(vm.metaCertainty).toBeNull()
  })

  it('renders Negation chip group', () => {
    const chipGroups = wrapper.findAllComponents({ name: 'VChipGroup' })
    expect(chipGroups.length).toBeGreaterThan(0)

    const text = wrapper.text()
    expect(text).toContain('Affirmed')
    expect(text).toContain('Negated')
  })

  it('renders Experiencer chip group', () => {
    const text = wrapper.text()
    expect(text).toContain('Patient')
    expect(text).toContain('Family')
    expect(text).toContain('Other')
  })

  it('renders Temporality chip group', () => {
    const text = wrapper.text()
    expect(text).toContain('Current')
    expect(text).toContain('Recent')
    expect(text).toContain('Historical')
  })

  it('renders Certainty chip group', () => {
    const text = wrapper.text()
    expect(text).toContain('High')
    expect(text).toContain('Medium')
    expect(text).toContain('Low')
  })

  it('renders document type checkboxes', () => {
    const checkboxes = wrapper.findAllComponents({ name: 'VCheckbox' })
    expect(checkboxes.length).toBeGreaterThanOrEqual(5)

    const text = wrapper.text()
    expect(text).toContain('Clinical Notes')
    expect(text).toContain('Discharge Summaries')
    expect(text).toContain('Lab Reports')
    expect(text).toContain('Radiology Reports')
    expect(text).toContain('Pathology Reports')
  })

  it('renders Apply Filters button', () => {
    const buttons = wrapper.findAllComponents({ name: 'VBtn' })
    const applyBtn = buttons.find((btn: any) => btn.text().includes('Apply Filters'))
    expect(applyBtn).toBeTruthy()
  })

  it('renders Clear Filters button', () => {
    const buttons = wrapper.findAllComponents({ name: 'VBtn' })
    const clearBtn = buttons.find((btn: any) => btn.text().includes('Clear Filters'))
    expect(clearBtn).toBeTruthy()
  })

  it('renders Save as Preset button', () => {
    const buttons = wrapper.findAllComponents({ name: 'VBtn' })
    const saveBtn = buttons.find((btn: any) => btn.text().includes('Save as Preset'))
    expect(saveBtn).toBeTruthy()
  })

  it('emits filters-applied when Apply Filters clicked', async () => {
    const vm = wrapper.vm as any

    // Set some filter values
    vm.selectedConcepts = ['C0011849', 'C0020538']
    vm.dateFrom = '2023-01-01'
    vm.dateTo = '2023-12-31'
    vm.metaNegation = 'Affirmed'
    vm.metaExperiencer = 'Patient'
    vm.metaTemporality = ['Current', 'Recent']
    vm.selectedDocumentTypes = ['clinical_note', 'lab_result']

    // Click Apply Filters
    const buttons = wrapper.findAllComponents({ name: 'VBtn' })
    const applyBtn = buttons.find((btn: any) => btn.text().includes('Apply Filters'))
    await applyBtn!.trigger('click')

    expect(wrapper.emitted('filters-applied')).toBeTruthy()
    const emittedFilters = wrapper.emitted('filters-applied')![0][0]

    expect(emittedFilters.conceptCuis).toEqual(['C0011849', 'C0020538'])
    expect(emittedFilters.dateFrom).toBeInstanceOf(Date)
    expect(emittedFilters.dateTo).toBeInstanceOf(Date)
    expect(emittedFilters.metaAnnotations.Negation).toBe('Affirmed')
    expect(emittedFilters.metaAnnotations.Experiencer).toBe('Patient')
    expect(emittedFilters.metaAnnotations.Temporality).toEqual(['Current', 'Recent'])
    expect(emittedFilters.documentTypes).toEqual(['clinical_note', 'lab_result'])
  })

  it('closes sidebar when Apply Filters clicked', async () => {
    const buttons = wrapper.findAllComponents({ name: 'VBtn' })
    const applyBtn = buttons.find((btn: any) => btn.text().includes('Apply Filters'))
    await applyBtn!.trigger('click')

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0]).toEqual([false])
  })

  it('clears all filters when Clear Filters clicked', async () => {
    const vm = wrapper.vm as any

    // Set some filter values
    vm.selectedConcepts = ['C0011849', 'C0020538']
    vm.dateFrom = '2023-01-01'
    vm.dateTo = '2023-12-31'
    vm.metaNegation = 'Negated'
    vm.metaExperiencer = 'Family'
    vm.metaTemporality = ['Historical']
    vm.metaCertainty = 'Low'
    vm.selectedDocumentTypes = ['clinical_note', 'lab_result']

    // Click Clear Filters
    const buttons = wrapper.findAllComponents({ name: 'VBtn' })
    const clearBtn = buttons.find((btn: any) => btn.text().includes('Clear Filters'))
    await clearBtn!.trigger('click')

    // Check filters reset to defaults
    expect(vm.selectedConcepts).toEqual([])
    expect(vm.dateFrom).toBe('')
    expect(vm.dateTo).toBe('')
    expect(vm.metaNegation).toBe('Affirmed')
    expect(vm.metaExperiencer).toBe('Patient')
    expect(vm.metaTemporality).toEqual(['Current', 'Recent'])
    expect(vm.metaCertainty).toBeNull()
    expect(vm.selectedDocumentTypes).toEqual([])
  })

  it('emits filters-applied with default values when Clear Filters clicked', async () => {
    const buttons = wrapper.findAllComponents({ name: 'VBtn' })
    const clearBtn = buttons.find((btn: any) => btn.text().includes('Clear Filters'))
    await clearBtn!.trigger('click')

    expect(wrapper.emitted('filters-applied')).toBeTruthy()
    const emittedFilters = wrapper.emitted('filters-applied')![0][0]

    expect(emittedFilters.conceptCuis).toEqual([])
    expect(emittedFilters.dateFrom).toBeNull()
    expect(emittedFilters.dateTo).toBeNull()
    expect(emittedFilters.metaAnnotations.Negation).toBe('Affirmed')
    expect(emittedFilters.metaAnnotations.Experiencer).toBe('Patient')
    expect(emittedFilters.metaAnnotations.Temporality).toEqual(['Current', 'Recent'])
    expect(emittedFilters.documentTypes).toEqual([])
  })

  it('removeConcept removes concept from selected list', async () => {
    const vm = wrapper.vm as any

    vm.selectedConcepts = ['C0011849', 'C0020538', 'C0004238']
    vm.removeConcept('C0020538')

    expect(vm.selectedConcepts).toEqual(['C0011849', 'C0004238'])
  })

  it('does not include Certainty in metaAnnotations if null', async () => {
    const vm = wrapper.vm as any

    vm.selectedConcepts = []
    vm.metaCertainty = null

    const buttons = wrapper.findAllComponents({ name: 'VBtn' })
    const applyBtn = buttons.find((btn: any) => btn.text().includes('Apply Filters'))
    await applyBtn!.trigger('click')

    const emittedFilters = wrapper.emitted('filters-applied')![0][0]
    expect(emittedFilters.metaAnnotations.Certainty).toBeUndefined()
  })

  it('includes Certainty in metaAnnotations if set', async () => {
    const vm = wrapper.vm as any

    vm.metaCertainty = 'High'

    const buttons = wrapper.findAllComponents({ name: 'VBtn' })
    const applyBtn = buttons.find((btn: any) => btn.text().includes('Apply Filters'))
    await applyBtn!.trigger('click')

    const emittedFilters = wrapper.emitted('filters-applied')![0][0]
    expect(emittedFilters.metaAnnotations.Certainty).toBe('High')
  })

  it('shows information tooltip for meta-annotations', () => {
    const tooltip = wrapper.findComponent({ name: 'VTooltip' })
    expect(tooltip.exists()).toBe(true)
  })

  it('debounces concept search input', async () => {
    vi.useFakeTimers()
    const vm = wrapper.vm as any

    vm.conceptSearch = 'dia'

    // Before debounce timeout
    expect(vm.loadingConcepts).toBe(false)
    expect(vm.conceptSuggestions.length).toBe(0)

    // After debounce timeout
    vi.advanceTimersByTime(300)
    await wrapper.vm.$nextTick()

    expect(vm.conceptSuggestions.length).toBeGreaterThan(0)

    vi.useRealTimers()
  })

  it('filters concept suggestions based on search input', async () => {
    vi.useFakeTimers()
    const vm = wrapper.vm as any

    vm.conceptSearch = 'diabetes'

    vi.advanceTimersByTime(300)
    await wrapper.vm.$nextTick()

    const suggestions = vm.conceptSuggestions
    expect(suggestions.length).toBeGreaterThan(0)
    expect(suggestions.every((s: any) => s.name.toLowerCase().includes('diabetes'))).toBe(true)

    vi.useRealTimers()
  })

  it('does not search if input is less than 2 characters', async () => {
    const vm = wrapper.vm as any

    vm.conceptSearch = 'a'
    await wrapper.vm.$nextTick()

    expect(vm.conceptSuggestions.length).toBe(0)
  })

  it('handles Save as Preset click (logs for now)', async () => {
    const consoleSpy = vi.spyOn(console, 'log')

    const buttons = wrapper.findAllComponents({ name: 'VBtn' })
    const saveBtn = buttons.find((btn: any) => btn.text().includes('Save as Preset'))
    await saveBtn!.trigger('click')

    expect(consoleSpy).toHaveBeenCalledWith('Save preset clicked - to be implemented in Task 5.4.6')

    consoleSpy.mockRestore()
  })
})
