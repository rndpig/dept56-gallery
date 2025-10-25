<#
PowerShell helper to prepare commands for scrubbing secrets with git-filter-repo.
This script does NOT rewrite history itself; it previews the commands and offers
to run them. Use with caution.

Prerequisites:
- python -m pip install git-filter-repo
- Make sure you have a backup and that all collaborators know you'll rewrite history
#>

Param(
    [switch]$Run
)

Write-Host "This script helps you remove files/strings from git history using git-filter-repo." -ForegroundColor Cyan

$repoRoot = (Get-Location).Path

Write-Host "Creating a safety backup branch 'backup-main'..."
& git branch -f backup-main

Write-Host "Recommended steps:" -ForegroundColor Yellow
Write-Host "1) Rotate any exposed secrets in external services immediately."
Write-Host "2) Ensure all collaborators know to re-clone after history rewrite."
Write-Host "3) This script will run git-filter-repo to remove specific files or patterns."

Write-Host "\nExample: Remove a committed file completely (vercel.env) from history:" -ForegroundColor Green
Write-Host "git filter-repo --path vercel.env --invert-paths"

Write-Host "\nExample: Remove a specific token string across history (dangerous):" -ForegroundColor Green
Write-Host "git filter-repo --replace-refs delete-no-add --path-rename : --invert-paths --refs refs/heads/main --replace-text replacements.txt"

Write-Host "\nIf you pass -Run, this script will execute the 'vercel.env' removal command now." -ForegroundColor Cyan
if ($Run) {
    Write-Host "Running: git filter-repo --path vercel.env --invert-paths" -ForegroundColor Red
    & git filter-repo --path vercel.env --invert-paths
    Write-Host "Done. You must force-push the rewritten history:" -ForegroundColor Yellow
    Write-Host "git push --force --all && git push --force --tags"
}
