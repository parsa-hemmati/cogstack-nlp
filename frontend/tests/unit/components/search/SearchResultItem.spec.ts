import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import SearchResultItem from '@/components/search/SearchResultItem.vue'

const vuetify = createVuetify()

describe('SearchResultItem', () => {
  describe('XSS Protection', () => {
    it('sanitizes malicious script tags in title highlights', () => {
      const maliciousResult = {
        id: '1',
        title: 'Patient Discharge',
        content: 'Content here',
        document_type: 'note',
        author: 'Dr. Smith',
        date: '2024-01-15',
        score: 85,
        highlights: {
          title: ['Patient <script>alert("XSS")</script>Discharge']
        }
      }

      const wrapper = mount(SearchResultItem, {
        props: {
          result: maliciousResult,
          index: 0
        },
        global: {
          plugins: [vuetify]
        }
      })

      // Script tag should be stripped, leaving only text
      const html = wrapper.html()
      expect(html).not.toContain('<script>')
      expect(html).not.toContain('alert')
      expect(html).toContain('Patient')
      expect(html).toContain('Discharge')
    })

    it('sanitizes malicious event handlers in content highlights', () => {
      const maliciousResult = {
        id: '2',
        title: 'Test Document',
        content: 'Content here',
        document_type: 'note',
        author: 'Dr. Jones',
        date: '2024-01-15',
        score: 75,
        highlights: {
          content: ['<img src=x onerror="alert(\'XSS\')">diabetes']
        }
      }

      const wrapper = mount(SearchResultItem, {
        props: {
          result: maliciousResult,
          index: 0
        },
        global: {
          plugins: [vuetify]
        }
      })

      // Event handler should be stripped
      const html = wrapper.html()
      expect(html).not.toContain('onerror')
      expect(html).not.toContain('alert')
      expect(html).toContain('diabetes')
    })

    it('allows safe <mark> tags in highlights', () => {
      const safeResult = {
        id: '3',
        title: 'Patient Discharge',
        content: 'Content here',
        document_type: 'note',
        author: 'Dr. Smith',
        date: '2024-01-15',
        score: 90,
        highlights: {
          title: ['Patient <mark>Discharge</mark>'],
          content: ['Patient has <mark>diabetes</mark> type 2']
        }
      }

      const wrapper = mount(SearchResultItem, {
        props: {
          result: safeResult,
          index: 0
        },
        global: {
          plugins: [vuetify]
        }
      })

      // <mark> tags should be preserved
      const html = wrapper.html()
      expect(html).toContain('<mark>')
      expect(html).toContain('</mark>')
      expect(html).toContain('Discharge')
      expect(html).toContain('diabetes')
    })

    it('sanitizes javascript: protocol in links', () => {
      const maliciousResult = {
        id: '4',
        title: 'Test',
        content: 'Content',
        document_type: 'note',
        author: 'Dr. Test',
        date: '2024-01-15',
        score: 80,
        highlights: {
          content: ['<a href="javascript:alert(\'XSS\')">Click me</a>']
        }
      }

      const wrapper = mount(SearchResultItem, {
        props: {
          result: maliciousResult,
          index: 0
        },
        global: {
          plugins: [vuetify]
        }
      })

      // javascript: protocol should be stripped
      const html = wrapper.html()
      expect(html).not.toContain('javascript:')
      expect(html).not.toContain('alert')
    })

    it('sanitizes data URIs with HTML', () => {
      const maliciousResult = {
        id: '5',
        title: 'Test',
        content: 'Content',
        document_type: 'note',
        author: 'Dr. Test',
        date: '2024-01-15',
        score: 70,
        highlights: {
          content: ['<iframe src="data:text/html,<script>alert(\'XSS\')</script>"></iframe>']
        }
      }

      const wrapper = mount(SearchResultItem, {
        props: {
          result: maliciousResult,
          index: 0
        },
        global: {
          plugins: [vuetify]
        }
      })

      // iframe and data URI should be stripped
      const html = wrapper.html()
      expect(html).not.toContain('<iframe')
      expect(html).not.toContain('data:text/html')
      expect(html).not.toContain('alert')
    })

    it('handles empty highlights gracefully', () => {
      const emptyResult = {
        id: '6',
        title: 'Test Document',
        content: 'Full content here',
        document_type: 'note',
        author: 'Dr. Smith',
        date: '2024-01-15',
        score: 85
      }

      const wrapper = mount(SearchResultItem, {
        props: {
          result: emptyResult,
          index: 0
        },
        global: {
          plugins: [vuetify]
        }
      })

      // Should render without errors
      expect(wrapper.text()).toContain('Test Document')
      expect(wrapper.text()).toContain('Full content here')
    })
  })

  describe('Basic Functionality', () => {
    const basicResult = {
      id: '1',
      title: 'Patient Discharge Summary',
      content: 'The patient was discharged on 2024-01-15',
      document_type: 'Discharge Summary',
      author: 'Dr. Smith',
      date: '2024-01-15',
      score: 85.5
    }

    it('renders title correctly', () => {
      const wrapper = mount(SearchResultItem, {
        props: {
          result: basicResult,
          index: 0
        },
        global: {
          plugins: [vuetify]
        }
      })

      expect(wrapper.text()).toContain('Patient Discharge Summary')
    })

    it('renders metadata (author, date, type)', () => {
      const wrapper = mount(SearchResultItem, {
        props: {
          result: basicResult,
          index: 0
        },
        global: {
          plugins: [vuetify]
        }
      })

      expect(wrapper.text()).toContain('Dr. Smith')
      expect(wrapper.text()).toContain('15 Jan 2024')
      expect(wrapper.text()).toContain('Discharge Summary')
    })

    it('renders relevance score', () => {
      const wrapper = mount(SearchResultItem, {
        props: {
          result: basicResult,
          index: 0
        },
        global: {
          plugins: [vuetify]
        }
      })

      expect(wrapper.text()).toContain('85.50')
    })

    it('emits click event when clicked', async () => {
      const wrapper = mount(SearchResultItem, {
        props: {
          result: basicResult,
          index: 0
        },
        global: {
          plugins: [vuetify]
        }
      })

      await wrapper.trigger('click')
      expect(wrapper.emitted('click')).toBeTruthy()
    })

    it('applies hover styles when hoverable=true', () => {
      const wrapper = mount(SearchResultItem, {
        props: {
          result: basicResult,
          index: 0,
          hoverable: true
        },
        global: {
          plugins: [vuetify]
        }
      })

      expect(wrapper.classes()).toContain('search-result-item--hover')
    })

    it('does not apply hover styles when hoverable=false', () => {
      const wrapper = mount(SearchResultItem, {
        props: {
          result: basicResult,
          index: 0,
          hoverable: false
        },
        global: {
          plugins: [vuetify]
        }
      })

      expect(wrapper.classes()).not.toContain('search-result-item--hover')
    })
  })
})
