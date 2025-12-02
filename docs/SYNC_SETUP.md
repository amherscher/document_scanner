# Pi to Server Sync Setup

## Overview

This feature allows the Raspberry Pi to:
1. **Save scans locally** initially (fast)
2. **Sync files to server** (10.29.0.1) automatically or manually
3. **Delete from Pi** after successful transfer (saves space)

## Quick Setup

### On Raspberry Pi

1. **Enable sync in service file:**
```bash
sudo nano /etc/systemd/system/pi-scan.service
```

Add these lines:
```ini
Environment="SYNC_ENABLED=true"
Environment="SYNC_SERVER_HOST=10.29.0.1"
Environment="SYNC_SERVER_USER=pi"
Environment="SYNC_SERVER_DIR=/opt/scanner/scans"
Environment="AUTO_SYNC=false"  # Set to true for auto-sync after each scan
```

2. **Reload and restart:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart pi-scan
```

### On Server (10.29.0.1)

1. **Create scans directory:**
```bash
mkdir -p /opt/scanner/scans
chmod 755 /opt/scanner/scans
```

2. **Set up SSH key authentication** (for passwordless sync):
```bash
# On Pi, generate SSH key if needed
ssh-keygen -t rsa

# Copy key to server
ssh-copy-id pi@10.29.0.1
```

3. **Test SSH connection from Pi:**
```bash
ssh pi@10.29.0.1 "ls /opt/scanner/scans"
```

## Usage

### Manual Sync (Web UI)

1. Open web interface: `http://pi-scan.local:5000`
2. Click **"Sync to Server"** button
3. Files are transferred and deleted from Pi
4. Status shows number of files synced

### Automatic Sync

Set `AUTO_SYNC=true` in service file:
```ini
Environment="AUTO_SYNC=true"
```

Then every scan will automatically:
1. Save to Pi
2. Sync to server
3. Delete from Pi

### API Endpoints

**Sync files:**
```bash
POST /api/sync
```

**Check sync status:**
```bash
GET /api/sync/status
```

Response:
```json
{
  "ok": true,
  "sync_enabled": true,
  "server_host": "10.29.0.1",
  "server_user": "pi",
  "server_dir": "/opt/scanner/scans",
  "files_ready": 5,
  "files_list": ["scan_20240120_143022.jpg", ...]
}
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SYNC_ENABLED` | `false` | Enable/disable sync feature |
| `SYNC_SERVER_HOST` | `10.29.0.1` | Server IP address |
| `SYNC_SERVER_USER` | `pi` | SSH username for server |
| `SYNC_SERVER_DIR` | `/opt/scanner/scans` | Directory on server |
| `AUTO_SYNC` | `false` | Auto-sync after each scan |

### Example Configuration

**Pi saves locally, manual sync:**
```ini
Environment="SYNC_ENABLED=true"
Environment="SYNC_SERVER_HOST=10.29.0.1"
Environment="AUTO_SYNC=false"
```

**Pi saves and auto-syncs:**
```ini
Environment="SYNC_ENABLED=true"
Environment="SYNC_SERVER_HOST=10.29.0.1"
Environment="AUTO_SYNC=true"
```

## How It Works

1. **Scan happens** → Files saved to Pi's `scans/` directory
2. **Sync triggered** → `rsync` transfers files to server
3. **Files deleted** → `--remove-source-files` removes from Pi after successful transfer
4. **Server has files** → Ready for ML classification

## Troubleshooting

### Sync Button Not Showing

- Check `SYNC_ENABLED=true` is set
- Restart service: `sudo systemctl restart pi-scan`
- Check status: `curl http://pi-scan.local:5000/api/sync/status`

### Sync Fails

1. **Check SSH connection:**
```bash
ssh pi@10.29.0.1 "ls /opt/scanner/scans"
```

2. **Check rsync is installed:**
```bash
which rsync
# If not: sudo apt-get install rsync
```

3. **Check server directory exists:**
```bash
ssh pi@10.29.0.1 "mkdir -p /opt/scanner/scans"
```

4. **Check permissions:**
```bash
ssh pi@10.29.0.1 "chmod 755 /opt/scanner/scans"
```

### Files Not Deleting

- Check rsync version supports `--remove-source-files`
- Verify transfer succeeded (check server)
- Check Pi has write permission to delete files

## Security Notes

- Use SSH keys (not passwords) for sync
- Restrict SSH access on server
- Use firewall rules to limit access
- Consider using VPN for remote access

## Benefits

✅ **Fast scanning** - No network delay during scan
✅ **Space efficient** - Pi doesn't fill up with scans
✅ **Centralized storage** - All scans on server
✅ **ML ready** - Server can classify immediately
✅ **Backup** - Server can backup scans

## Workflow

```
1. User scans invoice on Pi
   ↓
2. File saved to Pi: /opt/scanner/scans/scan_xxx.jpg
   ↓
3. User clicks "Sync to Server" (or auto-sync)
   ↓
4. rsync transfers to: pi@10.29.0.1:/opt/scanner/scans/
   ↓
5. File deleted from Pi (space freed)
   ↓
6. Server has file ready for ML classification
```

