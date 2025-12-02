#!/bin/bash
# Test LED/USB control on Pi

PI_USER=${PI_USER:-amherscher}
PI_HOST=${PI_HOST:-10.29.0.14}

echo "Testing LED/USB control on ${PI_USER}@${PI_HOST}..."
echo ""

ssh ${PI_USER}@${PI_HOST} << 'EOF'
cd /opt/scanner

echo "1. Checking if uhubctl is installed:"
which uhubctl || echo "❌ uhubctl not found - install with: sudo apt-get install uhubctl"
echo ""

echo "2. Checking USB hubs:"
sudo uhubctl 2>&1 | head -20
echo ""

echo "3. Checking if LED scripts exist:"
[ -f led_toggle.py ] && echo "✓ led_toggle.py exists" || echo "✗ led_toggle.py missing"
[ -f led_on.py ] && echo "✓ led_on.py exists" || echo "✗ led_on.py missing"
[ -f disable_usb.sh ] && echo "✓ disable_usb.sh exists" || echo "✗ disable_usb.sh missing"
[ -f enable_usb.sh ] && echo "✓ enable_usb.sh exists" || echo "✗ enable_usb.sh missing"
echo ""

echo "4. Testing disable_usb.sh:"
sudo bash disable_usb.sh 2>&1
echo "Exit code: $?"
echo ""

echo "5. Testing enable_usb.sh:"
sudo bash enable_usb.sh 2>&1
echo "Exit code: $?"
echo ""

echo "6. Testing led_toggle.py:"
sudo python3 led_toggle.py 2>&1
echo "Exit code: $?"
echo ""

echo "7. Current USB state file:"
cat /tmp/usb_led_state.txt 2>/dev/null || echo "No state file found"
echo ""
EOF

echo "✅ Test complete!"

