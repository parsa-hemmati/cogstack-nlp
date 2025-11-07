---
name: vue3-component-reuse
description: Discovers and provides guidance on reusing existing Vue 3 components from MedCAT Trainer. Use when building new UI features for clinical care tools, implementing forms, tables, modals, charts, or any frontend component. Searches 65 existing components for patterns and provides integration examples using Composition API and TypeScript. Prevents rebuilding components that already exist.
---

# Vue 3 Component Reuse

Helps discover and reuse 65 existing Vue 3 + TypeScript components from MedCAT Trainer instead of rebuilding from scratch.

## Component location

All existing components are in:
```
medcat-trainer/webapp/frontend/src/
├── components/       # Reusable components (65 total)
├── views/           # Page-level components
├── composables/     # Composition API logic
└── types/           # TypeScript interfaces
```

## When to use this skill

Invoke when:
- Building new UI features (tables, forms, modals, charts)
- Implementing clinical care interfaces
- Creating patient search or timeline views
- Adding any frontend component

**Before writing any Vue component**, search for existing patterns in MedCAT Trainer.

## Quick search workflow

1. **Identify component need**
   - What are you building? (table, form, modal, chart, etc.)

2. **Search existing components**
   ```bash
   # Search by component type
   find medcat-trainer/webapp/frontend/src/components -name "*.vue" | grep -i "table\|modal\|form\|chart"

   # Search component file contents
   grep -r "defineComponent\|defineProps" medcat-trainer/webapp/frontend/src/components
   ```

3. **Read relevant component**
   ```bash
   # Example: Read a table component
   cat medcat-trainer/webapp/frontend/src/components/DataTable.vue
   ```

4. **Adapt for your use case**
   - Copy the pattern (Composition API, TypeScript types)
   - Modify props and logic as needed
   - Maintain consistent style

## Common component patterns to reuse

### Pattern 1: Data tables

**Search for**:
```bash
find medcat-trainer/webapp/frontend/src -name "*.vue" -exec grep -l "v-data-table\|table" {} \;
```

**Likely components**:
- `DataTable.vue` - Generic data table with sorting/filtering
- Components in `TrainAnnotations.vue` (34,490 lines - contains many table patterns)

**Reuse strategy**:
```vue
<script setup lang="ts">
import { ref, computed } from 'vue'

// Props with TypeScript
interface Props {
  items: Array<any>
  headers: Array<{text: string, value: string}>
}
const props = defineProps<Props>()

// Emit events
const emit = defineEmits<{
  select: [item: any]
}>()
</script>

<template>
  <v-data-table
    :items="props.items"
    :headers="props.headers"
    @click:row="emit('select', $event)"
  />
</template>
```

---

### Pattern 2: Forms with validation

**Search for**:
```bash
grep -r "v-form\|v-text-field" medcat-trainer/webapp/frontend/src/components
```

**Reuse strategy**:
```vue
<script setup lang="ts">
import { ref } from 'vue'

interface FormData {
  name: string
  value: string
}

const formData = ref<FormData>({
  name: '',
  value: ''
})

const valid = ref(false)

const rules = {
  required: (v: string) => !!v || 'Required',
  minLength: (v: string) => v.length >= 3 || 'Min 3 characters'
}

const submit = () => {
  if (valid.value) {
    emit('submit', formData.value)
  }
}

const emit = defineEmits<{
  submit: [data: FormData]
}>()
</script>

<template>
  <v-form v-model="valid">
    <v-text-field
      v-model="formData.name"
      :rules="[rules.required, rules.minLength]"
      label="Name"
    />
    <v-btn :disabled="!valid" @click="submit">Submit</v-btn>
  </v-form>
</template>
```

---

### Pattern 3: Modals/dialogs

**Search for**:
```bash
grep -r "v-dialog\|modal" medcat-trainer/webapp/frontend/src/components
```

