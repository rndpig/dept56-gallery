# Copilot Instructions — Department 56 Gallery App

## Project Overview

This is a **Department 56 collectibles gallery web application** for managing and browsing a personal collection of porcelain houses and accessories. It is a private, family-use application with a small whitelisted user base (6 emails). The app was migrated from a Supabase/PostgreSQL backend to **Firebase** (Firestore + Storage + Hosting + Google Auth). Some legacy references to Supabase remain in documentation and Python scripts.

### Key URLs & Identifiers

- **Firebase project**: `dept56-gallery`
- **Hosting**: Firebase Hosting (builds to `dist/`)
- **Dev server**: `http://localhost:3000`

---

## Tech Stack

### Frontend (src/)

| Layer        | Technology                                              |
| ------------ | ------------------------------------------------------- |
| Framework    | React 18 (functional components, hooks only)            |
| Language     | TypeScript 5.3 (strict mode)                            |
| Build tool   | Vite 5                                                  |
| Styling      | Tailwind CSS 3.4 (utility-first, no component library)  |
| Search       | Fuse.js (import workflow) + custom trigram fuzzy search  |
| Backend      | Firebase v12 (Firestore, Storage, Auth)                 |
| Auth         | Google OAuth via Firebase with email whitelist           |

### Backend / Infrastructure

| Service          | Purpose                                                 |
| ---------------- | ------------------------------------------------------- |
| Firestore        | NoSQL document database (9 collections)                 |
| Firebase Storage | Image uploads (max 10 MB, images only)                  |
| Firebase Hosting | Static site hosting with SPA rewrites                   |
| Firebase Auth    | Google sign-in with client-side email whitelist          |

### Scripts & Tooling (scripts/)

| Tool            | Purpose                                                 |
| --------------- | ------------------------------------------------------- |
| Python 3.8+     | Data ingestion, scraping, maintenance, search index gen  |
| Selenium        | Web scraping Department 56 product sites                 |
| rapidfuzz       | Fuzzy string matching in Python scripts                  |
| python-docx     | Parsing Word documents for collection data               |
| PowerShell/Bash | Git hooks for secret detection                           |

---

## Project Structure

```
src/
├── main.tsx                  # React entry point
├── App.tsx                   # Thin wrapper, renders DeptApp
├── DeptApp.tsx               # ★ Main application (~4300 lines, monolithic)
├── index.css                 # Tailwind directives + minimal global styles
├── vite-env.d.ts             # Vite type declarations
├── lib/
│   ├── firebase.ts           # Firebase app init + service exports
│   ├── firebase-auth.ts      # Google OAuth, email whitelist, auth state
│   └── firebase-database.ts  # Firestore CRUD + Storage upload/delete
├── types/
│   ├── database.ts           # snake_case types (legacy, used by DeptApp)
│   └── firestore.ts          # camelCase Firestore types + converters
├── components/               # Empty — all components are inline in DeptApp.tsx
├── api/                      # Empty — API handled via Vite plugin in dev
├── DataReviewTab.tsx          # Not ported to Firebase (commented out)
├── EnhancedDataReview.tsx     # Not ported to Firebase (commented out)
└── enrichmentScanner.ts       # Data enrichment utilities

scripts/
├── scraper/                  # Production multi-source scrapers
├── scraping/                 # Legacy prototype scraper
├── data-ingestion/           # Word document importers
├── maintenance/              # Database cleanup & dedup tools
├── git/                      # Pre-commit hooks for secret prevention
├── bulk_import_scraper.py    # Called by Vite dev server API plugin
├── generate_search_index.py  # Builds public/house_search_index.json
├── docx_parser.py            # Parses .docx collection documents
└── ... (various analysis & fix scripts)

public/
├── house_search_index.json   # Pre-built Fuse.js search index
└── diagnostic.html           # Network diagnostic page
```

---

## Architecture & Patterns

### Monolithic Component Pattern

`DeptApp.tsx` is the main application file containing **all UI components, state management, business logic, and rendering** in a single file (~4300 lines). This includes:

- ~15 inline sub-components (`Button`, `Card`, `Field`, `TextInput`, `TextArea`, `Select`, `Pill`, `SectionTitle`, `ImageModal`, `HouseDetailModal`, `AccessoryDetailModal`, `MultiSelectChips`, `HouseForm`, `AccessoryForm`, `HouseCard`, `AccessoryCard`, `AddOneLine`)
- A custom `useModal` hook
- All application state via `useState` / `useMemo` / `useRef`
- Fuzzy search utilities (`trigram`, `similarity`, `fuzzyIncludes`)

