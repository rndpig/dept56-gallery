# Mobile Debugging Guide - Dept56 Gallery

## Issue: Site Appears Down on Mobile but Works on Desktop

### Symptoms
- Desktop browser: Site loads normally
- Mobile browsers (especially iOS Safari): Stuck on "Loading your collection..." screen
- No visible error messages
- Console logs not accessible on mobile

## Root Causes Identified

### 1. **Authentication Check Hanging**
The app performs authentication checks on startup that may timeout or hang on mobile browsers due to:
- Stricter security policies on mobile Safari
- Third-party cookie restrictions
- Network differences between mobile and WiFi

### 2. **Supabase Connection Issues**
Mobile browsers may have issues connecting to Supabase due to:
- Cross-origin restrictions
- Service worker limitations
- Aggressive caching policies

### 3. **Missing Timeout Mechanisms**
The original code had no timeout for:
- Authentication checks
- Data fetching operations
- This causes infinite loading on mobile

## Fixes Applied

### 1. Added Timeout for Auth Check (10 seconds)
```typescript
// Set a timeout to prevent infinite loading
const timeout = setTimeout(() => {
  if (!authChecked) {
    console.warn("Auth check timed out after 10 seconds");
    setAuthChecked(true);
  }
}, 10000);
```

### 2. Added Timeout for Data Fetch (30 seconds)
```typescript
// Create a timeout promise
const timeoutPromise = new Promise((_, reject) => {
  setTimeout(() => reject(new Error("Data fetch timed out after 30 seconds...")), 30000);
});

// Race between fetch and timeout
const fetchedData = await Promise.race([
  db.fetchAllData(),
  timeoutPromise
]) as Database;
```

### 3. Enhanced Error Reporting
Added diagnostic information to error screen:
- Browser user agent
- Network connection type
- Online/offline status
- Environment variable status
- Helpful troubleshooting tips

### 4. Added Diagnostic Page
Created `/diagnostic.html` page accessible at `https://dept56.rndpig.com/diagnostic` that:
- Tests Supabase connection directly
- Shows browser information
- Tests DNS resolution
- Tests CORS headers
- Provides cache clearing tool

### 5. Enhanced Console Logging
Added comprehensive logging throughout the data loading process:
- Auth state changes
- Supabase URL and key presence
- Detailed error information
- Timing information

## How to Test

### On Desktop
1. Open Chrome DevTools
2. Enable device emulation (F12 → Toggle Device Toolbar)
3. Select an iPhone or Android device
4. Reload the page
5. Check console for errors

### On Actual Mobile Device
1. Visit `https://dept56.rndpig.com/diagnostic` first
2. Run all tests to verify connectivity
3. If tests pass, go back to main app
4. If tests fail, you'll see which component is failing

### Using Safari Remote Debugging (iOS)
1. On iPhone: Settings → Safari → Advanced → Enable "Web Inspector"
2. Connect iPhone to Mac via USB
3. On Mac: Safari → Develop → [Your iPhone] → dept56.rndpig.com
4. View console logs and network requests

### Using Chrome Remote Debugging (Android)
1. On Android: Settings → Developer Options → Enable USB Debugging
2. Connect Android to computer via USB
3. Open Chrome on computer
4. Go to `chrome://inspect`
5. Click "inspect" under your device

## Common Mobile Issues & Solutions

### Issue: "Data fetch timed out after 30 seconds"
**Possible Causes:**
- Slow mobile network
- Supabase connection blocked by mobile carrier
- DNS resolution issues

**Solutions:**
1. Try different network (WiFi vs Cellular)
2. Check if Supabase subdomain is accessible
3. Contact mobile carrier about potential blocking
4. Check Supabase dashboard for API limits

### Issue: "Missing Supabase environment variables"
**Cause:** Environment variables not set in Vercel

**Solution:**
1. Go to Vercel Dashboard → Project → Settings → Environment Variables
2. Add:
   ```
   VITE_SUPABASE_URL=https://xctottgirqkkmjmutoon.supabase.co
   VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
3. Redeploy the site

### Issue: Stuck on Loading Screen
**Solutions:**
1. Hard refresh (Cmd+Shift+R on iOS Safari)
2. Clear Safari website data (Settings → Safari → Clear History and Website Data)
3. Try in Private/Incognito mode
4. Try different browser (Chrome, Firefox)

### Issue: Blank White Screen
**Possible Causes:**
- JavaScript error during initialization
- Build asset not loading

**Solutions:**
1. Check browser console
2. Verify all assets loaded in Network tab
3. Check Vercel deployment logs

## Monitoring & Debugging Tools

### 1. Browser Console
```javascript
// Check auth state
console.log("Auth checked:", authChecked);
console.log("User:", user);

// Check data loading
console.log("Loading:", loading);
console.log("Data:", data);
console.log("Error:", error);
```

### 2. Network Tab
Look for:
- Failed requests (red)
- Slow requests (yellow)
- CORS errors
- 404 errors

### 3. Application Tab
Check:
- Local Storage: Should have Supabase session
- Service Workers: Should be registered (if any)
- Cache Storage: Check for stale data

## Performance Optimization for Mobile

### Current Optimizations
- Lazy loading of components
- Image optimization through Supabase
- Responsive design with Tailwind CSS
- Efficient React rendering

### Future Optimizations
1. Implement progressive loading:
   - Load critical data first
   - Stream remaining data
   
2. Add service worker for offline support:
   - Cache static assets
   - Queue failed requests
   
3. Reduce initial bundle size:
   - Code splitting
   - Lazy load modals and forms
   
4. Optimize images:
   - WebP format
   - Responsive images
   - Lazy loading images

## Deployment Checklist

Before deploying fixes:
- [ ] Test on actual mobile device
- [ ] Test on iOS Safari
- [ ] Test on Android Chrome
- [ ] Test on slow 3G network
- [ ] Verify environment variables in Vercel
- [ ] Check Supabase RLS policies
- [ ] Review console logs
- [ ] Test auth flow
- [ ] Test data loading
- [ ] Verify error handling

After deploying:
- [ ] Visit `/diagnostic` page on mobile
- [ ] Run all connection tests
- [ ] Verify error messages show properly
- [ ] Test retry functionality
- [ ] Monitor Vercel logs for errors
- [ ] Check Supabase logs for connection issues

## Emergency Rollback

If issues persist after deployment:
1. Go to Vercel Dashboard → Deployments
2. Find the last working deployment
3. Click "..." → Promote to Production
4. Investigate logs from failed deployment

## Support Resources

- **Vercel Dashboard**: https://vercel.com/dashboard
- **Supabase Dashboard**: https://app.supabase.com
- **Browser DevTools**: F12 or Right-click → Inspect
- **Remote Debugging**: Safari/Chrome dev tools

## Contact for Help

If you continue to experience issues:
1. Run diagnostic page and screenshot results
2. Check browser console and screenshot errors
3. Note: Device type, OS version, Browser version
4. Network type (WiFi, 4G, 5G)
5. Open GitHub issue with above information

---

**Last Updated**: October 19, 2025
**Status**: Fixes deployed, monitoring mobile performance
