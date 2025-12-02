#!/bin/bash
# Enable sync on Pi by updating the service file

PI_USER=${PI_USER:-amherscher}
PI_HOST=${PI_HOST:-10.29.0.14}

echo "Enabling sync on Pi..."
echo ""

ssh ${PI_USER}@${PI_HOST} << 'EOF'
echo "Current service file:"
sudo cat /etc/systemd/system/pi-scan.service | grep -A 5 "SYNC" || echo "No sync config found"
echo ""

echo "Updating service file..."
sudo sed -i 's/# Environment="SYNC_ENABLED=true"/Environment="SYNC_ENABLED=true"/' /etc/systemd/system/pi-scan.service
sudo sed -i 's/# Environment="SYNC_SERVER_HOST=10.29.0.1"/Environment="SYNC_SERVER_HOST=10.29.0.1"/' /etc/systemd/system/pi-scan.service
sudo sed -i 's/# Environment="SYNC_SERVER_USER=pi"/Environment="SYNC_SERVER_USER=amherscher"/' /etc/systemd/system/pi-scan.service
sudo sed -i 's|# Environment="SYNC_SERVER_DIR=/opt/scanner/scans"|Environment="SYNC_SERVER_DIR=/home/data/Purdue/pi/scans"|' /etc/systemd/system/pi-scan.service

echo "Updated service file:"
sudo cat /etc/systemd/system/pi-scan.service | grep -A 5 "SYNC"
echo ""

echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Restarting service..."
sudo systemctl restart pi-scan

echo ""
echo "Service status:"
sudo systemctl status pi-scan --no-pager -l | head -15
EOF

echo ""
echo "✅ Sync enabled! Check the web UI to verify."

