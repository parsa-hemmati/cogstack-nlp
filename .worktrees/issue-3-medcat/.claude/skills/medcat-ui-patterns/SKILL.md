---
name: medcat-ui-patterns
description: Provides Vue 3 + Vuetify UI patterns from MedCAT Trainer's 24 production components. Use when building clinical care tool interfaces (patient search, timeline view, annotation UI, concept selection, document display). Documents actual component patterns, Vuetify usage, Django REST API integration, and authentication flows. Complements medcat-architecture for full-stack integration.
---

# MedCAT UI Patterns Expert Skill

## When to use this skill

Activate when:
- Building clinical care tool UIs (patient search, timeline, CDS interfaces)
- Implementing concept selection/autocomplete
- Displaying clinical text with annotations/highlights
- Creating data tables for medical concepts/patients
- Integrating Vue 3 frontend with Django REST backend
- Implementing authentication (Token or OIDC)
- Reusing MedCAT Trainer component patterns

## MedCAT Trainer Frontend Stack

**Tech Stack**:
```json
{
  "vue": "3.5.12",
  "vuetify": "3.7.3",         // Material Design components
  "typescript": "5.6.0",
  "vite": "6.3.4",            // Build tool
  "axios": "1.8.2",           // HTTP client
  "vue-router": "4.4.5",
  "keycloak-js": "26.2.0",    // OIDC authentication
  "plotly.js-dist": "3.0.0",  // Charts
  "vue-select": "3.20.3",     // Advanced select/autocomplete
  "lodash": "4.17.21"         // Utilities
}
```

**Component Inventory** (24 components):
```
src/components/
├── common/ (9 components)
│   ├── ClinicalText.vue           # Annotated text viewer ★
│   ├── ConceptPicker.vue          # Concept autocomplete ★
│   ├── ConceptFilter.vue          # Filter by CUI
│   ├── DocumentSummary.vue        # Document metadata card
│   ├── AnnotationSummary.vue      # Annotation stats
│   ├── ConceptSummary.vue         # Concept stats
│   ├── Login.vue                  # Login form
│   ├── NavBar.vue                 # Navigation header
│   ├── Modal.vue                  # Generic modal
│   ├── ProjectList.vue            # Project cards
│   └── AddNewConcept.vue          # Add concept form
├── anns/ (3 components)
│   ├── AnnoResult.vue             # Annotation result card
│   ├── AddAnnotation.vue          # Annotation form
│   └── TaskBar.vue                # Task buttons
├── usecases/ (5 components)
│   ├── MetaAnnotationTask.vue
│   ├── MetaAnnotationTaskContainer.vue
│   ├── RelationAnnotation.vue
│   ├── RelationAnnotationTaskContainer.vue
│   └── HelpContent.vue
├── metrics/ (3 components)
│   ├── ConceptSummary.vue         # Concept metrics table
│   ├── AnnotationsTable.vue       # Annotation data table
│   └── MetricCell.vue             # Metric display cell
└── models/ (2 components)
    ├── ConceptDatabaseViz.vue     # CDB visualization
    └── VueTree.vue                # Tree structure component

src/views/ (6 views)
├── Home.vue                       # Project dashboard
├── TrainAnnotations.vue           # Main annotation interface ★
├── Metrics.vue                    # Metrics reports
├── MetricsHome.vue                # Metrics dashboard
├── ConceptDatabase.vue            # CDB explorer
└── Demo.vue                       # MedCAT demo
```

★ = High-value components to study for reuse

## Pattern 1: Clinical Text with Highlights (ClinicalText.vue)

### Use Case
Display clinical documents with highlighted medical concepts, clickable annotations, and right-click context menus.