**When modifying the UI**: Work within `DeptApp.tsx`. Do not extract components to separate files unless explicitly asked — the current monolithic pattern is intentional for this small-team project.

### Data Flow

```
Firebase Firestore
    ↓ fetchAllData()
DeptApp state (data: Database)
    ↓ useMemo (filtering, sorting, dedup detection)
Rendered UI
    ↓ user action
Async Firebase call (create/update/delete)
    ↓ loadData()
Re-fetch all data → re-render
```

- Data is fetched **all-at-once** on load via `fetchAllData()` (no pagination, no real-time listeners)
- After every mutation, the entire dataset is re-fetched to ensure consistency
- Filtering, sorting, and duplicate detection happen client-side via `useMemo`

### Dual Type Systems

There are **two parallel type systems** — be aware of this when working with data:

1. **`src/types/database.ts`** — Uses `snake_case` field names (legacy from PostgreSQL). **This is what `DeptApp.tsx` consumes.**
   - `House`, `Accessory`, `Collection`, `Tag`, `HouseAccessoryLink`, etc.
   - Fields: `photo_url`, `retired_year`, `purchased_year`, `created_at`, `user_id`

2. **`src/types/firestore.ts`** — Uses `camelCase` field names matching Firestore documents.
   - `FirestoreHouse`, `FirestoreAccessory`, etc.
   - Fields: `photoUrl`, `retiredYear`, `purchasedYear`, `createdAt`, `userId`

The **conversion layer** lives in `src/lib/firebase-database.ts` with functions like `firestoreToHouse()` that map camelCase Firestore docs → snake_case app types.

**Rule**: When adding a new field:
1. Add to `database.ts` type (snake_case)
2. Add to `firestore.ts` type (camelCase)  
3. Add mapping in `firebase-database.ts` converter functions
4. Add to create/update functions in `firebase-database.ts`

### Authentication Model

- **Google OAuth only** — no email/password auth
- **Client-side email whitelist** in `firebase-auth.ts` (`ALLOWED_ADMIN_EMAILS` array)
- **Firestore rules** also enforce the whitelist for write operations
- **Public read access** — all Firestore collections allow unauthenticated reads
- **Write access** — requires authentication + whitelisted email
- Non-admin visitors can browse but cannot edit

### Firebase Collections (Firestore)

| Collection             | Purpose                                   |
| ---------------------- | ----------------------------------------- |
| `houses`               | Porcelain house items                     |
| `accessories`          | Accessory items                           |
| `collections`          | User-defined groupings                    |
| `tags`                 | Categorization labels (manual or ML)      |
| `houseAccessoryLinks`  | Many-to-many: house ↔ accessory           |
| `houseCollections`     | Many-to-many: house ↔ collection          |
| `accessoryCollections` | Many-to-many: accessory ↔ collection      |
| `houseTags`            | Many-to-many: house ↔ tag                 |
| `accessoryTags`        | Many-to-many: accessory ↔ tag             |

### Image Storage

- **Firebase Storage** path: `uploads/{timestamp}-{random}.{ext}`
- Legacy images may reference old Supabase URLs (handled gracefully)
- Max size: 10 MB, images only (enforced by Storage rules)
- Public read, authenticated write/delete

---

## Coding Conventions

### TypeScript

- **Strict mode** enabled (`strict: true`, `noUnusedLocals`, `noUnusedParameters`)
- Target: ES2020, JSX: react-jsx
- Module resolution: bundler mode
- Use `type` imports for type-only references
- Prefer explicit types over `any` (though some `any` exists in converter functions)

### React

- **Functional components only** — no class components
- **Hooks**: `useState`, `useEffect`, `useMemo`, `useRef`, `useCallback`
- **No state management library** — all state in `DeptApp` component
- **No router** — tab-based navigation via state (`tab`, `manageView`, `browseView`)
- Event handlers are defined as arrow functions inside the component

### Styling

- **Tailwind CSS utility classes exclusively** — no CSS modules, no styled-components
- Common patterns:
  - Cards: `rounded-3xl border border-gray-200 bg-white shadow-sm`
  - Buttons: `px-3 py-2 rounded-2xl text-sm font-medium shadow-sm`
  - Inputs: `rounded-xl border border-gray-300 px-3 py-2 text-sm`
  - Focus rings: `focus:outline-none focus:ring-2 focus:ring-indigo-500`
