# Firebase Migration - Phases 6-10

**Document**: Code Migration, Testing, Deployment, and Post-Migration  
**Part of**: [Main Migration Plan](./FIREBASE_MIGRATION_PLAN.md)

---

## Phase 6: Code Migration ⏱️ 6-8 hours

### 6.1 Update lib/firebase.ts (Enhanced Version)

Expand `src/lib/firebase.ts` with CRUD helper functions:

```typescript
import { initializeApp, getApps } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut as firebaseSignOut, onAuthStateChanged, User } from 'firebase/auth';
import { 
  getFirestore, 
  collection, 
  doc, 
  getDoc, 
  getDocs, 
  addDoc, 
  updateDoc, 
  deleteDoc, 
  query, 
  where, 
  orderBy,
  Timestamp,
  DocumentData,
  QueryDocumentSnapshot,
  serverTimestamp,
  writeBatch
} from 'firebase/firestore';
import { 
  getStorage,
  ref,
  uploadBytes,
  getDownloadURL,
  deleteObject
} from 'firebase/storage';
import type { 
  FirestoreHouse,
  FirestoreAccessory,
  FirestoreCollection,
  FirestoreTag,
  FirestoreHouseAccessoryLink,
  FirestoreHouseCollection,
  FirestoreAccessoryCollection,
  FirestoreHouseTag,
  FirestoreAccessoryTag,
  House,
  Accessory,
  Collection as AppCollection,
  Tag,
  HouseAccessoryLink,
  HouseCollection,
  AccessoryCollection,
  HouseTag,
  AccessoryTag
} from '@/types/firestore';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

if (!firebaseConfig.apiKey || !firebaseConfig.projectId) {
  throw new Error('Missing Firebase environment variables. Check .env.local file.');
}

// Initialize Firebase (only once)
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];

// Initialize services
export const auth = getAuth(app);
export const db = getFirestore(app);
export const storage = getStorage(app);
export const googleProvider = new GoogleAuthProvider();

// ============================================
// HELPER FUNCTIONS
// ============================================

// Convert Firestore Timestamp to Date
function timestampToDate(timestamp: Timestamp): Date {
  return timestamp.toDate();
}

// Convert document snapshot to typed object
function convertHouse(doc: QueryDocumentSnapshot<DocumentData>): House {
  const data = doc.data() as FirestoreHouse;
  return {
    id: doc.id,
    userId: data.userId,
    name: data.name,
    year: data.year,
    retiredYear: data.retiredYear,
    description: data.description,
    sku: data.sku,
    notes: data.notes,
    photoUrl: data.photoUrl,
    purchasedYear: data.purchasedYear,
    price: data.price,
    collection: data.collection,
    series: data.series,
    createdAt: timestampToDate(data.createdAt),
    updatedAt: timestampToDate(data.updatedAt),
  };
}

function convertAccessory(doc: QueryDocumentSnapshot<DocumentData>): Accessory {
  const data = doc.data() as FirestoreAccessory;
  return {
    id: doc.id,
    userId: data.userId,
    name: data.name,
    year: data.year,
    retiredYear: data.retiredYear,
    description: data.description,
    sku: data.sku,
    notes: data.notes,
    photoUrl: data.photoUrl,
    purchasedYear: data.purchasedYear,
    price: data.price,
    collection: data.collection,
    series: data.series,
    createdAt: timestampToDate(data.createdAt),
    updatedAt: timestampToDate(data.updatedAt),
  };
}

function convertCollection(doc: QueryDocumentSnapshot<DocumentData>): AppCollection {
  const data = doc.data() as FirestoreCollection;
  return {
    id: doc.id,
    userId: data.userId,
    name: data.name,
    notes: data.notes,
    createdAt: timestampToDate(data.createdAt),
  };
}

function convertTag(doc: QueryDocumentSnapshot<DocumentData>): Tag {
  const data = doc.data() as FirestoreTag;
  return {
    id: doc.id,
    userId: data.userId,
    name: data.name,
    createdAt: timestampToDate(data.createdAt),
  };
}

function convertLink<T extends { createdAt: Timestamp }>(doc: QueryDocumentSnapshot<DocumentData>): any {
  const data = doc.data() as T;
  return {
    id: doc.id,
    ...data,
    createdAt: timestampToDate(data.createdAt),
  };
}

// ============================================
// HOUSES CRUD
// ============================================

export async function getHouses(userId: string): Promise<House[]> {
  const q = query(
    collection(db, 'houses'),
    where('userId', '==', userId),
    orderBy('createdAt', 'desc')
  );
  const snapshot = await getDocs(q);
  return snapshot.docs.map(convertHouse);
}

export async function getHouse(houseId: string): Promise<House | null> {
  const docRef = doc(db, 'houses', houseId);
  const docSnap = await getDoc(docRef);
  return docSnap.exists() ? convertHouse(docSnap as QueryDocumentSnapshot<DocumentData>) : null;
}

export async function addHouse(userId: string, houseData: Omit<House, 'id' | 'userId' | 'createdAt' | 'updatedAt'>): Promise<string> {
  const docRef = await addDoc(collection(db, 'houses'), {
    userId,
    ...houseData,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
  });
  return docRef.id;
}

export async function updateHouse(houseId: string, updates: Partial<Omit<House, 'id' | 'createdAt'>>): Promise<void> {
  const docRef = doc(db, 'houses', houseId);
  await updateDoc(docRef, {
    ...updates,
    updatedAt: serverTimestamp(),
  });
}

export async function deleteHouse(houseId: string): Promise<void> {
  // Delete house document
  await deleteDoc(doc(db, 'houses', houseId));
  
  // Clean up related links
  const batch = writeBatch(db);
  
  // Delete house-accessory links
  const houseAccessoryLinksSnap = await getDocs(query(collection(db, 'houseAccessoryLinks'), where('houseId', '==', houseId)));
  houseAccessoryLinksSnap.docs.forEach(doc => batch.delete(doc.ref));
  
  // Delete house-collection links
  const houseCollectionsSnap = await getDocs(query(collection(db, 'houseCollections'), where('houseId', '==', houseId)));
  houseCollectionsSnap.docs.forEach(doc => batch.delete(doc.ref));
  
  // Delete house-tag links
  const houseTagsSnap = await getDocs(query(collection(db, 'houseTags'), where('houseId', '==', houseId)));
  houseTagsSnap.docs.forEach(doc => batch.delete(doc.ref));
  
  await batch.commit();
}

// ============================================
// ACCESSORIES CRUD
// ============================================

export async function getAccessories(userId: string): Promise<Accessory[]> {
  const q = query(
    collection(db, 'accessories'),
    where('userId', '==', userId),
    orderBy('createdAt', 'desc')
  );
  const snapshot = await getDocs(q);
  return snapshot.docs.map(convertAccessory);
}

export async function getAccessory(accessoryId: string): Promise<Accessory | null> {
  const docRef = doc(db, 'accessories', accessoryId);
  const docSnap = await getDoc(docRef);
  return docSnap.exists() ? convertAccessory(docSnap as QueryDocumentSnapshot<DocumentData>) : null;
}

export async function addAccessory(userId: string, accessoryData: Omit<Accessory, 'id' | 'userId' | 'createdAt' | 'updatedAt'>): Promise<string> {
  const docRef = await addDoc(collection(db, 'accessories'), {
    userId,
    ...accessoryData,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
  });
  return docRef.id;
}

export async function updateAccessory(accessoryId: string, updates: Partial<Omit<Accessory, 'id' | 'createdAt'>>): Promise<void> {
  const docRef = doc(db, 'accessories', accessoryId);
  await updateDoc(docRef, {
    ...updates,
    updatedAt: serverTimestamp(),
  });
}

export async function deleteAccessory(accessoryId: string): Promise<void> {
  await deleteDoc(doc(db, 'accessories', accessoryId));
  
  // Clean up related links
  const batch = writeBatch(db);
  
  const accessoryLinksSnap = await getDocs(query(collection(db, 'houseAccessoryLinks'), where('accessoryId', '==', accessoryId)));
  accessoryLinksSnap.docs.forEach(doc => batch.delete(doc.ref));
  
  const accessoryCollectionsSnap = await getDocs(query(collection(db, 'accessoryCollections'), where('accessoryId', '==', accessoryId)));
  accessoryCollectionsSnap.docs.forEach(doc => batch.delete(doc.ref));
  
  const accessoryTagsSnap = await getDocs(query(collection(db, 'accessoryTags'), where('accessoryId', '==', accessoryId)));
  accessoryTagsSnap.docs.forEach(doc => batch.delete(doc.ref));
  
  await batch.commit();
}

// ============================================
// COLLECTIONS CRUD
// ============================================

export async function getCollections(userId: string): Promise<AppCollection[]> {
  const q = query(
    collection(db, 'collections'),
    where('userId', '==', userId),
    orderBy('createdAt', 'desc')
  );
  const snapshot = await getDocs(q);
  return snapshot.docs.map(convertCollection);
}

export async function addCollection(userId: string, collectionData: Omit<AppCollection, 'id' | 'userId' | 'createdAt'>): Promise<string> {
  const docRef = await addDoc(collection(db, 'collections'), {
    userId,
    ...collectionData,
    createdAt: serverTimestamp(),
  });
  return docRef.id;
}

export async function updateCollection(collectionId: string, updates: Partial<Omit<AppCollection, 'id'>>): Promise<void> {
  await updateDoc(doc(db, 'collections', collectionId), updates);
}

export async function deleteCollection(collectionId: string): Promise<void> {
  await deleteDoc(doc(db, 'collections', collectionId));
  
  // Clean up related links
  const batch = writeBatch(db);
  
  const houseCollectionsSnap = await getDocs(query(collection(db, 'houseCollections'), where('collectionId', '==', collectionId)));
  houseCollectionsSnap.docs.forEach(doc => batch.delete(doc.ref));
  
  const accessoryCollectionsSnap = await getDocs(query(collection(db, 'accessoryCollections'), where('collectionId', '==', collectionId)));
  accessoryCollectionsSnap.docs.forEach(doc => batch.delete(doc.ref));
  
  await batch.commit();
}

// ============================================
// TAGS CRUD
// ============================================

export async function getTags(userId: string): Promise<Tag[]> {
  const q = query(
    collection(db, 'tags'),
    where('userId', '==', userId),
    orderBy('createdAt', 'desc')
  );
  const snapshot = await getDocs(q);
  return snapshot.docs.map(convertTag);
}

export async function addTag(userId: string, tagData: Omit<Tag, 'id' | 'userId' | 'createdAt'>): Promise<string> {
  const docRef = await addDoc(collection(db, 'tags'), {
    userId,
    ...tagData,
    createdAt: serverTimestamp(),
  });
  return docRef.id;
}

export async function deleteTag(tagId: string): Promise<void> {
  await deleteDoc(doc(db, 'tags', tagId));
  
  // Clean up related links
  const batch = writeBatch(db);
  
  const houseTagsSnap = await getDocs(query(collection(db, 'houseTags'), where('tagId', '==', tagId)));
  houseTagsSnap.docs.forEach(doc => batch.delete(doc.ref));
  
  const accessoryTagsSnap = await getDocs(query(collection(db, 'accessoryTags'), where('tagId', '==', tagId)));
  accessoryTagsSnap.docs.forEach(doc => batch.delete(doc.ref));
  
  await batch.commit();
}

// ============================================
// LINK CRUD (Relationships)
// ============================================

export async function getHouseAccessoryLinks(houseId: string): Promise<HouseAccessoryLink[]> {
  const q = query(collection(db, 'houseAccessoryLinks'), where('houseId', '==', houseId));
  const snapshot = await getDocs(q);
  return snapshot.docs.map(convertLink);
}

export async function addHouseAccessoryLink(userId: string, houseId: string, accessoryId: string): Promise<string> {
  const docRef = await addDoc(collection(db, 'houseAccessoryLinks'), {
    userId,
    houseId,
    accessoryId,
    createdAt: serverTimestamp(),
  });
  return docRef.id;
}

export async function deleteHouseAccessoryLink(linkId: string): Promise<void> {
  await deleteDoc(doc(db, 'houseAccessoryLinks', linkId));
}

// Similar functions for other link types...

// ============================================
// STORAGE (Images)
// ============================================

export async function uploadImage(file: File, path: string): Promise<string> {
  const storageRef = ref(storage, path);
  await uploadBytes(storageRef, file);
  const url = await getDownloadURL(storageRef);
  return url;
}

export async function deleteImage(path: string): Promise<void> {
  const storageRef = ref(storage, path);
  await deleteObject(storageRef);
}

// ============================================
// EXPORT DEFAULT
// ============================================

export default app;
```

