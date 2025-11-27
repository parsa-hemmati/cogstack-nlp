# Encryption Key Management Guide

## Overview

This document outlines the procedures for managing the `ENCRYPTION_KEY` used to encrypt Protected Health Information (PHI) at rest in the Clinical Care Tools application.

**CRITICAL**: The encryption key is required for HIPAA/GDPR compliance. Loss of this key results in **permanent, irrecoverable loss** of all encrypted PHI data.

## Key Specifications

| Property | Value |
|----------|-------|
| Algorithm | AES-256-GCM |
| Key Length | 256 bits (32 bytes) |
| Encoding | Base64 |
| Storage | Environment variable |

## Key Generation

### Production Environment

Generate a cryptographically secure key:

```bash
# Linux/macOS
openssl rand -base64 32

# Windows (PowerShell)
[Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))

# Python
python -c "import secrets; import base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

### Development Environment

For local development only (NOT production):

```bash
# Generate a development key (mark it clearly)
echo "DEV_ONLY_$(openssl rand -base64 32)"
```

## Key Storage

### Environment Variables

Store the key in `.env` file (never committed to git):

```bash
# .env
ENCRYPTION_KEY=your-generated-key-here
```

### Production Recommendations

For production deployments, use one of these secure storage methods:

1. **Secrets Manager** (Recommended)
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault
   - GCP Secret Manager

2. **Environment Injection**
   - Kubernetes Secrets
   - Docker Swarm Secrets
   - CI/CD environment variables

3. **Hardware Security Module (HSM)**
   - For high-security healthcare environments
   - Required for some compliance frameworks

## Key Backup Procedures

### Backup Strategy

1. **Primary Storage**: Production secrets manager
2. **Secondary Backup**: Encrypted offline backup
3. **Recovery Documentation**: Printed recovery procedure in secure location

### Creating Encrypted Backup

```bash
# Encrypt the key for offline storage
echo "ENCRYPTION_KEY=your-key-here" | gpg --symmetric --cipher-algo AES256 > encryption_key_backup.gpg

# Store the GPG passphrase separately from the backup
```

### Backup Verification

Monthly verification procedure:

1. Decrypt backup file
2. Verify key matches production
3. Test decryption of sample PHI record
4. Document verification in audit log

## Key Rotation

### Rotation Schedule

| Environment | Rotation Frequency |
|-------------|-------------------|
| Development | Not required |
| Staging | Quarterly |
| Production | Annually (or upon compromise) |

### Rotation Procedure

**WARNING**: Key rotation requires re-encryption of ALL PHI data. Plan for downtime.

1. **Generate new key**
   ```bash
   NEW_KEY=$(openssl rand -base64 32)
   ```

2. **Stop application** to prevent new writes

3. **Run re-encryption migration**
   ```bash
   # This script re-encrypts all PHI with the new key
   python scripts/rotate_encryption_key.py \
     --old-key "$OLD_ENCRYPTION_KEY" \
     --new-key "$NEW_KEY" \
     --verify
   ```

4. **Update environment variable** with new key

5. **Restart application**

6. **Verify** decryption works with new key

7. **Archive old key** securely (required for audit trail)

8. **Update backups** with new key

## Emergency Procedures

### Key Compromise Response

If you suspect the encryption key has been compromised:

1. **Immediately** notify security team
2. **Generate new key** using procedure above
3. **Rotate key** following rotation procedure
4. **Audit** all PHI access during potential exposure window
5. **Report** per HIPAA breach notification requirements (if applicable)
6. **Document** incident for compliance records

### Key Recovery

If the encryption key is lost:

1. **Check backups** (encrypted offline backup)
2. **Check secrets manager** history/versions
3. **Contact security team** for recovery procedures

**If key cannot be recovered**: Encrypted PHI data is permanently lost. This is a reportable HIPAA incident.

## Compliance Requirements

### HIPAA

- Encryption key must be stored separately from encrypted data
- Key access must be logged
- Key rotation must be documented
- Backup procedures must be tested annually

### GDPR

- Encryption key must be protected as personal data
- Key access limited to authorized personnel only
- Destruction procedures must ensure complete key removal

### Audit Logging

All key operations are logged:

```json
{
  "event": "encryption_key_access",
  "timestamp": "2025-01-15T10:30:00Z",
  "user_id": "admin-user-uuid",
  "operation": "decrypt_phi",
  "resource_type": "patient_document",
  "resource_id": "doc-uuid",
  "client_ip": "10.0.0.1"
}
```

## Development vs Production

| Aspect | Development | Production |
|--------|-------------|------------|
| Key Storage | `.env` file | Secrets manager |
| Key Rotation | Not required | Annual |
| Backups | Optional | Required (encrypted) |
| Access Logging | Optional | Required |
| HSM | No | Recommended |

## Security Checklist

Before deploying to production:

- [ ] Key generated with cryptographic RNG
- [ ] Key stored in secrets manager (not `.env`)
- [ ] Backup created and tested
- [ ] Recovery procedure documented
- [ ] Access logging enabled
- [ ] Rotation schedule documented
- [ ] Team trained on procedures

## Related Documentation

- [Healthcare Compliance Framework](../compliance/healthcare-compliance-framework.md)
- [HIPAA Audit Logging](../compliance/hipaa-audit-logging.md)
- [Incident Response Plan](./incident-response.md)
