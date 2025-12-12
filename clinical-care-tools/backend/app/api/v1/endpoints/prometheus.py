"""
Prometheus metrics endpoint for application monitoring.

Exposes metrics in Prometheus format for:
- HTTP request metrics (count, latency)
- Application-specific metrics (sessions, PHI access)
- Database connection pool metrics
"""

from fastapi import APIRouter, Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
)
import time

router = APIRouter()

# =============================================================================
# HTTP Request Metrics
# =============================================================================

# Request counter by method, path, and status
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"]
)

# Request latency histogram
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# =============================================================================
# Application Metrics
# =============================================================================

# Active user sessions
ACTIVE_SESSIONS = Gauge(
    "app_active_sessions",
    "Number of active user sessions"
)

# PHI access counter
PHI_ACCESS_COUNT = Counter(
    "app_phi_access_total",
    "Total PHI access events",
    ["action", "resource_type"]
)

# Login attempts
LOGIN_ATTEMPTS = Counter(
    "app_login_attempts_total",
    "Total login attempts",
    ["status"]  # success, failed, locked
)

# Document processing
DOCUMENT_PROCESSING_TIME = Histogram(
    "app_document_processing_seconds",
    "Document processing time in seconds",
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0]
)

DOCUMENTS_PROCESSED = Counter(
    "app_documents_processed_total",
    "Total documents processed",
    ["status"]  # success, failed
)

# =============================================================================
# Database Metrics
# =============================================================================

DB_CONNECTIONS_ACTIVE = Gauge(
    "db_connections_active",
    "Number of active database connections"
)

DB_CONNECTIONS_POOL_SIZE = Gauge(
    "db_connections_pool_size",
    "Database connection pool size"
)

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],  # select, insert, update, delete
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# =============================================================================
# Cache Metrics
# =============================================================================

CACHE_HITS = Counter(
    "cache_hits_total",
    "Total cache hits"
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Total cache misses"
)

# =============================================================================
# Alert Thresholds (for documentation)
# =============================================================================
# These are the thresholds used in alerting rules:
# - Error rate > 5% over 5 minutes
# - P95 latency > 2 seconds
# - Active sessions > 1000
# - Failed logins > 10 in 5 minutes (potential attack)

# =============================================================================
# Metrics Endpoint
# =============================================================================

@router.get(
    "",
    summary="Prometheus Metrics",
    description="Returns application metrics in Prometheus format",
    response_class=Response,
    tags=["monitoring"]
)
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns all application metrics in Prometheus exposition format.
    This endpoint should be scraped by Prometheus at regular intervals.
    
    **Security Note**: This endpoint should only be accessible from
    the internal network (not exposed publicly).
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


# =============================================================================
# Helper functions for recording metrics
# =============================================================================

def record_request(method: str, path: str, status_code: int, duration: float):
    """Record HTTP request metrics."""
    # Normalize path to avoid high cardinality
    normalized_path = _normalize_path(path)
    REQUEST_COUNT.labels(method=method, path=normalized_path, status_code=status_code).inc()
    REQUEST_LATENCY.labels(method=method, path=normalized_path).observe(duration)


def record_login_attempt(success: bool, locked: bool = False):
    """Record login attempt."""
    if locked:
        LOGIN_ATTEMPTS.labels(status="locked").inc()
    elif success:
        LOGIN_ATTEMPTS.labels(status="success").inc()
    else:
        LOGIN_ATTEMPTS.labels(status="failed").inc()


def record_phi_access(action: str, resource_type: str):
    """Record PHI access event."""
    PHI_ACCESS_COUNT.labels(action=action, resource_type=resource_type).inc()


def record_document_processed(success: bool, duration: float):
    """Record document processing."""
    DOCUMENTS_PROCESSED.labels(status="success" if success else "failed").inc()
    DOCUMENT_PROCESSING_TIME.observe(duration)


def update_session_count(count: int):
    """Update active session count."""
    ACTIVE_SESSIONS.set(count)


def record_cache_hit():
    """Record cache hit."""
    CACHE_HITS.inc()


def record_cache_miss():
    """Record cache miss."""
    CACHE_MISSES.inc()


def _normalize_path(path: str) -> str:
    """
    Normalize path to reduce cardinality.
    
    Replaces dynamic segments (UUIDs, IDs) with placeholders.
    """
    import re
    
    # Replace UUIDs
    path = re.sub(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        '{id}',
        path,
        flags=re.IGNORECASE
    )
    
    # Replace numeric IDs
    path = re.sub(r'/\d+(?=/|$)', '/{id}', path)
    
    return path
