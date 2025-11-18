# Tasks: Hardening & Production Readiness (Sprint 9.5)

**Plan Reference**: `.specify/plans/sprint-9.5-hardening-production-plan.md` (v1.0.0)
**Specification Reference**: `.specify/specifications/sprint-9.5-hardening-production.md` (v1.0.0)
**Estimated Total Time**: 120 hours (4 weeks)
**Dependencies**:
- Sprints 1-9 completed
- All features tested and validated
- Production environment provisioned

---

## Phase 9.5.1: Security Hardening (30 hours)

### Task 9.5.1.1: Penetration Testing (External Firm)
**Goal**: Professional penetration test of application
**Phase**: 9.5.1 | **Dependencies**: None | **Time**: 16h (2 days testing + 1 day report review)
**Steps**: 1) Engage external security firm, 2) Conduct pen test, 3) Review findings, 4) Prioritize remediation
**Acceptance**: Pen test completed, critical vulnerabilities identified
**Files**: `docs/security/penetration-test-report-YYYY-MM-DD.pdf`

### Task 9.5.1.2: Vulnerability Scanning (Snyk, OWASP ZAP)
**Goal**: Automated vulnerability scanning
**Phase**: 9.5.1 | **Dependencies**: None | **Time**: 4h
**Steps**: 1) Run Snyk scan on backend dependencies, 2) Run OWASP ZAP on frontend, 3) Fix critical/high vulnerabilities
**Acceptance**: No critical/high vulnerabilities
**Files**: `docs/security/vulnerability-scan-report.md`

### Task 9.5.1.3: HTTPS Enforcement (TLS 1.3 Only)
**Goal**: Enforce HTTPS, disable HTTP
**Phase**: 9.5.1 | **Dependencies**: None | **Time**: 2h
**Steps**: 1) Configure Nginx to redirect HTTP → HTTPS, 2) Set TLS minimum version to 1.3, 3) Disable weak ciphers
**Acceptance**: Only HTTPS connections accepted, TLS 1.3 enforced
**Files**: `nginx/nginx.conf` (updated)

### Task 9.5.1.4: Rate Limiting on API Endpoints
**Goal**: Prevent abuse with rate limiting
**Phase**: 9.5.1 | **Dependencies**: None | **Time**: 3h
**Steps**: 1) Install slowapi or similar, 2) Configure rate limits (100 requests/minute per IP), 3) Return 429 on limit exceeded
**Acceptance**: Rate limiting works, attacks prevented
**Files**: `backend/app/middleware/rate_limiter.py`

### Task 9.5.1.5: SQL Injection Prevention Audit
**Goal**: Audit all database queries for SQL injection
**Phase**: 9.5.1 | **Dependencies**: None | **Time**: 2h
**Steps**: 1) Review all SQL queries, 2) Verify parameterized queries used, 3) Fix any string concatenation
**Acceptance**: All queries use parameterized statements, no SQL injection risks
**Files**: Code review report

### Task 9.5.1.6: XSS Prevention Audit
**Goal**: Audit frontend for XSS vulnerabilities
**Phase**: 9.5.1 | **Dependencies**: None | **Time**: 2h
**Steps**: 1) Review all v-html usage, 2) Ensure input sanitization, 3) Add Content-Security-Policy header
**Acceptance**: All user inputs sanitized, CSP header set
**Files**: Frontend code review report, `nginx/nginx.conf` (CSP header)

### Task 9.5.1.7: Security Headers (CSP, HSTS, X-Frame-Options)
**Goal**: Configure security headers
**Phase**: 9.5.1 | **Dependencies**: None | **Time**: 1h
**Steps**: 1) Add Content-Security-Policy, 2) Add Strict-Transport-Security (HSTS), 3) Add X-Frame-Options: DENY, 4) Add X-Content-Type-Options: nosniff
**Acceptance**: All security headers present
**Files**: `nginx/nginx.conf` (updated)

---

## Phase 9.5.2: Performance Optimization (30 hours)

### Task 9.5.2.1: Database Query Optimization (EXPLAIN ANALYZE)
**Goal**: Optimize slow database queries
**Phase**: 9.5.2 | **Dependencies**: None | **Time**: 8h
**Steps**: 1) Identify slow queries (pg_stat_statements), 2) Run EXPLAIN ANALYZE, 3) Add missing indexes, 4) Optimize query structure
**Acceptance**: All queries <1 second, no seq scans on large tables
**Files**: Database optimization report, new migrations for indexes

