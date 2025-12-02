#!/bin/bash
# Fix the service file - run this ON THE PI

echo "Fixing pi-scan service..."
echo ""

echo "1. Checking current service file:"
sudo cat /etc/systemd/system/pi-scan.service | head -45
echo ""

echo "2. The service is trying to use /opt/scanner/venv/bin/python3"
echo "   But venv might not exist on Pi. Let's check:"
ls -la /opt/scanner/venv/bin/python3 2>&1 || echo "venv/python3 not found"
echo ""

echo "3. Checking what Python is available:"
which python3
python3 --version
echo ""

echo "4. Fixing service file to use system Python..."
sudo sed -i 's|ExecStart=/opt/scanner/venv/bin/python3|ExecStart=/usr/bin/python3|' /etc/systemd/system/pi-scan.service

echo "5. Updated ExecStart line:"
sudo grep ExecStart /etc/systemd/system/pi-scan.service
echo ""

echo "6. Reloading and restarting..."
sudo systemctl daemon-reload
sudo systemctl restart pi-scan

echo "7. Waiting 3 seconds..."
sleep 3

echo "8. Service status:"
sudo systemctl status pi-scan --no-pager | head -15
echo ""

echo "9. Checking if port 5000 is listening:"
sudo netstat -tlnp | grep 5000 || ss -tlnp | grep 5000 || echo "Port 5000 not listening yet"
echo ""

echo "10. Recent logs:"
sudo journalctl -u pi-scan -n 10 --no-pager
echo ""