### 6.2 Update DeptApp.tsx - Query Patterns

This is the most extensive change. The file is 4367 lines, so we'll need to update query patterns throughout. Here are the key patterns to replace:

**Pattern 1: Fetching data**

```typescript
// BEFORE (Supabase)
const { data: houses, error } = await supabase
  .from('houses')
  .select('*')
  .eq('user_id', userId);

// AFTER (Firebase)
import { getHouses } from './lib/firebase';
const houses = await getHouses(userId);
```

**Pattern 2: Adding data**

```typescript
// BEFORE (Supabase)
const { data, error } = await supabase
  .from('houses')
  .insert({
    user_id: userId,
    name: houseName,
    // ... other fields
  })
  .select()
  .single();

// AFTER (Firebase)
import { addHouse } from './lib/firebase';
const houseId = await addHouse(userId, {
  name: houseName,
  // ... other fields
});
```

**Pattern 3: Updating data**

```typescript
// BEFORE (Supabase)
const { error } = await supabase
  .from('houses')
  .update({ name: newName })
  .eq('id', houseId);

// AFTER (Firebase)
import { updateHouse } from './lib/firebase';
await updateHouse(houseId, { name: newName });
```

**Pattern 4: Deleting data**

```typescript
// BEFORE (Supabase)
const { error } = await supabase
  .from('houses')
  .delete()
  .eq('id', houseId);

// AFTER (Firebase)
import { deleteHouse } from './lib/firebase';
await deleteHouse(houseId);
```