### Task 9.5.2.2: Elasticsearch Query Optimization
**Goal**: Optimize Elasticsearch queries
**Phase**: 9.5.2 | **Dependencies**: None | **Time**: 4h
**Steps**: 1) Profile slow queries, 2) Optimize aggregations, 3) Tune field boosting
**Acceptance**: All ES queries <500ms
**Files**: Elasticsearch optimization report

### Task 9.5.2.3: Redis Caching Tuning (Optimal TTLs)
**Goal**: Tune cache TTLs for optimal hit rate
**Phase**: 9.5.2 | **Dependencies**: None | **Time**: 4h
**Steps**: 1) Monitor cache hit rates, 2) Adjust TTLs based on data volatility, 3) Verify hit rate >70%
**Acceptance**: Cache hit rate >70%
**Files**: Redis configuration updated

### Task 9.5.2.4: Connection Pooling (PostgreSQL, Redis, ES)
**Goal**: Configure optimal connection pools
**Phase**: 9.5.2 | **Dependencies**: None | **Time**: 3h
**Steps**: 1) Configure PostgreSQL pool (min=10, max=50), 2) Configure Redis pool, 3) Configure ES pool, 4) Monitor connection usage
**Acceptance**: Connection pools sized appropriately, no connection exhaustion
**Files**: Backend configuration updated

### Task 9.5.2.5: Load Testing (100 Concurrent Users)
**Goal**: Load test with 100 concurrent users
**Phase**: 9.5.2 | **Dependencies**: All previous optimization tasks | **Time**: 8h
**Steps**: 1) Create Locust load test script, 2) Run with 100 concurrent users, 3) Measure response times (p50, p95, p99), 4) Verify targets met
**Acceptance**: p95 <1 second, no errors, 100 concurrent users supported
**Files**: `tests/performance/locustfile_production.py`

### Task 9.5.2.6: Frontend Bundle Optimization
**Goal**: Optimize frontend bundle size
**Phase**: 9.5.2 | **Dependencies**: None | **Time**: 3h
**Steps**: 1) Enable code splitting, 2) Enable lazy loading for routes, 3) Remove unused dependencies, 4) Verify bundle size <2MB
**Acceptance**: Bundle size <2MB, initial load <3 seconds
**Files**: `webapp/vite.config.ts` (updated)

---

## Phase 9.5.3: Monitoring & Observability (30 hours)

### Task 9.5.3.1: Setup Prometheus Metrics
**Goal**: Instrument application with Prometheus
**Phase**: 9.5.3 | **Dependencies**: None | **Time**: 6h
**Steps**: 1) Install prometheus-fastapi-instrumentator, 2) Expose /metrics endpoint, 3) Add custom metrics (API latency, DB query time, cache hit rate, error rate)
**Acceptance**: Metrics exposed, Prometheus scraping
**Files**: `backend/app/main.py` (updated), `prometheus/prometheus.yml`

### Task 9.5.3.2: Create Grafana Dashboards
**Goal**: Grafana dashboards for system health
**Phase**: 9.5.3 | **Dependencies**: Task 9.5.3.1 | **Time**: 8h
**Steps**: 1) Create "System Health" dashboard (CPU, memory, disk), 2) Create "API Performance" dashboard (request rate, latency, error rate), 3) Create "Database Performance" dashboard (query duration, connection pool usage), 4) Create "User Activity" dashboard (active users, searches, alerts)
**Acceptance**: 4 Grafana dashboards operational
**Files**: `grafana/dashboards/*.json`

### Task 9.5.3.3: Setup Log Aggregation (ELK Stack or Loki)
**Goal**: Centralized log aggregation
**Phase**: 9.5.3 | **Dependencies**: None | **Time**: 6h
**Steps**: 1) Configure log shipping (Filebeat or Promtail), 2) Configure Elasticsearch/Loki, 3) Configure Kibana/Grafana for log viewing
**Acceptance**: Logs centralized, searchable
**Files**: `filebeat/filebeat.yml` or `promtail/promtail.yml`