**Reuse strategy**:
```vue
<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  modelValue: boolean
  title: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: []
}>()

const close = () => {
  emit('update:modelValue', false)
}

const confirm = () => {
  emit('confirm')
  close()
}
</script>

<template>
  <v-dialog :model-value="props.modelValue" @update:model-value="emit('update:modelValue', $event)">
    <v-card>
      <v-card-title>{{ props.title }}</v-card-title>
      <v-card-text>
        <slot />
      </v-card-text>
      <v-card-actions>
        <v-btn @click="close">Cancel</v-btn>
        <v-btn color="primary" @click="confirm">Confirm</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
```

---

### Pattern 4: Charts/visualizations

**Search for**:
```bash
grep -r "chart\|graph\|visualization" medcat-trainer/webapp/frontend/src
```

**Check**: `Metrics.vue` (25,991 lines) likely contains chart components

**Reuse strategy**: Read `Metrics.vue` for chart library usage and patterns

---

### Pattern 5: API calls with loading states

**Search for composables**:
```bash
find medcat-trainer/webapp/frontend/src/composables -name "*.ts"
```

**Pattern**:
```typescript
// composables/useApi.ts
import { ref } from 'vue'

export function useApi<T>() {
  const data = ref<T | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const execute = async (apiCall: () => Promise<T>) => {
    loading.value = true
    error.value = null
    try {
      data.value = await apiCall()
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, execute }
}

// Usage in component:
import { useApi } from '@/composables/useApi'

const { data, loading, error, execute } = useApi<Patient[]>()

onMounted(() => {
  execute(() => fetch('/api/patients').then(r => r.json()))
})
```

## Technology stack (from existing codebase)

**Vue 3.5.12** with:
- **Composition API** (not Options API)
- **TypeScript 5.6** (no `any` types)
- **Vuetify 3.7.3** (Material Design components)
- **Vite 6.3.4** (build tool)
- **Vue Router 4.4.5** (routing)

## Key patterns from MedCAT Trainer

### 1. Use Composition API

```vue
<!-- Good: Composition API -->
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const count = ref(0)
const doubled = computed(() => count.value * 2)
</script>

<!-- Bad: Options API (don't use) -->
<script lang="ts">
export default {
  data() {
    return { count: 0 }
  },
  computed: {
    doubled() { return this.count * 2 }
  }
}
</script>
```

### 2. Type your props and emits

```typescript
interface Props {
  items: Patient[]
  selectedId?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  select: [patient: Patient]
  delete: [id: string]
}>()
```

### 3. Use Vuetify components

```vue
<template>
  <v-container>
    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Patients</v-card-title>
          <v-card-text>
            <v-data-table :items="patients" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>
```

### 4. Organize imports

```typescript
// Vue core
import { ref, computed, onMounted } from 'vue'

// Components
import PatientCard from '@/components/PatientCard.vue'

// Composables
import { usePatientSearch } from '@/composables/usePatientSearch'

// Types
import type { Patient, SearchFilters } from '@/types'

// External libraries
import axios from 'axios'
```

## Component discovery commands

### Find all Vue components

```bash
find medcat-trainer/webapp/frontend/src/components -name "*.vue"
```

### Search by keyword

```bash
# Tables
grep -l "v-data-table\|<table" medcat-trainer/webapp/frontend/src/components/*.vue

# Forms
grep -l "v-form\|v-text-field" medcat-trainer/webapp/frontend/src/components/*.vue

# Modals
grep -l "v-dialog\|modal" medcat-trainer/webapp/frontend/src/components/*.vue

# Charts
grep -l "chart\|graph" medcat-trainer/webapp/frontend/src/components/*.vue
```

### Read large components strategically

```bash
# TrainAnnotations.vue is 34,490 lines - use head/grep
head -200 medcat-trainer/webapp/frontend/src/views/TrainAnnotations.vue
grep -A 10 "defineComponent" medcat-trainer/webapp/frontend/src/views/TrainAnnotations.vue
```

## TypeScript types to reuse

```bash
# Find existing type definitions
cat medcat-trainer/webapp/frontend/src/types/index.ts

# Common types to look for:
# - Patient
# - Document
# - Annotation
# - User
# - Project
```

## Vuetify components available

