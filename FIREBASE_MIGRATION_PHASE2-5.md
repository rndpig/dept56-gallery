# Firebase Migration - Phases 2-5

**Document**: Schema Design, Storage, Authentication, and Data Migration  
**Part of**: [Main Migration Plan](./FIREBASE_MIGRATION_PLAN.md)

---

## Phase 2: Schema Design & Mapping ⏱️ 2-3 hours

### 2.1 PostgreSQL → Firestore Collection Mapping

#### Current Supabase Schema (PostgreSQL)

```sql
-- 9 Tables with relationships

houses (table)
├─ id: UUID (PK)
├─ user_id: UUID (FK → auth.users)
├─ name: TEXT
├─ year: INTEGER
├─ retired_year: INTEGER
├─ description: TEXT
├─ sku: TEXT
├─ notes: TEXT
├─ photo_url: TEXT
├─ purchased_year: INTEGER
├─ price: NUMERIC
├─ collection: TEXT
├─ series: TEXT
├─ created_at: TIMESTAMPTZ
└─ updated_at: TIMESTAMPTZ

accessories (similar to houses)

collections (table)
├─ id: UUID (PK)
├─ user_id: UUID (FK)
├─ name: TEXT
├─ notes: TEXT
└─ created_at: TIMESTAMPTZ

tags (table)
├─ id: UUID (PK)
├─ user_id: UUID (FK)
├─ name: TEXT
└─ created_at: TIMESTAMPTZ

house_accessory_links (many-to-many)
├─ id: UUID (PK)
├─ house_id: UUID (FK)
├─ accessory_id: UUID (FK)
└─ created_at: TIMESTAMPTZ

house_collections (many-to-many)
├─ id: UUID (PK)
├─ house_id: UUID (FK)
├─ collection_id: UUID (FK)
└─ created_at: TIMESTAMPTZ

accessory_collections (many-to-many)
├─ id: UUID (PK)
├─ accessory_id: UUID (FK)
├─ collection_id: UUID (FK)
└─ created_at: TIMESTAMPTZ

house_tags (many-to-many with metadata)
├─ id: UUID (PK)
├─ house_id: UUID (FK)
├─ tag_id: UUID (FK)
├─ source: TEXT ('manual' | 'ml')
├─ confidence: DECIMAL
├─ reviewed: BOOLEAN
└─ created_at: TIMESTAMPTZ

accessory_tags (similar to house_tags)
```

#### Target Firestore Schema (NoSQL)

```javascript
// 9 Collections (mirroring tables)

users/{userId}  // Firebase Auth UID as document ID
{
  email: string,
  role: 'user' | 'admin',
  createdAt: Timestamp
}

houses/{houseId}
{
  userId: string,  // Indexed
  name: string,
  year?: number,
  retiredYear?: number,
  description?: string,
  sku?: string,
  notes?: string,
  photoUrl?: string,  // Firebase Storage URL
  purchasedYear?: number,
  price?: number,
  collection?: string,
  series?: string,
  createdAt: Timestamp,
  updatedAt: Timestamp
}

accessories/{accessoryId}
{
  // Same structure as houses
  userId: string,
  name: string,
  // ... (identical fields)
}

collections/{collectionId}
{
  userId: string,  // Indexed
  name: string,
  notes?: string,
  createdAt: Timestamp
}

tags/{tagId}
{
  userId: string,  // Indexed
  name: string,
  createdAt: Timestamp
}

houseAccessoryLinks/{linkId}
{
  houseId: string,      // Indexed
  accessoryId: string,  // Indexed
  userId: string,       // For RLS-like security
  createdAt: Timestamp
}

houseCollections/{linkId}
{
  houseId: string,      // Indexed
  collectionId: string, // Indexed
  userId: string,
  createdAt: Timestamp
}

accessoryCollections/{linkId}
{
  accessoryId: string,  // Indexed
  collectionId: string, // Indexed
  userId: string,
  createdAt: Timestamp
}

houseTags/{linkId}
{
  houseId: string,      // Indexed
  tagId: string,        // Indexed
  userId: string,
  source: 'manual' | 'ml',
  confidence?: number,
  reviewed: boolean,
  createdAt: Timestamp
}

accessoryTags/{linkId}
{
  // Same as houseTags but with accessoryId
}
```

