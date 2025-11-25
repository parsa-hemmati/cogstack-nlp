# PHI Detection Model Training Report

**Model**: `medcat_phi_v1.0`
**Training Date**: TBD (awaiting dataset and infrastructure)
**Report Author**: CogStack NLP Development Team
**Report Version**: 1.0.0 (TEMPLATE)
**Status**: 🚧 **TRAINING NOT STARTED** - Awaiting i2b2 2014 dataset acquisition

---

## Executive Summary

**⚠️ PLACEHOLDER**: This report will be populated after model training completion.

### Key Metrics (Target vs Actual)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Overall Precision | >95% | TBD | ⏳ Pending |
| Overall Recall | >90% | TBD | ⏳ Pending |
| Overall F1 Score | >0.92 | TBD | ⏳ Pending |
| Inference Speed (10 pages) | <2 min | TBD | ⏳ Pending |
| Per-Category F1 (all 18) | >0.85 | TBD | ⏳ Pending |

### Training Summary
- **Training Duration**: TBD hours (estimated: 60-80 hours)
- **Training Dataset**: i2b2 2014 De-identification Challenge (1,296 notes)
- **Validation Strategy**: 70/15/15 train/val/test split
- **Final Model Size**: TBD MB
- **GPU Utilization**: TBD% average

---

## 1. Training Dataset

