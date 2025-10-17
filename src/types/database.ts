export type House = {
  id: string;
  name: string;
  year?: number;
  notes?: string;
  photo_url?: string;
  purchased_on?: string;
  purchased_year?: number;
  created_at?: string;
  updated_at?: string;
  house_id?: string; // Added for accessories that might reference houses
};

export type Accessory = {
  id: string;
  name: string;
  notes?: string;
  photo_url?: string;
  purchased_on?: string;
  purchased_year?: number;
  house_id?: string; // Foreign key to houses
  created_at?: string;
  updated_at?: string;
};

export type Collection = {
  id: string;
  name: string;
  notes?: string;
  created_at?: string;
};

export type Tag = {
  id: string;
  name: string;
  created_at?: string;
};

export type HouseAccessoryLink = {
  id: string;
  house_id: string;
  accessory_id: string;
  created_at?: string;
};

export type HouseCollection = {
  id: string;
  house_id: string;
  collection_id: string;
  created_at?: string;
};

export type AccessoryCollection = {
  id: string;
  accessory_id: string;
  collection_id: string;
  created_at?: string;
};

export type HouseTag = {
  id: string;
  house_id: string;
  tag_id: string;
  source: 'manual' | 'ml';
  confidence?: number;
  reviewed?: boolean;
  created_at?: string;
};

export type AccessoryTag = {
  id: string;
  accessory_id: string;
  tag_id: string;
  source: 'manual' | 'ml';
  confidence?: number;
  reviewed?: boolean;
  created_at?: string;
};

export type Database = {
  houses: House[];
  accessories: Accessory[];
  collections: Collection[];
  tags: Tag[];
  houseAccessoryLinks: HouseAccessoryLink[];
  houseCollections: HouseCollection[];
  accessoryCollections: AccessoryCollection[];
  houseTags: HouseTag[];
  accessoryTags: AccessoryTag[];
};
