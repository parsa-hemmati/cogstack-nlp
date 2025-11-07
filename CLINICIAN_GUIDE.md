# CogStack NLP: A Guide for Clinicians

A non-technical introduction to using AI for extracting insights from clinical notes and medical records.

---

## What is CogStack NLP?

CogStack NLP is a tool that helps **read and understand clinical notes automatically**, just like a human would, but much faster. It can process thousands of patient records in minutes and identify medical concepts like diagnoses, symptoms, medications, and procedures.

Think of it as a **highly trained medical assistant** that can:
- Read through thousands of clinic letters, discharge summaries, or progress notes
- Identify and highlight medical terms (like "type 2 diabetes" or "atrial fibrillation")
- Link those terms to standardized medical vocabularies (SNOMED-CT, UMLS)
- Understand context (e.g., "no evidence of infection" vs. "bacterial infection")

**No coding required** - there are web-based interfaces designed for clinical use.

---

## Why Should Clinicians Care?

### Real-World Clinical Challenges

As a clinician, you likely face these challenges:

1. **Research Questions**: "How many of my patients with heart failure also have diabetes?"
2. **Audit and Quality Improvement**: "Are we documenting falls risk assessments consistently?"
3. **Patient Safety**: "Which patients are on aspirin AND clopidogrel?" (polypharmacy checks)
4. **Clinical Coding**: "Help clinical coders identify conditions mentioned in discharge letters"
5. **Cohort Identification**: "Find all patients with suspected COVID-19 in the last 6 months"

Traditionally, answering these questions requires:
- Manual chart review (hours or days per patient)
- Relying on coded data (which misses free-text information)
- Limited sample sizes due to time constraints

**CogStack NLP automates this**, allowing you to:
- Search across thousands of records in minutes
- Extract information from free-text notes (not just coded fields)
- Generate reports for research, audit, or quality improvement

---

## How Does It Work? (Simplified)

### Step 1: You Provide Text
Give the system clinical text - this could be:
- Progress notes
- Discharge summaries
- Radiology reports
- Clinic letters
- Pathology reports

### Step 2: The System Reads and Highlights
The AI "reads" the text and identifies medical concepts:

**Example Input:**
```
Patient presents with 3-day history of chest pain radiating to left arm.
Background of type 2 diabetes mellitus controlled on metformin.
ECG shows ST elevation in leads II, III, aVF.
Diagnosis: Acute inferior STEMI.
```

**What the System Finds:**
- **Symptoms**: "chest pain" → links to medical code C0008031
- **Conditions**: "type 2 diabetes mellitus" → links to SNOMED code 44054006
- **Medications**: "metformin" → links to drug database
- **Findings**: "ST elevation" → links to ECG finding code
- **Diagnosis**: "Acute inferior STEMI" → links to myocardial infarction code

### Step 3: You Get Structured Results
Instead of reading thousands of notes manually, you get:
- Spreadsheets with extracted diagnoses per patient
- Counts of how many times conditions appear
- Links to the original text (for verification)

---

## What Can You Do With It?

### 1. Clinical Audit
**Question**: "Are we documenting VTE risk assessments in all surgical patients?"

**Traditional Method**: Manually review 100 patient charts over several days.

**With CogStack NLP**: Search 1,000+ records in an hour for keywords like "VTE risk," "prophylaxis," "LMWH," "mechanical prophylaxis."

### 2. Research and Publications
**Question**: "What are the most common complications in patients with inflammatory bowel disease?"

**Traditional Method**: Limited manual review, small sample size.

**With CogStack NLP**: Extract complications from 5,000+ patient records, enabling robust statistical analysis.

### 3. Patient Identification for Trials
**Question**: "Which patients with rheumatoid arthritis have failed methotrexate?"

**Traditional Method**: Ask rheumatolgy team to manually identify patients.

**With CogStack NLP**: Automatically identify patients who have:
- Diagnosis: "rheumatoid arthritis"
- Medication: "methotrexate"
- Keywords: "failed," "intolerant," "stopped"

### 4. Safety Alerts and Pharmacovigilance
**Question**: "Which patients are on triple antiplatelets (aspirin + clopidogrel + anticoagulant)?"

**With CogStack NLP**: Scan medication lists in clinical notes and flag high-risk combinations.

### 5. De-identification for Data Sharing
**Question**: "Can I share these notes for research without breaching patient confidentiality?"

**With CogStack NLP (AnonCAT)**: Automatically remove:
- Patient names
- Addresses
- Phone numbers
- NHS numbers / MRN
- Dates of birth

---

## Getting Started (No Coding Required)

### Option 1: Use the Web Demo (Easiest)
Try out MedCAT without any installation:

