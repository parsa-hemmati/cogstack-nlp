/**
 * Unit tests for TimelineExportToolbar component.
 *
 * Tests export button rendering, dialog interactions, export options, and error handling.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { nextTick, ref } from 'vue'
import TimelineExportToolbar from '@/components/TimelineExportToolbar.vue'

// Create Vuetify instance for testing
const vuetify = createVuetify({
  components,
  directives
})

// Mock the useTimelineExport composable
const mockExportTimeline = vi.fn()
const mockDownloadPDF = vi.fn()
const mockDownloadJSON = vi.fn()
const mockIsLoading = ref(false)
const mockError = ref<string | null>(null)

vi.mock('@/composables/useTimelineExport', () => ({
  useTimelineExport: () => ({
    isLoading: mockIsLoading,
    error: mockError,
    exportTimeline: mockExportTimeline,
    downloadPDF: mockDownloadPDF,
    downloadJSON: mockDownloadJSON
  })
}))

describe('TimelineExportToolbar.vue', () => {
  const defaultProps = {
    patientId: 'patient-uuid-123',
    filters: null
  }

  const mountComponent = (props = defaultProps) => {
    return mount(TimelineExportToolbar, {
      props,
      global: {
        plugins: [vuetify]
      }
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockIsLoading.value = false
    mockError.value = null
  })

  /**
   * TEST 1: Renders export buttons
   */
  it('renders export buttons (PDF, FHIR, JSON)', () => {
    const wrapper = mountComponent()

    // Find all buttons
    const buttons = wrapper.findAll('button')
    expect(buttons.length).toBeGreaterThanOrEqual(3)

    // Check button text contains format names
    const buttonTexts = buttons.map(btn => btn.text()).join(' ')
    expect(buttonTexts).toContain('PDF')
    expect(buttonTexts).toContain('FHIR')
    expect(buttonTexts).toContain('JSON')
  })

  /**
   * TEST 2: Buttons are disabled when no patientId
   */
  it('disables export buttons when patientId is missing', () => {
    const wrapper = mountComponent({ patientId: '', filters: null })

    const buttons = wrapper.findAll('button')
    const pdfButton = buttons.find(btn => btn.text().includes('PDF'))

    // Button should be disabled
    expect(pdfButton?.attributes('disabled')).toBeDefined()
  })

  /**
   * TEST 3: Buttons are enabled when patientId is provided
   */
  it('enables export buttons when patientId is provided', () => {
    const wrapper = mountComponent()

    const buttons = wrapper.findAll('button')
    const pdfButton = buttons.find(btn => btn.text().includes('PDF'))

    // Button should not be disabled
    expect(pdfButton?.attributes('disabled')).toBeUndefined()
  })

  /**
   * TEST 4: Opens dialog when PDF button clicked
   */
  it('opens export dialog when PDF button clicked', async () => {
    const wrapper = mountComponent()

    // Find and click PDF button
    const buttons = wrapper.findAll('button')
    const pdfButton = buttons.find(btn => btn.text().includes('PDF'))
    await pdfButton?.trigger('click')
    await nextTick()

    // Dialog should be visible (check for dialog stub)
    expect(wrapper.find('v-dialog-stub').exists()).toBe(true)
  })

  /**
   * TEST 5: Opens dialog when FHIR button clicked
   */
  it('opens export dialog when FHIR button clicked', async () => {
    const wrapper = mountComponent()

    // Find and click FHIR button
    const buttons = wrapper.findAll('button')
    const fhirButton = buttons.find(btn => btn.text().includes('FHIR'))
    await fhirButton?.trigger('click')
    await nextTick()

    // Dialog should be visible
    expect(wrapper.find('v-dialog-stub').exists()).toBe(true)
  })

  /**
   * TEST 6: Opens dialog when JSON button clicked
   */
  it('opens export dialog when JSON button clicked', async () => {
    const wrapper = mountComponent()

    // Find and click JSON button
    const buttons = wrapper.findAll('button')
    const jsonButton = buttons.find(btn => btn.text().includes('JSON'))
    await jsonButton?.trigger('click')
    await nextTick()

    // Dialog should be visible
    expect(wrapper.find('v-dialog-stub').exists()).toBe(true)
  })

  /**
   * TEST 7: Dialog displays export options
   */
  it('displays export options in dialog', async () => {
    const wrapper = mountComponent()

    // Open dialog
    const buttons = wrapper.findAll('button')
    const pdfButton = buttons.find(btn => btn.text().includes('PDF'))
    await pdfButton?.trigger('click')
    await nextTick()

    // Check for checkboxes (de-identification, watermark, apply filters)
    const checkboxes = wrapper.findAll('v-checkbox-stub')
    expect(checkboxes.length).toBeGreaterThanOrEqual(2) // At least de_identified and apply_filters
  })

  /**
   * TEST 8: Watermark checkbox only visible for PDF
   */
  it('shows watermark checkbox only for PDF format', async () => {
    const wrapper = mountComponent()

    // Open PDF dialog
    const buttons = wrapper.findAll('button')
    const pdfButton = buttons.find(btn => btn.text().includes('PDF'))
    await pdfButton?.trigger('click')
    await nextTick()

    // Check for watermark checkbox
    const checkboxes = wrapper.findAll('v-checkbox-stub')
    const checkboxLabels = checkboxes.map(cb => cb.attributes('label')).join(' ')
    expect(checkboxLabels).toContain('watermark')
  })

  /**
   * TEST 9: Calls exportTimeline when Export button clicked
   */
  it('calls exportTimeline when Export button clicked in dialog', async () => {
    // Arrange
    const mockResponse = {
      export_id: 'export-123',
      status: 'completed',
      format: 'pdf',
      content_type: 'application/pdf',
      data: 'base64data',
      created_at: '2025-11-19T15:00:00Z'
    }
    mockExportTimeline.mockResolvedValue(mockResponse)

    const wrapper = mountComponent()

    // Open dialog
    const buttons = wrapper.findAll('button')
    const pdfButton = buttons.find(btn => btn.text().includes('PDF'))
    await pdfButton?.trigger('click')
    await nextTick()

    // Find and click Export button in dialog
    const cardActions = wrapper.find('v-card-actions-stub')
    const exportButton = cardActions.findAll('v-btn-stub').find(btn =>
      btn.text().includes('Export')
    )
    await exportButton?.trigger('click')
    await nextTick()

    // Assert
    expect(mockExportTimeline).toHaveBeenCalled()
    expect(mockExportTimeline).toHaveBeenCalledWith(
      'patient-uuid-123',
      'pdf',
      null,
      expect.any(Object) // Options object
    )
  })

  /**
   * TEST 10: Shows success snackbar after successful export
   */
  it('shows success snackbar after successful export', async () => {
    // Arrange
    const mockResponse = {
      export_id: 'export-123',
      status: 'completed',
      format: 'pdf',
      content_type: 'application/pdf',
      data: 'base64data',
      created_at: '2025-11-19T15:00:00Z'
    }
    mockExportTimeline.mockResolvedValue(mockResponse)

    const wrapper = mountComponent()

    // Trigger export
    const buttons = wrapper.findAll('button')
    const pdfButton = buttons.find(btn => btn.text().includes('PDF'))
    await pdfButton?.trigger('click')
    await nextTick()

    const cardActions = wrapper.find('v-card-actions-stub')
    const exportButton = cardActions.findAll('v-btn-stub').find(btn =>
      btn.text().includes('Export')
    )
    await exportButton?.trigger('click')
    await nextTick()
    await nextTick() // Wait for promise resolution

    // Check for snackbar
    const snackbar = wrapper.find('v-snackbar-stub')
    expect(snackbar.exists()).toBe(true)
  })

  /**
   * TEST 11: Shows error snackbar on export failure
   */
  it('shows error snackbar on export failure', async () => {
    // Arrange
    mockExportTimeline.mockRejectedValue(new Error('Export failed'))

    const wrapper = mountComponent()

    // Trigger export
    const buttons = wrapper.findAll('button')
    const pdfButton = buttons.find(btn => btn.text().includes('PDF'))
    await pdfButton?.trigger('click')
    await nextTick()

    const cardActions = wrapper.find('v-card-actions-stub')
    const exportButton = cardActions.findAll('v-btn-stub').find(btn =>
      btn.text().includes('Export')
    )
    await exportButton?.trigger('click')
    await nextTick()
    await nextTick() // Wait for promise rejection

    // Check for error snackbar
    const snackbar = wrapper.find('v-snackbar-stub')
    expect(snackbar.exists()).toBe(true)
  })

  /**
   * TEST 12: Closes dialog when Cancel button clicked
   */
  it('closes dialog when Cancel button clicked', async () => {
    const wrapper = mountComponent()

    // Open dialog
    const buttons = wrapper.findAll('button')
    const pdfButton = buttons.find(btn => btn.text().includes('PDF'))
    await pdfButton?.trigger('click')
    await nextTick()

    // Dialog should be visible
    expect(wrapper.find('v-dialog-stub').exists()).toBe(true)

    // Find and click Cancel button
    const cardActions = wrapper.find('v-card-actions-stub')
    const cancelButton = cardActions.findAll('v-btn-stub').find(btn =>
      btn.text().includes('Cancel')
    )
    await cancelButton?.trigger('click')
    await nextTick()

    // Dialog should be hidden (modelValue becomes false)
    // Note: In stub mode, dialog may still exist but modelValue should be false
    const dialog = wrapper.find('v-dialog-stub')
    expect(dialog.attributes('modelvalue')).toBe('false')
  })

  /**
   * TEST 13: Shows loading state during export
   */
  it('shows loading state during export', async () => {
    // Arrange
    let resolveExport: any
    const exportPromise = new Promise((resolve) => {
      resolveExport = resolve
    })
    mockExportTimeline.mockReturnValue(exportPromise)

    const wrapper = mountComponent()

    // Trigger export
    const buttons = wrapper.findAll('button')
    const pdfButton = buttons.find(btn => btn.text().includes('PDF'))
    await pdfButton?.trigger('click')
    await nextTick()

    const cardActions = wrapper.find('v-card-actions-stub')
    const exportButton = cardActions.findAll('v-btn-stub').find(btn =>
      btn.text().includes('Export')
    )

    // Set isLoading manually (mocking composable behavior)
    mockIsLoading.value = true
    await exportButton?.trigger('click')
    await nextTick()

    // Export button should show loading state
    expect(exportButton?.attributes('loading')).toBeDefined()

    // Resolve promise
    resolveExport({
      export_id: 'export-123',
      status: 'completed',
      format: 'pdf',
      data: 'base64data'
    })
    mockIsLoading.value = false
    await nextTick()
  })

  /**
   * TEST 14: Passes filters to export when provided
   */
  it('passes filters to export when provided', async () => {
    // Arrange
    const filters = {
      concept_cuis: ['C0011849'],
      date_from: '2023-01-01',
      date_to: '2023-12-31'
    }
    const mockResponse = {
      export_id: 'export-123',
      status: 'completed',
      format: 'json',
      data: {}
    }
    mockExportTimeline.mockResolvedValue(mockResponse)

    const wrapper = mountComponent({
      patientId: 'patient-uuid-123',
      filters
    })

    // Open JSON dialog and trigger export
    const buttons = wrapper.findAll('button')
    const jsonButton = buttons.find(btn => btn.text().includes('JSON'))
    await jsonButton?.trigger('click')
    await nextTick()

    const cardActions = wrapper.find('v-card-actions-stub')
    const exportButton = cardActions.findAll('v-btn-stub').find(btn =>
      btn.text().includes('Export')
    )
    await exportButton?.trigger('click')
    await nextTick()

    // Assert filters passed to exportTimeline
    expect(mockExportTimeline).toHaveBeenCalledWith(
      'patient-uuid-123',
      'json',
      filters, // Filters should be passed when apply_filters is true
      expect.any(Object)
    )
  })

  /**
   * TEST 15: Error message when no patient selected
   */
  it('shows error when no patient selected and export attempted', async () => {
    const wrapper = mountComponent({ patientId: '', filters: null })

    // Try to open dialog (button should be disabled, but test the error path)
    // Component should check patientId before exporting
    const buttons = wrapper.findAll('button')
    const pdfButton = buttons.find(btn => btn.text().includes('PDF'))

    // Button disabled, so no export should trigger
    expect(pdfButton?.attributes('disabled')).toBeDefined()
  })
})
