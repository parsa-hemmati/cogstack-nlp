# Healthcare Compliance Framework for CogStack NLP

**Last Updated**: 2025-01-07
**Applicable Regulations**: HIPAA, GDPR, UK GDPR, 21 CFR Part 11
**Target Audience**: Compliance Officers, Information Security, Legal, IT Leadership

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [HIPAA Compliance](#hipaa-compliance)
3. [GDPR/UK GDPR Compliance](#gdpruk-gdpr-compliance)
4. [21 CFR Part 11 (Clinical Trials)](#21-cfr-part-11-clinical-trials)
5. [Data Governance Requirements](#data-governance-requirements)
6. [Technical Controls](#technical-controls)
7. [Audit & Monitoring](#audit--monitoring)
8. [Incident Response](#incident-response)
9. [Compliance Checklist](#compliance-checklist)
10. [Documentation Templates](#documentation-templates)

---

## Executive Summary

CogStack NLP processes Protected Health Information (PHI) and Personal Data, making regulatory compliance critical. This framework provides:

- **HIPAA**: Compliance requirements for US healthcare organizations
- **GDPR/UK GDPR**: Data protection for EU/UK deployments
- **21 CFR Part 11**: Electronic records in clinical trials
- **Technical controls**: Encryption, access control, audit logging
- **Governance**: Policies, procedures, training

**Compliance Status**: CogStack NLP is a **tool**. Compliance depends on **how you deploy and use it**. This guide helps ensure compliant deployment.

---

## HIPAA Compliance

### HIPAA Security Rule

**Requirement**: Protect electronic Protected Health Information (ePHI).

#### Administrative Safeguards

**1. Security Management Process**

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Risk Analysis | Conduct annual risk assessment of NLP system | ☐ Not Started ☐ In Progress ☑ Complete |
| Risk Management | Document and mitigate identified risks | ☐ Not Started ☐ In Progress ☑ Complete |
| Sanction Policy | Establish sanctions for HIPAA violations | ☐ Not Started ☐ In Progress ☑ Complete |
| Information System Activity Review | Review audit logs monthly | ☐ Not Started ☐ In Progress ☑ Complete |

**Implementation Example**:

```markdown
## CogStack NLP Risk Assessment

**Date**: 2024-01-15
**Assessor**: CISO

### Identified Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Unauthorized access to PHI | Medium | High | Implement RBAC, MFA |
| Data breach via API | Low | High | API authentication, rate limiting |
| Insufficient audit trail | Medium | Medium | Enable comprehensive logging |

### Risk Mitigation Plan

1. **Implement Role-Based Access Control (RBAC)**
   - Deadline: 2024-02-01
   - Owner: Security Team
   - Status: In Progress

2. **Enable Multi-Factor Authentication (MFA)**
   - Deadline: 2024-02-15
   - Owner: IT Team
   - Status: Not Started
```

---

**2. Workforce Security**

| Requirement | Implementation |
|-------------|----------------|
| Authorization/Supervision | Only authorized personnel access NLP system |
| Workforce Clearance | Background checks for staff handling PHI |
| Termination Procedures | Revoke access within 24 hours of termination |

**Access Request Form Template**:

```
CogStack NLP Access Request

Requestor: _____________________
Role: _____________________
Justification: _____________________
Access Level: ☐ Read-Only ☐ Analyst ☐ Administrator
Approver: _____________________
Date Granted: _____________________
Review Date: _____________________
```

---

**3. Information Access Management**

| Requirement | Implementation |
|-------------|----------------|
| Access Authorization | Role-based permissions (clinician, researcher, admin) |
| Access Establishment/Modification | Documented approval process |
| Termination | Automated user deprovisioning |

**Implementation** (FastAPI RBAC):

```python
from fastapi import Depends, HTTPException
from enum import Enum

class Role(Enum):
    CLINICIAN = "clinician"
    RESEARCHER = "researcher"
    ADMIN = "admin"

def require_role(required_role: Role):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Requires {required_role.value} role"
            )
        return current_user
    return role_checker

@app.get("/api/v1/patients/{patient_id}")
async def get_patient(
    patient_id: str,
    user: User = Depends(require_role(Role.CLINICIAN))
):
    # Only clinicians can access patient data
    ...
```

---

**4. Security Awareness Training**

| Requirement | Implementation |
|-------------|----------------|
| Initial Training | All users complete HIPAA training before access |
| Annual Refresher | Yearly training updates |
| Documentation | Training records retained 6 years |

**Training Topics**:
- [ ] HIPAA Privacy Rule basics
- [ ] Minimum Necessary Standard
- [ ] How NLP processes PHI
- [ ] De-identification vs. anonymization
- [ ] Incident reporting procedures
- [ ] Acceptable use of NLP system

---

#### Physical Safeguards

**1. Facility Access Controls**

| Requirement | On-Premise | Cloud |
|-------------|------------|-------|
| Facility Security Plan | Data center access badges | AWS/Azure compliance certifications |
| Access Control/Validation | Visitor logs, escort requirements | IAM policies, network segmentation |
| Maintenance Records | Server room access logs | Cloud audit logs |

**Cloud Deployment Checklist**:
- [ ] Cloud provider is HIPAA-compliant (AWS BAA, Azure BAA, GCP BAA)
- [ ] Data stored in HIPAA-compliant regions
- [ ] Encryption at rest enabled (AES-256)
- [ ] Network isolation (VPC/VNet)

---

**2. Workstation Security**

| Requirement | Implementation |
|-------------|----------------|
| Workstation Use | Screen locks after 5 minutes |
| Workstation Security | Full disk encryption, antivirus |

---

**3. Device and Media Controls**

| Requirement | Implementation |
|-------------|----------------|
| Disposal | Secure wipe (NIST 800-88) before disposal |
| Media Re-use | Overwrite data before reassignment |
| Accountability | Asset tracking for all devices |
| Data Backup/Storage | Encrypted backups, offsite storage |

**Secure Deletion Script**:

```bash
# Before decommissioning server
shred -vfz -n 3 /dev/sda  # Overwrite disk 3 times
```

---

#### Technical Safeguards

**1. Access Control**

| Requirement | Implementation |
|-------------|----------------|
| Unique User IDs | No shared accounts |
| Emergency Access | Break-glass admin account (logged) |
| Auto Logoff | Session timeout after 15 minutes |
| Encryption/Decryption | TLS 1.3 for data in transit, AES-256 at rest |

**Session Management**:

```python
from fastapi import Depends
from datetime import datetime, timedelta

SESSION_TIMEOUT = timedelta(minutes=15)

def check_session_expiry(session: Session):
    if datetime.now() - session.last_activity > SESSION_TIMEOUT:
        raise HTTPException(status_code=401, detail="Session expired")
    session.last_activity = datetime.now()
    return session
```

---

**2. Audit Controls**

**Requirement**: Log all ePHI access.

**What to Log**:

| Event | Log Fields |
|-------|-----------|
| User Login | Timestamp, User ID, IP Address, Success/Failure |
| Patient Search | Timestamp, User ID, Query, Results Count |
| Document Access | Timestamp, User ID, Document ID, Patient ID |
| Data Export | Timestamp, User ID, Number of Records, Export Format |
| Admin Changes | Timestamp, Admin ID, Action, Changed Fields |

**Implementation** (Structured Logging):

```python
import logging
import json

audit_logger = logging.getLogger('audit')

def log_patient_access(user_id: str, patient_id: str, action: str):
    audit_logger.info(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "patient_id": patient_id,
        "action": action,
        "source_ip": request.client.host
    }))

@app.get("/api/v1/patients/{patient_id}")
async def get_patient(patient_id: str, user: User = Depends(get_current_user)):
    log_patient_access(user.id, patient_id, "VIEW")
    # ...
```

**Log Retention**: 6 years (HIPAA requirement)

---

**3. Integrity Controls**

| Requirement | Implementation |
|-------------|----------------|
| Data Integrity | Checksums (SHA-256) for all PHI |
| Tampering Detection | Immutable audit logs (WORM storage) |

**Example**:

```python
import hashlib

def compute_document_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

# Store hash with document
doc_hash = compute_document_hash(clinical_note_text)
db.store(document_id, text, hash=doc_hash)

# Verify integrity on retrieval
retrieved_hash = compute_document_hash(retrieved_text)
assert retrieved_hash == stored_hash, "Document integrity violated"
```

---

**4. Transmission Security**

| Requirement | Implementation |
|-------------|----------------|
| Encryption | TLS 1.3 for all API calls |
| Certificate Validation | Valid, non-self-signed certificates |

**Nginx Configuration**:

```nginx
server {
    listen 443 ssl http2;
    server_name nlp.example.com;

    ssl_certificate /etc/ssl/certs/nlp.example.com.crt;
    ssl_certificate_key /etc/ssl/private/nlp.example.com.key;

    ssl_protocols TLSv1.3;
    ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256';
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

---

### HIPAA Privacy Rule

**Minimum Necessary Standard**: Access only the minimum PHI needed.

**Implementation**:

1. **Search Results Pagination**: Return 20 results max per query
2. **Field-Level Access Control**: Researchers see de-identified data, clinicians see full PHI
3. **Purpose Limitation**: Log and enforce "reason for access"

```python
@app.get("/api/v1/patients/search")
async def search_patients(
    query: str,
    purpose: str,  # "treatment", "research", "quality_improvement"
    user: User = Depends(get_current_user)
):
    # Validate purpose
    if purpose not in ["treatment", "research", "quality_improvement"]:
        raise HTTPException(400, "Invalid purpose")

    # Log purpose
    audit_logger.info(f"User {user.id} accessed PHI for {purpose}")

    # Apply minimum necessary filters
    if purpose == "research":
        # Return de-identified data only
        return deidentified_results(query)
    else:
        return full_results(query)
```

---

## GDPR/UK GDPR Compliance

### Key Principles

| Principle | Requirement | Implementation |
|-----------|-------------|----------------|
| Lawfulness, Fairness, Transparency | Legal basis for processing | Explicit consent or legitimate interest |
| Purpose Limitation | Data used only for stated purpose | Document use cases, enforce via policies |
| Data Minimization | Collect only necessary data | De-identify when possible |
| Accuracy | Keep data accurate and up-to-date | Data quality checks |
| Storage Limitation | Retain only as long as needed | Data retention policies |
| Integrity & Confidentiality | Protect against unauthorized access | Encryption, access controls |
| Accountability | Demonstrate compliance | Documentation, audit logs |

---

### Legal Basis for Processing

**Options**:

1. **Consent**: Explicit, informed consent from data subject
2. **Legitimate Interest**: Public health research, quality improvement
3. **Legal Obligation**: Required by law (e.g., public health reporting)

**Consent Form Template**:

```
CONSENT FOR NLP PROCESSING OF CLINICAL NOTES

I consent to the processing of my clinical notes using natural language
processing (NLP) technology for the following purposes:

☐ Improving quality of care
☐ Medical research (anonymized)
☐ Clinical decision support

I understand:
- My notes will be analyzed by AI to extract medical concepts
- Data will be stored securely and accessed only by authorized personnel
- I can withdraw consent at any time by contacting [email]
- Withdrawal will not affect my care

Signature: _______________  Date: _______________
```

---

### Data Subject Rights

| Right | Implementation |
|-------|----------------|
| Right to Access | Provide all PHI held about individual |
| Right to Rectification | Allow correction of inaccurate data |
| Right to Erasure | Delete data upon request (with exceptions) |
| Right to Restrict Processing | Temporarily halt processing |
| Right to Data Portability | Export data in machine-readable format |
| Right to Object | Stop processing for specific purposes |

**Right to Erasure Implementation**:

```python
@app.delete("/api/v1/patients/{patient_id}/data")
async def delete_patient_data(
    patient_id: str,
    user: User = Depends(require_role(Role.ADMIN))
):
    # Check if deletion is permitted
    if has_legal_hold(patient_id):
        raise HTTPException(400, "Cannot delete: legal hold active")

    # Delete from all systems
    elasticsearch.delete_by_query(index="patients", patient_id=patient_id)
    db.delete_patient(patient_id)
    audit_logs.anonymize_patient_id(patient_id)  # Retain audit trail but anonymize

    audit_logger.info(f"Patient {patient_id} data deleted per GDPR request")
    return {"status": "deleted"}
```

---

### Data Protection Impact Assessment (DPIA)

**When Required**: High-risk processing (e.g., large-scale processing of health data).

**Template**:

```markdown
## Data Protection Impact Assessment (DPIA)

**Project**: CogStack NLP Deployment
**Date**: 2024-01-15
**Assessor**: Data Protection Officer

### 1. Nature of Processing
- **Data Types**: Clinical notes, diagnoses, medications, lab results
- **Volume**: 1,000,000+ patient records
- **Sensitivity**: Special category data (health)

### 2. Necessity and Proportionality
- **Purpose**: Improve patient care through NLP-assisted clinical decision support
- **Necessity**: Manual review is not feasible at scale
- **Proportionality**: De-identification applied where possible

### 3. Risks to Data Subjects

| Risk | Likelihood | Severity | Mitigation |
|------|-----------|----------|------------|
| Unauthorized access | Low | High | RBAC, MFA, encryption |
| Re-identification | Low | High | Expert de-identification review |
| Data breach | Low | High | Incident response plan, insurance |

### 4. Compliance Measures
- ☑ Encryption (TLS 1.3, AES-256)
- ☑ Access controls (RBAC)
- ☑ Audit logging
- ☑ Data retention policies (7 years)
- ☑ Breach notification procedures (<72 hours)

### 5. Approval
- DPO Approval: _______________
- CISO Approval: _______________
```

---

## 21 CFR Part 11 (Clinical Trials)

**Applicability**: If CogStack NLP is used to process clinical trial data.

### Key Requirements

| Requirement | Implementation |
|-------------|----------------|
| Electronic Signatures | Cryptographically signed audit logs |
| Audit Trails | Immutable, timestamped logs of all changes |
| System Validation | Documented testing and validation |
| Data Integrity | Checksums, backups, disaster recovery |

**Audit Trail Requirements**:

```python
import cryptography
from datetime import datetime

class AuditLog:
    def log_action(self, user_id, action, details):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "details": details,
            "signature": self._sign(user_id, action, details)
        }
        self.store(entry)

    def _sign(self, user_id, action, details):
        # Cryptographic signature for tamper-proof audit trail
        data = f"{user_id}|{action}|{details}".encode()
        return hmac.new(secret_key, data, hashlib.sha256).hexdigest()
```

---

## Data Governance Requirements

### Data Retention Policy

| Data Type | Retention Period | Rationale |
|-----------|------------------|-----------|
| Clinical Notes (Original) | 7 years | Medical-legal requirement |
| NLP Annotations | 7 years | Same as source documents |
| Audit Logs | 6 years | HIPAA requirement |
| De-identified Research Data | 10 years | Research reproducibility |
| User Access Logs | 3 years | Security analysis |

**Automated Deletion Script**:

```python
from datetime import datetime, timedelta

def purge_old_audit_logs():
    cutoff_date = datetime.now() - timedelta(days=6*365)  # 6 years
    db.audit_logs.delete_many({"timestamp": {"$lt": cutoff_date}})
    logger.info(f"Purged audit logs older than {cutoff_date}")

# Schedule monthly
schedule.every().month.at("02:00").do(purge_old_audit_logs)
```

---

### Data Classification

| Classification | Description | Examples | Controls |
|----------------|-------------|----------|----------|
| Public | No PHI/PII | Aggregated statistics | None required |
| Internal | De-identified data | Research datasets | Access control |
| Confidential | PHI/PII | Patient notes | Encryption, RBAC, audit |
| Restricted | Sensitive PHI | HIV status, mental health | MFA, need-to-know basis |

---

## Technical Controls

### Encryption

**At Rest**:
```bash
# Database encryption (PostgreSQL)
ALTER DATABASE cogstack_nlp SET encryption = on;

# Elasticsearch encryption
xpack.security.encryption.enabled: true
```

**In Transit**:
```yaml
# docker-compose.yml
services:
  api:
    environment:
      - FORCE_HTTPS=true
      - TLS_VERSION=1.3
```

---

### Access Control Matrix

| Role | Patient Search | View Document | Export Data | Admin Functions |
|------|---------------|---------------|-------------|-----------------|
| Clinician | ✓ | ✓ | ✗ | ✗ |
| Researcher | ✓ (de-ID) | ✓ (de-ID) | ✓ (de-ID) | ✗ |
| Admin | ✓ | ✓ | ✓ | ✓ |
| Auditor | ✗ | ✗ | ✗ | ✓ (logs only) |

---

## Compliance Checklist

### Pre-Deployment

- [ ] Risk assessment completed and documented
- [ ] DPIA completed (GDPR)
- [ ] Business Associate Agreements (BAAs) signed with cloud providers
- [ ] Encryption enabled (at rest and in transit)
- [ ] Access controls configured (RBAC)
- [ ] Audit logging enabled
- [ ] Training completed for all users
- [ ] Policies and procedures documented

### Post-Deployment

- [ ] Monthly audit log reviews
- [ ] Quarterly access reviews (remove unnecessary access)
- [ ] Annual risk assessments
- [ ] Annual HIPAA training
- [ ] Incident response drills (annually)
- [ ] Penetration testing (annually)

---

## Documentation Templates

All compliance documentation templates are available in `/docs/compliance/templates/`:

- `risk-assessment-template.md`
- `dpia-template.md`
- `consent-form-template.md`
- `baa-template.md`
- `incident-response-plan-template.md`

---

**Questions?** Contact your organization's Compliance Officer or Data Protection Officer.

**Related Resources**:
- [HHS HIPAA Resources](https://www.hhs.gov/hipaa)
- [ICO GDPR Guidance](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/)
- [FDA 21 CFR Part 11](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application)
