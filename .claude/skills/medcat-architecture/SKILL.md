---
name: medcat-architecture
description: Expert knowledge of MedCAT ecosystem architecture (v2 core library, Trainer web app, Service API, AnonCAT). Use when designing clinical care tools that integrate with existing MedCAT components, planning module architecture, choosing integration patterns, or reusing MedCAT infrastructure. Guides model loading strategies, database schema understanding, API contracts, and deployment patterns.
---

# MedCAT Architecture Expert Skill

## When to use this skill

Activate when:
- Designing new features that integrate with MedCAT Trainer, Service, or v2 library
- Planning module architecture for clinical care tools
- Choosing between integration options (REST API vs library import vs Trainer extension)
- Understanding existing database schemas (95 Django migrations)
- Configuring model loading strategies
- Setting up authentication flows (Token vs OIDC)
- Deploying MedCAT components (Docker, Kubernetes)
- Troubleshooting MedCAT integration issues

## MedCAT Ecosystem Overview

The repository contains **3 production-ready applications**:

### 1. MedCAT v2 Core Library (`/medcat-v2/`)
- **Type**: PyPI package (`medcat` v2.2.0-dev)
- **Files**: 228 Python files
- **Purpose**: Core NLP capabilities (NER, linking, MetaCAT, RelCAT, DeID)
- **Main Class**: `CAT` (Clinical Annotation Toolkit)
- **Architecture**: Modular addon system

### 2. MedCAT Trainer (`/medcat-trainer/`)
- **Type**: Full-stack web application (Django + Vue 3)
- **Backend**: Django REST Framework (95 migrations, 17 models)
- **Frontend**: Vue 3.5 + TypeScript + Vuetify (31 components)
- **Purpose**: Annotation, training, metrics, project management
- **Users**: Clinicians, annotators, researchers

### 3. MedCAT Service (`/medcat-service/`)
- **Type**: REST API microservice (FastAPI)
- **Endpoints**: `/api/process`, `/api/process_bulk`
- **Purpose**: NLP inference at scale (multiprocessing)
- **Features**: Single/bulk processing, Gradio demo, health checks

## Integration Decision Tree

### Question 1: What do you need?

**A. NLP processing only** → Use MedCAT Service REST API
- Best for: Stateless applications, external systems
- Pattern: HTTP POST → get annotations
- Authentication: Add at API gateway level

**B. Annotation + training workflows** → Extend MedCAT Trainer
- Best for: Building on existing annotation UI
- Pattern: Add Django views + Vue components
- Authentication: Token or OIDC (already implemented)

**C. Custom Python application** → Import MedCAT v2 library
- Best for: Research scripts, batch processing
- Pattern: `from medcat import CAT`
- Authentication: Not applicable (library)

**D. New clinical care tools platform** → Build modular app + integrate all 3
- Best for: Patient search, timeline view, CDS
- Pattern: New Vue 3 frontend → calls MedCAT Service API + optionally Trainer API
- Authentication: Shared OIDC provider

### Question 2: Which integration pattern?

#### Pattern A: REST API Integration (Recommended for new apps)

**Architecture**:
```
New Clinical App (Vue 3 + FastAPI)
  ↓ HTTP POST /api/process
MedCAT Service (port 5555)
  ↓ Loads models
MedCAT v2 Library
```

**Pros**:
- Clean separation of concerns
- Horizontal scaling (stateless)
- Language-agnostic (any HTTP client)
- No model loading in your app

**Cons**:
- Network latency (~50-100ms overhead)
- No access to CDB internals
- Requires running MedCAT Service

**When to use**: Most clinical care tools (patient search, timeline view, CDS)

#### Pattern B: Direct Library Integration

**Architecture**:
```
Your App (Python)
  ↓ import medcat
MedCAT v2 Library (in-process)
```

**Pros**:
- No network overhead
- Full control over CAT instance
- Access to CDB/Vocab for custom queries
- Can customize pipeline

**Cons**:
- Must manage model loading (2-10s startup, 2-10GB RAM)
- Tied to Python runtime
- Harder to scale (vertical only)

**When to use**: Research notebooks, batch ETL jobs, model training scripts

#### Pattern C: Trainer Extension

**Architecture**:
```
MedCAT Trainer (Django + Vue)
  ↓ Add new Django app
  ↓ Add new Vue views/components
Existing Trainer Database
```

**Pros**:
- Reuse 95 migrations (User, Project, Document, Annotations)
- Reuse 31 Vue components (ClinicalText.vue, ConceptPicker.vue, etc.)
- Reuse authentication (Token/OIDC)
- Reuse model caching (`CAT_MAP`)

