# Firebase Migration - Quick Reference Checklist

**Project**: Department 56 Gallery  
**Status**: Phase 1 Complete  
**Last Updated**: January 18, 2026

---

## 📋 Migration Progress Tracker

### Phase 1: Firebase Project Setup ✅ COMPLETE

- [x] Install dependencies (firebase, firebase-admin)
- [x] Create Firebase client library (src/lib/firebase.ts)
- [x] Create environment template (.env.local.example)
- [x] Update .gitignore with Firebase exclusions
- [x] Create migration documentation
- [ ] **YOU DO**: Create Firebase project in console
- [ ] **YOU DO**: Run `firebase init`
- [ ] **YOU DO**: Create .env.local with your config
- [ ] **YOU DO**: Download service account key
- [ ] **YOU DO**: Verify setup (npm run dev)

### Phase 2: Schema Design & Mapping ⏳ NEXT

- [ ] Review PostgreSQL → Firestore mapping
- [ ] Create firestore.indexes.json
- [ ] Create src/types/firestore.ts
- [ ] Document field name conversions
- [ ] Plan relationship strategy
- [ ] **Estimated time**: 2-3 hours

### Phase 3: Storage Migration ⏳ PENDING

- [ ] Create migrate-storage.js script
- [ ] Configure Firebase Storage rules
- [ ] Download images from Supabase
- [ ] Upload images to Firebase
- [ ] Update database URLs
- [ ] **Estimated time**: 2-4 hours

### Phase 4: Authentication Migration ⏳ PENDING

- [ ] Enable Firebase Auth in console
- [ ] Configure Google OAuth
- [ ] Create Auth component (src/components/Auth.tsx)
- [ ] Update App.tsx with Auth wrapper
- [ ] Test whitelist logic
- [ ] **Estimated time**: 2 hours

### Phase 5: Data Migration ⏳ PENDING

- [ ] Create export-supabase.js
- [ ] Export data from Supabase
- [ ] Create import-firestore.js
- [ ] Import data to Firestore
- [ ] Create verify-migration.js
- [ ] Verify all data migrated
- [ ] **Estimated time**: 4-6 hours

### Phase 6: Code Migration ⏳ PENDING

- [ ] Expand src/lib/firebase.ts with CRUD functions
- [ ] Update DeptApp.tsx imports
- [ ] Replace Supabase queries with Firestore
- [ ] Update image upload logic
- [ ] Update field names (snake_case → camelCase)
- [ ] **Estimated time**: 6-8 hours

### Phase 7: Build Configuration ⏳ PENDING

- [ ] Configure firebase.json
- [ ] Create firestore.rules
- [ ] Create storage.rules
- [ ] Deploy rules and indexes
- [ ] **Estimated time**: 1 hour

### Phase 8: Testing ⏳ PENDING

- [ ] Test authentication flow
- [ ] Test CRUD operations (houses, accessories, collections, tags)
- [ ] Test image upload/display
- [ ] Test search and filtering
- [ ] Test relationships
- [ ] Test error scenarios
- [ ] **Estimated time**: 4-6 hours

### Phase 9: Deployment ⏳ PENDING

- [ ] Build production bundle (npm run build)
- [ ] Deploy to Firebase Hosting
- [ ] Update Cloudflare DNS
- [ ] Add custom domain in Firebase
- [ ] Wait for SSL provisioning
- [ ] Test production site
- [ ] **Estimated time**: 2 hours

### Phase 10: Post-Migration ⏳ PENDING

- [ ] Monitor production (48 hours)
- [ ] Update documentation
- [ ] Create migration summary
- [ ] Archive old code
- [ ] Decommission Supabase (after 30 days)
- [ ] Decommission Vercel (after 30 days)
- [ ] **Estimated time**: 1 hour + monitoring

---

## 🎯 Critical Milestones

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Phase 1 Complete | ✅ Jan 18, 2026 | DONE |
| Firebase Project Created | TBD | TODO |
| Schema Designed | TBD | TODO |
| Data Migrated | TBD | TODO |
| Code Migrated | TBD | TODO |
| Testing Complete | TBD | TODO |
| Production Deployed | TBD | TODO |
| Supabase Decommissioned | TBD + 30 days | TODO |

---

## 📊 Migration Statistics (To Be Filled)

### Data to Migrate

| Collection | Supabase Count | Firestore Count | Status |
|------------|----------------|-----------------|--------|
| houses | ??? | ??? | ⏳ |
| accessories | ??? | ??? | ⏳ |
| collections | ??? | ??? | ⏳ |
| tags | ??? | ??? | ⏳ |
| house_accessory_links | ??? | ??? | ⏳ |
| house_collections | ??? | ??? | ⏳ |
| accessory_collections | ??? | ??? | ⏳ |
| house_tags | ??? | ??? | ⏳ |
| accessory_tags | ??? | ??? | ⏳ |
| **Images** | ??? | ??? | ⏳ |

