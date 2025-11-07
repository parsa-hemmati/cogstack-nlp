---
name: medcat-meta-annotations
description: Provides guidance on MedCAT meta-annotations (Negation, Temporality, Experiencer, Certainty) for medical concept extraction. Use when processing NLP results, building patient search queries, displaying medical concepts, filtering clinical entities, or implementing cohort identification. Ensures correct filtering to avoid false positives like family history, negated conditions, or hypothetical scenarios.
---

# MedCAT Meta-Annotations

Meta-annotations add critical context to medical concepts extracted by MedCAT, dramatically improving precision from 60% to 95%+ by filtering out false positives.

## What are meta-annotations?

MedCAT extracts medical concepts from clinical text, but raw extraction can include:
- **Negated conditions**: "No evidence of diabetes"
- **Family history**: "Mother has hypertension"
- **Historical conditions**: "Had pneumonia in 2015"
- **Hypothetical scenarios**: "If patient develops infection..."

**Meta-annotations** classify the context around each extracted concept to filter these false positives.

## The four meta-annotation types

### 1. Negation

Indicates whether a condition is affirmed or negated.

**Values**:
- `Affirmed`: Condition is present
- `Negated`: Condition is absent or ruled out

**Examples**:

| Clinical Text | Concept | Negation | Correct? |
|---------------|---------|----------|----------|
| "Patient has diabetes" | diabetes | `Affirmed` | ✅ Include |
| "No evidence of diabetes" | diabetes | `Negated` | ❌ Exclude |
| "Denies chest pain" | chest pain | `Negated` | ❌ Exclude |
| "Rules out myocardial infarction" | myocardial infarction | `Negated` | ❌ Exclude |

**Filter pattern** (Python):
```python
# Only include affirmed conditions
active_conditions = [
    entity for entity in entities
    if entity['meta_anns'].get('Negation') == 'Affirmed'
]
```

**Common negation triggers**:
- "no", "denies", "negative for", "rules out"
- "absence of", "without", "free of"
- "not", "never", "no evidence of"

---

### 2. Experiencer

Indicates who is experiencing the condition.

**Values**:
- `Patient`: The patient has/had the condition
- `Family`: Family member has/had the condition
- `Other`: Someone else (not patient or family)

**Examples**:

| Clinical Text | Concept | Experiencer | Correct? |
|---------------|---------|-------------|----------|
| "Patient diagnosed with asthma" | asthma | `Patient` | ✅ Include |
| "Mother has diabetes" | diabetes | `Family` | ❌ Exclude |
| "Family history of breast cancer" | breast cancer | `Family` | ❌ Exclude |
| "Brother had MI at age 45" | MI | `Family` | ❌ Exclude |

**Filter pattern** (Python):
```python
# Only include patient's own conditions
patient_conditions = [
    entity for entity in entities
    if entity['meta_anns'].get('Experiencer') == 'Patient'
]
```

**Why this matters**:
Without Experiencer filtering, a patient search for "diabetes" would incorrectly include patients with diabetic family members.

---

### 3. Temporality

Indicates the time frame of the condition.

**Values**:
- `Current`: Ongoing or recent condition
- `Historical`: Past condition, no longer active
- `Future`: Potential future scenario
- `Recent`: Recent past (implementation-specific timeframe)

**Examples**:

| Clinical Text | Concept | Temporality | Correct? |
|---------------|---------|-------------|----------|
| "Currently experiencing dyspnea" | dyspnea | `Current` | ✅ Include |
| "Had pneumonia in 2015" | pneumonia | `Historical` | ⚠️ Context-dependent |
| "If infection develops" | infection | `Future` | ❌ Exclude |
| "History of MI" | MI | `Historical` | ⚠️ Context-dependent |

**Filter pattern** (Python):
```python
# For acute conditions: current only
current_conditions = [
    entity for entity in entities
    if entity['meta_anns'].get('Temporality') in ['Current', 'Recent']
]

# For chronic conditions: current or historical
all_diagnoses = [
    entity for entity in entities
    if entity['meta_anns'].get('Temporality') in ['Current', 'Recent', 'Historical']
]
```

