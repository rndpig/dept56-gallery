// Firebase Firestore database layer
import { db, storage } from './firebase';
import {
  collection,
  doc,
  getDoc,
  getDocs,
  addDoc,
  updateDoc,
  deleteDoc,
  writeBatch,
  serverTimestamp
} from 'firebase/firestore';
import { ref, uploadBytes, getDownloadURL, deleteObject } from 'firebase/storage';
import type {
  House,
  Accessory,
  Collection as CollectionType,
  Tag,
  HouseAccessoryLink,
  Database,
} from '../types/database';

// Helper to convert Firestore doc to database format
function firestoreToHouse(id: string, data: any): House {
  return {
    id,
    name: data.name,
    year: data.year || null,
    retired_year: data.retiredYear || null,
    description: data.description || null,
    sku: data.sku || null,
    notes: data.notes || null,
    photo_url: data.photoUrl || null,
    purchased_year: data.purchasedYear || null,
    price: data.price || null,
    collection: data.collection || null,
    series: data.series || null,
    created_at: data.createdAt?.toDate().toISOString() || null,
    updated_at: data.updatedAt?.toDate().toISOString() || null,
    user_id: data.userId || null,
  };
}

function firestoreToAccessory(id: string, data: any): Accessory {
  return {
    id,
    name: data.name,
    year: data.year || null,
    retired_year: data.retiredYear || null,
    description: data.description || null,
    sku: data.sku || null,
    notes: data.notes || null,
    photo_url: data.photoUrl || null,
    purchased_year: data.purchasedYear || null,
    price: data.price || null,
    collection: data.collection || null,
    series: data.series || null,
    created_at: data.createdAt?.toDate().toISOString() || null,
    updated_at: data.updatedAt?.toDate().toISOString() || null,
    user_id: data.userId || null,
  };
}

function firestoreToCollection(id: string, data: any): CollectionType {
  return {
    id,
    name: data.name,
    notes: data.notes || null,
    created_at: data.createdAt?.toDate().toISOString() || new Date().toISOString(),
  };
}

function firestoreToTag(id: string, data: any): Tag {
  return {
    id,
    name: data.name,
    created_at: data.createdAt?.toDate().toISOString() || new Date().toISOString(),
  };
}

function firestoreToLink(id: string, data: any): any {
  return {
    id,
    house_id: data.houseId,
    accessory_id: data.accessoryId,
    collection_id: data.collectionId,
    tag_id: data.tagId,
    source: data.source,
    confidence: data.confidenceScore,
    reviewed: data.reviewed,
    created_at: data.createdAt?.toDate().toISOString() || new Date().toISOString(),
  };
}

// ============================================
// FETCH ALL DATA
// ============================================

export async function fetchAllData(): Promise<Database> {
  const [
    housesSnap,
    accessoriesSnap,
    collectionsSnap,
    tagsSnap,
    linksSnap,
    houseCollectionsSnap,
    accessoryCollectionsSnap,
    houseTagsSnap,
    accessoryTagsSnap,
  ] = await Promise.all([
    getDocs(collection(db, 'houses')),
    getDocs(collection(db, 'accessories')),
    getDocs(collection(db, 'collections')),
    getDocs(collection(db, 'tags')),
    getDocs(collection(db, 'houseAccessoryLinks')),
    getDocs(collection(db, 'houseCollections')),
    getDocs(collection(db, 'accessoryCollections')),
    getDocs(collection(db, 'houseTags')),
    getDocs(collection(db, 'accessoryTags')),
  ]);

  return {
    houses: housesSnap.docs.map((d) => firestoreToHouse(d.id, d.data())),
    accessories: accessoriesSnap.docs.map((d) => firestoreToAccessory(d.id, d.data())),
    collections: collectionsSnap.docs.map((d) => firestoreToCollection(d.id, d.data())),
    tags: tagsSnap.docs.map((d) => firestoreToTag(d.id, d.data())),
    houseAccessoryLinks: linksSnap.docs.map((d) => firestoreToLink(d.id, d.data())),
    houseCollections: houseCollectionsSnap.docs.map((d) => firestoreToLink(d.id, d.data())),
    accessoryCollections: accessoryCollectionsSnap.docs.map((d) => firestoreToLink(d.id, d.data())),
    houseTags: houseTagsSnap.docs.map((d) => firestoreToLink(d.id, d.data())),
    accessoryTags: accessoryTagsSnap.docs.map((d) => firestoreToLink(d.id, d.data())),
  };
}

// ============================================
// HOUSES
// ============================================