### 2.2 Field Name Conversions

**Critical**: PostgreSQL uses `snake_case`, Firestore best practice is `camelCase`.

| PostgreSQL Field | Firestore Field | Type Conversion |
|------------------|-----------------|-----------------|
| `user_id` | `userId` | UUID → string |
| `photo_url` | `photoUrl` | TEXT → string |
| `retired_year` | `retiredYear` | INTEGER → number |
| `purchased_year` | `purchasedYear` | INTEGER → number |
| `created_at` | `createdAt` | TIMESTAMPTZ → Timestamp |
| `updated_at` | `updatedAt` | TIMESTAMPTZ → Timestamp |
| `house_id` | `houseId` | UUID → string |
| `accessory_id` | `accessoryId` | UUID → string |
| `collection_id` | `collectionId` | UUID → string |
| `tag_id` | `tagId` | UUID → string |

### 2.3 Firestore Indexes Required

Create `firestore.indexes.json`:

```json
{
  "indexes": [
    {
      "collectionGroup": "houses",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "userId", "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "accessories",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "userId", "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "houseAccessoryLinks",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "houseId", "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "houseAccessoryLinks",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "accessoryId", "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "houseCollections",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "houseId", "order": "ASCENDING" }
      ]
    },
    {
      "collectionGroup": "accessoryCollections",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "accessoryId", "order": "ASCENDING" }
      ]
    },
    {
      "collectionGroup": "houseTags",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "houseId", "order": "ASCENDING" },
        { "fieldPath": "reviewed", "order": "ASCENDING" }
      ]
    },
    {
      "collectionGroup": "accessoryTags",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "accessoryId", "order": "ASCENDING" },
        { "fieldPath": "reviewed", "order": "ASCENDING" }
      ]
    }
  ],
  "fieldOverrides": []
}
```

### 2.4 Create TypeScript Types

Create `src/types/firestore.ts`:

```typescript
import { Timestamp } from 'firebase/firestore';

// Firestore document types (with Timestamp)
export interface FirestoreUser {
  email: string;
  role: 'user' | 'admin';
  createdAt: Timestamp;
}

export interface FirestoreHouse {
  userId: string;
  name: string;
  year?: number;
  retiredYear?: number;
  description?: string;
  sku?: string;
  notes?: string;
  photoUrl?: string;
  purchasedYear?: number;
  price?: number;
  collection?: string;
  series?: string;
  createdAt: Timestamp;
  updatedAt: Timestamp;
}

export interface FirestoreAccessory {
  userId: string;
  name: string;
  year?: number;
  retiredYear?: number;
  description?: string;
  sku?: string;
  notes?: string;
  photoUrl?: string;
  purchasedYear?: number;
  price?: number;
  collection?: string;
  series?: string;
  createdAt: Timestamp;
  updatedAt: Timestamp;
}

export interface FirestoreCollection {
  userId: string;
  name: string;
  notes?: string;
  createdAt: Timestamp;
}

export interface FirestoreTag {
  userId: string;
  name: string;
  createdAt: Timestamp;
}

export interface FirestoreHouseAccessoryLink {
  houseId: string;
  accessoryId: string;
  userId: string;
  createdAt: Timestamp;
}

export interface FirestoreHouseCollection {
  houseId: string;
  collectionId: string;
  userId: string;
  createdAt: Timestamp;
}

export interface FirestoreAccessoryCollection {
  accessoryId: string;
  collectionId: string;
  userId: string;
  createdAt: Timestamp;
}

export interface FirestoreHouseTag {
  houseId: string;
  tagId: string;
  userId: string;
  source: 'manual' | 'ml';
  confidence?: number;
  reviewed: boolean;
  createdAt: Timestamp;
}

export interface FirestoreAccessoryTag {
  accessoryId: string;
  tagId: string;
  userId: string;
  source: 'manual' | 'ml';
  confidence?: number;
  reviewed: boolean;
  createdAt: Timestamp;
}

// Client-safe types (with Date instead of Timestamp for UI)
export interface User {
  id: string;
  email: string;
  role: 'user' | 'admin';
  createdAt: Date;
}

export interface House {
  id: string;
  userId: string;
  name: string;
  year?: number;
  retiredYear?: number;
  description?: string;
  sku?: string;
  notes?: string;
  photoUrl?: string;
  purchasedYear?: number;
  price?: number;
  collection?: string;
  series?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface Accessory {
  id: string;
  userId: string;
  name: string;
  year?: number;
  retiredYear?: number;
  description?: string;
  sku?: string;
  notes?: string;
  photoUrl?: string;
  purchasedYear?: number;
  price?: number;
  collection?: string;
  series?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface Collection {
  id: string;
  userId: string;
  name: string;
  notes?: string;
  createdAt: Date;
}

export interface Tag {
  id: string;
  userId: string;
  name: string;
  createdAt: Date;
}

export interface HouseAccessoryLink {
  id: string;
  houseId: string;
  accessoryId: string;
  userId: string;
  createdAt: Date;
}

export interface HouseCollection {
  id: string;
  houseId: string;
  collectionId: string;
  userId: string;
  createdAt: Date;
}

export interface AccessoryCollection {
  id: string;
  accessoryId: string;
  collectionId: string;
  userId: string;
  createdAt: Date;
}

export interface HouseTag {
  id: string;
  houseId: string;
  tagId: string;
  userId: string;
  source: 'manual' | 'ml';
  confidence?: number;
  reviewed: boolean;
  createdAt: Date;
}

export interface AccessoryTag {
  id: string;
  accessoryId: string;
  tagId: string;
  userId: string;
  source: 'manual' | 'ml';
  confidence?: number;
  reviewed: boolean;
  createdAt: Date;
}

// Helper type for documents with ID
export type WithId<T> = T & { id: string };

// Converter helpers
export function timestampToDate(timestamp: Timestamp): Date {
  return timestamp.toDate();
}
```

