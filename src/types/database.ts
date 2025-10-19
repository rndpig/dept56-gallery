export type House = {
  id: string;
  name: string;
  year?: number; // Released year
  retired_year?: number; // Year retired from production
  description?: string; // New field for description
  sku?: string; // SKU/Item number
  notes?: string; // Keep for additional notes
  photo_url?: string;
  purchased_year?: number;
  price?: number; // Purchase or retail price
  collection?: string; // Collection name from document
  series?: string; // Series name from document
  created_at?: string;
  updated_at?: string;
  user_id?: string;
};

export type Accessory = {
  id: string;
  name: string;
  year?: number; // Released year (accessories can have release year too)
  retired_year?: number; // Year retired from production
  description?: string; // New field for description
  sku?: string; // SKU/Item number
  notes?: string; // Keep for additional notes
  photo_url?: string;
  purchased_year?: number;
  price?: number; // Purchase or retail price
  collection?: string; // Collection name from document
  series?: string; // Series name from document
  created_at?: string;
  updated_at?: string;
  user_id?: string;
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