**Cons**:
- Coupled to Django/Trainer codebase
- Harder to deploy independently
- Risk of merge conflicts on updates

**When to use**: Adding features directly to annotation workflows (e.g., inter-annotator agreement dashboard)

## MedCAT v2 Core Library Patterns

### Model Loading (3 strategies)

#### Strategy 1: Model Pack (Recommended)
```python
from medcat import CAT

cat = CAT.load_model_pack("/path/to/model.zip")
# Contains: CDB, Vocab, MetaCAT, RelCAT, Config
```

**Pros**: Single file, versioned, portable
**Cons**: Large files (500MB - 5GB)

#### Strategy 2: Component Loading
```python
from medcat import CAT
from medcat.cdb import CDB
from medcat.vocab import Vocab

cdb = CDB.load("/path/to/cdb.dat")
vocab = Vocab.load("/path/to/vocab.dat")
cat = CAT(cdb=cdb, vocab=vocab)

# Add MetaCAT addon
from medcat.components.addons import MetaCATAddon
meta_cat = MetaCATAddon.load("/path/to/meta_cat/")
cat.add_addon(meta_cat)
```

**Pros**: Fine-grained control, can mix components
**Cons**: More code, versioning challenges

#### Strategy 3: MedCAT Den (Model Registry)
```python
from medcat_den import Den
from medcat_den.injection import injected_den

den = Den()
den.list_available_models()  # ['model-v1', 'model-v2']

with injected_den():
    cat = CAT.load_model_pack("model-v1")  # Fetches from den
```

**Pros**: Centralized model management, caching, versioning
**Cons**: Requires Den setup

### Processing Text

#### Single Document
```python
text = "Patient has atrial flutter. No history of diabetes."
entities = cat.get_entities(text)

# entities structure:
[
  {
    'cui': 'C0004239',
    'source_value': 'atrial flutter',
    'start': 12,
    'end': 27,
    'confidence': 0.95,
    'meta_anns': {
      'Negation': 'Affirmed',      # NOT negated
      'Experiencer': 'Patient',    # NOT family
      'Temporality': 'Current',    # NOT historical
      'Certainty': 'Confirmed'
    },
    'snomed': ['5370000'],
    'icd10': ['I48.92']
  },
  {
    'cui': 'C0011849',
    'source_value': 'diabetes',
    'meta_anns': {
      'Negation': 'Negated',       # ← NEGATED!
      'Experiencer': 'Patient',
      'Temporality': 'Current'
    }
  }
]
```

#### Filtering by Meta-Annotations
```python
# Get only active patient conditions
active_conditions = [
    ent for ent in entities
    if ent['meta_anns'].get('Negation') == 'Affirmed'
    and ent['meta_anns'].get('Experiencer') == 'Patient'
    and ent['meta_anns'].get('Temporality') in ['Current', 'Recent']
]
# Result: [atrial flutter] (diabetes excluded because negated)
```

### Configuration Pattern (Pydantic)
```python
from medcat.config import Config

config = Config()
config.general.spacy_model = "en_core_web_md"
config.ner.min_name_len = 2
config.linking.filters.cuis = ["C0011849"]  # Only detect diabetes

cat = CAT(cdb, vocab, config=config)
```

## MedCAT Service API Patterns

### Endpoint: Process Single Document

**Request**:
```http
POST /api/process HTTP/1.1
Content-Type: application/json

{
  "content": {
    "text": "Patient has atrial flutter. No history of diabetes."
  },
  "meta_anns_filters": [
    ["Negation", ["Affirmed"]],
    ["Experiencer", ["Patient"]]
  ]
}
```

**Response**:
```json
{
  "medcat_info": {
    "service_version": "1.12.0",
    "model_name": "medmen"
  },
  "result": {
    "text": "Patient has atrial flutter. No history of diabetes.",
    "annotations": [
      {
        "cui": "C0004239",
        "pretty_name": "Atrial Flutter",
        "start": 12,
        "end": 27,
        "meta_anns": {"Negation": "Affirmed", "Experiencer": "Patient"}
      }
    ],
    "success": true,
    "elapsed_time": 0.245
  }
}
```

**Note**: `meta_anns_filters` filters results AFTER processing (diabetes still detected but excluded from response)

### Endpoint: Process Bulk Documents

**Request**:
```http
POST /api/process_bulk HTTP/1.1
Content-Type: application/json

{
  "content": [
    {"text": "Document 1 text..."},
    {"text": "Document 2 text..."},
    {"text": "Document 3 text..."}
  ]
}
```