export async function createHouse(
  house: Omit<House, 'id' | 'user_id' | 'created_at' | 'updated_at'>,
  collectionIds: string[],
  tagIds: string[]
): Promise<House> {
  const batch = writeBatch(db);
  
  // Transform snake_case to camelCase
  const houseData = {
    name: house.name,
    year: house.year || null,
    retiredYear: house.retired_year || null,
    description: house.description || null,
    sku: house.sku || null,
    notes: house.notes || null,
    photoUrl: house.photo_url || null,
    purchasedYear: house.purchased_year || null,
    price: house.price || null,
    collection: house.collection || null,
    series: house.series || null,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
  };
  
  // Add house
  const houseRef = doc(collection(db, 'houses'));
  batch.set(houseRef, houseData);
  
  // Link collections
  for (const collectionId of collectionIds) {
    const linkRef = doc(collection(db, 'houseCollections'));
    batch.set(linkRef, {
      houseId: houseRef.id,
      collectionId: collectionId,
      createdAt: serverTimestamp(),
    });
  }
  
  // Link tags
  for (const tagId of tagIds) {
    const linkRef = doc(collection(db, 'houseTags'));
    batch.set(linkRef, {
      houseId: houseRef.id,
      tagId: tagId,
      source: 'manual',
      reviewed: true,
      createdAt: serverTimestamp(),
    });
  }
  
  await batch.commit();
  
  // Fetch and return created house
  const createdDoc = await getDoc(houseRef);
  return firestoreToHouse(createdDoc.id, createdDoc.data());
}

export async function updateHouse(
  id: string,
  updates: Partial<Omit<House, 'id' | 'user_id' | 'created_at' | 'updated_at'>>
): Promise<House> {
  // Transform snake_case to camelCase
  const firestoreUpdates: any = {
    updatedAt: serverTimestamp(),
  };
  
  if (updates.name !== undefined) firestoreUpdates.name = updates.name;
  if (updates.year !== undefined) firestoreUpdates.year = updates.year;
  if (updates.retired_year !== undefined) firestoreUpdates.retiredYear = updates.retired_year;
  if (updates.description !== undefined) firestoreUpdates.description = updates.description;
  if (updates.sku !== undefined) firestoreUpdates.sku = updates.sku;
  if (updates.notes !== undefined) firestoreUpdates.notes = updates.notes;
  if (updates.photo_url !== undefined) firestoreUpdates.photoUrl = updates.photo_url;
  if (updates.purchased_year !== undefined) firestoreUpdates.purchasedYear = updates.purchased_year;
  if (updates.price !== undefined) firestoreUpdates.price = updates.price;
  if (updates.collection !== undefined) firestoreUpdates.collection = updates.collection;
  if (updates.series !== undefined) firestoreUpdates.series = updates.series;
  
  const houseRef = doc(db, 'houses', id);
  await updateDoc(houseRef, firestoreUpdates);
  
  const updatedDoc = await getDoc(houseRef);
  return firestoreToHouse(updatedDoc.id, updatedDoc.data());
}

export async function deleteHouse(id: string): Promise<void> {
  await deleteDoc(doc(db, 'houses', id));
}

// ============================================
// ACCESSORIES
// ============================================

export async function createAccessory(
  accessory: Omit<Accessory, 'id' | 'user_id' | 'created_at' | 'updated_at'>,
  collectionIds: string[],
  tagIds: string[]
): Promise<Accessory> {
  const batch = writeBatch(db);
  
  const accessoryData = {
    name: accessory.name,
    year: accessory.year || null,
    retiredYear: accessory.retired_year || null,
    description: accessory.description || null,
    sku: accessory.sku || null,
    notes: accessory.notes || null,
    photoUrl: accessory.photo_url || null,
    purchasedYear: accessory.purchased_year || null,
    price: accessory.price || null,
    collection: accessory.collection || null,
    series: accessory.series || null,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
  };
  
  const accessoryRef = doc(collection(db, 'accessories'));
  batch.set(accessoryRef, accessoryData);
  
  for (const collectionId of collectionIds) {
    const linkRef = doc(collection(db, 'accessoryCollections'));
    batch.set(linkRef, {
      accessoryId: accessoryRef.id,
      collectionId: collectionId,
      createdAt: serverTimestamp(),
    });
  }
  
  for (const tagId of tagIds) {
    const linkRef = doc(collection(db, 'accessoryTags'));
    batch.set(linkRef, {
      accessoryId: accessoryRef.id,
      tagId: tagId,
      source: 'manual',
      reviewed: true,
      createdAt: serverTimestamp(),
    });
  }
  
  await batch.commit();
  
  const createdDoc = await getDoc(accessoryRef);
  return firestoreToAccessory(createdDoc.id, createdDoc.data());
}

