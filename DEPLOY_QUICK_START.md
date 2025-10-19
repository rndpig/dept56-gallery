# 🚀 Quick Deploy to Vercel - Subdomain Setup

**Your app will be at:** `https://dept56.rndpig.com`

---

## ✅ Configuration Complete

Your app is now configured for subdomain deployment:
- ✅ Removed base path from `vite.config.ts`
- ✅ SPA routing configured in `vercel.json`
- ✅ Ready for independent deployment

---

## Deploy Now (5 Steps)

### 1. Deploy to Vercel
- Go to: https://vercel.com/dashboard
- Click: **Add New → Project**
- Import: **`rndpig/dept56-gallery`**
- Click: **Deploy**
- Wait: 1-3 minutes

### 2. Add Custom Domain
In Vercel project:
- **Settings → Domains**
- Add: `dept56.rndpig.com`
- Copy the CNAME value (usually `cname.vercel-dns.com`)

### 3. Configure DNS in GoDaddy
- Go to: https://dcc.godaddy.com/manage/rndpig.com/dns
- Click: **Add**
- Type: **CNAME**
- Name: **dept56**
- Value: **cname.vercel-dns.com**
- TTL: **600**
- Save and wait 10-30 minutes

### 4. Update Supabase
- Go to: https://app.supabase.com
- **Authentication → URL Configuration**
- Site URL: `https://dept56.rndpig.com`
- Redirect URLs: Add `https://dept56.rndpig.com/**`
- **Save**

### 5. Test
Visit: `https://dept56.rndpig.com`
- [ ] Gallery loads
- [ ] Google sign-in works
- [ ] Admin features work

---

## That's It! 🎉

Your app will auto-deploy on every GitHub push.

---

## Future: Add Dashboard at www.rndpig.com

Create a simple HTML page with links to all your apps:
1. New repo: `rndpig-dashboard`
2. Add domain: `www.rndpig.com`
3. GoDaddy CNAME: `www` → `cname.vercel-dns.com`

---

**Need help?** See `VERCEL_DEPLOYMENT.md` for detailed guide.
