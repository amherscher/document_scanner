# Deploy Script Behavior Explained

## How rsync Works

The `deploy_to_pi.sh` script uses `rsync` which is **smart about updates**:

### Default Behavior (Current Script)

**rsync only copies files that have changed:**
- ✅ Files with different **size** → Copied
- ✅ Files with different **modification time** → Copied  
- ✅ **New files** → Copied
- ❌ Files that are **identical** → Skipped (not copied)

This is **efficient** - it only transfers what's needed!

### Example

```bash
# First run - copies everything
./deploy_to_pi.sh
# Output: app.py, scan_once.py, templates/index.html, etc.

# Second run (no changes) - skips everything
./deploy_to_pi.sh  
# Output: (nothing copied, all files identical)

# After editing app.py - only copies changed file
./deploy_to_pi.sh
# Output: app.py (only this file copied)
```

## Force Update (Always Copy)

If you want to **always copy all files** (even if unchanged):

```bash
FORCE_UPDATE=true ./deploy_to_pi.sh
```

This uses `--ignore-times` flag to copy everything.

## Update Only If Newer

The script now uses `--update` by default, which means:
- Only copies if source file is **newer** than destination
- Skips if destination is newer or same age

## Common Scenarios

### Scenario 1: Normal Development
```bash
# Edit files on server
nano app.py

# Deploy - only changed files copied
./deploy_to_pi.sh
```

### Scenario 2: Force Full Update
```bash
# Copy everything, even if timestamps match
FORCE_UPDATE=true ./deploy_to_pi.sh
```

### Scenario 3: Files Modified on Pi
```bash
# If you edited files on Pi, they might be "newer"
# Force update to overwrite
FORCE_UPDATE=true ./deploy_to_pi.sh
```

### Scenario 4: Delete Files on Pi
```bash
# rsync doesn't delete files by default
# To sync deletions, add --delete flag (be careful!)
rsync -avz --delete ...
```

## What Gets Updated

**Always synced:**
- `app.py` (if changed)
- `scan_once.py` (if changed)
- `templates/index.html` (if changed)
- Other files in the sync list (if changed)

**Never synced (excluded):**
- `venv/` - Virtual environment
- `checkpoints/` - ML models
- `ml_pipeline/` - ML code (not needed on Pi for scanner-only)
- `*.md` - Documentation files
- `archive*/` - Large dataset files

## Verification

After deployment, check what was copied:
```bash
# rsync shows what it's copying
# Look for filenames in the output

# Or check on Pi
ssh pi@10.29.0.14 "ls -lh /opt/scanner/"
```

## Troubleshooting

### Files Not Updating

1. **Check timestamps:**
```bash
# On server
ls -l app.py

# On Pi
ssh pi@10.29.0.14 "ls -l /opt/scanner/app.py"
```

2. **Force update:**
```bash
FORCE_UPDATE=true ./deploy_to_pi.sh
```

3. **Check file permissions:**
```bash
ssh pi@10.29.0.14 "ls -l /opt/scanner/"
```

### Files Updated But Changes Not Visible

1. **Restart service on Pi:**
```bash
ssh pi@10.29.0.14 "sudo systemctl restart pi-scan"
```

2. **Check service logs:**
```bash
ssh pi@10.29.0.14 "sudo journalctl -u pi-scan -f"
```

## Summary

✅ **Yes, files will update** - but only if they've changed
✅ **Efficient** - only transfers what's needed
✅ **Fast** - skips identical files
✅ **Force option** - use `FORCE_UPDATE=true` to always copy

The script is designed to be **smart and efficient** - it updates what needs updating, and skips what doesn't!