**Phase 2 Completion Checklist**:
- [ ] Schema mapping documented (PostgreSQL → Firestore)
- [ ] Field name conversions identified
- [ ] Firestore indexes defined (firestore.indexes.json)
- [ ] TypeScript types created (src/types/firestore.ts)
- [ ] Relationship strategy planned (link collections)

---

## Phase 3: Storage Migration ⏱️ 2-4 hours

### 3.1 Current Storage Analysis

**Supabase Storage**:
- **Bucket**: `dept56-images`
- **Structure**: Likely flat or organized by type (houses/, accessories/)
- **URLs**: `https://[project].supabase.co/storage/v1/object/public/dept56-images/[filename]`
- **Access**: Public read (configured in bucket policies)

**Firebase Storage**:
- **Bucket**: `dept56-gallery.appspot.com`
- **Structure**: Will use `images/houses/` and `images/accessories/`
- **URLs**: `https://firebasestorage.googleapis.com/v0/b/[bucket]/o/images%2F[filename]?alt=media&token=[token]`
- **Access**: Authenticated users only (more secure)

### 3.2 Storage Migration Script

Create `scripts/migrate-storage.js`:

```javascript
// Node.js script to migrate images from Supabase to Firebase Storage
const { createClient } = require('@supabase/supabase-js');
const admin = require('firebase-admin');
const fs = require('fs');
const path = require('path');
const https = require('https');

// Initialize Supabase
const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
);

// Initialize Firebase Admin
const serviceAccount = require('../firebase-service-account.json');
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  storageBucket: 'dept56-gallery.appspot.com'
});

const bucket = admin.storage().bucket();
const db = admin.firestore();

// Download file from URL
function downloadFile(url, filepath) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(filepath);
    https.get(url, (response) => {
      response.pipe(file);
      file.on('finish', () => {
        file.close();
        resolve();
      });
    }).on('error', (err) => {
      fs.unlink(filepath, () => {});
      reject(err);
    });
  });
}

async function migrateStorage() {
  console.log('🔄 Starting storage migration...');
  
  // Get all houses with photos
  const housesSnap = await db.collection('houses').get();
  const houses = housesSnap.docs.map(doc => ({ id: doc.id, ...doc.data() }));
  
  const housesWithPhotos = houses.filter(h => h.photoUrl && h.photoUrl.includes('supabase'));
  console.log(`📸 Found ${housesWithPhotos.length} houses with Supabase photos`);
  
  // Get all accessories with photos
  const accessoriesSnap = await db.collection('accessories').get();
  const accessories = accessoriesSnap.docs.map(doc => ({ id: doc.id, ...doc.data() }));
  
  const accessoriesWithPhotos = accessories.filter(a => a.photoUrl && a.photoUrl.includes('supabase'));
  console.log(`📸 Found ${accessoriesWithPhotos.length} accessories with Supabase photos`);
  
  // Create temp directory
  const tempDir = path.join(__dirname, 'temp-images');
  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true });
  }
  
  const urlMapping = {};
  
  // Migrate house photos
  for (const house of housesWithPhotos) {
    try {
      console.log(`  Migrating house photo: ${house.name}`);
      
      // Extract filename from Supabase URL
      const filename = house.photoUrl.split('/').pop();
      const tempPath = path.join(tempDir, filename);
      
      // Download from Supabase
      await downloadFile(house.photoUrl, tempPath);
      
      // Upload to Firebase Storage
      const firebasePath = `images/houses/${house.id}-${filename}`;
      await bucket.upload(tempPath, {
        destination: firebasePath,
        metadata: {
          contentType: 'image/jpeg',
          metadata: {
            houseId: house.id,
            houseName: house.name
          }
        }
      });
      
      // Get public URL
      const file = bucket.file(firebasePath);
      const [url] = await file.getSignedUrl({
        action: 'read',
        expires: '03-01-2500' // Long expiration for public access
      });
      
      // Store mapping
      urlMapping[house.photoUrl] = url;
      
      // Update Firestore document
      await db.collection('houses').doc(house.id).update({
        photoUrl: url
      });
      
      // Clean up temp file
      fs.unlinkSync(tempPath);
      
      console.log(`  ✅ Migrated: ${house.name}`);
    } catch (error) {
      console.error(`  ❌ Error migrating ${house.name}:`, error.message);
    }
  }
  
  // Migrate accessory photos (similar loop)
  for (const accessory of accessoriesWithPhotos) {
    try {
      console.log(`  Migrating accessory photo: ${accessory.name}`);
      
      const filename = accessory.photoUrl.split('/').pop();
      const tempPath = path.join(tempDir, filename);
      
      await downloadFile(accessory.photoUrl, tempPath);
      
      const firebasePath = `images/accessories/${accessory.id}-${filename}`;
      await bucket.upload(tempPath, {
        destination: firebasePath,
        metadata: {
          contentType: 'image/jpeg',
          metadata: {
            accessoryId: accessory.id,
            accessoryName: accessory.name
          }
        }
      });
      
      const file = bucket.file(firebasePath);
      const [url] = await file.getSignedUrl({
        action: 'read',
        expires: '03-01-2500'
      });
      
      urlMapping[accessory.photoUrl] = url;
      
      await db.collection('accessories').doc(accessory.id).update({
        photoUrl: url
      });
      
      fs.unlinkSync(tempPath);
      
      console.log(`  ✅ Migrated: ${accessory.name}`);
    } catch (error) {
      console.error(`  ❌ Error migrating ${accessory.name}:`, error.message);
    }
  }
  
  // Save URL mapping for reference
  fs.writeFileSync(
    path.join(__dirname, 'url-mapping.json'),
    JSON.stringify(urlMapping, null, 2)
  );
  
  // Clean up temp directory
  fs.rmdirSync(tempDir, { recursive: true });
  
  console.log('✅ Storage migration complete!');
  console.log(`📝 URL mapping saved to scripts/url-mapping.json`);
}

// Run migration
migrateStorage().catch(console.error);
```

