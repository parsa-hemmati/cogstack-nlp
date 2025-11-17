# Large-Scale Multi-Clinician Deployment Guide

## Overview

This guide covers deploying MedCAT Trainer for **large-scale document validation** (5,000-10,000+ documents) with **multiple clinicians** working asynchronously with **poor communication**.

**Scenario**: NHS hospital with 10,000 RTF clinical documents, 5+ clinicians, different work schedules, need quality validation with overlap.

**Solution**: Overlapping batches with automatic boundaries and quality-check zones.

---

## Strategy: Overlapping Batches

### Why Overlapping Batches?

**Problem with single shared dataset** (10,000 docs):
- ❌ All clinicians start from document 1 (poor communication)
- ❌ Massive duplication at the beginning, gaps at the end
- ❌ Hard to track who's working on what
- ❌ No automatic load balancing

**Solution: Overlapping batches**:
- ✅ Each clinician has clear boundaries (docs 1-2500, 2001-4500, etc.)
- ✅ No coordination needed (automatic assignment)
- ✅ Overlap zones provide quality validation (2 clinicians per overlap zone)
- ✅ Flexibility (2,500 docs per clinician, work on any within batch)
- ✅ Easy progress tracking (5 separate completion rates)

### Batch Design Example (10,000 documents, 5 clinicians)

```
Batch A (Dr. Smith):   Documents 1-2500     (2,500 docs)
Batch B (Dr. Jones):   Documents 2001-4500  (2,500 docs, 500 overlap with A)
Batch C (Dr. Brown):   Documents 4001-6500  (2,500 docs, 500 overlap with B)
Batch D (Dr. White):   Documents 6001-8500  (2,500 docs, 500 overlap with C)
Batch E (Dr. Green):   Documents 8001-10000 (2,000 docs, 500 overlap with D)
```

**Overlap zones** (quality validation):
- Docs 2001-2500: Validated by Dr. Smith AND Dr. Jones (500 docs)
- Docs 4001-4500: Validated by Dr. Jones AND Dr. Brown (500 docs)
- Docs 6001-6500: Validated by Dr. Brown AND Dr. White (500 docs)
- Docs 8001-8500: Validated by Dr. White AND Dr. Green (500 docs)

**Total**: 2,000 documents validated twice (20% quality check rate)

---

## Step-by-Step Implementation

### Phase 1: Prepare RTF Files

**Step 1.1: Organize RTF Files**

Place all 10,000 RTF files in a single directory with **alphabetically sortable names**:

```
C:\Clinical_Notes\
├── Patient-0001.rtf
├── Patient-0002.rtf
├── Patient-0003.rtf
├── ...
└── Patient-10000.rtf
```

**Important**: Use zero-padded numbers (0001, 0002, not 1, 2) for correct alphabetical sorting.

If your files aren't named this way, rename them:
```powershell
# PowerShell script to rename files
$files = Get-ChildItem C:\Clinical_Notes\*.rtf | Sort-Object Name
$counter = 1
foreach ($file in $files) {
    $newName = "Patient-{0:D5}.rtf" -f $counter
    Rename-Item $file.FullName -NewName $newName
    $counter++
}
```

**Step 1.2: Install Dependencies**

```powershell
cd C:\MedCAT-Trainer\scripts
pip install -r requirements-rtf.txt
```

**Step 1.3: Split into Overlapping Batches**

```powershell
python split_rtf_batches.py `
  C:\Clinical_Notes `
  C:\MedCAT-Data\batches `
  --num-batches 5 `
  --overlap 500 `
  --batch-prefix nhs_cardiology

