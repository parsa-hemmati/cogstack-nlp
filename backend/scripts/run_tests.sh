#!/bin/bash

# =============================================================================
# Backend Test Runner Script
# =============================================================================
#
# Runs pytest tests for the CogStack NLP Clinical Care Tools backend.
# Supports multiple test modes, coverage reporting, and filtering.
#
# Usage:
#   ./scripts/run_tests.sh              # Run all tests
#   ./scripts/run_tests.sh unit         # Run unit tests only
#   ./scripts/run_tests.sh integration  # Run integration tests only
#   ./scripts/run_tests.sh performance  # Run performance tests only
#   ./scripts/run_tests.sh security     # Run security tests only
#   ./scripts/run_tests.sh coverage     # Run all tests with coverage report
#   ./scripts/run_tests.sh quick        # Run smoke tests (quick validation)
#   ./scripts/run_tests.sh <test_path>  # Run specific test file or directory
#
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory (relative to backend)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Change to backend directory
cd "$BACKEND_DIR"

# Print header
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  CogStack NLP Backend Test Runner${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Set test environment variables
export TESTING=true
export LOG_LEVEL=WARNING
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export JWT_SECRET_KEY="test-secret-key-do-not-use-in-production"
export ENCRYPTION_KEY="test-encryption-key-32-bytes-minimum"

# Default pytest options
PYTEST_OPTS="-v --tb=short"
COVERAGE_OPTS=""
MARKER_OPTS=""
TEST_PATH="tests"

# Parse command line arguments
case "${1:-all}" in
    "unit")
        echo -e "${YELLOW}Running unit tests only...${NC}"
        MARKER_OPTS="-m unit"
        TEST_PATH="tests/unit"
        ;;
    "integration")
        echo -e "${YELLOW}Running integration tests only...${NC}"
        MARKER_OPTS="-m integration"
        TEST_PATH="tests/integration"
        ;;
    "performance")
        echo -e "${YELLOW}Running performance tests only...${NC}"
        MARKER_OPTS="-m performance"
        TEST_PATH="tests/performance"
        ;;
    "security")
        echo -e "${YELLOW}Running security tests only...${NC}"
        TEST_PATH="tests/security"
        ;;
    "coverage")
        echo -e "${YELLOW}Running all tests with coverage...${NC}"
        COVERAGE_OPTS="--cov=app --cov-report=term-missing --cov-report=html:coverage_report --cov-fail-under=50"
        ;;
    "quick")
        echo -e "${YELLOW}Running quick smoke tests...${NC}"
        PYTEST_OPTS="-v --tb=short -x --max-fail=1"
        TEST_PATH="tests/unit/models tests/unit/schemas"
        ;;
    "all")
        echo -e "${YELLOW}Running all tests...${NC}"
        ;;
    *)
        # Assume it's a specific test path
        if [ -e "$1" ]; then
            echo -e "${YELLOW}Running specific tests: $1${NC}"
            TEST_PATH="$1"
        else
            echo -e "${RED}Unknown option or test path: $1${NC}"
            echo ""
            echo "Usage:"
            echo "  ./scripts/run_tests.sh              # Run all tests"
            echo "  ./scripts/run_tests.sh unit         # Run unit tests only"
            echo "  ./scripts/run_tests.sh integration  # Run integration tests only"
            echo "  ./scripts/run_tests.sh performance  # Run performance tests only"
            echo "  ./scripts/run_tests.sh security     # Run security tests only"
            echo "  ./scripts/run_tests.sh coverage     # Run all tests with coverage"
            echo "  ./scripts/run_tests.sh quick        # Run smoke tests"
            echo "  ./scripts/run_tests.sh <test_path>  # Run specific test file/dir"
            exit 1
        fi
        ;;
esac

echo ""

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}pytest not found! Please install test dependencies:${NC}"
    echo "  pip install pytest pytest-asyncio pytest-cov pytest-mock httpx aiosqlite"
    exit 1
fi

# Build the pytest command
PYTEST_CMD="pytest $PYTEST_OPTS $MARKER_OPTS $COVERAGE_OPTS $TEST_PATH"

echo -e "${BLUE}Command: $PYTEST_CMD${NC}"
echo ""

# Create logs directory if running with logging
mkdir -p tests/logs

# Run tests
START_TIME=$(date +%s)

if $PYTEST_CMD; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  All tests PASSED in ${DURATION}s${NC}"
    echo -e "${GREEN}============================================${NC}"

    # Show coverage report location if generated
    if [ -n "$COVERAGE_OPTS" ] && [ -d "coverage_report" ]; then
        echo ""
        echo -e "${BLUE}Coverage report generated at:${NC}"
        echo "  $(pwd)/coverage_report/index.html"
    fi

    exit 0
else
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    echo ""
    echo -e "${RED}============================================${NC}"
    echo -e "${RED}  Tests FAILED after ${DURATION}s${NC}"
    echo -e "${RED}============================================${NC}"
    exit 1
fi