### 3.3 Firebase Storage Rules

Update `storage.rules`:

```
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Images folder
    match /images/{allPaths=**} {
      // Authenticated users can read all images
      allow read: if request.auth != null;
      
      // Authenticated users can write/upload images
      allow write: if request.auth != null
                   && request.resource.size < 10 * 1024 * 1024  // Max 10MB
                   && request.resource.contentType.matches('image/.*');  // Images only
    }
  }
}
```

### 3.4 Running Storage Migration

```powershell
# After data migration (Phase 5), run storage migration
cd scripts
node migrate-storage.js
```

**Phase 3 Completion Checklist**:
- [ ] Storage migration script created
- [ ] Firebase Storage rules configured
- [ ] Images downloaded from Supabase (when ready)
- [ ] Images uploaded to Firebase Storage (when ready)
- [ ] Database URLs updated (when ready)
- [ ] URL mapping saved for reference

---

## Phase 4: Authentication Migration ⏱️ 2 hours

### 4.1 Configure Firebase Authentication

**Firebase Console Steps**:
1. Go to Firebase Console → Authentication
2. Click "Get Started"
3. Click "Sign-in method" tab
4. Enable "Google" provider:
   - Click "Google"
   - Toggle "Enable"
   - **Project support email**: Your email
   - Click "Save"