# Output:
# Found 10000 RTF files
# Creating 5 batches with 500 overlapping documents
#
# Batch Allocation:
# ------------------------------------------------------------
# Batch A: Documents     1 -  2500 (2500 docs)
# Batch B: Documents  2001 -  4500 (2500 docs) (overlap: 500 docs with Batch A)
# Batch C: Documents  4001 -  6500 (2500 docs) (overlap: 500 docs with Batch B)
# Batch D: Documents  6001 -  8500 (2500 docs) (overlap: 500 docs with Batch C)
# Batch E: Documents  8001 - 10000 (2000 docs) (overlap: 500 docs with Batch D)
# ------------------------------------------------------------
# Total unique documents: 10000
# Total overlap documents: 2000
# Total validations: 12000 (20.0% overlap rate)
#
# Creating batch_A.csv (2500 documents)...
# ✅ Created: C:\MedCAT-Data\batches\nhs_cardiology_A.csv
# ...
```

**Output files**:
```
C:\MedCAT-Data\batches\
├── nhs_cardiology_A.csv  (2,500 documents)
├── nhs_cardiology_B.csv  (2,500 documents)
├── nhs_cardiology_C.csv  (2,500 documents)
├── nhs_cardiology_D.csv  (2,500 documents)
└── nhs_cardiology_E.csv  (2,000 documents)
```

---

### Phase 2: Upload Batches to MedCAT Trainer

**Step 2.1: Start MedCAT Trainer**

```powershell
cd C:\MedCAT-Trainer
docker-compose up -d

# Verify running
docker-compose ps
```

**Step 2.2: Login as Admin**

Navigate to: `http://localhost:8000/admin/`
- Username: `admin`
- Password: `{your password}`

**Step 2.3: Upload 5 Datasets**

For **each CSV file** (A, B, C, D, E):

1. Navigate to: **Datasets** → **Add Dataset**
2. Fill in:
   - **Name**: `NHS Cardiology Batch A` (or B, C, D, E)
   - **Description**: `Documents 1-2500, assigned to Dr. Smith`
   - **Original File**: Upload `nhs_cardiology_A.csv`
3. Click **Save**
4. Verify: Dataset shows "2500 documents" (or 2000 for Batch E)

**Repeat 5 times** (one for each batch).

**Result**:
```
Datasets:
├── NHS Cardiology Batch A (2,500 documents)
├── NHS Cardiology Batch B (2,500 documents)
├── NHS Cardiology Batch C (2,500 documents)
├── NHS Cardiology Batch D (2,500 documents)
└── NHS Cardiology Batch E (2,000 documents)
```

---

### Phase 3: Create User Accounts

**Step 3.1: Create Clinician Users**

Navigate to: **Users** → **Add User**

Create 5 users:
```
User 1:
  Username: dr_smith
  Email: dr.smith@nhs.uk
  Staff status: ✓
  Superuser: ✗

User 2:
  Username: dr_jones
  Email: dr.jones@nhs.uk
  Staff status: ✓
  Superuser: ✗

User 3:
  Username: dr_brown
  Email: dr.brown@nhs.uk
  Staff status: ✓
  Superuser: ✗

User 4:
  Username: dr_white
  Email: dr.white@nhs.uk
  Staff status: ✓
  Superuser: ✗

User 5:
  Username: dr_green
  Email: dr.green@nhs.uk
  Staff status: ✓
  Superuser: ✗
```

**Set passwords**: Click on each user → Set password → Enter temporary password → Save

**Send credentials** to each clinician securely (NHS email, password manager, etc.)

---

### Phase 4: Create Annotation Projects

**Step 4.1: Upload MedCAT Model**

Navigate to: **Model Packs** → **Add Model Pack**
- **Name**: `NHS SNOMED-CT Cardiology v1`
- **Model Pack**: Upload your `.zip` MedCAT model
- Save

**Step 4.2: Create Project for Each Clinician**

Navigate to: **Project Annotate Entities** → **Add Project Annotate Entities**

