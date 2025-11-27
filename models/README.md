# MedCAT Models Directory

This directory contains the MedCAT NLP models used by CogStack-ModelServe.

**Status**: ⚠️ **BLOCKED** - Models must be downloaded before starting CogStack-ModelServe service

See `.claude/autonomous/blockers/blocker-002-medcat-models.md` for detailed instructions.

---

## Required Models

### 1. SNOMED-CT Model (`medcat_snomed.zip`)
- **Purpose**: Clinical concept extraction (diseases, symptoms, procedures, medications)
- **Size**: 2-5 GB
- **Features**:
  - Entity recognition with CUI codes (Concept Unique Identifiers)
  - Meta-annotations (Negation, Temporality, Experiencer, Certainty)
  - Concept linking to SNOMED-CT terminology
- **Required for**: Patient search, timeline view, clinical decision support, cohort identification

### 2. De-identification Model (`medcat_deid.zip`)
- **Purpose**: PHI detection (names, NHS numbers, dates, addresses, phone numbers)
- **Size**: 1-2 GB
- **Features**:
  - Person names (patients, clinicians, family members)
  - NHS numbers
  - Dates of birth
  - Addresses
  - Phone numbers
  - Email addresses
- **Required for**: Document upload, PHI extraction, privacy compliance (HIPAA/GDPR)

---

## Directory Structure

```
models/
├── README.md (this file)
├── medcat_snomed.zip          # SNOMED-CT model (to be downloaded)
├── medcat_deid.zip             # De-identification model (to be downloaded)
├── snomed/ (optional)          # Extracted SNOMED model
│   ├── model.dat
│   └── config.json
└── deid/ (optional)            # Extracted de-identification model
    ├── model.dat
    └── config.json
```

---

## Download Instructions

**⚠️ BLOCKER**: See `.claude/autonomous/blockers/blocker-002-medcat-models.md` for model download information.

Autonomous execution is blocked until models are available. Once downloaded, update the blocker file and autonomous execution will continue.

### Option A: CogStack Model Zoo (Recommended)
1. Check https://github.com/CogStack/CogStack-ModelServe for official model links
2. Download models to this directory
3. Extract if needed (CogStack-ModelServe can load .zip files directly)

### Option B: Custom Models from Organization
1. Obtain models from your NHS trust or partner organization
2. Copy to this directory
3. Ensure naming matches docker-compose.yml configuration:
   - `medcat_snomed.zip` for SNOMED model
   - `medcat_deid.zip` for de-identification model

### Option C: Train Custom Models (Not Recommended for MVP)
Training custom models requires:
- Annotated training data (100,000+ clinical notes)
- Training time: 2-4 weeks
- Clinical SME time for validation
- **Timeline impact**: +4 weeks

**Recommendation**: Use pre-trained models for MVP, consider custom training for production.

---

## Verification

After downloading models, verify integrity:

```bash
# Check file sizes
ls -lh models/

# Expected output:
# medcat_snomed.zip  (≥1 GB)
# medcat_deid.zip    (≥500 MB)

# Check checksums (if provided by model source)
sha256sum models/medcat_snomed.zip
sha256sum models/medcat_deid.zip

# Compare with expected checksums from model provider
```

---

## Docker Volume Mount

This directory is mounted as a **read-only** volume in the `cogstack-modelserve` service:

```yaml
# From docker-compose.yml
cogstack-modelserve:
  volumes:
    - medcat_models:/models:ro  # Read-only mount for security
```

**Why read-only?**
- **Security**: Prevents accidental model corruption
- **Multi-user**: All users share same models (single workstation deployment)
- **Immutability**: Models should not be modified during runtime

---

## CogStack-ModelServe Configuration

CogStack-ModelServe expects models at:
- SNOMED model: `/models/medcat_snomed.zip`
- De-identification model: `/models/medcat_deid.zip`

Environment variables (from docker-compose.yml):
```yaml
environment:
  - MODEL_SNOMED_PATH=/models/medcat_snomed.zip
  - MODEL_DEID_PATH=/models/medcat_deid.zip
```

---

## Model Loading

CogStack-ModelServe loads models on startup:
- **Loading time**: 60-90 seconds for SNOMED model
- **Memory requirement**: ~4 GB RAM (configured in docker-compose.yml)
- **Health check**: Has 90-second start period to accommodate model loading

Monitor logs during startup:
```bash
docker-compose logs -f cogstack-modelserve

# Expected output:
# Loading SNOMED model from /models/medcat_snomed.zip...
# Model loaded successfully in 73.5 seconds
# Loading de-identification model from /models/medcat_deid.zip...
# Model loaded successfully in 12.3 seconds
# Application startup complete
```

---

## Troubleshooting

### Issue: CogStack-ModelServe fails to start with "Model not found" error

**Solution**:
1. Check this directory contains `medcat_snomed.zip` and `medcat_deid.zip`
2. Verify file sizes (SNOMED ≥1GB, DeID ≥500MB)
3. Check docker-compose.yml volume mount: `./models:/models:ro`
4. Verify bind mount device path matches: `device: ./models`
5. Restart service: `docker-compose restart cogstack-modelserve`

### Issue: Models take >90 seconds to load

**Solution**: This is normal for large SNOMED models (2-5 GB). The health check has a 90-second start period to accommodate this. If loading takes longer:
1. Check available RAM (CogStack-ModelServe needs 4GB)
2. Check disk I/O (SSD recommended for fast model loading)
3. Increase start_period in docker-compose.yml if needed

### Issue: Permission denied when accessing models

**Solution**:
1. Check file ownership: `ls -l models/`
2. Ensure files are readable: `chmod 644 models/*.zip`
3. Ensure directory is executable: `chmod 755 models/`

---

## Security Notes

- Models may contain proprietary medical terminology
- **Do not commit models to version control** (too large, potentially proprietary)
- Models directory is in `.gitignore`
- Access restricted to CogStack-ModelServe container only (read-only mount)
- Models shared across all users (single workstation deployment)

---

## Next Steps

Once models are downloaded:

1. **Update blocker status**:
   ```bash
   # Edit .claude/autonomous/blockers/blocker-002-medcat-models.md
   # Change status to: resolved
   ```

2. **Update mission status** in `.claude/autonomous/progress.json`:
   ```json
   {
     "mission_id": "mvp-phase-0-task-2",
     "status": "completed",
     "actual_hours": 8.0,
     "notes": "Models downloaded and verified"
   }
   ```

3. **Verify CogStack-ModelServe startup**:
   ```bash
   docker-compose up -d cogstack-modelserve
   docker-compose logs -f cogstack-modelserve
   # Wait for "Application startup complete"
   ```

4. **Test models**:
   ```bash
   # Test SNOMED model
   curl -X POST http://localhost:8001/api/process \
     -H "Content-Type: application/json" \
     -d '{"text": "Patient has atrial fibrillation and diabetes", "model_name": "medcat_snomed"}'

   # Test de-identification model
   curl -X POST http://localhost:8001/api/process \
     -H "Content-Type: application/json" \
     -d '{"text": "Patient John Smith, NHS number 1234567890, DOB 01/01/1980", "model_name": "medcat_deid"}'
   ```

5. **Autonomous execution will continue** with Mission 0.6 (Setup CogStack-ModelServe)

---

**Blocker Reference**: `.claude/autonomous/blockers/blocker-002-medcat-models.md`
**Task Reference**: `.specify/tasks/clinical-care-tools-base-tasks.md` (Task 0.2)
**Specification**: `.specify/specifications/clinical-care-tools-base-app.md`