5. Configure **Authorized Domains**:
   - Add `dept56.rndpig.com`
   - Add `localhost` (for development)

### 4.2 Google Cloud OAuth Configuration

**Google Cloud Console** (if needed):
1. Go to https://console.cloud.google.com
2. Select project (or Firebase creates one automatically)
3. Navigate to: APIs & Services → OAuth consent screen
4. Configure:
   - **App name**: Department 56 Gallery
   - **User support email**: Your email
   - **Authorized domains**: `dept56.rndpig.com`, `firebaseapp.com`
   - **Developer contact**: Your email
5. Navigate to: APIs & Services → Credentials
6. Find OAuth 2.0 Client ID (auto-created by Firebase)
7. Add **Authorized redirect URIs**:
   - `https://dept56-gallery.firebaseapp.com/__/auth/handler`
   - `https://dept56.rndpig.com/__/auth/handler`
   - `http://localhost:5173/__/auth/handler` (Vite dev server)

### 4.3 Update Auth Component

The dept56 app currently doesn't have separate auth components (auth is handled in DeptApp.tsx). We'll create a proper auth system:

Create `src/components/Auth.tsx`:

```typescript
import React, { useState, useEffect } from 'react';
import { signInWithPopup, signOut as firebaseSignOut, onAuthStateChanged, User } from 'firebase/auth';
import { auth, googleProvider, db } from '../lib/firebase';
import { doc, getDoc, setDoc, serverTimestamp } from 'firebase/firestore';

// Whitelist of allowed admin emails (from original DeptApp.tsx)
const ALLOWED_ADMIN_EMAILS = [
  "rndpig@gmail.com",
  "annadilger@gmail.com",
  "bday1951@gmail.com",
  "drdcreek@gmail.com",
  "ericlday@gmail.com",
  "amyannday@gmail.com",
];

interface AuthProps {
  children: (user: User) => React.ReactNode;
}

export function Auth({ children }: AuthProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        // Check if user is whitelisted
        try {
          const userDoc = await getDoc(doc(db, 'users', firebaseUser.uid));
          
          if (!userDoc.exists()) {
            // New user - check whitelist
            if (firebaseUser.email && ALLOWED_ADMIN_EMAILS.includes(firebaseUser.email)) {
              // Create user document
              await setDoc(doc(db, 'users', firebaseUser.uid), {
                email: firebaseUser.email,
                role: 'admin',
                createdAt: serverTimestamp()
              });
              setUser(firebaseUser);
              setError(null);
            } else {
              // Not whitelisted - sign out
              await firebaseSignOut(auth);
              setUser(null);
              setError('Your email is not whitelisted. Please contact an administrator.');
            }
          } else {
            // Existing user
            setUser(firebaseUser);
            setError(null);
          }
        } catch (err) {
          console.error('Error checking user:', err);
          setError('Error verifying user access');
          await firebaseSignOut(auth);
          setUser(null);
        }
      } else {
        setUser(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const signIn = async () => {
    try {
      setError(null);
      await signInWithPopup(auth, googleProvider);
      // onAuthStateChanged will handle the rest
    } catch (err: any) {
      console.error('Sign-in error:', err);
      setError(err.message || 'Failed to sign in');
    }
  };

  const signOut = async () => {
    try {
      await firebaseSignOut(auth);
      setUser(null);
      setError(null);
    } catch (err: any) {
      console.error('Sign-out error:', err);
      setError(err.message || 'Failed to sign out');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full px-6">
          <div className="bg-white rounded-3xl shadow-lg p-8">
            <h1 className="text-3xl font-bold text-center mb-2">
              🏠 Department 56 Gallery
            </h1>
            <p className="text-gray-600 text-center mb-8">
              Sign in to manage your collection
            </p>
            
            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
                {error}
              </div>
            )}
            
            <button
              onClick={signIn}
              className="w-full bg-red-600 text-white rounded-xl py-3 px-4 font-medium hover:bg-red-700 transition flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Sign in with Google
            </button>
            
            <p className="mt-6 text-xs text-gray-500 text-center">
              Only authorized users can access this app.
              <br />
              Contact an administrator if you need access.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Optional: Add sign-out button in header */}
      {children(user)}
    </div>
  );
}
```

