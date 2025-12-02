# Quick Sync Fix - Run on Pi

## Step 1: Check what the API is actually returning

```bash
# On Pi, run this to see the raw response:
curl -v -H "X-Auth: changeme" http://localhost:5000/api/sync/status
```

This will show you the actual HTTP response (not parsed as JSON).

## Step 2: Check if service is running

```bash
sudo systemctl status pi-scan
```

## Step 3: Check service logs for errors

```bash
sudo journalctl -u pi-scan -n 50 --no-pager
```

## Step 4: Manually edit service file

```bash
sudo nano /etc/systemd/system/pi-scan.service
```

Find the line:
```
Environment="PI_SCAN_TOKEN=changeme"
```

Add these lines **immediately after it** (no # comments):
```
Environment="SYNC_ENABLED=true"
Environment="SYNC_SERVER_HOST=10.29.0.1"
Environment="SYNC_SERVER_USER=amherscher"
Environment="SYNC_SERVER_DIR=/home/data/Purdue/pi/scans"
Environment="AUTO_SYNC=false"
```

Save (Ctrl+X, Y, Enter)

## Step 5: Restart service

```bash
sudo systemctl daemon-reload
sudo systemctl restart pi-scan
sleep 3
```

## Step 6: Verify environment variables

```bash
sudo systemctl show pi-scan | grep SYNC
```

Should show:
```
Environment=SYNC_ENABLED=true
Environment=SYNC_SERVER_HOST=10.29.0.1
...
```

## Step 7: Test API again

```bash
# First without JSON parsing to see raw response:
curl -H "X-Auth: changeme" http://localhost:5000/api/sync/status

# Then with JSON parsing:
curl -s -H "X-Auth: changeme" http://localhost:5000/api/sync/status | python3 -m json.tool
```

## Common Issues

1. **Service not running**: `sudo systemctl start pi-scan`
2. **Wrong auth token**: Make sure you're using the same token as in the service file
3. **Port not listening**: Check `sudo netstat -tlnp | grep 5000`
4. **Python errors**: Check logs with `sudo journalctl -u pi-scan -f`

