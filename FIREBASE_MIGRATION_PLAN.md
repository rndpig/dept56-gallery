# Firebase Migration Plan - Department 56 Gallery

**Migration Date**: January 2026  
**Status**: 🔄 Planning Phase  
**Estimated Timeline**: 3-4 weeks (2-3 full days of active work)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current vs. Target Architecture](#current-vs-target-architecture)
3. [Complexity Assessment](#complexity-assessment)
4. [Migration Phases Overview](#migration-phases-overview)
5. [Detailed Phase Instructions](#detailed-phase-instructions)
6. [Critical Considerations](#critical-considerations)
7. [Pre-Migration Checklist](#pre-migration-checklist)
8. [Rollback Plan](#rollback-plan)
9. [Success Criteria](#success-criteria)

---

## Executive Summary

### Migration Goals

This document outlines the complete migration strategy for transitioning the Department 56 Gallery app from a **Supabase + Vercel** architecture to a **Firebase-unified** architecture, following the successful pattern established by the dinner-spinner project.

**Primary Objectives**:
- ✅ Consolidate all services under Firebase (database, storage, auth, hosting)
- ✅ Maintain 100% functional parity - zero user-facing changes
- ✅ Preserve all existing data (houses, accessories, collections, tags, relationships)
- ✅ Keep Cloudflare for DNS management only
- ✅ Simplify architecture and reduce service dependencies

**Reference Project**: The dinner-spinner app serves as our proven migration template. Key learnings:
- Firebase simplifies OAuth (no callback routes needed)
- Firestore requires careful schema design for relationships
- Static export works seamlessly with Firebase Hosting
- Custom domains via Cloudflare CNAME (no proxy)
- Total migration time for dinner-spinner: ~2 days

---

## Current vs. Target Architecture

### Current State (Supabase + Vercel)

```
┌─────────────────────────────────────────────────────────────┐
│                    dept56.rndpig.com                         │
│                   (Cloudflare DNS → Vercel)                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        VERCEL HOSTING                        │
│  - Vite + React + TypeScript                                │
│  - Build: npm run build → dist/                             │
│  - Framework: vite (not Next.js)                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────┬──────────────────┬──────────────────────┐
│   SUPABASE AUTH   │  SUPABASE DB     │  SUPABASE STORAGE   │
│                   │                  │                     │
│ - Google OAuth    │ - PostgreSQL     │ - dept56-images     │
│ - Email whitelist │ - 9 tables       │ - House photos      │
│ - 6 admin users   │ - RLS policies   │ - Accessory photos  │
└───────────────────┴──────────────────┴──────────────────────┘
```

**Components**:
- **Frontend**: Vite + React + TypeScript (not Next.js)
- **Database**: Supabase PostgreSQL (9 tables with complex relationships)
- **Storage**: Supabase Storage (`dept56-images` bucket)
- **Auth**: Supabase Auth with Google OAuth + Email whitelist
- **Hosting**: Vercel
- **Domain**: dept56.rndpig.com (Cloudflare DNS)

**Pain Points**:
- Multiple service dependencies (Supabase + Vercel + Cloudflare)
- Supabase free tier limitations and maintenance headaches
- Separate configuration for auth, database, storage, hosting
- Need to keep Supabase project active (billing/management complexity)

### Target State (Firebase Unified)

```
┌─────────────────────────────────────────────────────────────┐
│                    dept56.rndpig.com                         │
│                 (Cloudflare DNS → Firebase)                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    FIREBASE HOSTING                          │
│  - Static site (Vite build output)                          │
│  - Built-in CDN                                             │
│  - Auto SSL certificates                                     │
│  - Deploy: firebase deploy --only hosting                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────┬──────────────────┬──────────────────────┐
│   FIREBASE AUTH   │  CLOUD FIRESTORE │  FIREBASE STORAGE   │
│                   │                  │                     │
│ - Google OAuth    │ - NoSQL database │ - dept56-gallery    │
│ - Email whitelist │ - 9 collections  │ - House photos      │
│ - Built-in popup  │ - Security rules │ - Accessory photos  │
└───────────────────┴──────────────────┴──────────────────────┘
```

**Components**:
- **Frontend**: Vite + React + TypeScript (unchanged)
- **Database**: Cloud Firestore (9 collections, mapped from PostgreSQL)
- **Storage**: Firebase Storage (unified with database project)
- **Auth**: Firebase Authentication (simpler OAuth, no callbacks)
- **Hosting**: Firebase Hosting (integrated with auth/database)
- **Domain**: dept56.rndpig.com (Cloudflare DNS only)

**Benefits**:
- ✅ Single service provider (Firebase) for everything
- ✅ Unified console, billing, and management
- ✅ Better free tier (1GB Firestore, 5GB storage, 10GB bandwidth)
- ✅ Simpler authentication (no callback routes)
- ✅ Integrated hosting with automatic deployments
- ✅ Better developer experience (Firebase CLI)

---

## Complexity Assessment

### Why Dept56 is More Complex than Dinner-Spinner

| Aspect | Dinner-Spinner | Dept56-Gallery | Complexity |
|--------|----------------|----------------|------------|
| **Tables/Collections** | 4 simple tables | 9 interconnected tables | 🔴 High |
| **Relationships** | None (flat structure) | Many-to-many (3 types) | 🔴 High |
| **Image Storage** | None | Houses + Accessories | 🟡 Medium |
| **Data Volume** | ~10-20 restaurants | Hundreds of items | 🟡 Medium |
| **Auth Complexity** | Family whitelist | Multi-user + RLS | 🟡 Medium |
| **Queries** | Simple filters | Fuzzy search (Fuse.js) | 🟡 Medium |
| **Frontend** | Next.js (1 page) | Vite/React (4367 lines) | 🔴 High |

**Key Challenges**:

1. **Relational Data in NoSQL**: Dept56 uses PostgreSQL relationships extensively:
   - Houses ↔ Accessories (many-to-many)
   - Items ↔ Collections (many-to-many)
   - Items ↔ Tags (many-to-many with metadata)
   
2. **Image Migration**: Need to migrate stored images AND update all URLs

3. **Complex Queries**: Fuzzy search, filtering, multi-table joins need Firestore adaptation

4. **Large Codebase**: DeptApp.tsx is 4367 lines with extensive Supabase integration

5. **User ID Migration**: Supabase UUIDs → Firebase UIDs requires careful handling

**Estimated Effort**:
- **Setup & Planning**: 4 hours
- **Data Migration**: 8 hours
- **Code Migration**: 12 hours
- **Testing**: 6 hours
- **Deployment**: 2 hours
- **Total**: ~32 hours (4 full days or 2-3 weeks part-time)

---

## Migration Phases Overview

```
Phase 1: Firebase Setup (1 hour)
  ├─ Create Firebase project
  ├─ Install dependencies
  ├─ Configure environment variables
  └─ Initialize services (Firestore, Storage, Hosting)

Phase 2: Schema Design (2-3 hours)
  ├─ Map PostgreSQL tables → Firestore collections
  ├─ Design denormalized structure
  ├─ Plan indexes for queries
  └─ Create TypeScript types

Phase 3: Storage Migration (2-4 hours)
  ├─ Download images from Supabase Storage
  ├─ Upload to Firebase Storage
  ├─ Map old URLs → new URLs
  └─ Configure storage rules

Phase 4: Authentication (2 hours)
  ├─ Configure Firebase Auth with Google OAuth
  ├─ Implement email whitelist
  ├─ Update auth components
  └─ Test sign-in flow

Phase 5: Data Migration (4-6 hours)
  ├─ Export all data from Supabase
  ├─ Transform schema (snake_case → camelCase)
  ├─ Import to Firestore with Admin SDK
  ├─ Verify relationships
  └─ Update image URLs

Phase 6: Code Migration (6-8 hours)
  ├─ Create lib/firebase.ts
  ├─ Update types/database.ts → types/firestore.ts
  ├─ Replace Supabase queries with Firestore queries
  ├─ Update image upload/download logic
  └─ Update DeptApp.tsx (4367 lines!)

Phase 7: Build Configuration (1 hour)
  ├─ Create firebase.json
  ├─ Configure Firestore security rules
  ├─ Configure Storage security rules
  └─ Create Firestore indexes

Phase 8: Testing (4-6 hours)
  ├─ Local development testing
  ├─ Authentication flow testing
  ├─ CRUD operations testing
  ├─ Image upload/display testing
  ├─ Search functionality testing
  └─ Relationship testing

Phase 9: Deployment (2 hours)
  ├─ Build production bundle
  ├─ Deploy to Firebase Hosting
  ├─ Update Cloudflare DNS
  ├─ Verify custom domain
  └─ SSL certificate provisioning

Phase 10: Post-Migration (1 hour)
  ├─ Production verification
  ├─ Update documentation
  ├─ Monitor for issues
  └─ Decommission Supabase (after 30 days)
```

---

## Detailed Phase Instructions

### Phase 1: Firebase Project Setup ⏱️ 1 hour

#### 1.1 Prerequisites

**Before starting**:
- [ ] Ensure Node.js 18+ installed
- [ ] Ensure npm/yarn available
- [ ] Create Google Cloud account (if not already)
- [ ] Install Firebase CLI globally

```powershell
# Install Firebase CLI globally
npm install -g firebase-tools

# Verify installation
firebase --version
```

#### 1.2 Create Firebase Project

```powershell
# Navigate to project directory
cd "c:\Users\rndpi\Documents\Coding Projects\dept56-gallery"

# Login to Firebase
firebase login

# Initialize Firebase in project
firebase init

# When prompted, select:
# ✅ Firestore: Configure security rules and indexes files
# ✅ Storage: Configure security rules file for Cloud Storage
# ✅ Hosting: Configure files for Firebase Hosting and (optionally) set up GitHub Action deploys
# ❌ Functions: Skip for now (optional for future)

# Configuration answers:
# - Use an existing project? YES
# - Select project: Create new project → "dept56-gallery"
# - Firestore rules file: firestore.rules (default)
# - Firestore indexes file: firestore.indexes.json (default)
# - Storage rules file: storage.rules (default)
# - Hosting public directory: dist (for Vite output)
# - Configure as single-page app: YES
# - Set up automatic builds and deploys with GitHub: NO (manual for now)
```

#### 1.3 Install Dependencies

```powershell
# Install Firebase client SDK
npm install firebase

# Install Firebase Admin SDK (for migration scripts)
npm install --save-dev firebase-admin
```

**Expected changes**:
- `firebase.json` created
- `firestore.rules` created
- `firestore.indexes.json` created
- `storage.rules` created
- `.firebaserc` created (contains project ID)
- `package.json` updated with new dependencies

#### 1.4 Get Firebase Configuration

1. **Go to Firebase Console**: https://console.firebase.google.com
2. **Select your project**: dept56-gallery
3. **Click gear icon** (Project Settings)
4. **Scroll to "Your apps"** section
5. **Click "Add app"** → Select Web (</>) icon
6. **Register app**:
   - App nickname: `dept56-gallery-web`
   - Don't set up Firebase Hosting (we'll do manually)
7. **Copy configuration object**

#### 1.5 Configure Environment Variables

Create `.env.local` file (this replaces your Supabase .env):

```env
# Firebase Configuration
VITE_FIREBASE_API_KEY=your-api-key-here
VITE_FIREBASE_AUTH_DOMAIN=dept56-gallery.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=dept56-gallery
VITE_FIREBASE_STORAGE_BUCKET=dept56-gallery.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
```

**Important**: Add to `.gitignore`:

```gitignore
# Firebase
.env.local
firebase-service-account.json
.firebase/
```

#### 1.6 Get Service Account Key (for migration scripts)

1. **Firebase Console** → Project Settings
2. **Service Accounts** tab
3. **Click "Generate new private key"**
4. **Save as**: `firebase-service-account.json` (in project root)
5. **⚠️ CRITICAL**: Add to `.gitignore` immediately!
6. **Never commit this file** to version control

**Expected file structure**:
```json
{
  "type": "service_account",
  "project_id": "dept56-gallery",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  ...
}
```

#### 1.7 Create Firebase Client Library

Create `src/lib/firebase.ts`:

```typescript
import { initializeApp, getApps } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getStorage } from 'firebase/storage';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

// Validate configuration
if (!firebaseConfig.apiKey || !firebaseConfig.projectId) {
  throw new Error('Missing Firebase environment variables. Check .env.local file.');
}

// Initialize Firebase (only once)
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];

// Initialize services
export const auth = getAuth(app);
export const db = getFirestore(app);
export const storage = getStorage(app);

// Google Auth Provider
export const googleProvider = new GoogleAuthProvider();

// Export app for admin operations if needed
export default app;
```

#### 1.8 Verification

Test Firebase connection:

```powershell
# Start dev server
npm run dev

# Open browser console and test:
# Should log Firebase app object without errors
```

Create test file `src/lib/firebase-test.ts`:

```typescript
import { db, auth, storage } from './firebase';

console.log('Firebase initialized:');
console.log('- Firestore:', db.app.name);
console.log('- Auth:', auth.app.name);
console.log('- Storage:', storage.app.name);
```

**Phase 1 Completion Checklist**:
- [ ] Firebase project created
- [ ] Firebase CLI installed and logged in
- [ ] Dependencies installed (firebase, firebase-admin)
- [ ] Environment variables configured (.env.local)
- [ ] Service account key downloaded (firebase-service-account.json)
- [ ] Firebase client library created (src/lib/firebase.ts)
- [ ] Configuration files created (firebase.json, firestore.rules, storage.rules)
- [ ] Connection verified (no errors in console)

---