### 4.4 Update App.tsx

Update `src/App.tsx` to use the new Auth component:

```typescript
import { Auth } from './components/Auth';
import DeptApp from './DeptApp';

export default function App() {
  return (
    <Auth>
      {(user) => <DeptApp user={user} />}
    </Auth>
  );
}
```

**Phase 4 Completion Checklist**:
- [ ] Firebase Authentication enabled in console
- [ ] Google OAuth provider configured
- [ ] Authorized domains added (localhost, dept56.rndpig.com)
- [ ] Google Cloud OAuth redirect URIs configured
- [ ] Auth component created (src/components/Auth.tsx)
- [ ] App.tsx updated to use Auth wrapper
- [ ] Whitelist logic implemented
- [ ] Sign-in/sign-out tested locally

---

## Phase 5: Data Migration ⏱️ 4-6 hours

### 5.1 Export Data from Supabase

Create `scripts/export-supabase.js`:

```javascript
require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
);

async function exportData() {
  console.log('📦 Exporting data from Supabase...');
  
  const tables = [
    'houses',
    'accessories',
    'collections',
    'tags',
    'house_accessory_links',
    'house_collections',
    'accessory_collections',
    'house_tags',
    'accessory_tags'
  ];
  
  const exportData = {
    exportDate: new Date().toISOString(),
    tables: {}
  };
  
  for (const table of tables) {
    console.log(`  Exporting ${table}...`);
    const { data, error } = await supabase
      .from(table)
      .select('*');
    
    if (error) {
      console.error(`  ❌ Error exporting ${table}:`, error);
      continue;
    }
    
    exportData.tables[table] = data;
    console.log(`  ✅ Exported ${data.length} records from ${table}`);
  }
  
  // Save to file
  const exportPath = path.join(__dirname, 'supabase-export.json');
  fs.writeFileSync(exportPath, JSON.stringify(exportData, null, 2));
  
  console.log('✅ Export complete!');
  console.log(`📝 Saved to: ${exportPath}`);
  console.log('\nSummary:');
  for (const [table, data] of Object.entries(exportData.tables)) {
    console.log(`  - ${table}: ${data.length} records`);
  }
}

exportData().catch(console.error);
```

Run export:

```powershell
cd scripts
node export-supabase.js
```

### 5.2 Transform & Import to Firestore

Create `scripts/import-firestore.js`:

