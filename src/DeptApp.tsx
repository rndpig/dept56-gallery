import React, { useEffect, useMemo, useRef, useState } from "react";
import { supabase } from "./lib/supabase";
import * as db from "./lib/database";
import type { Database, House, Accessory, Collection, Tag, HouseAccessoryLink } from "./types/database";
import type { User } from "@supabase/supabase-js";
import { DataReviewTab } from "./DataReviewTab";
import Fuse from 'fuse.js';

// Type for search index items
type SearchIndexHouse = {
  name: string;
  year: number | null;
  description: string;
  sku: string;
  collection: string;
  images: string[];
  photo_url: string;
  url: string;
  search_terms: string;
  srp?: number;
  intro_year?: number;
  retired_year?: number;
};

/**
 * Department 56 Browser — React app (Supabase Edition)
 * --------------------------------------------------------------
 * FEATURES:
 * - Cloud database with Supabase
 * - Image storage in Supabase Storage
 * - Purchased date / purchased year metadata
 * - Collections (many-to-many links)
 * - Tags (manual + ML placeholder) with confidence + reviewed flag
 * - Fuzzy search across names, collections, and tags
 * - Real-time data sync
 * - Row Level Security for data protection
 * - Google OAuth authentication with email whitelist
 */

// Whitelist of allowed admin emails
const ALLOWED_ADMIN_EMAILS = [
  "rndpig@gmail.com",
  "annadilger@gmail.com",
  "bday1951@gmail.com",
  "drdcreek@gmail.com",
  "ericlday@gmail.com",
  "amyannday@gmail.com",
];

// ------------------------ Utils ------------------------
async function fileToDataURL(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function download(filename: string, text: string) {
  const a = document.createElement("a");
  a.href = "data:text/plain;charset=utf-8," + encodeURIComponent(text);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

// simple trigram-ish similarity for fuzzy search
function trigram(s: string) {
  const n = new Set<string>();
  const t = `  ${s.toLowerCase()} `;
  for (let i = 0; i < t.length - 2; i++) n.add(t.slice(i, i + 3));
  return n;
}
function similarity(a: string, b: string) {
  if (!a || !b) return 0;
  const A = trigram(a);
  const B = trigram(b);
  let inter = 0;
  A.forEach((x) => {
    if (B.has(x)) inter++;
  });
  return inter / Math.max(A.size, B.size);
}
function fuzzyIncludes(hay: string, needle: string) {
  hay = hay.toLowerCase();
  needle = needle.toLowerCase().trim();
  return hay.includes(needle) || similarity(hay, needle) > 0.28;
}

// ------------------------ UI bits ------------------------
function Button({
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { className?: string }) {
  const baseClasses = "px-3 py-2 rounded-2xl text-sm font-medium shadow-sm border active:scale-[.99] transition disabled:opacity-50 disabled:cursor-not-allowed";
  const defaultClasses = "border-gray-200 bg-red-600 text-white hover:bg-red-700";
  
  return (
    <button
      {...props}
      className={
        className 
          ? `${baseClasses} ${className}`
          : `${baseClasses} ${defaultClasses}`
      }
    />
  );
}
const Pill = ({ children }: { children: React.ReactNode }) => (
  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-700">
    {children}
  </span>
);
const Field = ({ label, children }: { label: string; children: React.ReactNode }) => (
  <label className="block space-y-1">
    <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">{label}</span>
    {children}
  </label>
);
function TextInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={
        "w-full rounded-xl border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" +
        (props.className ? " " + props.className : "")
      }
    />
  );
}
function TextArea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={
        "w-full rounded-xl border border-gray-300 px-3 py-2 text-sm min-h-[90px] focus:outline-none focus:ring-2 focus:ring-indigo-500" +
        (props.className ? " " + props.className : "")
      }
    />
  );
}
function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={
        "w-full rounded-xl border border-gray-300 px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500" +
        (props.className ? " " + props.className : "")
      }
    />
  );
}
const Card = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <div className={"rounded-3xl border border-gray-200 bg-white shadow-sm " + className}>
    {children}
  </div>
);
const SectionTitle = ({
  children,
  aside,
}: {
  children: React.ReactNode;
  aside?: React.ReactNode;
}) => (
  <div className="flex items-end justify-between gap-4">
    <h2 className="text-lg font-semibold text-gray-800">{children}</h2>
    {aside}
  </div>
);

// ------------------------ Modal ------------------------
function useModal<T = any>() {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<T | null>(null);
  return {
    open,
    data,
    show: (d: T) => {
      setData(d);
      setOpen(true);
    },
    hide: () => setOpen(false),
  } as const;
}

// Simple image modal for accessories
function ImageModal({
  open,
  onClose,
  title,
  src,
}: {
  open: boolean;
  onClose: () => void;
  title?: string;
  src?: string;
}) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 overflow-y-auto"
      onClick={onClose}
    >
      <div className="max-w-4xl w-full my-8" onClick={(e) => e.stopPropagation()}>
        <Card className="overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b">
            <div className="font-medium truncate pr-4">{title || "Photo"}</div>
            <Button onClick={onClose}>Close</Button>
          </div>
          {src ? (
            <div className="max-h-[calc(100vh-200px)] overflow-auto">
              <img src={src} alt={title} className="w-full h-auto" />
            </div>
          ) : (
            <div className="p-6 text-sm text-gray-500">No image</div>
          )}
        </Card>
      </div>
    </div>
  );
}

