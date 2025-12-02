#!/bin/bash
# Check sync status on Pi

PI_USER=${PI_USER:-amherscher}
PI_HOST=${PI_HOST:-10.29.0.14}

echo "Checking sync status on Pi..."
echo ""

ssh ${PI_USER}@${PI_HOST} << 'EOF'
echo "1. Checking service environment variables:"
sudo systemctl show pi-scan | grep -i SYNC || echo "No SYNC variables found"
echo ""

echo "2. Checking if sync is enabled in service file:"
sudo grep -i "SYNC_ENABLED" /etc/systemd/system/pi-scan.service | grep -v "^#" || echo "SYNC_ENABLED not found or commented out"
echo ""

echo "3. Testing SSH connection to server:"
ssh -o ConnectTimeout=5 -o BatchMode=yes amherscher@10.29.0.1 "echo 'SSH OK'" 2>&1
echo "Exit code: $?"
echo ""

echo "4. Testing server directory:"
ssh amherscher@10.29.0.1 "test -d /home/data/Purdue/pi/scans && echo 'Directory exists' || echo 'Directory missing'" 2>&1
echo ""

echo "5. Checking API sync status:"
curl -s -H "X-Auth: changeme" http://localhost:5000/api/sync/status | python3 -m json.tool 2>/dev/null || echo "API not accessible"
echo ""
EOF

echo "✅ Check complete!"
echo ""
echo "To enable sync, run: ./scripts/enable_sync_on_pi.sh"

