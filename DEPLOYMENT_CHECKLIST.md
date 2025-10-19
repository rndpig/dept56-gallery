# Deployment Checklist

**Target URL:** `https://dept56.rndpig.com`

---

## Pre-Deployment
- [x] Code pushed to GitHub
- [x] Vite config updated (base path removed)
- [x] vercel.json configured
- [x] All features working locally

---

## Deployment Steps

### Vercel Setup
- [ ] Go to https://vercel.com/dashboard
- [ ] Import `rndpig/dept56-gallery` from GitHub
- [ ] Deploy and get temporary URL
- [ ] Test temporary URL (sign-in will fail - that's OK)

### Domain Configuration
- [ ] Add domain `dept56.rndpig.com` in Vercel
- [ ] Copy CNAME value from Vercel
- [ ] Add CNAME in GoDaddy DNS:
  - Type: CNAME
  - Name: dept56
  - Value: cname.vercel-dns.com
  - TTL: 600

### DNS Propagation
- [ ] Wait 10-30 minutes
- [ ] Check https://dnschecker.org/ for `dept56.rndpig.com`
- [ ] Confirm domain resolves

### Supabase Configuration
- [ ] Update Site URL to `https://dept56.rndpig.com`
- [ ] Add redirect URL: `https://dept56.rndpig.com/**`
- [ ] Keep localhost URL for development
- [ ] Save changes

---

## Testing

### Public Access (Incognito)
- [ ] Gallery loads at https://dept56.rndpig.com
- [ ] Can browse houses
- [ ] Can browse accessories
- [ ] Filters work
- [ ] Detail modals work
- [ ] Images load
- [ ] No "Manage" tab visible

### Admin Access
- [ ] Sign in with Google works
- [ ] Redirects back successfully
- [ ] "Manage" tab appears
- [ ] Email shown in header

### Admin Features
- [ ] Can edit houses
- [ ] Can edit accessories
- [ ] Can upload photos
- [ ] Can link items
- [ ] Duplicates filter works
- [ ] Unlinked Houses filter works
- [ ] No Photos filter works

### Sign Out
- [ ] Logout button works
- [ ] Returns to Browse view
- [ ] Manage tab disappears

---

## Post-Deployment

- [ ] Update any bookmarks
- [ ] Share URL with family
- [ ] Monitor Vercel logs for any errors
- [ ] Verify auto-deploy works (make a small change and push)

---

## Future Enhancements

- [ ] Create dashboard at www.rndpig.com
- [ ] Add more photos to items
- [ ] Consider adding more family members to whitelist
- [ ] Set up Vercel analytics (optional)

---

**Current Status:** Ready to deploy! ✅

**Next Action:** Go to https://vercel.com/dashboard