**Pattern 5: Image uploads**

```typescript
// BEFORE (Supabase)
const { data, error } = await supabase.storage
  .from('dept56-images')
  .upload(filename, file);

if (!error && data) {
  const { data: { publicUrl } } = supabase.storage
    .from('dept56-images')
    .getPublicUrl(data.path);
  // Use publicUrl
}

// AFTER (Firebase)
import { uploadImage } from './lib/firebase';
const photoUrl = await uploadImage(file, `images/houses/${filename}`);
```

### 6.3 Migration Strategy for DeptApp.tsx

Given the size, I recommend:

1. **Create a new file** `DeptAppFirebase.tsx` alongside the old one
2. **Copy everything** from `DeptApp.tsx`
3. **Update incrementally**:
   - Replace imports (supabase → firebase)
   - Replace queries section by section
   - Test as you go
4. **Once working**, replace old file

**Key sections to update in DeptApp.tsx**:
- Line ~1-50: Imports
- Line ~300-500: useEffect data loading
- Line ~800-1200: Modal handlers (add/edit/delete)
- Line ~2000-2500: Image upload handlers
- Line ~3000-4000: Various CRUD operations

### 6.4 Update Import Statements

```typescript
// Remove Supabase imports
// import { supabase } from "./lib/supabase";
// import * as db from "./lib/database";

// Add Firebase imports
import { auth, db } from "./lib/firebase";
import * as firebaseHelpers from "./lib/firebase";
import type { User } from "firebase/auth";

// Update type imports
// import type { Database, House, Accessory, ... } from "./types/database";
import type { House, Accessory, Collection, Tag, ... } from "./types/firestore";
```