**Project 1 (Dr. Smith)**:
- **Name**: `NHS Cardiology Validation - Batch A (Dr. Smith)`
- **Description**: `Validate documents 1-2500 for atrial flutter cohort identification`
- **Members**: Select `dr_smith` only
- **Dataset**: Select `NHS Cardiology Batch A`
- **Model Pack**: Select `NHS SNOMED-CT Cardiology v1`
- **Require Entity Validation**: ✓ Checked
- **Train Model On Submit**: ✓ Checked (active learning)
- **Tasks**: Select meta-annotations if needed (Negation, Temporality, Experiencer)
- Save

**Repeat for Projects 2-5**:
```
Project 2: Batch B → dr_jones
Project 3: Batch C → dr_brown
Project 4: Batch D → dr_white
Project 5: Batch E → dr_green
```

**Result**:
```
Projects:
├── NHS Cardiology Validation - Batch A (Dr. Smith)
│   └── Dataset: Batch A (docs 1-2500)
│
├── NHS Cardiology Validation - Batch B (Dr. Jones)
│   └── Dataset: Batch B (docs 2001-4500)
│
├── NHS Cardiology Validation - Batch C (Dr. Brown)
│   └── Dataset: Batch C (docs 4001-6500)
│
├── NHS Cardiology Validation - Batch D (Dr. White)
│   └── Dataset: Batch D (docs 6001-8500)
│
└── NHS Cardiology Validation - Batch E (Dr. Green)
    └── Dataset: Batch E (docs 8001-10000)
```

---

### Phase 5: Clinician Workflow

**Step 5.1: Clinician RDPs to Workstation**

From clinician laptop:
```
Computer: NHS-WORKSTATION-01
Username: NHS\dr_smith (Windows credentials)
Password: {Windows password}
```

**Step 5.2: Access MedCAT Trainer**

Inside RDP session:
- Open browser → `http://localhost:8000` (or `https://medcat.nhs.uk` if HTTPS configured)
- Login with **MedCAT Trainer credentials**:
  - Username: `dr_smith`
  - Password: `{MedCAT password, not Windows password}`

**Step 5.3: Select Project**

Homepage shows:
```
Your Projects:
✓ NHS Cardiology Validation - Batch A (Dr. Smith)
  Dataset: NHS Cardiology Batch A
  Status: 0/2500 documents validated
```

Click on project.

**Step 5.4: Validate Documents**

- Document list (left sidebar): Shows docs 1-2500
- Current document: Patient-0001
- Annotate entities (grey → blue/red/turquoise)
- Submit document
- Next document auto-loads: Patient-0002
- Repeat for 2,500 documents

**Flexibility**: Dr. Smith can validate documents in any order (1→2→3 or 2500→2499→2498)

---

### Phase 6: Progress Monitoring

**Step 6.1: Admin Dashboard**

Navigate to: `http://localhost:8000/admin/api/projectannotateentities/`

**View progress**:
```
NHS Cardiology Validation - Batch A (Dr. Smith)
  Validated: 1,250/2,500 (50%)
  Last Modified: 2025-11-16 14:32

NHS Cardiology Validation - Batch B (Dr. Jones)
  Validated: 800/2,500 (32%)
  Last Modified: 2025-11-16 14:25

NHS Cardiology Validation - Batch C (Dr. Brown)
  Validated: 2,100/2,500 (84%)
  Last Modified: 2025-11-16 14:40

NHS Cardiology Validation - Batch D (Dr. White)
  Validated: 500/2,500 (20%)
  Last Modified: 2025-11-16 14:18

NHS Cardiology Validation - Batch E (Dr. Green)
  Validated: 1,900/2,000 (95%)
  Last Modified: 2025-11-16 14:50
```

**Calculate unique docs validated**:
```
Total unique docs covered:
- Batch A: 1,250 (docs 1-1250)
- Batch B: 800 (docs 2001-2800, overlap zone NOT included yet)
- Batch C: 2,100 (docs 4001-6100, includes overlap zone)
- Batch D: 500 (docs 6001-6500, all in overlap zone with C)
- Batch E: 1,900 (docs 8001-9900)

Unique docs validated: ~6,550/10,000 (65%)
```

