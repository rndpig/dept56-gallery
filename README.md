# Department 56 Gallery App

A beautiful web application for managing and displaying your Department 56 porcelain house and accessories collection, powered by React and Supabase.

## ✨ Features

- 🏠 **House & Accessory Management** - Add, edit, and organize your collection
- 📸 **Photo Upload** - Store images in Supabase Storage with automatic optimization
- 🏷️ **Collections & Tags** - Organize items with custom collections and tags
- 🔗 **Relationships** - Link accessories to houses with many-to-many relationships
- 🔍 **Fuzzy Search** - Smart search across names, collections, and tags
- 📅 **Purchase Tracking** - Track purchase dates and years
- 🔐 **Authentication** - Secure user authentication with Supabase Auth
- 🔒 **Row Level Security** - Your data is private and protected
- 📱 **Responsive Design** - Works beautifully on desktop and mobile

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ installed
- A Supabase account (free tier works great!)
- npm or yarn package manager

### Step 1: Clone or Set Up the Project

If you haven't already, navigate to your project directory:

```powershell
cd "C:\Users\rndpi\Documents\Coding Projects\Dept 56 gallery app"
```

### Step 2: Install Dependencies

```powershell
npm install
```

This will install:
- React 18
- Supabase JS Client
- Vite (build tool)
- TypeScript
- Tailwind CSS
- And all other dependencies

### Step 3: Set Up Supabase Project

1. **Create a Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Click "Start your project"
   - Create a new organization (if needed)
   - Click "New Project"
   - Choose a name (e.g., "dept56-gallery")
   - Set a strong database password
   - Select a region close to you
   - Click "Create new project" (takes ~2 minutes)

2. **Run the Database Migration**
   - Once your project is ready, go to the SQL Editor
   - Click "New Query"
   - Copy the entire contents of `supabase-schema.sql` from this project
   - Paste it into the SQL editor
   - Click "Run" to execute the migration
   - This creates all tables, relationships, indexes, RLS policies, and storage buckets

3. **Get Your API Keys**
   - Go to Settings > API
   - Copy your `Project URL`
   - Copy your `anon` `public` key

### Step 4: Configure Environment Variables

1. Copy the example environment file:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` and add your Supabase credentials:
   ```env
   VITE_SUPABASE_URL=https://your-project-ref.supabase.co
   VITE_SUPABASE_ANON_KEY=your-anon-key-here
   ```

### Step 5: Start the Development Server

```powershell
npm run dev
```

Your app will be available at http://localhost:3000

### Step 6: Create an Account

1. Open http://localhost:3000 in your browser
2. Click "Don't have an account? Sign Up"
3. Enter your email and password (minimum 6 characters)
4. Check your email for the confirmation link
5. Click the confirmation link
6. Return to the app and sign in

## 📦 Project Structure

```
dept-56-gallery-app/
├── src/                         # React application source code
│   ├── components/
│   │   └── Auth.tsx            # Authentication component
│   ├── lib/
│   │   ├── supabase.ts         # Supabase client initialization
│   │   └── database.ts         # Database service layer (CRUD operations)
│   ├── types/
│   │   └── database.ts         # TypeScript type definitions
│   ├── App.tsx                 # Main app with auth wrapper
│   ├── DeptApp.tsx             # Main gallery component
│   ├── main.tsx                # React entry point
│   └── index.css               # Global styles
├── scripts/                     # Utility scripts (see scripts/README.md)
│   ├── data-ingestion/         # Import data from Word docs
│   ├── scraping/               # Web scraping tools
│   └── maintenance/            # Database maintenance utilities
├── supabase-schema.sql         # Database migration script
├── index.html                  # HTML entry point
├── vite.config.ts              # Vite configuration
├── tsconfig.json               # TypeScript configuration
├── tailwind.config.js          # Tailwind CSS configuration
├── postcss.config.js           # PostCSS configuration
├── package.json                # Dependencies and scripts
├── .env.example                # Environment variable template
└── .env                        # Environment variables (create from .env.example)
```

## 🔧 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run type-check` - Run TypeScript type checking

## 🗄️ Database Schema

The app uses the following main tables:

