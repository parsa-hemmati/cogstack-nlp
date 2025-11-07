---
name: healthcare-compliance-checker
description: Reviews code changes for HIPAA, GDPR, and 21 CFR Part 11 compliance in healthcare applications. Use when implementing features that access patient data (PHI/PII), modify authentication or authorization, add API endpoints, create database schemas, handle clinical documents, or add logging. Checks for audit logging, encryption, access controls, data handling patterns, and PHI exposure risks.
---

# Healthcare Compliance Checker

Ensures code changes comply with HIPAA Security Rule, GDPR, UK GDPR, and 21 CFR Part 11 regulations for healthcare applications.

## When to use this skill

Invoke automatically when:
- Implementing features that access patient health information (PHI) or personally identifiable information (PII)
- Adding or modifying database schemas containing patient data
- Creating API endpoints that expose clinical data
- Implementing authentication or authorization systems
- Adding logging, error handling, or debugging code
- Working with clinical documents, medical records, or healthcare data

## Quick compliance checklist

Copy this checklist for every code change involving patient data:

```
Compliance Review:
- [ ] No PHI/PII in application logs
- [ ] Audit logging for all PHI access
- [ ] Encryption in transit (TLS 1.3)
- [ ] Encryption at rest (AES-256 or equivalent)
- [ ] Role-based access control (RBAC) enforced
- [ ] Minimum necessary access principle
- [ ] Proper error messages (no PHI leakage)
- [ ] Session timeouts configured
- [ ] Input validation and sanitization
- [ ] SQL injection prevention (parameterized queries)
```

## Critical violations to catch

### 1. PHI in application logs

**VIOLATION** (never do this):
```python
logger.info(f"Processing patient {patient_name} (MRN: {mrn})")
logger.debug(f"Patient DOB: {date_of_birth}")
print(f"Error processing record for {patient.email}")
```

**COMPLIANT**:
```python
logger.info(f"Processing patient {patient_id}")  # ID only, no PII
audit_logger.info({  # PHI goes to audit logs only
    "user_id": user_id,
    "action": "VIEW_PATIENT",
    "patient_id": patient_id,
    "timestamp": datetime.utcnow().isoformat(),
    "ip_address": request.client.host
})
```

**Search patterns**: Check for these in logs:
- Patient names, dates of birth, addresses
- Medical Record Numbers (MRNs)
- Email addresses, phone numbers
- Social Security Numbers
- Diagnosis codes or clinical details

### 2. Missing audit trails

**VIOLATION**:
```python
def get_patient_data(patient_id: str):
    return db.query(Patient).filter_by(id=patient_id).first()
```

**COMPLIANT**:
```python
def get_patient_data(
    patient_id: str,
    user: User = Depends(get_current_user)
):
    # Log EVERY access to PHI
    audit_log(
        user_id=user.id,
        action="VIEW_PATIENT",
        resource_type="Patient",
        resource_id=patient_id,
        ip_address=request.client.host,
        timestamp=datetime.utcnow()
    )
    return db.query(Patient).filter_by(id=patient_id).first()
```

**Required audit fields**:
- WHO: user_id, username, role
- WHAT: action (VIEW, CREATE, UPDATE, DELETE, EXPORT)
- WHEN: timestamp (UTC, ISO 8601 format)
- WHERE: ip_address, endpoint
- WHICH: resource_type, resource_id

### 3. Insufficient encryption

**Check for**:
- Database connections using TLS 1.3
- API endpoints using HTTPS only (no HTTP fallback)
- At-rest encryption for PHI columns
- Encrypted backups
- Secure key management (not hardcoded)

**Database connection example (PostgreSQL)**:
```python
# COMPLIANT
DATABASE_URL = "postgresql://user:pass@host:5432/db?sslmode=require&sslrootcert=ca.pem"
```

### 4. Weak access controls

**VIOLATION**:
```python
@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: str):
    return get_patient_data(patient_id)  # No auth check!
```

**COMPLIANT**:
```python
@app.get("/api/patients/{patient_id}")
async def get_patient(
    patient_id: str,
    user: User = Depends(get_current_user),  # Authenticate
    _: None = Depends(require_role("clinician"))  # Authorize
):
    # Additional check: Can this user access THIS patient?
    if not user.can_access_patient(patient_id):
        raise HTTPException(403, "Access denied")

    return get_patient_data(patient_id, user)
```

## Compliance review workflow

Follow these steps for every code change involving patient data:

1. **Identify PHI touchpoints**
   - Which functions access patient data?
   - Which API endpoints expose PHI?
   - Which database queries return patient records?

