import { supabase } from './supabase'
import type {
  House,
  Accessory,
  Collection,
  Tag,
  HouseAccessoryLink,
  HouseCollection,
  AccessoryCollection,
  HouseTag,
  AccessoryTag,
  Database,
} from '../types/database'

// ============================================
// FETCH ALL DATA
// ============================================

export async function fetchAllData(): Promise<Database> {
  const [
    housesRes,
    accessoriesRes,
    collectionsRes,
    tagsRes,
    linksRes,
    houseCollectionsRes,
    accessoryCollectionsRes,
    houseTagsRes,
    accessoryTagsRes,
  ] = await Promise.all([
    supabase.from('houses').select('*'),
    supabase.from('accessories').select('*'),
    supabase.from('collections').select('*'),
    supabase.from('tags').select('*'),
    supabase.from('house_accessory_links').select('*'),
    supabase.from('house_collections').select('*'),
    supabase.from('accessory_collections').select('*'),
    supabase.from('house_tags').select('*'),
    supabase.from('accessory_tags').select('*'),
  ])

  if (housesRes.error) throw housesRes.error
  if (accessoriesRes.error) throw accessoriesRes.error
  if (collectionsRes.error) throw collectionsRes.error
  if (tagsRes.error) throw tagsRes.error
  if (linksRes.error) throw linksRes.error
  if (houseCollectionsRes.error) throw houseCollectionsRes.error
  if (accessoryCollectionsRes.error) throw accessoryCollectionsRes.error
  if (houseTagsRes.error) throw houseTagsRes.error
  if (accessoryTagsRes.error) throw accessoryTagsRes.error

  return {
    houses: housesRes.data || [],
    accessories: accessoriesRes.data || [],
    collections: collectionsRes.data || [],
    tags: tagsRes.data || [],
    houseAccessoryLinks: linksRes.data || [],
    houseCollections: houseCollectionsRes.data || [],
    accessoryCollections: accessoryCollectionsRes.data || [],
    houseTags: houseTagsRes.data || [],
    accessoryTags: accessoryTagsRes.data || [],
  }
}

// ============================================
// HOUSES
// ============================================

export async function createHouse(
  house: Omit<House, 'id' | 'user_id' | 'created_at' | 'updated_at'>,
  collectionIds: string[],
  tagIds: string[]
): Promise<House> {
  // No authentication required - single user app
  
  // Insert house (without user_id)
  const { data, error } = await supabase
    .from('houses')
    .insert(house)
    .select()
    .single()

  if (error) throw error

  // Link collections
  if (collectionIds.length > 0) {
    const { error: collError } = await supabase.from('house_collections').insert(
      collectionIds.map((collection_id) => ({
        house_id: data.id,
        collection_id,
      }))
    )
    if (collError) throw collError
  }

  // Link tags
  if (tagIds.length > 0) {
    const { error: tagError } = await supabase.from('house_tags').insert(
      tagIds.map((tag_id) => ({
        house_id: data.id,
        tag_id,
        source: 'manual' as const,
        reviewed: true,
      }))
    )
    if (tagError) throw tagError
  }

  return data
}

export async function updateHouse(
  id: string,
  updates: Partial<Omit<House, 'id' | 'user_id' | 'created_at' | 'updated_at'>>
): Promise<House> {
  const { data, error } = await supabase
    .from('houses')
    .update(updates)
    .eq('id', id)
    .select()
    .single()

  if (error) throw error
  return data
}

export async function deleteHouse(id: string): Promise<void> {
  const { error } = await supabase.from('houses').delete().eq('id', id)
  if (error) throw error
}

// ============================================
// ACCESSORIES
// ============================================

