# MedCAT PHI Detection Model Card

**Model Name**: `medcat_phi_v1.0`
**Model Type**: Named Entity Recognition (NER) for Protected Health Information (PHI)
**Model Version**: 1.0.0
**Last Updated**: TBD (awaiting training completion)
**Status**: 🚧 **IN DEVELOPMENT** - Awaiting i2b2 2014 dataset and training infrastructure

---

## Model Overview

### Purpose
Detect 18 HIPAA Safe Harbor PHI identifiers in clinical text to enable de-identification and privacy-preserving research.

### Use Cases
- **Document De-identification**: Remove PHI from clinical notes before research use
- **Privacy Compliance**: HIPAA/GDPR compliance auditing
- **Redaction**: Automatic PHI masking for external sharing
- **Audit Logging**: Track PHI access for compliance

### Out of Scope
- ❌ Diagnosis or treatment decisions (not a clinical decision support tool)
- ❌ Patient identification (de-identification only)
- ❌ Structured data de-identification (EHR fields, databases)

---

## Model Details

### Architecture
- **Base Model**: MedCAT v2.x NER model
- **Training Approach**: Fine-tuning pre-trained clinical NER model
- **Transfer Learning**: Freeze embedding layers, train classification head
- **Framework**: PyTorch + Transformers

### Training Data
- **Dataset**: i2b2 2014 De-identification Challenge corpus
  - Source: PhysioNet (requires CITI training + data use agreement)
  - Size: 1,296 clinical notes with PHI annotations
  - Annotations: ~35,000 PHI entity labels
  - Split: 70% train (907 notes), 15% validation (194 notes), 15% test (195 notes)
  - Note Types: H&P, discharge summaries, progress notes, consult notes

### PHI Categories (18 HIPAA Safe Harbor Identifiers)

| Category | Examples | Expected F1 |
|----------|----------|-------------|
| 1. Names | "John Smith", "Dr. Jane Doe" | >0.90 |
| 2. Geographic locations | "123 Main St, London EC1A 1BB" | >0.85 |
| 3. Dates (except year) | "15/03/2023", "March 15" | >0.90 |
| 4. Telephone numbers | "020-7123-4567" | >0.95 |
| 5. Fax numbers | "020-7123-4568" | >0.95 |
| 6. Email addresses | "patient@nhs.net" | >0.95 |
| 7. NHS numbers (UK) / SSN (US) | "123 456 7890" | >0.95 |
| 8. Medical record numbers | "MRN-2023-001234" | >0.90 |
| 9. Health plan beneficiary numbers | "PLAN-123456" | >0.85 |
| 10. Account numbers | "ACC-789012" | >0.85 |
| 11. Certificate/license numbers | "GMC-1234567" | >0.85 |
| 12. Vehicle identifiers | "AB12 CDE" | >0.80 |
| 13. Device identifiers | "SN-987654321" | >0.80 |
| 14. URLs | "https://patient.nhs.uk/123" | >0.95 |
| 15. IP addresses | "192.168.1.100" | >0.95 |
| 16. Biometric identifiers | "Fingerprint ID: 123" | >0.75 |
| 17. Full-face photos | (metadata detection) | >0.70 |
| 18. Unique identifying numbers | "ID-ABC123" | >0.80 |

---

## Training Configuration

### Hyperparameters
```yaml
# Model
base_model: "medcat_snomed_v1"  # Pre-trained clinical NER model
embedding_dim: 300
hidden_dim: 512
num_layers: 2
dropout: 0.3

# Training
learning_rate: 0.0001  # Low LR for fine-tuning
batch_size: 16
epochs: 20
early_stopping_patience: 3
optimizer: AdamW
scheduler: ReduceLROnPlateau

# Transfer Learning
freeze_embeddings: true  # Initially freeze, unfreeze after epoch 5
freeze_encoder: false
warmup_epochs: 2

# Data Augmentation
augmentation: true
synonym_replacement_prob: 0.1
entity_masking_prob: 0.15
```

### Training Procedure
1. **Preprocessing** (2 hours):
   - Parse i2b2 XML annotations
   - Convert to MedCAT training format
   - Validate annotation quality (IAA >0.90)
   - Generate train/val/test splits (70/15/15)