### Task 9.5.3.4: Configure Alerting (PagerDuty or Opsgenie)
**Goal**: Alert on critical issues
**Phase**: 9.5.3 | **Dependencies**: Task 9.5.3.2 | **Time**: 4h
**Steps**: 1) Configure Grafana alerts, 2) Integrate with PagerDuty/Opsgenie, 3) Define alert rules (API error rate >5%, DB connections >80%, disk >85%)
**Acceptance**: Alerts configured, on-call notified
**Files**: `grafana/provisioning/alerting/*.yml`

### Task 9.5.3.5: Distributed Tracing (OpenTelemetry, Optional)
**Goal**: Implement distributed tracing
**Phase**: 9.5.3 | **Dependencies**: None | **Time**: 6h
**Steps**: 1) Install OpenTelemetry, 2) Instrument API endpoints, 3) Configure Jaeger backend, 4) View traces
**Acceptance**: Traces visible in Jaeger
**Files**: `backend/app/tracing.py`

---

## Phase 9.5.4: Backup, Documentation, Compliance (30 hours)

### Task 9.5.4.1: Automated PostgreSQL Backups
**Goal**: Daily automated backups with WAL archiving
**Phase**: 9.5.4 | **Dependencies**: None | **Time**: 4h
**Steps**: 1) Configure pg_dump daily (cron), 2) Configure WAL archiving to S3 or NFS, 3) Test backup restoration
**Acceptance**: Daily backups run successfully, restoration tested
**Files**: `scripts/backup_postgres.sh`, cron configuration

### Task 9.5.4.2: Automated Elasticsearch Snapshots
**Goal**: Daily ES snapshots
**Phase**: 9.5.4 | **Dependencies**: None | **Time**: 3h
**Steps**: 1) Configure ES snapshot repository (S3 or NFS), 2) Schedule daily snapshots, 3) Test snapshot restoration
**Acceptance**: Daily snapshots run successfully, restoration tested
**Files**: Elasticsearch configuration

### Task 9.5.4.3: Redis Persistence Configuration
**Goal**: Configure RDB + AOF for Redis
**Phase**: 9.5.4 | **Dependencies**: None | **Time**: 2h
**Steps**: 1) Enable RDB snapshots (every 6 hours), 2) Enable AOF, 3) Test recovery
**Acceptance**: Redis persistence configured, recovery tested
**Files**: `redis/redis.conf`

### Task 9.5.4.4: Disaster Recovery Plan
**Goal**: Document disaster recovery procedures
**Phase**: 9.5.4 | **Dependencies**: Tasks 9.5.4.1-9.5.4.3 | **Time**: 4h
**Steps**: 1) Document backup locations, 2) Document restoration procedures, 3) Define RPO (<24 hours) and RTO (<4 hours), 4) Conduct DR drill
**Acceptance**: DR plan documented, drill successful
**Files**: `docs/disaster-recovery-plan.md`

### Task 9.5.4.5: User Guide (Clinician Workflows)
**Goal**: Comprehensive user guide
**Phase**: 9.5.4 | **Dependencies**: None | **Time**: 6h
**Steps**: 1) Document patient search, 2) Document timeline view, 3) Document coding workflow, 4) Document CDS recommendations, 5) Add screenshots
**Acceptance**: User guide complete
**Files**: `docs/user-guides/clinician-guide.md`

### Task 9.5.4.6: Admin Guide (Configuration, Troubleshooting)
**Goal**: Administrator guide
**Phase**: 9.5.4 | **Dependencies**: None | **Time**: 5h
**Steps**: 1) Document configuration (environment variables), 2) Document user management, 3) Document troubleshooting, 4) Document backup/restore
**Acceptance**: Admin guide complete
**Files**: `docs/admin-guides/administrator-guide.md`

### Task 9.5.4.7: API Documentation (OpenAPI Spec, Swagger UI)
**Goal**: Complete API documentation
**Phase**: 9.5.4 | **Dependencies**: None | **Time**: 3h
**Steps**: 1) Review all API endpoints, 2) Ensure OpenAPI metadata complete, 3) Publish Swagger UI
**Acceptance**: All endpoints documented, Swagger UI accessible
**Files**: OpenAPI spec at `/docs`

