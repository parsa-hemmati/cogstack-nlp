/**
 * Unit tests for useTimelineExport composable.
 *
 * Tests export API calls, file downloads, loading/error states.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useTimelineExport } from '@/composables/useTimelineExport'

// Mock API client
const mockPost = vi.fn()
vi.mock('@/api/client', () => ({
  default: {
    post: (url: string, data: any) => mockPost(url, data)
  }
}))

describe('useTimelineExport Composable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  /**
   * TEST 1: Initial state
   */
  it('should initialize with correct default state', () => {
    // Arrange & Act
    const { isLoading, error } = useTimelineExport()

    // Assert
    expect(isLoading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  /**
   * TEST 2: Successful PDF export
   */
  it('should call API with correct parameters for PDF export', async () => {
    // Arrange
    const mockResponse = {
      data: {
        export_id: 'export-123',
        status: 'completed',
        format: 'pdf',
        content_type: 'application/pdf',
        data: 'JVBERi0xLjQKJdPr6eEK', // Base64 encoded PDF
        created_at: '2025-11-19T15:00:00Z'
      }
    }
    mockPost.mockResolvedValue(mockResponse)

    // Act
    const { exportTimeline, isLoading, error } = useTimelineExport()
    const result = await exportTimeline(
      'patient-uuid-123',
      'pdf',
      null,
      { watermark: true, de_identified: false }
    )

    // Assert
    expect(mockPost).toHaveBeenCalledWith(
      '/api/v1/timeline/patient-uuid-123/export',
      {
        format: 'pdf',
        filters: null,
        options: { watermark: true, de_identified: false }
      }
    )
    expect(result).toEqual(mockResponse.data)
    expect(isLoading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  /**
   * TEST 3: Successful FHIR export
   */
  it('should call API with correct parameters for FHIR export', async () => {
    // Arrange
    const mockResponse = {
      data: {
        export_id: 'export-456',
        status: 'completed',
        format: 'fhir',
        content_type: 'application/fhir+json',
        data: { resourceType: 'Composition' },
        created_at: '2025-11-19T15:00:00Z'
      }
    }
    mockPost.mockResolvedValue(mockResponse)

    // Act
    const { exportTimeline } = useTimelineExport()
    const result = await exportTimeline('patient-uuid-123', 'fhir', null, null)

    // Assert
    expect(mockPost).toHaveBeenCalledWith(
      '/api/v1/timeline/patient-uuid-123/export',
      {
        format: 'fhir',
        filters: null,
        options: null
      }
    )
    expect(result).toEqual(mockResponse.data)
  })

  /**
   * TEST 4: Successful JSON export
   */
  it('should call API with correct parameters for JSON export', async () => {
    // Arrange
    const mockResponse = {
      data: {
        export_id: 'export-789',
        status: 'completed',
        format: 'json',
        content_type: 'application/json',
        data: { patient_id: 'patient-uuid-123', concepts: [] },
        created_at: '2025-11-19T15:00:00Z'
      }
    }
    mockPost.mockResolvedValue(mockResponse)

    // Act
    const { exportTimeline } = useTimelineExport()
    const result = await exportTimeline('patient-uuid-123', 'json', null, null)

    // Assert
    expect(mockPost).toHaveBeenCalledWith(
      '/api/v1/timeline/patient-uuid-123/export',
      {
        format: 'json',
        filters: null,
        options: null
      }
    )
    expect(result).toEqual(mockResponse.data)
  })

  /**
   * TEST 5: Export with filters
   */
  it('should pass filters to API call', async () => {
    // Arrange
    const mockResponse = {
      data: {
        export_id: 'export-101',
        status: 'completed',
        format: 'pdf',
        content_type: 'application/pdf',
        data: 'base64data',
        created_at: '2025-11-19T15:00:00Z'
      }
    }
    mockPost.mockResolvedValue(mockResponse)

    const filters = {
      concept_cuis: ['C0011849'],
      date_from: '2023-01-01',
      date_to: '2023-12-31'
    }

    // Act
    const { exportTimeline } = useTimelineExport()
    await exportTimeline('patient-uuid-123', 'pdf', filters, null)

    // Assert
    expect(mockPost).toHaveBeenCalledWith(
      '/api/v1/timeline/patient-uuid-123/export',
      {
        format: 'pdf',
        filters: filters,
        options: null
      }
    )
  })

  /**
   * TEST 6: Loading state management
   */
  it('should set isLoading during export', async () => {
    // Arrange
    let resolvePromise: any
    const promise = new Promise((resolve) => {
      resolvePromise = resolve
    })
    mockPost.mockReturnValue(promise)

    // Act
    const { exportTimeline, isLoading } = useTimelineExport()
    expect(isLoading.value).toBe(false)

    const exportPromise = exportTimeline('patient-uuid-123', 'pdf', null, null)
    expect(isLoading.value).toBe(true)

    resolvePromise({ data: { export_id: 'export-123', status: 'completed' } })
    await exportPromise

    // Assert
    expect(isLoading.value).toBe(false)
  })

  /**
   * TEST 7: Error handling
   */
  it('should handle export errors', async () => {
    // Arrange
    const mockError = new Error('Export failed')
    ;(mockError as any).response = {
      data: { detail: 'Internal server error' }
    }
    mockPost.mockRejectedValue(mockError)

    // Act
    const { exportTimeline, isLoading, error } = useTimelineExport()

    try {
      await exportTimeline('patient-uuid-123', 'pdf', null, null)
    } catch (err) {
      // Expected to throw
    }

    // Assert
    expect(isLoading.value).toBe(false)
    expect(error.value).toBe('Internal server error')
  })

  /**
   * TEST 8: Error message extraction (no response)
   */
  it('should extract error message from exception', async () => {
    // Arrange
    const mockError = new Error('Network error')
    mockPost.mockRejectedValue(mockError)

    // Act
    const { exportTimeline, error } = useTimelineExport()

    try {
      await exportTimeline('patient-uuid-123', 'pdf', null, null)
    } catch (err) {
      // Expected to throw
    }

    // Assert
    expect(error.value).toBe('Network error')
  })

  /**
   * TEST 9: downloadPDF function
   */
  it('should download PDF from base64 data', () => {
    // Arrange
    const mockCreateObjectURL = vi.fn(() => 'blob:mock-url')
    const mockRevokeObjectURL = vi.fn()
    global.URL.createObjectURL = mockCreateObjectURL
    global.URL.revokeObjectURL = mockRevokeObjectURL

    const mockClick = vi.fn()
    const mockLink = {
      href: '',
      download: '',
      click: mockClick
    }
    vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any)

    const base64Data = 'JVBERi0xLjQKJdPr6eEK' // Valid base64
    const filename = 'timeline-test-2025-11-19.pdf'

    // Act
    const { downloadPDF } = useTimelineExport()
    downloadPDF(base64Data, filename)

    // Assert
    expect(document.createElement).toHaveBeenCalledWith('a')
    expect(mockCreateObjectURL).toHaveBeenCalled()
    expect(mockLink.download).toBe(filename)
    expect(mockClick).toHaveBeenCalled()
    expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
  })

  /**
   * TEST 10: downloadJSON function
   */
  it('should download JSON data', () => {
    // Arrange
    const mockCreateObjectURL = vi.fn(() => 'blob:mock-url')
    const mockRevokeObjectURL = vi.fn()
    global.URL.createObjectURL = mockCreateObjectURL
    global.URL.revokeObjectURL = mockRevokeObjectURL

    const mockClick = vi.fn()
    const mockLink = {
      href: '',
      download: '',
      click: mockClick
    }
    vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any)

    const jsonData = { patient_id: 'patient-123', concepts: [] }
    const filename = 'timeline-test-2025-11-19.json'

    // Act
    const { downloadJSON } = useTimelineExport()
    downloadJSON(jsonData, filename)

    // Assert
    expect(document.createElement).toHaveBeenCalledWith('a')
    expect(mockCreateObjectURL).toHaveBeenCalled()
    expect(mockLink.download).toBe(filename)
    expect(mockClick).toHaveBeenCalled()
    expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
  })

  /**
   * TEST 11: Default filename for downloadPDF
   */
  it('should use default filename when not provided', () => {
    // Arrange
    const mockCreateObjectURL = vi.fn(() => 'blob:mock-url')
    global.URL.createObjectURL = mockCreateObjectURL
    global.URL.revokeObjectURL = vi.fn()

    const mockLink = {
      href: '',
      download: '',
      click: vi.fn()
    }
    vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any)

    // Act
    const { downloadPDF } = useTimelineExport()
    downloadPDF('JVBERi0xLjQKJdPr6eEK')

    // Assert
    expect(mockLink.download).toBe('timeline.pdf')
  })

  /**
   * TEST 12: Default filename for downloadJSON
   */
  it('should use default filename for JSON when not provided', () => {
    // Arrange
    const mockCreateObjectURL = vi.fn(() => 'blob:mock-url')
    global.URL.createObjectURL = mockCreateObjectURL
    global.URL.revokeObjectURL = vi.fn()

    const mockLink = {
      href: '',
      download: '',
      click: vi.fn()
    }
    vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any)

    // Act
    const { downloadJSON } = useTimelineExport()
    downloadJSON({ data: 'test' })

    // Assert
    expect(mockLink.download).toBe('timeline.json')
  })
})
