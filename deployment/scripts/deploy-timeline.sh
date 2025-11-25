#!/bin/bash
#
# Timeline Module Deployment Script
# 
# Usage: ./deploy-timeline.sh [production|staging] [version]
# Example: ./deploy-timeline.sh production v1.2.0
#

set -euo pipefail

# Configuration
ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
NAMESPACE="clinical-app-${ENVIRONMENT}"
DEPLOYMENT_NAME="timeline-api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Pre-flight checks
preflight_checks() {
    log_info "Running pre-flight checks..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    
    # Check context
    CURRENT_CONTEXT=$(kubectl config current-context)
    log_info "Current kubectl context: $CURRENT_CONTEXT"
    
    if [[ "$ENVIRONMENT" == "production" ]] && [[ "$CURRENT_CONTEXT" != *"production"* ]]; then
        log_warn "Deploying to production but context is $CURRENT_CONTEXT"
        read -p "Continue? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log_error "Deployment aborted"
            exit 1
        fi
    fi
    
    # Check image exists
    IMAGE="your-registry.com/timeline-api:${VERSION}"
    log_info "Checking image: $IMAGE"
    # Add image existence check here
    
    log_info "Pre-flight checks passed"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    kubectl run migration-runner \
        --image=your-registry.com/timeline-api:${VERSION} \
        --namespace=${NAMESPACE} \
        --restart=Never \
        --command -- alembic upgrade head
    
    # Wait for migration to complete
    kubectl wait --for=condition=complete job/migration-runner \
        --namespace=${NAMESPACE} \
        --timeout=300s
    
    log_info "Migrations complete"
}

# Create Elasticsearch index if not exists
create_es_index() {
    log_info "Creating Elasticsearch index (if not exists)..."
    
    kubectl run es-index-creator \
        --image=your-registry.com/timeline-api:${VERSION} \
        --namespace=${NAMESPACE} \
        --restart=Never \
        --command -- python scripts/create_es_index.py --index clinical_concepts
    
    kubectl wait --for=condition=complete job/es-index-creator \
        --namespace=${NAMESPACE} \
        --timeout=120s
    
    log_info "Elasticsearch index ready"
}

# Deploy backend
deploy_backend() {
    log_info "Deploying backend (${DEPLOYMENT_NAME})..."
    
    # Update deployment image
    kubectl set image deployment/${DEPLOYMENT_NAME} \
        ${DEPLOYMENT_NAME}=your-registry.com/timeline-api:${VERSION} \
        --namespace=${NAMESPACE}
    
    # Wait for rollout
    kubectl rollout status deployment/${DEPLOYMENT_NAME} \
        --namespace=${NAMESPACE} \
        --timeout=600s
    
    log_info "Backend deployed successfully"
}

# Deploy frontend
deploy_frontend() {
    log_info "Deploying frontend..."
    
    # Build frontend
    cd frontend
    npm run build
    
    # Upload to CDN
    aws s3 sync dist/ s3://your-cdn-bucket/${ENVIRONMENT}/timeline/ \
        --delete \
        --cache-control max-age=31536000
    
    # Invalidate CloudFront cache
    aws cloudfront create-invalidation \
        --distribution-id YOUR_DIST_ID \
        --paths "/timeline/*"
    
    log_info "Frontend deployed successfully"
}

# Warm up cache
warm_cache() {
    log_info "Warming up Redis cache..."
    
    # Get API endpoint
    API_URL=$(kubectl get service timeline-api \
        --namespace=${NAMESPACE} \
        -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    # Warm cache for high-usage patients
    python scripts/warm_cache.py \
        --api-url "https://${API_URL}" \
        --patient-ids="P12345,P67890" \
        --environment=${ENVIRONMENT}
    
    log_info "Cache warmed up"
}

# Health checks
health_checks() {
    log_info "Running health checks..."
    
    # Get API endpoint
    API_URL=$(kubectl get service timeline-api \
        --namespace=${NAMESPACE} \
        -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    # Check health endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://${API_URL}/health")
    
    if [[ "$HTTP_CODE" == "200" ]]; then
        log_info "Health check passed (HTTP $HTTP_CODE)"
    else
        log_error "Health check failed (HTTP $HTTP_CODE)"
        exit 1
    fi
    
    # Check timeline endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $TEST_TOKEN" \
        "https://${API_URL}/api/v1/timeline/P12345")
    
    if [[ "$HTTP_CODE" == "200" ]]; then
        log_info "Timeline endpoint check passed (HTTP $HTTP_CODE)"
    else
        log_error "Timeline endpoint check failed (HTTP $HTTP_CODE)"
        exit 1
    fi
    
    log_info "All health checks passed"
}

# Rollback function
rollback() {
    log_error "Deployment failed. Rolling back..."
    
    kubectl rollout undo deployment/${DEPLOYMENT_NAME} \
        --namespace=${NAMESPACE}
    
    kubectl rollout status deployment/${DEPLOYMENT_NAME} \
        --namespace=${NAMESPACE} \
        --timeout=600s
    
    log_info "Rollback complete"
}

# Main deployment flow
main() {
    log_info "========================================="
    log_info "Timeline Module Deployment"
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    log_info "========================================="
    
    # Trap errors and rollback
    trap rollback ERR
    
    preflight_checks
    run_migrations
    create_es_index
    deploy_backend
    deploy_frontend
    warm_cache
    health_checks
    
    log_info "========================================="
    log_info "Deployment Complete!"
    log_info "Monitor: https://app.datadoghq.com/dashboard/timeline"
    log_info "========================================="
}

# Run deployment
main "$@"
