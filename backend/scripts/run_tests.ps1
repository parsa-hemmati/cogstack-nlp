# =============================================================================
# Backend Test Runner Script (PowerShell)
# =============================================================================
#
# Runs pytest tests for the CogStack NLP Clinical Care Tools backend.
# Supports multiple test modes, coverage reporting, and filtering.
#
# Usage:
#   .\scripts\run_tests.ps1              # Run all tests
#   .\scripts\run_tests.ps1 unit         # Run unit tests only
#   .\scripts\run_tests.ps1 integration  # Run integration tests only
#   .\scripts\run_tests.ps1 performance  # Run performance tests only
#   .\scripts\run_tests.ps1 security     # Run security tests only
#   .\scripts\run_tests.ps1 coverage     # Run all tests with coverage report
#   .\scripts\run_tests.ps1 quick        # Run smoke tests (quick validation)
#   .\scripts\run_tests.ps1 <test_path>  # Run specific test file or directory
#
# =============================================================================

param(
    [Parameter(Position=0)]
    [string]$TestMode = "all"
)

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Split-Path -Parent $ScriptDir

# Change to backend directory
Set-Location $BackendDir

# Print header
Write-Host "============================================" -ForegroundColor Blue
Write-Host "  CogStack NLP Backend Test Runner" -ForegroundColor Blue
Write-Host "============================================" -ForegroundColor Blue
Write-Host ""

# Set test environment variables
$env:TESTING = "true"
$env:LOG_LEVEL = "WARNING"
$env:DATABASE_URL = "sqlite+aiosqlite:///:memory:"
$env:JWT_SECRET_KEY = "test-secret-key-do-not-use-in-production"
$env:ENCRYPTION_KEY = "test-encryption-key-32-bytes-minimum"

# Default pytest options
$PytestOpts = "-v --tb=short"
$CoverageOpts = ""
$MarkerOpts = ""
$TestPath = "tests"

# Parse test mode
switch ($TestMode) {
    "unit" {
        Write-Host "Running unit tests only..." -ForegroundColor Yellow
        $MarkerOpts = "-m unit"
        $TestPath = "tests/unit"
    }
    "integration" {
        Write-Host "Running integration tests only..." -ForegroundColor Yellow
        $MarkerOpts = "-m integration"
        $TestPath = "tests/integration"
    }
    "performance" {
        Write-Host "Running performance tests only..." -ForegroundColor Yellow
        $MarkerOpts = "-m performance"
        $TestPath = "tests/performance"
    }
    "security" {
        Write-Host "Running security tests only..." -ForegroundColor Yellow
        $TestPath = "tests/security"
    }
    "coverage" {
        Write-Host "Running all tests with coverage..." -ForegroundColor Yellow
        $CoverageOpts = "--cov=app --cov-report=term-missing --cov-report=html:coverage_report --cov-fail-under=50"
    }
    "quick" {
        Write-Host "Running quick smoke tests..." -ForegroundColor Yellow
        $PytestOpts = "-v --tb=short -x --max-fail=1"
        $TestPath = "tests/unit/models tests/unit/schemas"
    }
    "all" {
        Write-Host "Running all tests..." -ForegroundColor Yellow
    }
    default {
        # Assume it's a specific test path
        if (Test-Path $TestMode) {
            Write-Host "Running specific tests: $TestMode" -ForegroundColor Yellow
            $TestPath = $TestMode
        } else {
            Write-Host "Unknown option or test path: $TestMode" -ForegroundColor Red
            Write-Host ""
            Write-Host "Usage:"
            Write-Host "  .\scripts\run_tests.ps1              # Run all tests"
            Write-Host "  .\scripts\run_tests.ps1 unit         # Run unit tests only"
            Write-Host "  .\scripts\run_tests.ps1 integration  # Run integration tests only"
            Write-Host "  .\scripts\run_tests.ps1 performance  # Run performance tests only"
            Write-Host "  .\scripts\run_tests.ps1 security     # Run security tests only"
            Write-Host "  .\scripts\run_tests.ps1 coverage     # Run all tests with coverage"
            Write-Host "  .\scripts\run_tests.ps1 quick        # Run smoke tests"
            Write-Host "  .\scripts\run_tests.ps1 <test_path>  # Run specific test file/dir"
            exit 1
        }
    }
}

Write-Host ""

# Check if pytest is available
$pytestPath = Get-Command pytest -ErrorAction SilentlyContinue
if (-not $pytestPath) {
    Write-Host "pytest not found! Please install test dependencies:" -ForegroundColor Red
    Write-Host "  pip install pytest pytest-asyncio pytest-cov pytest-mock httpx aiosqlite"
    exit 1
}

# Build the pytest command
$PytestArgs = @()
$PytestArgs += $PytestOpts.Split(' ')
if ($MarkerOpts) { $PytestArgs += $MarkerOpts.Split(' ') }
if ($CoverageOpts) { $PytestArgs += $CoverageOpts.Split(' ') }
$PytestArgs += $TestPath.Split(' ')

$PytestCmd = "pytest $($PytestArgs -join ' ')"
Write-Host "Command: $PytestCmd" -ForegroundColor Blue
Write-Host ""

# Create logs directory
New-Item -ItemType Directory -Path "tests/logs" -Force | Out-Null

# Run tests
$StartTime = Get-Date

try {
    & pytest @PytestArgs
    $ExitCode = $LASTEXITCODE
} catch {
    $ExitCode = 1
}

$EndTime = Get-Date
$Duration = [math]::Round(($EndTime - $StartTime).TotalSeconds)

if ($ExitCode -eq 0) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  All tests PASSED in ${Duration}s" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green

    # Show coverage report location if generated
    if ($CoverageOpts -and (Test-Path "coverage_report")) {
        Write-Host ""
        Write-Host "Coverage report generated at:" -ForegroundColor Blue
        Write-Host "  $(Get-Location)/coverage_report/index.html"
    }

    exit 0
} else {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "  Tests FAILED after ${Duration}s" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    exit 1
}