// Detailed house modal with metadata and accessories
function HouseDetailModal({
  open,
  onClose,
  house,
  data,
  collById,
  tagById,
  onAccessoryClick,
  onUnlink,
  onEdit,
  isAdmin,
}: {
  open: boolean;
  onClose: () => void;
  house: House | null;
  data: Database | null;
  collById: Record<string, Collection>;
  tagById: Record<string, Tag>;
  onAccessoryClick: (accessory: Accessory) => void;
  onUnlink: (linkId: string) => void;
  onEdit: (houseId: string) => void;
  isAdmin: boolean;
}) {
  const [selectedImage, setSelectedImage] = React.useState<{ url: string; name: string } | null>(null);

  // Initialize selected image to house photo when modal opens or house changes
  React.useEffect(() => {
    if (open && house?.photo_url) {
      setSelectedImage({ url: house.photo_url, name: house.name });
    } else if (open && house && !house.photo_url) {
      setSelectedImage(null);
    }
  }, [open, house?.id, house?.photo_url, house?.name]);

  if (!open || !house || !data) return null;

  // Get all unique accessories (including those without photos)
  const accessoryMap = new Map<string, { linkId: string; a: Accessory }>();
  data.houseAccessoryLinks
    .filter((l) => l.house_id === house.id)
    .forEach((l) => {
      const accessory = data.accessories.find((x) => x.id === l.accessory_id);
      if (accessory) {
        if (!accessoryMap.has(accessory.id)) {
          accessoryMap.set(accessory.id, { linkId: l.id, a: accessory });
        }
      }
    });
  const accessories = Array.from(accessoryMap.values());

  const colls = data.houseCollections
    .filter((x) => x.house_id === house.id)
    .map((x) => collById[x.collection_id])
    .filter(Boolean) as Collection[];
  
  const tags = data.houseTags
    .filter((x) => x.house_id === house.id)
    .map((x) => tagById[x.tag_id])
    .filter(Boolean) as Tag[];

  // Parse SKUs from notes
  const skus = house.notes ? (() => {
    const match = house.notes.match(/SKUs?:\s*([0-9.,\s]+)/i);
    if (match) {
      return match[1].split(',').map(s => s.trim()).filter(s => s);
    }
    return [];
  })() : [];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <div className="max-w-4xl w-full h-[85vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <Card className="overflow-hidden h-full flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b bg-gray-50 flex-shrink-0">
            <h2 className="text-xl font-semibold">{house.name}</h2>
            <div className="flex gap-2">
              {isAdmin && (
                <Button 
                  onClick={() => onEdit(house.id)}
                  className="bg-green-700 text-white border-green-700 hover:bg-green-800"
                >
                  Edit
                </Button>
              )}
              <Button onClick={onClose}>Close</Button>
            </div>
          </div>

          {/* Content: Image on left (75%), thumbnails/details on right (25%) */}
          <div className="flex flex-col lg:flex-row flex-1 min-h-0">
            {/* Left: Large Image Display */}
            <div className="lg:w-3/4 bg-gray-100 flex flex-col min-h-0">
              {/* Selected item name header */}
              {selectedImage && (
                <div className="bg-gray-200 px-4 py-2 border-b border-gray-300 flex-shrink-0">
                  <h3 className="text-sm font-semibold text-gray-800">{selectedImage.name}</h3>
                </div>
              )}
              {/* Image */}
              <div className="flex-1 flex items-center justify-center p-4 overflow-auto">
                {selectedImage?.url ? (
                  <img 
                    src={selectedImage.url} 
                    alt={selectedImage.name} 
                    className="max-w-full max-h-full object-contain"
                  />
                ) : (
                  <div className="p-12 text-gray-400 text-center">No photo available</div>
                )}
              </div>
            </div>

            {/* Right: Thumbnails and Metadata */}
            <div className="lg:w-1/4 overflow-y-auto p-4 space-y-4 bg-gray-50">
              {/* Thumbnails Section */}
              <div>
                {/* House Section */}
                <div className="mb-3">
                  <h3 className="text-xs font-semibold text-gray-700 mb-2 uppercase">House</h3>
                  {house.photo_url && (
                    <div>
                      <button
                        onClick={() => setSelectedImage({ url: house.photo_url!, name: house.name })}
                        className={`w-full border-2 rounded overflow-hidden hover:border-blue-500 transition-colors ${
                          selectedImage?.url === house.photo_url ? 'border-blue-500' : 'border-gray-300'
                        }`}
                      >
                        <img
                          src={house.photo_url}
                          alt={house.name}
                          className="w-full h-20 object-contain bg-white"
                        />
                      </button>
                      <div className="text-xs text-gray-700 mt-1 text-center font-medium px-1">
                        {house.name}
                      </div>
                    </div>
                  )}
                </div>

                {/* Accessories Section */}
                {accessories.length > 0 && (
                  <div>
                    <h3 className="text-xs font-semibold text-gray-700 mb-2 uppercase">Accessories ({accessories.length})</h3>
                    <div className="space-y-2">
                      {accessories.map(({ linkId, a }) => (
                        <div key={linkId}>
                          <button
                            onClick={() => onAccessoryClick(a)}
                            className="w-full border-2 rounded overflow-hidden hover:border-blue-500 transition-colors border-gray-300"
                          >
                            {a.photo_url ? (
                              <img
                                src={a.photo_url}
                                alt={a.name}
                                className="w-full h-20 object-contain bg-white"
                              />
                            ) : (
                              <div className="w-full h-20 bg-gray-100 flex items-center justify-center">
                                <div className="text-center px-2">
                                  <div className="text-xs font-medium text-gray-700">{a.name}</div>
                                  <div className="text-xs text-gray-500 mt-1">No photo</div>
                                </div>
                              </div>
                            )}
                          </button>
                          <div className="text-xs text-gray-700 mt-1 text-center font-medium px-1">
                            {a.name}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Metadata */}
              <div>
                <h3 className="text-xs font-semibold text-gray-700 mb-2">Details</h3>
                <div className="space-y-1 text-xs">
                  {house.sku && (
                    <div>
                      <span className="font-medium text-gray-600">SKU:</span>
                      <span className="ml-1">{house.sku}</span>
                    </div>
                  )}
                  {house.price && (
                    <div>
                      <span className="font-medium text-gray-600">Price:</span>
                      <span className="ml-1 text-green-700 font-semibold">${house.price.toFixed(2)}</span>
                    </div>
                  )}
                  {house.year && (
                    <div>
                      <span className="font-medium text-gray-600">Released:</span>
                      <span className="ml-1">{house.year}</span>
                    </div>
                  )}
                  {house.retired_year && (
                    <div>
                      <span className="font-medium text-gray-600">Retired:</span>
                      <span className="ml-1">{house.retired_year}</span>
                    </div>
                  )}
                  {house.purchased_year && (
                    <div>
                      <span className="font-medium text-gray-600">Purchased:</span>
                      <span className="ml-1">{house.purchased_year}</span>
                    </div>
                  )}
                  {house.collection && (
                    <div>
                      <span className="font-medium text-gray-600">Collection:</span>
                      <span className="ml-1">{house.collection}</span>
                    </div>
                  )}
                  {house.series && (
                    <div>
                      <span className="font-medium text-gray-600">Series:</span>
                      <span className="ml-1">{house.series}</span>
                    </div>
                  )}
                  {skus.length > 0 && (
                    <div>
                      <span className="font-medium text-gray-600">SKU(s) (notes):</span>
                      <span className="ml-1">{skus.join(', ')}</span>
                    </div>
                  )}
                  {house.description && (
                    <div className="pt-2">
                      <span className="font-medium text-gray-600">Description:</span>
                      <p className="mt-1 text-gray-700">{house.description}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Collections */}
              {colls.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-700 mb-2">Collections</h3>
                  <div className="flex flex-wrap gap-1">
                    {colls.map((c) => (
                      <Pill key={c.id}>{c.name}</Pill>
                    ))}
                  </div>
                </div>
              )}

              {/* Tags */}
              {tags.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-700 mb-2">Tags</h3>
                  <div className="flex flex-wrap gap-1">
                    {tags.map((t) => (
                      <span key={t.id} className="bg-gray-100 rounded-full px-2 py-0.5 text-xs text-gray-700">
                        #{t.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

function AccessoryDetailModal({
  open,
  onClose,
  accessory,
  data,
  collById,
  tagById,
  onEdit,
  onHouseClick,
  isAdmin,
}: {
  open: boolean;
  onClose: () => void;
  accessory: Accessory | null;
  data: Database | null;
  collById: Record<string, Collection>;
  tagById: Record<string, Tag>;
  onEdit: (accessoryId: string) => void;
  onHouseClick: (house: House) => void;
  isAdmin: boolean;
}) {
  const [selectedImage, setSelectedImage] = React.useState<{ url: string; name: string } | null>(null);

  // Initialize selected image to accessory photo when modal opens or accessory changes
  React.useEffect(() => {
    if (open && accessory?.photo_url) {
      setSelectedImage({ url: accessory.photo_url, name: accessory.name });
    } else if (open && accessory && !accessory.photo_url) {
      setSelectedImage(null);
    }
  }, [open, accessory?.id, accessory?.photo_url, accessory?.name]);

  if (!open || !accessory || !data) return null;

  // Get all linked houses (including those without photos)
  const houseMap = new Map<string, { linkId: string; h: House }>();
  data.houseAccessoryLinks
    .filter((l) => l.accessory_id === accessory.id)
    .forEach((l) => {
      const house = data.houses.find((x) => x.id === l.house_id);
      if (house) {
        if (!houseMap.has(house.id)) {
          houseMap.set(house.id, { linkId: l.id, h: house });
        }
      }
    });
  const houses = Array.from(houseMap.values());

  const colls = data.accessoryCollections
    .filter((x) => x.accessory_id === accessory.id)
    .map((x) => collById[x.collection_id])
    .filter(Boolean) as Collection[];
  
  const tags = data.accessoryTags
    .filter((x) => x.accessory_id === accessory.id)
    .map((x) => tagById[x.tag_id])
    .filter(Boolean) as Tag[];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <div className="max-w-4xl w-full h-[85vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <Card className="overflow-hidden h-full flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b bg-gray-50 flex-shrink-0">
            <h2 className="text-xl font-semibold">{accessory.name}</h2>
            <div className="flex gap-2">
              {isAdmin && (
                <Button 
                  onClick={() => onEdit(accessory.id)}
                  className="bg-green-700 text-white border-green-700 hover:bg-green-800"
                >
                  Edit
                </Button>
              )}
              <Button onClick={onClose}>Close</Button>
            </div>
          </div>

          {/* Content: Image on left (75%), thumbnails/details on right (25%) */}
          <div className="flex flex-col lg:flex-row flex-1 min-h-0">
            {/* Left: Large Image Display */}
            <div className="lg:w-3/4 bg-gray-100 flex flex-col min-h-0">
              {/* Selected item name header */}
              {selectedImage && (
                <div className="bg-gray-200 px-4 py-2 border-b border-gray-300 flex-shrink-0">
                  <h3 className="text-sm font-semibold text-gray-800">{selectedImage.name}</h3>
                </div>
              )}
              {/* Image */}
              <div className="flex-1 flex items-center justify-center p-4 overflow-auto">
                {selectedImage?.url ? (
                  <img 
                    src={selectedImage.url} 
                    alt={selectedImage.name} 
                    className="max-w-full max-h-full object-contain"
                  />
                ) : (
                  <div className="p-12 text-gray-400 text-center">No photo available</div>
                )}
              </div>
            </div>

            {/* Right: Thumbnails and Metadata */}
            <div className="lg:w-1/4 overflow-y-auto p-4 space-y-4 bg-gray-50">
              {/* Thumbnails Section */}
              <div>
                {/* Accessory Section */}
                <div className="mb-3">
                  <h3 className="text-xs font-semibold text-gray-700 mb-2 uppercase">Accessory</h3>
                  {accessory.photo_url && (
                    <div>
                      <button
                        onClick={() => setSelectedImage({ url: accessory.photo_url!, name: accessory.name })}
                        className={`w-full border-2 rounded overflow-hidden hover:border-blue-500 transition-colors ${
                          selectedImage?.url === accessory.photo_url ? 'border-blue-500' : 'border-gray-300'
                        }`}
                      >
                        <img
                          src={accessory.photo_url}
                          alt={accessory.name}
                          className="w-full h-20 object-contain bg-white"
                        />
                      </button>
                      <div className="text-xs text-gray-700 mt-1 text-center font-medium px-1">
                        {accessory.name}
                      </div>
                    </div>
                  )}
                </div>

                {/* Linked Houses Section */}
                {houses.length > 0 && (
                  <div>
                    <h3 className="text-xs font-semibold text-gray-700 mb-2 uppercase">Linked Houses ({houses.length})</h3>
                    <div className="space-y-2">
                      {houses.map(({ linkId, h }) => (
                        <div key={linkId}>
                          <button
                            onClick={() => onHouseClick(h)}
                            className="w-full border-2 rounded overflow-hidden hover:border-blue-500 transition-colors border-gray-300"
                          >
                            {h.photo_url ? (
                              <img
                                src={h.photo_url}
                                alt={h.name}
                                className="w-full h-20 object-contain bg-white"
                              />
                            ) : (
                              <div className="w-full h-20 bg-gray-100 flex items-center justify-center">
                                <div className="text-center px-2">
                                  <div className="text-xs font-medium text-gray-700">{h.name}</div>
                                  <div className="text-xs text-gray-500 mt-1">No photo</div>
                                </div>
                              </div>
                            )}
                          </button>
                          <div className="text-xs text-gray-700 mt-1 text-center font-medium px-1">
                            {h.name}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Metadata */}
              <div>
                <h3 className="text-xs font-semibold text-gray-700 mb-2">Details</h3>
                <div className="space-y-1 text-xs">
                  {accessory.sku && (
                    <div>
                      <span className="font-medium text-gray-600">SKU:</span>
                      <span className="ml-1">{accessory.sku}</span>
                    </div>
                  )}
                  {accessory.price && (
                    <div>
                      <span className="font-medium text-gray-600">Price:</span>
                      <span className="ml-1 text-green-700 font-semibold">${accessory.price.toFixed(2)}</span>
                    </div>
                  )}
                  {accessory.year && (
                    <div>
                      <span className="font-medium text-gray-600">Released:</span>
                      <span className="ml-1">{accessory.year}</span>
                    </div>
                  )}
                  {accessory.retired_year && (
                    <div>
                      <span className="font-medium text-gray-600">Retired:</span>
                      <span className="ml-1">{accessory.retired_year}</span>
                    </div>
                  )}
                  {accessory.purchased_year && (
                    <div>
                      <span className="font-medium text-gray-600">Purchased:</span>
                      <span className="ml-1">{accessory.purchased_year}</span>
                    </div>
                  )}
                  {accessory.collection && (
                    <div>
                      <span className="font-medium text-gray-600">Collection:</span>
                      <span className="ml-1">{accessory.collection}</span>
                    </div>
                  )}
                  {accessory.series && (
                    <div>
                      <span className="font-medium text-gray-600">Series:</span>
                      <span className="ml-1">{accessory.series}</span>
                    </div>
                  )}
                  {accessory.description && (
                    <div className="pt-2">
                      <span className="font-medium text-gray-600">Description:</span>
                      <p className="mt-1 text-gray-700">{accessory.description}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Collections */}
              {colls.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-700 mb-2">Collections</h3>
                  <div className="flex flex-wrap gap-1">
                    {colls.map((c) => (
                      <Pill key={c.id}>{c.name}</Pill>
                    ))}
                  </div>
                </div>
              )}

              {/* Tags */}
              {tags.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-700 mb-2">Tags</h3>
                  <div className="flex flex-wrap gap-1">
                    {tags.map((t) => (
                      <span key={t.id} className="bg-gray-100 rounded-full px-2 py-0.5 text-xs text-gray-700">
                        #{t.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

// ------------------------ Forms ------------------------
function MultiSelectChips<T extends { id: string; name: string }>({
  options,
  selectedIds,
  onChange,
  label,
}: {
  options: T[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  label: string;
}) {
  const [text, setText] = useState("");
  const filtered = useMemo(
    () => options.filter((o) => o.name.toLowerCase().includes(text.toLowerCase())),
    [options, text]
  );
  return (
    <div className="space-y-2">
      <Field label={label + " (type to filter)"}>
        <TextInput
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Start typing…"
        />
      </Field>
      <div className="flex flex-wrap gap-2">
        {filtered.map((o) => {
          const active = selectedIds.includes(o.id);
          return (
            <button
              key={o.id}
              onClick={(e) => {
                e.preventDefault();
                onChange(
                  active ? selectedIds.filter((id) => id !== o.id) : [...selectedIds, o.id]
                );
              }}
              className={`px-2 py-1 rounded-full text-xs border ${
                active ? "bg-indigo-600 text-white border-indigo-600" : "bg-white"
              }`}
            >
              {o.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function HouseForm({
  data,
  onSave,
  onDelete,
  onMoveToAccessory,
  onLink,
  initial,
}: {
  data: Database;
  onSave: (
    h: Omit<House, "id" | "user_id" | "created_at" | "updated_at">,
    collections: string[],
    tags: string[],
    existingId?: string
  ) => Promise<void>;
  onDelete?: (id: string, name: string) => Promise<void>;
  onMoveToAccessory?: (id: string, name: string) => Promise<void>;
  onLink?: (houseId: string, accessoryId: string) => Promise<void>;
  initial?: Partial<House> & { collectionIds?: string[]; tagIds?: string[]; id?: string };
}) {
  const [name, setName] = useState(initial?.name || "");
  const [year, setYear] = useState<number | undefined>(initial?.year);
  const [retiredYear, setRetiredYear] = useState<number | undefined>(initial?.retired_year);
  const [description, setDescription] = useState(initial?.description || "");
  const [sku, setSku] = useState(initial?.sku || "");
  const [price, setPrice] = useState<number | undefined>(initial?.price);
  const [collectionName, setCollectionName] = useState(initial?.collection || "");
  const [series, setSeries] = useState(initial?.series || "");
  const [notes, setNotes] = useState(initial?.notes || "");
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | undefined>(initial?.photo_url);
  const [photoDeleted, setPhotoDeleted] = useState(false);
  const [purchasedYear, setPurchasedYear] = useState<number | undefined>(initial?.purchased_year);
  const [collectionIds, setCollectionIds] = useState<string[]>(initial?.collectionIds || []);
  const [tagIds, setTagIds] = useState<string[]>(initial?.tagIds || []);
  const [saving, setSaving] = useState(false);
  const [linkAccessoryId, setLinkAccessoryId] = useState<string>("");

  // Update form when initial changes (when user selects a different house)
  React.useEffect(() => {
    setName(initial?.name || "");
    setYear(initial?.year);
    setRetiredYear(initial?.retired_year);
    setDescription(initial?.description || "");
    setSku(initial?.sku || "");
    setPrice(initial?.price);
    setCollectionName(initial?.collection || "");
    setSeries(initial?.series || "");
    setNotes(initial?.notes || "");
    setPhotoUrl(initial?.photo_url);
    setPurchasedYear(initial?.purchased_year);
    setCollectionIds(initial?.collectionIds || []);
    setTagIds(initial?.tagIds || []);
    setPhotoFile(null);
    setPhotoDeleted(false);
  }, [initial]);

  async function handleFile(file?: File) {
    if (file) {
      setPhotoFile(file);
      setPhotoDeleted(false);
      // Show preview
      const preview = await fileToDataURL(file);
      setPhotoUrl(preview);
    }
  }

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        setSaving(true);
        try {
          let finalPhotoUrl = photoUrl;
          
          // Upload new photo if selected
          if (photoFile) {
            finalPhotoUrl = await db.uploadImage(photoFile);
          } else if (photoDeleted) {
            // Explicitly set to null when photo was deleted
            finalPhotoUrl = null as any;
          }

          const h: Omit<House, "id" | "user_id" | "created_at" | "updated_at"> = {
            name: name.trim(),
            year,
            retired_year: retiredYear,
            description: description.trim() || undefined,
            sku: sku.trim() || undefined,
            price,
            collection: collectionName.trim() || undefined,
            series: series.trim() || undefined,
            notes: notes.trim() || undefined,
            photo_url: finalPhotoUrl,
            purchased_year: purchasedYear,
          };
          await onSave(h, collectionIds, tagIds, initial?.id);
        } catch (error) {
          console.error("Error saving house:", error);
          const errorMessage = error instanceof Error ? error.message : String(error);
          alert(`Failed to save house: ${errorMessage}`);
        } finally {
          setSaving(false);
        }
      }}
      className="space-y-3"
    >
      {/* House Name - Full Width */}
      <Field label="House name">
        <TextInput
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder="e.g., Mickey's Stuffed Animals"
          disabled={saving}
        />
      </Field>

      {/* SKU and Price Row - Compact */}
      <div className="grid grid-cols-2 gap-3">
        <Field label="SKU / Item Number">
          <TextInput
            value={sku}
            onChange={(e) => setSku(e.target.value)}
            placeholder="e.g., 56.12345"
            disabled={saving}
          />
        </Field>
        <Field label="Price ($)">
          <TextInput
            type="number"
            step="0.01"
            value={price ?? ""}
            onChange={(e) => setPrice(e.target.value ? Number(e.target.value) : undefined)}
            placeholder="79.99"
            disabled={saving}
          />
        </Field>
      </div>

      {/* Years Row - Compact, 4 columns */}
      <div className="grid grid-cols-4 gap-3">
        <Field label="Released">
          <TextInput
            type="number"
            value={year ?? ""}
            onChange={(e) => setYear(e.target.value ? Number(e.target.value) : undefined)}
            placeholder="2018"
            disabled={saving}
            className="w-full"
          />
        </Field>
        <Field label="Retired">
          <TextInput
            type="number"
            value={retiredYear ?? ""}
            onChange={(e) => setRetiredYear(e.target.value ? Number(e.target.value) : undefined)}
            placeholder="2020"
            disabled={saving}
            className="w-full"
          />
        </Field>
        <Field label="Purchased">
          <TextInput
            type="number"
            value={purchasedYear ?? ""}
            onChange={(e) =>
              setPurchasedYear(e.target.value ? Number(e.target.value) : undefined)
            }
            placeholder="2021"
            disabled={saving}
            className="w-full"
          />
        </Field>
      </div>

      {/* Collection and Series Row */}
      <div className="grid grid-cols-2 gap-3">
        <Field label="Collection">
          <TextInput
            value={collectionName}
            onChange={(e) => setCollectionName(e.target.value)}
            placeholder="e.g., North Pole Series"
            disabled={saving}
          />
        </Field>
        <Field label="Series">
          <TextInput
            value={series}
            onChange={(e) => setSeries(e.target.value)}
            placeholder="e.g., Original Snow Village"
            disabled={saving}
          />
        </Field>
      </div>

      {/* Photo Section with Thumbnail */}
      <Field label="Photo">
        <div className="flex items-start gap-3">
          <input
            type="file"
            accept="image/*"
            onChange={(e) => handleFile(e.target.files?.[0])}
            disabled={saving}
            className="flex-1"
          />
          {photoUrl && (
            <div className="relative flex-shrink-0">
              <img
                src={photoUrl}
                alt="preview"
                className="h-20 w-20 rounded-xl object-cover border border-gray-300"
              />
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setPhotoUrl(undefined);
                  setPhotoFile(null);
                  setPhotoDeleted(true);
                }}
                className="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-700 shadow-md"
                title="Delete photo"
              >
                ×
              </button>
            </div>
          )}
        </div>
      </Field>

      <Field label="Description">
        <TextArea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Brief description of the house"
          disabled={saving}
          rows={2}
        />
      </Field>
      <Field label="Notes">
        <TextArea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Additional notes"
          disabled={saving}
        />
      </Field>

      <MultiSelectChips
        options={data.collections}
        selectedIds={collectionIds}
        onChange={setCollectionIds}
        label="Collections"
      />
      <MultiSelectChips
        options={data.tags}
        selectedIds={tagIds}
        onChange={setTagIds}
        label="Tags"
      />

      {/* Link Accessories Section */}
      {initial?.id && onLink && (
        <div className="pt-3 border-t space-y-2">
          <label className="block text-sm font-semibold text-gray-700">Link to Accessory</label>
          <div className="flex gap-2">
            <Select 
              value={linkAccessoryId} 
              onChange={(e) => setLinkAccessoryId(e.target.value)}
              className="flex-1"
            >
              <option value="">Select an accessory...</option>
              {data.accessories
                .slice()
                .sort((a, b) => a.name.localeCompare(b.name))
                .map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name}
                  </option>
                ))}
            </Select>
            <Button
              type="button"
              onClick={async () => {
                if (linkAccessoryId && initial.id) {
                  await onLink(initial.id, linkAccessoryId);
                  setLinkAccessoryId("");
                }
              }}
              disabled={!linkAccessoryId || saving}
              className="bg-green-600 text-white border-green-600 hover:bg-green-700"
            >
              Link
            </Button>
          </div>
        </div>
      )}

      <div className="flex items-center gap-2 pt-2">
        <Button
          type="submit"
          disabled={saving}
          className="bg-green-700 text-white border-green-700 hover:bg-green-800"
        >
          {saving ? "Saving..." : initial?.id ? "Update House" : "Save House"}
        </Button>
        {initial?.id && onMoveToAccessory && (
          <Button
            type="button"
            onClick={() => onMoveToAccessory(initial.id!, name)}
            disabled={saving}
            className="bg-amber-600 text-white border-amber-600 hover:bg-amber-700"
          >
            Move to Accessories
          </Button>
        )}
        {initial?.id && onDelete && (
          <Button
            type="button"
            onClick={() => onDelete(initial.id!, name)}
            disabled={saving}
            className="bg-red-700 text-white border-red-700 hover:bg-red-800"
          >
            Delete
          </Button>
        )}
      </div>
    </form>
  );
}

function AccessoryForm({
  data,
  onSave,
  onDelete,
  onMoveToHouse,
  onLink,
  initial,
}: {
  data: Database;
  onSave: (
    a: Omit<Accessory, "id" | "user_id" | "created_at" | "updated_at">,
    collections: string[],
    tags: string[],
    existingId?: string
  ) => Promise<void>;
  onDelete?: (id: string, name: string) => Promise<void>;
  onMoveToHouse?: (id: string, name: string) => Promise<void>;
  onLink?: (houseId: string, accessoryId: string) => Promise<void>;
  initial?: Partial<Accessory> & { collectionIds?: string[]; tagIds?: string[]; id?: string };
}) {
  const [name, setName] = useState(initial?.name || "");
  const [year, setYear] = useState<number | undefined>(initial?.year);
  const [retiredYear, setRetiredYear] = useState<number | undefined>(initial?.retired_year);
  const [description, setDescription] = useState(initial?.description || "");
  const [sku, setSku] = useState(initial?.sku || "");
  const [price, setPrice] = useState<number | undefined>(initial?.price);
  const [collectionName, setCollectionName] = useState(initial?.collection || "");
  const [series, setSeries] = useState(initial?.series || "");
  const [notes, setNotes] = useState(initial?.notes || "");
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | undefined>(initial?.photo_url);
  const [photoDeleted, setPhotoDeleted] = useState(false);
  const [purchasedYear, setPurchasedYear] = useState<number | undefined>(initial?.purchased_year);
  const [collectionIds, setCollectionIds] = useState<string[]>(initial?.collectionIds || []);
  const [tagIds, setTagIds] = useState<string[]>(initial?.tagIds || []);
  const [saving, setSaving] = useState(false);
  const [linkHouseId, setLinkHouseId] = useState<string>("");

  // Update form when initial changes (when user selects a different accessory)
  React.useEffect(() => {
    setName(initial?.name || "");
    setYear(initial?.year);
    setRetiredYear(initial?.retired_year);
    setDescription(initial?.description || "");
    setSku(initial?.sku || "");
    setPrice(initial?.price);
    setCollectionName(initial?.collection || "");
    setSeries(initial?.series || "");
    setNotes(initial?.notes || "");
    setPhotoUrl(initial?.photo_url);
    setPurchasedYear(initial?.purchased_year);
    setCollectionIds(initial?.collectionIds || []);
    setTagIds(initial?.tagIds || []);
    setPhotoFile(null);
    setPhotoDeleted(false);
  }, [initial]);

  async function handleFile(file?: File) {
    if (file) {
      setPhotoFile(file);
      setPhotoDeleted(false);
      const preview = await fileToDataURL(file);
      setPhotoUrl(preview);
    }
  }

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        setSaving(true);
        try {
          let finalPhotoUrl = photoUrl;
          
          if (photoFile) {
            finalPhotoUrl = await db.uploadImage(photoFile);
          } else if (photoDeleted) {
            // Explicitly set to null when photo was deleted
            finalPhotoUrl = null as any;
          }

          const a: Omit<Accessory, "id" | "user_id" | "created_at" | "updated_at"> = {
            name: name.trim(),
            year,
            retired_year: retiredYear,
            description: description.trim() || undefined,
            sku: sku.trim() || undefined,
            price,
            collection: collectionName.trim() || undefined,
            series: series.trim() || undefined,
            notes: notes.trim() || undefined,
            photo_url: finalPhotoUrl,
            purchased_year: purchasedYear,
          };
          await onSave(a, collectionIds, tagIds, initial?.id);
        } catch (error) {
          console.error("Error saving accessory:", error);
          const errorMessage = error instanceof Error ? error.message : String(error);
          alert(`Failed to save accessory: ${errorMessage}`);
        } finally {
          setSaving(false);
        }
      }}
      className="space-y-3"
    >
      {/* Accessory Name - Full Width */}
      <Field label="Accessory name">
        <TextInput
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder="e.g., Stuffing Station"
          disabled={saving}
        />
      </Field>

      {/* SKU and Price Row - Compact */}
      <div className="grid grid-cols-2 gap-3">
        <Field label="SKU / Item Number">
          <TextInput
            value={sku}
            onChange={(e) => setSku(e.target.value)}
            placeholder="e.g., 56.12345"
            disabled={saving}
          />
        </Field>
        <Field label="Price ($)">
          <TextInput
            type="number"
            step="0.01"
            value={price ?? ""}
            onChange={(e) => setPrice(e.target.value ? Number(e.target.value) : undefined)}
            placeholder="29.99"
            disabled={saving}
          />
        </Field>
      </div>

      {/* Years Row - Compact, 4 columns */}
      <div className="grid grid-cols-4 gap-3">
        <Field label="Released">
          <TextInput
            type="number"
            value={year ?? ""}
            onChange={(e) => setYear(e.target.value ? Number(e.target.value) : undefined)}
            placeholder="2018"
            disabled={saving}
            className="w-full"
          />
        </Field>
        <Field label="Retired">
          <TextInput
            type="number"
            value={retiredYear ?? ""}
            onChange={(e) => setRetiredYear(e.target.value ? Number(e.target.value) : undefined)}
            placeholder="2020"
            disabled={saving}
            className="w-full"
          />
        </Field>
        <Field label="Purchased">
          <TextInput
            type="number"
            value={purchasedYear ?? ""}
            onChange={(e) =>
              setPurchasedYear(e.target.value ? Number(e.target.value) : undefined)
            }
            placeholder="2021"
            disabled={saving}
            className="w-full"
          />
        </Field>
      </div>

      {/* Collection and Series Row */}
      <div className="grid grid-cols-2 gap-3">
        <Field label="Collection">
          <TextInput
            value={collectionName}
            onChange={(e) => setCollectionName(e.target.value)}
            placeholder="e.g., North Pole Series"
            disabled={saving}
          />
        </Field>
        <Field label="Series">
          <TextInput
            value={series}
            onChange={(e) => setSeries(e.target.value)}
            placeholder="e.g., Original Snow Village"
            disabled={saving}
          />
        </Field>
      </div>

      {/* Photo Section with Thumbnail */}
      <Field label="Photo">
        <div className="flex items-start gap-3">
          <input
            type="file"
            accept="image/*"
            onChange={(e) => handleFile(e.target.files?.[0])}
            disabled={saving}
            className="flex-1"
          />
          {photoUrl && (
            <div className="relative flex-shrink-0">
              <img
                src={photoUrl}
                alt="preview"
                className="h-20 w-20 rounded-xl object-cover border border-gray-300"
              />
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setPhotoUrl(undefined);
                  setPhotoFile(null);
                  setPhotoDeleted(true);
                }}
                className="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-700 shadow-md"
                title="Delete photo"
              >
                ×
              </button>
            </div>
          )}
        </div>
      </Field>

      <Field label="Description">
        <TextArea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Brief description of the accessory"
          disabled={saving}
          rows={2}
        />
      </Field>
      <Field label="Notes">
        <TextArea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Additional notes"
          disabled={saving}
        />
      </Field>

      <MultiSelectChips
        options={data.collections}
        selectedIds={collectionIds}
        onChange={setCollectionIds}
        label="Collections"
      />
      <MultiSelectChips
        options={data.tags}
        selectedIds={tagIds}
        onChange={setTagIds}
        label="Tags"
      />

      {/* Link Houses Section */}
      {initial?.id && onLink && (
        <div className="pt-3 border-t space-y-2">
          <label className="block text-sm font-semibold text-gray-700">Link to House</label>
          <div className="flex gap-2">
            <Select 
              value={linkHouseId} 
              onChange={(e) => setLinkHouseId(e.target.value)}
              className="flex-1"
            >
              <option value="">Select a house...</option>
              {data.houses
                .slice()
                .sort((a, b) => a.name.localeCompare(b.name))
                .map((h) => (
                  <option key={h.id} value={h.id}>
                    {h.name}
                  </option>
                ))}
            </Select>
            <Button
              type="button"
              onClick={async () => {
                if (linkHouseId && initial.id) {
                  await onLink(linkHouseId, initial.id);
                  setLinkHouseId("");
                }
              }}
              disabled={!linkHouseId || saving}
              className="bg-green-600 text-white border-green-600 hover:bg-green-700"
            >
              Link
            </Button>
          </div>
        </div>
      )}

      <div className="flex items-center gap-2 pt-2">
        <Button
          type="submit"
          disabled={saving}
          className="bg-green-700 text-white border-green-700 hover:bg-green-800"
        >
          {saving ? "Saving..." : initial?.id ? "Update Accessory" : "Save Accessory"}
        </Button>
        {initial?.id && onMoveToHouse && (
          <Button
            type="button"
            onClick={() => onMoveToHouse(initial.id!, name)}
            disabled={saving}
            className="bg-amber-600 text-white border-amber-600 hover:bg-amber-700"
          >
            Move to Houses
          </Button>
        )}
        {initial?.id && onDelete && (
          <Button
            type="button"
            onClick={() => onDelete(initial.id!, name)}
            disabled={saving}
            className="bg-red-700 text-white border-red-700 hover:bg-red-800"
          >
            Delete
          </Button>
        )}
      </div>
    </form>
  );
}

// ------------------------ App ------------------------
export default function App() {
  const [data, setData] = useState<Database | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  const [tab, setTab] = useState<"browse" | "manage">("browse");
  const [manageView, setManageView] = useState<"edit" | "dataReview" | "import">("edit");
  const [q, setQ] = useState("");
  const [houseFilter, setHouseFilter] = useState<string>("");
  const [accessoryFilter, setAccessoryFilter] = useState<string>("");
  const [collectionFilter, setCollectionFilter] = useState<string>("");
  const [yearFrom, setYearFrom] = useState<string>("");
  const [yearTo, setYearTo] = useState<string>("");
  const [linkHouseId, setLinkHouseId] = useState<string>("");
  const [linkAccId, setLinkAccId] = useState<string>("");
  const [showDuplicatesOnly, setShowDuplicatesOnly] = useState(false);
  const [showUnlinkedHousesOnly, setShowUnlinkedHousesOnly] = useState(false);
  const [showNoPhotosOnly, setShowNoPhotosOnly] = useState(false);
  const [browseView, setBrowseView] = useState<"none" | "houses" | "accessories" | "both">("houses");
  const [filtersCollapsed, setFiltersCollapsed] = useState(false);
  
  // Manage tab - edit existing items
  const [editHouseId, setEditHouseId] = useState<string>("");
  const [editAccessoryId, setEditAccessoryId] = useState<string>("");

  // Import functionality
  const [importText, setImportText] = useState<string>("");
  const [importResults, setImportResults] = useState<any[] | null>(null);
  const [importLoading, setImportLoading] = useState<boolean>(false);
  const [importStep, setImportStep] = useState<"input" | "results" | "review">("input");
  const [selectedForApproval, setSelectedForApproval] = useState<Set<number>>(new Set());
  const [approvalInProgress, setApprovalInProgress] = useState<boolean>(false);
  const [purchaseYears, setPurchaseYears] = useState<Record<number, number | undefined>>({}); // Track purchase year for each item

  // Refs for scrolling
  const accessoriesSectionRef = useRef<HTMLDivElement>(null);

  // Modals
  const imageModal = useModal<{ title?: string; src?: string }>();
  const houseModal = useModal<House>();
  const accessoryModal = useModal<Accessory>();
  const fileRef = useRef<HTMLInputElement>(null);
  const houseFormRef = useRef<HTMLDivElement>(null);
  const accessoryFormRef = useRef<HTMLDivElement>(null);

  // Derived: maps for quick lookup (MUST be before early returns!)
  const collById = useMemo(
    () => data ? Object.fromEntries(data.collections.map((c) => [c.id, c])) : {},
    [data]
  );
  const tagById = useMemo(
    () => data ? Object.fromEntries(data.tags.map((t) => [t.id, t])) : {},
    [data]
  );

  // Filtering helpers (must be defined before useMemo)
  function houseMatches(h: House): boolean {
    if (!data) return false;
    if (q.trim()) {
      const text = [h.name, String(h.year ?? ""), String(h.purchased_year ?? ""), h.notes || ""].join(
        " "
      );
      const tags = data.houseTags
        .filter((x) => x.house_id === h.id)
        .map((x) => tagById[x.tag_id]?.name || "")
        .join(" ");
      const colls = data.houseCollections
        .filter((x) => x.house_id === h.id)
        .map((x) => collById[x.collection_id]?.name || "")
        .join(" ");
      if (!(fuzzyIncludes(text, q) || fuzzyIncludes(tags, q) || fuzzyIncludes(colls, q)))
        return false;
    }
    if (collectionFilter) {
      const has = data.houseCollections.some(
        (x) => x.house_id === h.id && x.collection_id === collectionFilter
      );
      if (!has) return false;
    }
    const yf = yearFrom ? Number(yearFrom) : undefined;
    const yt = yearTo ? Number(yearTo) : undefined;
    // Check if any of the year fields fall within the range
    if (yf || yt) {
      const purchasedYear = h.purchased_year ?? 0;
      const releaseYear = h.year ?? 0;
      const retiredYear = h.retired_year ?? 0;
      const matchesRange = 
        (yf && yt && (
          (purchasedYear >= yf && purchasedYear <= yt) ||
          (releaseYear >= yf && releaseYear <= yt) ||
          (retiredYear >= yf && retiredYear <= yt)
        )) ||
        (yf && !yt && (purchasedYear >= yf || releaseYear >= yf || retiredYear >= yf)) ||
        (!yf && yt && (purchasedYear <= yt || releaseYear <= yt || retiredYear <= yt));
      if (!matchesRange) return false;
    }
    return true;
  }

  function accessoryMatches(a: Accessory): boolean {
    if (!data) return false;
    if (q.trim()) {
      const text = [a.name, String(a.purchased_year ?? ""), a.notes || ""].join(" ");
      const tags = data.accessoryTags
        .filter((x) => x.accessory_id === a.id)
        .map((x) => tagById[x.tag_id]?.name || "")
        .join(" ");
      const colls = data.accessoryCollections
        .filter((x) => x.accessory_id === a.id)
        .map((x) => collById[x.collection_id]?.name || "")
        .join(" ");
      if (!(fuzzyIncludes(text, q) || fuzzyIncludes(tags, q) || fuzzyIncludes(colls, q)))
        return false;
    }
    if (collectionFilter) {
      const has = data.accessoryCollections.some(
        (x) => x.accessory_id === a.id && x.collection_id === collectionFilter
      );
      if (!has) return false;
    }
    const yf = yearFrom ? Number(yearFrom) : undefined;
    const yt = yearTo ? Number(yearTo) : undefined;
    // Check if any of the year fields fall within the range
    if (yf || yt) {
      const purchasedYear = a.purchased_year ?? 0;
      const releaseYear = a.year ?? 0;
      const retiredYear = a.retired_year ?? 0;
      const matchesRange = 
        (yf && yt && (
          (purchasedYear >= yf && purchasedYear <= yt) ||
          (releaseYear >= yf && releaseYear <= yt) ||
          (retiredYear >= yf && retiredYear <= yt)
        )) ||
        (yf && !yt && (purchasedYear >= yf || releaseYear >= yf || retiredYear >= yf)) ||
        (!yf && yt && (purchasedYear <= yt || releaseYear <= yt || retiredYear <= yt));
      if (!matchesRange) return false;
    }
    return true;
  }

  // Get duplicate item IDs
  const duplicateItemIds = useMemo(() => {
    if (!data) return { houseIds: new Set<string>(), accessoryIds: new Set<string>() };

    const houseIds = new Set<string>();
    const accessoryIds = new Set<string>();

    // Check houses for exact matches
    const housesByName = new Map<string, House[]>();
    data.houses.forEach(h => {
      const name = h.name.trim();
      if (!housesByName.has(name)) {
        housesByName.set(name, []);
      }
      housesByName.get(name)!.push(h);
    });
    housesByName.forEach((houses) => {
      if (houses.length > 1) {
        houses.forEach(h => houseIds.add(h.id));
      }
    });

    // Check houses for case-insensitive matches
    const housesByLowerName = new Map<string, House[]>();
    data.houses.forEach(h => {
      const name = h.name.trim().toLowerCase();
      if (!housesByLowerName.has(name)) {
        housesByLowerName.set(name, []);
      }
      housesByLowerName.get(name)!.push(h);
    });
    housesByLowerName.forEach((houses) => {
      if (houses.length > 1) {
        const names = houses.map(h => h.name.trim());
        const uniqueNames = new Set(names);
        if (uniqueNames.size > 1) {
          houses.forEach(h => houseIds.add(h.id));
        }
      }
    });

    // Check for houses that also exist as accessories
    data.houses.forEach(h => {
      const matchingAccessory = data.accessories.find(a => 
        a.name.trim().toLowerCase() === h.name.trim().toLowerCase()
      );
      if (matchingAccessory) {
        houseIds.add(h.id);
        accessoryIds.add(matchingAccessory.id);
      }
    });

    // Check accessories for exact matches
    const accessoriesByName = new Map<string, Accessory[]>();
    data.accessories.forEach(a => {
      const name = a.name.trim();
      if (!accessoriesByName.has(name)) {
        accessoriesByName.set(name, []);
      }
      accessoriesByName.get(name)!.push(a);
    });
    accessoriesByName.forEach((accessories) => {
      if (accessories.length > 1) {
        accessories.forEach(a => accessoryIds.add(a.id));
      }
    });

    // Check accessories for case-insensitive matches
    const accessoriesByLowerName = new Map<string, Accessory[]>();
    data.accessories.forEach(a => {
      const name = a.name.trim().toLowerCase();
      if (!accessoriesByLowerName.has(name)) {
        accessoriesByLowerName.set(name, []);
      }
      accessoriesByLowerName.get(name)!.push(a);
    });
    accessoriesByLowerName.forEach((accessories) => {
      if (accessories.length > 1) {
        const names = accessories.map(a => a.name.trim());
        const uniqueNames = new Set(names);
        if (uniqueNames.size > 1) {
          accessories.forEach(a => accessoryIds.add(a.id));
        }
      }
    });

    return { houseIds, accessoryIds };
  }, [data]);

  // Calculate filter counts for UI display
  const unlinkedHousesCount = useMemo(() => {
    if (!data) return 0;
    return data.houses.filter(h => data.houseAccessoryLinks.filter(l => l.house_id === h.id).length === 0).length;
  }, [data]);

  const noPhotosCount = useMemo(() => {
    if (!data) return 0;
    const noPhotoHouses = data.houses.filter(h => !h.photo_url || h.photo_url.trim() === '').length;
    const noPhotoAccessories = data.accessories.filter(a => !a.photo_url || a.photo_url.trim() === '').length;
    return noPhotoHouses + noPhotoAccessories;
  }, [data]);

  const filteredHouses = useMemo(() => {
    if (!data) return [];
    let rows = data.houses.filter(houseMatches);
    if (accessoryFilter) {
      const linkedHouseIds = new Set(
        data.houseAccessoryLinks.filter((l) => l.accessory_id === accessoryFilter).map((l) => l.house_id)
      );
      rows = rows.filter((h) => linkedHouseIds.has(h.id));
    }
    if (houseFilter) rows = rows.filter((h) => h.id === houseFilter);
    if (showDuplicatesOnly) rows = rows.filter((h) => duplicateItemIds.houseIds.has(h.id));
    if (showUnlinkedHousesOnly) {
      const linkedHouseIds = new Set(data.houseAccessoryLinks.map((l) => l.house_id));
      rows = rows.filter((h) => !linkedHouseIds.has(h.id));
    }
    if (showNoPhotosOnly) {
      rows = rows.filter((h) => !h.photo_url);
    }
    return rows.sort((a, b) => a.name.localeCompare(b.name));
  }, [data, q, houseFilter, accessoryFilter, collectionFilter, yearFrom, yearTo, showDuplicatesOnly, showUnlinkedHousesOnly, showNoPhotosOnly, duplicateItemIds]);

  const filteredAccessories = useMemo(() => {
    if (!data) return [];
    let rows = data.accessories.filter(accessoryMatches);
    if (houseFilter) {
      const linkedAccIds = new Set(
        data.houseAccessoryLinks.filter((l) => l.house_id === houseFilter).map((l) => l.accessory_id)
      );
      rows = rows.filter((a) => linkedAccIds.has(a.id));
    }
    if (accessoryFilter) rows = rows.filter((a) => a.id === accessoryFilter);
    if (showDuplicatesOnly) rows = rows.filter((a) => duplicateItemIds.accessoryIds.has(a.id));
    if (showNoPhotosOnly) {
      rows = rows.filter((a) => !a.photo_url);
    }
    return rows.sort((a, b) => a.name.localeCompare(b.name));
  }, [data, q, houseFilter, accessoryFilter, collectionFilter, yearFrom, yearTo, showDuplicatesOnly, showNoPhotosOnly, duplicateItemIds]);

  // Load data from Supabase
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log("Starting to fetch data...");
      console.log("Supabase URL:", import.meta.env.VITE_SUPABASE_URL);
      console.log("Has Supabase Key:", !!import.meta.env.VITE_SUPABASE_ANON_KEY);
      
      // Create a timeout promise
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error("Data fetch timed out after 30 seconds. This may indicate a network issue or the Supabase connection is blocked on mobile.")), 30000);
      });
      
      // Race between fetch and timeout
      const fetchedData = await Promise.race([
        db.fetchAllData(),
        timeoutPromise
      ]) as Database;
      
      console.log("Fetched data:", fetchedData);
      console.log("Houses:", fetchedData.houses.length);
      console.log("Accessories:", fetchedData.accessories.length);
      setData(fetchedData);
      console.log("Data set successfully!");
    } catch (err: any) {
      console.error("Error loading data:", err);
      console.error("Error details:", {
        message: err.message,
        name: err.name,
        stack: err.stack,
        details: err.details,
        hint: err.hint,
        code: err.code
      });
      setError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  // Check if user is an allowed admin
  const isAdmin = useMemo(() => {
    if (!user?.email) return false;
    return ALLOWED_ADMIN_EMAILS.includes(user.email);
  }, [user]);

  // Check auth state on mount
  useEffect(() => {
    console.log("Checking auth state...");
    
    // Set a timeout to prevent infinite loading
    const timeout = setTimeout(() => {
      if (!authChecked) {
        console.warn("Auth check timed out after 10 seconds");
        setAuthChecked(true);
      }
    }, 10000);

    supabase.auth.getSession()
      .then(({ data: { session } }) => {
        console.log("Auth session:", session ? "exists" : "none");
        setUser(session?.user ?? null);
        setAuthChecked(true);
        clearTimeout(timeout);
      })
      .catch((err) => {
        console.error("Error checking auth:", err);
        setAuthChecked(true); // Still mark as checked even on error
        clearTimeout(timeout);
      });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      console.log("Auth state changed:", _event);
      setUser(session?.user ?? null);
    });

    return () => {
      subscription.unsubscribe();
      clearTimeout(timeout);
    };
  }, []);

  useEffect(() => {
    if (authChecked) {
      console.log("Auth checked, loading data...");
      loadData();
    }
  }, [authChecked]);

  // Auto-collapse filters when scrolling down
  useEffect(() => {
    let lastScrollY = window.scrollY;
    let ticking = false;

    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const currentScrollY = window.scrollY;
          const scrollDelta = currentScrollY - lastScrollY;
          
          // Only auto-collapse if:
          // 1. Scrolling down (positive delta)
          // 2. Scrolled past 120px from top (past header)
          // 3. Scrolled at least 30px in one movement (intentional but not too aggressive)
          // 4. Filters are currently expanded
          if (scrollDelta > 30 && currentScrollY > 120 && !filtersCollapsed) {
            setFiltersCollapsed(true);
          }
          
          lastScrollY = currentScrollY;
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [filtersCollapsed]);

  // Redirect non-admins away from manage tab
  useEffect(() => {
    if (tab === "manage" && !isAdmin) {
      setTab("browse");
    }
  }, [tab, isAdmin]);

  if (loading || !authChecked) {
    return (
      <div className="min-h-screen grid place-items-center bg-gradient-to-b from-gray-50 to-white">
        <div className="text-center">
          <div className="inline-grid place-items-center h-16 w-16 rounded-2xl bg-red-600 text-white font-bold text-2xl mb-4 animate-pulse">
            56
          </div>
          <div className="text-gray-600">Loading your collection...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen grid place-items-center bg-gradient-to-b from-gray-50 to-white p-4">
        <Card className="p-6 max-w-md">
          <div className="text-center space-y-4">
            <div className="text-red-600 font-semibold text-lg">Error Loading Data</div>
            <div className="text-sm text-gray-600 whitespace-pre-wrap text-left bg-gray-100 p-3 rounded">{error}</div>
            
            {/* Diagnostic Information */}
            <div className="text-xs text-left space-y-1 text-gray-500 bg-gray-50 p-3 rounded">
              <div><strong>Browser:</strong> {navigator.userAgent}</div>
              <div><strong>Connection:</strong> {(navigator as any).connection?.effectiveType || 'Unknown'}</div>
              <div><strong>Online:</strong> {navigator.onLine ? 'Yes' : 'No'}</div>
              <div><strong>Supabase URL:</strong> {import.meta.env.VITE_SUPABASE_URL || 'MISSING'}</div>
              <div><strong>Has API Key:</strong> {import.meta.env.VITE_SUPABASE_ANON_KEY ? 'Yes' : 'NO - THIS IS THE PROBLEM'}</div>
            </div>
            
            <Button onClick={loadData} className="bg-red-600 text-white hover:bg-red-700">
              Retry
            </Button>
            
            <div className="text-xs text-gray-500 mt-4">
              If this error persists on mobile, try:
              <ul className="text-left mt-2 space-y-1 list-disc list-inside">
                <li>Refreshing the page (hard refresh)</li>
                <li>Clearing browser cache</li>
                <li>Using a different browser</li>
                <li>Checking your network connection</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (!data) return null;

  // CRUD helpers
  async function addHouse(
    h: Omit<House, "id" | "user_id" | "created_at" | "updated_at">,
    collectionIds: string[],
    tagIds: string[],
    existingId?: string
  ) {
    if (!data) return;
    
    try {
      let houseId: string;
      
      if (existingId) {
        // Update existing house
        await db.updateHouse(existingId, h);
        
        // Update collections - delete all and re-add
        const currentCollections = data.houseCollections.filter(hc => hc.house_id === existingId);
        for (const link of currentCollections) {
          await supabase.from('house_collections').delete().eq('id', link.id);
        }
        if (collectionIds.length > 0) {
          await supabase.from('house_collections').insert(
            collectionIds.map(collection_id => ({
              house_id: existingId,
              collection_id
            }))
          );
        }
        
        // Update tags - delete all and re-add
        const currentTags = data.houseTags.filter(ht => ht.house_id === existingId);
        for (const link of currentTags) {
          await supabase.from('house_tags').delete().eq('id', link.id);
        }
        if (tagIds.length > 0) {
          await supabase.from('house_tags').insert(
            tagIds.map(tag_id => ({
              house_id: existingId,
              tag_id,
              source: 'manual' as const,
              reviewed: true
            }))
          );
        }
        
        houseId = existingId;
      } else {
        // Create new house
        const newHouse = await db.createHouse(h, collectionIds, tagIds);
        houseId = newHouse.id;
      }
      
      await loadData(); // Refresh data
      // Stay in current tab instead of switching to browse
      // setTab("browse");
      // setBrowseView("both");
      // setHouseFilter(houseId);
      setEditHouseId(""); // Clear the edit selection
    } catch (error) {
      console.error("Error adding/updating house:", error);
      throw error;
    }
  }

  async function addAccessory(
    a: Omit<Accessory, "id" | "user_id" | "created_at" | "updated_at">,
    collectionIds: string[],
    tagIds: string[],
    existingId?: string
  ) {
    if (!data) return;
    
    try {
      let accessoryId: string;
      
      if (existingId) {
        // Update existing accessory
        await db.updateAccessory(existingId, a);
        
        // Update collections - delete all and re-add
        const currentCollections = data.accessoryCollections.filter(ac => ac.accessory_id === existingId);
        for (const link of currentCollections) {
          await supabase.from('accessory_collections').delete().eq('id', link.id);
        }
        if (collectionIds.length > 0) {
          await supabase.from('accessory_collections').insert(
            collectionIds.map(collection_id => ({
              accessory_id: existingId,
              collection_id
            }))
          );
        }
        
        // Update tags - delete all and re-add
        const currentTags = data.accessoryTags.filter(at => at.accessory_id === existingId);
        for (const link of currentTags) {
          await supabase.from('accessory_tags').delete().eq('id', link.id);
        }
        if (tagIds.length > 0) {
          await supabase.from('accessory_tags').insert(
            tagIds.map(tag_id => ({
              accessory_id: existingId,
              tag_id,
              source: 'manual' as const,
              reviewed: true
            }))
          );
        }
        
        accessoryId = existingId;
      } else {
        // Create new accessory
        const newAccessory = await db.createAccessory(a, collectionIds, tagIds);
        accessoryId = newAccessory.id;
      }
      
      await loadData(); // Refresh data
      // Stay in current tab instead of switching to browse
      // setTab("browse");
      // setBrowseView("both");
      // setAccessoryFilter(accessoryId);
      setEditAccessoryId(""); // Clear the edit selection
    } catch (error) {
      console.error("Error adding/updating accessory:", error);
      throw error;
    }
  }

  async function addLink(houseId: string, accessoryId: string) {
    if (!houseId || !accessoryId) return;
    const exists = data.houseAccessoryLinks.some(
      (l) => l.house_id === houseId && l.accessory_id === accessoryId
    );
    if (exists) return;
    try {
      await db.linkHouseToAccessory(houseId, accessoryId);
      await loadData();
    } catch (error) {
      console.error("Error linking:", error);
      alert("Failed to link. Please try again.");
    }
  }

  async function unlink(linkId: string) {
    try {
      await db.unlinkHouseFromAccessory(linkId);
      await loadData();
    } catch (error) {
      console.error("Error unlinking:", error);
      alert("Failed to unlink. Please try again.");
    }
  }

  async function deleteHouse(houseId: string, houseName: string) {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${houseName}"?\n\nThis will also remove all links to accessories, but the accessories themselves will not be deleted.\n\nThis action cannot be undone.`
    );
    if (!confirmed) return;
    
    try {
      await db.deleteHouse(houseId);
      await loadData();
      setEditHouseId(""); // Clear the edit selection
      alert("House deleted successfully.");
    } catch (error) {
      console.error("Error deleting house:", error);
      alert("Failed to delete house. Please try again.");
    }
  }

  async function deleteAccessory(accessoryId: string, accessoryName: string) {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${accessoryName}"?\n\nThis will also remove all links to houses, but the houses themselves will not be deleted.\n\nThis action cannot be undone.`
    );
    if (!confirmed) return;
    
    try {
      await db.deleteAccessory(accessoryId);
      await loadData();
      setEditAccessoryId(""); // Clear the edit selection
      alert("Accessory deleted successfully.");
    } catch (error) {
      console.error("Error deleting accessory:", error);
      alert("Failed to delete accessory. Please try again.");
    }
  }

  async function moveAccessoryToHouse(accessoryId: string, accessoryName: string) {
    const confirmed = window.confirm(
      `Are you sure you want to move "${accessoryName}" to the Houses table?\n\nAll data (photo, metadata, collections, tags) will be preserved, and any links to houses will be removed.\n\nThis action cannot be undone.`
    );
    if (!confirmed) return;
    
    try {
      if (!data) return;
      
      // Get the accessory data
      const accessory = data.accessories.find(a => a.id === accessoryId);
      if (!accessory) {
        alert("Accessory not found.");
        return;
      }

      // Get collections and tags
      const collectionIds = data.accessoryCollections
        .filter(ac => ac.accessory_id === accessoryId)
        .map(ac => ac.collection_id);
      const tagIds = data.accessoryTags
        .filter(at => at.accessory_id === accessoryId)
        .map(at => at.tag_id);

      // Create as house
      const houseData: Omit<House, "id" | "user_id" | "created_at" | "updated_at"> = {
        name: accessory.name,
        year: accessory.year,
        retired_year: accessory.retired_year,
        description: accessory.description,
        sku: accessory.sku,
        price: accessory.price,
        collection: accessory.collection,
        series: accessory.series,
        notes: accessory.notes,
        photo_url: accessory.photo_url,
        purchased_year: accessory.purchased_year,
      };

      await db.createHouse(houseData, collectionIds, tagIds);
      
      // Delete the accessory (this also removes links)
      await db.deleteAccessory(accessoryId);
      
      await loadData();
      setEditAccessoryId(""); // Clear the edit selection
      alert(`"${accessoryName}" moved to Houses successfully.`);
    } catch (error) {
      console.error("Error moving accessory to house:", error);
      alert("Failed to move item. Please try again.");
    }
  }

  async function moveHouseToAccessory(houseId: string, houseName: string) {
    const confirmed = window.confirm(
      `Are you sure you want to move "${houseName}" to the Accessories table?\n\nAll data (photo, metadata, collections, tags) will be preserved, and any links to accessories will be removed.\n\nThis action cannot be undone.`
    );
    if (!confirmed) return;
    
    try {
      if (!data) return;
      
      // Get the house data
      const house = data.houses.find(h => h.id === houseId);
      if (!house) {
        alert("House not found.");
        return;
      }

      // Get collections and tags
      const collectionIds = data.houseCollections
        .filter(hc => hc.house_id === houseId)
        .map(hc => hc.collection_id);
      const tagIds = data.houseTags
        .filter(ht => ht.house_id === houseId)
        .map(ht => ht.tag_id);

      // Create as accessory
      const accessoryData: Omit<Accessory, "id" | "user_id" | "created_at" | "updated_at"> = {
        name: house.name,
        year: house.year,
        retired_year: house.retired_year,
        description: house.description,
        sku: house.sku,
        price: house.price,
        collection: house.collection,
        series: house.series,
        notes: house.notes,
        photo_url: house.photo_url,
        purchased_year: house.purchased_year,
      };

      await db.createAccessory(accessoryData, collectionIds, tagIds);
      
      // Delete the house (this also removes links)
      await db.deleteHouse(houseId);
      
      await loadData();
      setEditHouseId(""); // Clear the edit selection
      alert(`"${houseName}" moved to Accessories successfully.`);
    } catch (error) {
      console.error("Error moving house to accessory:", error);
      alert("Failed to move item. Please try again.");
    }
  }

  // Manage lists: Collections & Tags
  async function addCollection(name: string) {
    const trimmed = name.trim();
    if (!trimmed) return;
    if (data.collections.some((c) => c.name.toLowerCase() === trimmed.toLowerCase())) {
      alert("Collection already exists");
      return;
    }
    try {
      await db.createCollection(trimmed);
      await loadData();
    } catch (error) {
      console.error("Error adding collection:", error);
      alert("Failed to add collection. Please try again.");
    }
  }

  async function addTag(name: string) {
    const trimmed = name.trim();
    if (!trimmed) return;
    if (data.tags.some((t) => t.name.toLowerCase() === trimmed.toLowerCase())) {
      alert("Tag already exists");
      return;
    }
    try {
      await db.createTag(trimmed);
      await loadData();
    } catch (error) {
      console.error("Error adding tag:", error);
      alert("Failed to add tag. Please try again.");
    }
  }

  // Import / Export
  function exportJSON() {
    download(`dept56-export-${new Date().toISOString().slice(0, 10)}.json`, JSON.stringify(data, null, 2));
  }
  async function importJSON(file?: File) {
    alert("Import from JSON is not yet implemented for Supabase version. Please add items manually or contact support.");
  }

  // House import functionality using web scraper
  async function handleImportHouses() {
    if (!importText.trim()) {
      alert("Please enter at least one house name");
      return;
    }

    setImportLoading(true);
    try {
      // Parse house names from text (one per line)
      const houseNames = importText
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);

      if (houseNames.length === 0) {
        alert("No valid house names found");
        return;
      }

      // Load the pre-generated search index
      const response = await fetch('/house_search_index.json');
      if (!response.ok) {
        throw new Error('Failed to load search index');
      }
      
      const searchData = await response.json();
      const houses = searchData.houses;

      // Set up Fuse.js for fuzzy searching
      const fuse = new Fuse<SearchIndexHouse>(houses, {
        keys: ['name', 'collection'],
        threshold: 0.4, // 0.6 similarity required (lower = more strict)
        includeScore: true,
        minMatchCharLength: 3,
        ignoreLocation: true
      });

      const results = houseNames.map(houseName => {
        const searchResults = fuse.search(houseName);
        
        if (searchResults.length > 0) {
          const bestMatch = searchResults[0];
          const confidence = Math.max(0, 1 - bestMatch.score!); // Convert Fuse score to confidence
          
          if (confidence > 0.5) { // Minimum confidence threshold
            return {
              input_name: houseName,
              status: 'found' as const,
              confidence: confidence,
              source: 'search_index',
              scraped_data: {
                name: bestMatch.item.name,
                year: bestMatch.item.year,
                description: bestMatch.item.description,
                sku: bestMatch.item.sku,
                collection: bestMatch.item.collection,
                photo_url: bestMatch.item.photo_url,
                images: bestMatch.item.images,
                url: bestMatch.item.url,
                srp: bestMatch.item.srp,
                intro_year: bestMatch.item.intro_year,
                retired_year: bestMatch.item.retired_year
              }
            };
          }
        }
        
        return {
          input_name: houseName,
          status: 'not_found' as const,
          confidence: 0,
          source: null,
          scraped_data: null
        };
      });

      setImportResults(results);
      setImportStep("results");
    } catch (error) {
      console.error('Import error:', error);
      alert('Error processing import. Please try again.');
    } finally {
      setImportLoading(false);
    }
  }

  function resetImport() {
    setImportText("");
    setImportResults(null);
    setImportStep("input");
    setSelectedForApproval(new Set());
    setPurchaseYears({});
  }

  function toggleItemSelection(index: number) {
    const newSelection = new Set(selectedForApproval);
    if (newSelection.has(index)) {
      newSelection.delete(index);
    } else {
      newSelection.add(index);
    }
    setSelectedForApproval(newSelection);
  }

  async function approveSelectedItems() {
    if (!importResults || selectedForApproval.size === 0) {
      alert("No items selected for approval");
      return;
    }

    setApprovalInProgress(true);
    const successfulAdds: string[] = [];
    const failedAdds: string[] = [];

    try {
      for (const index of selectedForApproval) {
        const result = importResults[index];
        if (!result || result.status !== 'found' || !result.scraped_data) {
          failedAdds.push(result?.input_name || `Item ${index}`);
          continue;
        }

        try {
          // Use the existing addHouse function
          await addHouse({
            name: result.scraped_data.name,
            year: result.scraped_data.intro_year || undefined,
            retired_year: result.scraped_data.retired_year || undefined,
            description: result.scraped_data.description || '',
            sku: result.scraped_data.sku || '',
            photo_url: result.scraped_data.photo_url || '',
            purchased_year: purchaseYears[index] || undefined,
            collection: result.scraped_data.collection || undefined,
          }, [], []); // Empty collections and tags arrays - can be assigned later

          successfulAdds.push(result.scraped_data.name);
        } catch (error) {
          console.error(`Failed to add ${result.scraped_data.name}:`, error);
          failedAdds.push(result.scraped_data.name);
        }
      }

      // Show results
      let message = '';
      if (successfulAdds.length > 0) {
        message += `✅ Successfully added ${successfulAdds.length} house(s):\n${successfulAdds.join(', ')}\n\n`;
      }
      if (failedAdds.length > 0) {
        message += `❌ Failed to add ${failedAdds.length} house(s):\n${failedAdds.join(', ')}`;
      }

      alert(message);

      if (successfulAdds.length > 0) {
        // Reset the import workflow on success
        resetImport();
        // Reload data to show new houses
        await loadData();
      }

    } catch (error) {
      console.error('Approval process error:', error);
      alert('Error during approval process. Please try again.');
    } finally {
      setApprovalInProgress(false);
    }
  }

  // UI cards
  function HouseCard({ h }: { h: House }) {
    // Get unique accessories with photos only
    const accessoryMap = new Map<string, { linkId: string; a: Accessory }>();
    data.houseAccessoryLinks
      .filter((l) => l.house_id === h.id)
      .forEach((l) => {
        const accessory = data.accessories.find((x) => x.id === l.accessory_id);
        // Only include if accessory exists and has a photo
        if (accessory && accessory.photo_url) {
          // Use accessory ID as key to deduplicate
          if (!accessoryMap.has(accessory.id)) {
            accessoryMap.set(accessory.id, { linkId: l.id, a: accessory });
          }
        }
      });
    const accessories = Array.from(accessoryMap.values());
    
    const colls = data.houseCollections
      .filter((x) => x.house_id === h.id)
      .map((x) => collById[x.collection_id])
      .filter(Boolean) as Collection[];
    const tags = data.houseTags
      .filter((x) => x.house_id === h.id)
      .map((x) => tagById[x.tag_id])
      .filter(Boolean) as Tag[];
    
    return (
      <Card className="overflow-hidden cursor-pointer hover:shadow-lg transition-shadow">
        <div
          className="block w-full"
          onClick={() => houseModal.show(h)}
        >
          {h.photo_url ? (
            <img src={h.photo_url} alt={h.name} className="w-full h-48 object-cover" />
          ) : (
            <div className="w-full h-48 grid place-items-center text-gray-400 text-sm">No photo</div>
          )}
        </div>
        <div className="p-3 space-y-2">
          <div 
            className="font-semibold leading-tight cursor-pointer hover:text-indigo-600"
            onClick={() => houseModal.show(h)}
          >
            {h.name}
          </div>
          {colls.length > 0 && (
            <div className="flex gap-2 flex-wrap">
              {colls.map((c) => (
                <Pill key={c.id}>{c.name}</Pill>
              ))}
            </div>
          )}
          {tags.length > 0 && (
            <div className="flex gap-1 flex-wrap text-[11px] text-gray-700">
              {tags.map((t) => (
                <span key={t.id} className="bg-gray-100 rounded-full px-2 py-0.5">
                  #{t.name}
                </span>
              ))}
            </div>
          )}
          {accessories.length > 0 && (
            <div className="pt-2">
              <div className="text-xs text-gray-500">
                {accessories.length} {accessories.length === 1 ? 'accessory' : 'accessories'}
              </div>
            </div>
          )}
        </div>
      </Card>
    );
  }

  function AccessoryCard({ a }: { a: Accessory }) {
    const houses = data.houseAccessoryLinks
      .filter((l) => l.accessory_id === a.id)
      .map((l) => ({
        linkId: l.id,
        h: data.houses.find((x) => x.id === l.house_id)!,
      }))
      .filter((x) => x.h);
    const colls = data.accessoryCollections
      .filter((x) => x.accessory_id === a.id)
      .map((x) => collById[x.collection_id])
      .filter(Boolean) as Collection[];
    const tags = data.accessoryTags
      .filter((x) => x.accessory_id === a.id)
      .map((x) => tagById[x.tag_id])
      .filter(Boolean) as Tag[];
    
    return (
      <Card className="overflow-hidden cursor-pointer hover:shadow-lg transition-shadow">
        <div
          className="block w-full"
          onClick={() => accessoryModal.show(a)}
        >
          {a.photo_url ? (
            <img src={a.photo_url} alt={a.name} className="w-full h-48 object-cover" />
          ) : (
            <div className="w-full h-48 grid place-items-center text-gray-400 text-sm">No photo</div>
          )}
        </div>
        <div className="p-3 space-y-2">
          <div 
            className="font-semibold leading-tight cursor-pointer hover:text-indigo-600"
            onClick={() => accessoryModal.show(a)}
          >
            {a.name}
          </div>
          {colls.length > 0 && (
            <div className="flex gap-2 flex-wrap">
              {colls.map((c) => (
                <Pill key={c.id}>{c.name}</Pill>
              ))}
            </div>
          )}
          {tags.length > 0 && (
            <div className="flex gap-1 flex-wrap text-[11px] text-gray-700">
              {tags.map((t) => (
                <span key={t.id} className="bg-gray-100 rounded-full px-2 py-0.5">
                  #{t.name}
                </span>
              ))}
            </div>
          )}
        </div>
      </Card>
    );
  }

  // Link state logic
  const canLink =
    linkHouseId &&
    linkAccId &&
    !data.houseAccessoryLinks.some((l) => l.house_id === linkHouseId && l.accessory_id === linkAccId);

  // Toggle duplicate filter
  function toggleDuplicateFilter() {
    const newValue = !showDuplicatesOnly;
    setShowDuplicatesOnly(newValue);
    if (newValue) {
      // Clear other filters and show browse view
      setHouseFilter("");
      setAccessoryFilter("");
      setCollectionFilter("");
      setYearFrom("");
      setYearTo("");
      setQ("");
      setShowUnlinkedHousesOnly(false);
      setShowNoPhotosOnly(false);
      setBrowseView("both");
    }
  }

  // Toggle unlinked houses filter
  function toggleUnlinkedHousesFilter() {
    const newValue = !showUnlinkedHousesOnly;
    setShowUnlinkedHousesOnly(newValue);
    if (newValue) {
      // Clear other filters and show browse view
      setHouseFilter("");
      setAccessoryFilter("");
      setCollectionFilter("");
      setYearFrom("");
      setYearTo("");
      setQ("");
      setShowDuplicatesOnly(false);
      setShowNoPhotosOnly(false);
      setBrowseView("both");
    }
  }

  // Toggle no photos filter
  function toggleNoPhotosFilter() {
    const newValue = !showNoPhotosOnly;
    setShowNoPhotosOnly(newValue);
    if (newValue) {
      // Clear other filters and show browse view
      setHouseFilter("");
      setAccessoryFilter("");
      setCollectionFilter("");
      setYearFrom("");
      setYearTo("");
      setQ("");
      setShowDuplicatesOnly(false);
      setShowUnlinkedHousesOnly(false);
      setBrowseView("both");
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white text-gray-900">
      <header className="sticky top-0 z-40 backdrop-blur bg-white/70 border-b">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="inline-grid place-items-center h-9 w-9 rounded-xl bg-red-600 text-white font-bold">
              56
            </span>
            <div className="leading-tight">
              <div className="font-semibold">Department 56 Browser</div>
              <div className="text-xs text-gray-500">Christmas in the Cloud</div>
            </div>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Button 
              onClick={() => setTab("browse")} 
              className={tab === "browse" ? "bg-gray-100 text-gray-900 border-gray-300" : "bg-green-700 text-white border-green-700 hover:bg-green-800"}
            >
              Browse
            </Button>
            <Button 
              onClick={async () => {
                if (isAdmin) {
                  // User is already authenticated and is admin, go to manage
                  setTab("manage");
                  setManageView("edit"); // Default to edit view
                } else if (user && !isAdmin) {
                  // User is authenticated but not admin, show message
                  alert("Admin access required. Only whitelisted accounts can manage the collection.");
                } else {
                  // User not authenticated, trigger Google sign-in
                  try {
                    const { error } = await supabase.auth.signInWithOAuth({
                      provider: 'google',
                      options: {
                        redirectTo: window.location.origin,
                      }
                    });
                    if (error) {
                      console.error('OAuth error:', error);
                      if (error.message.includes('not enabled') || error.message.includes('Unsupported provider')) {
                        alert('Google sign-in is not yet configured. Please follow the setup guide in GOOGLE_AUTH_SETUP.md to enable Google OAuth in your Supabase project.');
                      } else {
                        alert(`Sign in error: ${error.message}`);
                      }
                    }
                  } catch (err) {
                    console.error('Sign in error:', err);
                    alert('Unable to sign in. Please check the setup guide in GOOGLE_AUTH_SETUP.md');
                  }
                }
              }} 
              className={tab === "manage" ? "bg-gray-100 text-gray-900 border-gray-300" : "bg-red-700 text-white border-red-700 hover:bg-red-800"}
            >
              Manage
            </Button>
            {user && !isAdmin && (
              <span className="text-xs text-gray-500 ml-2">Signed in as {user.email}</span>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-4 space-y-6">
        {tab === "browse" ? (
          <>
            <Card className="sticky top-[73px] z-30 bg-white shadow-md">
              {/* Collapse Toggle Bar */}
              <div 
                className="flex items-center justify-between p-3 sm:p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => setFiltersCollapsed(!filtersCollapsed)}
              >
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-700">
                    {filtersCollapsed ? "Show Filters & Navigation" : "Hide Filters & Navigation"}
                  </span>
                  {filtersCollapsed && (
                    <span className="text-sm text-gray-500">
                      ({browseView === "houses" ? "Houses" : browseView === "accessories" ? "Accessories" : browseView === "both" ? "Both" : "None"})
                    </span>
                  )}
                </div>
                <svg 
                  className={`w-5 h-5 text-gray-600 transition-transform ${filtersCollapsed ? '' : 'rotate-180'}`}
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>

              {/* Collapsible Content */}
              {!filtersCollapsed && (
            <div className="px-3 sm:px-4 pb-3 sm:pb-4 border-t space-y-3">
            
            {/* Navigation buttons row */}
            <div className="flex flex-wrap items-center gap-2 sm:gap-3 pt-3">
              <div className="font-semibold text-gray-700 text-sm sm:text-base">Browse:</div>
              <Button 
                onClick={() => {
                  if (tab === "manage") {
                    // In Manage tab, always navigate to Browse with houses view
                    setQ("");
                    setHouseFilter("");
                    setAccessoryFilter("");
                    setCollectionFilter("");
                    setYearFrom("");
                    setYearTo("");
                    setShowDuplicatesOnly(false);
                    setShowUnlinkedHousesOnly(false);
                    setShowNoPhotosOnly(false);
                    setBrowseView("houses");
                    setTab("browse");
                  } else if (browseView === "houses") {
                    setBrowseView("none");
                  } else {
                    // Clear all filters when opening full gallery
                    setQ("");
                    setHouseFilter("");
                    setAccessoryFilter("");
                    setCollectionFilter("");
                    setYearFrom("");
                    setYearTo("");
                    setShowDuplicatesOnly(false);
                    setShowUnlinkedHousesOnly(false);
                    setShowNoPhotosOnly(false);
                    setBrowseView("houses");
                  }
                }}
                className={browseView === "houses" 
                  ? "bg-red-700 text-white border-red-700" 
                  : "bg-red-600 text-white border-red-600 hover:bg-red-700"
                }
              >
                {tab === "manage" 
                  ? `Houses (${data.houses.length})`
                  : browseView === "houses" 
                    ? "Hide Houses" 
                    : `Houses (${data.houses.length})`
                }
              </Button>
              <Button 
                onClick={() => {
                  if (tab === "manage") {
                    // In Manage tab, always navigate to Browse with accessories view
                    setQ("");
                    setHouseFilter("");
                    setAccessoryFilter("");
                    setCollectionFilter("");
                    setYearFrom("");
                    setYearTo("");
                    setShowDuplicatesOnly(false);
                    setShowUnlinkedHousesOnly(false);
                    setShowNoPhotosOnly(false);
                    setBrowseView("accessories");
                    setTab("browse");
                  } else if (browseView === "accessories") {
                    setBrowseView("none");
                  } else {
                    // Clear all filters when opening full gallery
                    setQ("");
                    setHouseFilter("");
                    setAccessoryFilter("");
                    setCollectionFilter("");
                    setYearFrom("");
                    setYearTo("");
                    setShowDuplicatesOnly(false);
                    setShowUnlinkedHousesOnly(false);
                    setShowNoPhotosOnly(false);
                    setBrowseView("accessories");
                  }
                }}
                className={browseView === "accessories" 
                  ? "bg-green-700 text-white border-green-700" 
                  : "bg-green-600 text-white border-green-600 hover:bg-green-700"
                }
              >
                {tab === "manage"
                  ? `Accessories (${data.accessories.length})`
                  : browseView === "accessories" 
                    ? "Hide Accessories" 
                    : `Accessories (${data.accessories.length})`
                }
              </Button>
              <Button 
                onClick={() => {
                  if (tab === "manage") {
                    // In Manage tab, always navigate to Browse with both view
                    setQ("");
                    setHouseFilter("");
                    setAccessoryFilter("");
                    setCollectionFilter("");
                    setYearFrom("");
                    setYearTo("");
                    setShowDuplicatesOnly(false);
                    setShowUnlinkedHousesOnly(false);
                    setShowNoPhotosOnly(false);
                    setBrowseView("both");
                    setTab("browse");
                  } else if (browseView === "both") {
                    setBrowseView("none");
                  } else {
                    // Clear all filters when opening full gallery
                    setQ("");
                    setHouseFilter("");
                    setAccessoryFilter("");
                    setCollectionFilter("");
                    setYearFrom("");
                    setYearTo("");
                    setShowDuplicatesOnly(false);
                    setShowUnlinkedHousesOnly(false);
                    setShowNoPhotosOnly(false);
                    setBrowseView("both");
                  }
                }}
                className={browseView === "both" 
                  ? "bg-gray-700 text-white border-gray-700" 
                  : "bg-gray-600 text-white border-gray-600 hover:bg-gray-700"
                }
              >
                {tab === "manage"
                  ? "All"
                  : browseView === "both" 
                    ? "Hide All" 
                    : "All"
                }
              </Button>
              {isAdmin && tab === "manage" && (
                <>
                  <Button 
                    onClick={toggleDuplicateFilter}
                    className={showDuplicatesOnly 
                      ? "bg-orange-700 text-white border-orange-700" 
                      : "bg-orange-600 text-white border-orange-600 hover:bg-orange-700"
                    }
                    title={showDuplicatesOnly ? "Show all items" : "Show only duplicates"}
                  >
                    {showDuplicatesOnly ? "Show All" : "Show Duplicates"}
                  </Button>
                  <Button 
                    onClick={toggleUnlinkedHousesFilter}
                    className={showUnlinkedHousesOnly 
                      ? "bg-blue-700 text-white border-blue-700" 
                      : "bg-blue-600 text-white border-blue-600 hover:bg-blue-700"
                    }
                    title={showUnlinkedHousesOnly ? "Show all houses" : "Show only houses without linked accessories"}
                  >
                    {showUnlinkedHousesOnly ? "Show All" : "Unlinked Houses"}
                  </Button>
                  <Button 
                    onClick={toggleNoPhotosFilter}
                    className={showNoPhotosOnly 
                      ? "bg-purple-700 text-white border-purple-700" 
                      : "bg-purple-600 text-white border-purple-600 hover:bg-purple-700"
                    }
                    title={showNoPhotosOnly ? "Show all items" : "Show only items without photos"}
                  >
                    {showNoPhotosOnly ? "Show All" : "No Photos"}
                  </Button>
                </>
              )}
            </div>

            {/* Second row: Search and Filter fields */}
            <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-end pt-2 border-t">
              <div className="sm:col-span-3">
                <Field label="Search">
                  <TextInput
                    value={q}
                    onChange={(e) => {
                      setQ(e.target.value);
                      if (e.target.value && browseView === "none") {
                        setBrowseView("both");
                      }
                      if (e.target.value && tab === "manage") {
                        setTab("browse");
                      }
                    }}
                    placeholder="Search items..."
                  />
                </Field>
              </div>
              <div className="sm:col-span-2">
                <Field label="House">
                  <Select value={houseFilter} onChange={(e) => {
                    setHouseFilter(e.target.value);
                    if (e.target.value) {
                      setAccessoryFilter("");
                    }
                    if (e.target.value && browseView === "none") {
                      setBrowseView("both");
                    }
                    if (e.target.value && tab === "manage") {
                      setTab("browse");
                    }
                  }}>
                    <option value="">All</option>
                    {data.houses
                      .slice()
                      .sort((a, b) => a.name.localeCompare(b.name))
                      .map((h) => (
                        <option key={h.id} value={h.id}>
                          {h.name}
                        </option>
                      ))}
                  </Select>
                </Field>
              </div>
              <div className="sm:col-span-2">
                <Field label="Accessory">
                  <Select
                    value={accessoryFilter}
                    onChange={(e) => {
                      setAccessoryFilter(e.target.value);
                      if (e.target.value) {
                        setHouseFilter("");
                      }
                      if (e.target.value && browseView === "none") {
                        setBrowseView("both");
                      }
                      if (e.target.value && tab === "manage") {
                        setTab("browse");
                      }
                    }}
                  >
                    <option value="">All</option>
                    {data.accessories
                      .slice()
                      .sort((a, b) => a.name.localeCompare(b.name))
                      .map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.name}
                        </option>
                      ))}
                  </Select>
                </Field>
              </div>
              <div className="sm:col-span-2">
                <Field label="Collection">
                  <Select value={collectionFilter} onChange={(e) => {
                    setCollectionFilter(e.target.value);
                    if (e.target.value && browseView === "none") {
                      setBrowseView("both");
                    }
                    if (e.target.value && tab === "manage") {
                      setTab("browse");
                    }
                  }}>
                    <option value="">All</option>
                    {data.collections
                      .slice()
                      .sort((a, b) => a.name.localeCompare(b.name))
                      .map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                        </option>
                      ))}
                  </Select>
                </Field>
              </div>
              <div className="sm:col-span-1">
                <Field label="From">
                  <TextInput
                    type="number"
                    value={yearFrom}
                    onChange={(e) => {
                      setYearFrom(e.target.value);
                      if (e.target.value && browseView === "none") {
                        setBrowseView("both");
                      }
                      if (e.target.value && tab === "manage") {
                        setTab("browse");
                      }
                    }}
                    placeholder="2015"
                  />
                </Field>
              </div>
              <div className="sm:col-span-1">
                <Field label="To">
                  <TextInput
                    type="number"
                    value={yearTo}
                    onChange={(e) => {
                      setYearTo(e.target.value);
                      if (e.target.value && browseView === "none") {
                        setBrowseView("both");
                      }
                      if (e.target.value && tab === "manage") {
                        setTab("browse");
                      }
                    }}
                    placeholder="2020"
                  />
                </Field>
              </div>
              <div className="sm:col-span-1 pb-[2px]">
                <Button
                  onClick={() => {
                    setQ("");
                    setHouseFilter("");
                    setAccessoryFilter("");
                    setCollectionFilter("");
                    setYearFrom("");
                    setYearTo("");
                    setShowDuplicatesOnly(false);
                    setShowUnlinkedHousesOnly(false);
                    setShowNoPhotosOnly(false);
                  }}
                  className="w-full"
                >
                  Clear
                </Button>
              </div>
            </div>
            </div>
          )}
        </Card>

        {tab === "browse" ? (
          (() => {
            // Detect if any filters are active (not just browse view)
            const hasActiveFilters = q.trim() !== "" || houseFilter !== "" || accessoryFilter !== "" || 
                                     collectionFilter !== "" || yearFrom !== "" || yearTo !== "" ||
                                     showDuplicatesOnly || showUnlinkedHousesOnly || showNoPhotosOnly;
            
            // Use side-by-side layout when filters are active
            if (hasActiveFilters && browseView === "both") {
              return (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Houses Section - Left Side */}
                  <section className="space-y-3">
                    <SectionTitle>
                      Houses ({filteredHouses.length})
                    </SectionTitle>
                    {filteredHouses.length === 0 ? (
                      <Card className="p-6 text-sm text-gray-500">
                        No houses match your filters.
                      </Card>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {filteredHouses.map((h) => (
                          <HouseCard key={h.id} h={h} />
                        ))}
                      </div>
                    )}
                  </section>

                  {/* Accessories Section - Right Side */}
                  <section ref={accessoriesSectionRef} className="space-y-3">
                    <SectionTitle>
                      Accessories ({filteredAccessories.length})
                    </SectionTitle>
                    {filteredAccessories.length === 0 ? (
                      <Card className="p-6 text-sm text-gray-500">
                        No accessories match your filters.
                      </Card>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {filteredAccessories.map((a) => (
                          <AccessoryCard key={a.id} a={a} />
                        ))}
                      </div>
                    )}
                  </section>
                </div>
              );
            }
            
            // Use vertical stacking for browse buttons (no filters)
            return (
              <div className="grid grid-cols-1 gap-6">
                {/* Houses Section */}
                {(browseView === "houses" || browseView === "both") && (
                  <section className="space-y-3">
                    <SectionTitle>
                      Houses ({filteredHouses.length})
                    </SectionTitle>
                    {filteredHouses.length === 0 ? (
                      <Card className="p-6 text-sm text-gray-500">
                        No houses match your filters.
                      </Card>
                    ) : (
                      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                        {filteredHouses.map((h) => (
                          <HouseCard key={h.id} h={h} />
                        ))}
                      </div>
                    )}
                  </section>
                )}

                {/* Accessories Section */}
                {(browseView === "accessories" || browseView === "both") && (
                  <section ref={accessoriesSectionRef} className="space-y-3">
                    <SectionTitle>
                      Accessories ({filteredAccessories.length})
                    </SectionTitle>
                    {filteredAccessories.length === 0 ? (
                      <Card className="p-6 text-sm text-gray-500">
                        No accessories match your filters.
                      </Card>
                    ) : (
                      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                        {filteredAccessories.map((a) => (
                          <AccessoryCard key={a.id} a={a} />
                        ))}
                      </div>
                    )}
                  </section>
                )}
              </div>
            );
          })()
        ) : !isAdmin ? (
          <Card className="p-8 text-center">
            <div className="space-y-4">
              <div className="text-6xl">🔒</div>
              <div className="text-xl font-semibold text-gray-900">Admin Access Required</div>
              <div className="text-gray-600">
                Please sign in with an authorized account to access the management features.
              </div>
              {!user && (
                <Button
                  onClick={async () => {
                    try {
                      const { error } = await supabase.auth.signInWithOAuth({
                        provider: 'google',
                        options: {
                          redirectTo: window.location.origin,
                        }
                      });
                      if (error) {
                        console.error('OAuth error:', error);
                        if (error.message.includes('not enabled') || error.message.includes('Unsupported provider')) {
                          alert('Google sign-in is not yet configured. Please follow the setup guide in GOOGLE_AUTH_SETUP.md to enable Google OAuth in your Supabase project.');
                        } else {
                          alert(`Sign in error: ${error.message}`);
                        }
                      }
                    } catch (err) {
                      console.error('Sign in error:', err);
                      alert('Unable to sign in. Please check the setup guide in GOOGLE_AUTH_SETUP.md');
                    }
                  }}
                  className="bg-blue-600 text-white border-blue-600 hover:bg-blue-700"
                >
                  <svg className="w-4 h-4 mr-2 inline-block" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                  </svg>
                  Sign in with Google
                </Button>
              )}
            </div>
          </Card>
        ) : null}
          </>
        ) : tab === "manage" ? (
          <>
            {/* Management Header with Logout */}
            <Card className="p-4">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Management Dashboard</h2>
                  <p className="text-sm text-gray-600">Manage your Department 56 collection</p>
                </div>
                <Button
                  onClick={async () => {
                    await supabase.auth.signOut();
                    setTab("browse"); // Return to browse on logout
                  }}
                  className="bg-gray-200 text-gray-700 border-gray-300 hover:bg-gray-300"
                >
                  Logout
                </Button>
              </div>
              
              {/* Management Function Buttons */}
              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={() => setManageView("edit")}
                  className={manageView === "edit" 
                    ? "bg-blue-600 text-white border-blue-600" 
                    : "bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200"
                  }
                >
                  📝 Edit Items
                </Button>
                <Button
                  onClick={() => setManageView("dataReview")}
                  className={manageView === "dataReview" 
                    ? "bg-green-600 text-white border-green-600" 
                    : "bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200"
                  }
                >
                  🔍 Data Review
                </Button>
                <Button
                  onClick={() => setManageView("import")}
                  className={manageView === "import" 
                    ? "bg-purple-600 text-white border-purple-600" 
                    : "bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200"
                  }
                >
                  📥 Import Houses
                </Button>
              </div>
            </Card>

            {/* Conditional Content Based on Selected View */}
            {manageView === "edit" && (
              <Card className="p-4">
                <SectionTitle>Edit Items</SectionTitle>
                <div className="pt-4">
                  {/* All the existing manage tab content starts here */}
                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    {/* Left column: House editing */}
                    <div className="space-y-6">
                      <Card className="p-4">
                        <SectionTitle>Edit / Add House</SectionTitle>
                        <div className="pt-3 space-y-3">
                          <Field label="Load Existing House to Edit (optional)">
                            <Select 
                              value={editHouseId}
                              onChange={(e) => setEditHouseId(e.target.value)}
                            >
                              <option value="">-- Create New House --</option>
                              {filteredHouses
                                .map((h) => (
                                  <option key={h.id} value={h.id}>
                                    {h.name} {h.year ? `(${h.year})` : ''}
                                  </option>
                                ))}
                            </Select>
                          </Field>
                          <HouseForm 
                            data={data} 
                            onSave={addHouse}
                            onDelete={deleteHouse}
                            onMoveToAccessory={moveHouseToAccessory}
                            initial={editHouseId ? (() => {
                              const house = data.houses.find(h => h.id === editHouseId);
                              if (!house) return undefined;
                              const collectionIds = data.houseCollections
                                .filter(hc => hc.house_id === house.id)
                                .map(hc => hc.collection_id);
                              const tagIds = data.houseTags
                                .filter(ht => ht.house_id === house.id)
                                .map(ht => ht.tag_id);
                              return { ...house, collectionIds, tagIds };
                            })() : undefined}
                          />
                        </div>
                      </Card>

                      {/* Linked accessories display for selected house */}
                      {(() => {
                        if (!editHouseId) return null;
                        
                        const linkedAccessories = data.houseAccessoryLinks
                          .filter(link => link.house_id === editHouseId)
                          .map(link => data.accessories.find(a => a.id === link.accessory_id))
                          .filter(Boolean) as Accessory[];
                        
                        if (linkedAccessories.length === 0) {
                          return (
                            <Card className="p-4">
                              <h3 className="text-sm font-semibold text-gray-900 mb-3">Linked Accessories</h3>
                              <p className="text-sm text-gray-500">No accessories linked to this house yet.</p>
                            </Card>
                          );
                        }
                        
                        return (
                          <Card className="p-4">
                            <h3 className="text-sm font-semibold text-gray-900 mb-3">
                              Linked Accessories ({linkedAccessories.length})
                            </h3>
                            <div className="space-y-3">
                              {linkedAccessories.map((accessory) => (
                                <div 
                                  key={accessory.id} 
                                  className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-indigo-300 transition"
                                >
                                  <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                      {accessory.photo_url && (
                                        <img 
                                          src={accessory.photo_url} 
                                          alt={accessory.name}
                                          className="w-10 h-10 object-cover rounded"
                                        />
                                      )}
                                      <span className="font-medium text-gray-900">{accessory.name}</span>
                                    </div>
                                    <Button
                                      onClick={() => {
                                        setEditAccessoryId(accessory.id);
                                        // Scroll to the accessory form after a brief delay
                                        setTimeout(() => {
                                          accessoryFormRef.current?.scrollIntoView({ 
                                            behavior: 'smooth', 
                                            block: 'start' 
                                          });
                                        }, 100);
                                      }}
                                      className="text-xs px-2 py-1"
                                    >
                                      Edit
                                    </Button>
                                  </div>
                                  {accessory.notes && (
                                    <div className="text-xs text-gray-600">
                                      <p>{accessory.notes}</p>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </Card>
                        );
                      })()}

                      {/* Accessory form - always visible */}
                      <div ref={accessoryFormRef}>
                        <Card className="p-4">
                          <SectionTitle>Edit / Add Accessory</SectionTitle>
                          <div className="pt-3 space-y-3">
                            <Field label="Load Existing Accessory to Edit (optional)">
                              <Select 
                                value={editAccessoryId}
                                onChange={(e) => setEditAccessoryId(e.target.value)}
                              >
                                <option value="">-- Create New Accessory --</option>
                                {filteredAccessories
                                  .map((a) => (
                                    <option key={a.id} value={a.id}>
                                      {a.name}
                                    </option>
                                  ))}
                              </Select>
                            </Field>
                            <AccessoryForm 
                              data={data} 
                              onSave={addAccessory}
                              onDelete={deleteAccessory}
                              onMoveToHouse={moveAccessoryToHouse}
                              onLink={addLink}
                              initial={editAccessoryId ? (() => {
                                const accessory = data.accessories.find(a => a.id === editAccessoryId);
                                if (!accessory) return undefined;
                                const collectionIds = data.accessoryCollections
                                  .filter(ac => ac.accessory_id === accessory.id)
                                  .map(ac => ac.collection_id);
                                const tagIds = data.accessoryTags
                                  .filter(at => at.accessory_id === accessory.id)
                                  .map(at => at.tag_id);
                                return { ...accessory, collectionIds, tagIds };
                              })() : undefined}
                            />
                          </div>
                        </Card>
                      </div>
                    </div>

                    {/* Right column: Management tools */}
                    <div className="space-y-6">
                      {/* Special filters */}
                      <Card className="p-4">
                        <SectionTitle>Special Views</SectionTitle>
                        <div className="pt-3 space-y-3">
                          <Button 
                            onClick={() => {
                              toggleDuplicateFilter();
                              // Switch to browse tab to show the filtered results
                              setTab("browse");
                            }}
                            className={`w-full justify-start ${showDuplicatesOnly ? 'bg-orange-600 text-white' : 'bg-gray-100 text-gray-700'}`}
                          >
                            🔍 {showDuplicatesOnly ? "Hide" : "Show"} Duplicates ({duplicateItemIds.houseIds.size + duplicateItemIds.accessoryIds.size})
                          </Button>
                          <Button 
                            onClick={() => {
                              toggleUnlinkedHousesFilter();
                              // Switch to browse tab to show the filtered results
                              setTab("browse");
                            }}
                            className={`w-full justify-start ${showUnlinkedHousesOnly ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}
                          >
                            🏠 {showUnlinkedHousesOnly ? "Hide" : "Show"} Unlinked Houses ({data.houses.filter(h => data.houseAccessoryLinks.filter(l => l.house_id === h.id).length === 0).length})
                          </Button>
                          <Button 
                            onClick={() => {
                              toggleNoPhotosFilter();
                              // Switch to browse tab to show the filtered results
                              setTab("browse");
                            }}
                            className={`w-full justify-start ${showNoPhotosOnly ? 'bg-purple-600 text-white' : 'bg-gray-100 text-gray-700'}`}
                          >
                            📷 {showNoPhotosOnly ? "Hide" : "Show"} No Photos ({[...data.houses, ...data.accessories].filter(item => !item.photo_url).length})
                          </Button>
                        </div>
                      </Card>

                      {/* Link accessories to houses */}
                      <Card className="p-4">
                        <SectionTitle>Link Accessory to House</SectionTitle>
                        <div className="grid grid-cols-1 gap-3 pt-3">
                          <Field label="House">
                            <Select value={linkHouseId} onChange={(e) => setLinkHouseId(e.target.value)}>
                              <option value="">Select…</option>
                              {data.houses
                                .slice()
                                .sort((a, b) => a.name.localeCompare(b.name))
                                .map((h) => (
                                  <option key={h.id} value={h.id}>
                                    {h.name}
                                  </option>
                                ))}
                            </Select>
                          </Field>
                          <Field label="Accessory">
                            <Select value={linkAccId} onChange={(e) => setLinkAccId(e.target.value)}>
                              <option value="">Select…</option>
                              {data.accessories
                                .slice()
                                .sort((a, b) => a.name.localeCompare(b.name))
                                .map((a) => (
                                  <option key={a.id} value={a.id}>
                                    {a.name}
                                  </option>
                                ))}
                            </Select>
                          </Field>
                          <div className="flex gap-2">
                            <Button
                              onClick={() => addLink(linkHouseId, linkAccId)}
                              disabled={!canLink}
                              className={`bg-emerald-600 text-white border-emerald-600 hover:bg-emerald-700 ${
                                !canLink ? "opacity-60 cursor-not-allowed" : ""
                              }`}
                            >
                              Link
                            </Button>
                            <Button
                              onClick={() => {
                                setLinkAccId("");
                                setLinkHouseId("");
                              }}
                            >
                              Clear
                            </Button>
                          </div>
                        </div>
                      </Card>

                      {/* Collections and Tags */}
                      <Card className="p-4 space-y-4">
                        <SectionTitle>Collections</SectionTitle>
                        <AddOneLine label="Add collection" onAdd={addCollection} />
                        <div className="flex flex-wrap gap-2">
                          {data.collections
                            .slice()
                            .sort((a, b) => a.name.localeCompare(b.name))
                            .map((c) => (
                              <Pill key={c.id}>{c.name}</Pill>
                            ))}
                        </div>
                      </Card>

                      <Card className="p-4 space-y-4">
                        <SectionTitle>Tags</SectionTitle>
                        <AddOneLine label="Add tag" onAdd={addTag} />
                        <div className="flex flex-wrap gap-2">
                          {data.tags
                            .slice()
                            .sort((a, b) => a.name.localeCompare(b.name))
                            .map((t) => (
                              <Pill key={t.id}>#{t.name}</Pill>
                            ))}
                        </div>
                        <p className="text-xs text-gray-500">
                          Tip: Tags are synced to the cloud and can be used for ML-powered suggestions in
                          the future.
                        </p>
                      </Card>

                      {/* Data Tools */}
                      <Card className="p-4">
                        <SectionTitle>Data Tools</SectionTitle>
                        <div className="pt-3 flex flex-wrap gap-2">
                          <Button onClick={exportJSON}>Export JSON</Button>
                          <Button onClick={loadData}>Refresh Data</Button>
                        </div>
                        <p className="text-xs text-gray-500 pt-2">
                          Data is automatically synced to the cloud. Export for backup purposes.
                        </p>
                      </Card>
                    </div>
                  </div>
                </div>
              </Card>
            )}

            {/* Data Review Section */}
            {manageView === "dataReview" && (
              <Card className="p-4">
                <SectionTitle>Data Review</SectionTitle>
                <div className="pt-4">
                  <DataReviewTab />
                </div>
              </Card>
            )}

            {/* Import Section (Coming Soon) */}
            {manageView === "import" && (
              <Card className="p-4">
                <SectionTitle>Import Houses</SectionTitle>
                <div className="pt-4">
                  {importStep === "input" && (
                    <div className="space-y-4">
                      <div className="text-sm text-gray-600">
                        Enter house names below, one per line. The system will automatically search for details using the web scraper.
                      </div>
                      <Field label="House Names (one per line)">
                        <TextArea
                          value={importText}
                          onChange={(e) => setImportText(e.target.value)}
                          placeholder={`Enter house names like:
A Christmas Carol Reading by Dickens
Biltmore Estate
Christmas at the Park`}
                          rows={8}
                          className="font-mono text-sm"
                        />
                      </Field>
                      <div className="flex gap-3">
                        <Button
                          onClick={handleImportHouses}
                          disabled={importLoading || !importText.trim()}
                          className="bg-purple-600 text-white border-purple-600 hover:bg-purple-700 disabled:bg-gray-300"
                        >
                          {importLoading ? "🔄 Searching..." : "🔍 Search & Import"}
                        </Button>
                        <Button
                          onClick={() => setImportText("")}
                          className="bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200"
                        >
                          Clear
                        </Button>
                      </div>
                      {importText.trim() && (
                        <div className="text-xs text-gray-500">
                          {importText.split('\n').filter(line => line.trim().length > 0).length} house(s) to process
                        </div>
                      )}
                    </div>
                  )}

                  {importStep === "results" && importResults && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold text-gray-900">Import Results</h3>
                          <div className="text-sm text-gray-600">
                            Found {importResults.filter(r => r.status === 'found').length} of {importResults.length} houses
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            onClick={resetImport}
                            className="bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200"
                          >
                            Start Over
                          </Button>
                          <Button
                            onClick={() => setImportStep("review")}
                            className="bg-green-600 text-white border-green-600 hover:bg-green-700"
                          >
                            Review & Approve
                          </Button>
                        </div>
                      </div>

                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {importResults.map((result, index) => (
                          <Card key={index} className="p-3">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="font-medium text-gray-900">{result.input_name}</div>
                                {result.status === 'found' && result.scraped_data ? (
                                  <div className="mt-2 space-y-3">
                                    {/* Images section */}
                                    {result.scraped_data.images && result.scraped_data.images.length > 0 && (
                                      <div>
                                        <div className="text-sm font-medium text-gray-700 mb-2">
                                          Images ({result.scraped_data.images.length})
                                        </div>
                                        <div className="flex gap-2 flex-wrap">
                                          {result.scraped_data.images.map((imageUrl: string, imgIndex: number) => (
                                            <img
                                              key={imgIndex}
                                              src={imageUrl}
                                              alt={`${result.scraped_data!.name} - Image ${imgIndex + 1}`}
                                              className="w-20 h-20 object-cover rounded border border-gray-300 hover:border-blue-500 cursor-pointer transition-colors"
                                              onClick={() => window.open(imageUrl, '_blank')}
                                              onError={(e) => {
                                                const target = e.target as HTMLImageElement;
                                                target.style.display = 'none';
                                              }}
                                            />
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                    
                                    {/* Details section */}
                                    <div className="text-sm space-y-1">
                                      <div><span className="font-medium">Found:</span> {result.scraped_data.name}</div>
                                      {result.scraped_data.intro_year && (
                                        <div><span className="font-medium">Introduced:</span> {result.scraped_data.intro_year}</div>
                                      )}
                                      {result.scraped_data.retired_year && (
                                        <div><span className="font-medium">Retired:</span> {result.scraped_data.retired_year}</div>
                                      )}
                                      {result.scraped_data.sku && (
                                        <div><span className="font-medium">SKU:</span> {result.scraped_data.sku}</div>
                                      )}
                                      <div><span className="font-medium">Collection:</span> {result.scraped_data.collection}</div>
                                      {result.scraped_data.srp && (
                                        <div><span className="font-medium">Price:</span> ${result.scraped_data.srp}</div>
                                      )}
                                      <div className="text-gray-600">{result.scraped_data.description}</div>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="mt-1 text-sm text-red-600">No match found</div>
                                )}
                              </div>
                              <div className="ml-4 text-right">
                                <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                  result.status === 'found' 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-red-100 text-red-800'
                                }`}>
                                  {result.status === 'found' 
                                    ? `✓ ${Math.round(result.confidence * 100)}%` 
                                    : '✗ Not Found'
                                  }
                                </div>
                              </div>
                            </div>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}

                  {importStep === "review" && importResults && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold text-gray-900">Review & Approve</h3>
                          <div className="text-sm text-gray-600">
                            Select houses to add to your collection ({selectedForApproval.size} selected)
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            onClick={() => setImportStep("results")}
                            className="bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200"
                          >
                            ← Back to Results
                          </Button>
                          <Button
                            onClick={approveSelectedItems}
                            disabled={selectedForApproval.size === 0 || approvalInProgress}
                            className="bg-green-600 text-white border-green-600 hover:bg-green-700 disabled:bg-gray-300"
                          >
                            {approvalInProgress ? "Adding..." : `Add ${selectedForApproval.size} Houses`}
                          </Button>
                        </div>
                      </div>

                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {importResults
                          .filter(result => result.status === 'found')
                          .map((result) => {
                            const actualIndex = importResults.findIndex(r => r === result);
                            const isSelected = selectedForApproval.has(actualIndex);
                            
                            return (
                              <Card key={actualIndex} className={`p-4 cursor-pointer transition-all ${
                                isSelected ? 'ring-2 ring-green-500 bg-green-50' : 'hover:bg-gray-50'
                              }`}>
                                <div 
                                  className="flex items-start gap-4"
                                  onClick={() => toggleItemSelection(actualIndex)}
                                >
                                  <div className="flex-shrink-0 pt-1">
                                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                                      isSelected 
                                        ? 'bg-green-600 border-green-600' 
                                        : 'border-gray-300'
                                    }`}>
                                      {isSelected && (
                                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                        </svg>
                                      )}
                                    </div>
                                  </div>
                                  
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-start justify-between">
                                      <div className="flex-1">
                                        <div className="font-medium text-gray-900">
                                          {result.scraped_data?.name || result.input_name}
                                        </div>
                                        <div className="text-sm text-gray-500 mt-1">
                                          Original search: {result.input_name}
                                        </div>
                                        {result.scraped_data && (
                                          <div className="mt-2 space-y-2">
                                            {/* Image preview */}
                                            {result.scraped_data.images && result.scraped_data.images.length > 0 && (
                                              <div>
                                                <div className="text-xs font-medium text-gray-600 mb-1">
                                                  Primary Image {result.scraped_data.images.length > 1 && `(${result.scraped_data.images.length} total available)`}
                                                </div>
                                                <img
                                                  src={result.scraped_data.images[0]}
                                                  alt={result.scraped_data.name}
                                                  className="w-16 h-16 object-cover rounded border border-gray-300"
                                                  onError={(e) => {
                                                    const target = e.target as HTMLImageElement;
                                                    target.style.display = 'none';
                                                  }}
                                                />
                                                {result.scraped_data.images.length > 1 && (
                                                  <div className="text-xs text-blue-600 mt-1">
                                                    + {result.scraped_data.images.length - 1} more image{result.scraped_data.images.length > 2 ? 's' : ''} available
                                                  </div>
                                                )}
                                              </div>
                                            )}
                                            
                                            {/* Details */}
                                            <div className="text-sm space-y-1">
                                              {result.scraped_data.intro_year && (
                                                <div><span className="font-medium">Introduced:</span> {result.scraped_data.intro_year}</div>
                                              )}
                                              {result.scraped_data.retired_year && (
                                                <div><span className="font-medium">Retired:</span> {result.scraped_data.retired_year}</div>
                                              )}
                                              {result.scraped_data.collection && (
                                                <div><span className="font-medium">Collection:</span> {result.scraped_data.collection}</div>
                                              )}
                                              {result.scraped_data.sku && (
                                                <div><span className="font-medium">SKU:</span> {result.scraped_data.sku}</div>
                                              )}
                                              {result.scraped_data.srp && (
                                                <div><span className="font-medium">Price:</span> ${result.scraped_data.srp}</div>
                                              )}
                                              {result.scraped_data.description && (
                                                <div className="text-gray-600 mt-1">{result.scraped_data.description}</div>
                                              )}
                                            </div>
                                            
                                            {/* Purchase Year Input */}
                                            <div className="mt-3 pt-3 border-t border-gray-200">
                                              <label className="block text-xs font-medium text-gray-700 mb-1">
                                                Purchase Year (Optional)
                                              </label>
                                              <input
                                                type="number"
                                                min="1990"
                                                max={new Date().getFullYear()}
                                                placeholder="e.g., 2023"
                                                value={purchaseYears[actualIndex] || ''}
                                                onChange={(e) => {
                                                  const year = e.target.value ? parseInt(e.target.value) : undefined;
                                                  setPurchaseYears(prev => ({
                                                    ...prev,
                                                    [actualIndex]: year
                                                  }));
                                                }}
                                                className="w-24 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                onClick={(e) => e.stopPropagation()} // Prevent toggle when clicking input
                                              />
                                            </div>
                                          </div>
                                        )}
                                      </div>
                                      
                                      <div className="ml-4 text-right flex-shrink-0">
                                        <div className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                          ✓ {Math.round(result.confidence * 100)}%
                                        </div>
                                        {result.source && (
                                          <div className="text-xs text-gray-500 mt-1">
                                            from {result.source}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </Card>
                            );
                          })}
                      </div>

                      {importResults.filter(r => r.status === 'found').length === 0 && (
                        <div className="text-center py-8 text-gray-500">
                          <div className="text-2xl mb-2">�</div>
                          <div>No houses found to review. Try different search terms.</div>
                        </div>
                      )}

                      <div className="flex items-center justify-between pt-4 border-t">
                        <div className="text-sm text-gray-600">
                          {importResults.filter(r => r.status === 'found').length} house(s) available for import
                        </div>
                        <div className="flex gap-2">
                          <Button
                            onClick={() => {
                              const foundIndices = new Set(
                                importResults
                                  .map((result, index) => result.status === 'found' ? index : -1)
                                  .filter(index => index !== -1)
                              );
                              setSelectedForApproval(foundIndices);
                            }}
                            className="bg-blue-100 text-blue-700 border-blue-300 hover:bg-blue-200"
                          >
                            Select All
                          </Button>
                          <Button
                            onClick={() => setSelectedForApproval(new Set())}
                            className="bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200"
                          >
                            Clear Selection
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            )}
            
            {/* Filter Card for Manage Tab */}
            <Card className="sticky top-[73px] z-30 bg-white shadow-md">
              {/* Collapse Toggle Bar */}
              <div 
                className="flex items-center justify-between p-3 sm:p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => setFiltersCollapsed(!filtersCollapsed)}
              >
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-700">
                    {filtersCollapsed ? "Show Filters & Navigation" : "Hide Filters & Navigation"}
                  </span>
                  {filtersCollapsed && (
                    <span className="text-sm text-gray-500">
                      ({browseView === "houses" ? "Houses" : browseView === "accessories" ? "Accessories" : browseView === "both" ? "Both" : "None"})
                    </span>
                  )}
                </div>
                <svg 
                  className={`w-5 h-5 text-gray-600 transition-transform ${filtersCollapsed ? '' : 'rotate-180'}`}
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>

              {/* Collapsible Content */}
              {!filtersCollapsed && (
                <div className="border-t">
                  <div className="p-3 sm:p-4 space-y-4">
                    {/* Browse View Selector */}
                    <div className="flex gap-2 justify-center">
                      <Button
                        onClick={() => setBrowseView("houses")}
                        className={browseView === "houses" 
                          ? "bg-blue-600 text-white border-blue-600" 
                          : "bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200"
                        }
                      >
                        🏠 Houses
                      </Button>
                      <Button
                        onClick={() => setBrowseView("accessories")}
                        className={browseView === "accessories" 
                          ? "bg-green-600 text-white border-green-600" 
                          : "bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200"
                        }
                      >
                        🎄 Accessories
                      </Button>
                      <Button
                        onClick={() => setBrowseView("both")}
                        className={browseView === "both" 
                          ? "bg-purple-600 text-white border-purple-600" 
                          : "bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200"
                        }
                      >
                        📋 All
                      </Button>
                    </div>

                    {/* Search and Filters */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div className="sm:col-span-3">
                        <Field label="Search">
                          <TextInput
                            value={q}
                            onChange={(e) => setQ(e.target.value)}
                            placeholder="Search by name or description..."
                          />
                        </Field>
                      </div>
                      
                      {tab === "manage"
                        ? isAdmin && (
                          <div className="sm:col-span-3 space-y-3">
                            {/* Admin quick filters for management */}
                            <div className="flex flex-wrap gap-2">
                              <Button
                                onClick={toggleDuplicateFilter}
                                className={showDuplicatesOnly 
                                  ? "bg-orange-600 text-white border-orange-600" 
                                  : "bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200"
                                }
                              >
                                🔍 Show Duplicates ({duplicateItemIds.houseIds.size + duplicateItemIds.accessoryIds.size})
                              </Button>
                              <Button
                                onClick={toggleUnlinkedHousesFilter}
                                className={showUnlinkedHousesOnly 
                                  ? "bg-blue-600 text-white border-blue-600" 
                                  : "bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200"
                                }
                              >
                                🔗 Unlinked Houses ({unlinkedHousesCount})
                              </Button>
                              <Button
                                onClick={toggleNoPhotosFilter}
                                className={showNoPhotosOnly 
                                  ? "bg-red-600 text-white border-red-600" 
                                  : "bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200"
                                }
                              >
                                📷 No Photos ({noPhotosCount})
                              </Button>
                            </div>
                          </div>
                        )
                        : (
                          <>
                            <Field label="Houses">
                              <TextInput
                                value={houseFilter}
                                onChange={(e) => {
                                  setHouseFilter(e.target.value);
                                  if (e.target.value && tab === "manage") {
                                    setTab("browse");
                                  }
                                }}
                                placeholder="Filter houses..."
                              />
                            </Field>
                            <Field label="Accessories">
                              <TextInput
                                value={accessoryFilter}
                                onChange={(e) => {
                                  setAccessoryFilter(e.target.value);
                                  if (e.target.value && tab === "manage") {
                                    setTab("browse");
                                  }
                                }}
                                placeholder="Filter accessories..."
                              />
                            </Field>
                            <Field label="Collection">
                              <Select
                                value={collectionFilter}
                                onChange={(e) => {
                                  setCollectionFilter(e.target.value);
                                  if (e.target.value && tab === "manage") {
                                    setTab("browse");
                                  }
                                }}
                              >
                                <option value="">All Collections</option>
                                {data.collections.map((c) => (
                                  <option key={c.id} value={c.id}>
                                    {c.name}
                                  </option>
                                ))}
                              </Select>
                            </Field>
                            <Field label="Year From">
                              <TextInput
                                value={yearFrom}
                                onChange={(e) => {
                                  setYearFrom(e.target.value);
                                  if (e.target.value && tab === "manage") {
                                    setTab("browse");
                                  }
                                }}
                                placeholder="1995"
                              />
                            </Field>
                            <Field label="Year To">
                              <TextInput
                                value={yearTo}
                                onChange={(e) => {
                                  setYearTo(e.target.value);
                                  if (e.target.value && tab === "manage") {
                                    setTab("browse");
                                  }
                                }}
                                placeholder="2020"
                              />
                            </Field>
                            <div className="sm:col-span-1 pb-[2px]">
                              <Button
                                onClick={() => {
                                  setQ("");
                                  setHouseFilter("");
                                  setAccessoryFilter("");
                                  setCollectionFilter("");
                                  setYearFrom("");
                                  setYearTo("");
                                  setShowDuplicatesOnly(false);
                                  setShowUnlinkedHousesOnly(false);
                                  setShowNoPhotosOnly(false);
                                }}
                                className="w-full"
                              >
                                Clear
                              </Button>
                            </div>
                          </>
                        )
                      }
                    </div>
                  </div>
                </div>
              )}
            </Card>
          </>
        ) : (
          // This is the Browse tab content
          <div className="space-y-6">
            {/* Check if any special filter is active to show gallery view */}
            {(showDuplicatesOnly || showUnlinkedHousesOnly || showNoPhotosOnly) ? (
              <>
                {/* Duplicate Detection Banner */}
                {showDuplicatesOnly && (
                  <Card className="p-4 bg-orange-50 border-orange-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-orange-900">Showing Duplicates Only</div>
                        <div className="text-sm text-orange-700">
                          Found {duplicateItemIds.houseIds.size} duplicate house(s) and {duplicateItemIds.accessoryIds.size} duplicate accessory(ies).
                          Click on items below to view and delete unwanted copies.
                        </div>
                      </div>
                      <Button 
                        onClick={toggleDuplicateFilter}
                        className="bg-orange-600 text-white border-orange-600 hover:bg-orange-700"
                      >
                        Clear Filter
                      </Button>
                    </div>
                  </Card>
                )}

                {/* Unlinked Houses Banner */}
                {showUnlinkedHousesOnly && (
                  <Card className="p-4 bg-blue-50 border-blue-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-blue-900">Showing Unlinked Houses Only</div>
                        <div className="text-sm text-blue-700">
                          Found {filteredHouses.length} house(s) without linked accessories.
                          Click on items below to view and link accessories.
                        </div>
                      </div>
                      <Button 
                        onClick={toggleUnlinkedHousesFilter}
                        className="bg-blue-600 text-white border-blue-600 hover:bg-blue-700"
                      >
                        Clear Filter
                      </Button>
                    </div>
                  </Card>
                )}

                {/* No Photos Banner */}
                {showNoPhotosOnly && (
                  <Card className="p-4 bg-purple-50 border-purple-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-purple-900">Showing Items Without Photos</div>
                        <div className="text-sm text-purple-700">
                          Found {filteredHouses.filter(h => !h.photo_url).length} house(s) and {filteredAccessories.filter(a => !a.photo_url).length} accessory(ies) without photos.
                          Click on items below to add photos.
                        </div>
                      </div>
                      <Button 
                        onClick={toggleNoPhotosFilter}
                        className="bg-purple-600 text-white border-purple-600 hover:bg-purple-700"
                      >
                        Clear Filter
                      </Button>
                    </div>
                  </Card>
                )}

                {/* Gallery View for Filtered Items */}
                {showUnlinkedHousesOnly ? (
                  // For unlinked houses, only show houses (no accessories since they're unlinked by definition)
                  <section className="space-y-3">
                    <SectionTitle>
                      Houses ({filteredHouses.length})
                    </SectionTitle>
                    {filteredHouses.length === 0 ? (
                      <Card className="p-6 text-sm text-gray-500">
                        No houses match this filter.
                      </Card>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {filteredHouses.map((house) => (
                          <HouseCard
                            key={house.id}
                            h={house}
                          />
                        ))}
                      </div>
                    )}
                  </section>
                ) : (
                  // For other filters, show both houses and accessories side-by-side
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Houses Section */}
                    <section className="space-y-3">
                      <SectionTitle>
                        Houses ({filteredHouses.length})
                      </SectionTitle>
                      {filteredHouses.length === 0 ? (
                        <Card className="p-6 text-sm text-gray-500">
                          No houses match this filter.
                        </Card>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {filteredHouses.map((house) => (
                            <HouseCard
                              key={house.id}
                              h={house}
                            />
                          ))}
                        </div>
                      )}
                    </section>

                    {/* Accessories Section */}
                    <section className="space-y-3">
                      <SectionTitle>
                        Accessories ({filteredAccessories.length})
                      </SectionTitle>
                      {filteredAccessories.length === 0 ? (
                        <Card className="p-6 text-sm text-gray-500">
                          No accessories match this filter.
                        </Card>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {filteredAccessories.map((accessory) => (
                            <AccessoryCard
                              key={accessory.id}
                              a={accessory}
                            />
                          ))}
                        </div>
                      )}
                    </section>
                  </div>
                )}
              </>
            ) : (
              // Normal browse content would go here
              // For now, we'll show a message that filtering/browse functionality
              // is accessed through the collapsible filters section above
              <Card className="p-6 text-center">
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-gray-900">Welcome to Department 56 Browser</h3>
                  <p className="text-gray-600">
                    Use the filters above to browse your houses and accessories, or switch to Manage to edit your collection.
                  </p>
                  <div className="text-sm text-gray-500">
                    <p>• Click "Browse" buttons above to view Houses, Accessories, or All items</p>
                    <p>• Use search and filters to find specific items</p>
                    <p>• Sign in with Google to access management features</p>
                  </div>
                </div>
              </Card>
            )}
          </div>
        )}
      </main>

      <footer className="py-6 text-center text-xs text-gray-500">
        © {new Date().getFullYear()} Dept56 Browser — Cloud Edition
      </footer>
      
      {/* Modals */}
      <ImageModal 
        open={imageModal.open} 
        onClose={imageModal.hide} 
        title={imageModal.data?.title} 
        src={imageModal.data?.src} 
      />
      <HouseDetailModal
        open={houseModal.open}
        onClose={houseModal.hide}
        house={houseModal.data}
        data={data}
        collById={collById}
        tagById={tagById}
        onAccessoryClick={(accessory) => {
          houseModal.hide();
          accessoryModal.show(accessory);
        }}
        onUnlink={unlink}
        onEdit={(houseId) => {
          setTab("manage");
          // Clear all filters to ensure the house can be found
          setQ("");
          setHouseFilter("");
          setAccessoryFilter("");
          setCollectionFilter("");
          setYearFrom("");
          setYearTo("");
          setShowDuplicatesOnly(false);
          setShowUnlinkedHousesOnly(false);
          setShowNoPhotosOnly(false);
          
          setEditHouseId(houseId);
          // Find and set the first linked accessory if one exists
          const linkedAccessory = data.houseAccessoryLinks.find((l) => l.house_id === houseId);
          if (linkedAccessory) {
            setEditAccessoryId(linkedAccessory.accessory_id);
          } else {
            setEditAccessoryId(""); // Clear accessory form if no link exists
          }
          houseModal.hide();
          setTimeout(() => {
            houseFormRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
          }, 100);
        }}
        isAdmin={isAdmin}
      />
      <AccessoryDetailModal
        open={accessoryModal.open}
        onClose={accessoryModal.hide}
        accessory={accessoryModal.data}
        data={data}
        collById={collById}
        tagById={tagById}
        onHouseClick={(house) => {
          accessoryModal.hide();
          houseModal.show(house);
        }}
        onEdit={(accessoryId) => {
          setTab("manage");
          // Clear all filters to ensure the accessory and linked house can be found
          setQ("");
          setHouseFilter("");
          setAccessoryFilter("");
          setCollectionFilter("");
          setYearFrom("");
          setYearTo("");
          setShowDuplicatesOnly(false);
          setShowUnlinkedHousesOnly(false);
          setShowNoPhotosOnly(false);
          
          setEditAccessoryId(accessoryId);
          // Find and set the linked house if one exists
          const linkedHouse = data.houseAccessoryLinks.find((l) => l.accessory_id === accessoryId);
          if (linkedHouse) {
            setEditHouseId(linkedHouse.house_id);
          } else {
            setEditHouseId(""); // Clear house form if no link exists
          }
          accessoryModal.hide();
          setTimeout(() => {
            accessoryFormRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
          }, 100);
        }}
        isAdmin={isAdmin}
      />
    </div>
  );
}

function AddOneLine({ label, onAdd }: { label: string; onAdd: (name: string) => void }) {
  const [v, setV] = useState("");
  return (
    <form
      className="flex gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        onAdd(v);
        setV("");
      }}
    >
      <TextInput value={v} onChange={(e) => setV(e.target.value)} placeholder={label} />
      <Button type="submit">Add</Button>
    </form>
  );
}