1. Visit the [MedCAT Demo App](https://medcat.sites.er.kcl.ac.uk/)
2. Paste in clinical text (anonymized!)
3. See highlighted medical entities instantly
4. Click on highlighted terms to see linked medical codes

**Perfect for**: Testing the tool, understanding how it works, small-scale exploration.

### Option 2: MedCAT Trainer (Build Your Own Model)
If you want to customize the tool for your specialty (e.g., cardiology, psychiatry):

1. Your IT team sets up MedCAT Trainer (a web interface)
2. You upload sample clinical notes from your domain
3. You review and correct what the AI identifies (supervised learning)
4. The AI learns from your corrections and improves

**Perfect for**: Specialty-specific models, improving accuracy, training the AI on local terminology.

**Documentation**: [MedCAT Trainer Guide](medcat-trainer/)

### Option 3: Work With Your IT/Informatics Team
For large-scale deployment:

1. **You define the clinical question** (e.g., "Find all patients with heart failure and anemia")
2. **IT team sets up MedCAT Service** (runs in the background)
3. **MedCAT processes your EHR data** (with appropriate governance)
4. **You receive structured output** (Excel/CSV file with results)

**Perfect for**: Research projects, clinical audits, ongoing quality improvement.

---

## Understanding the Output

When MedCAT processes text, you'll see results like this:

| Term Found | Medical Name | Medical Code | Confidence | Context |
|------------|-------------|--------------|------------|---------|
| "chest pain" | Chest Pain | C0008031 (UMLS) | 99% | Affirmed |
| "no fever" | Fever | C0015967 (UMLS) | 95% | Negated |
| "COPD" | Chronic Obstructive Pulmonary Disease | 13645005 (SNOMED) | 98% | Affirmed |
| "metformin" | Metformin | C0025598 (UMLS) | 99% | Affirmed |

### Key Columns Explained:

- **Term Found**: The exact text from the clinical note
- **Medical Name**: Standardized medical name (may differ from local slang/abbreviations)
- **Medical Code**: Links to SNOMED-CT, UMLS, or ICD-10 codes
- **Confidence**: How sure the AI is (higher = more certain)
- **Context**: Whether the condition is present (affirmed), absent (negated), or uncertain

---

## Important Considerations for Clinicians

### 1. Accuracy Is Not Perfect
- MedCAT is typically **85-95% accurate** (depending on the model and clinical domain)
- **Always verify critical findings** manually before making clinical decisions
- Best used for **screening** (identifying potential cases for review) rather than definitive diagnosis

### 2. Garbage In, Garbage Out
- Quality depends on the quality of clinical notes
- Abbreviations, typos, and unclear documentation reduce accuracy
- Well-structured notes → better results

### 3. Context Matters
- The AI can distinguish "no history of diabetes" from "diabetes"
- It understands "suspected pneumonia" vs. "confirmed pneumonia"
- However, complex clinical reasoning (e.g., "patient too frail for surgery") is harder

### 4. Information Governance
- Always follow local data protection policies
- De-identify data when sharing outside your organization
- Ensure appropriate ethical approvals for research use

### 5. It's a Tool, Not a Replacement
- Use NLP to **augment** clinical work, not replace clinical judgment
- Human review is essential for critical decisions
- Think of it as an intelligent search engine, not a diagnostic tool

---

## Real-World Examples

### Example 1: Cardiology Audit
**Clinical Question**: "How many patients with heart failure are on guideline-directed medical therapy (GDMT)?"

**Process**:
1. MedCAT scans 2,000 cardiology clinic letters
2. Identifies patients with "heart failure" diagnosis
3. Extracts medications: ACE inhibitors, beta-blockers, mineralocorticoid receptor antagonists
4. Generates report showing GDMT compliance rates

**Outcome**: Identified gaps in therapy, leading to quality improvement project.

---

### Example 2: Infectious Diseases Research
**Clinical Question**: "What are the most common side effects of antiretroviral therapy mentioned in clinic notes?"

**Process**:
1. MedCAT processes 5,000 HIV clinic notes
2. Extracts mentions of "nausea," "diarrhea," "lipodystrophy," etc.
3. Links side effects to specific antiretroviral medications
4. Produces frequency table for publication

**Outcome**: Published research paper on real-world treatment tolerability.

---

### Example 3: Emergency Department Safety
**Clinical Question**: "Are we documenting head injury advice in all patients with minor head trauma?"

**Process**:
1. MedCAT searches 500 ED discharge letters
2. Identifies patients with "head injury" or "head trauma"
3. Checks for presence of keywords: "head injury advice," "return if," "warning signs"
4. Flags cases missing documentation

**Outcome**: Improved documentation compliance from 65% to 95%.

---

## Frequently Asked Questions

### Q: Do I need to know how to code?
**A:** No. There are web-based interfaces designed for clinicians. Your IT team can set up the backend, and you interact through a browser.

### Q: Can it read handwritten notes?
**A:** Only if they've been converted to text first (e.g., using handwriting recognition software). MedCAT works with typed/digital text.

### Q: What if the AI makes a mistake?
**A:** Always verify results, especially for clinical decisions. You can also retrain the AI to improve accuracy using MedCAT Trainer.

### Q: Is it HIPAA/GDPR compliant?
**A:** CogStack NLP itself is a tool - compliance depends on how it's deployed. Work with your IT and information governance teams to ensure appropriate data handling.

### Q: Can it replace clinical coders?
**A:** No, but it can assist by pre-populating likely codes, which coders then verify. Think of it as a "first pass" tool.

### Q: What languages does it support?
**A:** Primarily English, but models exist for Dutch and other languages. Custom models can be built for other languages with appropriate training data.

### Q: How long does it take to process records?
**A:** Very fast - typically hundreds of documents per minute once set up. The bottleneck is usually data extraction from your EHR system.

### Q: Can I use it for retrospective research?
**A:** Yes, this is one of the most common use cases. Ensure you have ethical approval and follow local data governance policies.

### Q: What if my specialty uses unique terminology?
**A:** You can train a custom model using MedCAT Trainer. Provide examples of your specialty's notes, and the AI will learn your terminology.

### Q: Is it free?
**A:** The software is open-source and free to use. However, you need:
- A free UMLS license (from NIH) to download pre-trained models
- IT infrastructure to run it (or cloud hosting costs)

---

## Getting Help and Support

### For Technical Setup
- **Documentation**: [https://docs.cogstack.org](https://docs.cogstack.org)
- **GitHub Repository**: [https://github.com/CogStack/cogstack-nlp](https://github.com/CogStack/cogstack-nlp)
- **Community Forum**: [https://discourse.cogstack.org](https://discourse.cogstack.org)

### For Clinical Applications
- Post your questions on the [CogStack Discourse forum](https://discourse.cogstack.org)
- Many clinicians and clinical informaticians are active there
- Search for previous discussions on similar topics

### For Model Access
- **Model Download**: [https://medcat.sites.er.kcl.ac.uk/auth-callback](https://medcat.sites.er.kcl.ac.uk/auth-callback)
- Requires free NIH/UMLS account

---

## Next Steps for Clinicians

### 1. Explore (15 minutes)
- Visit the [MedCAT Demo](https://medcat.sites.er.kcl.ac.uk/)
- Try pasting in anonymized clinical text
- See what medical concepts it identifies

### 2. Identify a Use Case (1 hour)
- Think of a clinical question or audit you've wanted to do
- Consider: "Would this benefit from analyzing lots of clinical notes?"
- Draft a one-paragraph description

### 3. Engage Your Team (1 week)
- Talk to your clinical informatics or IT team
- Share this guide and your use case
- Discuss feasibility and data governance requirements

### 4. Start Small (1-3 months)
- Pilot project with 100-500 records
- Validate results manually
- Refine approach before scaling up

### 5. Share Your Experience
- Present findings at local audit meetings
- Submit to conferences (tool papers welcome!)
- Help other clinicians learn from your experience

---

## Key Takeaways

1. **CogStack NLP extracts medical information from free-text notes automatically**
2. **No coding required** - web interfaces available for clinicians
3. **Use cases include**: research, audit, cohort identification, safety monitoring
4. **85-95% accurate** - always verify critical findings
5. **Start with the demo** to understand capabilities
6. **Work with your IT team** for production deployment
7. **Think augmentation, not replacement** - it's a tool to help you work smarter

---

## Additional Resources

### For Clinical Use
- [MedCAT Demo App](medcat-demo-app/) - Try it in your browser
- [MedCAT Trainer](medcat-trainer/) - Build custom models
- [Quick Start Guide](QUICK_START.md) - Technical quick start

### For Understanding the Technology
- [Original MedCAT Paper (arXiv)](https://arxiv.org/abs/2010.01165)
- [Video Tutorials](medcat-v2-tutorials/) - Step-by-step guides
- [CogStack Discourse](https://discourse.cogstack.org/) - Community discussions

### For Data Governance
- Work with your local Caldicott Guardian / Data Protection Officer
- Ensure appropriate ethical approvals for research
- Follow NHS Digital / local data sharing agreements

---

## Glossary for Clinicians

**NLP (Natural Language Processing)**: The field of AI that helps computers understand human language.

**Entity Recognition**: The process of identifying medical terms (like "diabetes") in text.

**Entity Linking**: Connecting identified terms to standardized medical codes (like SNOMED-CT).

**SNOMED-CT**: Systematized Nomenclature of Medicine - Clinical Terms. A standardized medical vocabulary used globally.

**UMLS**: Unified Medical Language System. A collection of medical vocabularies maintained by the US National Library of Medicine.

**CUI (Concept Unique Identifier)**: A unique code in UMLS for each medical concept.

**Context Detection**: Understanding whether a term is affirmed ("has diabetes"), negated ("no diabetes"), or uncertain ("?diabetes").

**MetaCAT**: A component that adds extra information (like experiencer: patient vs. family history, or temporality: current vs. past).

**Model**: The AI "brain" that has been trained to recognize medical concepts. Pre-trained models exist, or you can build custom ones.

**Confidence Score**: How certain the AI is about its identification (0-100%). Higher scores = more reliable.

**De-identification**: Removing personal identifiable information (names, addresses, etc.) from text to protect patient privacy.

---

**Questions?** Visit our [discussion forum](https://discourse.cogstack.org/) or contact your local clinical informatics team.

**Ready to try it?** Start with the [MedCAT Demo](https://medcat.sites.er.kcl.ac.uk/) - no installation required!
