# How to scrub secrets from git history (runbook)

This runbook shows safe steps to remove committed files (like `vercel.env`) from git history
using `git-filter-repo`. It includes a non-destructive preview and an option to run the removal.

IMPORTANT: rotating keys is mandatory. If you do not rotate secrets, removing them from git
history is not enough because old clones and forks may still contain them.

1) Rotate exposed secrets now
   - Supabase: Project → Settings → API → Rotate anon key / service role key
   - Vercel: Project → Settings → Environment Variables → Replace keys

2) Inform your team
   - Let collaborators know you'll rewrite history and they should re-clone after the operation.

3) Install git-filter-repo
   - Recommended: python -m pip install git-filter-repo

4) Create a safety backup branch
   - git branch backup-main

5) Preview removal (recommended)
   - From repo root:
     - git filter-repo --path vercel.env --invert-paths --dry-run

6) Run removal
   - git filter-repo --path vercel.env --invert-paths

7) Force-push rewritten history
   - git push --force --all
   - git push --force --tags

8) Ask collaborators to re-clone
   - After you force-push, every collaborator must re-clone or follow advanced rebase steps.

If you prefer automated assistance, run the included PowerShell helper:

    .\scripts\git\scrub_history.ps1 -Run

This will execute `git filter-repo --path vercel.env --invert-paths` (only the single example).

Security note: if you discover a service-role key was exposed anywhere, rotate it immediately and consider revoking any sessions that used it.
