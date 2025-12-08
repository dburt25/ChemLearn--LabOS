[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$imageName = if ($env:LABOS_IMAGE) { $env:LABOS_IMAGE } else { "labos-dev" }
$port = if ($env:LABOS_PORT) { $env:LABOS_PORT } else { "8501" }
$workdir = if ($env:LABOS_WORKDIR) { $env:LABOS_WORKDIR } else { "/labos" }

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not (Test-Path (Join-Path $repoRoot "Dockerfile"))) {
    Write-Error "Unable to locate the repository root adjacent to this script."
    exit 1
}

$commandToRun = if ($args.Count -gt 0) { $args -join " " } else { $null }

Write-Host "[docker-run] Building image $imageName ..."
docker build -t $imageName $repoRoot

Write-Host "[docker-run] Starting container on port $port ..."
if (-not $commandToRun) {
    docker run `
      --rm `
      -it `
      -p "$port:8501" `
      -v "$repoRoot:$workdir" `
      $imageName `
      /bin/bash
} else {
    docker run `
      --rm `
      -it `
      -p "$port:8501" `
      -v "$repoRoot:$workdir" `
      $imageName `
      /bin/bash -lc "$commandToRun"
}