### 6.5 Update Props and State

```typescript
// Add user prop from Auth wrapper
interface DeptAppProps {
  user: User;
}

export default function DeptApp({ user }: DeptAppProps) {
  const userId = user.uid; // Firebase UID instead of Supabase UUID
  
  // Rest of component...
}
```

**Phase 6 Completion Checklist**:
- [ ] lib/firebase.ts expanded with CRUD functions
- [ ] types/firestore.ts created with all types
- [ ] DeptApp.tsx imports updated
- [ ] All Supabase queries replaced with Firebase queries
- [ ] Image upload/download logic updated
- [ ] User ID references changed (user_id → userId)
- [ ] Field names changed (snake_case → camelCase)
- [ ] Local testing passes (npm run dev works)

---

## Phase 7: Build Configuration ⏱️ 1 hour

### 7.1 Update firebase.json

```json
{
  "firestore": {
    "rules": "firestore.rules",
    "indexes": "firestore.indexes.json"
  },
  "storage": {
    "rules": "storage.rules"
  },
  "hosting": {
    "public": "dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(jpg|jpeg|gif|png|svg|webp)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000"
          }
        ]
      },
      {
        "source": "**/*.@(js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000, immutable"
          }
        ]
      },
      {
        "source": "**",
        "headers": [
          {
            "key": "X-Content-Type-Options",
            "value": "nosniff"
          },
          {
            "key": "X-Frame-Options",
            "value": "DENY"
          },
          {
            "key": "X-XSS-Protection",
            "value": "1; mode=block"
          }
        ]
      }
    ]
  }
}
```

