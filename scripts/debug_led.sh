#!/bin/bash
# Debug LED toggle issue on Pi

PI_USER=${PI_USER:-amherscher}
PI_HOST=${PI_HOST:-10.29.0.14}

echo "Debugging LED toggle on Pi..."
echo ""

ssh ${PI_USER}@${PI_HOST} << 'EOF'
cd /opt/scanner

echo "1. Checking if scripts exist:"
ls -la led_*.py disable_usb.sh enable_usb.sh 2>&1
echo ""

echo "2. Testing passwordless sudo for uhubctl:"
sudo -n uhubctl --version 2>&1
echo "Exit code: $?"
echo ""

echo "3. Testing passwordless sudo for Python script:"
sudo -n /usr/bin/python3 /opt/scanner/led_toggle.py 2>&1
echo "Exit code: $?"
echo ""

echo "4. Testing passwordless sudo for bash script:"
sudo -n /bin/bash /opt/scanner/disable_usb.sh 2>&1
echo "Exit code: $?"
echo ""

echo "5. Checking sudoers configuration:"
sudo cat /etc/sudoers.d/pi-uhubctl 2>&1 || echo "No sudoers file found"
echo ""

echo "6. Testing as pi user (service user):"
sudo -u pi sudo -n uhubctl --version 2>&1
echo "Exit code: $?"
echo ""

echo "7. Checking service user:"
ps aux | grep pi-scan | grep -v grep | head -1
echo ""

echo "8. Testing direct uhubctl:"
sudo uhubctl 2>&1 | head -5
echo ""
EOF

echo "✅ Debug complete!"

