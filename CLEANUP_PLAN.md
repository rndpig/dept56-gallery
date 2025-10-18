# Project Cleanup Plan

Generated: October 18, 2025

## Executive Summary

This document outlines a comprehensive cleanup plan for the Department 56 Gallery App project, identifying files that can be safely removed and proposing code improvements.

---

## 📂 File Categories

### ✅ Core Production Files (KEEP)
**Frontend Application:**
- `src/` - React/TypeScript application
  - `App.tsx` - Main app with auth wrapper
  - `DeptApp.tsx` - Main gallery component
  - `main.tsx` - Entry point
  - `components/Auth.tsx` - Authentication component
  - `lib/supabase.ts` - Supabase client
  - `lib/database.ts` - Database service layer
  - `types/database.ts` - TypeScript types
  - `index.css` - Global styles
- `index.html` - HTML entry point
- `vite.config.ts` - Vite configuration
- `tsconfig.json`, `tsconfig.node.json` - TypeScript config
- `tailwind.config.js` - Tailwind CSS config
- `postcss.config.js` - PostCSS config
- `package.json`, `package-lock.json` - Dependencies

**Database:**
- `supabase-schema.sql` - Complete database schema

**Configuration:**
- `.env.example` - Template for environment variables
- `.gitignore` - Git ignore rules

**Documentation:**
- `README.md` - Main documentation
- `QUICKSTART.md` - Quick start guide
- `GITHUB_SETUP.md` - GitHub setup instructions
- `INGESTION_GUIDE.md` - Data ingestion guide
- `SCRAPING_PLAN.md` - Web scraping documentation

### 🛠️ Useful Utility Scripts (KEEP - But Organize)
**Data Ingestion:**
- `ingest_docx.py` - Import data from Word documents
- `requirements-ingest.txt` - Dependencies for ingestion

**Web Scraping:**
- `scraper_prototype.py` - Web scraping tool
- `requirements-scraper.txt` - Dependencies for scraping

**Database Maintenance:**
- `analyze_duplicates_v3.py` - Duplicate detection (latest version)
- `generate_cleanup_plan.py` - Generate cleanup plans
- `execute_cleanup.py` - Execute cleanup operations

### ❌ Files to DELETE

#### One-Time Analysis/Debug Files
These were created for specific debugging sessions and are no longer needed:

**Duplicate Analysis Results (10 files):**
- `duplicate_analysis.json` ⚠️ DELETE
- `duplicate_analysis_full.json` ⚠️ DELETE
- `duplicate_analysis_20251018_093616.json` ⚠️ DELETE
- `duplicate_analysis_20251018_093646.json` ⚠️ DELETE
- `duplicate_analysis_20251018_093712.json` ⚠️ DELETE
- `duplicate_analysis_20251018_094604.json` ⚠️ DELETE
- `duplicate_analysis_20251018_094657.json` ⚠️ DELETE
- `duplicate_analysis_20251018_094745.json` ⚠️ DELETE
- `duplicate_analysis_20251018_094920.json` ⚠️ DELETE
- `duplicate_analysis_20251018_094946.json` ⚠️ DELETE
- `duplicate_analysis_20251018_095029.json` ⚠️ DELETE
- `duplicate_analysis_20251018_095219.json` ⚠️ DELETE (latest, but cleanup is done)

**Cleanup Plans (5 files):**
- `cleanup_plan_20251018_093936.json` ⚠️ DELETE
- `cleanup_plan_20251018_094121.json` ⚠️ DELETE
- `cleanup_plan_20251018_094657.json` ⚠️ DELETE
- `cleanup_plan_20251018_094949.json` ⚠️ DELETE
- `cleanup_plan_20251018_095029.json` ⚠️ DELETE (already executed)

**Scraping Debug Files (10 files):**
- `scraping_debug_Candy_Cane_and_Peppe.html` ⚠️ DELETE
- `scraping_debug_Ginger's_Cottage.html` ⚠️ DELETE
- `scraping_debug_Kringle_Street_Snowm.html` ⚠️ DELETE
- `scraping_debug_Light_the_Way-Santa'.html` ⚠️ DELETE
- `scraping_debug_Nanook's_Home.html` ⚠️ DELETE
- `scraping_debug_North_Pole_Gate_(lit.html` ⚠️ DELETE
- `scraping_debug_Santa's_Reindeer_Pet.html` ⚠️ DELETE
- `scraping_debug_SCHEMA_TEST_DELETE_M.html` ⚠️ DELETE
- `scraping_debug_Sugar_Mountain_Lodge.html` ⚠️ DELETE
- `scraping_debug_The_Bitsy_Bungalows.html` ⚠️ DELETE