### 7.2 Firestore Security Rules

Create `firestore.rules`:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Helper functions
    function isAuthenticated() {
      return request.auth != null;
    }
    
    function isOwner(userId) {
      return isAuthenticated() && request.auth.uid == userId;
    }
    
    function isOwnerOfDocument() {
      return isAuthenticated() && request.auth.uid == resource.data.userId;
    }
    
    // Users collection
    match /users/{userId} {
      allow read: if isAuthenticated();
      allow create, update, delete: if isOwner(userId);
    }
    
    // Houses collection
    match /houses/{houseId} {
      allow read: if isAuthenticated() && isOwnerOfDocument();
      allow create: if isAuthenticated() && isOwner(request.resource.data.userId);
      allow update, delete: if isAuthenticated() && isOwnerOfDocument();
    }
    
    // Accessories collection
    match /accessories/{accessoryId} {
      allow read: if isAuthenticated() && isOwnerOfDocument();
      allow create: if isAuthenticated() && isOwner(request.resource.data.userId);
      allow update, delete: if isAuthenticated() && isOwnerOfDocument();
    }
    
    // Collections collection
    match /collections/{collectionId} {
      allow read: if isAuthenticated() && isOwnerOfDocument();
      allow create: if isAuthenticated() && isOwner(request.resource.data.userId);
      allow update, delete: if isAuthenticated() && isOwnerOfDocument();
    }
    
    // Tags collection
    match /tags/{tagId} {
      allow read: if isAuthenticated() && isOwnerOfDocument();
      allow create: if isAuthenticated() && isOwner(request.resource.data.userId);
      allow update, delete: if isAuthenticated() && isOwnerOfDocument();
    }
    
    // House-Accessory links
    match /houseAccessoryLinks/{linkId} {
      allow read: if isAuthenticated() && isOwnerOfDocument();
      allow create: if isAuthenticated() && isOwner(request.resource.data.userId);
      allow delete: if isAuthenticated() && isOwnerOfDocument();
    }
    
    // House-Collection links
    match /houseCollections/{linkId} {
      allow read: if isAuthenticated() && isOwnerOfDocument();
      allow create: if isAuthenticated() && isOwner(request.resource.data.userId);
      allow delete: if isAuthenticated() && isOwnerOfDocument();
    }
    
    // Accessory-Collection links
    match /accessoryCollections/{linkId} {
      allow read: if isAuthenticated() && isOwnerOfDocument();
      allow create: if isAuthenticated() && isOwner(request.resource.data.userId);
      allow delete: if isAuthenticated() && isOwnerOfDocument();
    }
    
    // House-Tag links
    match /houseTags/{linkId} {
      allow read: if isAuthenticated() && isOwnerOfDocument();
      allow create: if isAuthenticated() && isOwner(request.resource.data.userId);
      allow update, delete: if isAuthenticated() && isOwnerOfDocument();
    }
    
    // Accessory-Tag links
    match /accessoryTags/{linkId} {
      allow read: if isAuthenticated() && isOwnerOfDocument();
      allow create: if isAuthenticated() && isOwner(request.resource.data.userId);
      allow update, delete: if isAuthenticated() && isOwnerOfDocument();
    }
  }
}
```

### 7.3 Firebase Storage Rules

Update `storage.rules`:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Images folder
    match /images/{type}/{imageId} {
      // Allow read if authenticated
      allow read: if request.auth != null;
      
      // Allow write if authenticated and file meets requirements
      allow write: if request.auth != null
                   && request.resource.size < 10 * 1024 * 1024  // Max 10MB
                   && request.resource.contentType.matches('image/.*');  // Images only
    }
  }
}
```

### 7.4 Deploy Firestore Rules & Indexes

```powershell
# Deploy just the rules and indexes (before deploying app)
firebase deploy --only firestore:rules,firestore:indexes,storage
```

**Phase 7 Completion Checklist**:
- [ ] firebase.json configured with hosting settings
- [ ] firestore.rules created with RLS-like security
- [ ] storage.rules created with upload restrictions
- [ ] firestore.indexes.json created
- [ ] Rules and indexes deployed to Firebase
- [ ] Rules tested in Firebase Console (Firestore → Rules)

---

## Phase 8: Testing ⏱️ 4-6 hours

### 8.1 Local Development Testing

```powershell
# Start dev server with Firebase
npm run dev
```

**Test Checklist**:

