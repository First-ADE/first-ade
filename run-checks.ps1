#!/usr/bin/env pwsh
<#!
.SYNOPSIS
  Unified Quality & Compliance Gates Orchestrator for First-ADE

.DESCRIPTION
  This script executes a comprehensive suite of quality, styling, and compliance checks:
    1. Scan for unresolved Git merge conflict markers (aggressive fail-early).
    2. Run Ruff format and lint checks (supporting auto-fixes via -Fix).
    3. Run Mypy strict type-safety checks.
    4. Run pytest suite.
    5. Run ade-compliance checks.

.PARAMETER Fix
  Auto-fix formatting and linting errors where supported.

.EXAMPLE
  ./run-checks.ps1

.EXAMPLE
  ./run-checks.ps1 -Fix
#>

[CmdletBinding()]
param(
    [switch]$Fix,
    [switch]$Help
)

$ErrorActionPreference = 'Continue'

# UTF-8 Encoding enforcement for PowerShell console output
if ($PSVersionTable.PSVersion.Major -ge 5) {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
}

if ($Help) {
    Write-Host "Usage: ./run-checks.ps1 [-Fix] [-Help]" -ForegroundColor Cyan
    Write-Host "  -Fix   Run auto-fixers for linting and formatting (ruff check --fix, ruff format)"
    Write-Host "  -Help  Show this help message"
    exit 0
}