### Component Structure
```vue
<template>
  <div class="note-container">
    <!-- Loading overlay -->
    <v-overlay :model-value="loading !== null"
               color="primary"
               :persistent="true">
      <v-progress-circular indeterminate color="primary"/>
      <span class="overlay-message">{{loading}}</span>
    </v-overlay>

    <!-- Clinical text with runtime-compiled highlights -->
    <div v-if="!loading" class="clinical-note">
      <v-runtime-template :template="formattedText"/>
    </div>

    <!-- Right-click context menu -->
    <vue-simple-context-menu
      :elementId="'ctxMenuId'"
      :options="ctxMenuOptions"
      @option-clicked="ctxOptionClicked">
    </vue-simple-context-menu>
  </div>
</template>

<script>
import VRuntimeTemplate from "vue3-runtime-template"
import VueSimpleContextMenu from 'vue-simple-context-menu'
import _ from 'lodash'

export default {
  name: 'ClinicalText',
  components: { VRuntimeTemplate, VueSimpleContextMenu },
  props: {
    text: String,                  // Raw clinical text
    ents: Array,                   // Entities with start_ind, end_ind, id
    currentEnt: Object,            // Currently selected entity
    loading: String,               // Loading message
    addAnnos: Boolean              // Enable right-click to add annotations
  },
  emits: [
    'select:concept',              // User clicked an entity
    'select:addSynonym',           // User added synonym from context menu
    'remove:newAnno'               // User removed manually created annotation
  ],
  computed: {
    formattedText() {
      // Build HTML string with highlighted spans
      let formattedText = ''
      let start = 0

      for (let i = 0; i < this.ents.length; i++) {
        let highlightText = this.text.slice(
          this.ents[i].start_ind,
          this.ents[i].end_ind
        )

        // Dynamic CSS class based on task value
        let styleClass = `highlight-task-default`
        if (this.ents[i].assignedValues[this.taskName]) {
          let btnIndex = this.taskValues.indexOf(
            this.ents[i].assignedValues[this.taskName]
          )
          styleClass = `highlight-task-${btnIndex}`
        }

        // Highlight selected entity
        if (this.ents[i] === this.currentEnt) {
          styleClass += ' highlight-task-selected'
        }

        // Build clickable span
        let spanText = `<span @click="selectEnt(${i})" class="${styleClass}">
          ${_.escape(highlightText)}
        </span>`

        // Add preceding text
        formattedText += _.escape(this.text.slice(start, this.ents[i].start_ind))
        formattedText += spanText
        start = this.ents[i].end_ind
      }

      // Add remaining text
      formattedText += this.text.slice(start)

      // Wrap in div with context menu handler
      return this.addAnnos
        ? `<div @contextmenu.prevent.stop="showCtxMenu($event)">${formattedText}</div>`
        : `<div>${formattedText}</div>`
    }
  },
  methods: {
    selectEnt(entIdx) {
      this.$emit('select:concept', entIdx)
    },
    showCtxMenu(event) {
      // Get text selection and show context menu
      const selection = window.getSelection()
      // ... (complex selection logic)
      this.$refs.ctxMenu.showMenu(event, this.selection)
    }
  }
}
</script>

<style scoped>
.highlight-task-default {
  background-color: #ffeb3b;
  cursor: pointer;
}
.highlight-task-selected {
  background-color: #ff9800;
  font-weight: bold;
}
</style>
```

### Reuse Pattern for Clinical Care Tools
```vue
<!-- PatientDocumentViewer.vue -->
<template>
  <ClinicalText
    :text="document.text"
    :ents="annotations"
    :current-ent="selectedAnnotation"
    @select:concept="onConceptClick"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ClinicalText from '@/components/common/ClinicalText.vue'

interface Annotation {
  start_ind: number
  end_ind: number
  cui: string
  id: string
}

const document = ref({ text: "Patient has atrial flutter..." })
const annotations = ref<Annotation[]>([
  { start_ind: 12, end_ind: 27, cui: 'C0004239', id: '1' }
])

function onConceptClick(idx: number) {
  selectedAnnotation.value = annotations.value[idx]
}
</script>
```

## Pattern 2: Concept Autocomplete (ConceptPicker.vue)

### Use Case
Search and select medical concepts from CDB using autocomplete with debouncing.

