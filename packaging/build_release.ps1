# Build NeuroFlow release zip (Windows CI / local).
# Usage: powershell -File packaging/build_release.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if ($env:NEUROFLOW_VERSION) {
  $Version = $env:NEUROFLOW_VERSION
} else {
  $Version = (poetry version -s).Trim()
}

$OsLabel = "windows"
$Arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLower()
if ($Arch -eq "x64") { $ArchLabel = "x86_64" }
elseif ($Arch -eq "arm64") { $ArchLabel = "arm64" }
else { $ArchLabel = $Arch }

$OutDir = Join-Path $Root "dist/release"
$ZipName = "neuroflow-$Version-$OsLabel-$ArchLabel.zip"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Write-Host "Building frontend..."
Push-Location frontend
npm ci
npm run build
Pop-Location

Write-Host "Running PyInstaller..."
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Root "build/neuroflow")
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Root "dist/neuroflow")
poetry run pyinstaller --noconfirm --clean packaging/neuroflow.spec

Write-Host "Creating $ZipName..."
$ZipPath = Join-Path $OutDir $ZipName
if (Test-Path $ZipPath) { Remove-Item $ZipPath }
Compress-Archive -Path (Join-Path $Root "dist/neuroflow") -DestinationPath $ZipPath
Write-Host "Built $ZipPath"
