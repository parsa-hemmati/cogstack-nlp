# CCPM Parallel Cherry-Pick PowerShell Script
# For Windows execution

Write-Host "========================================" -ForegroundColor Blue
Write-Host "CCPM Parallel Cherry-Pick Consolidation" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Configuration
$CCPMConfig = ".ccpm\ccpm-cherry-pick.yaml"
$Workers = 8
$ParallelLimit = 4
$CurrentBranch = "ccpm-consolidated"
$AnalysisDir = ".ccpm\analysis"
$ReportsDir = ".ccpm\reports"

# Create necessary directories
New-Item -ItemType Directory -Force -Path $AnalysisDir | Out-Null
New-Item -ItemType Directory -Force -Path $ReportsDir | Out-Null

# Check prerequisites
function Check-Prerequisites {
    Write-Host "Checking prerequisites..." -ForegroundColor Yellow

    # Check current branch
    $current = git branch --show-current
    if ($current -ne $CurrentBranch) {
        Write-Host "Error: Not on $CurrentBranch branch" -ForegroundColor Red
        Write-Host "Current branch: $current"
        Write-Host "Please checkout $CurrentBranch first"
        exit 1
    }

    # Fetch all remotes
    Write-Host "Fetching all remotes..."
    git fetch --all --prune

    Write-Host "Prerequisites checked successfully" -ForegroundColor Green
}

# Analyze module function
function Analyze-Module {
    param(
        [string]$WorkerId,
        [string]$Module,
        [string[]]$Branches,
        [string]$OutputFile
    )

    Write-Host "[$WorkerId] Analyzing module: $Module" -ForegroundColor Blue

    "# Analysis Report for $Module" | Out-File $OutputFile
    "## Branches Analyzed" | Out-File $OutputFile -Append
    "" | Out-File $OutputFile -Append

    foreach ($branch in $Branches) {
        Write-Host "  Checking branch: $branch"
        "### Branch: $branch" | Out-File $OutputFile -Append

        # Check if module exists in branch
        $files = git ls-tree -r $branch --name-only 2>$null | Select-String $Module | Select-Object -First 10
        if ($files) {
            $files | Out-File $OutputFile -Append
        } else {
            "No matches found" | Out-File $OutputFile -Append
        }

        # Get recent commits
        "#### Recent Commits:" | Out-File $OutputFile -Append
        $commits = git log --oneline $branch -- "*$Module*" -10 2>$null
        if ($commits) {
            $commits | Out-File $OutputFile -Append
        } else {
            "No commits found" | Out-File $OutputFile -Append
        }
        "" | Out-File $OutputFile -Append
    }

    Write-Host "[$WorkerId] Analysis complete" -ForegroundColor Green
}

# Run parallel analysis
function Run-ParallelAnalysis {
    Write-Host "Starting parallel analysis with $Workers workers..." -ForegroundColor Yellow
    Write-Host ""

    # Create job scriptblocks for each worker
    $jobs = @()

    # Worker 1: MedCAT Core
    $jobs += Start-Job -ScriptBlock {
        param($WorkerId, $Module, $Branches, $OutputFile)
        Set-Location $using:PWD
        $analysis = @()
        foreach ($branch in $Branches) {
            $files = git ls-tree -r $branch --name-only 2>$null | Select-String $Module
            $commits = git log --oneline $branch -- "*$Module*" -10 2>$null
            $analysis += @{Branch=$branch; Files=$files; Commits=$commits}
        }
        $analysis | ConvertTo-Json | Out-File $OutputFile
    } -ArgumentList "Worker-1", "medcat-v2", @("origin/medcat/v2.3", "origin/medcat/v2.2", "development", "main"), "$AnalysisDir\medcat-core-analysis.json"

    # Worker 2: UI/Frontend
    $jobs += Start-Job -ScriptBlock {
        param($WorkerId, $Module, $Branches, $OutputFile)
        Set-Location $using:PWD
        $analysis = @()
        foreach ($branch in $Branches) {
            $files = git ls-tree -r $branch --name-only 2>$null | Select-String $Module
            $commits = git log --oneline $branch -- "*$Module*" -10 2>$null
            $analysis += @{Branch=$branch; Files=$files; Commits=$commits}
        }
        $analysis | ConvertTo-Json | Out-File $OutputFile
    } -ArgumentList "Worker-2", "trainer", @("myfork/development", "development", "main"), "$AnalysisDir\ui-frontend-analysis.json"

    # Worker 3: Search & NLP
    $jobs += Start-Job -ScriptBlock {
        param($WorkerId, $Module, $Branches, $OutputFile)
        Set-Location $using:PWD
        $analysis = @()
        foreach ($branch in $Branches) {
            $files = git ls-tree -r $branch --name-only 2>$null | Select-String $Module
            $commits = git log --oneline $branch -- "*$Module*" -10 2>$null
            $analysis += @{Branch=$branch; Files=$files; Commits=$commits}
        }
        $analysis | ConvertTo-Json | Out-File $OutputFile
    } -ArgumentList "Worker-3", "search", @("development", "myfork/development", "main"), "$AnalysisDir\search-nlp-analysis.json"

    # Worker 4: Infrastructure
    $jobs += Start-Job -ScriptBlock {
        param($WorkerId, $Module, $Branches, $OutputFile)
        Set-Location $using:PWD
        $analysis = @()
        foreach ($branch in $Branches) {
            $files = git ls-tree -r $branch --name-only 2>$null | Select-String -Pattern "docker|scripts|deploy"
            $commits = git log --oneline $branch -- "*docker*" "*scripts*" -10 2>$null
            $analysis += @{Branch=$branch; Files=$files; Commits=$commits}
        }
        $analysis | ConvertTo-Json | Out-File $OutputFile
    } -ArgumentList "Worker-4", "infrastructure", @("development", "main"), "$AnalysisDir\infrastructure-analysis.json"

    Write-Host "Waiting for all workers to complete..." -ForegroundColor Yellow
    $jobs | Wait-Job | Out-Null
    $jobs | Receive-Job
    $jobs | Remove-Job

    Write-Host "All workers completed analysis" -ForegroundColor Green
}

