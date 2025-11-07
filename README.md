# Cogstack NLP

[![Build Status](https://github.com/CogStack/cogstack-nlp/actions/workflows/medcat-v2_main.yml/badge.svg?branch=main)](https://github.com/CogStack/cogstack-nlp/actions/workflows/medcat-v2_main.yml/badge.svg?branch=main)
[![Documentation Status](https://readthedocs.org/projects/cogstack-nlp/badge/?version=latest)](https://readthedocs.org/projects/cogstack-nlp/badge/?version=latest)
[![Latest release](https://img.shields.io/github/v/release/CogStack/cogstack-nlp?filter=medcat/*)](https://github.com/CogStack/cogstack-nlp/releases/latest)
<!-- [![pypi Version](https://img.shields.io/pypi/v/medcat.svg?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/medcat/) -->

CogStack Natural Language Processing offers tools to process and extract information from clinical text and documents in Electronic Health Records (EHRs).

The primary NLP focus is the [Medical Concept Annotation Tool](medcat-v2/README.md) (MedCAT), a self-supervised machine learning algorithm for extracting concepts using any concept vocabulary including UMLS/SNOMED-CT. See the paper on [arXiv](https://arxiv.org/abs/2010.01165).


**Official Docs [here](https://docs.cogstack.org)**

**Discussion Forum [discourse](https://discourse.cogstack.org/)**

---

## 🚀 Quick Start Guides

### For Users

**Get started with MedCAT in 5 minutes**: See [QUICK_START.md](QUICK_START.md)

**Clinician Guide** (non-technical): See [CLINICIAN_GUIDE.md](CLINICIAN_GUIDE.md)

**IT Deployment Guide** (production setup): See [IT_DEPLOYMENT_GUIDE.md](IT_DEPLOYMENT_GUIDE.md)

### For Developers: Spec-Kit Framework

This project uses **[Spec-Kit](https://github.com/github/spec-kit)** for specification-driven development.

#### 🎯 Build Your Next Feature

1. **Write Specification** → `.specify/specifications/feature-name.md`
   - Define WHAT needs to be built and WHY
   - Include user stories and acceptance criteria

2. **Create Technical Plan** → `.specify/plans/feature-name-plan.md`
   - Define HOW to implement the specification
   - Architecture, tech stack, data models

3. **Break into Tasks** → `.specify/tasks/feature-name-tasks.md`
   - Create actionable, ordered tasks
   - Each task completable in one session

4. **Implement Systematically** → Follow task-by-task approach
   - Test each task against acceptance criteria
   - Document decisions and deviations

📖 **Complete Guide**: See [.specify/README.md](.specify/README.md)

📋 **Example Specification**: See [Meta-Annotations UI](.specify/specifications/meta-annotations-ui.md)

🏛️ **Project Constitution**: See [Project Constitution](.specify/constitution/project-constitution.md)

#### 🤖 Alternative: CCPM (Claude Code Project Manager)

For **parallel agent execution** and **GitHub-native workflows**, consider [CCPM](https://github.com/automazeio/ccpm):

**Spec-Kit vs CCPM Comparison:**

| Feature | Spec-Kit | CCPM |
|---------|----------|------|
| **Focus** | Specification-driven development | Multi-agent orchestration |
| **Storage** | `.specify/` directory | GitHub Issues |
| **Workflow** | Constitution → Specs → Plans → Tasks | PRD → Epic → Issues → Worktrees |
| **Execution** | Single agent/developer | Multiple parallel agents |
| **Best For** | Detailed specifications, governance | Team collaboration, parallel work |

**Hybrid Approach** (Recommended for Large Teams):
1. Use **Spec-Kit** for high-level specifications and governance
2. Use **CCPM** to break specs into GitHub issues and coordinate parallel agents
3. Link CCPM epics to Spec-Kit specifications for traceability

**Example Workflow**:
```bash
# 1. Write specification (Spec-Kit)
.specify/specifications/fhir-integration.md

# 2. Create GitHub epic from spec (CCPM)
/pm:prd-parse .specify/specifications/fhir-integration.md

# 3. Decompose into parallel tasks (CCPM)
/pm:epic-oneshot

# 4. Multiple agents work on independent issues
/pm:issue-start #42  # Agent 1: API layer
/pm:issue-start #43  # Agent 2: UI components
/pm:issue-start #44  # Agent 3: Tests
```

---

## Projects

### NLP
- [Medical Concept Annotation Tool](medcat-v2/README.md): MedCAT can be used to extract information from Electronic Health Records (EHRs) and link it to biomedical ontologies like SNOMED-CT, UMLS, or HPO (and potentially other ontologies).
- [Medical Concept Annotation Tool Trainer](medcat-trainer/README.md): MedCATTrainer is an interface for building, improving and customising a given Named Entity Recognition and Linking (NER+L) model (MedCAT) for biomedical domain text.
- [MedCAT Service](medcat-service/README.md): A REST API wrapper for [MedCAT](https://github.com/CogStack/cogstack-nlp/blob/main/medcat-v2/), allowing you to send text for processing and receive structured annotations in response.

### Learning and Demos
- [Deidentify app](anoncat-demo-app/README.md): Demo for AnonCAT. It uses [MedCAT](https://github.com/CogStack/cogstack-nlp/tree/main/medcat-v2), an advanced natural language processing tool, to identify and classify sensitive information, such as names, addresses, and medical terms.
- [MedCAT Demo App](medcat-demo-app/README.md): A simple web application showcasing how to use MedCAT for clinical text annotation.
- [MedCAT Tutorials](medcat-v2-tutorials/README.md): The MedCAT Tutorials privde an interactive learning path for using MedCAT