```javascript
const admin = require('firebase-admin');
const fs = require('fs');
const path = require('path');

// Initialize Firebase Admin
const serviceAccount = require('../firebase-service-account.json');
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

// Helper: Convert snake_case to camelCase
function toCamelCase(str) {
  return str.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
}

// Helper: Transform object keys from snake_case to camelCase
function transformKeys(obj) {
  if (!obj || typeof obj !== 'object') return obj;
  
  const transformed = {};
  for (const [key, value] of Object.entries(obj)) {
    transformed[toCamelCase(key)] = value;
  }
  return transformed;
}

// Helper: Convert ISO timestamp to Firestore Timestamp
function toTimestamp(isoString) {
  if (!isoString) return admin.firestore.FieldValue.serverTimestamp();
  return admin.firestore.Timestamp.fromDate(new Date(isoString));
}

// Transform house data
function transformHouse(house) {
  const transformed = transformKeys(house);
  delete transformed.id; // Will use as document ID
  
  // Convert timestamps
  transformed.createdAt = toTimestamp(house.created_at);
  transformed.updatedAt = toTimestamp(house.updated_at);
  
  return transformed;
}

// Transform accessory (same as house)
const transformAccessory = transformHouse;

// Transform collection
function transformCollection(collection) {
  const transformed = transformKeys(collection);
  delete transformed.id;
  transformed.createdAt = toTimestamp(collection.created_at);
  return transformed;
}

// Transform tag
const transformTag = transformCollection;

// Transform link
function transformLink(link) {
  const transformed = transformKeys(link);
  delete transformed.id;
  transformed.createdAt = toTimestamp(link.created_at);
  return transformed;
}

async function importData() {
  console.log('📥 Importing data to Firestore...');
  
  // Load export
  const exportPath = path.join(__dirname, 'supabase-export.json');
  const exportData = JSON.parse(fs.readFileSync(exportPath, 'utf8'));
  
  const tables = exportData.tables;
  const stats = {};
  
  // Import houses
  console.log('  Importing houses...');
  const houses = tables.houses || [];
  for (const house of houses) {
    const transformed = transformHouse(house);
    await db.collection('houses').doc(house.id).set(transformed);
  }
  stats.houses = houses.length;
  console.log(`  ✅ Imported ${houses.length} houses`);
  
  // Import accessories
  console.log('  Importing accessories...');
  const accessories = tables.accessories || [];
  for (const accessory of accessories) {
    const transformed = transformAccessory(accessory);
    await db.collection('accessories').doc(accessory.id).set(transformed);
  }
  stats.accessories = accessories.length;
  console.log(`  ✅ Imported ${accessories.length} accessories`);
  
  // Import collections
  console.log('  Importing collections...');
  const collections = tables.collections || [];
  for (const collection of collections) {
    const transformed = transformCollection(collection);
    await db.collection('collections').doc(collection.id).set(transformed);
  }
  stats.collections = collections.length;
  console.log(`  ✅ Imported ${collections.length} collections`);
  
  // Import tags
  console.log('  Importing tags...');
  const tags = tables.tags || [];
  for (const tag of tags) {
    const transformed = transformTag(tag);
    await db.collection('tags').doc(tag.id).set(transformed);
  }
  stats.tags = tags.length;
  console.log(`  ✅ Imported ${tags.length} tags`);
  
  // Import house_accessory_links
  console.log('  Importing house-accessory links...');
  const houseAccessoryLinks = tables.house_accessory_links || [];
  for (const link of houseAccessoryLinks) {
    const transformed = transformLink(link);
    await db.collection('houseAccessoryLinks').doc(link.id).set(transformed);
  }
  stats.houseAccessoryLinks = houseAccessoryLinks.length;
  console.log(`  ✅ Imported ${houseAccessoryLinks.length} house-accessory links`);
  
  // Import house_collections
  console.log('  Importing house-collection links...');
  const houseCollections = tables.house_collections || [];
  for (const link of houseCollections) {
    const transformed = transformLink(link);
    await db.collection('houseCollections').doc(link.id).set(transformed);
  }
  stats.houseCollections = houseCollections.length;
  console.log(`  ✅ Imported ${houseCollections.length} house-collection links`);
  
  // Import accessory_collections
  console.log('  Importing accessory-collection links...');
  const accessoryCollections = tables.accessory_collections || [];
  for (const link of accessoryCollections) {
    const transformed = transformLink(link);
    await db.collection('accessoryCollections').doc(link.id).set(transformed);
  }
  stats.accessoryCollections = accessoryCollections.length;
  console.log(`  ✅ Imported ${accessoryCollections.length} accessory-collection links`);
  
  // Import house_tags
  console.log('  Importing house-tag links...');
  const houseTags = tables.house_tags || [];
  for (const link of houseTags) {
    const transformed = transformLink(link);
    await db.collection('houseTags').doc(link.id).set(transformed);
  }
  stats.houseTags = houseTags.length;
  console.log(`  ✅ Imported ${houseTags.length} house-tag links`);
  
  // Import accessory_tags
  console.log('  Importing accessory-tag links...');
  const accessoryTags = tables.accessory_tags || [];
  for (const link of accessoryTags) {
    const transformed = transformLink(link);
    await db.collection('accessoryTags').doc(link.id).set(transformed);
  }
  stats.accessoryTags = accessoryTags.length;
  console.log(`  ✅ Imported ${accessoryTags.length} accessory-tag links`);
  
  // Save stats
  fs.writeFileSync(
    path.join(__dirname, 'import-stats.json'),
    JSON.stringify(stats, null, 2)
  );
  
  console.log('✅ Import complete!');
  console.log('\nSummary:');
  for (const [collection, count] of Object.entries(stats)) {
    console.log(`  - ${collection}: ${count} documents`);
  }
}

importData().catch(console.error);
```

