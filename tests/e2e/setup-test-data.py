#!/usr/bin/env python3
"""
Setup script for E2E test data in MedCAT Trainer.
Creates test users, sample datasets, and projects.

Usage:
    docker-compose exec medcattrainer python /path/to/setup-test-data.py
    OR
    python manage.py shell < setup-test-data.py
"""

import os
import sys
import json
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Dataset, Document

# Test data configuration
TEST_USERS = [
    {
        'username': 'e2e_test_user',
        'password': 'TestPassword123!',
        'email': 'test@example.com',
        'is_staff': False,
        'is_superuser': False,
    },
    {
        'username': 'e2e_admin_user',
        'password': 'AdminPassword123!',
        'email': 'admin_test@example.com',
        'is_staff': True,
        'is_superuser': True,
    }
]

CLINICAL_DOCUMENTS = [
    {
        'name': 'discharge_summary_001',
        'text': """DISCHARGE SUMMARY

Patient: John Smith
MRN: 123456
Date of Admission: 2024-01-15
Date of Discharge: 2024-01-20

CHIEF COMPLAINT: Chest pain and shortness of breath

HISTORY OF PRESENT ILLNESS:
The patient is a 65-year-old male with a history of hypertension, type 2 diabetes mellitus, and hyperlipidemia who presented to the emergency department with substernal chest pain radiating to the left arm. The pain started approximately 3 hours prior to arrival and was associated with diaphoresis and nausea.

PAST MEDICAL HISTORY:
1. Hypertension - diagnosed 10 years ago
2. Type 2 Diabetes Mellitus - on metformin 1000mg BID
3. Hyperlipidemia - on atorvastatin 40mg daily
4. Obesity - BMI 32
5. Former smoker - quit 5 years ago

MEDICATIONS ON ADMISSION:
- Metformin 1000mg twice daily
- Atorvastatin 40mg daily
- Lisinopril 20mg daily
- Aspirin 81mg daily

PHYSICAL EXAMINATION:
Vitals: BP 158/92, HR 88, RR 18, Temp 98.6F, SpO2 96% on room air
General: Alert, oriented, in mild distress
Cardiac: Regular rate and rhythm, no murmurs
Lungs: Clear to auscultation bilaterally

LABORATORY RESULTS:
- Troponin I: 2.4 ng/mL (elevated)
- BNP: 450 pg/mL (elevated)
- HbA1c: 7.8%
- Creatinine: 1.2 mg/dL
- LDL: 142 mg/dL

DIAGNOSIS:
1. Non-ST elevation myocardial infarction (NSTEMI)
2. Uncontrolled type 2 diabetes mellitus
3. Hypertensive urgency

HOSPITAL COURSE:
Patient underwent cardiac catheterization which revealed 85% stenosis of the LAD. Successful PCI with drug-eluting stent placement was performed. Post-procedure course was uncomplicated.

DISCHARGE MEDICATIONS:
- Aspirin 81mg daily
- Clopidogrel 75mg daily
- Metoprolol succinate 50mg daily
- Atorvastatin 80mg daily
- Lisinopril 40mg daily
- Metformin 1000mg twice daily

FOLLOW-UP:
- Cardiology in 2 weeks
- Primary care in 1 week
- Cardiac rehabilitation referral"""
    },
    {
        'name': 'clinical_note_002',
        'text': """CLINIC NOTE

Date: 2024-02-10
Provider: Dr. Sarah Johnson

SUBJECTIVE:
Patient is a 45-year-old female presenting for follow-up of rheumatoid arthritis. She reports increased joint pain and stiffness in bilateral hands and wrists over the past 2 weeks. Morning stiffness lasting approximately 2 hours. She denies fever, rash, or eye symptoms. Current medications include methotrexate 15mg weekly and folic acid 1mg daily.

OBJECTIVE:
Vitals: BP 122/78, HR 72, Temp 98.2F
MSK: Bilateral MCP and PIP joint swelling noted. Warmth present over wrists bilaterally. Grip strength reduced.
Labs (from last week): ESR 42, CRP 2.8, RF positive, Anti-CCP positive

ASSESSMENT:
1. Rheumatoid arthritis - disease flare
2. Possible methotrexate inadequate response

PLAN:
1. Increase methotrexate to 20mg weekly
2. Add prednisone 10mg daily taper over 2 weeks
3. Consider adding adalimumab if no improvement
4. Repeat labs in 6 weeks
5. Return in 8 weeks for reassessment"""
    },
    {
        'name': 'radiology_report_003',
        'text': """RADIOLOGY REPORT

Exam: CT Chest with Contrast
Date: 2024-03-05
Indication: Persistent cough, weight loss, smoking history

FINDINGS:
Lungs: A 2.3 cm spiculated nodule is identified in the right upper lobe concerning for primary lung malignancy. Additional 4mm nodule in the left lower lobe, likely benign. No pleural effusion.

Mediastinum: Enlarged right hilar lymph node measuring 1.8 cm. No mediastinal lymphadenopathy.

Heart: Normal cardiac silhouette. No pericardial effusion.

Upper Abdomen: Liver, spleen, and adrenal glands appear normal. No focal lesions identified.

Bones: No aggressive osseous lesions.

IMPRESSION:
1. Right upper lobe spiculated nodule highly suspicious for primary bronchogenic carcinoma. Recommend PET-CT for staging and tissue sampling.
2. Right hilar lymphadenopathy - concern for nodal metastasis.
3. Small left lower lobe nodule - recommend follow-up imaging in 3 months.

Recommendation: Urgent pulmonology and oncology consultation."""
    },
    {
        'name': 'emergency_note_004',
        'text': """EMERGENCY DEPARTMENT NOTE

Chief Complaint: Severe headache and confusion

History of Present Illness:
72-year-old male brought in by EMS with sudden onset severe headache described as "the worst headache of my life". Wife reports patient became confused and had difficulty speaking approximately 1 hour ago. Patient has history of atrial fibrillation on warfarin.

Past Medical History:
- Atrial fibrillation
- Hypertension
- Previous TIA 2 years ago

Vital Signs:
BP: 185/110, HR: 88 irregular, RR: 20, SpO2: 97%

Neurological Exam:
- GCS: 13 (E3V4M6)
- Pupils: Equal and reactive
- Right-sided facial droop noted
- Right arm weakness 3/5
- Aphasia - expressive type

Labs:
- INR: 3.8 (supratherapeutic)
- PT: 42 seconds
- Platelet: 165,000

Imaging:
CT Head without contrast: Large left basal ganglia hemorrhage with surrounding edema. Midline shift of 8mm. Intraventricular extension present.

DIAGNOSIS:
1. Intracerebral hemorrhage - warfarin-associated
2. Malignant hypertension

TREATMENT:
1. Vitamin K 10mg IV
2. 4-factor PCC administered
3. Nicardipine drip for BP control
4. Neurosurgery consultation
5. ICU admission"""
    },
    {
        'name': 'pathology_report_005',
        'text': """PATHOLOGY REPORT

Specimen: Breast, right, lumpectomy
Clinical History: 58-year-old female with mammographically detected right breast mass

GROSS DESCRIPTION:
Received fresh labeled "right breast lumpectomy" is an irregularly shaped fibrofatty tissue specimen measuring 5.2 x 4.1 x 3.0 cm. Serial sectioning reveals a firm, gray-white, stellate mass measuring 1.8 x 1.5 x 1.4 cm.

MICROSCOPIC DESCRIPTION:
Sections show invasive ductal carcinoma, moderately differentiated. The tumor cells form glands and nests with moderate nuclear pleomorphism. Mitotic figures are present (8 per 10 HPF).

TUMOR CHARACTERISTICS:
- Histologic Type: Invasive ductal carcinoma, NOS
- Histologic Grade: 2 (Nottingham score 6/9)
- Tumor Size: 1.8 cm
- Margins: Negative, closest margin 3mm (superior)
- Lymphovascular Invasion: Present
- DCIS Component: Present, cribriform type, intermediate grade

IMMUNOHISTOCHEMISTRY:
- ER: Positive (95% cells, strong intensity)
- PR: Positive (80% cells, moderate intensity)
- HER2: Negative (1+)
- Ki-67: 25%

STAGING:
pT1c pNx (sentinel lymph node pending)

DIAGNOSIS:
Right breast lumpectomy:
- Invasive ductal carcinoma, Grade 2, ER/PR positive, HER2 negative
- Margins negative"""
    }
]


