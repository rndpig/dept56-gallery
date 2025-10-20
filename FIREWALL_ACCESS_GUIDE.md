# 🔒 Firewall & Network Access Guide

## For Family Members: If the Site Won't Load

If you're trying to access **dept56.rndpig.com** and it won't load, your home network's security system (like Eero, Circle, Norton, etc.) might be blocking it. This is a **false positive** - the site is safe!

### Why It Gets Blocked

The app uses cloud services (Supabase) for the database, which some security systems incorrectly flag as suspicious. This is common for new websites using modern cloud infrastructure.

### How to Fix It

#### If You Have Eero:
1. Open the **Eero app**
2. Tap **Discover** → **eero Secure**
3. Tap **Blocked Content**
4. Find **rndpig.com** or **supabase.co** in the list
5. Tap on it and select **"Don't Block This Site"**
6. Or add to **Allowed websites** list:
   - `rndpig.com`
   - `dept56.rndpig.com`
   - `supabase.co`

#### If You Have Circle (Disney):
1. Open **Circle app**
2. Go to **Settings** → **Filter Settings**
3. Add to **Allowed Sites**:
   - `rndpig.com`
   - `supabase.co`

#### If You Have Norton Family:
1. Log in to **Norton Family** website
2. Select your child's profile
3. Go to **Web Supervision**
4. Click **Add site to allow list**
5. Add: `rndpig.com` and `supabase.co`

#### General Router/Firewall:
1. Log into your router admin panel (usually `192.168.1.1` or `192.168.0.1`)
2. Look for **Parental Controls** or **Security Settings**
3. Add to whitelist/allowed sites
4. Or temporarily disable security to test

#### Quick Test:
Try accessing on **mobile data** (not WiFi):
- If it works on cellular but not WiFi → network is blocking it
- If it doesn't work anywhere → different issue

### Still Not Working?

Try these in order:
1. **Use a different browser** (Chrome, Safari, Firefox)
2. **Clear browser cache** (Settings → Privacy → Clear browsing data)
3. **Try incognito/private mode**
4. **Restart your device**
5. **Contact the site admin** if still blocked

---

## For Network Administrators

### Domains to Whitelist

If you're managing a network firewall, whitelist these domains:

```
rndpig.com
*.rndpig.com
dept56.rndpig.com
supabase.co
*.supabase.co
xctottgirqkkmjmutoon.supabase.co
accounts.google.com (for sign-in)
```

### Why This Site Uses These Services

- **rndpig.com**: Main domain (hosted on Vercel)
- **supabase.co**: Legitimate cloud database service (PostgreSQL backend)
- **Google OAuth**: Authentication for admin access

### Security Information

- ✅ Site uses HTTPS encryption
- ✅ No ads or tracking
- ✅ Private family collection database
- ✅ Row-level security on all data
- ✅ Google OAuth for admin authentication
- ✅ Open source React application

### False Positive Triggers

Your security system may flag this because:
1. Supabase subdomain looks auto-generated (it is, but it's legitimate)
2. Multiple cross-origin API calls (normal for modern web apps)
3. New domain without established reputation
4. OAuth redirect chain (normal for authentication)

This is a **false positive**. The site is safe for your network.

---

## For Site Owner (You)

### Options to Reduce Blocking

1. **Custom Domain for Supabase** (Advanced):
   - Set up `api.rndpig.com` pointing to Supabase
   - Reduces suspicion of random subdomain
   - Requires custom domain setup in Supabase

2. **Add to Common Whitelists**:
   - Submit to browser safe lists
   - Add to Google Safe Browsing
   - Register with security vendors

3. **Documentation**:
   - Include this guide in README
   - Send to family members proactively
   - Create a troubleshooting page

4. **Monitor**:
   - Check which networks block access
   - Document patterns
   - Consider alternative hosting if needed

---

## Quick Reference Card (Share This)

**Can't access dept56.rndpig.com?**

1. Check if your network has parental controls or security software
2. Add `rndpig.com` and `supabase.co` to allowed sites
3. Try on mobile data to confirm it's a network block
4. Contact network admin or site owner for help

**The site is safe!** It's a private family photo collection. Your security system is being overly cautious.
