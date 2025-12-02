#!/bin/bash
# Quick script to restart the pi-scan service on the Pi

PI_USER=${PI_USER:-amherscher}
PI_HOST=${PI_HOST:-10.29.0.14}

echo "Restarting pi-scan service on ${PI_USER}@${PI_HOST}..."

ssh ${PI_USER}@${PI_HOST} << 'EOF'
echo "Stopping service..."
sudo systemctl stop pi-scan

echo "Waiting 2 seconds..."
sleep 2

echo "Starting service..."
sudo systemctl start pi-scan

echo "Waiting 2 seconds..."
sleep 2

echo "Service status:"
sudo systemctl status pi-scan --no-pager -l | head -20

echo ""
echo "Recent logs:"
sudo journalctl -u pi-scan -n 10 --no-pager
EOF

echo ""
echo "✅ Service restarted!"

