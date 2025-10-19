# Project Cleanup Plan

## Files Safe to Delete (No Longer Needed for Production)

### 1. Historical SQL Migration Files (Keep Only Essential)
These were one-time migrations already applied:
- ❌ `add_description_field.sql`
- ❌ `add_price_field.sql`
- ❌ `add_retired_year_field.sql`
- ❌ `add_sku_field.sql`
- ❌ `check_duplicates.sql`
- ❌ `cleanup_imported_text.sql`
- ❌ `diagnose_duplicates.sql`
- ❌ `fix_duplicates.sql`
- ❌ `fix_rls_policies.sql`
- ❌ `verify_deployment.sql`
- ✅ **KEEP:** `setup_auth_rls_policies.sql` (reference for RLS setup)
- ✅ **KEEP:** `supabase-schema.sql` (full schema reference)
- ✅ **KEEP:** `clear_database.sql` (useful for future resets)
- ✅ **KEEP:** `migration_add_all_fields.sql` (comprehensive migration)

### 2. Development/Process Documentation (Archive)
These documented the development process but aren't needed now:
- ❌ `CLEANUP_GUIDE.md`
- ❌ `CLEANUP_PLAN.md`
- ❌ `CLEANUP_SUMMARY.md`
- ❌ `CODE_IMPROVEMENTS.md`
- ❌ `DELETE_FEATURE.md`
- ❌ `DUPLICATE_DIAGNOSIS.md`
- ❌ `DUPLICATE_FIX_SUMMARY.md`
- ❌ `FORM_LAYOUT_UPDATE.md`
- ❌ `FRONTEND_UPDATE.md`
- ❌ `IMPORT_BUG_DIAGNOSIS.md`
- ❌ `IMPORT_BUG_FIX.md`
- ❌ `IMPORT_DUPLICATE_PREVENTION_SUMMARY.md`
- ❌ `MISCLASSIFIED_FIX_COMPLETE.md`
- ❌ `MISCLASSIFIED_ITEMS.md`
- ❌ `PARSER_TEST_RESULTS.md`
- ❌ `RECENT_UPDATES.md`
- ❌ `SCHEMA_CHANGES.md`
- ❌ `SCRAPING_PLAN.md`
- ❌ `UI_LAYOUT_UPDATE.md`

### 3. Linking Reports (Temporary Data)
- ❌ `linking_report_20251018_102001.json`
- ❌ `linking_report_20251018_102011.json`

### 4. PowerShell Deploy Script (Not Needed with Vercel)
- ❌ `deploy.ps1`

### 5. Python Cache
- ❌ `__pycache__/` (should already be in .gitignore)

### 6. Duplicate Deployment Docs (Consolidate)
- ❌ `PRODUCTION_DEPLOYMENT.md` (old version)
- ❌ `DEPLOYMENT_COMPLETE.md` (old version)
- ✅ **KEEP:** `DEPLOY_QUICK_START.md` (quickest guide)
- ✅ **KEEP:** `VERCEL_DEPLOYMENT.md` (comprehensive)
- ✅ **KEEP:** `DEPLOYMENT_CHECKLIST.md` (useful reference)
- ✅ **KEEP:** `DEPLOYMENT_READY.md` (ingestion guide)

### 7. Output Directories (Not Needed in Git)
- ❌ `ingestion_output/` (add to .gitignore if not already)
- ❌ `parsed_output/` (add to .gitignore if not already)

### 8. Python Scripts (Archive - Keep for Future Maintenance)
Move to `scripts/archive/` or keep as-is for future data updates:
- ✅ **KEEP ALL SCRIPTS** - Useful if you need to re-import or fix data

---

## Files to KEEP (Essential)

### Core Application
- ✅ `src/` - Your React app
- ✅ `index.html` - Entry point
- ✅ `package.json` - Dependencies
- ✅ `package-lock.json` - Lock file
- ✅ `vite.config.ts` - Build config
- ✅ `vercel.json` - Deployment config
- ✅ `tsconfig.json` - TypeScript config
- ✅ `tsconfig.node.json` - TypeScript config
- ✅ `tailwind.config.js` - Styling
- ✅ `postcss.config.js` - CSS processing

### Environment & Config
- ✅ `.env` - Local environment (not in git)
- ✅ `.env.example` - Template
- ✅ `.env.production` - Production template (not in git)
- ✅ `.gitignore` - Git ignore rules
- ✅ `vercel.env` - Vercel env template

### Documentation (Keep Essential)
- ✅ `README.md` - Main documentation
- ✅ `QUICKSTART.md` - Quick start guide
- ✅ `AUTH_IMPLEMENTATION_SUMMARY.md` - Auth reference
- ✅ `GOOGLE_AUTH_SETUP.md` - OAuth setup guide
- ✅ `GITHUB_SETUP.md` - GitHub guide
- ✅ `INGESTION_GUIDE.md` - Data import guide
- ✅ `DEPLOY_QUICK_START.md` - Deployment
- ✅ `VERCEL_DEPLOYMENT.md` - Detailed deployment
- ✅ `VERCEL_ENV_SETUP.md` - Environment setup
- ✅ `DEPLOYMENT_CHECKLIST.md` - Deployment checklist
- ✅ `DEPLOYMENT_READY.md` - Production ready doc

### Database & Scripts
- ✅ `setup_auth_rls_policies.sql` - RLS setup reference
- ✅ `supabase-schema.sql` - Schema reference
- ✅ `clear_database.sql` - Reset utility
- ✅ `migration_add_all_fields.sql` - Migration reference
- ✅ `scripts/` - Keep all for future maintenance

---

## Recommended Actions

1. **Delete obsolete files** (listed above)
2. **Update .gitignore** to exclude output directories
3. **Keep scripts** for future data maintenance
4. **Archive development docs** or delete if confident

---

## Safety Note

All files marked for deletion are safely in git history if you ever need them back!
