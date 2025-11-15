# Troubleshooting Guide - Site Down & Supabase Pausing

**Date**: November 14, 2025

## Issue #1: Site Down (dept56.rndpig.com)

### Quick Diagnosis Checklist

1. **Check Vercel Status**
   - Go to: https://vercel.com/dashboard
   - Find: `dept56-gallery` project
   - Check: Latest deployment status
   - Look for: Any error messages or warnings

2. **Verify Domain Configuration**
   - In Vercel → Settings → Domains
   - Check `dept56.rndpig.com` status
   - Should show: ✅ Valid Configuration
   - If invalid: Follow Vercel's prompts to fix

3. **Check GoDaddy DNS**
   - Login: https://dcc.godaddy.com
   - Navigate: My Products → Domain (rndpig.com) → DNS
   - Verify CNAME record exists:
     ```
     Type: CNAME
     Name: dept56
     Value: cname.vercel-dns.com
     TTL: 600
     ```

4. **Test DNS Propagation**
   - Go to: https://dnschecker.org/
   - Enter: dept56.rndpig.com
   - Check: Should resolve to Vercel's IP

### Common Fixes

**Fix 1: Force Redeploy**
```bash
# In Vercel Dashboard:
# Deployments → Latest → "..." menu → Redeploy
```

**Fix 2: Re-add Domain**
```bash
# In Vercel Dashboard:
# Settings → Domains → Remove dept56.rndpig.com → Re-add it
```

**Fix 3: Update DNS**
```bash
# Sometimes Vercel's CNAME changes. Check Vercel's domain settings
# for the current CNAME value and update GoDaddy if needed
```

**Fix 4: Clear Vercel Cache**
```bash
# Push a new commit to force rebuild:
git commit --allow-empty -m "Trigger rebuild"
git push origin main
```

---

## Issue #2: Supabase Pausing Free Tier Projects

### Understanding the Issue

**Supabase Free Tier Policy:**
- Projects pause after **7 days of inactivity**
- "Activity" = database queries, API calls, or dashboard access
- Paused projects can be manually restarted
- No data loss, just requires manual restart

### Solution Options

#### **Option A: Upgrade to Pro ($25/month)**
**Pros:**
- No pausing ever
- Better performance
- More storage (8GB → 100GB)
- More bandwidth
- Priority support

**Cons:**
- Costs $25/month

**Best for:** Production apps with users

---

#### **Option B: GitHub Actions Keep-Alive (FREE!)**
**Automated solution using GitHub Actions**

**Setup Steps:**

1. **Add Secrets to GitHub:**
   - Go to: GitHub repo → Settings → Secrets and variables → Actions
   - Click: "New repository secret"
   - Add these secrets:
     ```
     Name: SUPABASE_URL
     Value: https://gxabjmvtzxslojsgawdh.supabase.co
     
     Name: SUPABASE_ANON_KEY
     Value: [Your Supabase anon key from project settings]
     ```

2. **Commit the Workflow:**
   ```bash
   cd "c:\Users\rndpi\Documents\Coding Projects\dept56-gallery"
   git add .github/workflows/keep-alive.yml
   git commit -m "Add Supabase keep-alive workflow"
   git push origin main
   ```

3. **Verify Setup:**
   - Go to: GitHub repo → Actions tab
   - Should see: "Keep Supabase Active" workflow
   - Click: "Run workflow" to test manually
   - Check: Logs to verify it worked

4. **Automated Schedule:**
   - Runs automatically every 6 days
   - No manual intervention needed
   - Free (within GitHub Actions free tier)

**Pros:**
- Completely free
- Fully automated
- No maintenance needed
- Runs in GitHub's cloud

**Cons:**
- Requires GitHub secrets setup (one-time)
- Depends on GitHub Actions availability

**Best for:** Personal projects, hobby apps

---

#### **Option C: Manual Script (Fallback)**
**Use the Python script with Windows Task Scheduler**

**Setup Steps:**

1. **Configure the Script:**
   - Open: `scripts/keep_alive.py`
   - Replace `SUPABASE_URL` with your actual URL
   - Replace `SUPABASE_KEY` with your anon key
   - Save the file

2. **Test the Script:**
   ```powershell
   cd "c:\Users\rndpi\Documents\Coding Projects\dept56-gallery"
   python scripts/keep_alive.py
   ```

3. **Set Up Task Scheduler:**
   - Open: Task Scheduler (Windows)
   - Create: New Basic Task
   - Name: "Supabase Keep-Alive"
   - Trigger: Weekly, every 6 days
   - Action: Start a program
     - Program: `python`
     - Arguments: `C:\Users\rndpi\Documents\Coding Projects\dept56-gallery\scripts\keep_alive.py`
   - Save and test

**Pros:**
- Full control
- Runs on your computer

**Cons:**
- Computer must be on
- Not fully automated
- More setup required

**Best for:** If GitHub Actions doesn't work

---

### Recommended Approach

**For your situation, I recommend:**

1. **Short term (Today):**
   - Fix the site down issue using Vercel dashboard
   - Manually restart Supabase if paused (just visit dashboard)

2. **Long term (This week):**
   - Set up GitHub Actions keep-alive (Option B)
   - It's free, automated, and reliable
   - Takes 5 minutes to configure

3. **Future consideration:**
   - If you get more users or want guaranteed uptime
   - Consider upgrading to Supabase Pro
   - $25/month is reasonable for a production app

---

## Quick Commands

### Check if site is down:
```powershell
# Test from command line:
curl -I https://dept56.rndpig.com
```

### Force Vercel rebuild:
```bash
cd "c:\Users\rndpi\Documents\Coding Projects\dept56-gallery"
git commit --allow-empty -m "Force rebuild"
git push origin main
```

### Test keep-alive script:
```bash
cd "c:\Users\rndpi\Documents\Coding Projects\dept56-gallery"
python scripts/keep_alive.py
```

---

## Next Steps

1. **Fix site down:**
   - [ ] Check Vercel dashboard
   - [ ] Verify domain configuration
   - [ ] Force redeploy if needed

2. **Prevent Supabase pausing:**
   - [ ] Set up GitHub Actions keep-alive
   - [ ] Add secrets to GitHub repo
   - [ ] Test the workflow manually
   - [ ] Verify it runs automatically

3. **Monitor:**
   - [ ] Check site is back up
   - [ ] Verify GitHub Action runs successfully
   - [ ] Confirm Supabase stays active

---

## Support Resources

- **Vercel Dashboard**: https://vercel.com/dashboard
- **Vercel Docs**: https://vercel.com/docs
- **Supabase Dashboard**: https://app.supabase.com
- **Supabase Pausing Docs**: https://supabase.com/docs/guides/platform/going-into-prod
- **GitHub Actions**: https://github.com/[your-username]/dept56-gallery/actions