**Other Analysis Files:**
- `scraping_analysis.json` ⚠️ DELETE
- `scraping_prototype_results.json` ⚠️ DELETE
- `photo_analysis.json` ⚠️ DELETE
- `houses_without_photos.json` ⚠️ DELETE
- `north_pole_collection.html` ⚠️ DELETE (test file)
- `simple-test.html` ⚠️ DELETE (test file)

#### Superseded/Obsolete Python Scripts

**Old Duplicate Analysis Versions:**
- `analyze_duplicates.py` ⚠️ DELETE (v1 - superseded by v3)
- `analyze_duplicates_v2.py` ⚠️ DELETE (v2 - superseded by v3)
- `cleanup_duplicates_v2.py` ⚠️ DELETE (old cleanup approach)

**One-Off Fix Scripts (Already Applied):**
- `fix_duplicates.py` ⚠️ DELETE (one-time operation, completed)
- `fix_duplicate_alfies.py` ⚠️ DELETE (one-time operation, completed)
- `fix_photo_urls.py` ⚠️ DELETE (one-time operation, completed)
- `fix_photo_urls_v2.py` ⚠️ DELETE (one-time operation, completed)
- `fix_image_urls_from_manifest.py` ⚠️ DELETE (one-time operation, completed)
- `quick_fix_urls.py` ⚠️ DELETE (one-time operation, completed)

**Old Migration Scripts (Already Applied):**
- `add_auth_columns.sql` ⚠️ DELETE (incorporated into main schema)
- `add_house_id_to_accessories.sql` ⚠️ DELETE (incorporated into main schema)
- `complete_schema_migration.sql` ⚠️ DELETE (incorporated into main schema)
- `fix_user_id_constraint.sql` ⚠️ DELETE (incorporated into main schema)
- `remove_user_id_columns.sql` ⚠️ DELETE (incorporated into main schema)
- `run_migration.py` ⚠️ DELETE (one-time operation, completed)
- `run_complete_migration.py` ⚠️ DELETE (one-time operation, completed)
- `run_remove_user_id_migration.py` ⚠️ DELETE (one-time operation, completed)

**One-Off Check/Debug Scripts:**
- `check_database.py` ⚠️ DELETE (one-time check, completed)
- `check_duplicates.py` ⚠️ DELETE (use analyze_duplicates_v3.py instead)
- `check_house_accessory_links.py` ⚠️ DELETE (one-time check, completed)
- `check_photos.py` ⚠️ DELETE (one-time check, completed)
- `check_users.py` ⚠️ DELETE (one-time check, completed)
- `debug_database.py` ⚠️ DELETE (one-time debug, completed)
- `analyze_photo_issues.py` ⚠️ DELETE (one-time analysis, completed)
- `analyze_photo_matches.py` ⚠️ DELETE (one-time analysis, completed)
- `search_reindeer.py` ⚠️ DELETE (one-time search, completed)
- `search_water_tower.py` ⚠️ DELETE (one-time search, completed)

**Test Scripts (Completed):**
- `test_anon_access.py` ⚠️ DELETE (one-time test, completed)
- `test_auth_access.py` ⚠️ DELETE (one-time test, completed)
- `test_collection_browse.py` ⚠️ DELETE (one-time test, completed)
- `test_image_access.py` ⚠️ DELETE (one-time test, completed)
- `test_parsing.py` ⚠️ DELETE (one-time test, completed)

**Verification Scripts (Completed):**
- `verify_import.py` ⚠️ DELETE (one-time verification, completed)
- `verify_photos.py` ⚠️ DELETE (one-time verification, completed)
- `verify_schema.py` ⚠️ DELETE (one-time verification, completed)

**Other One-Off Scripts:**
- `cleanup_and_reset.py` ⚠️ DELETE (dangerous script, not needed)
- `create_supabase_user.py` ⚠️ DELETE (one-time operation, completed)
- `update_photos.py` ⚠️ DELETE (one-time operation, completed)
- `update_photos.py.bak` ⚠️ DELETE (backup file)
- `update_rls_policies.py` ⚠️ DELETE (one-time operation, completed)

**Obsolete Documentation:**
- `SCRAPING_PROTOTYPE_RESULTS.md` ⚠️ DELETE (results documented in SCRAPING_PLAN.md)