MedCAT Trainer uses Vuetify 3.7.3, which provides:
- Layout: `v-container`, `v-row`, `v-col`, `v-app-bar`, `v-navigation-drawer`
- Forms: `v-text-field`, `v-select`, `v-checkbox`, `v-radio`, `v-form`
- Data: `v-data-table`, `v-list`, `v-card`
- Feedback: `v-alert`, `v-snackbar`, `v-progress-circular`
- Modals: `v-dialog`, `v-menu`, `v-tooltip`
- Buttons: `v-btn`, `v-btn-group`, `v-fab`

**Reference**: https://vuetifyjs.com/en/components/all/

## Common mistakes to avoid

### Mistake 1: Rebuilding existing components

```vue
<!-- Bad: Rebuilding a data table from scratch -->
<template>
  <table>
    <tr v-for="item in items">...</tr>
  </table>
</template>

<!-- Good: Use existing Vuetify component -->
<template>
  <v-data-table :items="items" />
</template>
```

### Mistake 2: Using Options API

```vue
<!-- Bad: Options API (old pattern) -->
<script>
export default {
  data() { return { count: 0 } }
}
</script>

<!-- Good: Composition API (current pattern) -->
<script setup lang="ts">
const count = ref(0)
</script>
```

### Mistake 3: Missing TypeScript types

```typescript
// Bad: Using 'any'
const items = ref<any[]>([])

// Good: Proper types
interface Patient {
  id: string
  name: string
}
const items = ref<Patient[]>([])
```

## Integration with existing workflow

This skill automatically activates when:
- Implementing new Vue components
- Building clinical care interface UI
- Creating forms, tables, or charts
- Working in `/src/` frontend directories

Works alongside:
- `medcat-meta-annotations`: Frontend needs to display meta-annotation context
- `healthcare-compliance-checker`: UI components may display PHI

## Quick decision guide

**Need a table?** → Search for `v-data-table` in existing components

**Need a form?** → Search for `v-form` patterns

**Need a modal?** → Search for `v-dialog` examples

**Need API calls?** → Check `composables/` directory for patterns

**Need types?** → Read `types/index.ts` first

**Complex component?** → Read `TrainAnnotations.vue` or `Metrics.vue` for advanced patterns

## Example: Building patient search UI

1. **Search for existing search patterns**:
   ```bash
   grep -r "search\|filter" medcat-trainer/webapp/frontend/src/components
   ```

2. **Find table component**:
   ```bash
   grep -l "v-data-table" medcat-trainer/webapp/frontend/src/components/*.vue
   ```

3. **Read relevant components**:
   ```bash
   cat medcat-trainer/webapp/frontend/src/components/[SearchComponent].vue
   ```

4. **Adapt pattern**:
   - Copy Composition API structure
   - Modify props for patient data
   - Add meta-annotation display
   - Use existing Vuetify components

5. **Implement with TypeScript**:
   ```vue
   <script setup lang="ts">
   import { ref, computed } from 'vue'
   import type { Patient, MetaAnnotations } from '@/types'

   interface Props {
     patients: Patient[]
   }

   const props = defineProps<Props>()
   const search = ref('')

   const filteredPatients = computed(() =>
     props.patients.filter(p =>
       p.name.toLowerCase().includes(search.value.toLowerCase())
     )
   )
   </script>

   <template>
     <v-card>
       <v-card-title>Patient Search</v-card-title>
       <v-card-text>
         <v-text-field
           v-model="search"
           label="Search patients"
           prepend-icon="mdi-magnify"
         />
         <v-data-table
           :items="filteredPatients"
           :headers="[
             { text: 'Name', value: 'name' },
             { text: 'MRN', value: 'mrn' },
             { text: 'Conditions', value: 'conditions' }
           ]"
         />
       </v-card-text>
     </v-card>
   </template>
   ```

## Resources

**Component documentation**: Vuetify 3 docs (https://vuetifyjs.com)

**Vue 3 guide**: https://vuejs.org/guide/

**TypeScript with Vue**: https://vuejs.org/guide/typescript/composition-api.html

**Existing codebase**: Read MedCAT Trainer components as primary reference

## Remember

**Always search before building.** The 65 existing components contain patterns for most common UI needs. Reusing existing patterns ensures:
- Consistent user experience
- Less code to maintain
- Proven, tested patterns
- Faster development