2. **Initial Fine-tuning** (40 hours):
   - Load pre-trained `medcat_snomed` model
   - Freeze embedding layers
   - Train classification head (5 epochs)
   - Validate on validation set

3. **Full Fine-tuning** (60 hours):
   - Unfreeze all layers
   - Train end-to-end (15 epochs)
   - Early stopping (patience=3)
   - Hyperparameter tuning (learning rate, batch size)

4. **Evaluation** (10 hours):
   - Test on held-out test set (195 notes)
   - Calculate per-category precision, recall, F1
   - Generate confusion matrix
   - Error analysis (false positives/negatives)

5. **Iteration** (if needed, 20 hours):
   - Address low-performing categories
   - Retrain with adjusted hyperparameters
   - Re-evaluate until targets met

---

## Performance Metrics

### Target Metrics
- **Overall Precision**: >95%
- **Overall Recall**: >90%
- **Overall F1 Score**: >0.92
- **Per-Category F1**: All >0.85 (see table above)
- **Inference Speed**: <2 min per 10-page note (~5000 words)

### Actual Metrics (TBD - awaiting training completion)

**⚠️ TRAINING NOT STARTED**: Metrics will be populated after model training

```yaml
# Placeholder - replace after training
overall_precision: TBD
overall_recall: TBD
overall_f1: TBD

per_category_f1:
  names: TBD
  geographic_locations: TBD
  dates: TBD
  telephone_numbers: TBD
  email_addresses: TBD
  nhs_numbers: TBD
  # ... (18 categories total)

inference_speed:
  avg_time_per_document: TBD  # seconds
  avg_time_per_10_pages: TBD  # seconds
  throughput: TBD  # documents/hour
```

### Confusion Matrix
TBD - will be generated after training

### Error Analysis
TBD - will document common false positives/negatives

---

## Limitations

### Known Limitations
1. **Non-Standard Formats**: May miss PHI in unusual formats (e.g., DOB written as "born March fifteen, nineteen eighty")
2. **Abbreviations**: May miss abbreviated names (e.g., "J. Smith" vs "John Smith")
3. **Context Ambiguity**: May misclassify common words as PHI (e.g., "Smith" as surname vs "Smith fracture")
4. **Multi-Lingual**: Trained on English clinical text only (UK/US)
5. **Domain Specificity**: Optimized for clinical notes (may underperform on other healthcare documents)

### Mitigation Strategies
- **Human Review**: Always review automated de-identification (especially for high-risk use cases)
- **Confidence Thresholds**: Flag low-confidence detections (<0.8 accuracy) for manual review
- **Allowlists**: Maintain allowlist of clinical terms (to reduce false positives)
- **Regular Updates**: Retrain model quarterly on new clinical text patterns

---

## Ethical Considerations

### Privacy & Safety
- **Purpose**: De-identification to PROTECT patient privacy (not to identify patients)
- **Risk of Re-identification**: Even with de-identification, statistical attacks may re-identify patients
- **HIPAA Compliance**: De-identification must meet HIPAA Safe Harbor OR Expert Determination standards
- **Manual Review Required**: Automated de-identification should be reviewed by privacy experts

### Bias & Fairness
- **Training Data Bias**: i2b2 corpus from US hospitals (may underrepresent UK clinical writing styles)
- **Name Bias**: May perform worse on non-Western names (e.g., South Asian, East Asian names)
- **Geographic Bias**: UK postcodes have different format than US ZIP codes
- **Mitigation**: Evaluate model on diverse test sets, retrain on UK clinical notes if needed

### Transparency
- **Model Decisions**: Always show confidence scores with PHI detections
- **False Negatives**: Communicate risk of missed PHI (recall <100%)
- **Auditability**: Log all de-identification operations for compliance audits

---

## Usage

### Loading Model
```python
from medcat.cat import CAT

# Load fine-tuned PHI detection model
cat = CAT.load_model_pack("/models/medcat_phi_v1.0.model")
```

