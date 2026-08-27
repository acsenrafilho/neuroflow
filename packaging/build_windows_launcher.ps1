# Build NeuroFlow Windows release zip: launcher + Linux portal payload.
# Usage (CI): pwsh -File packaging/build_windows_launcher.ps1
# Requires NEUROFLOW_LINUX_PAYLOAD (or -LinuxPayload) pointing at the Linux onedir.
param(
  [string]$LinuxPayload = $env:NEUROFLOW_LINUX_PAYLOAD
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLower()
if ($Arch -ne "x64") {
  Write-Error "Windows release zip is x86_64 only (got architecture: $Arch). ARM is out of scope."
  exit 1
}

if ($env:NEUROFLOW_VERSION) {
  $Version = $env:NEUROFLOW_VERSION
} else {
  $Version = (poetry version -s).Trim()
}

if (-not $LinuxPayload) {
  Write-Error "Set NEUROFLOW_LINUX_PAYLOAD or pass -LinuxPayload to the Linux portal onedir (neuroflow + _internal/)."
  exit 1
}
if (-not (Test-Path -LiteralPath $LinuxPayload -PathType Container)) {
  Write-Error "Linux payload directory not found: $LinuxPayload"
  exit 1
}

$OutDir = Join-Path $Root "dist/release"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Write-Host "Running PyInstaller (Windows WSL launcher)..."
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Root "build/NeuroFlow")
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Root "build/windows_launcher")
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Root "dist/NeuroFlow")
poetry run pyinstaller --noconfirm --clean packaging/windows_launcher.spec

$LauncherOnedir = Join-Path $Root "dist/NeuroFlow"
if (-not (Test-Path -LiteralPath (Join-Path $LauncherOnedir "NeuroFlow.exe"))) {
  Write-Error "PyInstaller did not produce dist/NeuroFlow/NeuroFlow.exe"
  exit 1
}

Write-Host "Assembling Windows zip (launcher + linux-payload)..."
poetry run python packaging/assemble_windows_release.py `
  --linux-onedir $LinuxPayload `
  --launcher-onedir $LauncherOnedir `
  --version $Version `
  --output-dir $OutDir `
  --readme (Join-Path $Root "packaging/README-WINDOWS.txt")

Write-Host "Done. Artifacts under $OutDir"