**Response**:
```json
{
  "result": [
    {"text": "Document 1 text...", "annotations": [...], "success": true},
    {"text": "Document 2 text...", "annotations": [...], "success": true},
    {"text": "Document 3 text...", "annotations": [...], "success": true}
  ]
}
```

**Performance**: Uses multiprocessing (`APP_BULK_NPROC=8`)

### Service Configuration (Environment Variables)

```bash
# Model paths
APP_MODEL_CDB_PATH=/cat/models/medmen/cdb.dat
APP_MODEL_VOCAB_PATH=/cat/models/medmen/vocab.dat
APP_MODEL_META_PATH_LIST=/cat/models/meta_negation:/cat/models/meta_experiencer
# Or use model pack
APP_MEDCAT_MODEL_PACK=/cat/models/model_pack.zip

# Performance
APP_BULK_NPROC=8              # Parallel workers for bulk processing
APP_TORCH_THREADS=-1          # PyTorch threads (-1 = auto)

# De-identification mode
APP_DEID_MODE=0               # Set to 1 for PHI redaction
APP_DEID_REDACT=1             # [***] vs [NAME]

# Logging
APP_LOG_LEVEL=20              # 10=DEBUG, 20=INFO, 30=WARNING
MEDCAT_LOG_LEVEL=20
```

### Deployment (Docker)

**Production Setup**:
```yaml
services:
  medcat-service:
    image: cogstacksystems/medcat-service:latest
    ports: ["5555:5000"]
    volumes:
      - ./models:/cat/models:ro    # Mount models read-only
    env_file: ./env/medcat.env
    shm_size: "1g"                 # CRITICAL for multiprocessing
    deploy:
      resources:
        limits:
          memory: 8G               # 2-10GB depending on model
        reservations:
          memory: 4G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**GPU Support**:
```yaml
image: cogstacksystems/medcat-service-gpu:latest
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

## MedCAT Trainer Database Schema

### Core Models (Django ORM)

**Projects**:
```python
ProjectAnnotateEntities
  - id, name, description
  - dataset (FK → Dataset)
  - cdb (FK → ConceptDB)
  - vocab (FK → Vocabulary)
  - members (ManyToMany → User)
  - cuis (text): Comma-separated CUIs to annotate
  - train_model_on_submit (bool)
```

**Documents**:
```python
Dataset
  - id, name, description, original_file

Document
  - id, name, text
  - dataset (FK)
```

**Annotations**:
```python
AnnotatedEntity
  - id, value, start_ind, end_ind
  - user (FK), project (FK), document (FK), entity (FK)
  - validated (bool), correct (bool), deleted (bool)
  - last_modified

MetaAnnotation
  - annotated_entity (FK)
  - meta_task (FK)          # e.g., "Negation"
  - meta_task_value (FK)    # e.g., "Affirmed"
  - validated (bool)

EntityRelation
  - start_entity (FK), end_entity (FK)
  - relation (FK)           # e.g., "caused_by"
  - project (FK), document (FK), user (FK)
```

**Concepts**:
```python
Entity
  - id, label (CUI, e.g., "C0004239")

MetaTask
  - id, name (e.g., "Negation", "Temporality")

MetaTaskValue
  - id, name (e.g., "Affirmed", "Negated", "Current")
```

**Models**:
```python
ModelPack
  - id, name, model_pack (FileField)
  - concept_db (FK), vocab (FK)
  - meta_cats (ManyToMany → MetaCATModel)

ConceptDB, Vocabulary, MetaCATModel
  - File storage for model artifacts
```

### Querying Annotations (API or direct)

**Via REST API**:
```http
GET /api/annotated-entities/?project=123&document=456
Authorization: Token abc123...
```

**Direct SQL** (if using same database):
```sql
SELECT
  ae.value,
  ae.start_ind,
  ae.end_ind,
  e.label AS cui,
  u.username,
  ma.meta_task.name AS meta_task_name,
  ma.meta_task_value.name AS meta_value
FROM api_annotatedentity ae
JOIN api_entity e ON ae.entity_id = e.id
JOIN auth_user u ON ae.user_id = u.id
LEFT JOIN api_metaannotation ma ON ae.id = ma.annotated_entity_id
WHERE ae.project_id = 123
  AND ae.document_id = 456
  AND ae.deleted = FALSE;
```

## MedCAT Trainer Vue 3 Frontend Patterns

### Reusable Components (`/webapp/frontend/src/components/`)

**ConceptPicker.vue** - Concept autocomplete search
```vue
<ConceptPicker
  :project="project"
  @select="onConceptSelected"
/>
```

**ClinicalText.vue** - Document viewer with highlighted annotations
```vue
<ClinicalText
  :text="document.text"
  :annotations="annotations"
  @annotation-click="onAnnotationClick"
/>
```

