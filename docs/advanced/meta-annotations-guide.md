# MedCAT Meta-Annotations: Advanced Context Detection

**Last Updated**: 2025-01-07
**Difficulty**: Intermediate
**Prerequisites**: Basic MedCAT usage, understanding of clinical NLP

---

## Table of Contents

1. [Overview](#overview)
2. [What Are Meta-Annotations?](#what-are-meta-annotations)
3. [Built-in Meta-Annotation Types](#built-in-meta-annotation-types)
4. [Practical Applications](#practical-applications)
5. [Configuration & Customization](#configuration--customization)
6. [Training Custom Meta-Annotation Models](#training-custom-meta-annotation-models)
7. [API Integration](#api-integration)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Overview

Meta-annotations add critical context to medical concepts extracted by MedCAT. While basic NLP identifies "diabetes" in a note, meta-annotations tell you whether:
- The patient **has** diabetes or **doesn't have** it (Negation)
- It's **current** or **historical** (Temporality)
- It's about the **patient** or **family history** (Experiencer)
- It's **confirmed** or **suspected** (Certainty)

**Without meta-annotations**: "Family history of diabetes" → False positive
**With meta-annotations**: Experiencer=Family → Correctly excluded

---

## What Are Meta-Annotations?

Meta-annotations are machine learning models that classify the **context** around extracted medical concepts.

### Example

**Clinical Note**:
```
Patient denies chest pain. Mother has history of diabetes.
Currently on metformin for type 2 diabetes diagnosed in 2020.
```

**MedCAT Output with Meta-Annotations**:

| Concept | CUI | Negation | Experiencer | Temporality | Certainty |
|---------|-----|----------|-------------|-------------|-----------|
| chest pain | C0008031 | **Negated** | Patient | Recent | Confirmed |
| diabetes | C0011849 | Affirmed | **Family** | Historical | Confirmed |
| type 2 diabetes | C0011860 | Affirmed | Patient | **Historical** | Confirmed |
| metformin | C0025598 | Affirmed | Patient | **Current** | Confirmed |

**Clinical Impact**: Without meta-annotations, query for "patients with diabetes" would incorrectly include this patient based on family history mention.

---

## Built-in Meta-Annotation Types

### 1. Negation Detection

**Purpose**: Distinguish between presence and absence of a condition.

**Values**:
- `Affirmed`: Condition is present
- `Negated`: Condition is explicitly absent

**Examples**:

| Text | Concept | Negation |
|------|---------|----------|
| "Patient has pneumonia" | pneumonia | Affirmed |
| "No evidence of pneumonia" | pneumonia | **Negated** |
| "Denies chest pain" | chest pain | **Negated** |
| "Rule out appendicitis" | appendicitis | **Negated** (implicit) |

**Clinical Applications**:
- Exclude false positives in cohort identification
- Distinguish diagnostic workup from confirmed diagnoses
- Safety alerts (e.g., drug allergies)

---

### 2. Temporality Detection

**Purpose**: Determine when the condition occurred relative to the current encounter.

**Values**:
- `Recent` / `Current`: Active, ongoing condition
- `Historical`: Past condition, may or may not be active
- `Future`: Planned interventions or potential future events

**Examples**:

| Text | Concept | Temporality |
|------|---------|-------------|
| "Currently experiencing dyspnea" | dyspnea | **Recent** |
| "History of myocardial infarction in 2015" | MI | **Historical** |
| "Plan for colonoscopy next month" | colonoscopy | **Future** |
| "Chronic kidney disease stage 3" | CKD | **Current** |

**Clinical Applications**:
- Quality metrics (active vs resolved conditions)
- Care gap identification (chronic disease management)
- Acute vs chronic disease differentiation
- Treatment timeline analysis

---

### 3. Experiencer Detection

**Purpose**: Identify who the condition refers to.

**Values**:
- `Patient`: The condition affects the patient
- `Family`: Family history
- `Other`: Healthcare provider, other person

**Examples**:

| Text | Concept | Experiencer |
|------|---------|-------------|
| "Patient diagnosed with diabetes" | diabetes | **Patient** |
| "Mother died of breast cancer" | breast cancer | **Family** |
| "Sister has asthma" | asthma | **Family** |
| "Physician suspects pneumonia" | pneumonia | **Other** |

**Clinical Applications**:
- Exclude family history from active diagnoses
- Genetic risk stratification
- Clinical trial eligibility (exclude family history mentions)
- Pharmacogenomics (identify inherited conditions)

---

### 4. Certainty / Hypothetical

**Purpose**: Determine confidence level or speculative nature.

**Values**:
- `Confirmed`: Definite diagnosis
- `Suspected` / `Possible`: Differential diagnosis
- `Hypothetical`: Conditional or speculative

**Examples**:

| Text | Concept | Certainty |
|------|---------|-----------|
| "Diagnosed with hypertension" | hypertension | **Confirmed** |
| "Possible pneumonia" | pneumonia | **Suspected** |
| "Rule out pulmonary embolism" | PE | **Suspected** |
| "If symptoms worsen, consider sepsis" | sepsis | **Hypothetical** |

**Clinical Applications**:
- Distinguish confirmed from working diagnoses
- Track diagnostic uncertainty
- Research: analyze diagnostic processes
- Audit: documentation quality assessment

---

## Practical Applications

### Application 1: Cohort Identification for Clinical Pathways

**Scenario**: Identify patients with **active** heart failure for HF pathway enrollment.

**Challenge**: Notes contain:
- Current HF diagnoses
- Historical HF (resolved)
- Family history of HF
- Rule-out HF (differential)

**Solution with Meta-Annotations**:

```python
from medcat.cat import CAT

cat = CAT.load_model_pack("./models/medcat_model.zip")

# Get entities with meta-annotations
doc = cat("Patient with acute decompensated heart failure...")
entities = doc.ents

# Filter for active, confirmed, patient HF
active_hf_patients = []
for ent in entities:
    if (ent._.cui == "C0018802" and  # Heart Failure CUI
        ent._.meta_anns.get('Negation') == 'Affirmed' and
        ent._.meta_anns.get('Experiencer') == 'Patient' and
        ent._.meta_anns.get('Temporality') in ['Recent', 'Current'] and
        ent._.meta_anns.get('Certainty') == 'Confirmed'):
        active_hf_patients.append(ent)
```

**Result**: 95% precision (vs. 60% without meta-annotations)

---

### Application 2: Adverse Event Detection

**Scenario**: Identify patients experiencing drug side effects (not family history or hypothetical).

**Example Note**:
```
Patient reports nausea after starting metformin.
Mother had severe nausea with chemotherapy.
If nausea continues, will consider alternative agent.
```

**Query with Meta-Annotations**:

| Mention | Experiencer | Certainty | Include? |
|---------|-------------|-----------|----------|
| "nausea after starting metformin" | **Patient** | Confirmed | ✓ Yes |
| "Mother had severe nausea" | **Family** | Confirmed | ✗ No |
| "If nausea continues" | Patient | **Hypothetical** | ✗ No |

**Result**: Only true patient-experienced side effects reported.

---

### Application 3: Clinical Decision Support

**Scenario**: Alert for contraindications (e.g., prescribing aspirin to patient with bleeding disorder).

**Challenge**: Distinguish current contraindications from historical or negated mentions.

**Example**:
```
History of GI bleed in 2010, resolved.
No active bleeding disorders.
```

**Meta-Annotation Analysis**:
- "GI bleed" → Temporality=Historical, Negation=Affirmed → **Low risk**
- "bleeding disorders" → Negation=**Negated** → **No contraindication**

**Action**: Aspirin can be safely prescribed.

---

## Configuration & Customization

### Enabling Meta-Annotations

**Model Pack Requirements**: Ensure your MedCAT model includes MetaCAT models.

```python
from medcat.cat import CAT

# Load model with MetaCAT
cat = CAT.load_model_pack("./models/medcat_model_with_meta.zip")

# Check available meta-annotation models
print(cat.config.general['meta_cat_config_dict'])

# Output:
# {
#   'Negation': {'model_path': './models/negation_model'},
#   'Temporality': {'model_path': './models/temporality_model'},
#   'Experiencer': {'model_path': './models/experiencer_model'}
# }
```

---

### Configuring Meta-Annotation Behavior

**config.json** (within model pack):

```json
{
  "general": {
    "meta_cat_config_dict": {
      "Negation": {
        "model_path": "./models/negation",
        "category_name": "Negation",
        "category_values": ["Affirmed", "Negated"],
        "default_value": "Affirmed"
      },
      "Temporality": {
        "model_path": "./models/temporality",
        "category_name": "Temporality",
        "category_values": ["Recent", "Historical", "Future"],
        "default_value": "Recent"
      },
      "Experiencer": {
        "model_path": "./models/experiencer",
        "category_name": "Experiencer",
        "category_values": ["Patient", "Family", "Other"],
        "default_value": "Patient"
      }
    }
  }
}
```

---

## Training Custom Meta-Annotation Models

### When to Train Custom Models

- Default models insufficient for your domain (e.g., radiology, pathology)
- Local terminology differs significantly
- Need additional meta-annotation types (e.g., Severity, Acuity)

### Training Workflow

**Step 1: Prepare Training Data**

```python
# Annotate examples using MedCAT Trainer or manual annotation
training_data = [
    {
        "text": "Patient denies chest pain",
        "entities": [
            {
                "start": 14, "end": 24,
                "cui": "C0008031",
                "meta_anns": {"Negation": "Negated"}
            }
        ]
    },
    {
        "text": "Mother has diabetes",
        "entities": [
            {
                "start": 11, "end": 19,
                "cui": "C0011849",
                "meta_anns": {"Experiencer": "Family"}
            }
        ]
    }
]
```

**Step 2: Train MetaCAT Model**

```python
from medcat.meta_cat import MetaCAT

# Initialize MetaCAT
meta_cat = MetaCAT(tokenizer=cat.cdb.addl_info['tokenizer'],
                    embeddings=cat.cdb.addl_info['embeddings'])

# Configure meta-annotation type
meta_cat_config = {
    "category_name": "Negation",
    "category_values": ["Affirmed", "Negated"],
    "model_architecture": "lstm",  # or 'transformer'
    "epochs": 10,
    "lr": 0.001
}

# Train
meta_cat.train(training_data, config=meta_cat_config)

# Save
meta_cat.save("./models/custom_negation_model")
```

**Step 3: Integrate into CAT**

```python
# Load and add to CAT
cat.add_meta_cat(meta_cat, category_name="Negation")

# Save updated model pack
cat.create_model_pack("./models/medcat_with_custom_meta.zip")
```

---

## API Integration

### REST API with Meta-Annotations

**MedCAT Service Configuration**:

```yaml
# docker-compose.yml
services:
  medcat-service:
    environment:
      - ENABLE_META_ANNOTATIONS=true
      - META_CAT_MODELS=Negation,Temporality,Experiencer
```

**API Request**:

```bash
curl -X POST http://localhost:5000/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient denies chest pain. History of diabetes.",
    "include_meta": true
  }'
```

**API Response**:

```json
{
  "entities": [
    {
      "cui": "C0008031",
      "source_value": "chest pain",
      "start": 14,
      "end": 24,
      "meta_anns": {
        "Negation": "Negated",
        "Experiencer": "Patient",
        "Temporality": "Recent"
      }
    },
    {
      "cui": "C0011849",
      "source_value": "diabetes",
      "start": 37,
      "end": 45,
      "meta_anns": {
        "Negation": "Affirmed",
        "Experiencer": "Patient",
        "Temporality": "Historical"
      }
    }
  ]
}
```

---

## Troubleshooting

### Issue: Meta-Annotations Always Default Value

**Cause**: MetaCAT models not loaded.

**Solution**:
```python
# Check if meta_cats are present
print(cat.config.general.get('meta_cat_config_dict'))

# If None, download models with MetaCAT
cat = CAT.load_model_pack("./models/model_with_meta.zip")
```

---

### Issue: Poor Accuracy for Negation

**Cause**: Model not trained on domain-specific negation patterns.

**Examples**: Radiology often uses "no evidence of" vs clinical notes "denies"

**Solution**: Train custom negation model with domain-specific examples.

---

### Issue: Experiencer Confusion (Patient vs Family)

**Cause**: Ambiguous pronouns or family history sections.

**Solution**:
- Improve training data with edge cases
- Add section detection (Family History section → Experiencer=Family)
- Post-processing rules for specific patterns

---

## Best Practices

### 1. Always Validate Meta-Annotations

**Don't blindly trust**: Manually review sample (100+ annotations) before production use.

```python
# Validation script
import pandas as pd

results = []
for doc in validation_set:
    entities = cat(doc.text).ents
    for ent in entities:
        results.append({
            'text': ent.text,
            'negation_predicted': ent._.meta_anns.get('Negation'),
            'negation_actual': doc.get_label(ent, 'Negation'),
            'correct': ent._.meta_anns.get('Negation') == doc.get_label(ent, 'Negation')
        })

df = pd.DataFrame(results)
print(f"Negation Accuracy: {df['correct'].mean():.2%}")
```

---

### 2. Combine Meta-Annotations

**Example**: Patient cohort requires:
- Negation=Affirmed AND
- Experiencer=Patient AND
- Temporality=Current

```python
def is_active_patient_condition(entity):
    meta = entity._.meta_anns
    return (meta.get('Negation') == 'Affirmed' and
            meta.get('Experiencer') == 'Patient' and
            meta.get('Temporality') in ['Recent', 'Current'])
```

---

### 3. Monitor Model Drift

**Track accuracy over time**:
- Set up regular validation against held-out test set
- Alert if accuracy drops >5%
- Retrain with new annotated examples quarterly

---

### 4. Document Your Configuration

```markdown
## Meta-Annotation Configuration

- **Negation Model**: Custom trained on radiology reports (2023-Q4)
- **Temporality Model**: MedCAT default v1.2
- **Experiencer Model**: Custom trained with family history edge cases

**Validation Results** (2024-01-15):
- Negation: 94.2% accuracy (n=500)
- Temporality: 88.1% accuracy (n=500)
- Experiencer: 96.7% accuracy (n=500)
```

---

## Related Resources

- [MedCAT Trainer](../../medcat-trainer/) - Annotate training data for meta-models
- [MedCAT Documentation](https://github.com/CogStack/MedCAT)
- [Research Paper: Context Detection in Clinical NLP](https://arxiv.org/abs/2010.01165)

---

## Next Steps

1. **Test with your data**: Load model, process 10 documents, inspect meta-annotations
2. **Measure baseline**: Calculate accuracy on validation set
3. **Train custom model** (if needed): Annotate 500+ examples, train MetaCAT
4. **Integrate into pipelines**: Update cohort queries to use meta-annotations
5. **Monitor and iterate**: Track accuracy, retrain quarterly

---

**Questions?** Visit the [CogStack Forum](https://discourse.cogstack.org/) or open an issue on [GitHub](https://github.com/CogStack/cogstack-nlp).