### Component Structure
```vue
<template>
  <div @keydown.stop>
    <v-select
      v-model="selectedCUI"
      @search="searchCUI"
      :inputId="'searchBox'"
      :clearSearchOnSelect="true"
      :filterable="false"              <!-- Server-side filtering -->
      :appendToBody="true"
      :options="searchResults"
      :loading="loadingResults"
      label="cui"
      @open="$emit('picker:opened')"
      @close="$emit('picker:closed')">

      <!-- No options slot -->
      <template v-slot:no-options="{ search, searching }">
        <span v-if="error" class="text-danger">{{ error }}</span>
        <template v-if="searching">No results for <em>{{ search }}</em></template>
        <em v-else style="opacity: 0.5">Start typing to search...</em>
      </template>

      <!-- Option slot (customize appearance) -->
      <template v-slot:option="option">
        <span class="select-option">{{option.name}}</span>
        <span class="select-option-cui"> - {{option.cui}}</span>
      </template>
    </v-select>
  </div>
</template>

<script>
import vSelect from 'vue-select'
import _ from 'lodash'

export default {
  name: 'ConceptPicker',
  components: { vSelect },
  props: {
    restrict_concept_lookup: Boolean,
    cui_filter: String,              // Comma-separated CUIs to filter by
    cdb_search_filter: Array,        // CDB IDs to search
    concept_db: Number,
    selection: String                // Pre-populate search
  },
  emits: ['pickedResult:concept', 'picker:opened', 'picker:closed'],
  data() {
    return {
      selectedCUI: null,
      searchResults: [],
      loadingResults: false,
      error: null
    }
  },
  watch: {
    selectedCUI(newVal) {
      this.$emit('pickedResult:concept', newVal)
    }
  },
  methods: {
    searchCUI: _.debounce(function(term) {
      this.loadingResults = true

      if (!term || term.trim().length === 0) {
        this.loadingResults = false
        return
      }

      // Build query params
      const conceptDBset = new Set(this.cdb_search_filter.concat(this.concept_db))
      conceptDBset.delete(null)
      const conceptDbs = Array.from(conceptDBset).join(',')
      const searchConceptsQueryParams = `search=${term}&cdbs=${conceptDbs}`

      // Call Django REST API
      this.$http.get(`/api/search-concepts/?${searchConceptsQueryParams}`)
        .then(resp => {
          this.searchResults = resp.data.results.map(r => ({
            name: r.pretty_name,
            cui: r.cui,
            type_ids: r.type_ids,
            desc: r.desc,
            icd10: r.icd10,
            semantic_type: r.semantic_type
          }))

          // Filter by CUI if restricted
          if (this.restrict_concept_lookup && this.cui_filter) {
            let cuis = this.cui_filter.split(',').map(c => c.trim())
            this.searchResults = this.searchResults.filter(r =>
              cuis.indexOf(r.cui) !== -1
            )
          }

          this.loadingResults = false
        })
        .catch(err => {
          this.error = err.response?.data?.message || 'Error searching concepts'
          this.loadingResults = false
          this.searchResults = []
        })
    }, 500)  // 500ms debounce
  }
}
</script>
```

### Reuse Pattern for Clinical Care Tools
```vue
<!-- ConceptSearch.vue for patient search -->
<template>
  <ConceptPicker
    :concept_db="activeProjectCDB"
    :selection="initialSearchTerm"
    @pickedResult:concept="onConceptSelected"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ConceptPicker from '@/components/common/ConceptPicker.vue'

const activeProjectCDB = ref(1)
const initialSearchTerm = ref("")

function onConceptSelected(concept: { cui: string, name: string }) {
  // Search patients with this CUI
  searchPatients(concept.cui)
}
</script>
```

## Pattern 3: Django REST API Integration

### Axios Configuration
```typescript
// src/plugins/axios.ts
import axios from 'axios'
import type { AxiosInstance } from 'axios'

const apiClient: AxiosInstance = axios.create({
  baseURL: '/api',  // Nginx proxies /api to Django
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Add authentication interceptor
apiClient.interceptors.request.use((config) => {
  // Token auth
  const token = getCookie('api-token')
  if (token) {
    config.headers.Authorization = `Token ${token}`
  }

  // OIDC auth
  if (window.keycloak?.token) {
    config.headers.Authorization = `Bearer ${window.keycloak.token}`
  }

  return config
})

// Error interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
```

