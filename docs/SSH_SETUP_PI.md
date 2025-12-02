# SSH Setup for Sync - Run on Pi

## Quick Setup (On Pi)

```bash
# 1. Start SSH agent
eval "$(ssh-agent -s)"

# 2. Add your key (if you have one)
ssh-add ~/.ssh/id_ed25519  # or id_rsa if that's what you have

# 3. If you don't have a key, generate one:
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""

# 4. Add server to known_hosts
ssh-keyscan -H 10.29.0.1 >> ~/.ssh/known_hosts

# 5. Copy key to server (enter password when prompted)
ssh-copy-id -i ~/.ssh/id_ed25519.pub amherscher@10.29.0.1

# 6. Test passwordless connection
ssh -o BatchMode=yes amherscher@10.29.0.1 "echo 'test'"

# 7. Create server directory
ssh amherscher@10.29.0.1 "mkdir -p /home/data/Purdue/pi/scans && chmod 755 /home/data/Purdue/pi/scans"
```

## Or use the script

Copy the script to Pi and run:
```bash
# On Pi:
./setup_ssh_simple.sh
```

## After setup, test sync

```bash
# On Pi:
curl -s -H "X-Auth: changeme" http://localhost:5000/api/sync/status | python3 -m json.tool
```

Should show `ssh_connected: true` and `server_dir_exists: true`.

