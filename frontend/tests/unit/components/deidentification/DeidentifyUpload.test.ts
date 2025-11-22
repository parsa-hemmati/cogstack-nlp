/**
 * Tests for DeidentifyUpload component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import DeidentifyUpload from '@/components/deidentification/DeidentifyUpload.vue'
import { DeidentificationMethod } from '@/types/deidentification'

// Mock router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  })
}))

// Mock composable
const mockUploadCSV = vi.fn()
const mockSubmitBatch = vi.fn()

vi.mock('@/composables/useDeidentification', () => ({
  useDeidentification: () => ({
    uploadCSV: mockUploadCSV,
    submitBatch: mockSubmitBatch,
    isBatchUploading: false,
    batchUploadError: null,
    currentJob: null
  })
}))

const vuetify = createVuetify({
  components,
  directives
})

describe('DeidentifyUpload.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render upload form', () => {
    // Arrange & Act
    const wrapper = mount(DeidentifyUpload, {
      global: {
        plugins: [vuetify]
      }
    })

    // Assert
    expect(wrapper.text()).toContain('Upload Notes for De-identification')
    expect(wrapper.find('.v-file-input').exists()).toBe(true)
    expect(wrapper.find('.v-select').exists()).toBe(true)
  })

  it('should validate CSV file format', async () => {
    // Arrange
    const wrapper = mount(DeidentifyUpload, {
      global: {
        plugins: [vuetify]
      }
    })

    // Act - Create invalid file (too large)
    const largeFile = new File(
      [new ArrayBuffer(60 * 1024 * 1024)], // 60MB
      'large.csv',
      { type: 'text/csv' }
    )

    const vm = wrapper.vm as any
    vm.csvFile = [largeFile]
    vm.onCsvFileChange()

    // Assert
    expect(vm.csvValidation.valid).toBe(false)
    expect(vm.csvValidation.errors).toContain('CSV file exceeds 50MB limit')
  })

  it('should validate CSV file is not empty', async () => {
    // Arrange
    const wrapper = mount(DeidentifyUpload, {
      global: {
        plugins: [vuetify]
      }
    })

    // Act - Create empty file
    const emptyFile = new File([], 'empty.csv', { type: 'text/csv' })

    const vm = wrapper.vm as any
    vm.csvFile = [emptyFile]
    vm.onCsvFileChange()

    // Assert
    expect(vm.csvValidation.valid).toBe(false)
    expect(vm.csvValidation.errors).toContain('CSV file is empty')
  })

  it('should validate SQL query format', async () => {
    // Arrange
    const wrapper = mount(DeidentifyUpload, {
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Act - Valid SELECT query
    vm.sqlQuery = 'SELECT id, text FROM clinical_notes WHERE date > 2024-01-01'
    vm.onQueryChange()

    // Assert
    expect(vm.queryValidation.valid).toBe(true)
    expect(vm.queryValidation.errors).toHaveLength(0)
  })

  it('should reject destructive SQL operations', async () => {
    // Arrange
    const wrapper = mount(DeidentifyUpload, {
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Act - DELETE query (not allowed)
    vm.sqlQuery = 'DELETE FROM clinical_notes WHERE id = 1'
    vm.onQueryChange()

    // Assert
    expect(vm.queryValidation.valid).toBe(false)
    expect(vm.queryValidation.errors.some((e: string) => e.includes('DELETE'))).toBe(true)
  })

  it('should submit CSV batch and navigate to job status', async () => {
    // Arrange
    const mockJob = {
      job_id: '550e8400-e29b-41d4-a716-446655440000',
      status: 'pending',
      total_notes: 100,
      created_at: '2024-01-15T10:00:00Z',
      estimated_completion: '2024-01-15T11:00:00Z'
    }

    mockUploadCSV.mockResolvedValue(mockJob)

    const wrapper = mount(DeidentifyUpload, {
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Act - Set up valid CSV upload
    const validFile = new File(['note_id,text\n1,Patient data'], 'notes.csv', { type: 'text/csv' })
    vm.csvFile = [validFile]
    vm.onCsvFileChange()
    vm.method = DeidentificationMethod.REPLACEMENT
    vm.email = 'test@example.com'

    await vm.submitBatch()

    // Assert
    expect(mockUploadCSV).toHaveBeenCalledWith(
      validFile,
      DeidentificationMethod.REPLACEMENT,
      'test@example.com'
    )
    expect(mockPush).toHaveBeenCalledWith('/deidentify/jobs/550e8400-e29b-41d4-a716-446655440000')
  })

  it('should validate email format', async () => {
    // Arrange
    const wrapper = mount(DeidentifyUpload, {
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Act - Invalid email
    const invalidEmail = 'not-an-email'
    const validationResult = vm.emailRules[0](invalidEmail)

    // Assert
    expect(validationResult).toContain('Invalid email')

    // Act - Valid email
    const validEmail = 'researcher@example.com'
    const validResult = vm.emailRules[0](validEmail)

    // Assert
    expect(validResult).toBe(true)
  })

  it('should disable submit button when no file selected', async () => {
    // Arrange
    const wrapper = mount(DeidentifyUpload, {
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Assert
    expect(vm.canSubmit).toBe(false)
  })

  it('should enable submit button when valid CSV is selected', async () => {
    // Arrange
    const wrapper = mount(DeidentifyUpload, {
      global: {
        plugins: [vuetify]
      }
    })

    const vm = wrapper.vm as any

    // Act - Set up valid CSV
    const validFile = new File(['note_id,text\n1,Data'], 'notes.csv', { type: 'text/csv' })
    vm.csvFile = [validFile]
    vm.onCsvFileChange()

    // Assert
    expect(vm.canSubmit).toBe(true)
  })
})