export async function updateAccessory(
  id: string,
  updates: Partial<Omit<Accessory, 'id' | 'user_id' | 'created_at' | 'updated_at'>>
): Promise<Accessory> {
  const firestoreUpdates: any = {
    updatedAt: serverTimestamp(),
  };
  
  if (updates.name !== undefined) firestoreUpdates.name = updates.name;
  if (updates.year !== undefined) firestoreUpdates.year = updates.year;
  if (updates.retired_year !== undefined) firestoreUpdates.retiredYear = updates.retired_year;
  if (updates.description !== undefined) firestoreUpdates.description = updates.description;
  if (updates.sku !== undefined) firestoreUpdates.sku = updates.sku;
  if (updates.notes !== undefined) firestoreUpdates.notes = updates.notes;
  if (updates.photo_url !== undefined) firestoreUpdates.photoUrl = updates.photo_url;
  if (updates.purchased_year !== undefined) firestoreUpdates.purchasedYear = updates.purchased_year;
  if (updates.price !== undefined) firestoreUpdates.price = updates.price;
  if (updates.collection !== undefined) firestoreUpdates.collection = updates.collection;
  if (updates.series !== undefined) firestoreUpdates.series = updates.series;
  
  const accessoryRef = doc(db, 'accessories', id);
  await updateDoc(accessoryRef, firestoreUpdates);
  
  const updatedDoc = await getDoc(accessoryRef);
  return firestoreToAccessory(updatedDoc.id, updatedDoc.data());
}

export async function deleteAccessory(id: string): Promise<void> {
  await deleteDoc(doc(db, 'accessories', id));
}

// ============================================
// COLLECTIONS
// ============================================

export async function createCollection(name: string, notes?: string): Promise<CollectionType> {
  const collectionData = {
    name,
    notes: notes || null,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
  };
  
  const docRef = await addDoc(collection(db, 'collections'), collectionData);
  const createdDoc = await getDoc(docRef);
  return firestoreToCollection(createdDoc.id, createdDoc.data());
}

export async function deleteCollection(id: string): Promise<void> {
  await deleteDoc(doc(db, 'collections', id));
}

// ============================================
// TAGS
// ============================================

export async function createTag(name: string): Promise<Tag> {
  const tagData = {
    name,
    createdAt: serverTimestamp(),
  };
  
  const docRef = await addDoc(collection(db, 'tags'), tagData);
  const createdDoc = await getDoc(docRef);
  return firestoreToTag(createdDoc.id, createdDoc.data());
}

export async function deleteTag(id: string): Promise<void> {
  await deleteDoc(doc(db, 'tags', id));
}

// ============================================
// LINKS
// ============================================

export async function linkHouseToAccessory(
  houseId: string,
  accessoryId: string
): Promise<HouseAccessoryLink> {
  const linkData = {
    houseId,
    accessoryId,
    createdAt: serverTimestamp(),
  };
  
  const docRef = await addDoc(collection(db, 'houseAccessoryLinks'), linkData);
  const createdDoc = await getDoc(docRef);
  return firestoreToLink(createdDoc.id, createdDoc.data());
}

export async function unlinkHouseFromAccessory(linkId: string): Promise<void> {
  await deleteDoc(doc(db, 'houseAccessoryLinks', linkId));
}

// ============================================
// IMAGE UPLOAD (Firebase Storage)
// ============================================

import { storage } from './firebase';
import { ref, uploadBytes, getDownloadURL, deleteObject } from 'firebase/storage';

export async function uploadImage(file: File): Promise<string> {
  const fileExt = file.name.split('.').pop();
  const fileName = `uploads/${Date.now()}-${Math.random().toString(36).slice(2)}.${fileExt}`;

  const storageRef = ref(storage, fileName);
  await uploadBytes(storageRef, file, {
    cacheControl: 'public, max-age=3600',
  });

  const downloadURL = await getDownloadURL(storageRef);
  return downloadURL;
}

export async function deleteImage(url: string): Promise<void> {
  try {
    // Extract path from Firebase Storage URL
    const urlObj = new URL(url);
    const pathMatch = urlObj.pathname.match(/\/o\/(.+)\?/);
    if (pathMatch) {
      const path = decodeURIComponent(pathMatch[1]);
      const storageRef = ref(storage, path);
      await deleteObject(storageRef);
    }
  } catch (error) {
    console.error('Error deleting image:', error);
    // Don't throw - image might be from Supabase during migration
  }
}

// ============================================
// CONVERT BASE64 TO FILE
// ============================================

export function base64ToFile(base64: string, filename: string): File {
  const arr = base64.split(',');
  const mime = arr[0].match(/:(.*?);/)?.[1] || 'image/jpeg';
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);

  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }

  return new File([u8arr], filename, { type: mime });
}