### Task 9.5.4.8: HIPAA/GDPR/DSPT Compliance Checklist
**Goal**: Complete compliance checklists
**Phase**: 9.5.4 | **Dependencies**: All previous work | **Time**: 3h
**Steps**: 1) Complete HIPAA compliance checklist, 2) Complete GDPR checklist, 3) Complete NHS DSPT checklist, 4) Document gaps, 5) Remediate critical gaps
**Acceptance**: Compliance checklists complete, critical gaps remediated
**Files**: `docs/compliance/*.md`

---

## Production Deployment Checklist

### Pre-Production
- [ ] Security audit passed, vulnerabilities remediated
- [ ] Performance testing passed (100 concurrent users, p95 <1 second)
- [ ] Monitoring dashboards operational (Grafana)
- [ ] Backup/recovery tested successfully
- [ ] Documentation complete (user/admin guides, API docs)
- [ ] Compliance checklists completed (HIPAA, GDPR, DSPT)

### Production Environment
- [ ] Production servers provisioned (8GB RAM, 4 CPU cores minimum)
- [ ] TLS certificates installed (Let's Encrypt or commercial)
- [ ] DNS configured (production domain)
- [ ] Firewall rules configured (IP whitelisting if needed)
- [ ] Environment variables configured (secrets in vault/secret manager)
- [ ] Database migrations applied (PostgreSQL, Elasticsearch)
- [ ] Initial data loaded (ICD-10 library, dm+d codes, clinical guidelines)
- [ ] MedCAT models mounted (SNOMED, ICD-10, PHI detection)

### Deployment
- [ ] Backend deployed (Docker containers)
- [ ] Frontend deployed (static files to Nginx)
- [ ] Nginx configured (HTTPS, rate limiting, security headers)
- [ ] PostgreSQL running (connection pool configured)
- [ ] Redis running (persistence enabled)
- [ ] Elasticsearch running (snapshots configured)
- [ ] CogStack-ModelServe running (all models loaded)
- [ ] Celery workers running (task processing, beat scheduler)
- [ ] Event consumers running (audit log, cache invalidation, etc.)

### Monitoring
- [ ] Prometheus scraping metrics (/metrics)
- [ ] Grafana dashboards accessible
- [ ] Log aggregation operational (ELK/Loki)
- [ ] Alerting configured (PagerDuty/Opsgenie)
- [ ] On-call rotation defined

### Post-Deployment
- [ ] Smoke tests run on production (all critical workflows)
- [ ] User acceptance testing (UAT) with pilot users
- [ ] Training sessions conducted (clinicians, admins)
- [ ] Go-live announcement sent
- [ ] Monitor for 48 hours (on-call standby)

---

## Rollback Plan

**If critical issues arise post-deployment:**

1. **Immediate**: Revert Nginx to route to previous version
2. **Database**: Restore from last backup (RPO <24 hours)
3. **Notify**: Alert all users of rollback
4. **Investigate**: Root cause analysis
5. **Fix**: Address issues in development
6. **Re-deploy**: Schedule new deployment after fixes validated

---

## Summary

**Total Tasks**: 28 tasks across 4 phases
**Total Estimated Time**: 120 hours (4 weeks)

**Phase Breakdown**:
- Phase 9.5.1 (Security Hardening): 30 hours, 7 tasks
- Phase 9.5.2 (Performance Optimization): 30 hours, 6 tasks
- Phase 9.5.3 (Monitoring & Observability): 30 hours, 5 tasks
- Phase 9.5.4 (Backup, Documentation, Compliance): 30 hours, 10 tasks

**Deliverables**:
- Security audit report (pen test, vulnerability scan)
- Performance test report (load testing results)
- Grafana dashboards (4 dashboards)
- Documentation (user guide, admin guide, API docs)
- Compliance checklists (HIPAA, GDPR, DSPT)
- Disaster recovery plan

**Production Readiness Criteria**:
- Security: No critical vulnerabilities, TLS 1.3 enforced
- Performance: 100 concurrent users, p95 <1 second
- Monitoring: Prometheus + Grafana operational, alerting configured
- Backups: Daily automated backups, restoration tested
- Compliance: HIPAA/GDPR/DSPT checklists complete
- Documentation: User/admin guides complete

**Total Program Effort**: ~1,560 hours across Sprints 1-9.5 (39 weeks / 9.75 months)