**Authentication Testing**:
- [ ] Sign in with Google (popup appears)
- [ ] Whitelisted email accepts successfully
- [ ] Non-whitelisted email rejects correctly
- [ ] User document created in Firestore
- [ ] Sign out works correctly
- [ ] Session persists on page refresh

**Houses CRUD**:
- [ ] View all houses (list loads)
- [ ] Add new house (with all fields)
- [ ] Add house with image upload
- [ ] Edit existing house
- [ ] Delete house (with confirmation)
- [ ] Search/filter houses

**Accessories CRUD**:
- [ ] View all accessories
- [ ] Add new accessory
- [ ] Add accessory with image
- [ ] Edit existing accessory
- [ ] Delete accessory

**Collections**:
- [ ] Create new collection
- [ ] Link house to collection
- [ ] Link accessory to collection
- [ ] View items in collection
- [ ] Unlink items from collection
- [ ] Delete collection

**Tags**:
- [ ] Create new tag
- [ ] Assign tag to house
- [ ] Assign tag to accessory
- [ ] Tag confidence/source display
- [ ] Mark tag as reviewed
- [ ] Delete tag

**Relationships**:
- [ ] Link accessory to house
- [ ] View accessories for house
- [ ] View houses for accessory
- [ ] Unlink accessory from house
- [ ] Cascade delete (delete house deletes links)

**Search & Filter**:
- [ ] Fuzzy search by name
- [ ] Filter by collection
- [ ] Filter by tag
- [ ] Filter by year
- [ ] Combined filters work

**Image Testing**:
- [ ] Image upload works
- [ ] Image displays correctly
- [ ] Image URLs load
- [ ] Image delete works
- [ ] Multiple image formats (JPG, PNG)
- [ ] Image size validation (max 10MB)

### 8.2 Browser Console Testing

Open browser DevTools → Console and test Firebase connection:

```javascript
// Test Firestore connection
import { db } from './lib/firebase';
console.log('Firestore:', db);

// Test Auth state
import { auth } from './lib/firebase';
console.log('Current user:', auth.currentUser);

// Test query
import { collection, getDocs } from 'firebase/firestore';
const housesSnap = await getDocs(collection(db, 'houses'));
console.log('Houses count:', housesSnap.size);
```

### 8.3 Error Handling Testing

**Test error scenarios**:
- [ ] Network offline (graceful degradation)
- [ ] Permission denied (security rules)
- [ ] Invalid data (type checking)
- [ ] File too large (upload validation)
- [ ] Missing required fields
- [ ] Concurrent edits (optimistic updates)

### 8.4 Performance Testing

**Measure performance**:
- [ ] Initial page load time
- [ ] Time to fetch houses/accessories
- [ ] Image load times
- [ ] Search response time
- [ ] Filter response time

Use browser DevTools → Network tab to monitor:
- Firestore queries
- Storage downloads
- Auth API calls

**Phase 8 Completion Checklist**:
- [ ] All authentication flows tested
- [ ] All CRUD operations tested for each entity
- [ ] All relationships tested
- [ ] Search and filtering tested
- [ ] Image upload/display tested
- [ ] Error scenarios handled gracefully
- [ ] Performance acceptable (<2s load time)
- [ ] No console errors or warnings

---

## Phase 9: Deployment ⏱️ 2 hours

### 9.1 Pre-Deployment Checklist

- [ ] All tests passing locally
- [ ] No console errors in development
- [ ] Environment variables set correctly
- [ ] Firebase rules deployed
- [ ] Firestore indexes deployed
- [ ] Service account key secured (not in git!)
- [ ] .env.local not in git

### 9.2 Build Production Bundle

```powershell
# Build for production
npm run build

# Verify build output
ls dist

# Preview production build locally (optional)
npm run preview
```

**Expected output**:
```
dist/
├── assets/
│   ├── index-[hash].js
│   ├── index-[hash].css
│   └── [other bundled assets]
├── index.html
└── vite.svg
```

### 9.3 Deploy to Firebase Hosting

```powershell
# Deploy everything (hosting, rules, indexes)
firebase deploy

# Or deploy only hosting
firebase deploy --only hosting
```

**Expected output**:
```
=== Deploying to 'dept56-gallery'...

✔  Deploy complete!

Project Console: https://console.firebase.google.com/project/dept56-gallery/overview
Hosting URL: https://dept56-gallery.web.app
```

### 9.4 Verify Firebase Deployment

