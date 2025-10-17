# 🚀 Quick Start Guide

## Get Your Department 56 Gallery App Running in 10 Minutes

### Step 1: Install Dependencies (2 min)
```powershell
npm install
```

### Step 2: Create Supabase Project (3 min)
1. Go to https://supabase.com
2. Click "Start your project" and sign in/sign up
3. Click "New Project"
4. Fill in:
   - Name: `dept56-gallery`
   - Database Password: (create a strong password)
   - Region: (choose closest to you)
5. Click "Create new project" (waits ~2 minutes)

### Step 3: Set Up Database (2 min)
1. Once project is ready, click "SQL Editor" in left sidebar
2. Click "New Query"
3. Open `supabase-schema.sql` file in this project
4. Copy ALL the contents and paste into the SQL editor
5. Click "Run" button
6. ✅ You should see "Success. No rows returned"

### Step 4: Get Your Keys (1 min)
1. Click "Settings" icon in left sidebar
2. Click "API"
3. Copy these two values:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **anon public** key (under "Project API keys")

### Step 5: Configure Environment (1 min)
1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Open `.env` in your editor
3. Paste your values:
   ```
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_ANON_KEY=your-anon-key-here
   ```
4. Save the file

### Step 6: Start the App (1 min)
```powershell
npm run dev
```

### Step 7: Create Your Account
1. Open http://localhost:3000
2. Click "Don't have an account? Sign Up"
3. Enter email and password (min 6 characters)
4. Check your email for confirmation link
5. Click the link to confirm
6. Go back and sign in

## 🎉 You're Done!

Start adding your Department 56 collection!

## 📌 Common Issues

**"Missing Supabase environment variables"**
- Make sure you created `.env` file (not `.env.example`)
- Check that both values are filled in

**"Cannot find module" errors**
- Run `npm install` again

**Confirmation email not arriving**
- Check spam folder
- In Supabase, go to Authentication > URL Configuration
- Make sure "Site URL" is set to `http://localhost:3000`

## 🆘 Need Help?

Check the full `README.md` for detailed documentation and troubleshooting.
