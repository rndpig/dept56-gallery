<#
PowerShell pre-commit hook for Windows environments.
Scans staged files for JWT-like tokens, private key blocks, and common secret variable names.
Exits with non-zero code to block the commit when a match is found.
#>

param()

Write-Host "Running secret-scan pre-commit hook (PowerShell)..."

$patterns = @(
    'eyJ[A-Za-z0-9_-]{10,}',
    '-----BEGIN PRIVATE KEY-----',
    'SUPABASE_SERVICE_ROLE_KEY',
    'AWS_SECRET_ACCESS_KEY'
)

$found = $false

$files = git diff --cached --name-only --diff-filter=ACM
foreach ($file in $files) {
    if (-not (Test-Path $file)) { continue }
    try {
        $content = Get-Content -Raw -ErrorAction Stop $file
    } catch {
        continue
    }
    foreach ($pat in $patterns) {
        if ($content -match $pat) {
            Write-Host "Potential secret found in $file (pattern: $pat)" -ForegroundColor Yellow
            $found = $true
        }
    }
}

if ($found) {
    Write-Host "\nCommit blocked: potential secret(s) found in staged files." -ForegroundColor Red
    Write-Host "If these are false positives, fix the files or use: git commit -n" -ForegroundColor Yellow
    exit 1
}

Write-Host "Secret-scan passed. Proceeding with commit." -ForegroundColor Green
exit 0