# Identify cherry-pick candidates
function Identify-Candidates {
    Write-Host "Identifying cherry-pick candidates..." -ForegroundColor Yellow

    $candidatesFile = "$ReportsDir\cherry-pick-candidates.txt"

    "# Cherry-Pick Candidates" | Out-File $candidatesFile
    "Generated: $(Get-Date)" | Out-File $candidatesFile -Append
    "" | Out-File $candidatesFile -Append

    "## High-Value Commits (last 30 days)" | Out-File $candidatesFile -Append

    # Find valuable commits
    $commits = git log --all --grep="feat\|fix\|perf\|security" --oneline --since="30 days ago" | Select-Object -First 50
    $commits | Out-File $candidatesFile -Append

    Write-Host "Candidates identified and saved to $candidatesFile" -ForegroundColor Green
}

# Create consolidation plan
function Create-ConsolidationPlan {
    Write-Host "Creating consolidation plan..." -ForegroundColor Yellow

    $planFile = "$ReportsDir\consolidation-plan.md"

    @"
# Consolidation Plan for $CurrentBranch
Generated: $(Get-Date)

## Summary
- Target Branch: $CurrentBranch
- Workers: $Workers
- Modules Analyzed: 8

## Merge Sequence
1. Documentation updates (no conflicts expected)
2. Test additions (minimal conflicts)
3. Infrastructure changes
4. Backend services
5. Frontend components
6. Clinical features
7. MedCAT core updates

## Parallel Execution Strategy
- Group 1 (Independent): Documentation, Tests
- Group 2 (Core): Backend, API
- Group 3 (UI): Frontend, Search
- Group 4 (Features): Clinical, Infrastructure
"@ | Out-File $planFile

    Write-Host "Consolidation plan created" -ForegroundColor Green
}

# Generate final report
function Generate-Report {
    Write-Host "Generating final report..." -ForegroundColor Yellow

    $reportFile = "$ReportsDir\final-report.md"

    @"
# CCPM Cherry-Pick Consolidation Report

## Execution Summary
- Date: $(Get-Date)
- Branch: $CurrentBranch
- Workers Used: $Workers

## Analysis Results

"@ | Out-File $reportFile

    # Append analysis results
    Get-ChildItem "$AnalysisDir\*.json" | ForEach-Object {
        "### $($_.BaseName)" | Out-File $reportFile -Append
        "Analysis file: $($_.Name)" | Out-File $reportFile -Append
        "" | Out-File $reportFile -Append
    }

    Write-Host "Report generated at $reportFile" -ForegroundColor Green
}

# Main execution
function Main {
    Write-Host "Starting CCPM Parallel Cherry-Pick Process"
    Write-Host "==========================================="
    Write-Host ""

    # Step 1: Check prerequisites
    Check-Prerequisites
    Write-Host ""

    # Step 2: Run parallel analysis
    Run-ParallelAnalysis
    Write-Host ""

    # Step 3: Identify candidates
    Identify-Candidates
    Write-Host ""

    # Step 4: Create consolidation plan
    Create-ConsolidationPlan
    Write-Host ""

    # Step 5: Generate report
    Generate-Report
    Write-Host ""

    Write-Host "========================================" -ForegroundColor Green
    Write-Host "CCPM Cherry-Pick Analysis Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:"
    Write-Host "1. Review analysis reports in: $AnalysisDir\"
    Write-Host "2. Review consolidation plan: $ReportsDir\consolidation-plan.md"
    Write-Host "3. Review candidates list: $ReportsDir\cherry-pick-candidates.txt"
    Write-Host "4. Execute cherry-picks using: .ccpm\execute-cherry-picks.ps1"
}

# Run main
Main