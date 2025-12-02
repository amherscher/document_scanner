#!/bin/bash
# Fix service user - run this ON THE PI

echo "Fixing service user..."
echo ""

echo "1. Current user in service file:"
sudo grep "^User=" /etc/systemd/system/pi-scan.service
echo ""

echo "2. Current system user:"
whoami
echo ""

echo "3. Updating service to use current user..."
sudo sed -i 's/^User=pi/User=amherscher/' /etc/systemd/system/pi-scan.service
sudo sed -i 's/^User=.*/User=amherscher/' /etc/systemd/system/pi-scan.service

echo "4. Updated user:"
sudo grep "^User=" /etc/systemd/system/pi-scan.service
echo ""

echo "5. Checking file permissions:"
ls -ld /opt/scanner
ls -l /opt/scanner/app.py
echo ""

echo "6. Reloading and restarting..."
sudo systemctl daemon-reload
sudo systemctl restart pi-scan

echo "7. Waiting 3 seconds..."
sleep 3

echo "8. Service status:"
sudo systemctl status pi-scan --no-pager | head -20
echo ""

echo "9. Recent logs:"
sudo journalctl -u pi-scan -n 15 --no-pager
echo ""

