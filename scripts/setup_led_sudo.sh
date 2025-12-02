#!/bin/bash
# Setup passwordless sudo for LED control on Pi

PI_USER=${PI_USER:-amherscher}
PI_HOST=${PI_HOST:-10.29.0.14}

echo "Setting up passwordless sudo for LED control on Pi..."
echo ""

ssh ${PI_USER}@${PI_HOST} << 'EOF'
echo "Creating sudoers file for uhubctl..."
echo "pi ALL=(ALL) NOPASSWD: /usr/bin/uhubctl" | sudo tee /etc/sudoers.d/pi-uhubctl
echo "pi ALL=(ALL) NOPASSWD: /usr/bin/python3 /opt/scanner/led_toggle.py" | sudo tee -a /etc/sudoers.d/pi-uhubctl
echo "pi ALL=(ALL) NOPASSWD: /usr/bin/python3 /opt/scanner/led_on.py" | sudo tee -a /etc/sudoers.d/pi-uhubctl
echo "pi ALL=(ALL) NOPASSWD: /bin/bash /opt/scanner/disable_usb.sh" | sudo tee -a /etc/sudoers.d/pi-uhubctl
echo "pi ALL=(ALL) NOPASSWD: /bin/bash /opt/scanner/enable_usb.sh" | sudo tee -a /etc/sudoers.d/pi-uhubctl

echo ""
echo "Setting correct permissions..."
sudo chmod 0440 /etc/sudoers.d/pi-uhubctl

echo ""
echo "Verifying sudoers file:"
sudo cat /etc/sudoers.d/pi-uhubctl

echo ""
echo "Testing passwordless sudo..."
sudo -n uhubctl --version 2>&1 && echo "✓ Passwordless sudo works!" || echo "⚠️  May still need password"

echo ""
echo "✅ Setup complete! Restart the service:"
echo "  sudo systemctl restart pi-scan"
EOF

