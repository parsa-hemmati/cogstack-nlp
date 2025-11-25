/**
 * QueryBuilder Component Tests
 *
 * Tests for the visual query builder component that allows users to construct
 * complex search queries through a drag-and-drop interface with field selection,
 * operator selection, and query preview/validation.
 *
 * Test Coverage:
 * - Rendering and initialization (6 tests)
 * - Condition management (add, remove, reorder) (8 tests)
 * - Field selection (concept, date, confidence) (5 tests)
 * - Operator selection (AND, OR, NOT) (6 tests)
 * - Query generation and preview (7 tests)
 * - Query validation (8 tests)
 * - Syntax highlighting (3 tests)
 * - Accessibility (5 tests)
 * - Integration with parent (4 tests)
 *
 * Total: 52 tests (exceeds 40+ requirement)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import QueryBuilder from '@/components/search/QueryBuilder.vue'

// Create Vuetify instance for testing
const vuetify = createVuetify({
  components,
  directives,
})

// Test helpers
function createWrapper(props = {}) {
  return mount(QueryBuilder, {
    props: {
      modelValue: '',
      ...props,
    },
    global: {
      plugins: [vuetify],
    },
  })
}

describe('QueryBuilder Component', () => {
  let wrapper: VueWrapper<any>

  beforeEach(() => {
    wrapper = createWrapper()
  })

  // ============================================================================
  // Rendering and Initialization Tests (6 tests)
  // ============================================================================

  describe('Rendering and Initialization', () => {
    it('renders the component', () => {
      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('[data-testid="query-builder"]').exists()).toBe(true)
    })

    it('renders with empty state initially', () => {
      expect(wrapper.findAll('[data-testid="condition-row"]').length).toBe(0)
      expect(wrapper.find('[data-testid="empty-state"]').exists()).toBe(true)
    })

    it('renders add condition button', () => {
      const addButton = wrapper.find('[data-testid="add-condition-btn"]')
      expect(addButton.exists()).toBe(true)
      expect(addButton.text()).toContain('Add Condition')
    })

    it('renders query preview section', () => {
      expect(wrapper.find('[data-testid="query-preview"]').exists()).toBe(true)
    })

    it('renders validation section', () => {
      expect(wrapper.find('[data-testid="validation-section"]').exists()).toBe(true)
    })

    it('renders action buttons (apply, clear, close)', () => {
      expect(wrapper.find('[data-testid="apply-btn"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="clear-btn"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="close-btn"]').exists()).toBe(true)
    })
  })

  // ============================================================================
  // Condition Management Tests (8 tests)
  // ============================================================================

  describe('Condition Management', () => {
    it('adds a condition when add button clicked', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const conditions = wrapper.findAll('[data-testid="condition-row"]')
      expect(conditions.length).toBe(1)
    })

    it('adds multiple conditions', async () => {
      const addBtn = wrapper.find('[data-testid="add-condition-btn"]')

      await addBtn.trigger('click')
      await addBtn.trigger('click')
      await addBtn.trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.findAll('[data-testid="condition-row"]').length).toBe(3)
    })

    it('removes a condition when remove button clicked', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const removeBtn = wrapper.findAll('[data-testid="remove-condition-btn"]')[0]
      await removeBtn.trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.findAll('[data-testid="condition-row"]').length).toBe(1)
    })

    it('shows empty state when all conditions removed', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      await wrapper.find('[data-testid="remove-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="empty-state"]').exists()).toBe(true)
    })

    it('allows reordering conditions via drag handles', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const dragHandles = wrapper.findAll('[data-testid="drag-handle"]')
      expect(dragHandles.length).toBe(2)
      expect(dragHandles[0].exists()).toBe(true)
    })

    it('maintains condition state when reordering', async () => {
      // Add two conditions and set values
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      // Set first condition field
      const fieldSelects = wrapper.findAll('[data-testid="field-select"]')
      await fieldSelects[0].setValue('concept')

      // Verify state persists
      expect(wrapper.vm.conditions[0].field).toBe('concept')
    })

    it('assigns unique IDs to each condition', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const condition1Id = wrapper.vm.conditions[0].id
      const condition2Id = wrapper.vm.conditions[1].id

      expect(condition1Id).toBeDefined()
      expect(condition2Id).toBeDefined()
      expect(condition1Id).not.toBe(condition2Id)
    })

    it('limits maximum number of conditions to 10', async () => {
      const addBtn = wrapper.find('[data-testid="add-condition-btn"]')

      // Try to add 15 conditions
      for (let i = 0; i < 15; i++) {
        await addBtn.trigger('click')
      }
      await wrapper.vm.$nextTick()

      expect(wrapper.findAll('[data-testid="condition-row"]').length).toBe(10)
      expect(addBtn.attributes('disabled')).toBeDefined()
    })
  })

  // ============================================================================
  // Field Selection Tests (5 tests)
  // ============================================================================

  describe('Field Selection', () => {
    beforeEach(async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()
    })

    it('renders field selector with correct options', () => {
      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      expect(fieldSelect.exists()).toBe(true)

      // Check that field options are available
      const vm = wrapper.vm
      expect(vm.fieldOptions).toContain('concept')
      expect(vm.fieldOptions).toContain('date')
      expect(vm.fieldOptions).toContain('confidence')
    })

    it('updates condition field when selected', async () => {
      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      await fieldSelect.setValue('concept')
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.conditions[0].field).toBe('concept')
    })

    it('shows appropriate input for concept field', async () => {
      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      await fieldSelect.setValue('concept')
      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="value-input-text"]').exists()).toBe(true)
    })

    it('shows date picker for date field', async () => {
      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      await fieldSelect.setValue('date')
      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="value-input-date"]').exists()).toBe(true)
    })

    it('shows slider for confidence field', async () => {
      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      await fieldSelect.setValue('confidence')
      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="value-input-slider"]').exists()).toBe(true)
    })
  })

  // ============================================================================
  // Operator Selection Tests (6 tests)
  // ============================================================================

  describe('Operator Selection', () => {
    beforeEach(async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()
    })

    it('renders operator selector between conditions', () => {
      const operatorSelects = wrapper.findAll('[data-testid="operator-select"]')
      expect(operatorSelects.length).toBe(1) // n-1 operators for n conditions
    })

    it('defaults to AND operator', () => {
      expect(wrapper.vm.conditions[0].operator).toBe('AND')
    })

    it('allows changing to OR operator', async () => {
      const operatorSelect = wrapper.find('[data-testid="operator-select"]')
      await operatorSelect.setValue('OR')
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.conditions[0].operator).toBe('OR')
    })

    it('allows changing to NOT operator', async () => {
      const operatorSelect = wrapper.find('[data-testid="operator-select"]')
      await operatorSelect.setValue('NOT')
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.conditions[0].operator).toBe('NOT')
    })

    it('updates query preview when operator changes', async () => {
      // Set field values first
      const fieldSelects = wrapper.findAll('[data-testid="field-select"]')
      await fieldSelects[0].setValue('concept')
      await fieldSelects[1].setValue('concept')

      const valueInputs = wrapper.findAll('[data-testid="value-input-text"]')
      await valueInputs[0].setValue('diabetes')
      await valueInputs[1].setValue('hypertension')
      await wrapper.vm.$nextTick()

      const previewBefore = wrapper.find('[data-testid="query-preview-text"]').text()

      // Change operator
      const operatorSelect = wrapper.find('[data-testid="operator-select"]')
      await operatorSelect.setValue('OR')
      await wrapper.vm.$nextTick()

      const previewAfter = wrapper.find('[data-testid="query-preview-text"]').text()
      expect(previewAfter).not.toBe(previewBefore)
      expect(previewAfter).toContain('OR')
    })

    it('does not render operator selector for single condition', async () => {
      // Remove one condition to leave only 1
      await wrapper.find('[data-testid="remove-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.findAll('[data-testid="operator-select"]').length).toBe(0)
    })
  })

  // ============================================================================
  // Query Generation and Preview Tests (7 tests)
  // ============================================================================

  describe('Query Generation and Preview', () => {
    it('generates simple query for single condition', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      await fieldSelect.setValue('concept')

      const valueInput = wrapper.find('[data-testid="value-input-text"]')
      await valueInput.setValue('diabetes')
      await wrapper.vm.$nextTick()

      const preview = wrapper.find('[data-testid="query-preview-text"]').text()
      expect(preview).toContain('diabetes')
    })

    it('generates AND query for multiple conditions', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const fieldSelects = wrapper.findAll('[data-testid="field-select"]')
      await fieldSelects[0].setValue('concept')
      await fieldSelects[1].setValue('concept')

      const valueInputs = wrapper.findAll('[data-testid="value-input-text"]')
      await valueInputs[0].setValue('diabetes')
      await valueInputs[1].setValue('medication')
      await wrapper.vm.$nextTick()

      const preview = wrapper.find('[data-testid="query-preview-text"]').text()
      expect(preview).toMatch(/diabetes.*AND.*medication/)
    })

    it('generates OR query when operator is OR', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const fieldSelects = wrapper.findAll('[data-testid="field-select"]')
      await fieldSelects[0].setValue('concept')
      await fieldSelects[1].setValue('concept')

      const valueInputs = wrapper.findAll('[data-testid="value-input-text"]')
      await valueInputs[0].setValue('diabetes')
      await valueInputs[1].setValue('hypertension')

      const operatorSelect = wrapper.find('[data-testid="operator-select"]')
      await operatorSelect.setValue('OR')
      await wrapper.vm.$nextTick()

      const preview = wrapper.find('[data-testid="query-preview-text"]').text()
      expect(preview).toMatch(/diabetes.*OR.*hypertension/)
    })

    it('generates NOT query when operator is NOT', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const fieldSelects = wrapper.findAll('[data-testid="field-select"]')
      await fieldSelects[0].setValue('concept')
      await fieldSelects[1].setValue('concept')

      const valueInputs = wrapper.findAll('[data-testid="value-input-text"]')
      await valueInputs[0].setValue('diabetes')
      await valueInputs[1].setValue('cancer')

      const operatorSelect = wrapper.find('[data-testid="operator-select"]')
      await operatorSelect.setValue('NOT')
      await wrapper.vm.$nextTick()

      const preview = wrapper.find('[data-testid="query-preview-text"]').text()
      expect(preview).toMatch(/diabetes.*NOT.*cancer/)
    })

    it('generates date range query for date field', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      await fieldSelect.setValue('date')

      const dateInput = wrapper.find('[data-testid="value-input-date"]')
      await dateInput.setValue('2024-01-01')
      await wrapper.vm.$nextTick()

      const preview = wrapper.find('[data-testid="query-preview-text"]').text()
      expect(preview).toContain('date:2024-01-01')
    })

    it('generates confidence query for confidence field', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      await fieldSelect.setValue('confidence')

      // Set slider value
      wrapper.vm.conditions[0].value = 0.8
      await wrapper.vm.$nextTick()

      const preview = wrapper.find('[data-testid="query-preview-text"]').text()
      expect(preview).toContain('confidence:')
      expect(preview).toContain('0.8')
    })

    it('updates preview in real-time as conditions change', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      await fieldSelect.setValue('concept')

      const valueInput = wrapper.find('[data-testid="value-input-text"]')

      await valueInput.setValue('diab')
      await wrapper.vm.$nextTick()
      let preview = wrapper.find('[data-testid="query-preview-text"]').text()
      expect(preview).toContain('diab')

      await valueInput.setValue('diabetes')
      await wrapper.vm.$nextTick()
      preview = wrapper.find('[data-testid="query-preview-text"]').text()
      expect(preview).toContain('diabetes')
    })
  })

  // ============================================================================
  // Query Validation Tests (8 tests)
  // ============================================================================

  describe('Query Validation', () => {
    it('shows validation error when no conditions added', async () => {
      await wrapper.find('[data-testid="apply-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const error = wrapper.find('[data-testid="validation-error"]')
      expect(error.exists()).toBe(true)
      expect(error.text()).toContain('Add at least one condition')
    })

    it('shows validation error when condition has no field selected', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      await wrapper.find('[data-testid="apply-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const error = wrapper.find('[data-testid="validation-error"]')
      expect(error.exists()).toBe(true)
      expect(error.text()).toContain('Select a field')
    })

    it('shows validation error when condition has no value', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      await fieldSelect.setValue('concept')
      await wrapper.vm.$nextTick()

      await wrapper.find('[data-testid="apply-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const error = wrapper.find('[data-testid="validation-error"]')
      expect(error.exists()).toBe(true)
      expect(error.text()).toContain('Enter a value')
    })

    it('shows validation success when query is valid', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      await fieldSelect.setValue('concept')

      const valueInput = wrapper.find('[data-testid="value-input-text"]')
      await valueInput.setValue('diabetes')
      await wrapper.vm.$nextTick()

      const success = wrapper.find('[data-testid="validation-success"]')
      expect(success.exists()).toBe(true)
      expect(success.text()).toContain('Valid query')
    })

    it('validates all conditions before applying', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      // Set first condition
      const fieldSelects = wrapper.findAll('[data-testid="field-select"]')
      await fieldSelects[0].setValue('concept')
      const valueInputs = wrapper.findAll('[data-testid="value-input-text"]')
      await valueInputs[0].setValue('diabetes')

      // Leave second condition empty
      await wrapper.vm.$nextTick()

      await wrapper.find('[data-testid="apply-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const error = wrapper.find('[data-testid="validation-error"]')
      expect(error.exists()).toBe(true)
    })

    it('disables apply button when validation fails', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const applyBtn = wrapper.find('[data-testid="apply-btn"]')
      expect(applyBtn.attributes('disabled')).toBeDefined()
    })

    it('enables apply button when validation passes', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      await fieldSelect.setValue('concept')

      const valueInput = wrapper.find('[data-testid="value-input-text"]')
      await valueInput.setValue('diabetes')
      await wrapper.vm.$nextTick()

      const applyBtn = wrapper.find('[data-testid="apply-btn"]')
      expect(applyBtn.attributes('disabled')).toBeUndefined()
    })

    it('shows inline validation errors on condition rows', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      // Trigger validation
      await wrapper.find('[data-testid="apply-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const conditionRow = wrapper.find('[data-testid="condition-row"]')
      expect(conditionRow.find('[data-testid="field-error"]').exists()).toBe(true)
    })
  })

  // ============================================================================
  // Syntax Highlighting Tests (3 tests)
  // ============================================================================

  describe('Syntax Highlighting', () => {
    it('highlights operators in preview', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const fieldSelects = wrapper.findAll('[data-testid="field-select"]')
      await fieldSelects[0].setValue('concept')
      await fieldSelects[1].setValue('concept')

      const valueInputs = wrapper.findAll('[data-testid="value-input-text"]')
      await valueInputs[0].setValue('diabetes')
      await valueInputs[1].setValue('medication')
      await wrapper.vm.$nextTick()

      const preview = wrapper.find('[data-testid="query-preview-text"]')
      const highlightedOperators = preview.findAll('.highlight-operator')
      expect(highlightedOperators.length).toBeGreaterThan(0)
    })

    it('highlights field names in preview', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      await fieldSelect.setValue('concept')

      const valueInput = wrapper.find('[data-testid="value-input-text"]')
      await valueInput.setValue('diabetes')
      await wrapper.vm.$nextTick()

      const preview = wrapper.find('[data-testid="query-preview-text"]')
      const highlightedFields = preview.findAll('.highlight-field')
      expect(highlightedFields.length).toBeGreaterThan(0)
    })

    it('highlights values in preview', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      await fieldSelect.setValue('concept')

      const valueInput = wrapper.find('[data-testid="value-input-text"]')
      await valueInput.setValue('diabetes')
      await wrapper.vm.$nextTick()

      const preview = wrapper.find('[data-testid="query-preview-text"]')
      const highlightedValues = preview.findAll('.highlight-value')
      expect(highlightedValues.length).toBeGreaterThan(0)
    })
  })

  // ============================================================================
  // Accessibility Tests (5 tests)
  // ============================================================================

  describe('Accessibility', () => {
    it('has appropriate ARIA labels on add button', () => {
      const addBtn = wrapper.find('[data-testid="add-condition-btn"]')
      expect(addBtn.attributes('aria-label')).toBeDefined()
      expect(addBtn.attributes('aria-label')).toContain('Add')
    })

    it('has appropriate ARIA labels on remove buttons', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const removeBtn = wrapper.find('[data-testid="remove-condition-btn"]')
      expect(removeBtn.attributes('aria-label')).toBeDefined()
      expect(removeBtn.attributes('aria-label')).toContain('Remove')
    })

    it('has role="group" on condition rows', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const conditionRow = wrapper.find('[data-testid="condition-row"]')
      expect(conditionRow.attributes('role')).toBe('group')
    })

    it('has aria-live region for validation messages', () => {
      const validationSection = wrapper.find('[data-testid="validation-section"]')
      expect(validationSection.attributes('aria-live')).toBeDefined()
    })

    it('supports keyboard navigation', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      // Tab to field select
      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      expect(fieldSelect.attributes('tabindex')).toBeDefined()

      // Tab to value input
      await fieldSelect.setValue('concept')
      await wrapper.vm.$nextTick()

      const valueInput = wrapper.find('[data-testid="value-input-text"]')
      expect(valueInput.attributes('tabindex')).toBeDefined()
    })
  })

  // ============================================================================
  // Integration with Parent Tests (4 tests)
  // ============================================================================

  describe('Integration with Parent', () => {
    it('emits update:modelValue when apply clicked', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      const fieldSelect = wrapper.find('[data-testid="field-select"]')
      await fieldSelect.setValue('concept')

      const valueInput = wrapper.find('[data-testid="value-input-text"]')
      await valueInput.setValue('diabetes')
      await wrapper.vm.$nextTick()

      await wrapper.find('[data-testid="apply-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')![0][0]).toContain('diabetes')
    })

    it('emits close event when close button clicked', async () => {
      await wrapper.find('[data-testid="close-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.emitted('close')).toBeTruthy()
    })

    it('clears all conditions when clear button clicked', async () => {
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.find('[data-testid="add-condition-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      await wrapper.find('[data-testid="clear-btn"]').trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.findAll('[data-testid="condition-row"]').length).toBe(0)
      expect(wrapper.find('[data-testid="empty-state"]').exists()).toBe(true)
    })

    it('accepts modelValue prop to initialize query', async () => {
      const wrapperWithQuery = createWrapper({ modelValue: 'concept:diabetes' })
      await wrapperWithQuery.vm.$nextTick()

      // Check that condition was parsed and added
      expect(wrapperWithQuery.vm.conditions.length).toBeGreaterThan(0)
    })
  })
})
