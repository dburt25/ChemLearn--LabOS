#!/usr/bin/env pwsh
<#
.SYNOPSIS
Fast local verification script for ChemLearn LabOS development.

.DESCRIPTION
Runs unit tests and import checks without Docker overhead.
Appends results to VALIDATION_LOG.md with timestamp.

.PARAMETER LogPath
Path to validation log file. Default: VALIDATION_LOG.md

.EXAMPLE
.\scripts\verify-local.ps1
#>

param(
    [string]$LogPath = "VALIDATION_LOG.md"
)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss K"

Write-Host "`n[verify] Running unit tests..." -ForegroundColor Cyan
python -m unittest discover -s tests
if ($LASTEXITCODE -ne 0) {
    Write-Host "[verify] ✗ Tests failed" -ForegroundColor Red
    throw "Unit tests failed with exit code $LASTEXITCODE"
}

Write-Host "`n[verify] Checking import integrity..." -ForegroundColor Cyan
python -c "from labos.runtime import LabOSRuntime; from labos.modules import get_registry; print('✓ Imports OK')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[verify] ✗ Import checks failed" -ForegroundColor Red
    throw "Import validation failed with exit code $LASTEXITCODE"
}

Write-Host "`n[verify] Recording validation..." -ForegroundColor Cyan
"" | Add-Content -Path $LogPath
"## $timestamp - local dev verification" | Add-Content -Path $LogPath
"- [SUCCESS] Unit tests passed ($(Get-ChildItem tests\test_*.py | Measure-Object | Select-Object -ExpandProperty Count) test files)" | Add-Content -Path $LogPath
"- [SUCCESS] Import checks passed" | Add-Content -Path $LogPath
"" | Add-Content -Path $LogPath

Write-Host "[verify] ✓ All checks passed" -ForegroundColor Green
Write-Host "[verify] Validation logged to $LogPath" -ForegroundColor Gray
