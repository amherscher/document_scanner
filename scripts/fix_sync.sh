#!/bin/bash
# Force enable sync on Pi

PI_USER=${PI_USER:-amherscher}
PI_HOST=${PI_HOST:-10.29.0.14}

echo "Force enabling sync on Pi..."
echo ""

ssh ${PI_USER}@${PI_HOST} << 'EOF'
echo "1. Current service file sync settings:"
sudo cat /etc/systemd/system/pi-scan.service | grep -i SYNC
echo ""

echo "2. Adding/updating sync environment variables..."
# Remove any existing SYNC lines (commented or not)
sudo sed -i '/SYNC_/d' /etc/systemd/system/pi-scan.service

# Add sync configuration after the PI_SCAN_TOKEN line
sudo sed -i '/Environment="PI_SCAN_TOKEN=/a\
Environment="SYNC_ENABLED=true"\
Environment="SYNC_SERVER_HOST=10.29.0.1"\
Environment="SYNC_SERVER_USER=amherscher"\
Environment="SYNC_SERVER_DIR=/home/data/Purdue/pi/scans"\
Environment="AUTO_SYNC=false"' /etc/systemd/system/pi-scan.service

echo "3. Updated service file:"
sudo cat /etc/systemd/system/pi-scan.service | grep -A 6 "PI_SCAN_TOKEN"
echo ""

echo "4. Reloading systemd..."
sudo systemctl daemon-reload

echo "5. Restarting service..."
sudo systemctl restart pi-scan

echo "6. Waiting 3 seconds..."
sleep 3

echo "7. Service status:"
sudo systemctl status pi-scan --no-pager -l | head -20
echo ""

echo "8. Checking environment variables in running process:"
sudo systemctl show pi-scan | grep -i SYNC
echo ""

echo "9. Testing API sync status:"
curl -s -H "X-Auth: changeme" http://localhost:5000/api/sync/status 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "API test failed"
echo ""
EOF

echo ""
echo "✅ Sync should now be enabled!"
echo "Refresh the web UI to see the sync button."

