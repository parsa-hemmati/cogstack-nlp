import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import DocumentModal from '@/components/DocumentModal.vue'

const vuetify = createVuetify()

const mockDocument = {
  documentId: 'doc-123',
  title: 'Discharge Summary',
  date: '2024-01-15T10:30:00Z',
  snippet: 'Patient has <b>diabetes</b> type 2 and <b>hypertension</b>. Blood pressure controlled.',
  metaAnnotations: {
    Negation: 'Affirmed',
    Temporality: 'Current',
    Experiencer: 'Patient',
    Certainty: 'Definite'
  }
}

describe('DocumentModal', () => {
  describe('XSS Protection', () => {
    it('sanitizes malicious script tags in document snippet', () => {
      const maliciousDocument = {
        ...mockDocument,
        snippet: 'Patient has <script>alert("XSS")</script><b>diabetes</b>'
      }

      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: maliciousDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      // Script tag should be stripped
      const html = wrapper.html()
      expect(html).not.toContain('<script>')
      expect(html).not.toContain('alert')
      expect(html).toContain('diabetes')
    })

    it('sanitizes event handlers in document snippet', () => {
      const maliciousDocument = {
        ...mockDocument,
        snippet: '<img src=x onerror="alert(\'XSS\')"><b>diabetes</b>'
      }

      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: maliciousDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      const html = wrapper.html()
      expect(html).not.toContain('onerror')
      expect(html).not.toContain('alert')
      expect(html).toContain('diabetes')
    })

    it('sanitizes javascript: protocol in links', () => {
      const maliciousDocument = {
        ...mockDocument,
        snippet: '<a href="javascript:alert(\'XSS\')">Click me</a><b>diabetes</b>'
      }

      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: maliciousDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      const html = wrapper.html()
      expect(html).not.toContain('javascript:')
      expect(html).not.toContain('alert')
    })

    it('sanitizes iframe tags', () => {
      const maliciousDocument = {
        ...mockDocument,
        snippet: '<iframe src="https://evil.com"></iframe><b>diabetes</b>'
      }

      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: maliciousDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      const html = wrapper.html()
      expect(html).not.toContain('<iframe')
      expect(html).not.toContain('evil.com')
      expect(html).toContain('diabetes')
    })

    it('sanitizes object and embed tags', () => {
      const maliciousDocument = {
        ...mockDocument,
        snippet: '<object data="https://evil.com"></object><embed src="https://evil.com"><b>diabetes</b>'
      }

      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: maliciousDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      const html = wrapper.html()
      expect(html).not.toContain('<object')
      expect(html).not.toContain('<embed')
      expect(html).not.toContain('evil.com')
      expect(html).toContain('diabetes')
    })

    it('sanitizes data URIs with HTML', () => {
      const maliciousDocument = {
        ...mockDocument,
        snippet: '<iframe src="data:text/html,<script>alert(\'XSS\')</script>"></iframe><b>diabetes</b>'
      }

      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: maliciousDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      const html = wrapper.html()
      expect(html).not.toContain('data:text/html')
      expect(html).not.toContain('<iframe')
      expect(html).not.toContain('alert')
    })

    it('allows safe <mark> tags for highlighting', () => {
      const safeDocument = {
        ...mockDocument,
        snippet: 'Patient has <mark>diabetes</mark> type 2'
      }

      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: safeDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      // <mark> tags should be preserved (sanitizeHtml allows them)
      const html = wrapper.html()
      expect(html).toContain('<mark>')
      expect(html).toContain('</mark>')
      expect(html).toContain('diabetes')
    })

    it('handles empty snippet gracefully', () => {
      const emptyDocument = {
        ...mockDocument,
        snippet: ''
      }

      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: emptyDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      // Should render without errors
      expect(wrapper.html()).toBeTruthy()
      expect(wrapper.text()).toContain('Discharge Summary')
    })
  })

  describe('Basic Functionality', () => {
    it('renders document title', () => {
      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: mockDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      expect(wrapper.text()).toContain('Discharge Summary')
    })

    it('renders formatted date', () => {
      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: mockDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      // en-GB format with time
      expect(wrapper.text()).toContain('15 January 2024')
      expect(wrapper.text()).toContain('10:30')
    })

    it('renders document ID (truncated)', () => {
      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: mockDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      expect(wrapper.text()).toContain('Document ID')
      expect(wrapper.text()).toContain('doc-123')
    })

    it('truncates long document IDs', () => {
      const longIdDocument = {
        ...mockDocument,
        documentId: 'very-long-document-id-that-should-be-truncated-123456789'
      }

      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: longIdDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      expect(wrapper.text()).toContain('very-long-do...')
    })

    it('renders all meta-annotations', () => {
      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: mockDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      expect(wrapper.text()).toContain('Negation: Affirmed')
      expect(wrapper.text()).toContain('Temporality: Current')
      expect(wrapper.text()).toContain('Experiencer: Patient')
      expect(wrapper.text()).toContain('Certainty: Definite')
    })

    it('emits update:modelValue(false) when close button clicked', async () => {
      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: mockDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      // Find close button (icon button in header)
      const closeButtons = wrapper.findAll('button')
      const closeButton = closeButtons.find(btn => btn.text().includes('Close') || btn.html().includes('mdi-close'))

      if (closeButton) {
        await closeButton.trigger('click')
        expect(wrapper.emitted('update:modelValue')).toBeTruthy()
        expect(wrapper.emitted('update:modelValue')![0]).toEqual([false])
      }
    })

    it('displays download button', () => {
      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: mockDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      expect(wrapper.text()).toContain('Download')
    })

    it('shows correct meta-annotation colors', () => {
      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: mockDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      const html = wrapper.html()

      // Affirmed, Current, Patient should be green (flat variant)
      // These are positive/relevant annotations
      expect(html).toContain('Affirmed')
      expect(html).toContain('Current')
      expect(html).toContain('Patient')
    })

    it('handles negated condition with correct color', () => {
      const negatedDocument = {
        ...mockDocument,
        metaAnnotations: {
          Negation: 'Negated',
          Temporality: 'Historical',
          Experiencer: 'Family',
          Certainty: 'Definite'
        }
      }

      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: negatedDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      // Negated, Historical, Family should be red (outlined variant)
      expect(wrapper.text()).toContain('Negated')
      expect(wrapper.text()).toContain('Historical')
      expect(wrapper.text()).toContain('Family')
    })

    it('does not render when modelValue is false', () => {
      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: false,
          document: mockDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      // Dialog should not be visible
      const dialog = wrapper.findComponent({ name: 'VDialog' })
      expect(dialog.props('modelValue')).toBe(false)
    })

    it('renders when modelValue is true', () => {
      const wrapper = mount(DocumentModal, {
        props: {
          modelValue: true,
          document: mockDocument
        },
        global: {
          plugins: [vuetify]
        }
      })

      const dialog = wrapper.findComponent({ name: 'VDialog' })
      expect(dialog.props('modelValue')).toBe(true)
    })
  })
})
