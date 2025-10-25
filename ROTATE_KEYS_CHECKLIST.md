# Supabase & Vercel Key Rotation Checklist

Follow these steps immediately to rotate and verify your Supabase and Vercel keys after a potential exposure.

Important: rotate keys BEFORE rewriting git history or publicizing the project status. Rotating invalidates leaked keys.

1) Prepare: inform collaborators
   - Tell your team you'll rotate keys and may briefly affect deployments.
   - Ensure someone can update Vercel env vars (project owner or admin).

2) Supabase: rotate keys
   - Go to: https://app.supabase.com → Select your project → Settings → API
   - Under "Project API keys":
     - Click **Rotate** for the ANON public key. Note: rotating anon key will require updating client deployments.
     - If you suspect any service-role key exposure, click **Rotate** for SERVICE_ROLE key as well.
   - Copy the new keys to a secure password manager (do NOT commit to repo).

3) Vercel: update environment variables
   - Go to: https://vercel.com → Your project → Settings → Environment Variables
   - Update the following variables with the NEW values from Supabase:
     - `VITE_SUPABASE_URL` (if changed)
     - `VITE_SUPABASE_ANON_KEY` (new anon key)
     - If you use server-side functions and store `SUPABASE_SERVICE_ROLE_KEY` in Vercel, update it too (Production only).
   - For each variable select appropriate environments (Production/Preview/Development) and save.
   - Redeploy the project via the Vercel UI (or push a no-op commit):
     ```powershell
     git commit --allow-empty -m "Trigger redeploy after env rotation"
     git push
     ```

4) Verify application works
   - Visit your production site (https://dept56.rndpig.com) and exercise admin flows.
   - Open browser console to confirm no auth errors and that requests use the new keys (client-side will use anon key automatically when redeployed).

5) Rotate other linked services (if any)
   - If you used the same key on other services, rotate those keys too.

6) Scrub git history (optional but recommended)
   - After keys are rotated and confirmed, remove committed secrets from git history (this is destructive and requires force-push).
   - Use `git-filter-repo` or BFG. Example (git-filter-repo):
     ```powershell
     python -m pip install git-filter-repo
     git branch backup-main
     git filter-repo --path vercel.env --invert-paths
     git push --force --all
     git push --force --tags
     ```
   - Notify collaborators to re-clone after this operation.

7) Post-rotation audit
   - Check Supabase logs for suspicious activity and invalidate sessions if needed.
   - Review RLS policies to ensure anon key alone cannot perform privileged writes.

8) Prevent future leaks
   - Ensure `.gitignore` contains local env files (e.g., `.env`, `vercel.env`).
   - Use the pre-commit secret scanner installed in this repo (`scripts/git/prevent_secrets_precommit.ps1` / `.sh`).
   - Consider enabling branch protection rules and pre-receive hooks on your Git host.

If you'd like, I can now run the history-scrub helper to remove `vercel.env` from git history (it will run `git filter-repo --path vercel.env --invert-paths` and then you'll need to force-push). This operation rewrites history and is irreversible for collaborators — confirm with a reply of `YES, SCRUB` to proceed.
