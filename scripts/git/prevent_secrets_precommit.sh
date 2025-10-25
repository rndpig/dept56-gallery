#!/usr/bin/env bash
# Pre-commit hook (POSIX shell)
# Scans staged files for JWT-like tokens and private key blocks.
# Exit non-zero to block the commit if a potential secret is found.

set -euo pipefail

echo "Running secret-scan pre-commit hook..."

# Patterns to check (feel free to extend)
patterns=(
  "eyJ[A-Za-z0-9_-]{10,}" # JWT-like
  "-----BEGIN PRIVATE KEY-----" # Private key
  "SUPABASE_SERVICE_ROLE_KEY" # service role var name
  "AWS_SECRET_ACCESS_KEY" # common AWS var
)

found=0

# Get list of staged files
files=$(git diff --cached --name-only --diff-filter=ACM)

for file in $files; do
  # Only check text files (avoid binary noise)
  if file --mime "${file}" 2>/dev/null | grep -q text; then
    for pat in "${patterns[@]}"; do
      if grep -E --line-number --color=never "$pat" "$file" >/dev/null 2>&1; then
        echo "Potential secret found in $file (pattern: $pat)"
        grep -nE --color=always "$pat" "$file" || true
        found=1
      fi
    done
  fi
done

if [ "$found" -ne 0 ]; then
  echo "\nCommit blocked: potential secret(s) found in staged files.\n" >&2
  echo "If these are false positives, you can amend the files or skip the check with: git commit -n" >&2
  exit 1
fi

echo "Secret-scan passed. Proceeding with commit."
exit 0