*Fill in after running export-supabase.js*

---

## 🚨 Pre-Flight Checks

### Before Starting Any Phase

- [ ] Git working directory is clean
- [ ] All changes committed to safe branch
- [ ] Supabase is still active (DO NOT PAUSE)
- [ ] Backup of current production state exists
- [ ] Team notified of migration progress

### Before Going to Production

- [ ] All tests passing
- [ ] No console errors
- [ ] Firebase rules deployed
- [ ] Indexes created
- [ ] Custom domain configured
- [ ] SSL certificate active
- [ ] Rollback plan documented
- [ ] Team ready for launch

---

## 🛡️ Rollback Plan

**If critical issues arise after deployment**:

1. **Immediate Rollback** (< 5 minutes):
   ```powershell
   # Revert Cloudflare DNS to Vercel
   # In Cloudflare Dashboard:
   # Change dept56 CNAME back to: cname.vercel-dns.com
   ```

2. **Re-enable Supabase**:
   - Ensure Supabase project is still active
   - Verify data is intact
   - Test authentication

3. **Deploy Previous Version**:
   ```powershell
   # In Vercel Dashboard:
   # Redeploy previous working deployment
   ```

4. **Communicate**:
   - Notify users of temporary issues
   - Document what went wrong
   - Plan fixes

**Rollback Window**: 30 days (while Supabase remains active)

---

## 📞 Support & Resources

### Documentation

- [Main Migration Plan](./FIREBASE_MIGRATION_PLAN.md) - Complete overview
- [Phases 2-5](./FIREBASE_MIGRATION_PHASE2-5.md) - Schema, storage, auth, data
- [Phases 6-10](./FIREBASE_MIGRATION_PHASE6-10.md) - Code, testing, deployment
- [Phase 1 Complete](./PHASE1_COMPLETE.md) - Setup details

### External Resources

- [Firebase Documentation](https://firebase.google.com/docs)
- [Firestore Security Rules](https://firebase.google.com/docs/firestore/security/get-started)
- [Firebase Hosting](https://firebase.google.com/docs/hosting)
- [Supabase to Firebase Migration](https://firebase.google.com/docs/firestore/migrate)

### Reference Projects

- **dinner-spinner**: Successfully migrated Supabase → Firebase
  - Location: `c:\Users\rndpi\Documents\Coding Projects\dinner-spinner`
  - Review for patterns and solutions

---

## ⏱️ Time Estimates Summary

| Phase | Estimated Time | Actual Time |
|-------|---------------|-------------|
| Phase 1: Setup | 1 hour | ✅ Done |
| Phase 2: Schema | 2-3 hours | ⏳ |
| Phase 3: Storage | 2-4 hours | ⏳ |
| Phase 4: Auth | 2 hours | ⏳ |
| Phase 5: Data | 4-6 hours | ⏳ |
| Phase 6: Code | 6-8 hours | ⏳ |
| Phase 7: Build | 1 hour | ⏳ |
| Phase 8: Testing | 4-6 hours | ⏳ |
| Phase 9: Deploy | 2 hours | ⏳ |
| Phase 10: Post | 1 hour | ⏳ |
| **TOTAL** | **25-34 hours** | **TBD** |

**Realistic Timeline**: 2-3 weeks part-time OR 4 full days

---

## 🎉 Success Criteria

Migration is considered successful when:

✅ **Functionality**:
- [ ] All users can sign in with Google OAuth
- [ ] All houses/accessories display correctly
- [ ] All images load properly
- [ ] All CRUD operations work (add, edit, delete)
- [ ] Collections and tags work
- [ ] Relationships preserved (houses ↔ accessories)
- [ ] Search and filtering work

✅ **Performance**:
- [ ] Page load < 2 seconds
- [ ] Image load < 1 second
- [ ] Query response < 500ms
- [ ] No visible lag in UI

✅ **Data Integrity**:
- [ ] All records migrated (counts match)
- [ ] No data loss
- [ ] All relationships intact
- [ ] All images accessible

✅ **Security**:
- [ ] Authentication enforced
- [ ] Users can only see their own data
- [ ] No unauthorized access
- [ ] HTTPS working (green lock)

✅ **Stability**:
- [ ] No console errors
- [ ] No server errors
- [ ] Runs smoothly for 48+ hours
- [ ] No user-reported issues

---

## 📝 Notes & Learnings

*Document any issues, solutions, or insights here as you progress*

---

**Last Updated**: January 18, 2026  
**Next Action**: Complete manual Firebase setup, then proceed to Phase 2
