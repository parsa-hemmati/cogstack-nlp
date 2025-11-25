# Timeline Module - Operations Runbook

**Version**: 1.0.0  
**Last Updated**: 2025-11-22  
**Owner**: Operations Team

## Quick Reference

| Alert | Severity | Response Time | Action |
|-------|----------|---------------|--------|
| API Error Rate >5% | Critical | Immediate | See "High Error Rate" |
| API P95 >1s | Critical | Immediate | See "Slow API Responses" |
| Elasticsearch Down | Critical | Immediate | See "Elasticsearch Outage" |
| Redis Down | Critical | Immediate | See "Redis Outage" |
| API Error Rate >2% | Warning | 30 minutes | Monitor, investigate logs |
| Cache Hit Rate <50% | Warning | 1 hour | Check Redis memory |

---

## Incident Response Procedures

### High Error Rate (>5%)

**Symptoms**:
- APM dashboard shows error rate spike
- User reports of "something went wrong" errors
- Sentry showing increased exceptions

**Diagnosis**:
1. Check APM dashboard for error details
2. Review application logs: `kubectl logs -l app=timeline-api --tail=100`
3. Check Sentry for exception stack traces
4. Verify external dependencies (Elasticsearch, Redis, PostgreSQL)

**Resolution**:
```bash
# Check API pod health
kubectl get pods -l app=timeline-api

# Check recent deployments (possible bad deploy)
kubectl rollout history deployment/timeline-api

# If recent deploy is bad, rollback
kubectl rollout undo deployment/timeline-api

# Restart pods if stale connections
kubectl rollout restart deployment/timeline-api

# Check Elasticsearch health
curl -XGET 'http://elasticsearch:9200/_cluster/health'

# Check Redis health
redis-cli ping
```

**Escalation**: If error rate remains >5% after 15 minutes, page on-call developer

---

### Slow API Responses (P95 >1s)

**Symptoms**:
- APM shows increased response times
- Users report timeline "loading forever"
- High CPU usage on API pods

**Diagnosis**:
1. Check APM for slow endpoints
2. Review database query times
3. Check Elasticsearch query performance
4. Monitor Redis cache hit rate

**Resolution**:
```bash
# Scale up API pods
kubectl scale deployment/timeline-api --replicas=6

# Check Elasticsearch slow queries
curl -XGET 'http://elasticsearch:9200/_nodes/stats/indices/search'

# Warm up Redis cache
python scripts/warm_cache.py --patient-ids=<high-usage-patients>

# Check database connection pool
psql -h postgres -U app -c "SELECT count(*) FROM pg_stat_activity WHERE datname='clinicaldb';"
```

**Temporary Mitigation**:
- Enable feature flag to disable timeline for non-critical users
- Increase API timeout to 5s (from 2s)

---

### Elasticsearch Outage

**Symptoms**:
- Timeline returns "Service Unavailable"
- Logs show "Connection refused" to Elasticsearch

**Diagnosis**:
```bash
# Check Elasticsearch status
curl -XGET 'http://elasticsearch:9200/_cluster/health'

# Check pod status
kubectl get pods -l app=elasticsearch

# Check logs
kubectl logs -l app=elasticsearch --tail=100
```

**Resolution**:
```bash
# If Elasticsearch is down, restart
kubectl rollout restart statefulset/elasticsearch

# If index is corrupted, restore from backup
./scripts/restore_es_backup.sh --date=<yesterday>

# If disk full, expand volume
kubectl edit pvc elasticsearch-data
# Change size: 100Gi -> 200Gi
```

**Impact**: Timeline completely unavailable. ETA: 5-15 minutes

---

### Redis Outage

**Symptoms**:
- Timeline still works but slower (no cache)
- Logs show "Connection refused" to Redis

**Diagnosis**:
```bash
# Check Redis status
redis-cli ping

# Check pod status
kubectl get pods -l app=redis

# Check memory usage
redis-cli info memory
```

**Resolution**:
```bash
# Restart Redis
kubectl rollout restart deployment/redis

# If memory full, increase memory limit
kubectl edit deployment redis
# Increase resources.limits.memory

# Flush stale keys
redis-cli --scan --pattern 'timeline:*' | xargs redis-cli del
```

**Impact**: Timeline works but slower (cache miss penalty ~200ms). Not critical.

---

## Monitoring Dashboards

### APM Dashboard (DataDog/New Relic)

**URL**: https://app.datadoghq.com/dashboard/timeline-api

**Key Metrics**:
- Request rate (normal: 50-200 req/min)
- Response time P95 (target: <500ms)
- Error rate (target: <1%)
- Cache hit rate (target: >70%)

### Logs (Elasticsearch/Splunk)

**Query Examples**:
```
# High error rate
index=app service=timeline-api level=ERROR | stats count by error_type

# Slow queries
index=app service=timeline-api duration_ms>1000 | stats avg(duration_ms) by endpoint

# PHI access audit
index=audit action=VIEW_TIMELINE | stats count by user_id
```

---

## Routine Maintenance

### Weekly

- Review error trends (Sentry)
- Check disk usage (Elasticsearch, PostgreSQL)
- Verify backup success

### Monthly

- Review performance trends (APM)
- Update dependencies (security patches)
- Capacity planning review

### Quarterly

- Disaster recovery drill
- Load testing
- Security audit

---

## Rollback Procedure

**When to rollback**:
- Error rate >10% for >5 minutes
- Data corruption detected
- Security vulnerability in current release

**Steps**:
```bash
# 1. Check deployment history
kubectl rollout history deployment/timeline-api

# 2. Rollback to previous version
kubectl rollout undo deployment/timeline-api

# 3. Verify pods are healthy
kubectl get pods -l app=timeline-api

# 4. Monitor error rate (should drop immediately)
# Check APM dashboard

# 5. Notify stakeholders
# Post to #incidents Slack channel
```

---

## Contact Information

| Role | Name | Slack | Phone | Escalation |
|------|------|-------|-------|------------|
| On-Call Engineer | Rotation | @oncall-eng | 555-ON-CALL | PagerDuty |
| Tech Lead | Dr. Smith | @dr-smith | 555-1234 | Slack first |
| DevOps Lead | Jane Doe | @jane-doe | 555-5678 | Slack first |
| Product Owner | Bob Johnson | @bob-j | 555-9012 | Email okay |

---

## Escalation Policy

1. **0-15 minutes**: On-call engineer investigates
2. **15-30 minutes**: If unresolved, page tech lead
3. **30-60 minutes**: If critical impact, escalate to CTO
4. **60+ minutes**: Incident commander assigned

---

*For technical details, see [Timeline Architecture](../technical/timeline-architecture.md)*