### 1.1 Dataset Acquisition
**⚠️ BLOCKED**: i2b2 2014 corpus download requires:
1. PhysioNet account (https://physionet.org/register/)
2. CITI training completion (research ethics certification)
3. Data Use Agreement (DUA) signed

**Status**: Dataset NOT acquired yet.

**Timeline**:
- PhysioNet account creation: 1 day
- CITI training completion: 3-5 days
- DUA approval: 1-2 weeks
- Dataset download: 1 day

**Next Steps**: Assign team member to complete CITI training and obtain PhysioNet access.

### 1.2 Dataset Statistics

**i2b2 2014 De-identification Challenge Corpus**:
- **Total Notes**: 1,296 clinical notes
- **Total PHI Annotations**: ~35,000 entities
- **Note Types**: History & Physical (H&P), Discharge Summaries, Progress Notes, Consult Notes
- **Average Note Length**: 2,500 words (range: 500-10,000 words)
- **PHI Density**: ~27 PHI entities per note (average)

**PHI Category Distribution** (from i2b2 2014 paper):
| PHI Category | Count | Percentage |
|--------------|-------|------------|
| Names | 8,500 | 24% |
| Dates | 12,000 | 34% |
| Locations | 5,000 | 14% |
| Phone Numbers | 2,500 | 7% |
| NHS/SSN Numbers | 1,500 | 4% |
| Email Addresses | 800 | 2% |
| URLs | 400 | 1% |
| Other Identifiers | 4,300 | 12% |
| **Total** | **35,000** | **100%** |

### 1.3 Dataset Splits

**Split Strategy**: Stratified random split (maintain PHI category distribution)

| Split | Notes | PHI Entities | Percentage |
|-------|-------|--------------|------------|
| Training | 907 | ~24,500 | 70% |
| Validation | 194 | ~5,250 | 15% |
| Test | 195 | ~5,250 | 15% |
| **Total** | **1,296** | **~35,000** | **100%** |

### 1.4 Data Preprocessing

**Preprocessing Steps**:
1. **Parse XML Annotations**: Extract PHI entity spans and types from i2b2 XML format
2. **Convert to MedCAT Format**: Transform to MedCAT training format (JSON with entity offsets)
3. **Quality Validation**:
   - Check annotation completeness (all notes have annotations)
   - Verify entity span boundaries (start/end chars within text)
   - Calculate inter-annotator agreement (IAA >0.90 expected)
4. **Tokenization**: Pre-tokenize text for faster training
5. **Entity Type Mapping**: Map i2b2 categories to 18 HIPAA Safe Harbor identifiers

**Quality Checks** (TBD after dataset acquisition):
- Inter-Annotator Agreement (IAA): TBD (expected >0.90)
- Annotation Coverage: TBD% (expected >99%)
- Entity Span Validation: TBD errors found (expected <10)

---

## 2. Model Architecture

### 2.1 Base Model
- **Model**: MedCAT v2.x pre-trained clinical NER model
- **Embedding Dimension**: 300 (from pre-trained embeddings)
- **Vocabulary Size**: ~400,000 clinical terms (SNOMED-CT + UMLS)
- **Pretrained On**: MIMIC-III clinical notes (2 million notes)

### 2.2 Fine-Tuning Architecture
```
Input Text
  ↓
Clinical Word Embeddings (pre-trained, frozen initially)
  ↓
BiLSTM Encoder (2 layers, 512 hidden units)
  ↓
CRF Layer (Conditional Random Field for sequence labeling)
  ↓
18 PHI Categories + O (Outside) = 19 labels
```

### 2.3 Model Parameters
- **Total Parameters**: TBD million (estimated: 50-100M)
- **Trainable Parameters**: TBD million (after freezing embeddings)
- **Model Size**: TBD MB (estimated: 500 MB - 2 GB)

---

## 3. Training Configuration

### 3.1 Hyperparameters

**Chosen Hyperparameters**:
```yaml
# Optimizer
optimizer: AdamW
learning_rate: 0.0001  # Low LR for fine-tuning
weight_decay: 0.01
beta1: 0.9
beta2: 0.999

# Training
batch_size: 16  # Limited by GPU memory
epochs: 20
early_stopping_patience: 3  # Stop if no improvement for 3 epochs

# Learning Rate Schedule
scheduler: ReduceLROnPlateau
factor: 0.5  # Reduce LR by 50% on plateau
patience: 2
min_lr: 0.00001

# Transfer Learning
freeze_embeddings: true  # Initially freeze
unfreeze_at_epoch: 5  # Unfreeze after 5 epochs
warmup_epochs: 2

# Regularization
dropout: 0.3
label_smoothing: 0.1  # Prevent overconfidence

# Data Augmentation
augmentation: true
synonym_replacement_prob: 0.1
entity_masking_prob: 0.15
```

### 3.2 Hardware Configuration
```yaml
# GPU
gpu: NVIDIA RTX A6000 (48GB VRAM)  # Example - TBD
gpu_count: 1
cuda_version: 11.8

# CPU
cpu_cores: 16
ram: 64GB

# Storage
ssd: 500GB NVMe (fast model loading)
```

### 3.3 Training Procedure

**Phase 1: Embedding Freezing (Epochs 1-5)**
- Freeze word embeddings (prevent catastrophic forgetting)
- Train only BiLSTM encoder + CRF layer
- Low learning rate (0.0001)
- Goal: Adapt to PHI detection task without forgetting clinical knowledge

**Phase 2: Full Fine-Tuning (Epochs 6-20)**
- Unfreeze all layers
- End-to-end training
- Learning rate decay (ReduceLROnPlateau)
- Early stopping (patience=3)
- Goal: Optimize all parameters for PHI detection

**Training Loop**:
```python
for epoch in range(1, 21):
    # Unfreeze embeddings at epoch 5
    if epoch == 5:
        model.unfreeze_embeddings()

    # Training
    train_loss = train_epoch(model, train_loader, optimizer)

    # Validation
    val_loss, val_f1 = validate_epoch(model, val_loader)

    # Learning rate scheduling
    scheduler.step(val_loss)

    # Early stopping
    if no_improvement_for_3_epochs:
        break

    # Save best model
    if val_f1 > best_f1:
        save_model(model, f"medcat_phi_v1.0_epoch{epoch}.model")
        best_f1 = val_f1
```

---

## 4. Training Results

### 4.1 Training Curves

**⚠️ PLACEHOLDER**: Training curves will be generated after training.

**Metrics to Track**:
- Training loss (per epoch)
- Validation loss (per epoch)
- Validation F1 score (per epoch)
- Learning rate (per epoch)

**Expected Curves**:
```
Training Loss: Decreasing (from ~2.0 to ~0.5)
Validation Loss: Decreasing then plateau (from ~2.0 to ~0.6)
Validation F1: Increasing (from ~0.70 to >0.92)
Learning Rate: Decreasing (0.0001 → 0.00001)
```

### 4.2 Training Time

**Total Training Time**: TBD hours (estimated: 60-80 hours)

**Breakdown**:
- Data preprocessing: TBD hours (estimated: 2 hours)
- Phase 1 (epochs 1-5): TBD hours (estimated: 20 hours)
- Phase 2 (epochs 6-20): TBD hours (estimated: 40 hours)
- Hyperparameter tuning: TBD hours (estimated: 20 hours)

### 4.3 Convergence

**Convergence Criteria**:
- Validation F1 > 0.92 (met: TBD)
- No improvement for 3 consecutive epochs (met: TBD)
- Training loss < 0.5 (met: TBD)

**Final Epoch**: TBD (out of 20 max)

---

## 5. Validation Results

### 5.1 Overall Metrics (Test Set)

**⚠️ PLACEHOLDER**: Metrics will be calculated after training.

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Precision** | TBD% | >95% | TBD |
| **Recall** | TBD% | >90% | TBD |
| **F1 Score** | TBD | >0.92 | TBD |
| **Accuracy** | TBD% | >95% | TBD |

**Interpretation**:
- **Precision**: TBD% of predicted PHI are actual PHI (false positive rate: TBD%)
- **Recall**: TBD% of actual PHI are detected (false negative rate: TBD%)
- **F1 Score**: Harmonic mean of precision and recall

### 5.2 Per-Category Results

**⚠️ PLACEHOLDER**: Per-category metrics will be calculated after training.

| PHI Category | Precision | Recall | F1 | Target F1 | Status |
|--------------|-----------|--------|-----|-----------|--------|
| 1. Names | TBD% | TBD% | TBD | >0.90 | TBD |
| 2. Geographic Locations | TBD% | TBD% | TBD | >0.85 | TBD |
| 3. Dates | TBD% | TBD% | TBD | >0.90 | TBD |
| 4. Telephone Numbers | TBD% | TBD% | TBD | >0.95 | TBD |
| 5. Email Addresses | TBD% | TBD% | TBD | >0.95 | TBD |
| 6. NHS/SSN Numbers | TBD% | TBD% | TBD | >0.95 | TBD |
| 7. Medical Record Numbers | TBD% | TBD% | TBD | >0.90 | TBD |
| 8. URLs | TBD% | TBD% | TBD | >0.95 | TBD |
| 9. IP Addresses | TBD% | TBD% | TBD | >0.95 | TBD |
| ... (18 total) | ... | ... | ... | ... | ... |

### 5.3 Confusion Matrix

**⚠️ PLACEHOLDER**: Confusion matrix will be generated after training.

**Interpretation**:
- **Rows**: Actual PHI categories
- **Columns**: Predicted PHI categories
- **Diagonal**: Correct predictions (high values = good)
- **Off-diagonal**: Misclassifications (low values = good)

**Expected Issues**:
- **Names vs Locations**: Common words (e.g., "Washington") may be ambiguous
- **Dates vs Medical Concepts**: Date patterns (e.g., "2nd degree burn") may confuse model
- **Phone vs Account Numbers**: Similar digit patterns

---

## 6. Error Analysis

### 6.1 False Positives (Over-Detection)

**⚠️ PLACEHOLDER**: Examples will be analyzed after training.

**Common False Positive Patterns** (expected):
1. **Clinical Terms Misclassified as Names**:
   - Example: "Smith fracture" → Detected as "Smith" (name)
   - Mitigation: Add clinical term allowlist

2. **Dates in Medical Contexts**:
   - Example: "Stage 2 cancer" → Detected as date ("2")
   - Mitigation: Context-aware classification

3. **Common Words as Locations**:
   - Example: "Washington criterion" → Detected as location
   - Mitigation: Medical knowledge base integration

### 6.2 False Negatives (Missed PHI)

**⚠️ PLACEHOLDER**: Examples will be analyzed after training.

**Common False Negative Patterns** (expected):
1. **Abbreviated Names**:
   - Example: "J. Smith" not detected (model trained on full names)
   - Mitigation: Data augmentation with abbreviations

2. **Non-Standard Date Formats**:
   - Example: "Born March fifteen, nineteen eighty" not detected
   - Mitigation: Add written-out date patterns

3. **Partial Addresses**:
   - Example: "Lives in London" not detected (missing street address)
   - Mitigation: Lower detection threshold for location keywords

### 6.3 Error Impact Assessment

**HIPAA Compliance Risk**:
- **False Negatives**: HIGH RISK (missed PHI = privacy breach)
  - Mitigation: Human review required for all de-identification
  - Target: False negative rate <10%

- **False Positives**: LOW RISK (over-redaction = loss of clinical utility)
  - Mitigation: Manual correction of over-redacted text
  - Acceptable: False positive rate <5%

**Recommendation**: Err on side of caution (prefer false positives over false negatives)

---

## 7. Performance Benchmarks

### 7.1 Inference Speed

**⚠️ PLACEHOLDER**: Benchmarks will be measured after deployment.

| Document Type | Avg Length | Avg Time | Target | Status |
|---------------|------------|----------|--------|--------|
| Progress Note (1 page) | 500 words | TBD sec | <12 sec | TBD |
| Discharge Summary (5 pages) | 2,500 words | TBD sec | <60 sec | TBD |
| H&P Report (10 pages) | 5,000 words | TBD sec | <120 sec | TBD |

### 7.2 Resource Utilization

**⚠️ PLACEHOLDER**: Resource metrics will be measured after deployment.

| Resource | Usage | Limit | Status |
|----------|-------|-------|--------|
| GPU Memory | TBD GB | 8 GB | TBD |
| CPU Cores | TBD% | 4 cores | TBD |
| RAM | TBD GB | 8 GB | TBD |
| Disk I/O | TBD MB/s | 500 MB/s | TBD |

---

## 8. Recommendations

### 8.1 Model Deployment

**✅ Recommendations for Production Deployment**:
1. **Human Review**: Always review automated de-identification (especially for external sharing)
2. **Confidence Thresholds**: Flag low-confidence detections (<0.8) for manual review
3. **Audit Logging**: Log all de-identification operations (HIPAA compliance)
4. **Version Control**: Tag model version in de-identified documents (for reproducibility)

### 8.2 Model Improvements

**🔧 Future Improvements** (if metrics not met):
1. **Data Augmentation**: Add synthetic PHI examples (names, addresses, phone numbers)
2. **Ensemble Models**: Combine multiple models (MedCAT + regex + rule-based)
3. **Active Learning**: Collect production errors and retrain
4. **UK-Specific Training**: Fine-tune on UK clinical notes (current model trained on US data)

### 8.3 Monitoring & Maintenance

**📊 Production Monitoring**:
1. **Monthly Audit**: Sample 100 de-identified notes, manually verify PHI removal
2. **Error Logging**: Log all false negatives discovered in production
3. **Model Drift**: Track F1 score over time (retrain if drops below 0.90)
4. **Quarterly Retraining**: Retrain on new clinical notes every 3 months

---

## 9. Next Steps

### 9.1 Immediate Actions

**⚠️ BLOCKERS TO RESOLVE**:
1. **Obtain i2b2 2014 Dataset**:
   - Create PhysioNet account
   - Complete CITI training (research ethics)
   - Sign Data Use Agreement
   - Download dataset
   - **Estimated Time**: 2-3 weeks

2. **Setup Training Infrastructure**:
   - Provision GPU server (8-16GB VRAM)
   - Install PyTorch + MedCAT dependencies
   - Configure training scripts
   - **Estimated Time**: 1-2 days

3. **Data Preprocessing**:
   - Parse i2b2 XML annotations
   - Convert to MedCAT format
   - Validate annotation quality
   - **Estimated Time**: 2-3 days

### 9.2 Training Timeline

**Estimated Timeline** (assuming no blockers):

| Week | Phase | Tasks | Hours |
|------|-------|-------|-------|
| 1 | Data Acquisition | PhysioNet access, download dataset | 20h |
| 1 | Preprocessing | Parse annotations, convert to MedCAT format | 20h |
| 2 | Initial Training | Phase 1 fine-tuning (epochs 1-5) | 30h |
| 2-3 | Full Training | Phase 2 fine-tuning (epochs 6-20) | 40h |
| 3 | Validation | Test set evaluation, error analysis | 20h |
| 3 | Deployment | Model deployment, integration testing | 10h |
| **Total** | **3 weeks** | **All phases** | **120h** |

### 9.3 Success Criteria

**Model is READY for production when**:
- ✅ Overall F1 score >0.92 on test set
- ✅ All per-category F1 scores >0.85
- ✅ Inference speed <2 min per 10-page note
- ✅ Manual review of 100 test notes confirms <10% false negatives
- ✅ Model deployed to CogStack-ModelServe and passing health checks

---

## 10. Appendix

### 10.1 Dataset References
- i2b2 2014 De-identification Challenge: https://portal.dbmi.hms.harvard.edu/projects/n2c2-nlp/
- PhysioNet: https://physionet.org/
- CITI Training: https://about.citiprogram.org/

### 10.2 Model References
- MedCAT: https://github.com/CogStack/MedCAT
- MedCAT Paper: https://arxiv.org/abs/2010.01165
- CogStack-ModelServe: https://github.com/CogStack/CogStack-ModelServe

### 10.3 HIPAA References
- HIPAA Safe Harbor: https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html
- 18 HIPAA Identifiers: https://cphs.berkeley.edu/hipaa/hipaa18.html

### 10.4 Training Logs

**⚠️ PLACEHOLDER**: Training logs will be attached after training.

**Expected Logs**:
- `training_log.txt`: Full training output (loss, metrics per epoch)
- `tensorboard_logs/`: TensorBoard visualization files
- `checkpoints/`: Model checkpoints (best model, final model)

---

## Changelog

### v1.0.0 (TBD - Template)
- **Status**: Training not started (awaiting dataset and infrastructure)
- **Created**: 2025-11-21
- **Purpose**: Template for training report (to be populated after model training)

---

**⚠️ IMPORTANT**: This report is a TEMPLATE. Actual training results will be documented here after model training is complete (estimated: 3 weeks from dataset acquisition).

**See**: `.claude/ccpm/epics/de-identification-module/001.md` for task details.
