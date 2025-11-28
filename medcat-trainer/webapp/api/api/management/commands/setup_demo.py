"""
Management command to set up demo data for MedCAT Trainer.
Creates default group, project, and mock clinical documents.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import connection
from django.db.models.signals import post_save
from api.models import (
    Dataset, Document, ProjectAnnotateEntities, ModelPack,
    ConceptDB, Vocabulary
)
from api.signals import save_dataset


# Sample clinical letters for demonstration
SAMPLE_CLINICAL_LETTERS = [
    {
        "name": "Cardiology Clinic Letter - Patient A",
        "text": """NHS Number: 123 456 7890
Consultant: Dr. Sarah Johnson
Specialty: Cardiology

Dear Dr. Smith,

Re: Mr. John Davies, DOB: 15/03/1958

Thank you for referring this 65-year-old gentleman who presented with chest pain and shortness of breath on exertion.

History of Presenting Complaint:
The patient reports a 3-month history of central chest discomfort, described as a "tight" sensation, occurring on moderate exertion such as climbing stairs. The pain typically resolves within 5 minutes of rest. He denies any radiation to the arm or jaw. Associated symptoms include mild dyspnoea on exertion.

Past Medical History:
- Type 2 Diabetes Mellitus (diagnosed 2015)
- Hypertension (on treatment)
- Hypercholesterolaemia
- No previous myocardial infarction
- Family history of coronary artery disease (father had MI at age 60)

Current Medications:
- Metformin 1g BD
- Ramipril 5mg OD
- Atorvastatin 40mg ON
- Aspirin 75mg OD

Examination:
BP: 142/88 mmHg, HR: 78 bpm regular, BMI: 29
Heart sounds: Normal S1 S2, no murmurs
Chest: Clear
Peripheral pulses: Present and equal

Investigations:
- ECG: Normal sinus rhythm, no ST changes
- Bloods: HbA1c 7.2%, Total cholesterol 4.8, eGFR 78

Assessment:
This gentleman presents with typical stable angina symptoms. Given his cardiovascular risk factors, I recommend further investigation.

Plan:
1. Exercise tolerance test arranged
2. Commence GTN spray PRN for angina symptoms
3. Continue current medications
4. Lifestyle advice given regarding diet and exercise
5. Review in 6 weeks with ETT results

Kind regards,
Dr. Sarah Johnson
Consultant Cardiologist"""
    },
    {
        "name": "Respiratory Clinic Letter - Patient B",
        "text": """NHS Number: 987 654 3210
Consultant: Dr. Michael Chen
Specialty: Respiratory Medicine

Dear Dr. Williams,

Re: Mrs. Margaret Thompson, DOB: 22/08/1945

I reviewed this 78-year-old lady in clinic today regarding her chronic cough and progressive breathlessness.

History of Presenting Complaint:
Mrs. Thompson reports worsening breathlessness over the past 18 months, now limiting her to walking approximately 100 metres on the flat. She has a persistent productive cough with white sputum, worse in the mornings. She denies haemoptysis, fever, or weight loss.

Smoking History:
40 pack-year history, stopped smoking 5 years ago.

Past Medical History:
- COPD (GOLD Stage III)
- Osteoporosis
- Atrial fibrillation (rate controlled)
- Previous pulmonary embolism (2019)

Current Medications:
- Seretide 500 Accuhaler BD
- Tiotropium 18mcg OD
- Salbutamol PRN
- Rivaroxaban 20mg OD
- Bisoprolol 5mg OD
- Alendronic acid 70mg weekly
- Adcal D3 BD

Examination:
O2 sats: 92% on air, RR: 20/min
Chest: Bilateral expiratory wheeze, reduced air entry bases
No peripheral oedema

Spirometry Results:
FEV1: 0.92L (42% predicted)
FVC: 2.1L (78% predicted)
FEV1/FVC: 0.44

Assessment:
Severe COPD with progressive symptoms despite optimal inhaler therapy. No evidence of acute exacerbation today.

Plan:
1. Refer for pulmonary rehabilitation
2. Add Roflumilast 500mcg OD given frequent exacerbations
3. Pneumococcal and influenza vaccines up to date
4. Home oxygen assessment arranged
5. COPD action plan reviewed
6. Follow-up in 3 months

Yours sincerely,
Dr. Michael Chen
Consultant Respiratory Physician"""
    },
    {
        "name": "Neurology Clinic Letter - Patient C",
        "text": """NHS Number: 456 789 0123
Consultant: Dr. Emma Wilson
Specialty: Neurology