- Primary action color: `bg-red-600 hover:bg-red-700 text-white`
- Responsive grid: `grid-cols-2 md:grid-cols-3 lg:grid-cols-4`
- Mobile-friendly collapsible filter bar with scroll-detection

### Python Scripts

- Shebang: `#!/usr/bin/env python3`
- Module docstrings at top of file
- Path manipulation for imports: `sys.path.append(str(Path(__file__).parent / "scraper"))`
- Environment variables for credentials (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` — legacy)
- Destructive operations require confirmation prompts
- Batch processing with progress output
- JSON as interchange format between scripts

---

## Environment Variables

Frontend environment variables use the `VITE_` prefix (required by Vite):

```env
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=dept56-gallery.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=dept56-gallery
VITE_FIREBASE_STORAGE_BUCKET=dept56-gallery.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
```

**NEVER commit** `.env.local`, `firebase-service-account.json`, or any file containing API keys. The `.gitignore` is configured to exclude these. Git pre-commit hooks in `scripts/git/` scan for accidental secret commits.

---

## Development Commands

| Command              | Purpose                                  |
| -------------------- | ---------------------------------------- |
| `npm run dev`        | Start Vite dev server on port 3000       |
| `npm run build`      | Production build to `dist/`              |
| `npm run preview`    | Preview production build locally         |
| `npm run type-check` | Run TypeScript type checking (no emit)   |

### Firebase Deployment

```powershell
npm run build
firebase deploy              # Deploy everything (hosting + rules)
firebase deploy --only hosting   # Deploy just the built site
firebase deploy --only firestore # Deploy Firestore rules + indexes
```

### Vite Dev Server API

The `vite.config.ts` includes a custom plugin (`createImportApiHandler`) that exposes a `/api/import-houses` POST endpoint during development. This endpoint spawns `scripts/bulk_import_scraper.py` as a child process to handle bulk imports. This only works in dev mode.

---

## Key Domain Concepts

- **House**: A Department 56 porcelain building (the primary collectible)
- **Accessory**: A smaller item that accompanies a house (figurines, trees, vehicles, etc.)
- **Collection**: A named grouping (e.g., "North Pole Series", "Dickens Village")
- **Series**: A sub-grouping within a collection
- **SKU**: The manufacturer's item number
- **Released year** (`year`): When the item was first produced
- **Retired year**: When production stopped
- **Purchased year**: When the owner acquired the item
- **House↔Accessory link**: A many-to-many relationship connecting houses with their matching accessories
- **Move between tables**: Items can be reclassified from house→accessory or accessory→house (carries over all metadata and links)

---

## Important Considerations

### Security

- Email whitelist is enforced both client-side and in Firestore rules — keep them in sync
- All Firestore data is publicly readable (collection items are not sensitive)
- Write operations require Google sign-in + whitelisted email
- Firebase service account JSON must never be committed

### Legacy Supabase References

The README and some Python scripts still reference Supabase (the previous backend). The frontend has been fully migrated to Firebase. When updating documentation, prefer Firebase references. The Python admin scripts under `scripts/` still use Supabase credentials and would need updating to use Firebase Admin SDK if they are to be used again.

### Data Quality Features

The app includes built-in data quality tooling:
- **Duplicate detection**: Exact, case-insensitive, and cross-table (house name = accessory name)
- **Unlinked houses filter**: Find houses with no associated accessories
- **Missing photos filter**: Find items without images
- **Move/reclassify**: Move items between the houses and accessories tables
- **Import workflow**: 3-step wizard (enter names → Fuse.js fuzzy match against search index → review/approve with purchase year → batch create)

### Search Index

The file `public/house_search_index.json` is a pre-generated Fuse.js search index built by `scripts/generate_search_index.py`. It's used by the import workflow to match user-entered house names against known Department 56 products. Regenerate it when scraper data changes.

### No CI/CD Pipeline

There are no GitHub Actions workflows. Deployment is manual via `firebase deploy`. The only automated safeguard is the git pre-commit hook for secret detection.

### Monolith Awareness

`DeptApp.tsx` at ~4300 lines is large. When making changes:
- Use targeted searches to find the relevant section
- The file is organized in sections: Utils → UI primitives → Modals → Forms → Cards → Main component (state → handlers → render)
- Test changes thoroughly — there are no automated tests