**Step 6.2: Identify Bottlenecks**

In above example:
- ⚠️ **Dr. White is slow** (20% complete)
- ✅ **Dr. Green nearly done** (95% complete)

**Action**: Ask Dr. Green to help Dr. White (if possible)

**How**:
1. Admin adds `dr_green` to Project D members
2. Dr. Green can now access Batch D documents
3. Dr. Green picks up from where Dr. White left off

---

### Phase 7: Quality Analysis (Overlap Zones)

**Step 7.1: Export Annotations**

After all projects complete:

Navigate to: **Project Annotate Entities**
- Select all 5 projects
- **Actions** → **Download**
- Exports JSON with all annotations

**Step 7.2: Analyze Overlap Agreement**

Overlap zones (validated by 2 clinicians):
- Docs 2001-2500: Dr. Smith + Dr. Jones
- Docs 4001-4500: Dr. Jones + Dr. Brown
- Docs 6001-6500: Dr. Brown + Dr. White
- Docs 8001-8500: Dr. White + Dr. Green

**Inter-Rater Reliability** (IRR) calculation:

```python
# Example: Calculate Cohen's Kappa for overlap zone
overlap_docs = range(2001, 2501)  # 500 docs

smith_annotations = load_annotations("batch_A.json", overlap_docs)
jones_annotations = load_annotations("batch_B.json", overlap_docs)

kappa = cohen_kappa(smith_annotations, jones_annotations)
# kappa > 0.8 → Excellent agreement
# kappa 0.6-0.8 → Good agreement
# kappa < 0.6 → Poor agreement (need adjudication)
```

**If agreement is low** (<0.6):
- Schedule review meeting with Dr. Smith + Dr. Jones
- Discuss disagreements
- Clarify annotation guidelines
- Re-annotate if needed

---

## Customization Options

### Option 1: Increase Overlap (More Quality Validation)

**Default**: 500 docs overlap (20% validation rate)

**Increase to 1,000 docs** (40% validation rate):
```powershell
python split_rtf_batches.py `
  C:\Clinical_Notes `
  C:\MedCAT-Data\batches `
  --num-batches 5 `
  --overlap 1000  # ← Increased from 500
```

**Result**: 4,000 documents validated twice (40% quality check)

**Trade-off**: More validation work (14,000 total validations vs 12,000)

---

### Option 2: Decrease Batch Size (More Clinicians)

**Default**: 5 batches, ~2,500 docs each

**Increase to 10 clinicians** (1,250 docs each):
```powershell
python split_rtf_batches.py `
  C:\Clinical_Notes `
  C:\MedCAT-Data\batches `
  --num-batches 10  # ← Increased from 5
  --overlap 250     # ← Decreased to maintain ~20% overlap
```

**Result**: 10 batches of ~1,250 documents each, 250-doc overlap zones

**Benefit**: Faster completion (more parallel work)

---

### Option 3: No Overlap (Maximum Efficiency)

**If you don't need quality validation**:
```powershell
python split_rtf_batches.py `
  C:\Clinical_Notes `
  C:\MedCAT-Data\batches `
  --num-batches 5 `
  --overlap 0  # ← No overlap