Dear Dr. Brown,

Re: Ms. Rebecca Foster, DOB: 10/11/1982

Thank you for referring this 41-year-old teacher who presents with recurring headaches and visual disturbance.

History of Presenting Complaint:
Ms. Foster describes a 6-month history of severe, unilateral throbbing headaches, typically affecting the right temple. Episodes last 4-72 hours and are associated with nausea, photophobia, and phonophobia. She reports a visual aura preceding approximately 50% of attacks, described as "zigzag lines" lasting 20-30 minutes. Frequency has increased to 3-4 attacks per month, significantly impacting her work.

Past Medical History:
- Migraine with aura (since age 25, previously well controlled)
- Depression (stable on sertraline)
- No history of head injury or seizures
- No family history of stroke

Current Medications:
- Sertraline 50mg OD
- Sumatriptan 50mg PRN (using 6-8 per month)

Examination:
Neurological examination: Normal cranial nerves, power, sensation, coordination and reflexes
Fundoscopy: Normal optic discs
BP: 118/72 mmHg

Assessment:
Chronic migraine with aura, poorly controlled with current management. Red flags excluded.

Plan:
1. Start Topiramate 25mg ON, titrate to 50mg BD over 4 weeks for migraine prophylaxis
2. Reduce triptan use to maximum 10 days per month to avoid medication overuse headache
3. Headache diary provided
4. Lifestyle modifications discussed (sleep hygiene, regular meals, hydration)
5. Avoid combined oral contraceptives given migraine with aura
6. MRI brain arranged to exclude structural pathology (routine, not urgent)
7. Review in 8 weeks

Best wishes,
Dr. Emma Wilson
Consultant Neurologist"""
    },
    {
        "name": "Diabetes Clinic Letter - Patient D",
        "text": """NHS Number: 321 654 9870
Consultant: Dr. Raj Patel
Specialty: Endocrinology/Diabetes

Dear Dr. Taylor,

Re: Mr. Ahmed Khan, DOB: 03/06/1970

I reviewed Mr. Khan in the diabetes clinic today for his annual review and insulin optimisation.

History:
Mr. Khan is a 53-year-old gentleman with Type 2 Diabetes Mellitus diagnosed 12 years ago. He was started on insulin 3 years ago due to secondary sulphonylurea failure. He reports variable blood glucose readings, with fasting levels typically 8-12 mmol/L and post-prandial spikes to 15-18 mmol/L. He has experienced 2 episodes of mild hypoglycaemia in the past month.

Past Medical History:
- Type 2 Diabetes Mellitus
- Diabetic retinopathy (background, stable)
- Microalbuminuria
- Hypertension
- Obesity (BMI 34)

Current Medications:
- Lantus (insulin glargine) 42 units ON
- Metformin 1g BD
- Linagliptin 5mg OD
- Ramipril 10mg OD
- Amlodipine 10mg OD

Recent Results:
- HbA1c: 8.4% (target <7%)
- eGFR: 62 (stage 3a CKD)
- Urine ACR: 4.2 mg/mmol
- Total cholesterol: 4.2
- Retinal screening: Background retinopathy, no maculopathy

Examination:
BP: 138/82 mmHg
Weight: 98kg (stable)
Feet: Intact sensation to monofilament, pulses present, no ulcers

Assessment:
Suboptimal glycaemic control despite basal insulin. Evidence of microvascular complications (retinopathy, nephropathy).

Plan:
1. Increase Lantus to 48 units ON
2. Add Empagliflozin 10mg OD for cardiovascular and renal protection
3. Continue Metformin (dose adjusted for renal function)
4. Target HbA1c <7.5% given hypoglycaemia episodes
5. Dietitian referral for weight management support
6. Retinal screening: Annual
7. Foot review: Annual with podiatry
8. Review in 3 months with HbA1c

Kind regards,
Dr. Raj Patel
Consultant Diabetologist"""
    },
    {
        "name": "Gastroenterology Clinic Letter - Patient E",
        "text": """NHS Number: 789 012 3456
Consultant: Dr. Lisa Murphy
Specialty: Gastroenterology

Dear Dr. Anderson,

Re: Mrs. Susan Clark, DOB: 28/02/1965

I saw Mrs. Clark today regarding her ongoing gastrointestinal symptoms and recent colonoscopy findings.

History of Presenting Complaint:
This 58-year-old lady presents with a 4-month history of altered bowel habit, predominantly loose stools 3-4 times daily, associated with intermittent crampy abdominal pain relieved by defecation. She reports occasional rectal bleeding, described as bright red blood on the paper. She denies weight loss, night sweats, or family history of colorectal cancer.

