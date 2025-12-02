# Reset Git Repository - Start Fresh

## Option 1: Complete Reset (Remove all Git history)

If you want to completely start over with a fresh git repository:

```bash
cd /home/data/Purdue/pi

# Remove the entire .git directory (deletes all history)
rm -rf .git

# Initialize a fresh repository
git init

# Add all files (respecting .gitignore)
git add .

# Make initial commit
git commit -m "Initial commit: Pi Scanner project"
```

## Option 2: Keep History but Unstage Everything

If you want to keep git history but remove all files from staging:

```bash
cd /home/data/Purdue/pi

# Remove all files from git tracking (but keep them on disk)
git rm -r --cached .

# Re-add everything (respecting .gitignore)
git add .

# Commit the changes
git commit -m "Reset: Update .gitignore and remove large files"
```

## Option 3: Reset to Specific Commit

If you want to go back to a specific commit:

```bash
# See commit history
git log --oneline

# Reset to a specific commit (replace COMMIT_HASH)
git reset --hard COMMIT_HASH

# Or reset to before any commits (empty repository state)
git update-ref -d HEAD
```

## Recommended: Complete Reset

For a clean start, I recommend **Option 1** - it's the simplest and cleanest:

```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit: Pi Scanner project"
```

This will:
- ✅ Remove all previous git history
- ✅ Start with a fresh repository
- ✅ Respect your .gitignore (won't add excluded files)
- ✅ Create a clean initial commit

