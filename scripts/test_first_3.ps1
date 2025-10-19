# Batch test script for parsing first 3 Word documents
# Run this from PowerShell

$pythonPath = "C:/Users/rndpi/AppData/Local/Programs/Python/Python314/python.exe"
$scriptPath = "scripts\docx_parser_simple.py"
$basePath = "\\DilgerNAS\Public\Media\Day NP Files"

# Get first 3 docx files
$files = Get-ChildItem -Path $basePath -Filter "*.docx" | Select-Object -First 3

Write-Host "`n============================================================"
Write-Host "BATCH PARSING TEST - First 3 Word Documents"
Write-Host "============================================================`n"

$successCount = 0
$errorCount = 0

foreach ($file in $files) {
    Write-Host "`n------------------------------------------------------------"
    Write-Host "Processing: $($file.Name)"
    Write-Host "------------------------------------------------------------"
    
    $fullPath = Join-Path $basePath $file.Name
    
    try {
        & $pythonPath $scriptPath $fullPath
        if ($LASTEXITCODE -eq 0) {
            $successCount++
        } else {
            $errorCount++
        }
    } catch {
        Write-Host "ERROR: $_" -ForegroundColor Red
        $errorCount++
    }
    
    Write-Host "`nPress Enter to continue to next file..."
    Read-Host
}

Write-Host "`n============================================================"
Write-Host "BATCH TEST COMPLETE"
Write-Host "============================================================"
Write-Host "Successfully parsed: $successCount"
Write-Host "Errors: $errorCount"
Write-Host "============================================================`n"