### Inference Example
```python
# Clinical text with PHI
text = """
Patient John Smith (NHS 123 456 7890) presented with chest pain.
DOB: 15/03/1980. Contact: 020-7123-4567.
"""

# Detect PHI
entities = cat.get_entities(text)
phi_entities = [e for e in entities if e["types"][0].startswith("PHI")]

# Print detected PHI
for entity in phi_entities:
    print(f"{entity['pretty_name']} ({entity['types'][0]}) - Confidence: {entity['accuracy']:.2f}")

# Output:
# John Smith (PHI_NAME) - Confidence: 0.97
# 123 456 7890 (PHI_NHS_NUMBER) - Confidence: 0.99
# 15/03/1980 (PHI_DATE) - Confidence: 0.95
# 020-7123-4567 (PHI_PHONE) - Confidence: 0.98
```

### Integration with CogStack-ModelServe
```bash
# Test PHI detection via API
curl -X POST http://localhost:8001/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient John Smith, NHS 123 456 7890",
    "model_name": "medcat_phi_v1"
  }'
```

---

## Deployment

### Infrastructure Requirements
- **GPU**: NVIDIA GPU with 8-16GB VRAM (for training)
- **CPU**: Multi-core CPU (for inference, 4+ cores recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB for model files
- **OS**: Ubuntu 20.04+ or Docker container

### Model Serving
- **Service**: CogStack-ModelServe v2.x
- **API Endpoint**: `POST /api/process`
- **Model Path**: `/models/medcat_phi_v1.0.model`
- **Loading Time**: ~30-60 seconds on startup
- **Concurrency**: Support multiple concurrent requests (via async)

### Monitoring
- **Inference Speed**: Track avg processing time (target: <2 min per 10 pages)
- **Error Rate**: Track ModelServe errors (timeouts, OOM)
- **Model Drift**: Periodically evaluate on new clinical notes (quarterly)
- **Confidence Distribution**: Monitor distribution of accuracy scores (flag if many <0.8)

---

## Maintenance

### Retraining Schedule
- **Quarterly**: Retrain on new clinical notes (if available)
- **On Demand**: Retrain if performance degrades (F1 drops below 0.90)
- **Version Control**: Tag models with semantic versioning (v1.0, v1.1, v2.0)

### Model Versioning
```
medcat_phi_v1.0.model  ← Initial release (i2b2 2014)
medcat_phi_v1.1.model  ← Retrained with UK clinical notes
medcat_phi_v2.0.model  ← Architecture change (e.g., transformer upgrade)
```

### Evaluation on Production Data
- **Monthly Audit**: Sample 100 de-identified notes, manually review PHI detection
- **Error Logging**: Log false negatives discovered in production
- **Feedback Loop**: Use production errors to retrain model

---

## References

### Datasets
- i2b2 2014 De-identification Challenge: https://portal.dbmi.hms.harvard.edu/projects/n2c2-nlp/
- PhysioNet: https://physionet.org/

### Papers
- MedCAT: https://arxiv.org/abs/2010.01165
- HIPAA Safe Harbor: https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html
- i2b2 De-identification Challenge: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4419867/

### Tools
- MedCAT: https://github.com/CogStack/MedCAT
- CogStack-ModelServe: https://github.com/CogStack/CogStack-ModelServe
- Transformers: https://huggingface.co/transformers/

---

## Model Card Authors

- **Author**: CogStack NLP Development Team
- **Contact**: [Team contact information]
- **License**: [Model license - e.g., Apache 2.0 for code, proprietary for model weights]
- **Citation**: TBD (if model is published)

---

## Changelog

### v1.0.0 (TBD - In Development)
- **Status**: Awaiting i2b2 2014 dataset acquisition and training infrastructure
- **Blockers**:
  1. i2b2 2014 corpus download (requires PhysioNet account + CITI training)
  2. GPU infrastructure for training (8-16GB VRAM)
  3. 120 hours of ML engineering time for fine-tuning and validation
- **Next Steps**:
  1. Obtain PhysioNet access
  2. Download and preprocess i2b2 2014 corpus
  3. Fine-tune MedCAT model
  4. Validate on test set
  5. Deploy to CogStack-ModelServe
  6. Update this model card with actual metrics

---

**⚠️ STATUS**: This model card is a TEMPLATE. Model training has NOT started. Actual metrics and performance data will be added after training completion (estimated: 3 weeks of ML engineering work).

**See**: `.claude/ccpm/epics/de-identification-module/001.md` for implementation task details.
