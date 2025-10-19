import React, { useEffect, useMemo, useRef, useState } from "react";
import { supabase } from "./lib/supabase";
import * as db from "./lib/database";
import type { Database, House, Accessory, Collection, Tag, HouseAccessoryLink } from "./types/database";

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
 */

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
  const defaultClasses = "border-gray-200 bg-indigo-600 text-white hover:bg-indigo-700";
  
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
}) {
  const [selectedImage, setSelectedImage] = React.useState<{ url: string; name: string } | null>(null);

  // Initialize selected image to house photo when modal opens
  React.useEffect(() => {
    if (open && house?.photo_url) {
      setSelectedImage({ url: house.photo_url, name: house.name });
    }
  }, [open, house]);

  if (!open || !house || !data) return null;

  // Get unique accessories with photos only
  const accessoryMap = new Map<string, { linkId: string; a: Accessory }>();
  data.houseAccessoryLinks
    .filter((l) => l.house_id === house.id)
    .forEach((l) => {
      const accessory = data.accessories.find((x) => x.id === l.accessory_id);
      if (accessory && accessory.photo_url) {
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
              <Button 
                onClick={() => onEdit(house.id)}
                className="bg-indigo-600 text-white border-indigo-600 hover:bg-indigo-700"
              >
                Edit
              </Button>
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
                  )}
                </div>

                {/* Accessories Section */}
                {accessories.length > 0 && (
                  <div>
                    <h3 className="text-xs font-semibold text-gray-700 mb-2 uppercase">Accessories ({accessories.length})</h3>
                    <div className="space-y-2">
                      {accessories.map(({ linkId, a }) => (
                        <button
                          key={linkId}
                          onClick={() => onAccessoryClick(a)}
                          className="w-full border-2 rounded overflow-hidden hover:border-blue-500 transition-colors border-gray-300"
                        >
                          <img
                            src={a.photo_url!}
                            alt={a.name}
                            className="w-full h-20 object-contain bg-white"
                          />
                        </button>
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
}: {
  open: boolean;
  onClose: () => void;
  accessory: Accessory | null;
  data: Database | null;
  collById: Record<string, Collection>;
  tagById: Record<string, Tag>;
  onEdit: (accessoryId: string) => void;
  onHouseClick: (house: House) => void;
}) {
  const [selectedImage, setSelectedImage] = React.useState<{ url: string; name: string } | null>(null);

  // Initialize selected image to accessory photo when modal opens
  React.useEffect(() => {
    if (open && accessory?.photo_url) {
      setSelectedImage({ url: accessory.photo_url, name: accessory.name });
    }
  }, [open, accessory]);

  if (!open || !accessory || !data) return null;

  // Get linked houses with photos
  const houseMap = new Map<string, { linkId: string; h: House }>();
  data.houseAccessoryLinks
    .filter((l) => l.accessory_id === accessory.id)
    .forEach((l) => {
      const house = data.houses.find((x) => x.id === l.house_id);
      if (house && house.photo_url) {
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
              <Button 
                onClick={() => onEdit(accessory.id)}
                className="bg-indigo-600 text-white border-indigo-600 hover:bg-indigo-700"
              >
                Edit
              </Button>
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
                  )}
                </div>

                {/* Linked Houses Section */}
                {houses.length > 0 && (
                  <div>
                    <h3 className="text-xs font-semibold text-gray-700 mb-2 uppercase">Linked Houses ({houses.length})</h3>
                    <div className="space-y-2">
                      {houses.map(({ linkId, h }) => (
                        <button
                          key={linkId}
                          onClick={() => onHouseClick(h)}
                          className="w-full border-2 rounded overflow-hidden hover:border-blue-500 transition-colors border-gray-300"
                        >
                          <img
                            src={h.photo_url!}
                            alt={h.name}
                            className="w-full h-20 object-contain bg-white"
                          />
                        </button>
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
  initial,
}: {
  data: Database;
  onSave: (
    h: Omit<House, "id" | "user_id" | "created_at" | "updated_at">,
    collections: string[],
    tags: string[]
  ) => Promise<void>;
  onDelete?: (id: string, name: string) => Promise<void>;
  onMoveToAccessory?: (id: string, name: string) => Promise<void>;
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
  const [purchasedYear, setPurchasedYear] = useState<number | undefined>(initial?.purchased_year);
  const [collectionIds, setCollectionIds] = useState<string[]>(initial?.collectionIds || []);
  const [tagIds, setTagIds] = useState<string[]>(initial?.tagIds || []);
  const [saving, setSaving] = useState(false);

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
  }, [initial]);

  async function handleFile(file?: File) {
    if (file) {
      setPhotoFile(file);
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
          await onSave(h, collectionIds, tagIds);
        } catch (error) {
          console.error("Error saving house:", error);
          alert("Failed to save house. Please try again.");
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
            <img
              src={photoUrl}
              alt="preview"
              className="h-20 w-20 rounded-xl object-cover border border-gray-300 flex-shrink-0"
            />
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

      <div className="flex items-center gap-2 pt-2">
        <Button
          type="submit"
          disabled={saving}
          className="bg-indigo-600 text-white border-indigo-600 hover:bg-indigo-700"
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
            className="bg-red-600 text-white border-red-600 hover:bg-red-700"
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
  const [purchasedYear, setPurchasedYear] = useState<number | undefined>(initial?.purchased_year);
  const [collectionIds, setCollectionIds] = useState<string[]>(initial?.collectionIds || []);
  const [tagIds, setTagIds] = useState<string[]>(initial?.tagIds || []);
  const [saving, setSaving] = useState(false);

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
  }, [initial]);

  async function handleFile(file?: File) {
    if (file) {
      setPhotoFile(file);
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
          alert("Failed to save accessory. Please try again.");
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
            <img
              src={photoUrl}
              alt="preview"
              className="h-20 w-20 rounded-xl object-cover border border-gray-300 flex-shrink-0"
            />
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

      <div className="flex items-center gap-2 pt-2">
        <Button
          type="submit"
          disabled={saving}
          className="bg-indigo-600 text-white border-indigo-600 hover:bg-indigo-700"
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
            className="bg-red-600 text-white border-red-600 hover:bg-red-700"
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

  const [tab, setTab] = useState<"browse" | "manage">("browse");
  const [q, setQ] = useState("");
  const [houseFilter, setHouseFilter] = useState<string>("");
  const [accessoryFilter, setAccessoryFilter] = useState<string>("");
  const [collectionFilter, setCollectionFilter] = useState<string>("");
  const [yearFrom, setYearFrom] = useState<string>("");
  const [yearTo, setYearTo] = useState<string>("");
  const [linkHouseId, setLinkHouseId] = useState<string>("");
  const [linkAccId, setLinkAccId] = useState<string>("");
  const [showDuplicatesOnly, setShowDuplicatesOnly] = useState(false);
  
  // Manage tab - edit existing items
  const [editHouseId, setEditHouseId] = useState<string>("");
  const [editAccessoryId, setEditAccessoryId] = useState<string>("");

  // Refs for scrolling
  const accessoriesSectionRef = useRef<HTMLDivElement>(null);

  // Modals
  const imageModal = useModal<{ title?: string; src?: string }>();
  const houseModal = useModal<House>();
  const accessoryModal = useModal<Accessory>();
  const fileRef = useRef<HTMLInputElement>(null);
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
    if (yf && (h.purchased_year ?? 0) < yf) return false;
    if (yt && (h.purchased_year ?? 99999) > yt) return false;
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
    if (yf && (a.purchased_year ?? 0) < yf) return false;
    if (yt && (a.purchased_year ?? 99999) > yt) return false;
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
    return rows.sort((a, b) => a.name.localeCompare(b.name));
  }, [data, q, houseFilter, accessoryFilter, collectionFilter, yearFrom, yearTo, showDuplicatesOnly, duplicateItemIds]);

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
    return rows.sort((a, b) => a.name.localeCompare(b.name));
  }, [data, q, houseFilter, accessoryFilter, collectionFilter, yearFrom, yearTo, showDuplicatesOnly, duplicateItemIds]);

  // Load data from Supabase
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log("Starting to fetch data...");
      const fetchedData = await db.fetchAllData();
      console.log("Fetched data:", fetchedData);
      console.log("Houses:", fetchedData.houses.length);
      console.log("Accessories:", fetchedData.accessories.length);
      setData(fetchedData);
      console.log("Data set successfully!");
    } catch (err: any) {
      console.error("Error loading data:", err);
      setError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen grid place-items-center bg-gradient-to-b from-gray-50 to-white">
        <div className="text-center">
          <div className="inline-grid place-items-center h-16 w-16 rounded-2xl bg-indigo-600 text-white font-bold text-2xl mb-4 animate-pulse">
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
            <div className="text-red-600 font-semibold">Error Loading Data</div>
            <div className="text-sm text-gray-600">{error}</div>
            <Button onClick={loadData} className="bg-indigo-600 text-white">
              Retry
            </Button>
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
    tagIds: string[]
  ) {
    try {
      const newHouse = await db.createHouse(h, collectionIds, tagIds);
      await loadData(); // Refresh data
      setTab("browse");
      setHouseFilter(newHouse.id);
    } catch (error) {
      console.error("Error adding house:", error);
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
      setTab("browse");
      setAccessoryFilter(accessoryId);
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
          {(h.collection || h.series) && (
            <div className="text-xs text-gray-600">
              {h.collection && <div>Collection: {h.collection}</div>}
              {h.series && <div>Series: {h.series}</div>}
            </div>
          )}
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
          {(a.collection || a.series) && (
            <div className="text-xs text-gray-600">
              {a.collection && <div>Collection: {a.collection}</div>}
              {a.series && <div>Series: {a.series}</div>}
            </div>
          )}
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

  // Scroll to accessories section
  function scrollToAccessories() {
    setTab("browse");
    setTimeout(() => {
      accessoriesSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  }

  // Toggle duplicate filter
  function toggleDuplicateFilter() {
    setShowDuplicatesOnly(!showDuplicatesOnly);
    if (!showDuplicatesOnly) {
      setTab("browse");
      // Clear other filters
      setHouseFilter("");
      setAccessoryFilter("");
      setCollectionFilter("");
      setYearFrom("");
      setYearTo("");
      setQ("");
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white text-gray-900">
      <header className="sticky top-0 z-40 backdrop-blur bg-white/70 border-b">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="inline-grid place-items-center h-9 w-9 rounded-xl bg-indigo-600 text-white font-bold">
              56
            </span>
            <div className="leading-tight">
              <div className="font-semibold">Department 56 Browser</div>
              <div className="text-xs text-gray-500">Cloud-synced collection</div>
            </div>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Button onClick={() => setTab("browse")} className={tab === "browse" ? "bg-gray-100" : ""}>
              Browse
            </Button>
            <Button onClick={() => setTab("manage")} className={tab === "manage" ? "bg-gray-100" : ""}>
              Manage
            </Button>
            <Button 
              onClick={scrollToAccessories}
              className="bg-purple-600 text-white border-purple-600 hover:bg-purple-700"
              title="Jump to Accessories section"
            >
              → Accessories
            </Button>
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
            <div className="hidden sm:flex items-center gap-2">
              <Button onClick={exportJSON}>Export</Button>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-4 space-y-6">
        <Card className="p-3 sm:p-4">
          <div className="grid grid-cols-1 sm:grid-cols-6 gap-3 items-end">
            <Field label="Search (fuzzy, tags & collections)">
              <TextInput
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Try 'Mickys stufed'"
              />
            </Field>
            <Field label="Collection">
              <Select value={collectionFilter} onChange={(e) => setCollectionFilter(e.target.value)}>
                <option value="">All collections</option>
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
            <Field label="Purchased from year">
              <TextInput
                type="number"
                value={yearFrom}
                onChange={(e) => setYearFrom(e.target.value)}
                placeholder="e.g., 2015"
              />
            </Field>
            <Field label="to year">
              <TextInput
                type="number"
                value={yearTo}
                onChange={(e) => setYearTo(e.target.value)}
                placeholder="e.g., 2020"
              />
            </Field>
            <Field label="Filter by house">
              <Select value={houseFilter} onChange={(e) => setHouseFilter(e.target.value)}>
                <option value="">All houses</option>
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
            <Field label="Filter by accessory">
              <Select
                value={accessoryFilter}
                onChange={(e) => setAccessoryFilter(e.target.value)}
              >
                <option value="">All accessories</option>
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
            <div className="sm:col-span-6 flex gap-2">
              <Button
                onClick={() => {
                  setQ("");
                  setHouseFilter("");
                  setAccessoryFilter("");
                  setCollectionFilter("");
                  setYearFrom("");
                  setYearTo("");
                }}
              >
                Clear
              </Button>
              <Button
                onClick={() => setTab("manage")}
                className="bg-indigo-600 text-white border-indigo-600 hover:bg-indigo-700"
              >
                Add / Link
              </Button>
            </div>
          </div>
        </Card>

        {tab === "browse" ? (
          <div className="grid grid-cols-1 gap-6">
            {showDuplicatesOnly && (
              <Card className="p-4 bg-orange-50 border-orange-200">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-orange-900">Showing Duplicates Only</div>
                    <div className="text-sm text-orange-700">
                      Found {duplicateItemIds.houseIds.size} duplicate house(s) and {duplicateItemIds.accessoryIds.size} duplicate accessory(ies).
                      Click items to view details, or use the Manage tab to delete unwanted copies.
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
            <section className="space-y-3">
              <SectionTitle>
                Houses ({filteredHouses.length}{showDuplicatesOnly ? ` of ${data.houses.length}` : ""})
              </SectionTitle>
              {filteredHouses.length === 0 ? (
                <Card className="p-6 text-sm text-gray-500">
                  {showDuplicatesOnly ? "No duplicate houses found." : "No houses match your filters."}
                </Card>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {filteredHouses.map((h) => (
                    <HouseCard key={h.id} h={h} />
                  ))}
                </div>
              )}
            </section>
            <section ref={accessoriesSectionRef} className="space-y-3">
              <SectionTitle>
                Accessories ({filteredAccessories.length}{showDuplicatesOnly ? ` of ${data.accessories.length}` : ""})
              </SectionTitle>
              {filteredAccessories.length === 0 ? (
                <Card className="p-6 text-sm text-gray-500">
                  {showDuplicatesOnly ? "No duplicate accessories found." : "No accessories match your filters."}
                </Card>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {filteredAccessories.map((a) => (
                    <AccessoryCard key={a.id} a={a} />
                  ))}
                </div>
              )}
            </section>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Top row: House form and linked accessories/accessory form */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
              <div className="lg:col-span-3">
                <Card className="p-4">
                  <SectionTitle>Edit / Add House</SectionTitle>
                  <div className="pt-3 space-y-3">
                    <Field label="Load Existing House to Edit (optional)">
                      <Select 
                        value={editHouseId}
                        onChange={(e) => setEditHouseId(e.target.value)}
                      >
                        <option value="">-- Create New House --</option>
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
              </div>

              {/* Right column: Linked accessories and accessory form */}
              <div className="lg:col-span-2 space-y-6">
                {/* Linked accessories - shown when editing a house */}
                {editHouseId && (() => {
                  const linkedAccessories = data.houseAccessoryLinks
                    .filter((ha: HouseAccessoryLink) => ha.house_id === editHouseId)
                    .map((ha: HouseAccessoryLink) => data.accessories.find((a: Accessory) => a.id === ha.accessory_id))
                    .filter((a: Accessory | undefined): a is Accessory => a !== undefined);
                  
                  if (linkedAccessories.length === 0) {
                    return (
                      <Card className="p-4">
                        <h3 className="text-sm font-semibold text-gray-900 mb-2">
                          Linked Accessories
                        </h3>
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
                            {accessory.description && (
                              <div className="text-xs text-gray-600">
                                <p>{accessory.description}</p>
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
                      <AccessoryForm 
                        data={data} 
                        onSave={addAccessory}
                        onDelete={deleteAccessory}
                        onMoveToHouse={moveAccessoryToHouse}
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
            </div>

            {/* Bottom row: Link, Collections, Tags, Data Tools */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
          setEditHouseId(houseId);
          houseModal.hide();
        }}
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
          setEditAccessoryId(accessoryId);
          accessoryModal.hide();
          setTimeout(() => {
            accessoryFormRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
          }, 100);
        }}
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