### API Service Pattern
```typescript
// src/services/api/annotations.ts
import apiClient from '@/plugins/axios'

export interface AnnotatedEntity {
  id: number
  value: string
  start_ind: number
  end_ind: number
  cui: string
  validated: boolean
  correct: boolean
}

export const annotationsAPI = {
  async getAnnotations(projectId: number, documentId: number): Promise<AnnotatedEntity[]> {
    const response = await apiClient.get('/annotated-entities/', {
      params: { project: projectId, document: documentId }
    })
    return response.data.results
  },

  async createAnnotation(data: Partial<AnnotatedEntity>): Promise<AnnotatedEntity> {
    const response = await apiClient.post('/annotated-entities/', data)
    return response.data
  },

  async updateAnnotation(id: number, data: Partial<AnnotatedEntity>): Promise<AnnotatedEntity> {
    const response = await apiClient.patch(`/annotated-entities/${id}/`, data)
    return response.data
  },

  async deleteAnnotation(id: number): Promise<void> {
    await apiClient.delete(`/annotated-entities/${id}/`)
  }
}
```

### Usage in Components
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { annotationsAPI, type AnnotatedEntity } from '@/services/api/annotations'

const annotations = ref<AnnotatedEntity[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

async function loadAnnotations(projectId: number, documentId: number) {
  loading.value = true
  error.value = null

  try {
    annotations.value = await annotationsAPI.getAnnotations(projectId, documentId)
  } catch (err: any) {
    error.value = err.response?.data?.message || 'Failed to load annotations'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAnnotations(1, 123)
})
</script>
```

## Pattern 4: Authentication Flows

### Token-Based Authentication (Default)

**Login**:
```vue
<!-- Login.vue -->
<template>
  <v-form @submit.prevent="login">
    <v-text-field
      v-model="username"
      label="Username"
      :rules="[rules.required]"
    />
    <v-text-field
      v-model="password"
      label="Password"
      type="password"
      :rules="[rules.required]"
    />
    <v-btn type="submit" :loading="loading">Login</v-btn>
    <v-alert v-if="error" type="error">{{ error }}</v-alert>
  </v-form>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/plugins/axios'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref<string | null>(null)

const rules = {
  required: (v: string) => !!v || 'Required'
}

async function login() {
  loading.value = true
  error.value = null

  try {
    const response = await apiClient.post('/api-token-auth/', {
      username: username.value,
      password: password.value
    })

    // Store token in cookie
    document.cookie = `api-token=${response.data.token}; path=/; max-age=604800`

    // Set default header for future requests
    apiClient.defaults.headers.common['Authorization'] = `Token ${response.data.token}`

    // Redirect to home
    router.push('/')
  } catch (err: any) {
    error.value = err.response?.data?.message || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
```

### OIDC/Keycloak Authentication (Optional)

**Setup** (`src/auth.ts`):
```typescript
import Keycloak from 'keycloak-js'

// Environment-based configuration
const keycloak = new Keycloak({
  url: import.meta.env.VITE_OIDC_HOST || 'http://keycloak:8080',
  realm: import.meta.env.VITE_OIDC_REALM || 'cogstack-realm',
  clientId: import.meta.env.VITE_OIDC_CLIENT_ID || 'cogstack-medcattrainer-frontend'
})

export async function initAuth() {
  const authenticated = await keycloak.init({
    onLoad: 'login-required',
    checkLoginIframe: false
  })

  if (authenticated) {
    // Set bearer token for API calls
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${keycloak.token}`

    // Auto-refresh token every 10 seconds
    setInterval(() => {
      keycloak.updateToken(70).then(refreshed => {
        if (refreshed) {
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${keycloak.token}`
          console.log('Token refreshed')
        }
      }).catch(() => {
        console.error('Failed to refresh token')
        keycloak.logout()
      })
    }, 10000)
  }

  return authenticated
}

export { keycloak }
```

**Main.ts**:
```typescript
import { createApp } from 'vue'
import App from './App.vue'
import { initAuth } from './auth'

