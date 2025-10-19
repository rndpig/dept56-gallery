# Adding Environment Variables to Vercel

## Quick Method: Copy/Paste from File

I've created a `vercel.env` file in your project with your Supabase credentials.

### Step 1: Open the File
Open `vercel.env` in your project (it's in the root directory)

### Step 2: Copy the Contents
Copy these two lines:
```
VITE_SUPABASE_URL=https://xctottgirqkkmjmutoon.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhjdG90dGdpcnFra21qbXV0b29uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA1NTQ5ODUsImV4cCI6MjA3NjEzMDk4NX0.ioIkzka-s1N5UKH8Ds8ZXug6CUT6vVXH4_00G9XuoJI
```

### Step 3: Import to Vercel

**Option A: Paste Each Variable (Easiest)**
1. Go to: Vercel Dashboard → dept56-gallery → Settings → Environment Variables
2. For **VITE_SUPABASE_URL**:
   - Click "Add New"
   - Key: `VITE_SUPABASE_URL`
   - Value: `https://xctottgirqkkmjmutoon.supabase.co`
   - Select: Production, Preview, Development (all three)
   - Click "Save"

3. For **VITE_SUPABASE_ANON_KEY**:
   - Click "Add New"
   - Key: `VITE_SUPABASE_ANON_KEY`
   - Value: (paste the long key)
   - Select: Production, Preview, Development (all three)
   - Click "Save"

**Option B: Bulk Import (If Available)**
1. Look for "Import .env" or "Bulk Add" button
2. Paste all contents from `vercel.env`
3. Make sure all are assigned to Production, Preview, Development

---

## Step 4: Redeploy

After adding the variables:

1. Go to: **Deployments** tab
2. Find your latest deployment
3. Click the **three dots (...)** menu
4. Click **"Redeploy"**

Or just push a small change to trigger automatic deployment:

```powershell
cd "C:\Users\rndpi\Documents\Coding Projects\Dept 56 gallery app"
git commit --allow-empty -m "Trigger redeploy with env vars"
git push
```

---

## Verification

After redeployment:
- Visit `https://dept56.rndpig.com`
- Open browser console (F12)
- The error should be gone!
- The gallery should load correctly

---

## What These Variables Do

- **VITE_SUPABASE_URL**: Tells your app where your Supabase database is
- **VITE_SUPABASE_ANON_KEY**: Public key that allows read access (safe to expose)

These are NOT secret - they're meant to be public and are already in your frontend JavaScript. Row Level Security in Supabase controls what users can actually do.

---

## Troubleshooting

### Still getting the error after redeploy?
- Verify both variables are added in Vercel
- Check they're assigned to "Production"
- Try a hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Check Vercel deployment logs for any build errors

### Can't find Environment Variables in Vercel?
- Make sure you're in the right project (dept56-gallery)
- Look under: Settings → Environment Variables (left sidebar)

---

**Quick Link:** https://vercel.com/rndpig/dept56-gallery/settings/environment-variables