export async function createAccessory(
  accessory: Omit<Accessory, 'id' | 'user_id' | 'created_at' | 'updated_at'>,
  collectionIds: string[],
  tagIds: string[]
): Promise<Accessory> {
  // No authentication required - single user app

  // Insert accessory (without user_id)
  const { data, error } = await supabase
    .from('accessories')
    .insert(accessory)
    .select()
    .single()

  if (error) throw error

  // Link collections
  if (collectionIds.length > 0) {
    const { error: collError } = await supabase.from('accessory_collections').insert(
      collectionIds.map((collection_id) => ({
        accessory_id: data.id,
        collection_id,
      }))
    )
    if (collError) throw collError
  }

  // Link tags
  if (tagIds.length > 0) {
    const { error: tagError } = await supabase.from('accessory_tags').insert(
      tagIds.map((tag_id) => ({
        accessory_id: data.id,
        tag_id,
        source: 'manual' as const,
        reviewed: true,
      }))
    )
    if (tagError) throw tagError
  }

  return data
}

export async function updateAccessory(
  id: string,
  updates: Partial<Omit<Accessory, 'id' | 'user_id' | 'created_at' | 'updated_at'>>
): Promise<Accessory> {
  const { data, error } = await supabase
    .from('accessories')
    .update(updates)
    .eq('id', id)
    .select()
    .single()

  if (error) throw error
  return data
}

export async function deleteAccessory(id: string): Promise<void> {
  const { error } = await supabase.from('accessories').delete().eq('id', id)
  if (error) throw error
}

// ============================================
// COLLECTIONS
// ============================================

export async function createCollection(name: string, notes?: string): Promise<Collection> {
  // No authentication required - single user app

  const { data, error } = await supabase
    .from('collections')
    .insert({ name, notes })
    .select()
    .single()

  if (error) throw error
  return data
}

export async function deleteCollection(id: string): Promise<void> {
  const { error } = await supabase.from('collections').delete().eq('id', id)
  if (error) throw error
}

// ============================================
// TAGS
// ============================================

export async function createTag(name: string): Promise<Tag> {
  // No authentication required - single user app

  const { data, error } = await supabase
    .from('tags')
    .insert({ name })
    .select()
    .single()

  if (error) throw error
  return data
}

export async function deleteTag(id: string): Promise<void> {
  const { error } = await supabase.from('tags').delete().eq('id', id)
  if (error) throw error
}

// ============================================
// LINKS
// ============================================

export async function linkHouseToAccessory(
  houseId: string,
  accessoryId: string
): Promise<HouseAccessoryLink> {
  const { data, error } = await supabase
    .from('house_accessory_links')
    .insert({ house_id: houseId, accessory_id: accessoryId })
    .select()
    .single()

  if (error) throw error
  return data
}

export async function unlinkHouseFromAccessory(linkId: string): Promise<void> {
  const { error } = await supabase.from('house_accessory_links').delete().eq('id', linkId)
  if (error) throw error
}

// ============================================
// IMAGE UPLOAD
// ============================================

export async function uploadImage(file: File): Promise<string> {
  // No authentication required - use simple naming scheme

  // Create unique filename
  const fileExt = file.name.split('.').pop()
  const fileName = `uploads/${Date.now()}-${Math.random().toString(36).slice(2)}.${fileExt}`

  // Upload to Supabase Storage
  const { data, error } = await supabase.storage
    .from('dept56-images')
    .upload(fileName, file, {
      cacheControl: '3600',
      upsert: false,
    })

  if (error) throw error

  // Get public URL
  const {
    data: { publicUrl },
  } = supabase.storage.from('dept56-images').getPublicUrl(data.path)

  return publicUrl
}

export async function deleteImage(url: string): Promise<void> {
  // Extract path from URL
  const path = url.split('/').slice(-2).join('/')

  const { error } = await supabase.storage.from('dept56-images').remove([path])

  if (error) throw error
}

// ============================================
// CONVERT BASE64 TO FILE
// ============================================

export function base64ToFile(base64: string, filename: string): File {
  const arr = base64.split(',')
  const mime = arr[0].match(/:(.*?);/)?.[1] || 'image/jpeg'
  const bstr = atob(arr[1])
  let n = bstr.length
  const u8arr = new Uint8Array(n)

  while (n--) {
    u8arr[n] = bstr.charCodeAt(n)
  }

  return new File([u8arr], filename, { type: mime })
}
