import React, { useEffect, useMemo, useRef, useState } from "react";

/**
 * Department 56 Browser — React app (enhanced)
 * --------------------------------------------------------------
 * NEW in this revision
 * - Purchased date / purchased year metadata on houses & accessories
 * - First‑class Collections (many‑to‑many links to houses & accessories)
 * - Tags (manual + ML placeholder) with confidence + reviewed flag
 * - Fuzzy search across names, collections, and tags (trigram‑ish)
 * - LocalStorage DB remains; structure mirrors proposed Supabase schema
 */

// ------------------------ Types ------------------------
export type House = {
  id: string;
  name: string;
  year?: number;
  notes?: string;
  photo?: string;
  purchasedOn?: string; // ISO date
  purchasedYear?: number; // if only year known
};

export type Accessory = {
  id: string;
  name: string;
  notes?: string;
  photo?: string;
  purchasedOn?: string;
  purchasedYear?: number;
};

export type Collection = {
  id: string;
  name: string;
  notes?: string;
};

export type Tag = {
  id: string;
  name: string;
};

export type Link = { id: string; houseId: string; accessoryId: string };
export type HouseCollection = { id: string; houseId: string; collectionId: string };
export type AccessoryCollection = { id: string; accessoryId: string; collectionId: string };
export type HouseTag = { id: string; houseId: string; tagId: string; source: "manual" | "ml"; confidence?: number; reviewed?: boolean };
export type AccessoryTag = { id: string; accessoryId: string; tagId: string; source: "manual" | "ml"; confidence?: number; reviewed?: boolean };

export type DBExport = {
  version: 2;
  houses: House[];
  accessories: Accessory[];
  links: Link[];
  collections: Collection[];
  houseCollections: HouseCollection[];
  accessoryCollections: AccessoryCollection[];
  tags: Tag[];
  houseTags: HouseTag[];
  accessoryTags: AccessoryTag[];
};

// ------------------------ Storage ------------------------
const KEY = "dept56-db-v2";
const uid = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

function loadDB(): DBExport {
  const raw = localStorage.getItem(KEY);
  if (!raw) return emptyDB();
  try {
    const parsed = JSON.parse(raw);
    if (!parsed.version) return migrateV1(parsed);
    return parsed as DBExport;
  } catch {
    return emptyDB();
  }
}

function emptyDB(): DBExport {
  return {
    version: 2,
    houses: [],
    accessories: [],
    links: [],
    collections: [],
    houseCollections: [],
    accessoryCollections: [],
    tags: [],
    houseTags: [],
    accessoryTags: [],
  };
}

function migrateV1(v1: any): DBExport {
  // Basic migration from the initial prototype structure
  return {
    version: 2,
    houses: v1.houses || [],
    accessories: v1.accessories || [],
    links: v1.links || [],
    collections: [],
    houseCollections: [],
    accessoryCollections: [],
    tags: [],
    houseTags: [],
    accessoryTags: [],
  };
}

function saveDB(db: DBExport) {
  localStorage.setItem(KEY, JSON.stringify(db));
}

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
  A.forEach((x) => { if (B.has(x)) inter++; });
  return inter / Math.max(A.size, B.size);
}
function fuzzyIncludes(hay: string, needle: string) {
  hay = hay.toLowerCase();
  needle = needle.toLowerCase().trim();
  return hay.includes(needle) || similarity(hay, needle) > 0.28;
}

