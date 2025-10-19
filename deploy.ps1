# Production Deployment Script
# Run this to execute the complete deployment

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DEPT 56 GALLERY - PRODUCTION DEPLOYMENT" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Apply Database Migration
Write-Host "[STEP 1] Database Migration" -ForegroundColor Yellow
Write-Host "Action Required: Go to Supabase SQL Editor and run:" -ForegroundColor White
Write-Host "  1. migration_add_all_fields.sql" -ForegroundColor Green
Write-Host ""
$continue = Read-Host "Have you applied the migration? (y/n)"
if ($continue -ne 'y') {
    Write-Host "Please apply the migration first, then run this script again." -ForegroundColor Red
    exit
}

# Step 2: Clear Database
Write-Host "`n[STEP 2] Clear Database" -ForegroundColor Yellow
Write-Host "WARNING: This will delete ALL existing data!" -ForegroundColor Red
Write-Host "Action Required: Go to Supabase SQL Editor and run:" -ForegroundColor White
Write-Host "  1. clear_database.sql" -ForegroundColor Green
Write-Host ""
$continue = Read-Host "Have you cleared the database? (y/n)"
if ($continue -ne 'y') {
    Write-Host "Please clear the database first, then run this script again." -ForegroundColor Red
    exit
}

# Step 3: Parse and Upload Documents
Write-Host "`n[STEP 3] Batch Process Documents" -ForegroundColor Yellow
Write-Host "Processing all Word documents..." -ForegroundColor White
Write-Host ""

$docsPath = "\\DilgerNAS\Public\Media\Day NP Files"
Write-Host "Documents directory: $docsPath" -ForegroundColor Cyan

# Count documents
$docCount = (Get-ChildItem "$docsPath" -Filter "*.docx" | Where-Object { -not $_.Name.StartsWith("~$") }).Count
Write-Host "Found $docCount documents to process" -ForegroundColor Green
Write-Host ""

$confirm = Read-Host "Start batch processing? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit
}

Write-Host "`nStarting batch process..." -ForegroundColor Cyan
python.exe scripts\batch_process.py "$docsPath"

# Check if successful
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green
    
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Check parsed_output/upload_summary.json for results" -ForegroundColor White
    Write-Host "2. Review parsed_output/images/ directory" -ForegroundColor White
    Write-Host "3. Verify data in Supabase dashboard" -ForegroundColor White
    Write-Host "4. Upload images to Supabase Storage (manual step)" -ForegroundColor White
} else {
    Write-Host "`n❌ Deployment failed. Check errors above." -ForegroundColor Red
}
