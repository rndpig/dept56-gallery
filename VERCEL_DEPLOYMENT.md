# Vercel Deployment Guide - Department 56 Gallery

## Overview
This guide will help you deploy your Department 56 gallery app to Vercel and configure it to be accessible at `https://www.rndpig.com/dept56`.

---

## Part 1: Deploy to Vercel

### Step 1: Connect GitHub Repository to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Click **"Import Git Repository"**
4. Find and select **`rndpig/dept56-gallery`** from your GitHub repositories
5. Click **"Import"**

### Step 2: Configure Project Settings

On the import screen, configure these settings:

**Framework Preset:** Vite  
**Build Command:** `npm run build`  
**Output Directory:** `dist`  
**Install Command:** `npm install`

**Environment Variables:** (Add these by clicking "Environment Variables")
- You don't need to add Supabase keys here since they're already in your code (`src/lib/supabase.ts`)

### Step 3: Deploy

1. Click **"Deploy"**
2. Wait for the build to complete (1-3 minutes)
3. Once deployed, Vercel will give you a URL like: `https://dept56-gallery-xxxx.vercel.app`
4. Test this URL to make sure everything works

**Important:** After deployment, you'll need to update Supabase settings (see Part 3 below).

---

## Part 2: Custom Domain Setup with GoDaddy

### Step 1: Add Custom Domain in Vercel

1. In your Vercel project dashboard, go to **Settings** → **Domains**
2. Click **"Add"**
3. Enter: `www.rndpig.com`
4. Vercel will show you DNS configuration options
5. Choose **"Add both www.rndpig.com and rndpig.com"** if you want both to work
6. Vercel will provide you with DNS records to add

### Step 2: Get DNS Configuration from Vercel

Vercel will show you one of these configurations:

**Option A: CNAME Record (Recommended)**
```
Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

**Option B: A Record**
```
Type: A
Name: www
Value: 76.76.21.21
```

**For the root domain (rndpig.com):**
```
Type: A
Name: @
Value: 76.76.21.21
```

### Step 3: Configure DNS in GoDaddy

1. Log in to [GoDaddy](https://www.godaddy.com/)
2. Go to **My Products** → **Domain Name** → Click on **rndpig.com** → **DNS**
3. You'll see your existing DNS records

**For www subdomain:**
- Click **"Add"**
- Type: **CNAME**
- Name: **www**
- Value: **cname.vercel-dns.com** (or the value Vercel provided)
- TTL: **600 seconds** (10 minutes)
- Click **"Save"**

**For root domain (optional, if you want rndpig.com to also work):**
- Click **"Add"**
- Type: **A**
- Name: **@**
- Value: **76.76.21.21** (or the IP Vercel provided)
- TTL: **600 seconds**
- Click **"Save"**

### Step 4: Wait for DNS Propagation

- DNS changes can take **5 minutes to 48 hours** to propagate
- Typically happens within **10-30 minutes** with GoDaddy
- You can check status at: https://dnschecker.org/

---

## Part 3: Configure Subdirectory (/dept56)

### Current Setup
Your app is now configured to work at the `/dept56` subdirectory with these files:
- `vite.config.ts` → `base: '/dept56/'`
- `vercel.json` → routing configuration

### Two Deployment Options:

#### Option A: Deploy to Subdirectory (Multiple Projects)
**Use this if you want different Vercel projects for each app.**

1. Your dept56 app will be at: `https://www.rndpig.com/dept56`
2. Each app gets its own Vercel project
3. You'll need to set up path-based routing (see below)

**Path-Based Routing Setup:**
This requires either:
- A separate Vercel project for your dashboard at the root
- Using Vercel's monorepo features
- Setting up redirects in your root project

#### Option B: Deploy to Subdomain (Recommended)
**Use this if you want clean URLs for each app.**

Instead of `/dept56`, use: `https://dept56.rndpig.com`

**Benefits:**
- Each app is independent
- Easier to manage
- No path conflicts
- Better for multiple apps

**To switch to subdomain approach:**
1. In Vercel, add domain: `dept56.rndpig.com`
2. In GoDaddy, add CNAME:
   ```
   Type: CNAME
   Name: dept56
   Value: cname.vercel-dns.com
   ```
3. Remove the `base: '/dept56/'` from `vite.config.ts`:
   ```typescript
   export default defineConfig({
     plugins: [react()],
     // base: '/dept56/', // Remove this line
     server: {
       port: 3000,
     },
   })
   ```

---

## Part 4: Update Supabase Settings

After your domain is live, you MUST update Supabase:

### Step 1: Update Site URL

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **Authentication** → **URL Configuration**
4. Update **Site URL** to:
   - If using subdirectory: `https://www.rndpig.com/dept56`
   - If using subdomain: `https://dept56.rndpig.com`