1. **Open Hosting URL**: https://dept56-gallery.web.app
2. **Test authentication**: Sign in with Google
3. **Test basic CRUD**: Add a test house
4. **Check Firestore**: Verify document created
5. **Test image upload**: Upload test image
6. **Check Storage**: Verify image in Firebase Storage

### 9.5 Update Cloudflare DNS

**Current DNS** (Vercel):
```
Type: CNAME
Name: dept56
Content: cname.vercel-dns.com
Proxy: OFF
```

**New DNS** (Firebase):
```
Type: CNAME
Name: dept56
Content: dept56-gallery.web.app
Proxy: OFF (orange cloud DISABLED)
TTL: Auto
```

**Steps**:
1. Go to Cloudflare Dashboard
2. Select domain: rndpig.com
3. Go to DNS → Records
4. Find `dept56` CNAME record
5. Click "Edit"
6. Change content to: `dept56-gallery.web.app`
7. Ensure Proxy is OFF (gray cloud)
8. Save

### 9.6 Add Custom Domain in Firebase

1. **Firebase Console** → Hosting → Add custom domain
2. Enter domain: `dept56.rndpig.com`
3. Firebase will verify DNS (sees the CNAME)
4. Click "Continue"
5. Firebase provisions SSL certificate (10-60 minutes)
6. Wait for "Connected" status

**DNS Verification**:
```powershell
# Check DNS propagation
nslookup dept56.rndpig.com

# Should return Firebase IP
```

### 9.7 SSL Certificate Provisioning

**Firebase automatically provisions SSL certificates** for custom domains.

**Status progression**:
1. 🟡 Pending (DNS verification)
2. 🟡 Provisioning (SSL cert request)
3. 🟢 Connected (Live with HTTPS)

**Timeline**: Usually 10-30 minutes, can take up to 24 hours.

**Check status**:
- Firebase Console → Hosting → Custom domains
- Look for green checkmark

### 9.8 Test Production Deployment

Once SSL is active:

1. **Visit**: https://dept56.rndpig.com
2. **Verify HTTPS**: Green lock icon
3. **Test sign-in**: Google OAuth should work
4. **Test CRUD**: Add/edit/delete operations
5. **Test images**: Upload and display
6. **Test on mobile**: Responsive design