**Legacy Code:**
- `dept_56_app.jsx` ⚠️ DELETE (old version, replaced by src/DeptApp.tsx)

---

## 📊 Cleanup Summary

| Category | Count | Action |
|----------|-------|--------|
| Duplicate analysis JSON files | 12 | DELETE |
| Cleanup plan JSON files | 5 | DELETE |
| Scraping debug HTML files | 10 | DELETE |
| Other analysis JSON files | 4 | DELETE |
| Old script versions | 3 | DELETE |
| One-off fix scripts | 6 | DELETE |
| Migration SQL files | 5 | DELETE |
| Migration Python files | 3 | DELETE |
| Check/debug scripts | 10 | DELETE |
| Test scripts | 5 | DELETE |
| Verification scripts | 3 | DELETE |
| Other one-off scripts | 5 | DELETE |
| Backup files | 1 | DELETE |
| Obsolete docs | 1 | DELETE |
| Legacy code | 1 | DELETE |
| **TOTAL FILES TO DELETE** | **74** | |

---

## 🗂️ Recommended File Organization

After cleanup, create a `scripts/` directory to organize remaining utilities:

```
scripts/
├── data-ingestion/
│   ├── ingest_docx.py
│   └── requirements.txt (renamed from requirements-ingest.txt)
├── scraping/
│   ├── scraper_prototype.py
│   └── requirements.txt (renamed from requirements-scraper.txt)
└── maintenance/
    ├── analyze_duplicates.py (renamed from analyze_duplicates_v3.py)
    ├── generate_cleanup_plan.py
    └── execute_cleanup.py
```

---

## 🔧 Code Improvements Recommended

### 1. Frontend Improvements
- [ ] Add error boundaries to React components
- [ ] Implement proper loading states
- [ ] Add input validation and sanitization
- [ ] Improve accessibility (ARIA labels, keyboard navigation)
- [ ] Add unit tests with Vitest
- [ ] Add E2E tests with Playwright

### 2. Type Safety
- [ ] Review and strengthen TypeScript types
- [ ] Add strict null checks
- [ ] Ensure all database types match Supabase schema

### 3. Performance
- [ ] Implement virtual scrolling for large lists
- [ ] Add image lazy loading
- [ ] Optimize bundle size (check with `npm run build`)
- [ ] Add service worker for offline support

### 4. Security
- [ ] Review RLS policies in Supabase
- [ ] Add rate limiting
- [ ] Implement CSP headers
- [ ] Add input sanitization

### 5. Documentation
- [ ] Add JSDoc comments to complex functions
- [ ] Create CONTRIBUTING.md
- [ ] Add API documentation
- [ ] Document component props

### 6. Developer Experience
- [ ] Add ESLint configuration
- [ ] Add Prettier for code formatting
- [ ] Set up pre-commit hooks with Husky
- [ ] Add GitHub Actions for CI/CD

---

## ⚠️ Before Deleting

**IMPORTANT:** Before executing the cleanup:

1. ✅ **Ensure the latest duplicate cleanup was successful** (verified - 0 duplicates remaining)
2. ✅ **Verify the database is in good state**
3. ⚠️ **Create a git commit** before deleting files:
   ```powershell
   git add -A
   git commit -m "Pre-cleanup snapshot"
   ```
4. ⚠️ **Optionally archive deleted files** to a separate location:
   ```powershell
   mkdir archived_files
   # Move files there instead of deleting
   ```

---

## 🚀 Execution Plan

### Phase 1: Backup
```powershell
git add -A
git commit -m "Pre-cleanup snapshot - preserving all files before major cleanup"
```

### Phase 2: Delete Temporary Files
Remove all JSON/HTML analysis and debug files.

### Phase 3: Delete Obsolete Scripts
Remove all one-off, test, and verification scripts.

### Phase 4: Reorganize Utilities
Move remaining utility scripts to `scripts/` directory.

### Phase 5: Update Documentation
Update README.md to reflect new structure.

### Phase 6: Final Commit
```powershell
git add -A
git commit -m "Major cleanup: removed 74 obsolete files, reorganized utilities"
```

---

## 📝 Notes

- The cleanup will remove **74 files** totaling several MB
- All removed files were either:
  - One-time operations already completed
  - Temporary analysis/debug output
  - Superseded by newer versions
  - Test files for completed features
- No production code or active utilities will be removed
- The project will be significantly cleaner and easier to navigate