**ConceptFilter.vue** - Filter annotations by CUI
```vue
<ConceptFilter
  :concepts="allConcepts"
  @filter-changed="applyFilter"
/>
```

**DocumentSummary.vue** - Document metadata card
```vue
<DocumentSummary
  :document="document"
  :stats="annotationStats"
/>
```

### Authentication (Token-based)

**Login Flow**:
```typescript
// Login.vue
async login(username: string, password: string) {
  const response = await axios.post('/api/api-token-auth/', {
    username,
    password
  })

  // Store token in cookie
  document.cookie = `api-token=${response.data.token}; path=/`

  // Set default header for all requests
  axios.defaults.headers.common['Authorization'] = `Token ${response.data.token}`
}
```

### Authentication (OIDC/Keycloak)

**Setup**:
```typescript
// auth.ts
import Keycloak from 'keycloak-js'

const keycloak = new Keycloak({
  url: 'http://keycloak:8080',
  realm: 'cogstack-realm',
  clientId: 'cogstack-medcattrainer-frontend'
})

await keycloak.init({ onLoad: 'login-required' })

// Refresh token every 10s
setInterval(() => {
  keycloak.updateToken(70).then(refreshed => {
    if (refreshed) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${keycloak.token}`
    }
  })
}, 10000)
```

## Common Integration Pitfalls

### Pitfall 1: Not filtering by meta-annotations
**Problem**: Including family history, negated conditions, historical mentions
**Solution**: Always filter by `Negation=Affirmed`, `Experiencer=Patient`, `Temporality=Current`
**Reference**: `.claude/skills/medcat-meta-annotations/SKILL.md`

### Pitfall 2: Model loading time on first request
**Problem**: 2-10 second delay on first API call
**Solution**:
- Pre-warm MedCAT Service on startup
- Use health check endpoint to trigger model load: `curl /api/health/ready`
- Consider model caching service (MedCAT Den)

### Pitfall 3: Insufficient shared memory for multiprocessing
**Problem**: `OSError: [Errno 28] No space left on device` in bulk processing
**Solution**: Set `shm_size: "1g"` in Docker Compose (default 64MB is too small)

### Pitfall 4: Hardcoding model paths
**Problem**: Models not portable across environments
**Solution**: Use environment variables or MedCAT Den

### Pitfall 5: Direct database access to Trainer
**Problem**: Tight coupling, schema changes break your app
**Solution**: Use Trainer REST API (`/api/annotated-entities/`, etc.)

### Pitfall 6: Not handling model pack versions
**Problem**: v1 (.dat) vs v2 (folder) model packs
**Solution**: Use MedCAT v2 which handles both, but prefer v2 format

## Recommended Architecture for Clinical Care Tools

### Modular Design

```
Clinical Care Tools Platform
├── Shared Infrastructure
│   ├── Authentication Service (Keycloak/OIDC)
│   ├── MedCAT Service (NLP processing)
│   ├── Elasticsearch (patient data index)
│   └── PostgreSQL (application data)
├── Core App (Vue 3 + FastAPI)
│   ├── User management
│   ├── Audit logging
│   ├── Dashboard
│   └── Module loader
└── Modules (Pluggable)
    ├── Patient Search Module
    ├── Timeline View Module
    ├── Clinical Decision Support Module
    ├── Cohort Builder Module
    └── (Future modules)
```

### Integration Points

**Module → MedCAT Service**:
```typescript
// services/medcat.ts
export async function annotateText(text: string) {
  const response = await axios.post('http://medcat-service:5555/api/process', {
    content: { text },
    meta_anns_filters: [
      ['Negation', ['Affirmed']],
      ['Experiencer', ['Patient']]
    ]
  })
  return response.data.result.annotations
}
```

**Module → MedCAT Trainer (optional, for annotation export)**:
```typescript
// services/trainer.ts
export async function getAnnotations(projectId: number) {
  const response = await axios.get(
    `http://medcat-trainer:8000/api/annotated-entities/?project=${projectId}`,
    { headers: { Authorization: `Token ${token}` } }
  )
  return response.data.results
}
```

## Next Steps

After understanding architecture:
1. **Choose integration pattern** (REST API vs library vs Trainer extension)
2. **Design module system** (how modules plug into core app)
3. **Plan database schema** (reuse Trainer DB or separate?)
4. **Set up authentication** (shared OIDC provider)
5. **Create Spec-Kit specification** using `prd-to-spec` skill
6. **Build base app structure** using `modular-app-architect` skill
7. **Implement modules** using existing Vue 3 components (see `vue3-component-reuse` skill)