**Phase 9 Completion Checklist**:
- [ ] Production build created successfully
- [ ] Firebase Hosting deployed
- [ ] Hosting URL accessible (https://dept56-gallery.web.app)
- [ ] Cloudflare DNS updated to Firebase
- [ ] Custom domain added in Firebase Console
- [ ] SSL certificate provisioned (green checkmark)
- [ ] Custom domain accessible (https://dept56.rndpig.com)
- [ ] HTTPS working (green lock)
- [ ] All functionality tested in production
- [ ] No console errors in production

---

## Phase 10: Post-Migration ⏱️ 1 hour

### 10.1 Production Verification (24-48 hours)

**Monitor for**:
- [ ] Authentication issues
- [ ] Data loading problems
- [ ] Image display issues
- [ ] Performance degradation
- [ ] Security rule violations
- [ ] User-reported bugs

**Firebase Console Monitoring**:
- Go to Console → Analytics → Dashboard
- Monitor active users
- Check error logs (Console → Firestore → Logs)
- Review storage usage (Storage → Usage)

### 10.2 Update Documentation

**README.md updates**:
```markdown
# Department 56 Gallery

## 🚀 Now powered by Firebase!

- **Database**: Cloud Firestore
- **Storage**: Firebase Storage
- **Authentication**: Firebase Auth (Google OAuth)
- **Hosting**: Firebase Hosting
- **Domain**: https://dept56.rndpig.com

## Quick Start

1. Clone repository
2. Install dependencies: `npm install`
3. Create `.env.local` with Firebase config
4. Run dev server: `npm run dev`
5. Deploy: `firebase deploy`

## Firebase Configuration

See `.env.local.example` for required environment variables.
```

**QUICKSTART.md updates**:
- Replace Supabase setup with Firebase setup
- Update environment variable instructions
- Update deployment instructions

### 10.3 Create Migration Summary

Create `MIGRATION_COMPLETE.md`:

```markdown
# Firebase Migration - Complete ✅

**Migration Date**: [DATE]  
**Status**: ✅ Production  
**Duration**: [X] days

## What Changed

### Before (Supabase)
- Database: Supabase PostgreSQL (9 tables)
- Storage: Supabase Storage
- Auth: Supabase Auth
- Hosting: Vercel
- Domain: dept56.rndpig.com via Cloudflare

### After (Firebase)
- Database: Cloud Firestore (9 collections)
- Storage: Firebase Storage
- Auth: Firebase Authentication
- Hosting: Firebase Hosting
- Domain: dept56.rndpig.com via Cloudflare

## Data Migration Stats

- Houses: [X] migrated
- Accessories: [X] migrated
- Collections: [X] migrated
- Tags: [X] migrated
- Images: [X] migrated
- Total documents: [X]

## Benefits Realized

✅ Single service provider (Firebase)  
✅ Simplified authentication (no callback routes)  
✅ Unified console and billing  
✅ Better free tier limits  
✅ Integrated hosting with database  

## Decommission Plan

### Supabase (30-day grace period)

- **Keep Active Until**: [DATE + 30 days]
- **Final Backup**: [DATE]
- **Pause Project**: [DATE + 30 days]
- **Delete Project**: [DATE + 60 days] (optional)

### Vercel

- **Keep Active Until**: [DATE + 30 days]
- **Remove Project**: [DATE + 30 days]

## Rollback Plan (if needed)

If critical issues arise:

1. Revert Cloudflare DNS to Vercel
2. Re-enable Supabase project
3. Deploy last Vercel version
4. Investigate Firebase issues
5. Fix and re-deploy

Rollback window: 30 days
```

### 10.4 Archive Old Code

```powershell
# Create archive branch (before deleting Supabase code)
git checkout -b archive/supabase-version
git push origin archive/supabase-version

# Return to main
git checkout main
```

**Keep for reference**:
- `src/lib/supabase.ts` (in archive branch)
- `supabase-schema.sql` (in archive branch)
- Old environment variables (document somewhere)

### 10.5 Decommission Supabase (After 30 days)

**Only after confirming production stability**:

1. **Download Final Backup**:
   ```sql
   -- In Supabase SQL Editor
   -- Export all data one last time
   ```

2. **Pause Project** (stops billing):
   - Supabase Dashboard → Settings → General
   - Scroll to "Pause Project"
   - Click "Pause Project"

3. **Document Credentials** (for emergency recovery):
   - Save Supabase URL
   - Save API keys (encrypted)
   - Store backup files securely

4. **Delete Project** (optional, after 60 days):
   - Supabase Dashboard → Settings → General
   - Scroll to "Delete Project"
   - Confirm deletion

### 10.6 Decommission Vercel

1. **Remove Project**:
   - Vercel Dashboard → Settings
   - Scroll to "Delete Project"
   - Confirm deletion

2. **Update GitHub Actions** (if any):
   - Remove Vercel deployment workflows
   - Add Firebase deployment workflows (optional)

### 10.7 Monitoring & Optimization

**Week 1-4 Post-Migration**:

1. **Monitor Firebase Usage**:
   - Go to Firebase Console → Usage and Billing
   - Check Firestore reads/writes
   - Check Storage bandwidth
   - Check Hosting bandwidth

2. **Optimize if Needed**:
   - Add caching headers
   - Optimize Firestore queries
   - Compress images in Storage
   - Review security rules

3. **User Feedback**:
   - Collect feedback from users
   - Address any issues promptly
   - Document any workarounds

**Phase 10 Completion Checklist**:
- [ ] Production running smoothly for 48+ hours
- [ ] Documentation updated (README, QUICKSTART)
- [ ] Migration summary created
- [ ] Old code archived (Git branch)
- [ ] Firebase usage monitored
- [ ] User feedback collected
- [ ] Supabase project paused (after 30 days)
- [ ] Vercel project removed (after 30 days)
- [ ] Team notified of changes

---

## 🎉 Migration Complete!

Congratulations! Your Department 56 Gallery app is now fully running on Firebase.

**Key Achievements**:
- ✅ All data migrated successfully
- ✅ All functionality preserved
- ✅ Single unified service provider
- ✅ Improved authentication experience
- ✅ Better free tier limits
- ✅ Custom domain working with HTTPS

**Next Steps**:
- Monitor production for 30 days
- Collect user feedback
- Optimize performance as needed
- Decommission old services after verification period

---

**For Issues**: Reference the [Main Migration Plan](./FIREBASE_MIGRATION_PLAN.md) or [Phases 2-5](./FIREBASE_MIGRATION_PHASE2-5.md).
