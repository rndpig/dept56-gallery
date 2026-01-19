// Firestore database types
// These map from the PostgreSQL schema to Firestore collections
// Field names converted from snake_case to camelCase

import { Timestamp } from 'firebase/firestore';

// ============================================
// FIRESTORE DOCUMENT TYPES (with Timestamp)
// ============================================

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

// ============================================
// CLIENT-SAFE TYPES (with Date for UI)
// ============================================

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

// ============================================
// HELPER TYPES
// ============================================

// Type for documents with ID
export type WithId<T> = T & { id: string };

// Database structure (for app state)
export interface Database {
  houses: House[];
  accessories: Accessory[];
  collections: Collection[];
  tags: Tag[];
  houseAccessoryLinks: HouseAccessoryLink[];
  houseCollections: HouseCollection[];
  accessoryCollections: AccessoryCollection[];
  houseTags: HouseTag[];
  accessoryTags: AccessoryTag[];
}

// ============================================
// CONVERTER HELPERS
// ============================================

/**
 * Convert Firestore Timestamp to JavaScript Date
 */
export function timestampToDate(timestamp: Timestamp): Date {
  return timestamp.toDate();
}

/**
 * Field name conversion map (snake_case → camelCase)
 */
export const FIELD_NAME_MAP = {
  user_id: 'userId',
  photo_url: 'photoUrl',
  retired_year: 'retiredYear',
  purchased_year: 'purchasedYear',
  created_at: 'createdAt',
  updated_at: 'updatedAt',
  house_id: 'houseId',
  accessory_id: 'accessoryId',
  collection_id: 'collectionId',
  tag_id: 'tagId',
} as const;

/**
 * Collection name map (PostgreSQL table → Firestore collection)
 */
export const COLLECTION_NAME_MAP = {
  houses: 'houses',
  accessories: 'accessories',
  collections: 'collections',
  tags: 'tags',
  house_accessory_links: 'houseAccessoryLinks',
  house_collections: 'houseCollections',
  accessory_collections: 'accessoryCollections',
  house_tags: 'houseTags',
  accessory_tags: 'accessoryTags',
} as const;
