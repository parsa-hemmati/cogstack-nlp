# RTF to CSV Converter for MedCAT Trainer

## Overview

MedCAT Trainer natively supports **CSV and XLSX** uploads only. This script converts a directory of **RTF clinical documents** into a CSV file suitable for upload.

## Requirements

```bash
pip install -r requirements-rtf.txt
```

## Usage

### Step 1: Organize RTF Files

Place all clinical RTF files in a directory:

```
/mnt/clinical_notes/
├── Patient-001.rtf
├── Patient-002.rtf
├── Patient-003.rtf
└── ...
```

### Step 2: Convert to CSV

```bash
python rtf_to_csv_converter.py /mnt/clinical_notes clinical_notes.csv
```

**Output**:
```
Found 150 RTF files
Processing: Patient-001.rtf
Processing: Patient-002.rtf
Processing: Patient-003.rtf
...
✅ Conversion complete: clinical_notes.csv
   150 documents converted
```

### Step 3: Upload to MedCAT Trainer

1. Login to MedCAT Trainer Admin: `http://localhost:8000/admin/`
2. Navigate to **Datasets** → **Add Dataset**
3. Upload `clinical_notes.csv`
4. Save

The CSV will have this format:

```csv
name,text
Patient-001,"Patient presents with chest pain. History of hypertension. ECG shows ST elevation."
Patient-002,"Admitted with acute diabetes. HbA1c 9.2%. Started on insulin."
Patient-003,"Suspected atrial flutter. Irregular rhythm noted. Referred to cardiology."
```

## RTF File Naming

**Document names** are derived from filenames (without `.rtf` extension):

- `Patient-001.rtf` → Document name: `Patient-001`
- `NHS-12345678.rtf` → Document name: `NHS-12345678`
- `Clinical_Note_2025-01-15.rtf` → Document name: `Clinical_Note_2025-01-15`

## Troubleshooting

### Issue: "No RTF files found"

**Cause**: Files have different extensions or are in subdirectories.

**Fix**: Ensure files have `.rtf` or `.RTF` extension and are in the top-level directory (not nested).

### Issue: "Error processing XYZ.rtf"

**Cause**: Corrupted or malformed RTF file.

**Fix**:
1. Try opening the file in WordPad to verify it's valid RTF
2. Check the error message for details
3. The script will skip corrupted files and continue processing others

### Issue: Text looks garbled

**Cause**: RTF encoding issues.

**Fix**: The script uses UTF-8 with error handling. If specific files have issues, manually convert them using:

```bash
# On Windows
Get-Content Patient-001.rtf | Out-File -Encoding UTF8 Patient-001-fixed.rtf

# On Linux/Mac
iconv -f WINDOWS-1252 -t UTF-8 Patient-001.rtf > Patient-001-fixed.rtf
```

## Alternative: Option B (Future Enhancement)

If you need **native RTF support** in MedCAT Trainer (upload RTF directly without preprocessing), this requires development:

**Follow Spec-Kit Workflow**:
1. Create specification: `.specify/specifications/rtf-dataset-upload.md`
2. Create technical plan
3. Create task breakdown
4. Implement feature
5. Test and deploy

**Estimated effort**: 8-12 hours (backend: RTF parsing, frontend: file validation, testing)

See `CLAUDE.md` for workflow details.
