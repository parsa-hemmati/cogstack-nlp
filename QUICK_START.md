# Quick Start Guide

Get started with CogStack NLP in under 5 minutes!

## What is CogStack NLP?

CogStack NLP provides tools to extract medical information from clinical text in Electronic Health Records (EHRs). The core tool is **MedCAT** - a machine learning algorithm that identifies and links medical concepts to ontologies like SNOMED-CT and UMLS.

## Installation

### Option 1: Python Package (Recommended for Development)

```bash
# Basic installation
pip install medcat

# With all features (spacy, meta-annotation, de-identification)
pip install "medcat[spacy,meta-cat,deid]"
```

### Option 2: Docker Services (Recommended for Production)

Use pre-built Docker services for REST API or web demos:
- **MedCAT Service**: [medcat-service/](medcat-service/) - REST API for production
- **MedCAT Demo App**: [medcat-demo-app/](medcat-demo-app/) - Interactive web demo
- **AnonCAT Demo**: [anoncat-demo-app/](anoncat-demo-app/) - De-identification demo

## Get a Model

1. Visit the [MedCAT model download page](https://uts.nlm.nih.gov/uts/login?service=https://medcat.sites.er.kcl.ac.uk/auth-callback)
2. Sign in with your NIH/UMLS credentials (free to register)
3. Download a pre-trained model (SNOMED-CT or UMLS based)

**Available models:**
- SNOMED-CT UK Clinical + UMLS (2024, 2025 editions)
- UMLS Full (4M+ concepts)
- Dutch UMLS model

## Basic Usage

```python
from medcat.cat import CAT

# Load your model
cat = CAT.load_model_pack("<path_to_model_pack.zip>")

# Process clinical text
text = """
Patient presents with severe chest pain and shortness of breath.
History of type 2 diabetes mellitus and hypertension.
"""

# Extract medical entities
entities = cat.get_entities(text)

# Print results
for entity in entities['entities'].values():
    print(f"{entity['pretty_name']}: {entity['source_value']} (CUI: {entity['cui']})")
```

### Expected Output

```
Chest pain: chest pain (CUI: C0008031)
Shortness of breath: shortness of breath (CUI: C0013404)
Type 2 diabetes mellitus: type 2 diabetes mellitus (CUI: C0011860)
Hypertension: hypertension (CUI: C0020538)
```

## Quick Test with Docker

Run the MedCAT demo app (requires model download first):

```bash
cd medcat-demo-app
# Follow instructions in medcat-demo-app/README.md
docker-compose up
```

Visit `http://localhost:8001` to annotate text in your browser.

## Next Steps

### Tutorials
- [MedCAT v2 Tutorials](medcat-v2-tutorials/) - Interactive Jupyter notebooks
- [Migration Guide](medcat-v2/docs/migration_guide_v2.md) - Moving from v1 to v2

### Tools
- **[MedCAT Trainer](medcat-trainer/)**: Build and improve custom NER+L models
- **[MedCAT Service](medcat-service/)**: Production-ready REST API
- **[MedCAT Scripts](medcat-scripts/)**: CLI tools for model management

### Resources
- [Official Documentation](https://docs.cogstack.org)
- [API Reference](https://cogstack-nlp.readthedocs.io/)
- [Discussion Forum](https://discourse.cogstack.org/)
- [Paper on arXiv](https://arxiv.org/abs/2010.01165)

## Common Use Cases

| Task | Tool | Location |
|------|------|----------|
| Extract medical entities from text | MedCAT Library | [medcat-v2/](medcat-v2/) |
| Build/train custom models | MedCAT Trainer | [medcat-trainer/](medcat-trainer/) |
| REST API for production | MedCAT Service | [medcat-service/](medcat-service/) |
| De-identify clinical text | AnonCAT | [anoncat-demo-app/](anoncat-demo-app/) |
| Try before installing | Demo App | [medcat-demo-app/](medcat-demo-app/) |

## Troubleshooting

**No model available?**
You need a UMLS license (free) to download models. [Register here](https://uts.nlm.nih.gov/uts/).

**Version conflicts?**
MedCAT v2 can load v1 models but requires conversion. See [migration tutorials](medcat-v2-tutorials/notebooks/introductory/migration/).

**Need help?**
Post on [Discourse](https://discourse.cogstack.org/) or check [GitHub Issues](https://github.com/CogStack/cogstack-nlp/issues).

## License

MedCAT uses the [Elastic License 2.0](LICENSE).