Past Medical History:
- Irritable bowel syndrome (diagnosed 2010)
- Appendicectomy (1985)
- No previous colonoscopy

Investigations:
Colonoscopy (last week): Examination to caecum. Two sessile polyps identified in the sigmoid colon (8mm and 5mm), removed by snare polypectomy. No other abnormalities. Histology awaited.

Bloods:
- FBC: Hb 118 (mild anaemia), MCV 76 (microcytic)
- Ferritin: 12 (low)
- CRP: <5
- Coeliac serology: Negative

Assessment:
Sigmoid polyps (awaiting histology) with iron deficiency anaemia, likely secondary to chronic blood loss.

Plan:
1. Await histology - if adenomatous polyps, will need surveillance colonoscopy in 3 years
2. Start Ferrous Fumarate 210mg TDS for 3 months
3. OGD arranged to exclude upper GI source of blood loss
4. Repeat FBC in 6 weeks
5. If histology shows high-risk features, will discuss at MDT
6. Colonoscopy findings letter sent to patient

Yours sincerely,
Dr. Lisa Murphy
Consultant Gastroenterologist"""
    }
]


class Command(BaseCommand):
    help = 'Set up demo data for MedCAT Trainer including group, project, and mock documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing demo data before creating new',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Setting up MedCAT Trainer demo data...'))

        # Check if model pack exists
        model_pack = ModelPack.objects.first()
        if not model_pack:
            self.stdout.write(self.style.ERROR(
                'No ModelPack found. Please upload a model pack first via Admin.'
            ))
            return

        self.stdout.write(f'Using ModelPack: {model_pack.name}')

        # Get or create admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'is_superuser': True,
                'is_staff': True,
                'email': 'admin@example.com'
            }
        )
        if created:
            admin.set_password('admin')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin user (password: admin)'))
        else:
            self.stdout.write('Admin user already exists')

        # Reset if requested
        if options['reset']:
            self.stdout.write('Resetting existing demo data...')
            ProjectAnnotateEntities.objects.filter(name='Demo Project').delete()
            Dataset.objects.filter(name='Demo Clinical Letters').delete()

        # Disconnect the post_save signal that requires a file
        post_save.disconnect(save_dataset, sender=Dataset)

        try:
            # Create Dataset directly (bypassing the signal that requires a file)
            dataset, created = Dataset.objects.get_or_create(
                name='Demo Clinical Letters',
                defaults={'description': 'Sample clinical letters for demonstration'}
            )
            if created:
                self.stdout.write(self.style.SUCCESS('Created Dataset: Demo Clinical Letters'))
            else:
                self.stdout.write('Dataset already exists')
        finally:
            # Reconnect the signal
            post_save.connect(save_dataset, sender=Dataset)

        # Create Documents
        for letter in SAMPLE_CLINICAL_LETTERS:
            doc, created = Document.objects.get_or_create(
                name=letter['name'],
                dataset=dataset,
                defaults={
                    'text': letter['text'],
                    'source_file_type': 'demo'
                }
            )
            if created:
                # Extract regex fields
                from api.regex_extractors import extract_all_fields
                fields = extract_all_fields(letter['text'])
                doc.nhs_number = fields.get('nhs_number')
                doc.consultant = fields.get('consultant')
                doc.specialty = fields.get('specialty')
                doc.save()
                self.stdout.write(f'  Created document: {letter["name"]}')
            else:
                self.stdout.write(f'  Document exists: {letter["name"]}')

        # Create Project
        project, created = ProjectAnnotateEntities.objects.get_or_create(
            name='Demo Project',
            defaults={
                'description': 'Demo project for testing MedCAT annotations with sample clinical letters',
                'dataset': dataset,
                'model_pack': model_pack,
                'cuis': '',
                'require_entity_validation': False,
                'train_model_on_submit': False,
            }
        )
        if created:
            project.members.add(admin)
            self.stdout.write(self.style.SUCCESS('Created Project: Demo Project'))
        else:
            self.stdout.write('Project already exists')

        self.stdout.write(self.style.SUCCESS(
            f'\nDemo setup complete!\n'
            f'  - ModelPack: {model_pack.name}\n'
            f'  - Dataset: {dataset.name} ({Document.objects.filter(dataset=dataset).count()} documents)\n'
            f'  - Project: {project.name}\n'
            f'\nAccess the demo at: http://localhost:8001'
        ))
