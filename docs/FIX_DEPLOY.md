# Fixing Deployment Issues

## Problem: index.html Not Updating

### Solution 1: Force Update Templates

The deploy script now **always updates** `templates/index.html`:

```bash
./deploy_to_pi.sh
```

It will:
1. Sync all files normally (only changed files)
2. **Force update** `templates/index.html` (always copies)

### Solution 2: Manual Force Update

If you need to force update everything:

```bash
FORCE_UPDATE=true ./deploy_to_pi.sh
```

### Solution 3: Manual Copy

```bash
# Copy just the template
scp templates/index.html pi@10.29.0.14:/opt/scanner/templates/

# Or use rsync
rsync -avz --ignore-times templates/index.html pi@10.29.0.14:/opt/scanner/templates/
```

## Problem: Can't Update Server Directory Path

### Check Current Status

1. **Open browser console** (F12) when on the web page
2. **Try to update directory** - check for errors in console
3. **Check network tab** - see if API call is being made

### Common Issues

1. **Path format:**
   - ✅ Good: `/opt/scanner/scans`
   - ✅ Good: `/mnt/server/scans`
   - ✅ Good: `~/scans` (expands to home directory)
   - ❌ Bad: `scans` (relative path - might not work)

2. **Permissions:**
   - Directory must be writable by the Flask app user
   - Check: `ls -ld /opt/scanner/scans`

3. **Network mounts:**
   - If using server path like `/mnt/server/scans`, ensure:
     - Mount point exists
     - Mount is accessible
     - Permissions are correct

### Test Directory Update

```bash
# Test via API
curl -X POST http://pi-scan.local:5000/api/set_workdir \
  -H "Content-Type: application/json" \
  -d '{"path": "/opt/scanner/scans"}'
```

### Debug Steps

1. **Check Flask logs:**
```bash
ssh pi@10.29.0.14
sudo journalctl -u pi-scan -f
```

2. **Check browser console:**
   - Open web page
   - Press F12
   - Go to Console tab
   - Try updating directory
   - Look for errors

3. **Verify file was updated:**
```bash
# On Pi
cat /opt/scanner/templates/index.html | grep -A 5 "setDir"
```

## Quick Fixes

### Force Update Everything
```bash
FORCE_UPDATE=true ./deploy_to_pi.sh
```

### Restart Service After Update
```bash
ssh pi@10.29.0.14 "sudo systemctl restart pi-scan"
```

### Verify Files Updated
```bash
# Check file timestamp
ssh pi@10.29.0.14 "ls -lh /opt/scanner/templates/index.html"

# Check file content (should have setDir function)
ssh pi@10.29.0.14 "grep 'setDir' /opt/scanner/templates/index.html"
```

## Updated Deploy Script

The script now:
- ✅ Always forces update of `templates/index.html`
- ✅ Automatically restarts service after deployment
- ✅ Shows verification steps

Run it and check the output!

