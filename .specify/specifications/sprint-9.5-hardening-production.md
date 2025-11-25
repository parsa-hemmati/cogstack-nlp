# Specification: Hardening & Production Readiness (Sprint 9.5)

**Version**: 1.0.0
**Date**: 2025-11-25
**Status**: Planned
**Author**: AI Assistant (Claude Code)
**Reviewers**: [To be assigned]
**Sprint Duration**: 4 weeks (~120 hours)
**Dependencies**: Sprints 1-9

**Version History**:
- **1.0.0** (2025-11-25): Initial specification extracted from technical plan

---

## Table of Contents

1. [Context](#context)
2. [Goals](#goals)
3. [Non-Goals](#non-goals)
4. [User Stories](#user-stories)
5. [Requirements](#requirements)
6. [Architecture](#architecture)
7. [Security Hardening](#security-hardening)
8. [Performance Optimization](#performance-optimization)
9. [Monitoring & Observability](#monitoring--observability)
10. [Backup & Recovery](#backup--recovery)
11. [Compliance Validation](#compliance-validation)
12. [Constraints](#constraints)
13. [Acceptance Criteria](#acceptance-criteria)
14. [Alignment with Constitution](#alignment-with-constitution)
15. [Testing Strategy](#testing-strategy)
16. [Open Questions](#open-questions)

---

## Context

### Background

Sprint 9.5 is the **final hardening sprint** before production deployment. It focuses on security, performance, monitoring, backup/recovery, documentation, and compliance validation.

**CogStack Product Alignment**: Enterprise Infrastructure (Production Readiness)

### The Problem

Before production deployment, the system requires:
- **Security hardening** (penetration testing, vulnerability scanning)
- **Performance optimization** (load testing, query tuning)
- **Monitoring infrastructure** (metrics, alerting, logging)
- **Backup & recovery** (disaster recovery planning)
- **Compliance validation** (HIPAA, GDPR, NHS DSPT)

### Solution

Comprehensive hardening sprint that:
1. Validates security through penetration testing
2. Optimizes performance for production load
3. Establishes monitoring and alerting
4. Implements backup and disaster recovery
5. Validates regulatory compliance

### Business Value

- **Risk Mitigation**: Security vulnerabilities identified and fixed
- **Reliability**: Monitoring ensures issues detected early
- **Compliance**: Regulatory requirements validated
- **Recoverability**: Backups ensure data protection
- **Documentation**: Operations team can maintain system

---

## Goals

### Primary Goals

1. **Security Hardening** (P0)
   - Penetration testing by external security firm
   - Vulnerability scanning (Snyk, OWASP ZAP)
   - HTTPS enforcement (TLS 1.3 only)
   - Rate limiting on API endpoints
   - Security headers (CSP, HSTS, X-Frame-Options)

2. **Performance Optimization** (P0)
   - Database query optimization
   - Redis caching tuning
   - Load testing (100 concurrent users)
   - API response time < 1 second (p95)

3. **Monitoring & Observability** (P0)
   - Prometheus metrics collection
   - Grafana dashboards
   - Log aggregation (ELK or Loki)
   - Alerting rules configured

4. **Backup & Recovery** (P0)
   - Automated daily backups
   - Recovery tested monthly
   - RPO < 24 hours, RTO < 4 hours
   - Disaster recovery plan documented

5. **Compliance Validation** (P0)
   - HIPAA compliance checklist completed
   - GDPR compliance validated
   - NHS DSPT assertion ready
   - Clinical safety review (if applicable)

### Secondary Goals

- OpenTelemetry distributed tracing
- Chaos engineering (failure injection testing)
- Blue/green deployment capability

---

## Non-Goals

- **Feature development** (no new features in hardening sprint)
- **Major refactoring** (stability focus)
- **Multi-site deployment** (single site for MVP)
- **Full SOC 2 certification** (future sprint)

---

## User Stories

### US-9.5.1: Security Audit (P0)

**As a** security officer
**I want** the system to pass penetration testing
**So that** I can be confident in production deployment

**Acceptance Criteria**:
- External penetration test completed
- All critical/high vulnerabilities remediated
- Security audit report available
- No known SQL injection or XSS vulnerabilities

### US-9.5.2: Performance Under Load (P0)

**As an** administrator
**I want** the system to handle 100 concurrent users
**So that** the department can use it during peak hours

**Acceptance Criteria**:
- Load test with 100 concurrent users passed
- API response time < 1 second (p95)
- No errors under load
- Dashboard loads in < 3 seconds

### US-9.5.3: System Monitoring (P0)

**As an** operations team member
**I want** dashboards showing system health
**So that** I can identify issues before they impact users

**Acceptance Criteria**:
- Grafana dashboards for API, database, cache health
- Alerts configured for error rate > 5%
- Alerts configured for disk > 85%
- Log aggregation operational

### US-9.5.4: Data Recovery (P0)

**As a** data protection officer
**I want** automated backups with tested recovery
**So that** we can recover from data loss incidents

**Acceptance Criteria**:
- Daily automated backups configured
- Recovery tested and documented
- RPO < 24 hours achieved
- RTO < 4 hours demonstrated

### US-9.5.5: Compliance Certification (P0)

**As a** compliance officer
**I want** documented evidence of HIPAA/GDPR compliance
**So that** we can demonstrate regulatory adherence

**Acceptance Criteria**:
- HIPAA compliance checklist completed
- GDPR compliance evidence documented
- NHS DSPT assertion prepared
- Audit logging verified for all PHI access

---

## Requirements

### Functional Requirements

#### FR-1: Security Controls

| Control | Requirement |
|---------|-------------|
| HTTPS | TLS 1.3 only, HTTP redirects to HTTPS |
| Rate Limiting | 100 requests/minute per user |
| Authentication | JWT with 1-hour expiry |
| Authorization | RBAC enforced on all endpoints |
| Audit Logging | All PHI access logged |
| Input Validation | Parameterized queries, XSS sanitization |
| Security Headers | CSP, HSTS, X-Frame-Options, X-Content-Type-Options |

#### FR-2: Performance Targets

| Metric | Target |
|--------|--------|
| API Response (p95) | < 1 second |
| Dashboard Load | < 3 seconds |
| Search Response | < 500ms |
| Concurrent Users | 100 |
| Requests/Minute | 1000 |

#### FR-3: Monitoring Requirements

| System | Metrics |
|--------|---------|
| API | Request rate, latency (p50/p95/p99), error rate |
| Database | Connection pool, query duration, deadlocks |
| Elasticsearch | Index size, query latency, cluster health |
| Redis | Memory usage, cache hit rate, connections |
| System | CPU, memory, disk, network |

#### FR-4: Backup Requirements

| Component | Backup Frequency | Retention |
|-----------|-----------------|-----------|
| PostgreSQL | Daily full + continuous WAL | 30 days |
| Elasticsearch | Daily snapshots | 30 days |
| Redis | Every 6 hours (RDB) + AOF | 7 days |
| Application Logs | Continuous | 90 days |

### Non-Functional Requirements

#### NFR-1: Availability

- **Target**: 99.9% uptime (excluding planned maintenance)
- **Planned Maintenance**: Monthly, < 2 hours
- **Unplanned Downtime**: < 4 hours per incident

#### NFR-2: Recovery

- **RPO (Recovery Point Objective)**: < 24 hours
- **RTO (Recovery Time Objective)**: < 4 hours
- **Monthly Recovery Drill**: Required

#### NFR-3: Compliance

- **HIPAA**: Administrative, Physical, Technical safeguards
- **GDPR**: Data subject rights, breach notification
- **NHS DSPT**: Annual assertion, audit log review

---

## Security Hardening

### Penetration Testing Scope

| Area | Tests |
|------|-------|
| Network | Port scanning, firewall rules |
| Application | OWASP Top 10 (injection, XSS, CSRF) |
| Authentication | Brute force, session management |
| Authorization | Privilege escalation, IDOR |
| Data | Encryption at rest/transit, PHI exposure |

### Vulnerability Remediation

| Severity | SLA |
|----------|-----|
| Critical | 24 hours |
| High | 72 hours |
| Medium | 7 days |
| Low | 30 days |

### Security Checklist

- [ ] Penetration testing completed
- [ ] All critical/high vulnerabilities fixed
- [ ] HTTPS enforced (no HTTP)
- [ ] TLS 1.3 only (no TLS 1.2)
- [ ] Rate limiting configured
- [ ] Security headers enabled
- [ ] CORS policy restrictive
- [ ] Secrets in environment variables (not code)
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified
- [ ] CSRF protection enabled
- [ ] Session management secure

---

## Performance Optimization

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_annotations_patient_id ON annotations(patient_id);
CREATE INDEX idx_annotations_cui ON annotations(cui);
CREATE INDEX idx_documents_patient_id ON documents(patient_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(created_at);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM patients WHERE id = $1;
```

### Caching Strategy

| Cache | TTL | Invalidation |
|-------|-----|--------------|
| Patient details | 5 min | On update event |
| Search results | 5 min | On document index |
| User session | 1 hour | On logout |
| Static assets | 1 day | On deployment |

### Load Testing

```yaml
# Locust test configuration
users: 100
spawn_rate: 10
duration: 10m
scenarios:
  - name: Search patients
    weight: 50
    endpoint: POST /api/v1/patients/search
  - name: Get timeline
    weight: 30
    endpoint: GET /api/v1/patients/{id}/timeline
  - name: Export FHIR
    weight: 20
    endpoint: GET /api/v1/fhir/export/{id}
```

---

## Monitoring & Observability

### Prometheus Metrics

```python
# API metrics
api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint', 'status']
)

api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

# Database metrics
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)
```

### Grafana Dashboards

| Dashboard | Panels |
|-----------|--------|
| API Health | Request rate, latency heatmap, error rate |
| Database | Connections, query duration, deadlocks |
| Elasticsearch | Cluster health, index size, query latency |
| Redis | Memory, hit rate, evictions |
| System | CPU, memory, disk, network |

### Alerting Rules

```yaml
groups:
  - name: api-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(api_requests_total{status=~"5.."}[5m]) / rate(api_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High API error rate (> 5%)

      - alert: SlowResponses
        expr: histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: 95th percentile response time > 1 second

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.15
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: Disk space below 15%
```

---

## Backup & Recovery

### Backup Configuration

#### PostgreSQL

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump -Fc cogstack_nlp > /backups/postgres/cogstack_nlp_${DATE}.dump

# WAL archiving (postgresql.conf)
archive_mode = on
archive_command = 'cp %p /backups/postgres/wal/%f'
```

#### Elasticsearch

```json
// Snapshot repository
PUT /_snapshot/backup_repo
{
  "type": "fs",
  "settings": {
    "location": "/backups/elasticsearch"
  }
}

// Daily snapshot policy
PUT /_slm/policy/daily-snapshots
{
  "schedule": "0 30 1 * * ?",
  "name": "<daily-snap-{now/d}>",
  "repository": "backup_repo",
  "config": {
    "indices": ["patients", "documents", "annotations"]
  },
  "retention": {
    "expire_after": "30d"
  }
}
```

### Recovery Procedures

1. **PostgreSQL Recovery**
   ```bash
   pg_restore -d cogstack_nlp /backups/postgres/cogstack_nlp_20251125.dump
   ```

2. **Elasticsearch Recovery**
   ```bash
   POST /_snapshot/backup_repo/daily-snap-2025.11.25/_restore
   {
     "indices": "patients,documents,annotations"
   }
   ```

3. **Redis Recovery**
   ```bash
   redis-cli CONFIG SET dir /backups/redis
   redis-cli CONFIG SET dbfilename dump.rdb
   redis-cli DEBUG RELOAD
   ```

---

## Compliance Validation

### HIPAA Checklist

| Control | Status |
|---------|--------|
| Audit logging for PHI access | ☐ |
| Encryption at rest (AES-256) | ☐ |
| Encryption in transit (TLS 1.3) | ☐ |
| Access control (RBAC) | ☐ |
| Automatic session timeout | ☐ |
| Unique user identification | ☐ |
| Emergency access procedures | ☐ |
| Data backup and recovery | ☐ |
| Password complexity requirements | ☐ |
| Audit log review procedures | ☐ |

### GDPR Checklist

| Requirement | Status |
|-------------|--------|
| Data processing agreement | ☐ |
| Right to access (data export) | ☐ |
| Right to erasure (data deletion) | ☐ |
| Breach notification procedure | ☐ |
| Data protection impact assessment | ☐ |
| Privacy by design implemented | ☐ |
| Consent management | ☐ |

### NHS DSPT Checklist

| Standard | Status |
|----------|--------|
| Leadership & governance | ☐ |
| Confidential data security | ☐ |
| Staff responsibilities | ☐ |
| Training | ☐ |
| Managing data access | ☐ |
| Process reviews | ☐ |
| Responding to incidents | ☐ |
| Business continuity | ☐ |

---

## Constraints

### Technical Constraints

- Must maintain backward compatibility with existing APIs
- No database schema changes that require migration downtime
- Monitoring infrastructure must not impact application performance

### Operational Constraints

- Penetration testing requires external vendor coordination
- Compliance validation requires input from legal/compliance team
- Recovery testing requires scheduled downtime window

### Resource Constraints

- 4-week sprint duration
- Single security engineer for remediation
- Limited budget for external pen testing

---

## Acceptance Criteria

### Security Acceptance

- [ ] Penetration testing completed by external firm
- [ ] All critical vulnerabilities remediated
- [ ] All high vulnerabilities remediated
- [ ] Security audit report signed off
- [ ] HTTPS enforced, no HTTP endpoints

### Performance Acceptance

- [ ] Load test passed (100 concurrent users)
- [ ] API response time < 1 second (p95)
- [ ] Dashboard load time < 3 seconds
- [ ] Search response time < 500ms
- [ ] No errors under load

### Monitoring Acceptance

- [ ] Prometheus metrics collecting
- [ ] Grafana dashboards operational
- [ ] Log aggregation working
- [ ] Alerts configured and tested
- [ ] On-call rotation documented

### Backup Acceptance

- [ ] Automated backups configured
- [ ] Recovery procedure documented
- [ ] Recovery tested successfully
- [ ] RPO < 24 hours verified
- [ ] RTO < 4 hours verified

### Compliance Acceptance

- [ ] HIPAA checklist completed
- [ ] GDPR checklist completed
- [ ] NHS DSPT assertion ready
- [ ] Audit logging verified
- [ ] Encryption verified

### Documentation Acceptance

- [ ] User guide complete
- [ ] Admin guide complete
- [ ] API documentation complete
- [ ] Runbooks documented
- [ ] Architecture diagrams updated

---

## Alignment with Constitution

| Principle | How This Sprint Addresses It |
|-----------|------------------------------|
| Patient Safety First | Security hardening protects patient data |
| Privacy by Design | Compliance validation ensures privacy |
| Evidence-Based Development | Monitoring provides operational evidence |
| Performance | Load testing validates performance |
| Continuous Improvement | Monitoring enables continuous improvement |

---

## Testing Strategy

### Security Testing

- External penetration testing
- OWASP ZAP automated scanning
- Snyk vulnerability scanning
- Manual security review

### Performance Testing

- Load testing (Locust/JMeter)
- Stress testing (beyond 100 users)
- Endurance testing (24-hour run)
- Database query profiling

### Disaster Recovery Testing

- Monthly recovery drill
- Failover testing
- Backup restoration verification
- Data integrity validation

### Compliance Testing

- Audit log verification
- Encryption validation
- Access control testing
- Data export/deletion testing

---

## Open Questions

1. **Penetration testing vendor**: Which security firm to engage?
   - Proposed: Get 3 quotes, select based on healthcare experience

2. **Monitoring retention**: How long to retain metrics data?
   - Proposed: 90 days for detailed, 1 year for aggregated

3. **Compliance scope**: Is DCB0129/DCB0160 clinical safety required?
   - Proposed: Consult with NHS clinical safety officer

---

## References

- Technical Plan: `.specify/plans/sprint-9.5-hardening-production-plan.md`
- Tasks: `.specify/tasks/sprint-9.5-hardening-production-tasks.md`
- HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/
- GDPR: https://gdpr.eu/
- NHS DSPT: https://www.dsptoolkit.nhs.uk/
