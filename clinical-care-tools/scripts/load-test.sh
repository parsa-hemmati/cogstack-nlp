#!/bin/bash

# Clinical Care Tools - Load Testing Script
# Version: 1.0.0
# Purpose: Load testing using Locust

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
NUM_USERS="${NUM_USERS:-10}"
RAMP_UP="${RAMP_UP:-5}"  # Users added per second
DURATION="${DURATION:-60}"  # Seconds

echo -e "${BLUE}=========================================="
echo "Clinical Care Tools - Load Testing"
echo "==========================================${NC}"
echo ""
echo "Configuration:"
echo "  API URL: $API_BASE_URL"
echo "  Users: $NUM_USERS"
echo "  Ramp-up: $RAMP_UP users/second"
echo "  Duration: $DURATION seconds"
echo ""

# Create Locust test file
cat > /tmp/locustfile.py << 'EOF'
from locust import HttpUser, task, between
import json

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def health_check(self):
        """Check API health"""
        self.client.get("/api/health", name="/api/health")

    @task(2)
    def list_patients(self):
        """List patients"""
        self.client.get("/api/patients?skip=0&limit=20", name="/api/patients")

    @task(1)
    def search_patients(self):
        """Search for patients"""
        payload = {
            "concept": "Type 2 Diabetes",
            "filters": {
                "negation": "Affirmed",
                "temporality": "Current"
            },
            "limit": 20
        }
        self.client.post(
            "/api/patients/search",
            json=payload,
            name="/api/patients/search"
        )

    @task(1)
    def get_audit_logs(self):
        """Get audit logs"""
        self.client.get("/api/audit-logs?skip=0&limit=50", name="/api/audit-logs")
EOF

# Check if Locust is installed
if ! command -v locust &> /dev/null; then
    echo -e "${YELLOW}Installing Locust...${NC}"
    pip install locust
fi

echo -e "${YELLOW}Starting load test...${NC}"
echo ""

# Run Locust
locust -f /tmp/locustfile.py \
    --host=$API_BASE_URL \
    --users=$NUM_USERS \
    --spawn-rate=$RAMP_UP \
    --run-time=${DURATION}s \
    --headless \
    --csv=load_test_results

echo ""
echo -e "${GREEN}Load test completed!${NC}"
echo ""
echo "Results:"
echo "  Statistics: load_test_results_stats.csv"
echo "  History: load_test_results_stats_history.csv"
echo "  Failures: load_test_results_failures.csv"
echo ""

# Display summary
if [ -f "load_test_results_stats.csv" ]; then
    echo "Summary:"
    head -10 load_test_results_stats.csv
fi

echo ""
echo "To run interactive load testing:"
echo "  locust -f /tmp/locustfile.py --host=$API_BASE_URL"
echo "  Then open http://localhost:8089"
echo ""