```

**Result**: Each clinician validates exactly 2,000 unique documents, no duplicates

**Trade-off**: No inter-rater reliability check

---

## Troubleshooting

### Issue 1: Batch Sizes Uneven

**Problem**: Batch E has fewer documents (2,000 vs 2,500)

**Why**: 10,000 doesn't divide evenly by 5 with 500 overlap

**Solutions**:

**Option A**: Manually adjust last batch
- Give Dr. Green fewer documents (they finish early, can help others)

**Option B**: Use 6 batches instead of 5
- 10,000 docs ÷ 6 batches = ~1,667 docs per batch (more even)

---

### Issue 2: Clinician Finishes Early

**Scenario**: Dr. Green finishes Batch E (2,000 docs), others still working

**Solution**: Add Dr. Green to another project

1. Admin navigates to Project D (Dr. White's batch)
2. Edit project → **Members** → Add `dr_green`
3. Save
4. Dr. Green now sees both Project E and Project D
5. Dr. Green can help Dr. White complete Batch D

**Flexibility benefit**: No need to re-assign documents or create new projects

---

### Issue 3: Clinician Too Slow

**Scenario**: Dr. White only completed 20% after 2 weeks

**Solutions**:

**Option A**: Redistribute remaining work
- Dr. Green helps (see Issue 2)
- Split remaining docs between other clinicians

**Option B**: Reduce batch size
- Remove 1,000 docs from Dr. White's batch
- Create new mini-batch for another clinician

**Option C**: Replace clinician
- Create new user `dr_purple`
- Add to Project D
- Dr. Purple continues from where Dr. White left off

---

### Issue 4: Too Much Duplicate Work in Overlap

**Problem**: Overlap zones creating too much extra work

**Solution**: Reduce overlap
```powershell
# Re-run with 250-doc overlap instead of 500
python split_rtf_batches.py ... --overlap 250
```

**Trade-off**: Less quality validation (10% vs 20%)

---

## Performance Considerations

### Dataset Size Limits

**PostgreSQL**:
- ✅ 10,000 documents: No problem
- ✅ 50,000 documents: Works fine
- ⚠️ 100,000+ documents: May need database tuning

**CSV Upload**:
- ✅ 2,500 docs × 50KB each = ~125MB CSV (uploads fine)
- ⚠️ 10,000 docs in single CSV = ~500MB (may timeout, split into batches)

**Recommendation**: Keep batches under 5,000 documents each

---

### Disk Space

**Estimate for 10,000 documents**:
```
RTF files:         10,000 × 50KB  = 500 MB
CSV files:         10,000 × 50KB  = 500 MB
PostgreSQL:        10,000 docs    = 1 GB (with annotations)
MedCAT models:                    = 2 GB
Total:                            = 4 GB
```

**Recommendation**: 20GB free disk space for safety

---

### Network Bandwidth (RDP)

**RDP bandwidth per clinician**:
- Idle: ~50 Kbps
- Active annotation: ~200 Kbps
- Document loading: ~500 Kbps peak

**5 simultaneous clinicians**:
- Total: ~1 Mbps average, ~2.5 Mbps peak

**Recommendation**: 5 Mbps+ internet connection for smooth RDP experience

---

## Summary

**For 10,000 documents + 5 clinicians + poor communication + need flexibility**:

✅ **Use overlapping batches** (this guide)
- ✅ No coordination needed (automatic boundaries)
- ✅ Quality validation (20% overlap = 2,000 docs validated twice)
- ✅ Flexibility (clinicians can help each other)
- ✅ Easy progress tracking (5 separate completion rates)
- ✅ No custom development needed (works today)

**Estimated timeline**:
- Batch preparation: 2 hours (RTF conversion + CSV upload)
- User setup: 1 hour (create 5 accounts, 5 projects)
- Validation work: ~200 hours total (2,500 docs × 5 clinicians × 15 min/doc average)
- Admin monitoring: 30 min/day (check progress, redistribute if needed)

**Total**: ~6 weeks with 5 clinicians working 8 hours/day

---

## Next Steps

1. **Organize RTF files** (rename with zero-padded numbers)
2. **Run batch splitter** (creates 5 overlapping CSV files)
3. **Upload to MedCAT Trainer** (5 datasets, 5 projects)
4. **Assign clinicians** (each gets one batch)
5. **Monitor progress** (weekly check, redistribute if needed)
6. **Analyze overlap** (calculate inter-rater reliability)
7. **Export final annotations** (merge all 5 projects)

**Ready to start!**
