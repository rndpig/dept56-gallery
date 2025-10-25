<#
Install git hooks into .git/hooks for this repository (Windows PowerShell)
Run from the repo root: .\scripts\git\install-hooks.ps1
#>

Param()

Write-Host "Installing git hooks..." -ForegroundColor Cyan

$repoRoot = (Get-Location).Path
$hooksDir = Join-Path $repoRoot ".git\hooks"
if (-not (Test-Path $hooksDir)) {
    Write-Error ".git/hooks not found. Are you in the repository root?"
    exit 1
}

$sourceHookPs1 = Join-Path $repoRoot "scripts\git\prevent_secrets_precommit.ps1"
$targetHook = Join-Path $hooksDir "pre-commit"

Write-Host "Copying PowerShell hook to $targetHook"
Set-Content -Path $targetHook -Value "#!/usr/bin/env pwsh`n`n# Auto-generated pre-commit wrapper to run PowerShell hook`n& pwsh -File '$sourceHookPs1'`n" -Encoding UTF8

# Make the wrapper executable (on Windows with Git Bash, ensure permissions)
try { icacls $targetHook /grant '*S-1-1-0:(RX)' } catch { }

Write-Host "Installing optional POSIX hook for Unix environments..."
$sourceHookSh = Join-Path $repoRoot "scripts\git\prevent_secrets_precommit.sh"
if (Test-Path $sourceHookSh) {
    $targetHookSh = Join-Path $hooksDir "pre-commit.sh"
    Copy-Item -Force $sourceHookSh $targetHookSh
    # Create a small wrapper to call the shell script if /bin/sh exists
    Set-Content -Path $targetHook -Value "#!/usr/bin/env bash`n`nSCRIPT_DIR=\"$(dirname \"$0\")\"`nif command -v bash >/dev/null 2>&1; then \"$SCRIPT_DIR/pre-commit.sh\"; else echo 'No bash found - skipping shell hook'; fi" -Encoding UTF8
    & git update-index --add --chmod=+x $targetHook
    & git update-index --add --chmod=+x $targetHookSh
}

Write-Host "Hooks installed. To uninstall, remove files from .git/hooks/pre-commit and .git/hooks/pre-commit.sh" -ForegroundColor Green
