# Google OAuth Authentication Setup Guide

This guide will help you enable Google OAuth authentication for your Department 56 gallery app with admin-only editing capabilities.

## Overview

**Security Model:**
- ✅ **Public browsing** - Anyone can view the collection
- 🔒 **Admin-only editing** - Only whitelisted Gmail accounts can manage items
- 🎯 **Email whitelist** - Currently configured for: `rndpig@gmail.com`

## Step 1: Enable Google OAuth in Supabase

### 1.1 Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth client ID**
5. If prompted, configure the OAuth consent screen:
   - Choose **External** (unless you have a Google Workspace)
   - Fill in app name: "Department 56 Gallery"
   - Add your email as support email
   - Skip scopes (default is fine)
   - Add test users: `rndpig@gmail.com` (and any other family members)
6. For Application type, select **Web application**
7. Add authorized redirect URIs:
   ```
   https://[YOUR-PROJECT-REF].supabase.co/auth/v1/callback
   ```
   Replace `[YOUR-PROJECT-REF]` with your actual Supabase project reference
   (Find it in your Supabase project URL: `https://app.supabase.com/project/[YOUR-PROJECT-REF]`)

8. Click **Create** and save your:
   - **Client ID**
   - **Client Secret**

### 1.2 Configure Supabase

1. Go to your [Supabase Dashboard](https://app.supabase.com)
2. Select your Department 56 project
3. Navigate to **Authentication** > **Providers**
4. Find **Google** in the list and click to enable it
5. Enter your Google OAuth credentials:
   - **Client ID**: Paste the Client ID from Google
   - **Client Secret**: Paste the Client Secret from Google
6. Click **Save**

### 1.3 Configure Site URL (Important!)

1. Still in **Authentication** settings
2. Go to **URL Configuration**
3. Set your **Site URL** to your app's URL:
   - Local development: `http://localhost:3000`
   - Production: `https://your-domain.com`
4. Add **Redirect URLs** (same as site URL)
5. Click **Save**

## Step 2: Update RLS Policies

### 2.1 Run SQL Script

1. In Supabase Dashboard, go to **SQL Editor**
2. Click **New query**
3. Copy the entire contents of `setup_auth_rls_policies.sql`
4. Paste into the SQL editor
5. Click **Run** or press `Ctrl+Enter`
6. Verify all policies were created successfully (check for green checkmarks)

### 2.2 Configure Storage Bucket Policies

1. Go to **Storage** in your Supabase Dashboard
2. Click on the **dept56-images** bucket
3. Click the **Policies** tab
4. Click **New Policy**

**Create 4 policies:**

#### Policy 1: Public Read Access
- **Name**: Public read access to images
- **Allowed operation**: SELECT
- **Policy definition**: Use this SQL
  ```sql
  true
  ```
- Click **Review** then **Save policy**

#### Policy 2: Authenticated Upload
- **Name**: Authenticated users can upload images
- **Allowed operation**: INSERT
- **Policy definition**: Use this SQL
  ```sql
  (auth.role() = 'authenticated'::text)
  ```
- Click **Review** then **Save policy**

#### Policy 3: Authenticated Update
- **Name**: Authenticated users can update images
- **Allowed operation**: UPDATE
- **Policy definition**: Use this SQL
  ```sql
  (auth.role() = 'authenticated'::text)
  ```
- Click **Review** then **Save policy**

#### Policy 4: Authenticated Delete
- **Name**: Authenticated users can delete images
- **Allowed operation**: DELETE
- **Policy definition**: Use this SQL
  ```sql
  (auth.role() = 'authenticated'::text)
  ```
- Click **Review** then **Save policy**

## Step 3: Test the Setup

### 3.1 Test Public Browsing (No Auth)

1. Open your app in an incognito/private window
2. Verify you can:
   - ✅ See the Browse tab
   - ✅ Use all filters
   - ✅ View house and accessory details
   - ✅ See all images
3. Verify you CANNOT:
   - ❌ See the Manage tab
   - ❌ See any edit buttons

### 3.2 Test Admin Login

1. In a normal browser window, click **Sign in with Google**
2. Sign in with `rndpig@gmail.com`
3. You should be redirected back to the app
4. Verify you can now:
   - ✅ See the Manage tab
   - ✅ See your email in the header
   - ✅ Edit houses and accessories
   - ✅ Upload photos
   - ✅ Use all management features
5. Click **Logout** to test sign out

### 3.3 Test Non-Whitelisted User

1. Sign in with a different Gmail account (not in the whitelist)
2. Verify they:
   - ✅ Can browse normally
   - ❌ Cannot see the Manage tab
   - ❌ Cannot access admin features
3. If they try to access `/manage`, they should see "Admin Access Required"

## Step 4: Adding More Admin Users

To add family members to the admin whitelist:

1. Open `src/DeptApp.tsx`
2. Find the `ALLOWED_ADMIN_EMAILS` constant (near the top)
3. Add their Gmail addresses:
   ```typescript
   const ALLOWED_ADMIN_EMAILS = [
     "rndpig@gmail.com",
     "familymember@gmail.com",  // Add here
     "another@gmail.com",        // Add here
   ];
   ```
4. Save the file
5. Redeploy your app

**Important:** Make sure to add these emails as **test users** in your Google OAuth consent screen (Step 1.1.5) if your app is in testing mode.

## Step 5: Deploy to Production

### For Netlify/Vercel:

1. Update your production Site URL in Supabase (Step 1.3)
2. Add production redirect URL to Google OAuth (Step 1.1.7)
3. Push your code changes
4. Your hosting platform will auto-deploy

### Environment Variables:

No additional environment variables needed! All Supabase config is in `src/lib/supabase.ts`.

## Troubleshooting

### "Failed to save: new row violates row-level security policy"
- **Cause**: RLS policies not applied correctly
- **Fix**: Re-run `setup_auth_rls_policies.sql` in Supabase SQL Editor
- **Fix**: Check storage bucket policies are created

### Photo upload fails after login
- **Cause**: Storage bucket policies missing
- **Fix**: Follow Step 2.2 to create all 4 storage policies

### Google sign-in redirects to wrong URL
- **Cause**: Site URL misconfigured
- **Fix**: Update Site URL in Supabase Authentication settings (Step 1.3)
- **Fix**: Update authorized redirect URIs in Google Cloud Console

### Non-admin user sees Manage tab briefly
- **Cause**: Normal behavior - React checks auth state and hides it
- **Fix**: No action needed, UI will update in ~100ms

### "Sign in with Google" button doesn't work
- **Cause**: Google OAuth not enabled or misconfigured
- **Fix**: Double-check Client ID and Client Secret in Supabase
- **Fix**: Verify redirect URI in Google Cloud Console matches your Supabase project

## Security Notes

- **Email whitelist is code-based**: Admin emails are hardcoded in the app. This is intentional for a small family app.
- **Public reads are safe**: All RLS policies allow public SELECT operations. Your collection data is public by design.
- **No user registration**: Users cannot self-register. Only whitelisted Gmail accounts have admin access.
- **Google handles auth**: Supabase uses Google's OAuth, so passwords are never stored in your app.

## Success Checklist

Before going live, verify:

- [ ] Google OAuth credentials created
- [ ] Supabase Google provider enabled with credentials
- [ ] Site URL configured correctly
- [ ] All RLS policies created (run SQL script)
- [ ] All 4 storage bucket policies created
- [ ] Test public browsing (incognito)
- [ ] Test admin login with rndpig@gmail.com
- [ ] Test photo upload while authenticated
- [ ] Test logout
- [ ] Test non-whitelisted user (if available)

## Next Steps

Once setup is complete:
1. Add photo to "All Clear for Take Off" accessory
2. Test all management features
3. Add family member emails to whitelist
4. Deploy to production
5. Share public URL with family

## Support

If you encounter issues:
1. Check browser console for error messages
2. Check Supabase logs: Dashboard > Logs
3. Verify all steps completed in order
4. Try clearing browser cache/cookies
