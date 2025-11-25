import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import SearchResults from '@/components/search/SearchResults.vue'

const vuetify = createVuetify()

const mockResults = [
  {
    id: '1',
    title: 'Patient Discharge Summary',
    content: 'The patient was discharged on 2024-01-15 with improved condition...',
    document_type: 'Discharge Summary',
    author: 'Dr. Smith',
    date: '2024-01-15',
    score: 85.5,
    highlights: {
      title: ['Patient <mark>Discharge</mark> Summary'],
      content: ['The patient was <mark>discharged</mark> on 2024-01-15...']
    }
  },
  {
    id: '2',
    title: 'Clinical Notes - Follow-up',
    content: 'Follow-up appointment scheduled for next week...',
    document_type: 'Clinical Note',
    author: 'Dr. Jones',
    date: '2024-01-20',
    score: 72.3
  }
]

describe('SearchResults', () => {
  it('renders results count correctly', () => {
    const wrapper = mount(SearchResults, {
      props: {
        results: mockResults,
        total: 2,
        query: 'discharge'
      },
      global: {
        plugins: [vuetify],
        stubs: {
          SearchResultItem: true
        }
      }
    })

    expect(wrapper.text()).toContain('2 results')
    expect(wrapper.text()).toContain('for "discharge"')
  })

  it('renders singular result text for one result', () => {
    const wrapper = mount(SearchResults, {
      props: {
        results: [mockResults[0]],
        total: 1
      },
      global: {
        plugins: [vuetify],
        stubs: {
          SearchResultItem: true
        }
      }
    })

    expect(wrapper.text()).toContain('1 result')
  })

  it('shows loading skeletons when loading', () => {
    const wrapper = mount(SearchResults, {
      props: {
        results: [],
        loading: true
      },
      global: {
        plugins: [vuetify],
        stubs: {
          SearchResultItem: true
        }
      }
    })

    expect(wrapper.findAll('.v-skeleton-loader').length).toBeGreaterThan(0)
  })

  it('shows error alert when error prop provided', () => {
    const wrapper = mount(SearchResults, {
      props: {
        results: [],
        error: 'Failed to fetch results'
      },
      global: {
        plugins: [vuetify],
        stubs: {
          SearchResultItem: true
        }
      }
    })

    expect(wrapper.text()).toContain('Failed to fetch results')
  })

  it('shows empty state when no results', () => {
    const wrapper = mount(SearchResults, {
      props: {
        results: [],
        loading: false
      },
      global: {
        plugins: [vuetify],
        stubs: {
          SearchResultItem: true
        }
      }
    })

    expect(wrapper.text()).toContain('No results found')
  })

  it('emits update:sort when sort changes', async () => {
    const wrapper = mount(SearchResults, {
      props: {
        results: mockResults
      },
      global: {
        plugins: [vuetify],
        stubs: {
          SearchResultItem: true
        }
      }
    })

    const select = wrapper.findComponent({ name: 'VSelect' })
    await select.setValue('date_desc')

    expect(wrapper.emitted('update:sort')).toBeTruthy()
    expect(wrapper.emitted('update:sort')![0]).toEqual(['date_desc'])
  })

  it('emits update:page when page changes', async () => {
    const wrapper = mount(SearchResults, {
      props: {
        results: mockResults,
        total: 100,
        pageSize: 20
      },
      global: {
        plugins: [vuetify],
        stubs: {
          SearchResultItem: true
        }
      }
    })

    // Find pagination component
    const pagination = wrapper.findComponent({ name: 'VPagination' })
    await pagination.setValue(2)

    expect(wrapper.emitted('update:page')).toBeTruthy()
    expect(wrapper.emitted('update:page')![0]).toEqual([2])
  })

  it('calculates total pages correctly', () => {
    const wrapper = mount(SearchResults, {
      props: {
        results: mockResults,
        total: 47,
        pageSize: 10
      },
      global: {
        plugins: [vuetify],
        stubs: {
          SearchResultItem: true
        }
      }
    })

    // 47 results / 10 per page = 5 pages
    const pagination = wrapper.findComponent({ name: 'VPagination' })
    expect(pagination.props('length')).toBe(5)
  })

  it('renders SearchResultItem for each result', () => {
    const wrapper = mount(SearchResults, {
      props: {
        results: mockResults
      },
      global: {
        plugins: [vuetify],
        stubs: {
          SearchResultItem: true
        }
      }
    })

    const resultItems = wrapper.findAllComponents({ name: 'SearchResultItem' })
    expect(resultItems.length).toBe(2)
  })

  it('emits result-click when result item clicked', async () => {
    const wrapper = mount(SearchResults, {
      props: {
        results: mockResults
      },
      global: {
        plugins: [vuetify],
        stubs: {
          SearchResultItem: {
            template: '<div @click="$emit(\'click\')"></div>'
          }
        }
      }
    })

    const firstResult = wrapper.findAllComponents({ name: 'SearchResultItem' })[0]
    await firstResult.trigger('click')

    expect(wrapper.emitted('result-click')).toBeTruthy()
    expect(wrapper.emitted('result-click')![0]).toEqual([mockResults[0]])
  })

  it('does not show pagination when only one page', () => {
    const wrapper = mount(SearchResults, {
      props: {
        results: mockResults,
        total: 10,
        pageSize: 20
      },
      global: {
        plugins: [vuetify],
        stubs: {
          SearchResultItem: true
        }
      }
    })

    const pagination = wrapper.findComponent({ name: 'VPagination' })
    expect(pagination.exists()).toBe(false)
  })
})
