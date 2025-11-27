[CmdletBinding()]
param(
    [string]$LogPath = "VALIDATION_LOG.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $repoRoot

if (-not (Test-Path ".venv/")) {
    throw "Missing .venv virtual environment. Run 'python -m venv .venv' first."
}

. ./.venv/Scripts/Activate.ps1

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$displayTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss K"
$logsRoot = Join-Path $repoRoot "logs/verify/$timestamp"
New-Item -ItemType Directory -Path $logsRoot -Force | Out-Null

$summary = New-Object System.Collections.Generic.List[string]
$containerName = "labos-verify"
$script:containerId = $null

function Invoke-Step {
    param(
        [string]$Label,
        [string]$LogName,
        [ScriptBlock]$Action
    )

    $logPath = Join-Path $logsRoot $LogName
    Write-Host "[verify] $Label"
    $relativeLog = Join-Path (Join-Path 'logs/verify' $timestamp) $LogName
    try {
        $previousPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"

        Set-Variable -Name LASTEXITCODE -Value 0 -Scope Global
        & $Action 2>&1 | Tee-Object -FilePath $logPath | Out-Null
        $pipelineSucceeded = $?
        $nativeExitCode = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 0 }

        if (-not $pipelineSucceeded -or $nativeExitCode -ne 0) {
            throw "Step failed with exit code $nativeExitCode"
        }

        $status = "SUCCESS"
    } catch {
        $_ | Out-String | Add-Content -Path $logPath
        $status = "FAILED"
        $summary.Add("- [$status] $Label ($relativeLog)")
        throw
    } finally {
        if ($null -ne $previousPreference) {
            $ErrorActionPreference = $previousPreference
        }
    }

    $summary.Add("- [$status] $Label ($relativeLog)")
}

function Stop-VerifyContainer {
    if ($script:containerId) {
        Write-Host "[verify] Stopping container $containerName ($($script:containerId.Substring(0,12)))"
        docker stop $script:containerId | Out-Null
        $script:containerId = $null
    }
}

try {
    Invoke-Step "Build labos-dev image" "01_docker_build.log" { docker build --progress=plain -t labos-dev . }
    Invoke-Step "Run unit tests" "02_unit_tests.log" { python -m unittest }
    Invoke-Step "Rate Dockerfile with Gordon" "03_docker_ai_rate.log" { docker ai rate my Dockerfile }

    Invoke-Step "Start Streamlit container" "04_container_start.log" {
        $existing = docker ps -aq -f "name=^$containerName$"
        if ($existing) {
            docker rm -f $containerName | Out-Null
        }
        $script:containerId = docker run -d --rm --name $containerName -p 48501:8501 labos-dev
        $script:containerId
    }

    Invoke-Step "Analyze running container with Gordon" "05_docker_ai_analyze.log" {
        if (-not $script:containerId) { throw "Container not running" }
        docker ai "Analyze my running container with ID $script:containerId"
    }

    Stop-VerifyContainer

    Invoke-Step "Scan image with Docker Scout" "06_docker_scout.log" {
        docker scout cves labos-dev:latest --only-severity critical,high
    }

    Invoke-Step "Log compose helper availability" "07_compose_helper.log" {
        docker compose run --rm docker-scout version
    }

} finally {
    Stop-VerifyContainer
}

"" | Add-Content -Path $LogPath
"## $displayTime - self reviewed" | Add-Content -Path $LogPath
foreach ($line in $summary) {
    Add-Content -Path $LogPath -Value $line
}
"" | Add-Content -Path $LogPath

Write-Host "[verify] Complete. Detailed logs: $logsRoot"
