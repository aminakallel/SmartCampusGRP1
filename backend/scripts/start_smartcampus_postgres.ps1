$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$dataDirectory = Join-Path $projectRoot '.smartcampus_pgdata'
$logFile = Join-Path $projectRoot '.smartcampus_pg.log'
$defaultBin = 'C:\Program Files\Odoo 19.0.20260202\PostgreSQL\bin'
$postgresBin = if ($env:SMARTCAMPUS_PG_BIN) { $env:SMARTCAMPUS_PG_BIN } else { $defaultBin }
$initFile = Join-Path $dataDirectory 'PG_VERSION'

if (-not (Test-Path -LiteralPath $initFile -PathType Leaf)) {
    throw "Existing SmartCampus cluster not found at $dataDirectory. This script never initializes a cluster."
}

$pgCtl = Join-Path $postgresBin 'pg_ctl.exe'
$postgres = Join-Path $postgresBin 'postgres.exe'
if (-not (Test-Path -LiteralPath $pgCtl -PathType Leaf) -or -not (Test-Path -LiteralPath $postgres -PathType Leaf)) {
    throw "PostgreSQL binaries not found in $postgresBin. Set SMARTCAMPUS_PG_BIN to the PostgreSQL bin directory."
}

$clusterMajor = (Get-Content -LiteralPath $initFile -Raw).Trim()
$versionText = (& $postgres --version | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $versionText -notmatch 'PostgreSQL\)\s+(\d+)\.') {
    throw "Could not determine PostgreSQL binary version: $versionText"
}
if ($Matches[1] -ne $clusterMajor) {
    throw "Cluster major version $clusterMajor does not match binary version $($Matches[1]); refusing to start."
}

$env:PATH = "$postgresBin;$env:PATH"
$status = & $pgCtl -D $dataDirectory status 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Output ($status | Out-String).Trim()
    exit 0
}

& $pgCtl -D $dataDirectory -l $logFile -o '-h 127.0.0.1 -p 55432' start
if ($LASTEXITCODE -ne 0) {
    throw "PostgreSQL could not start. Review $logFile; the data directory was not reinitialized or deleted."
}