// Initialize auth before app
if (import.meta.env.VITE_USE_OIDC === 'true') {
  initAuth().then(() => {
    createApp(App).mount('#app')
  })
} else {
  createApp(App).mount('#app')
}
```

## Pattern 5: Vuetify Component Usage

### Data Tables
```vue
<template>
  <v-data-table
    :headers="headers"
    :items="patients"
    :loading="loading"
    :items-per-page="20"
    class="elevation-1"
    @click:row="onRowClick">

    <!-- Custom column template -->
    <template v-slot:item.concept="{ item }">
      <v-chip :color="getConceptColor(item.concept)">
        {{ item.concept }}
      </v-chip>
    </template>

    <!-- Custom actions column -->
    <template v-slot:item.actions="{ item }">
      <v-icon small @click="viewDetails(item)">mdi-eye</v-icon>
      <v-icon small @click="deleteItem(item)">mdi-delete</v-icon>
    </template>
  </v-data-table>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const headers = [
  { title: 'MRN', key: 'mrn', sortable: true },
  { title: 'Age', key: 'age', sortable: true },
  { title: 'Concept', key: 'concept', sortable: false },
  { title: 'Actions', key: 'actions', sortable: false }
]

const patients = ref([
  { mrn: 'MRN123', age: 65, concept: 'Atrial Flutter' },
  { mrn: 'MRN456', age: 72, concept: 'Diabetes' }
])
</script>
```

### Cards with Expansion
```vue
<template>
  <v-card>
    <v-card-title>Patient Summary</v-card-title>
    <v-card-subtitle>MRN: {{ patient.mrn }}</v-card-subtitle>
    <v-card-text>
      <p>Age: {{ patient.age }}</p>
      <p>Conditions: {{ patient.conditions.length }}</p>
    </v-card-text>
    <v-card-actions>
      <v-btn @click="viewTimeline">View Timeline</v-btn>
      <v-spacer/>
      <v-btn icon @click="expanded = !expanded">
        <v-icon>{{ expanded ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
      </v-btn>
    </v-card-actions>
    <v-expand-transition>
      <v-card-text v-if="expanded">
        <!-- Detailed info -->
        <v-list>
          <v-list-item v-for="condition in patient.conditions" :key="condition.cui">
            <v-list-item-title>{{ condition.name }}</v-list-item-title>
            <v-list-item-subtitle>{{ condition.cui }}</v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-expand-transition>
  </v-card>
</template>
```

## Pattern 6: Plotly Charts for Metrics

```vue
<template>
  <div ref="chartContainer"></div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Plotly from 'plotly.js-dist'

const chartContainer = ref<HTMLDivElement | null>(null)

onMounted(() => {
  if (!chartContainer.value) return

  const data = [{
    x: ['Atrial Flutter', 'Diabetes', 'Hypertension'],
    y: [45, 120, 89],
    type: 'bar',
    marker: { color: '#1976d2' }
  }]

  const layout = {
    title: 'Patient Counts by Condition',
    xaxis: { title: 'Condition' },
    yaxis: { title: 'Count' }
  }

  Plotly.newPlot(chartContainer.value, data, layout, { responsive: true })
})
</script>
```

## Common Pitfalls and Solutions

### Pitfall 1: Not handling loading states
**Problem**: UI freezes during API calls
**Solution**: Always use loading indicators
```vue
<v-overlay :model-value="loading" persistent>
  <v-progress-circular indeterminate/>
</v-overlay>
```

### Pitfall 2: Forgetting CSRF token for Django
**Problem**: POST requests fail with 403
**Solution**: Django REST Framework uses Token auth (no CSRF needed), but for session auth:
```typescript
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'
```

### Pitfall 3: Not debouncing search
**Problem**: Too many API calls while typing
**Solution**: Use lodash debounce (500ms)
```typescript
import { debounce } from 'lodash'

const search = debounce((term: string) => {
  // API call
}, 500)
```

### Pitfall 4: Hardcoding API URLs
**Problem**: Different URLs per environment
**Solution**: Use Vite environment variables
```typescript
// .env.development
VITE_API_BASE_URL=http://localhost:8000/api

// .env.production
VITE_API_BASE_URL=/api

// Code
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL
})
```

## Next Steps

After understanding UI patterns:
1. **Reuse ClinicalText.vue** for displaying annotated patient documents
2. **Reuse ConceptPicker.vue** for medical concept search in patient search module
3. **Follow API integration pattern** (axios + interceptors + service layer)
4. **Choose auth method** (Token for simple, OIDC for enterprise)
5. **Use Vuetify components** (v-data-table, v-card, v-chip) for consistency
6. **Reference medcat-architecture** for backend integration details
