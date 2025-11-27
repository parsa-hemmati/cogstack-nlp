/**
 * Unit tests for EventDetailModal component (Task #004).
 *
 * Tests event detail display, meta-annotations, and source document linking.
 *
 * PRD Specification: .claude/ccpm/epics/timeline-module/004.md
 * Test Coverage: EventDetailModal component
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import EventDetailModal from '@/components/timeline/EventDetailModal.vue'
import type { TimelineEvent } from '@/types/timeline'

// Create Vuetify instance for tests
const vuetify = createVuetify({
  components,
  directives,
})

// Mock event data
const mockEvent: TimelineEvent = {
  id: 'event-123',
  event_type: 'diagnosis',
  date: '2023-06-15T10:30:00Z',
  title: 'Type 2 Diabetes Mellitus',
  description: 'Patient diagnosed with Type 2 Diabetes. HbA1c 8.5%. Started on Metformin 500mg BID.',
  specialty: 'endocrinology',
  provider: 'Dr. Jane Smith',
  location: 'Main Hospital - Endocrinology Clinic',
  concept_cui: 'C0011849',
  concept_name: 'Diabetes Mellitus',
  meta_annotations: {
    Negation: 'Affirmed',
    Temporality: 'Current',
    Experiencer: 'Patient',
    Certainty: 'High'
  },
  source_document_id: 'doc-456',
  confidence: 0.96
}

describe('EventDetailModal.vue', () => {
  let wrapper: VueWrapper<any>

  beforeEach(() => {
    wrapper = mount(EventDetailModal, {
      global: {
        plugins: [vuetify]
      },
      props: {
        modelValue: true,
        event: mockEvent
      }
    })
  })

  it('renders when modelValue is true', () => {
    expect(wrapper.find('.v-dialog').exists()).toBe(true)
  })

  it('does not render when modelValue is false', async () => {
    await wrapper.setProps({ modelValue: false })
    expect(wrapper.find('.v-dialog').isVisible()).toBe(false)
  })

  it('displays event title correctly', () => {
    const title = wrapper.find('.v-card-title')
    expect(title.text()).toContain('Type 2 Diabetes Mellitus')
  })

  it('displays event date correctly', () => {
    const dateElement = wrapper.find('[data-test="event-date"]')
    expect(dateElement.exists()).toBe(true)
    expect(dateElement.text()).toContain('2023-06-15')
  })

  it('displays event description', () => {
    const description = wrapper.find('[data-test="event-description"]')
    expect(description.text()).toContain('Patient diagnosed with Type 2 Diabetes')
    expect(description.text()).toContain('HbA1c 8.5%')
  })

  it('displays specialty', () => {
    const specialty = wrapper.find('[data-test="event-specialty"]')
    expect(specialty.text()).toContain('endocrinology')
  })

  it('displays provider', () => {
    const provider = wrapper.find('[data-test="event-provider"]')
    expect(provider.text()).toContain('Dr. Jane Smith')
  })

  it('displays location', () => {
    const location = wrapper.find('[data-test="event-location"]')
    expect(location.text()).toContain('Main Hospital - Endocrinology Clinic')
  })

  it('displays concept CUI and name', () => {
    const cui = wrapper.find('[data-test="concept-cui"]')
    const name = wrapper.find('[data-test="concept-name"]')

    expect(cui.text()).toContain('C0011849')
    expect(name.text()).toContain('Diabetes Mellitus')
  })

  it('displays confidence score', () => {
    const confidence = wrapper.find('[data-test="confidence-score"]')
    expect(confidence.text()).toContain('96')
  })

  describe('Meta-Annotation Indicators', () => {
    it('displays Negation badge as green for Affirmed', () => {
      const negationBadge = wrapper.find('[data-test="meta-negation"]')
      expect(negationBadge.exists()).toBe(true)
      expect(negationBadge.classes()).toContain('badge--affirmed')
      expect(negationBadge.text()).toContain('Affirmed')
    })

    it('displays Negation badge as red for Negated', async () => {
      await wrapper.setProps({
        event: {
          ...mockEvent,
          meta_annotations: {
            ...mockEvent.meta_annotations,
            Negation: 'Negated'
          }
        }
      })

      const negationBadge = wrapper.find('[data-test="meta-negation"]')
      expect(negationBadge.classes()).toContain('badge--negated')
      expect(negationBadge.text()).toContain('Negated')
    })

    it('displays Temporality icon for Current', () => {
      const temporalityIcon = wrapper.find('[data-test="meta-temporality"]')
      expect(temporalityIcon.exists()).toBe(true)
      expect(temporalityIcon.text()).toContain('Current')
    })

    it('displays Experiencer badge for Patient', () => {
      const experiencerBadge = wrapper.find('[data-test="meta-experiencer"]')
      expect(experiencerBadge.exists()).toBe(true)
      expect(experiencerBadge.text()).toContain('Patient')
    })

    it('displays Experiencer badge differently for Family', async () => {
      await wrapper.setProps({
        event: {
          ...mockEvent,
          meta_annotations: {
            ...mockEvent.meta_annotations,
            Experiencer: 'Family'
          }
        }
      })

      const experiencerBadge = wrapper.find('[data-test="meta-experiencer"]')
      expect(experiencerBadge.classes()).toContain('badge--family')
      expect(experiencerBadge.text()).toContain('Family')
    })

    it('displays Certainty stars based on level', () => {
      const certaintyStars = wrapper.findAll('[data-test="certainty-star"]')

      // High certainty = 5 stars
      expect(certaintyStars.length).toBe(5)
    })

    it('displays fewer stars for Medium certainty', async () => {
      await wrapper.setProps({
        event: {
          ...mockEvent,
          meta_annotations: {
            ...mockEvent.meta_annotations,
            Certainty: 'Medium'
          }
        }
      })

      const certaintyStars = wrapper.findAll('[data-test="certainty-star"]')
      // Medium certainty = 3 stars
      expect(certaintyStars.length).toBe(3)
    })
  })

  it('source document link works', async () => {
    const documentLink = wrapper.find('[data-test="source-document-link"]')
    expect(documentLink.exists()).toBe(true)
    expect(documentLink.attributes('href')).toContain('doc-456')

    // Should have target="_blank" to open in new tab
    expect(documentLink.attributes('target')).toBe('_blank')
  })

  it('shows related events section', () => {
    const relatedEvents = wrapper.find('[data-test="related-events"]')
    expect(relatedEvents.exists()).toBe(true)
  })

  it('displays related events correctly', async () => {
    await wrapper.setProps({
      event: mockEvent,
      relatedEvents: [
        {
          id: 'event-789',
          event_type: 'diagnosis',
          date: '2023-03-10T14:00:00Z',
          title: 'Type 2 Diabetes Mellitus',
          concept_cui: 'C0011849'
        }
      ]
    })

    const relatedEvent = wrapper.find('[data-test="related-event-0"]')
    expect(relatedEvent.exists()).toBe(true)
    expect(relatedEvent.text()).toContain('2023-03-10')
  })

  it('copy event details to clipboard works', async () => {
    // Mock clipboard API
    const writeTextMock = vi.fn()
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: writeTextMock
      },
      writable: true
    })

    const copyButton = wrapper.find('[data-test="copy-details-button"]')
    await copyButton.trigger('click')

    expect(writeTextMock).toHaveBeenCalled()

    const copiedText = writeTextMock.mock.calls[0][0]
    expect(copiedText).toContain('Type 2 Diabetes Mellitus')
    expect(copiedText).toContain('C0011849')
    expect(copiedText).toContain('2023-06-15')
  })

  it('shows copy success message after copying', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: writeTextMock
      },
      writable: true
    })

    const copyButton = wrapper.find('[data-test="copy-details-button"]')
    await copyButton.trigger('click')

    await wrapper.vm.$nextTick()

    const successMessage = wrapper.find('[data-test="copy-success-message"]')
    expect(successMessage.exists()).toBe(true)
    expect(successMessage.text()).toContain('Copied')
  })

  it('closes modal when close button clicked', async () => {
    const closeButton = wrapper.find('[data-test="close-button"]')
    await closeButton.trigger('click')

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0]).toEqual([false])
  })

  it('closes modal when clicking outside', async () => {
    const overlay = wrapper.find('.v-overlay__scrim')
    await overlay.trigger('click')

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0]).toEqual([false])
  })

  it('emits event-clicked when related event is clicked', async () => {
    await wrapper.setProps({
      event: mockEvent,
      relatedEvents: [
        {
          id: 'event-789',
          event_type: 'diagnosis',
          date: '2023-03-10T14:00:00Z',
          title: 'Type 2 Diabetes Mellitus',
          concept_cui: 'C0011849'
        }
      ]
    })

    const relatedEvent = wrapper.find('[data-test="related-event-0"]')
    await relatedEvent.trigger('click')

    expect(wrapper.emitted('event-clicked')).toBeTruthy()
    expect(wrapper.emitted('event-clicked')![0]).toEqual(['event-789'])
  })

  it('handles missing optional fields gracefully', async () => {
    const minimalEvent = {
      id: 'event-minimal',
      event_type: 'visit',
      date: '2023-05-01T09:00:00Z',
      title: 'Routine Checkup'
      // No description, specialty, provider, location, etc.
    }

    await wrapper.setProps({ event: minimalEvent })

    // Should not throw errors
    expect(wrapper.exists()).toBe(true)

    // Optional fields should not render if missing
    expect(wrapper.find('[data-test="event-description"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="event-specialty"]').exists()).toBe(false)
  })

  it('responsive design on mobile', async () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375
    })

    wrapper = mount(EventDetailModal, {
      global: {
        plugins: [vuetify]
      },
      props: {
        modelValue: true,
        event: mockEvent
      }
    })

    // Verify mobile-specific max-width
    const dialog = wrapper.findComponent({ name: 'v-dialog' })
    expect(dialog.props('maxWidth')).toBe('600')
  })
})