// ------------------------ UI bits ------------------------
function Button({ className = "", ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { className?: string }) {
  return (
    <button
      {...props}
      className={
        "px-3 py-2 rounded-2xl text-sm font-medium shadow-sm border border-gray-200 bg-white hover:bg-gray-50 active:scale-[.99] transition " +
        className
      }
    />
  );
}
const Pill = ({ children }: { children: React.ReactNode }) => (
  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-700">{children}</span>
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
  <div className={"rounded-3xl border border-gray-200 bg-white shadow-sm " + className}>{children}</div>
);
const SectionTitle = ({ children, aside }: { children: React.ReactNode; aside?: React.ReactNode }) => (
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
    show: (d: T) => { setData(d); setOpen(true); },
    hide: () => setOpen(false),
  } as const;
}
function ImageModal({ open, onClose, title, src }: { open: boolean; onClose: () => void; title?: string; src?: string }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4" onClick={onClose}>
      <div className="max-w-3xl w-full" onClick={(e) => e.stopPropagation()}>
        <Card className="overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b">
            <div className="font-medium truncate pr-4">{title || "Photo"}</div>
            <Button onClick={onClose}>Close</Button>
          </div>
          {src ? <img src={src} alt={title} className="w-full h-auto" /> : <div className="p-6 text-sm text-gray-500">No image</div>}
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
  const filtered = useMemo(() => options.filter((o) => o.name.toLowerCase().includes(text.toLowerCase())), [options, text]);
  return (
    <div className="space-y-2">
      <Field label={label + " (type to filter)"}>
        <TextInput value={text} onChange={(e) => setText(e.target.value)} placeholder="Start typing…" />
      </Field>
      <div className="flex flex-wrap gap-2">
        {filtered.map((o) => {
          const active = selectedIds.includes(o.id);
          return (
            <button
              key={o.id}
              onClick={(e) => { e.preventDefault(); onChange(active ? selectedIds.filter((id) => id !== o.id) : [...selectedIds, o.id]); }}
              className={`px-2 py-1 rounded-full text-xs border ${active ? "bg-indigo-600 text-white border-indigo-600" : "bg-white"}`}
            >
              {o.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function HouseForm({ db, onSave, initial }: { db: DBExport; onSave: (h: House, collections: string[], tags: string[]) => void; initial?: Partial<House> & { collectionIds?: string[]; tagIds?: string[] } }) {
  const [name, setName] = useState(initial?.name || "");
  const [year, setYear] = useState<number | undefined>(initial?.year);
  const [notes, setNotes] = useState(initial?.notes || "");
  const [photo, setPhoto] = useState<string | undefined>(initial?.photo);
  const [purchasedOn, setPurchasedOn] = useState(initial?.purchasedOn || "");
  const [purchasedYear, setPurchasedYear] = useState<number | undefined>(initial?.purchasedYear);
  const [collectionIds, setCollectionIds] = useState<string[]>(initial?.collectionIds || []);
  const [tagIds, setTagIds] = useState<string[]>(initial?.tagIds || []);

  async function handleFile(file?: File) {
    if (file) setPhoto(await fileToDataURL(file));
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const h: House = { id: initial?.id || uid(), name: name.trim(), year, notes: notes.trim() || undefined, photo, purchasedOn: purchasedOn || undefined, purchasedYear };
        onSave(h, collectionIds, tagIds);
      }}
      className="space-y-3"
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Field label="House name"><TextInput value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g., Mickey's Stuffed Animals" /></Field>
        <Field label="Year"><TextInput type="number" value={year ?? ""} onChange={(e) => setYear(e.target.value ? Number(e.target.value) : undefined)} placeholder="2018" /></Field>
        <Field label="Purchased on (date)"><TextInput type="date" value={purchasedOn} onChange={(e) => setPurchasedOn(e.target.value)} /></Field>
        <Field label="Purchased year"><TextInput type="number" value={purchasedYear ?? ""} onChange={(e) => setPurchasedYear(e.target.value ? Number(e.target.value) : undefined)} placeholder="If date unknown" /></Field>
        <Field label="Photo"><input type="file" accept="image/*" onChange={(e) => handleFile(e.target.files?.[0])} /></Field>
        <Field label="Notes"><TextArea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Any details" /></Field>
        {photo && <img src={photo} alt="preview" className="h-24 w-24 rounded-xl object-cover border" />}
      </div>

      <MultiSelectChips options={db.collections} selectedIds={collectionIds} onChange={setCollectionIds} label="Collections" />
      <MultiSelectChips options={db.tags} selectedIds={tagIds} onChange={setTagIds} label="Tags" />

      <div className="flex items-center gap-2 pt-2">
        <Button type="submit" className="bg-indigo-600 text-white border-indigo-600 hover:bg-indigo-700">Save House</Button>
      </div>
    </form>
  );
}

function AccessoryForm({ db, onSave, initial }: { db: DBExport; onSave: (a: Accessory, collections: string[], tags: string[]) => void; initial?: Partial<Accessory> & { collectionIds?: string[]; tagIds?: string[] } }) {
  const [name, setName] = useState(initial?.name || "");
  const [notes, setNotes] = useState(initial?.notes || "");
  const [photo, setPhoto] = useState<string | undefined>(initial?.photo);
  const [purchasedOn, setPurchasedOn] = useState(initial?.purchasedOn || "");
  const [purchasedYear, setPurchasedYear] = useState<number | undefined>(initial?.purchasedYear);
  const [collectionIds, setCollectionIds] = useState<string[]>(initial?.collectionIds || []);
  const [tagIds, setTagIds] = useState<string[]>(initial?.tagIds || []);

  async function handleFile(file?: File) { if (file) setPhoto(await fileToDataURL(file)); }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const a: Accessory = { id: initial?.id || uid(), name: name.trim(), notes: notes.trim() || undefined, photo, purchasedOn: purchasedOn || undefined, purchasedYear };
        onSave(a, collectionIds, tagIds);
      }}
      className="space-y-3"
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Field label="Accessory name"><TextInput value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g., Stuffing Station" /></Field>
        <Field label="Purchased on (date)"><TextInput type="date" value={purchasedOn} onChange={(e) => setPurchasedOn(e.target.value)} /></Field>
        <Field label="Purchased year"><TextInput type="number" value={purchasedYear ?? ""} onChange={(e) => setPurchasedYear(e.target.value ? Number(e.target.value) : undefined)} placeholder="If date unknown" /></Field>
        <Field label="Photo"><input type="file" accept="image/*" onChange={(e) => handleFile(e.target.files?.[0])} /></Field>
        <Field label="Notes"><TextArea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Any details" /></Field>
        {photo && <img src={photo} alt="preview" className="h-24 w-24 rounded-xl object-cover border" />}
      </div>

      <MultiSelectChips options={db.collections} selectedIds={collectionIds} onChange={setCollectionIds} label="Collections" />
      <MultiSelectChips options={db.tags} selectedIds={tagIds} onChange={setTagIds} label="Tags" />

      <div className="flex items-center gap-2 pt-2">
        <Button type="submit" className="bg-indigo-600 text-white border-indigo-600 hover:bg-indigo-700">Save Accessory</Button>
      </div>
    </form>
  );
}

// ------------------------ App ------------------------
export default function App() {
  const [db, setDb] = useState<DBExport>(() => loadDB());
  useEffect(() => saveDB(db), [db]);

  const [tab, setTab] = useState<"browse" | "manage">("browse");
  const [q, setQ] = useState("");
  const [houseFilter, setHouseFilter] = useState<string>("");
  const [accessoryFilter, setAccessoryFilter] = useState<string>("");
  const [collectionFilter, setCollectionFilter] = useState<string>("");
  const [yearFrom, setYearFrom] = useState<string>("");
  const [yearTo, setYearTo] = useState<string>("");

  // Image modal
  const modal = useModal<{ title?: string; src?: string }>();

  // Derived: maps for quick lookup
  const collById = useMemo(() => Object.fromEntries(db.collections.map(c => [c.id, c])), [db.collections]);
  const tagById = useMemo(() => Object.fromEntries(db.tags.map(t => [t.id, t])), [db.tags]);

  // Filtering helpers
  function houseMatches(h: House): boolean {
    if (q.trim()) {
      const text = [h.name, String(h.year ?? ""), String(h.purchasedYear ?? ""), h.notes || ""].join(" ");
      const tags = db.houseTags.filter(x => x.houseId === h.id).map(x => tagById[x.tagId]?.name || "").join(" ");
      const colls = db.houseCollections.filter(x => x.houseId === h.id).map(x => collById[x.collectionId]?.name || "").join(" ");
      if (!(fuzzyIncludes(text, q) || fuzzyIncludes(tags, q) || fuzzyIncludes(colls, q))) return false;
    }
    if (collectionFilter) {
      const has = db.houseCollections.some((x) => x.houseId === h.id && x.collectionId === collectionFilter);
      if (!has) return false;
    }
    const yf = yearFrom ? Number(yearFrom) : undefined;
    const yt = yearTo ? Number(yearTo) : undefined;
    if (yf && (h.purchasedYear ?? 0) < yf) return false;
    if (yt && (h.purchasedYear ?? 99999) > yt) return false;
    return true;
  }
  function accessoryMatches(a: Accessory): boolean {
    if (q.trim()) {
      const text = [a.name, String(a.purchasedYear ?? ""), a.notes || ""].join(" ");
      const tags = db.accessoryTags.filter(x => x.accessoryId === a.id).map(x => tagById[x.tagId]?.name || "").join(" ");
      const colls = db.accessoryCollections.filter(x => x.accessoryId === a.id).map(x => collById[x.collectionId]?.name || "").join(" ");
      if (!(fuzzyIncludes(text, q) || fuzzyIncludes(tags, q) || fuzzyIncludes(colls, q))) return false;
    }
    if (collectionFilter) {
      const has = db.accessoryCollections.some((x) => x.accessoryId === a.id && x.collectionId === collectionFilter);
      if (!has) return false;
    }
    const yf = yearFrom ? Number(yearFrom) : undefined;
    const yt = yearTo ? Number(yearTo) : undefined;
    if (yf && (a.purchasedYear ?? 0) < yf) return false;
    if (yt && (a.purchasedYear ?? 99999) > yt) return false;
    return true;
  }

  const filteredHouses = useMemo(() => {
    let rows = db.houses.filter(houseMatches);
    if (accessoryFilter) {
      const linkedHouseIds = new Set(db.links.filter(l => l.accessoryId === accessoryFilter).map(l => l.houseId));
      rows = rows.filter(h => linkedHouseIds.has(h.id));
    }
    if (houseFilter) rows = rows.filter(h => h.id === houseFilter);
    return rows.sort((a, b) => a.name.localeCompare(b.name));
  }, [db, q, houseFilter, accessoryFilter, collectionFilter, yearFrom, yearTo]);

  const filteredAccessories = useMemo(() => {
    let rows = db.accessories.filter(accessoryMatches);
    if (houseFilter) {
      const linkedAccIds = new Set(db.links.filter(l => l.houseId === houseFilter).map(l => l.accessoryId));
      rows = rows.filter(a => linkedAccIds.has(a.id));
    }
    if (accessoryFilter) rows = rows.filter(a => a.id === accessoryFilter);
    return rows.sort((a, b) => a.name.localeCompare(b.name));
  }, [db, q, houseFilter, accessoryFilter, collectionFilter, yearFrom, yearTo]);

  // CRUD helpers
  function addHouse(h: House, collectionIds: string[], tagIds: string[]) {
    setDb(d => ({ ...d, houses: [...d.houses, h], houseCollections: [...d.houseCollections, ...collectionIds.map(cid => ({ id: uid(), houseId: h.id, collectionId: cid }))], houseTags: [...d.houseTags, ...tagIds.map(tid => ({ id: uid(), houseId: h.id, tagId: tid, source: "manual", reviewed: true }))] }));
    setTab("browse");
    setHouseFilter(h.id);
  }
  function addAccessory(a: Accessory, collectionIds: string[], tagIds: string[]) {
    setDb(d => ({ ...d, accessories: [...d.accessories, a], accessoryCollections: [...d.accessoryCollections, ...collectionIds.map(cid => ({ id: uid(), accessoryId: a.id, collectionId: cid }))], accessoryTags: [...d.accessoryTags, ...tagIds.map(tid => ({ id: uid(), accessoryId: a.id, tagId: tid, source: "manual", reviewed: true }))] }));
    setTab("browse");
    setAccessoryFilter(a.id);
  }
  function addLink(houseId: string, accessoryId: string) {
    if (!houseId || !accessoryId) return;
    const exists = db.links.some(l => l.houseId === houseId && l.accessoryId === accessoryId);
    if (exists) return;
    setDb(d => ({ ...d, links: [...d.links, { id: uid(), houseId, accessoryId }] }));
  }
  function unlink(linkId: string) { setDb(d => ({ ...d, links: d.links.filter(l => l.id !== linkId) })); }

  // Manage lists: Collections & Tags
  function addCollection(name: string) {
    const trimmed = name.trim(); if (!trimmed) return;
    if (db.collections.some(c => c.name.toLowerCase() === trimmed.toLowerCase())) return;
    setDb(d => ({ ...d, collections: [...d.collections, { id: uid(), name: trimmed }] }));
  }
  function addTag(name: string) {
    const trimmed = name.trim(); if (!trimmed) return;
    if (db.tags.some(t => t.name.toLowerCase() === trimmed.toLowerCase())) return;
    setDb(d => ({ ...d, tags: [...d.tags, { id: uid(), name: trimmed }] }));
  }

  // Import / Export
  const fileRef = useRef<HTMLInputElement>(null);
  function exportJSON() { download(`dept56-export-${new Date().toISOString().slice(0,10)}.json`, JSON.stringify(db, null, 2)); }
  async function importJSON(file?: File) {
    if (!file) return;
    try { const parsed = JSON.parse(await file.text()); setDb(parsed); alert("Import complete."); } catch (e: any) { alert("Import failed: " + e.message); }
  }

  // UI cards
  function HouseCard({ h }: { h: House }) {
    const accessories = db.links.filter(l => l.houseId === h.id).map(l => ({ linkId: l.id, a: db.accessories.find(x => x.id === l.accessoryId)! })).filter(x => x.a);
    const colls = db.houseCollections.filter(x => x.houseId === h.id).map(x => collById[x.collectionId]).filter(Boolean) as Collection[];
    const tags = db.houseTags.filter(x => x.houseId === h.id).map(x => tagById[x.tagId]).filter(Boolean) as Tag[];
    return (
      <Card className="overflow-hidden">
        {h.photo ? <button className="block w-full" onClick={() => modal.show({ src: h.photo, title: h.name })}><img src={h.photo} alt={h.name} className="w-full h-48 object-cover" /></button> : <div className="w-full h-48 grid place-items-center text-gray-400 text-sm">No photo</div>}
        <div className="p-3 space-y-2">
          <div className="font-semibold leading-tight">{h.name}</div>
          <div className="flex gap-2 flex-wrap">
            {h.year && <Pill>Year {h.year}</Pill>}
            {h.purchasedYear && <Pill>Purchased {h.purchasedYear}</Pill>}
            {colls.map(c => <Pill key={c.id}>{c.name}</Pill>)}
          </div>
          {tags.length > 0 && <div className="flex gap-1 flex-wrap text-[11px] text-gray-700">{tags.map(t => <span key={t.id} className="bg-gray-100 rounded-full px-2 py-0.5">#{t.name}</span>)}</div>}
          <div className="pt-2">
            <div className="text-xs font-semibold text-gray-700 mb-1">Accessories</div>
            {accessories.length === 0 ? <div className="text-xs text-gray-500">None linked yet</div> : (
              <div className="grid grid-cols-4 gap-2 sm:grid-cols-6">
                {accessories.map(({ linkId, a }) => (
                  <div key={linkId} className="relative group">
                    <button className="block w-full" onClick={() => modal.show({ src: a.photo, title: a.name })} title={a.name}>
                      {a.photo ? <img src={a.photo} alt={a.name} className="h-16 w-full object-cover rounded-lg border" /> : <div className="h-16 w-full grid place-items-center text-[10px] text-gray-400 border rounded-lg">No photo</div>}
                    </button>
                    <button className="absolute top-1 right-1 hidden group-hover:block bg-white/90 border rounded-full px-1 text-[10px]" onClick={() => unlink(linkId)} title="Unlink">✕</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </Card>
    );
  }

  function AccessoryCard({ a }: { a: Accessory }) {
    const houses = db.links.filter(l => l.accessoryId === a.id).map(l => ({ linkId: l.id, h: db.houses.find(x => x.id === l.houseId)! })).filter(x => x.h);
    const colls = db.accessoryCollections.filter(x => x.accessoryId === a.id).map(x => collById[x.collectionId]).filter(Boolean) as Collection[];
    const tags = db.accessoryTags.filter(x => x.accessoryId === a.id).map(x => tagById[x.tagId]).filter(Boolean) as Tag[];
    return (
      <Card className="overflow-hidden">
        {a.photo ? <button className="block w-full" onClick={() => modal.show({ src: a.photo, title: a.name })}><img src={a.photo} alt={a.name} className="w-full h-48 object-cover" /></button> : <div className="w-full h-48 grid place-items-center text-gray-400 text-sm">No photo</div>}
        <div className="p-3 space-y-2">
          <div className="font-semibold leading-tight">{a.name}</div>
          <div className="flex gap-2 flex-wrap">{a.purchasedYear && <Pill>Purchased {a.purchasedYear}</Pill>}{colls.map(c => <Pill key={c.id}>{c.name}</Pill>)}</div>
          {tags.length > 0 && <div className="flex gap-1 flex-wrap text-[11px] text-gray-700">{tags.map(t => <span key={t.id} className="bg-gray-100 rounded-full px-2 py-0.5">#{t.name}</span>)}</div>}
          {houses.length > 0 && <div className="text-xs text-gray-700">Linked to: {houses.map(({ h }) => h.name).join(", ")}</div>}
        </div>
      </Card>
    );
  }

  // Link state
  const [linkHouseId, setLinkHouseId] = useState<string>("");
  const [linkAccId, setLinkAccId] = useState<string>("");
  const canLink = linkHouseId && linkAccId && !db.links.some(l => l.houseId === linkHouseId && l.accessoryId === linkAccId);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white text-gray-900">
      <header className="sticky top-0 z-40 backdrop-blur bg-white/70 border-b">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="inline-grid place-items-center h-9 w-9 rounded-xl bg-indigo-600 text-white font-bold">56</span>
            <div className="leading-tight">
              <div className="font-semibold">Department 56 Browser</div>
              <div className="text-xs text-gray-500">Private collection manager</div>
            </div>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Button onClick={() => setTab("browse")} className={tab === "browse" ? "bg-gray-100" : ""}>Browse</Button>
            <Button onClick={() => setTab("manage")} className={tab === "manage" ? "bg-gray-100" : ""}>Manage</Button>
            <div className="hidden sm:flex items-center gap-2">
              <Button onClick={exportJSON}>Export</Button>
              <input ref={fileRef} type="file" accept="application/json" className="hidden" onChange={(e) => importJSON(e.target.files?.[0] || undefined)} />
              <Button onClick={() => fileRef.current?.click()}>Import</Button>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-4 space-y-6">
        <Card className="p-3 sm:p-4">
          <div className="grid grid-cols-1 sm:grid-cols-6 gap-3 items-end">
            <Field label="Search (fuzzy, tags & collections)"><TextInput value={q} onChange={(e) => setQ(e.target.value)} placeholder="Try 'Mickys stufed'" /></Field>
            <Field label="Collection">
              <Select value={collectionFilter} onChange={(e) => setCollectionFilter(e.target.value)}>
                <option value="">All collections</option>
                {db.collections.slice().sort((a,b)=>a.name.localeCompare(b.name)).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </Select>
            </Field>
            <Field label="Purchased from year"><TextInput type="number" value={yearFrom} onChange={(e)=>setYearFrom(e.target.value)} placeholder="e.g., 2015" /></Field>
            <Field label="to year"><TextInput type="number" value={yearTo} onChange={(e)=>setYearTo(e.target.value)} placeholder="e.g., 2020" /></Field>
            <Field label="Filter by house">
              <Select value={houseFilter} onChange={(e) => setHouseFilter(e.target.value)}>
                <option value="">All houses</option>
                {db.houses.slice().sort((a,b)=>a.name.localeCompare(b.name)).map(h => <option key={h.id} value={h.id}>{h.name}</option>)}
              </Select>
            </Field>
            <Field label="Filter by accessory">
              <Select value={accessoryFilter} onChange={(e) => setAccessoryFilter(e.target.value)}>
                <option value="">All accessories</option>
                {db.accessories.slice().sort((a,b)=>a.name.localeCompare(b.name)).map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </Select>
            </Field>
            <div className="sm:col-span-6 flex gap-2">
              <Button onClick={() => { setQ(""); setHouseFilter(""); setAccessoryFilter(""); setCollectionFilter(""); setYearFrom(""); setYearTo(""); }}>Clear</Button>
              <Button onClick={() => setTab("manage")} className="bg-indigo-600 text-white border-indigo-600 hover:bg-indigo-700">Add / Link</Button>
            </div>
          </div>
        </Card>

        {tab === "browse" ? (
          <div className="grid grid-cols-1 gap-6">
            <section className="space-y-3">
              <SectionTitle aside={<Pill>{filteredHouses.length}</Pill>}>Houses</SectionTitle>
              {filteredHouses.length === 0 ? <Card className="p-6 text-sm text-gray-500">No houses match your filters.</Card> : (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {filteredHouses.map(h => <HouseCard key={h.id} h={h} />)}
                </div>
              )}
            </section>
            <section className="space-y-3">
              <SectionTitle aside={<Pill>{filteredAccessories.length}</Pill>}>Accessories</SectionTitle>
              {filteredAccessories.length === 0 ? <Card className="p-6 text-sm text-gray-500">No accessories match your filters.</Card> : (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {filteredAccessories.map(a => <AccessoryCard key={a.id} a={a} />)}
                </div>
              )}
            </section>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            <div className="lg:col-span-3 space-y-6">
              <Card className="p-4"><SectionTitle>New House</SectionTitle><div className="pt-3"><HouseForm db={db} onSave={addHouse} /></div></Card>
              <Card className="p-4"><SectionTitle>New Accessory</SectionTitle><div className="pt-3"><AccessoryForm db={db} onSave={addAccessory} /></div></Card>
            </div>
            <div className="lg:col-span-2 space-y-6">
              <Card className="p-4">
                <SectionTitle>Link Accessory to House</SectionTitle>
                <div className="grid grid-cols-1 gap-3 pt-3">
                  <Field label="House">
                    <Select value={linkHouseId} onChange={(e) => setLinkHouseId(e.target.value)}>
                      <option value="">Select…</option>
                      {db.houses.slice().sort((a,b)=>a.name.localeCompare(b.name)).map(h => <option key={h.id} value={h.id}>{h.name}</option>)}
                    </Select>
                  </Field>
                  <Field label="Accessory">
                    <Select value={linkAccId} onChange={(e) => setLinkAccId(e.target.value)}>
                      <option value="">Select…</option>
                      {db.accessories.slice().sort((a,b)=>a.name.localeCompare(b.name)).map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                    </Select>
                  </Field>
                  <div className="flex gap-2">
                    <Button onClick={() => addLink(linkHouseId, linkAccId)} disabled={!canLink} className={`bg-emerald-600 text-white border-emerald-600 hover:bg-emerald-700 ${!canLink ? "opacity-60 cursor-not-allowed" : ""}`}>Link</Button>
                    <Button onClick={() => { setLinkAccId(""); setLinkHouseId(""); }}>Clear</Button>
                  </div>
                </div>
              </Card>

              <Card className="p-4 space-y-4">
                <SectionTitle>Collections</SectionTitle>
                <AddOneLine label="Add collection" onAdd={addCollection} />
                <div className="flex flex-wrap gap-2">
                  {db.collections.slice().sort((a,b)=>a.name.localeCompare(b.name)).map(c => <Pill key={c.id}>{c.name}</Pill>)}
                </div>
              </Card>

              <Card className="p-4 space-y-4">
                <SectionTitle>Tags</SectionTitle>
                <AddOneLine label="Add tag" onAdd={addTag} />
                <div className="flex flex-wrap gap-2">
                  {db.tags.slice().sort((a,b)=>a.name.localeCompare(b.name)).map(t => <Pill key={t.id}>#{t.name}</Pill>)}
                </div>
                <p className="text-xs text-gray-500">Tip: when we hook this up to Supabase, an Edge Function can propose ML tags. Here we support manual tags.</p>
              </Card>

              <Card className="p-4">
                <SectionTitle>Data Tools</SectionTitle>
                <div className="pt-3 flex flex-wrap gap-2">
                  <Button onClick={exportJSON}>Export JSON</Button>
                  <input ref={fileRef} type="file" accept="application/json" className="hidden" onChange={(e) => importJSON(e.target.files?.[0] || undefined)} />
                  <Button onClick={() => fileRef.current?.click()}>Import JSON</Button>
                  <Button onClick={() => { localStorage.removeItem(KEY); setDb(emptyDB()); }}>Reset (danger)</Button>
                </div>
                <p className="text-xs text-gray-500 pt-2">Data live only in this browser. Export to back up or migrate.</p>
              </Card>
            </div>
          </div>
        )}
      </main>

      <footer className="py-6 text-center text-xs text-gray-500">© {new Date().getFullYear()} Dept56 Browser — local demo (v2)</footer>
      <ImageModal open={modal.open} onClose={modal.hide} title={modal.data?.title} src={modal.data?.src} />
    </div>
  );
}

function AddOneLine({ label, onAdd }: { label: string; onAdd: (name: string) => void }) {
  const [v, setV] = useState("");
  return (
    <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); onAdd(v); setV(""); }}>
      <TextInput value={v} onChange={(e) => setV(e.target.value)} placeholder={label} />
      <Button type="submit">Add</Button>
    </form>
  );
}