- **houses** - Porcelain houses with photos, years, notes, and purchase info
- **accessories** - Accessories with photos, notes, and purchase info
- **collections** - Custom collections to organize items
- **tags** - Tags for categorization (supports manual and ML tags)
- **house_accessory_links** - Many-to-many relationships between houses and accessories
- **house_collections** - Links houses to collections
- **accessory_collections** - Links accessories to collections
- **house_tags** - Links houses to tags
- **accessory_tags** - Links accessories to tags

All tables include Row Level Security (RLS) policies to ensure users can only access their own data.

## 📸 Image Storage

Images are stored in Supabase Storage in the `dept56-images` bucket:

- **Path structure**: `{user_id}/{timestamp}-{random}.{ext}`
- **Public access**: Yes (but scoped to authenticated users)
- **Storage policies**: Users can only upload/view/delete their own images

## 🔐 Security Features

1. **Row Level Security (RLS)** - All database tables are protected
2. **Authentication** - Supabase Auth with email/password
3. **Storage Policies** - Users can only access their own images
4. **Environment Variables** - API keys stored securely in `.env` (never committed)

## �️ Utility Scripts

The `scripts/` directory contains utilities for data management and maintenance:

- **data-ingestion/** - Import data from Word documents
- **scraping/** - Web scraping tools for Department 56 product data
- **maintenance/** - Database maintenance (duplicate detection, cleanup)

For detailed usage instructions, see [scripts/README.md](scripts/README.md).

## �🚢 Deployment

### Deploy to Vercel (Recommended)

1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Click "New Project"
4. Import your GitHub repository
5. Add environment variables:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
6. Click "Deploy"

### Deploy to Netlify

1. Push your code to GitHub
2. Go to [netlify.com](https://netlify.com)
3. Click "Add new site" > "Import an existing project"
4. Connect to GitHub and select your repository
5. Build settings:
   - Build command: `npm run build`
   - Publish directory: `dist`
6. Add environment variables in Site settings > Build & deploy > Environment
7. Deploy

## 🎨 Customization

### Changing Colors

Edit `tailwind.config.js` to customize the color scheme:

```js
theme: {
  extend: {
    colors: {
      primary: '#your-color-here',
    }
  }
}
```

### Modifying the Schema

To add new fields or tables:

1. Update `supabase-schema.sql` with your changes
2. Run the new SQL in Supabase SQL Editor
3. Update TypeScript types in `src/types/database.ts`
4. Update database service functions in `src/lib/database.ts`

## 📝 Migration from LocalStorage

If you have existing data in the localStorage version:

1. Open the old version of the app
2. Click "Export JSON" to download your data
3. The export will include all houses, accessories, collections, tags, and links
4. *Note: You'll need to write a migration script to convert localStorage IDs to UUID format and upload to Supabase*

## 🐛 Troubleshooting

### Site Won't Load / Network Blocking
**If the site won't load on your home network:**

Your network's security system (Eero, Circle, Norton, etc.) might be blocking the site. This is a **false positive** - the site is safe!

**Quick Fix:**
1. Add `rndpig.com` and `supabase.co` to your security system's allowed/trusted sites list
2. Test on mobile data (not WiFi) to confirm it's a network block
3. See [FIREWALL_ACCESS_GUIDE.md](FIREWALL_ACCESS_GUIDE.md) for detailed instructions

**Why it happens:** The app uses Supabase cloud services, which some security systems incorrectly flag as suspicious. This is common for new sites using modern cloud infrastructure.

### "Cannot find module" errors
Run `npm install` to ensure all dependencies are installed.

### "Missing Supabase environment variables"
Make sure you created `.env` file and added your Supabase URL and anon key.

### "Invalid API key"
Double-check that you copied the `anon` key from Supabase Settings > API.

### Images not uploading
1. Verify the `dept56-images` bucket exists in Supabase Storage
2. Check that storage policies were created (run the SQL migration again if needed)
3. Ensure you're authenticated (sign out and sign back in)

### RLS Policy Errors
If you get "Row Level Security" errors, re-run the `supabase-schema.sql` file in the SQL Editor.

## 📚 Resources

- [Supabase Documentation](https://supabase.com/docs)
- [React Documentation](https://react.dev)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Vite Documentation](https://vitejs.dev)

## 📄 License

Private project - All rights reserved.

## 🙏 Support

For issues or questions, refer to:
- [Supabase Discord](https://discord.supabase.com)
- [React Community](https://react.dev/community)

---

Built with ❤️ using React, TypeScript, Supabase, and Tailwind CSS