# Terminal helper functions
function Write-Header {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Write-Status {
    param(
        [string]$Name,
        [string]$Status, # PASS, FAIL, SKIP, WARN
        [string]$Details = ""
    )
    $color = "White"
    $symbol = " "
    switch ($Status) {
        "PASS" { $color = "Green"; $symbol = "v" }
        "FAIL" { $color = "Red"; $symbol = "x" }
        "WARN" { $color = "Yellow"; $symbol = "!" }
        "SKIP" { $color = "Gray"; $symbol = "-" }
    }
    
    $padName = $Name.PadRight(30)
    $padStatus = "[$Status]".PadRight(8)
    
    Write-Host "  [$symbol] $padName " -NoNewline
    Write-Host $padStatus -ForegroundColor $color -NoNewline
    if ($Details) {
        Write-Host " - $Details" -ForegroundColor Gray
    } else {
        Write-Host ""
    }
}

# --- GATE 1: Git Conflict Marker Scanning (Fail-Early) ---
Write-Header "Gate 1: Scanning for Git Conflict Markers"
$unresolvedConflicts = @()

$scanPatterns = @("*.py", "*.md", "*.json", "*.yml", "*.yaml", "*.toml", "*.sh", "*.ps1")
$excludeDirs = @(".venv", "venv", ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache")

$filesToScan = Get-ChildItem -Path . -Recurse -File | Where-Object {
    $file = $_
    $relative = $file.FullName.Replace((Get-Location).Path, "").TrimStart("\").TrimStart("/")
    
    # Check exclusion list
    $exclude = $false
    foreach ($dir in $excludeDirs) {
        if ($relative -match "^$dir" -or $relative -match "[\\/]$dir[\\/]") {
            $exclude = $true
            break
        }
    }
    
    # Check extension pattern list
    $matchPattern = $false
    if (-not $exclude) {
        foreach ($pattern in $scanPatterns) {
            if ($file.Name -like $pattern) {
                $matchPattern = $true
                break
            }
        }
    }
    
    $matchPattern -and -not $exclude
}

foreach ($file in $filesToScan) {
    $lineNum = 1
    $lines = Get-Content -LiteralPath $file.FullName -ErrorAction SilentlyContinue
    if ($null -eq $lines) { continue }
    
    foreach ($line in $lines) {
        if ($line -match "^<<<<<<<" -or $line -match "^=======" -or $line -match "^>>>>>>>") {
            $unresolvedConflicts += [PSCustomObject]@{
                File = $file.FullName.Replace((Get-Location).Path, "").TrimStart("\").TrimStart("/")
                Line = $lineNum
                Content = $line.Trim()
            }
        }
        $lineNum++
    }
}

if ($unresolvedConflicts.Count -gt 0) {
    Write-Host "CRITICAL: Leftover Git merge conflict markers detected in your files!" -ForegroundColor Red
    foreach ($conflict in $unresolvedConflicts) {
        Write-Host "  - File: $($conflict.File) at line $($conflict.Line): '$($conflict.Content)'" -ForegroundColor Yellow
    }
    Write-Host "`nAborting checks. Please resolve all conflict markers before running checks again.`n" -ForegroundColor Red
    exit 1
} else {
    Write-Host "  [v] No Git conflict markers found." -ForegroundColor Green
}

# Results Tracker
$results = [ordered]@{
    "Git Conflict Scan"   = "PASS"
    "Ruff Formatting"     = "SKIP"
    "Ruff Linting"        = "SKIP"
    "Mypy Strict Typing"  = "SKIP"
    "Pytest Suite"        = "SKIP"
    "ADE Compliance Gate" = "SKIP"
}
$details = @{}

# --- GATE 2: Ruff Formatter ---
Write-Header "Gate 2: Ruff Code Formatting"
if ($Fix) {
    Write-Host "Running Ruff formatter..." -ForegroundColor Gray
    uv run ruff format .
    if ($LASTEXITCODE -eq 0) {
        $results["Ruff Formatting"] = "PASS"
        $details["Ruff Formatting"] = "Auto-formatted successfully"
    } else {
        $results["Ruff Formatting"] = "FAIL"
        $details["Ruff Formatting"] = "Format operation failed"
    }
} else {
    Write-Host "Checking code formatting (dry-run)..." -ForegroundColor Gray
    uv run ruff format --check .
    if ($LASTEXITCODE -eq 0) {
        $results["Ruff Formatting"] = "PASS"
    } else {
        $results["Ruff Formatting"] = "FAIL"
        $details["Ruff Formatting"] = "Formatting violations detected. Run with -Fix to auto-format."
    }
}

# --- GATE 3: Ruff Linter ---
Write-Header "Gate 3: Ruff Linter"
if ($Fix) {
    Write-Host "Running Ruff linter with auto-fixes..." -ForegroundColor Gray
    uv run ruff check . --fix
    if ($LASTEXITCODE -eq 0) {
        $results["Ruff Linting"] = "PASS"
        $details["Ruff Linting"] = "Linted and auto-fixed issues"
    } else {
        $results["Ruff Linting"] = "FAIL"
        $details["Ruff Linting"] = "Linter failures remaining"
    }
} else {
    Write-Host "Running Ruff linter check..." -ForegroundColor Gray
    uv run ruff check .
    if ($LASTEXITCODE -eq 0) {
        $results["Ruff Linting"] = "PASS"
    } else {
        $results["Ruff Linting"] = "FAIL"
        $details["Ruff Linting"] = "Linter errors detected. Run with -Fix to resolve auto-fixable issues."
    }
}

# --- GATE 4: Mypy Strict Typechecking ---
Write-Header "Gate 4: Mypy Strict Typechecking"
Write-Host "Running strict type-checking on src/..." -ForegroundColor Gray
uv run mypy src/
if ($LASTEXITCODE -eq 0) {
    $results["Mypy Strict Typing"] = "PASS"
} else {
    $results["Mypy Strict Typing"] = "FAIL"
    $details["Mypy Strict Typing"] = "Type-checking errors detected in src/"
}

# --- GATE 5: Pytest Execution ---
Write-Header "Gate 5: Pytest Suite"
Write-Host "Running test suite with pytest..." -ForegroundColor Gray
uv run pytest
if ($LASTEXITCODE -eq 0) {
    $results["Pytest Suite"] = "PASS"
} else {
    $results["Pytest Suite"] = "FAIL"
    $details["Pytest Suite"] = "One or more tests failed"
}

# --- GATE 6: ADE Compliance Gateway ---
Write-Header "Gate 6: ADE Compliance Framework Checks"
Write-Host "Running compliance orchestrator..." -ForegroundColor Gray
uv run ade-compliance check-all src/
$adeCode = $LASTEXITCODE
if ($adeCode -eq 0) {
    $results["ADE Compliance Gate"] = "PASS"
    $details["ADE Compliance Gate"] = "All axioms compliant"
} elseif ($adeCode -eq 2) {
    $results["ADE Compliance Gate"] = "WARN"
    $details["ADE Compliance Gate"] = "Compliance warnings detected"
} else {
    $results["ADE Compliance Gate"] = "FAIL"
    $details["ADE Compliance Gate"] = "Compliance violations or framework error detected (code $adeCode)"
}

# --- FINAL REPORT DASHBOARD ---
Write-Host "`n"
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "       QUALITY & COMPLIANCE REPORT       " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$anyFail = $false
foreach ($gate in $results.Keys) {
    $status = $results[$gate]
    $desc = $details[$gate]
    Write-Status -Name $gate -Status $status -Details $desc
    if ($status -eq "FAIL") { $anyFail = $true }
}

Write-Host "=========================================" -ForegroundColor Cyan

if ($anyFail) {
    Write-Host " STATUS: QUALITY GATES FAILED " -ForegroundColor Red -BackgroundColor Black
    Write-Host "Please resolve the errors highlighted above before proposing a merge.`n" -ForegroundColor Red
    exit 1
} else {
    Write-Host " STATUS: ALL GATES PASSING! " -ForegroundColor Green -BackgroundColor Black
    Write-Host "Your changes conform to First-ADE code quality and compliance standards.`n" -ForegroundColor Green
    exit 0
}