def create_test_users():
    """Create test users for E2E testing."""
    print("Creating test users...")
    created = []

    for user_data in TEST_USERS:
        username = user_data['username']

        if User.objects.filter(username=username).exists():
            print(f"  User '{username}' already exists, skipping...")
            continue

        user = User.objects.create_user(
            username=username,
            email=user_data['email'],
            password=user_data['password']
        )
        user.is_staff = user_data['is_staff']
        user.is_superuser = user_data['is_superuser']
        user.save()

        created.append(username)
        print(f"  Created user: {username}")

    return created


def create_test_dataset():
    """Create a test dataset with clinical documents."""
    print("\nCreating test dataset...")

    dataset_name = "E2E Test Dataset"

    if Dataset.objects.filter(name=dataset_name).exists():
        print(f"  Dataset '{dataset_name}' already exists")
        dataset = Dataset.objects.get(name=dataset_name)
    else:
        # Create a simple CSV file for the dataset
        import tempfile
        import csv

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'text'])
            writer.writeheader()
            for doc in CLINICAL_DOCUMENTS:
                writer.writerow(doc)
            csv_path = f.name

        from django.core.files import File

        with open(csv_path, 'rb') as f:
            dataset = Dataset.objects.create(
                name=dataset_name,
                description="Test dataset for E2E testing with clinical documents"
            )
            dataset.original_file.save('e2e_test_data.csv', File(f))

        print(f"  Created dataset: {dataset_name}")

        # Clean up temp file
        os.unlink(csv_path)

    return dataset


def create_test_documents(dataset):
    """Create test documents in the dataset."""
    print("\nCreating test documents...")
    created = []

    for doc_data in CLINICAL_DOCUMENTS:
        doc_name = doc_data['name']

        if Document.objects.filter(name=doc_name, dataset=dataset).exists():
            print(f"  Document '{doc_name}' already exists, skipping...")
            continue

        doc = Document.objects.create(
            name=doc_name,
            text=doc_data['text'],
            dataset=dataset
        )
        created.append(doc_name)
        print(f"  Created document: {doc_name}")

    return created


def main():
    """Main setup function."""
    print("=" * 60)
    print("MedCAT Trainer E2E Test Data Setup")
    print("=" * 60)

    # Create users
    users = create_test_users()

    # Create dataset and documents
    try:
        dataset = create_test_dataset()
        documents = create_test_documents(dataset)
    except Exception as e:
        print(f"\nWarning: Could not create dataset/documents: {e}")
        print("This is expected if running outside Django context")
        dataset = None
        documents = []

    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print(f"\nUsers created: {len(users)}")
    if dataset:
        print(f"Dataset created: {dataset.name}")
        print(f"Documents created: {len(documents)}")

    print("\nTest credentials:")
    for user in TEST_USERS:
        print(f"  - {user['username']} / {user['password']}")


if __name__ == '__main__':
    main()
