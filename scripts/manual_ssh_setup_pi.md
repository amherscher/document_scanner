# Manual SSH Setup - Run on Pi

## Step 1: Add server host key

```bash
# On Pi, run:
ssh-keyscan -H 10.29.0.1 >> ~/.ssh/known_hosts
```

## Step 2: Copy SSH key to server

```bash
# On Pi, run (will prompt for server password):
ssh-copy-id amherscher@10.29.0.1
```

If you don't have an SSH key yet:
```bash
# Generate one first:
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
# Then copy it:
ssh-copy-id -i ~/.ssh/id_ed25519.pub amherscher@10.29.0.1
```

## Step 3: Test passwordless connection

```bash
# On Pi, test:
ssh -o BatchMode=yes amherscher@10.29.0.1 "echo 'test'"
```

Should work without password prompt.

## Step 4: Verify server directory

```bash
# On Pi, check:
ssh amherscher@10.29.0.1 "test -d /home/data/Purdue/pi/scans && echo 'exists' || echo 'missing'"
```

## Step 5: Test sync

After setup, the sync should work. Test on Pi:
```bash
curl -s -H "X-Auth: changeme" http://localhost:5000/api/sync/status | python3 -m json.tool
```

Should show:
- `ssh_connected: true`
- `server_dir_exists: true`