2. **Review logging statements**
   - Run: `grep -r "logger\\.info\\|logger\\.debug\\|print" [changed_files]`
   - Check each log statement for PHI
   - Verify audit logging is present

3. **Verify encryption**
   - Database: TLS 1.3 required
   - API: HTTPS only
   - At-rest: Encrypted columns for PHI

4. **Check access controls**
   - Authentication required (JWT, OAuth, etc.)
   - Authorization enforced (RBAC)
   - Minimum necessary access

5. **Validate input handling**
   - Parameterized SQL queries (no string concatenation)
   - Input sanitization
   - Output encoding

6. **Review error messages**
   - No PHI in error responses
   - Generic messages to users
   - Detailed errors to audit logs only

## Reference materials

**Comprehensive compliance framework**: See [docs/compliance/healthcare-compliance-framework.md](../../docs/compliance/healthcare-compliance-framework.md)

**HIPAA Security Rule**: Administrative, physical, and technical safeguards detailed in compliance framework

**GDPR Requirements**: Data subject rights, consent management, breach notification in compliance framework

**Common PHI identifiers** (18 types under HIPAA):
1. Names
2. Geographic subdivisions smaller than state
3. Dates (except year) related to individual
4. Phone numbers
5. Fax numbers
6. Email addresses
7. Social Security Numbers
8. Medical Record Numbers
9. Health Plan Beneficiary Numbers
10. Account numbers
11. Certificate/license numbers
12. Vehicle identifiers
13. Device identifiers and serial numbers
14. URLs
15. IP addresses
16. Biometric identifiers
17. Full-face photos
18. Any other unique identifying number/code

## Quick fixes for common violations

### Fix 1: Remove PHI from logs

Search and replace:
```bash
# Find potential violations
grep -rn "logger.*patient.*name\|logger.*mrn\|logger.*dob" .

# Pattern to fix
# BEFORE: logger.info(f"Patient: {patient.name}")
# AFTER:  logger.info(f"Patient ID: {patient.id}")
```

### Fix 2: Add audit logging

Template:
```python
def audit_log(user_id, action, resource_type, resource_id, ip_address):
    """Log to dedicated audit trail (separate from application logs)"""
    AuditLog.create({
        "user_id": user_id,
        "action": action,  # VIEW, CREATE, UPDATE, DELETE, EXPORT
        "resource_type": resource_type,  # Patient, Document, etc.
        "resource_id": resource_id,
        "ip_address": ip_address,
        "timestamp": datetime.utcnow(),
        "success": True  # Log failures too!
    })
```

### Fix 3: Add authentication dependency

FastAPI example:
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    user = verify_token(token)  # Implement token verification
    if not user:
        raise HTTPException(401, "Invalid credentials")
    return user

# Use in routes:
@app.get("/api/patients")
async def list_patients(user: User = Depends(get_current_user)):
    # user is authenticated
    pass
```

## Validation scripts

No executable scripts bundled (compliance checks are context-dependent). Use grep and manual review following the workflow above.

## Integration with existing workflow

This skill automatically activates when:
- Code changes involve `Patient`, `Document`, `User`, `Auth` models
- API routes contain `/patients/`, `/documents/`, `/clinical/`
- Database migrations add PHI-containing columns
- Logging statements are added or modified

Works alongside:
- `spec-kit-enforcer` skill (ensures specification includes compliance requirements)
- `vue3-component-reuse` skill (frontend components may display PHI)

## Key principles

1. **Default deny**: Assume all patient data requires protection unless proven otherwise
2. **Audit everything**: Every PHI access must be logged
3. **Encrypt always**: TLS 1.3 in transit, AES-256 at rest
4. **Minimum necessary**: Users get only the access they need for their role
5. **Fail securely**: Errors should not expose PHI

## Common questions

**Q: Is patient ID considered PHI?**
A: Depends. If the ID can be used to identify the patient (like MRN), yes. If it's an internal UUID with no external mapping, it's safer but still treat carefully.

**Q: Can I log PHI for debugging?**
A: Only to dedicated, encrypted audit logs. Never to application logs, console, or error tracking services.

**Q: What about test data?**
A: Use synthetic data only. Never use real patient data for testing, even with names changed.

**Q: How long must audit logs be retained?**
A: HIPAA: 6 years. GDPR: Varies by purpose. See compliance framework for details.

## When in doubt

If unsure whether something is compliant, ask the user to:
1. Consult the compliance framework documentation
2. Review with their security/compliance team
3. Follow the strictest interpretation (default deny)

Never compromise patient privacy for convenience.
