# Firebase Migration Cleanup Checklist

## ✅ Completed
- [x] Migrated 551 records to Firestore
- [x] Updated authentication to Firebase Auth
- [x] Deployed to Firebase Hosting
- [x] Custom domain configured (dept56.rndpig.com)
- [x] Security rules deployed (public read, whitelist write)
- [x] Renamed old database.ts to database.ts.backup

## 📋 Post-Migration Tasks

### Supabase Cleanup
- [ ] **Keep Supabase Storage ACTIVE** - Images are still hosted there
- [ ] **Pause Supabase Database** - No longer needed (optional - saves costs)
  - Go to Supabase project settings
  - Pause the project (keeps storage, disables database)
- [ ] **Keep anon key in .env.local** - Needed for image uploads

### Vercel Cleanup (Optional)
- [ ] Remove old Vercel deployment
  - Go to Vercel dashboard
  - Delete the dept56-gallery project
  
### Future Considerations
- [ ] Consider migrating storage to Firebase Storage if Supabase costs become an issue
- [ ] Monitor Firebase usage in Firebase Console
- [ ] Backup Firestore regularly (Firebase has automatic daily backups)

## 📁 Files to Keep
- `scripts/export-supabase.js` - For reference or re-migration
- `scripts/import-firestore.js` - For reference
- `scripts/verify-migration.js` - For validation
- `scripts/migration-data/supabase-export.json` - Backup of original data
- `src/lib/database.ts.backup` - Old Supabase database layer (reference)
- `src/lib/supabase.ts` - Still needed for image uploads

## 🗑️ Optional Cleanup
These files can be deleted after confirming everything works:
- `scripts/migrate-storage.js` - Not used (kept Supabase Storage)
- `scripts/check-storage-usage.js` - One-time use
- `FIREBASE_MIGRATION_*.md` - Documentation files (archive or delete)
- `PHASE1_COMPLETE.md` - Milestone documentation

## 🔒 Security Notes
- `firebase-service-account.json` is in .gitignore ✓
- `.env.local` is in .gitignore ✓
- Migration data is in .gitignore ✓