**Use case dependent**:
- **Acute care**: Usually want `Current` only
- **Research/cohorts**: May want `Historical` too
- **Alerts**: Definitely exclude `Future`

---

### 4. Certainty

Indicates the confidence level of the diagnosis.

**Values**:
- `Confirmed`: Definite diagnosis
- `Suspected`: Possible/probable diagnosis
- `Hypothetical`: Considered but not diagnosed

**Examples**:

| Clinical Text | Concept | Certainty | Correct? |
|---------------|---------|-----------|----------|
| "Diagnosed with pneumonia" | pneumonia | `Confirmed` | ✅ Include |
| "Possible appendicitis" | appendicitis | `Suspected` | ⚠️ Context-dependent |
| "Considering malignancy" | malignancy | `Suspected` | ⚠️ Context-dependent |
| "To rule out sepsis" | sepsis | `Hypothetical` | ❌ Exclude |

**Filter pattern** (Python):
```python
# High confidence only
confirmed_diagnoses = [
    entity for entity in entities
    if entity['meta_anns'].get('Certainty') == 'Confirmed'
]

# Include suspected (for differential diagnosis)
all_diagnoses = [
    entity for entity in entities
    if entity['meta_anns'].get('Certainty') in ['Confirmed', 'Suspected']
]
```

## Common filtering patterns

### Pattern 1: Active patient conditions (highest precision)

```python
def get_active_patient_conditions(entities):
    """Returns only current, affirmed conditions for the patient."""
    return [
        entity for entity in entities
        if (entity['meta_anns'].get('Negation') == 'Affirmed' and
            entity['meta_anns'].get('Experiencer') == 'Patient' and
            entity['meta_anns'].get('Temporality') in ['Current', 'Recent'])
    ]
```

**Use for**: Clinical decision support, active problem lists, real-time alerts

---

### Pattern 2: Patient diagnosis history (for research)

```python
def get_patient_diagnosis_history(entities):
    """Returns all patient diagnoses (current and historical)."""
    return [
        entity for entity in entities
        if (entity['meta_anns'].get('Negation') == 'Affirmed' and
            entity['meta_anns'].get('Experiencer') == 'Patient' and
            entity['meta_anns'].get('Temporality') in ['Current', 'Recent', 'Historical'] and
            entity['meta_anns'].get('Certainty') in ['Confirmed', 'Suspected'])
    ]
```

**Use for**: Cohort building, research studies, patient timelines

---

### Pattern 3: Family history extraction

```python
def get_family_history(entities):
    """Returns family history (excluding patient's own conditions)."""
    return [
        entity for entity in entities
        if (entity['meta_anns'].get('Negation') == 'Affirmed' and
            entity['meta_anns'].get('Experiencer') == 'Family')
    ]
```

**Use for**: Genetic risk assessment, family history documentation

---

### Pattern 4: Ruled-out conditions

```python
def get_ruled_out_conditions(entities):
    """Returns conditions explicitly ruled out or negated."""
    return [
        entity for entity in entities
        if entity['meta_anns'].get('Negation') == 'Negated'
    ]
```

**Use for**: Differential diagnosis tracking, documentation completeness

## Real-world impact example

**Clinical text**:
```
"Patient denies chest pain. No evidence of myocardial infarction.
Mother has diabetes. Currently experiencing shortness of breath.
Had pneumonia in 2020. Family history of breast cancer."
```

**Without meta-annotation filtering** (60% precision):
```python
entities = cat.get_entities(text)
# Returns: ["chest pain", "myocardial infarction", "diabetes",
#           "shortness of breath", "pneumonia", "breast cancer"]
# FALSE POSITIVES: chest pain (negated), MI (negated), diabetes (family),
#                  pneumonia (historical), breast cancer (family)
```

**With meta-annotation filtering** (95% precision):
```python
active_conditions = [
    e for e in entities
    if (e['meta_anns'].get('Negation') == 'Affirmed' and
        e['meta_anns'].get('Experiencer') == 'Patient' and
        e['meta_anns'].get('Temporality') in ['Current', 'Recent'])
]
# Returns: ["shortness of breath"]
# CORRECT: Only the active patient condition
```

## Elasticsearch integration

When storing MedCAT results in Elasticsearch, index meta-annotations as filterable fields:

```json
{
  "patient_id": "12345",
  "document_id": "67890",
  "concept": {
    "cui": "C0011849",
    "name": "Diabetes Mellitus",
    "negation": "Affirmed",
    "experiencer": "Patient",
    "temporality": "Current",
    "certainty": "Confirmed"
  }
}
```

**Query example** (Elasticsearch DSL):
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"concept.cui": "C0011849"}},
        {"term": {"concept.negation": "Affirmed"}},
        {"term": {"concept.experiencer": "Patient"}},
        {"terms": {"concept.temporality": ["Current", "Recent"]}}
      ]
    }
  }
}
```

## Frontend display patterns

### Display with context indicators

```typescript
// Good: Show context clearly
interface ConceptDisplay {
  name: string;
  negation: 'Affirmed' | 'Negated';
  experiencer: 'Patient' | 'Family' | 'Other';
  temporality: 'Current' | 'Historical' | 'Future';
  certainty: 'Confirmed' | 'Suspected' | 'Hypothetical';
}

// Visual indicators:
// ✓ Current, Affirmed, Patient, Confirmed - Green
// ⨯ Negated - Red strikethrough
// ⏱ Historical - Gray with date
// 👨‍👩‍👧 Family - Blue with family icon
// ? Suspected - Yellow with question mark
```

### Filtering UI

```vue
<template>
  <div class="concept-filters">
    <label>
      <input type="checkbox" v-model="filters.includeHistorical">
      Include historical conditions
    </label>
    <label>
      <input type="checkbox" v-model="filters.includeFamilyHistory">
      Include family history
    </label>
    <label>
      <input type="checkbox" v-model="filters.includeSuspected">
      Include suspected diagnoses
    </label>
  </div>
</template>
```

## Reference documentation

**Comprehensive guide**: See [docs/advanced/meta-annotations-guide.md](../../docs/advanced/meta-annotations-guide.md)

**MedCAT documentation**: MetaCAT component in MedCAT library

**Research paper**: Links to original meta-annotation research (if available in docs)

## Common mistakes to avoid

### Mistake 1: Ignoring meta-annotations entirely

```python
# BAD: Includes false positives
results = cat.get_entities(text)
concepts = [e['pretty_name'] for e in results]
```

### Mistake 2: Inconsistent filtering

```python
# BAD: Different filters in different parts of code
# File 1: Filters by Negation only
# File 2: Filters by Experiencer only
# File 3: No filtering
```

**Solution**: Create a centralized filtering function (Pattern 1 above)

### Mistake 3: Wrong filter for use case

```python
# BAD: Using historical filter for real-time alerts
if entity['meta_anns'].get('Temporality') == 'Historical':
    trigger_alert()  # Alert for old condition!
```

## Quick decision guide

**Building patient search**:
- Filter: Negation=Affirmed, Experiencer=Patient
- Temporality: Use case dependent (current vs all)

**Clinical decision support alerts**:
- Filter: Negation=Affirmed, Experiencer=Patient, Temporality=Current

**Cohort identification for research**:
- Filter: Negation=Affirmed, Experiencer=Patient
- Include: Historical (for past diagnoses)

**Family history tracking**:
- Filter: Experiencer=Family
- Include: Negation=Affirmed

**Differential diagnosis tracking**:
- Include: Certainty=Suspected
- May include: Negation=Negated (ruled out)

## Integration with other skills

Works with:
- `healthcare-compliance-checker`: Meta-annotations help prevent showing ruled-out conditions as active
- `fhir-r4-mapper`: Map meta-annotations to FHIR qualifiers
- `vue3-component-reuse`: Frontend components display meta-annotation context

## Testing meta-annotation filters

Test with edge cases:

```
Test text: "Patient denies chest pain. Mother has diabetes.
Had asthma as a child. Currently on insulin for diabetes."
```

Expected results (Negation=Affirmed, Experiencer=Patient, Temporality=Current):
- ✅ "diabetes" (current, patient)
- ❌ "chest pain" (negated)
- ❌ "diabetes" from "Mother has" (family)
- ⚠️ "asthma" (historical - include or exclude based on use case)

Always verify filtering logic with clinical SME review.