5. Add to **Redirect URLs**:
   - `https://www.rndpig.com/dept56`
   - `https://dept56.rndpig.com` (if using subdomain)
   - `http://localhost:3000` (keep for local development)
6. Click **"Save"**

### Step 2: Update Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Click on your OAuth 2.0 Client ID
4. Under **Authorized redirect URIs**, add:
   ```
   https://[YOUR-SUPABASE-PROJECT].supabase.co/auth/v1/callback
   ```
5. Click **"Save"**

---

## Part 5: Testing Checklist

After deployment, test these features:

- [ ] **Public browsing** (incognito window)
  - Can view houses and accessories
  - Filters work
  - Search works
  - Detail modals work
  
- [ ] **Google Sign-in** (with rndpig@gmail.com)
  - Sign in button works
  - Redirects back to app after auth
  - Manage tab appears
  
- [ ] **Admin Features**
  - Can edit houses and accessories
  - Can upload photos
  - Can link items
  - Can use special filters (Duplicates, Unlinked Houses, No Photos)
  
- [ ] **Sign Out**
  - Logout button works
  - Returns to public view

---

## Part 6: Future Dashboard Setup

For your main dashboard at `https://www.rndpig.com`:

### Option 1: Simple HTML Dashboard
Create a simple `index.html` in a new repository:

```html
<!DOCTYPE html>
<html>
<head>
    <title>RNDPig Apps</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
        .app-link { display: block; padding: 20px; margin: 10px 0; background: #f0f0f0; border-radius: 8px; text-decoration: none; color: #333; }
        .app-link:hover { background: #e0e0e0; }
    </style>
</head>
<body>
    <h1>Welcome to RNDPig Apps</h1>
    <a href="/dept56" class="app-link">
        <h2>🏠 Department 56 Gallery</h2>
        <p>Browse and manage my Department 56 collection</p>
    </a>
    <!-- Add more apps here in the future -->
</body>
</html>
```

### Option 2: Vercel Monorepo
Use Vercel's monorepo features to host multiple projects under one domain.

---

## Troubleshooting

### Issue: "Page Not Found" on Custom Domain
**Solution:** 
- Check DNS propagation at https://dnschecker.org/
- Verify DNS records in GoDaddy match Vercel's requirements
- Wait up to 48 hours for full propagation

### Issue: Google Sign-in Fails
**Solution:**
- Verify Site URL in Supabase matches your domain
- Check Google OAuth redirect URIs include your Supabase callback URL
- Clear browser cookies and try again

### Issue: Images Not Loading
**Solution:**
- Check that Supabase storage bucket policies are set (see `GOOGLE_AUTH_SETUP.md`)
- Verify images are using full URLs, not relative paths

### Issue: 404 on Page Refresh
**Solution:**
- Verify `vercel.json` has the rewrite rules
- Check that SPA routing is enabled in Vercel

### Issue: Assets Not Loading (CSS/JS 404)
**Solution:**
- Verify `base: '/dept56/'` is in `vite.config.ts` if using subdirectory
- Or remove it if using subdomain

---

## Recommended Approach

For the cleanest setup with multiple future apps:

1. **Use subdomains** instead of subdirectories:
   - `dept56.rndpig.com` → Department 56 Gallery
   - `app2.rndpig.com` → Future App 2
   - `www.rndpig.com` → Dashboard

2. **Benefits:**
   - Each app is independent
   - No routing conflicts
   - Easier to manage
   - Professional URLs

3. **Implementation:**
   - Remove `base: '/dept56/'` from `vite.config.ts`
   - Deploy as separate Vercel project
   - Add subdomain in Vercel: `dept56.rndpig.com`
   - Add CNAME in GoDaddy: `dept56` → `cname.vercel-dns.com`

---

## Quick Reference

### Vercel Dashboard URLs
- Project Settings: `https://vercel.com/[username]/dept56-gallery/settings`
- Domains: `https://vercel.com/[username]/dept56-gallery/settings/domains`
- Deployments: `https://vercel.com/[username]/dept56-gallery/deployments`

### DNS Configuration
- GoDaddy DNS Management: `https://dcc.godaddy.com/manage/[domain]/dns`
- DNS Checker: `https://dnschecker.org/`

### Supabase Configuration
- Dashboard: `https://app.supabase.com/project/[project-id]`
- Authentication Settings: `Authentication → URL Configuration`
- Storage Policies: `Storage → dept56-images → Policies`

---

## Support

If you encounter issues:
1. Check Vercel deployment logs
2. Check browser console for errors
3. Verify all URLs in Supabase match your deployment
4. Test with incognito window to rule out cache issues
