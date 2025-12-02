#!/bin/bash
# Test script to diagnose Pi setup issues

echo "=========================================="
echo "Pi Scanner Setup Diagnostic"
echo "=========================================="
echo ""

PI_USER=${PI_USER:-amherscher}
PI_HOST=${PI_HOST:-10.29.0.14}
PI_DIR=${PI_DIR:-/opt/scanner}

echo "Testing connection to Pi..."
ssh ${PI_USER}@${PI_HOST} "echo 'Connected successfully'" || {
    echo "❌ Cannot connect to Pi"
    exit 1
}

echo ""
echo "Checking file structure on Pi..."
ssh ${PI_USER}@${PI_HOST} << 'EOF'
cd /opt/scanner
echo "Current directory: $(pwd)"
echo ""
echo "Files in /opt/scanner:"
ls -la
echo ""
echo "Checking key files:"
[ -f app.py ] && echo "✓ app.py exists" || echo "✗ app.py missing"
[ -f scan_once.py ] && echo "✓ scan_once.py exists" || echo "✗ scan_once.py missing"
[ -f led_toggle.py ] && echo "✓ led_toggle.py exists" || echo "✗ led_toggle.py missing"
[ -f led_on.py ] && echo "✓ led_on.py exists" || echo "✗ led_on.py missing"
[ -f disable_usb.sh ] && echo "✓ disable_usb.sh exists" || echo "✗ disable_usb.sh missing"
[ -f enable_usb.sh ] && echo "✓ enable_usb.sh exists" || echo "✗ enable_usb.sh missing"
[ -d templates ] && echo "✓ templates/ exists" || echo "✗ templates/ missing"
[ -f templates/index.html ] && echo "✓ templates/index.html exists" || echo "✗ templates/index.html missing"
echo ""
echo "Checking Python:"
which python3
python3 --version
echo ""
echo "Checking dependencies:"
python3 -c "import flask; print('✓ Flask installed')" 2>/dev/null || echo "✗ Flask not installed"
echo ""
echo "Checking system tools:"
which fswebcam && echo "✓ fswebcam installed" || echo "✗ fswebcam not installed"
which uhubctl && echo "✓ uhubctl installed" || echo "✗ uhubctl not installed"
echo ""
echo "Checking service status:"
sudo systemctl status pi-scan --no-pager -l || echo "Service not running or not installed"
echo ""
echo "Checking recent logs:"
sudo journalctl -u pi-scan -n 20 --no-pager || echo "No logs found"
EOF

echo ""
echo "=========================================="
echo "Diagnostic complete"
echo "=========================================="

