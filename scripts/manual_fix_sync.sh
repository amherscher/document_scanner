#!/bin/bash
# Manual sync fix - run this ON THE PI

echo "Manual Sync Fix - Run this ON THE PI"
echo "======================================"
echo ""

echo "1. Check current service file:"
sudo cat /etc/systemd/system/pi-scan.service | grep -A 10 "PI_SCAN_TOKEN"
echo ""

echo "2. Edit the service file manually:"
echo "   sudo nano /etc/systemd/system/pi-scan.service"
echo ""
echo "3. Find the line with PI_SCAN_TOKEN and add these lines RIGHT AFTER it:"
echo ""
echo "Environment=\"SYNC_ENABLED=true\""
echo "Environment=\"SYNC_SERVER_HOST=10.29.0.1\""
echo "Environment=\"SYNC_SERVER_USER=amherscher\""
echo "Environment=\"SYNC_SERVER_DIR=/home/data/Purdue/pi/scans\""
echo "Environment=\"AUTO_SYNC=false\""
echo ""
echo "4. Save and exit (Ctrl+X, Y, Enter)"
echo ""
echo "5. Then run these commands:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl restart pi-scan"
echo ""
echo "6. Verify it worked:"
echo "   sudo systemctl show pi-scan | grep SYNC"
echo "   curl -s -H 'X-Auth: changeme' http://localhost:5000/api/sync/status | python3 -m json.tool"

