# GitHub Setup Guide

## Step 1: Install Git (if not already installed)

1. Download Git for Windows from: https://git-scm.com/download/win
2. Run the installer with default options
3. After installation, restart VS Code
4. Verify installation by running: `git --version`

## Step 2: Initialize Git Repository

Run these commands in the terminal:

```bash
# Initialize git repository
git init

# Add all files to staging
git add .

# Create first commit
git commit -m "Initial commit: Department 56 Gallery App with Supabase backend"
```

## Step 3: Create GitHub Repository

1. Go to: https://github.com/new
2. Repository name: `dept56-gallery-app` (or your preferred name)
3. Description: "Department 56 collectibles gallery with React frontend and Supabase backend"
4. Choose: **Private** (recommended) or Public
5. DO NOT initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 4: Connect Local Repo to GitHub

After creating the repo on GitHub, run these commands (replace USERNAME with your GitHub username):

```bash
# Add GitHub as remote origin
git remote add origin https://github.com/USERNAME/dept56-gallery-app.git

# Push code to GitHub
git branch -M main
git push -u origin main
```

## Step 5: Future Updates

After making changes, use these commands to push updates:

```bash
# Check what files changed
git status

# Stage all changes
git add .

# Commit with a message
git commit -m "Describe your changes here"

# Push to GitHub
git push
```

## Important Files Already Configured

✅ `.gitignore` - Prevents committing sensitive files (.env, node_modules, etc.)
✅ `README.md` - Project documentation
✅ `.env` - **NOT committed** (contains your Supabase keys)

## What Gets Committed vs Ignored

**✅ Will be committed:**
- Source code (src/, components/)
- Configuration files (package.json, vite.config.ts, etc.)
- SQL schema files
- Documentation (*.md files)

**❌ Will be ignored (not committed):**
- `.env` file (contains secrets!)
- `node_modules/` (too large, can be reinstalled)
- `ingestion_output/` (local data processing files)
- `__pycache__/` (Python cache)
- Build outputs (`dist/`)

## Security Note

⚠️ **NEVER commit your `.env` file!** It contains:
- Supabase service role key
- Supabase URL
- User credentials

The `.gitignore` file is configured to prevent this, but always double-check with `git status` before committing.
