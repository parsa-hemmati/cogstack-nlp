# Blocker 002: MedCAT Models Download Required

**Mission ID**: mvp-phase-0-task-2
**Created**: 2025-11-17T00:00:00Z
**Status**: pending_human_input
**Priority**: P1 (Blocks CogStack-ModelServe setup)

---

## Issue

Autonomous execution requires MedCAT model download URLs and credentials, which are not specified in the specification or available in the codebase.

## Context

- **Spec file**: `.specify/specifications/clinical-care-tools-base-app.md`
- **Task section**: "Phase 0: Environment Setup - Task 0.2"
- **Estimated time**: 8 hours (mostly download time)

**Required Models**:
1. **SNOMED-CT Model** (2-5 GB)
   - Purpose: Clinical concept extraction (diseases, symptoms, procedures)
   - Required for: Patient search, timeline view, clinical decision support

2. **De-identification Model** (1-2 GB)
   - Purpose: PHI detection (names, NHS numbers, dates, addresses)
   - Required for: Document upload, PHI extraction, privacy compliance

## Question for Human

**Where can autonomous execution download the MedCAT models?**

Please provide:
1. **Model download URLs** (direct links or instructions)
2. **Credentials** (if required for model access)
3. **Model names/versions** (for verification)

## Options Considered

### Option A: CogStack Model Zoo (Recommended)

If models are available from CogStack Model Zoo:
- URL: https://github.com/CogStack/CogStack-ModelServe (check documentation)
- Provide download link or instructions

### Option B: Pre-trained Models from Partner

If models are provided by NHS trust or partner organization:
- Provide secure download link
- Provide credentials if needed
- Confirm models include SNOMED-CT and de-identification capabilities

### Option C: Train Custom Models (Not Recommended for MVP)

Training custom models would require:
- Annotated training data (100,000+ clinical notes)
- Training time: 2-4 weeks
- Clinical SME time for validation
- **Impact**: +4 weeks to timeline
- **Recommendation**: Use pre-trained models for MVP

## Action Required

### Step 1: Provide Model Access Information

Update this file with model download information:

```markdown
## Model Download Information (USER TO COMPLETE)

**SNOMED-CT Model**:
- Download URL: _______________
- Credentials (if needed): _______________
- Expected file size: _______________ GB
- Checksum (if available): _______________

**De-identification Model**:
- Download URL: _______________
- Credentials (if needed): _______________
- Expected file size: _______________ GB
- Checksum (if available): _______________
```

### Step 2: Autonomous Execution Will Handle

Once model information is provided, autonomous execution will:

1. **Create Directory Structure**
   ```bash
   medcat_models/
   ├── snomed/
   │   ├── model.dat
   │   └── config.json
   └── deid/
       ├── model.dat
       └── config.json
   ```

2. **Download Models**
   ```bash
   # Autonomous execution will run:
   wget -c <SNOMED_MODEL_URL> -O medcat_models/snomed/model.zip
   wget -c <DEID_MODEL_URL> -O medcat_models/deid/model.zip
   ```

3. **Verify Integrity**
   ```bash
   # Check file sizes
   # Verify checksums (if provided)
   # Extract models
   ```

4. **Update Mission Status**
   ```json
   {
     "mission_id": "mvp-phase-0-task-2",
     "status": "completed",
     "actual_hours": 8.0
   }
   ```

### Step 3: Alternative - Manual Download

If automatic download is not possible, user can manually download:

1. **Download models to local machine**
2. **Copy to project directory**:
   ```bash
   # Create directories
   mkdir -p medcat_models/snomed
   mkdir -p medcat_models/deid

   # Copy models
   cp /path/to/downloaded/snomed_model.zip medcat_models/snomed/
   cp /path/to/downloaded/deid_model.zip medcat_models/deid/

   # Extract
   cd medcat_models/snomed && unzip snomed_model.zip
   cd medcat_models/deid && unzip deid_model.zip
   ```

3. **Update mission status** in `.claude/autonomous/progress.json`

## Acceptance Criteria

- [ ] `medcat_models/snomed/` directory exists with model files
- [ ] `medcat_models/deid/` directory exists with model files
- [ ] Model files extracted successfully
- [ ] Checksum verification passed (if applicable)
- [ ] SNOMED model size >= 1 GB
- [ ] De-identification model size >= 500 MB

## Impact if Not Resolved

**Blocks missions**:
- mvp-phase-0-task-6 (Setup CogStack-ModelServe)
- mvp-phase-3 (Document Management - PHI extraction)
- mvp-phase-4 (Patient Search - concept extraction)
- **All clinical NLP functionality**

**Timeline impact**: +1 week (if models not available, need to source alternatives)

## Recommended Action

**Provide model download URLs** in "Model Download Information" section above. Autonomous execution will handle download, extraction, and verification.

**Alternative**: If models are proprietary/restricted, provide manual download instructions and autonomous execution will verify integrity only.

---

**Dependencies**: Blocker 001 (Docker Installation) must be resolved first
**Next Mission**: mvp-phase-0-task-3 (Docker Compose) can proceed in parallel