### 5.3 Run Data Migration

```powershell
# Step 1: Export from Supabase
cd scripts
node export-supabase.js

# Step 2: Review export (optional)
# Open scripts/supabase-export.json to verify

# Step 3: Import to Firestore
node import-firestore.js

# Step 4: Verify in Firebase Console
# Go to Firestore Database and check collections
```

### 5.4 Verification Script

Create `scripts/verify-migration.js`:

```javascript
const admin = require('firebase-admin');
const fs = require('fs');
const path = require('path');

const serviceAccount = require('../firebase-service-account.json');
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

async function verifyMigration() {
  console.log('🔍 Verifying migration...');
  
  // Load export to compare
  const exportPath = path.join(__dirname, 'supabase-export.json');
  const exportData = JSON.parse(fs.readFileSync(exportPath, 'utf8'));
  
  const collections = [
    'houses',
    'accessories',
    'collections',
    'tags',
    'houseAccessoryLinks',
    'houseCollections',
    'accessoryCollections',
    'houseTags',
    'accessoryTags'
  ];
  
  const results = {};
  
  for (const collectionName of collections) {
    const snapshot = await db.collection(collectionName).get();
    const count = snapshot.size;
    
    // Get original table name (camelCase -> snake_case)
    const tableName = collectionName.replace(/([A-Z])/g, '_$1').toLowerCase();
    const originalCount = (exportData.tables[tableName] || []).length;
    
    results[collectionName] = {
      firestore: count,
      supabase: originalCount,
      match: count === originalCount
    };
    
    const status = count === originalCount ? '✅' : '❌';
    console.log(`${status} ${collectionName}: ${count} (Supabase: ${originalCount})`);
  }
  
  // Check for any mismatches
  const mismatches = Object.entries(results).filter(([_, r]) => !r.match);
  
  if (mismatches.length === 0) {
    console.log('\n✅ All collections match! Migration successful.');
  } else {
    console.log('\n⚠️  Some collections have mismatches:');
    mismatches.forEach(([name, result]) => {
      console.log(`  - ${name}: Firestore=${result.firestore}, Supabase=${result.supabase}`);
    });
  }
  
  // Save results
  fs.writeFileSync(
    path.join(__dirname, 'verification-results.json'),
    JSON.stringify(results, null, 2)
  );
}

verifyMigration().catch(console.error);
```

Run verification:

```powershell
node verify-migration.js
```

**Phase 5 Completion Checklist**:
- [ ] Export script created and run (export-supabase.js)
- [ ] Data exported successfully (supabase-export.json)
- [ ] Import script created (import-firestore.js)
- [ ] Data imported to Firestore
- [ ] Verification script run (verify-migration.js)
- [ ] All collection counts match
- [ ] Sample documents checked in Firebase Console
- [ ] Relationships preserved (IDs intact)

---

**Continue to**: [FIREBASE_MIGRATION_PHASE6-10.md](./FIREBASE_MIGRATION_PHASE6-10.md) for code migration, testing, and deployment.
