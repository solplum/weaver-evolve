param(
  [Parameter(Mandatory = $true)][string]$Dest,
  [switch]$All,
  [switch]$Force,
  [switch]$DryRun
)
$ErrorActionPreference = "Stop"
$installerArgs = @((Join-Path $PSScriptRoot "scripts/install.py"), "--dest", $Dest)
if ($All) { $installerArgs += "--all" }
if ($Force) { $installerArgs += "--force" }
if ($DryRun) { $installerArgs += "--dry-run" }
if (Get-Command py -ErrorAction SilentlyContinue) {
  & py -3 @installerArgs
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
  & python3 @installerArgs
} else {
  & python @installerArgs
}
exit $LASTEXITCODE
