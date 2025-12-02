#!/bin/bash
# Check LED files on Pi

PI_USER=${PI_USER:-amherscher}
PI_HOST=${PI_HOST:-10.29.0.14}

echo "Checking LED files on Pi..."
echo ""

ssh ${PI_USER}@${PI_HOST} << 'EOF'
cd /opt/scanner

echo "1. Checking bash location:"
which bash
ls -la /bin/bash /usr/bin/bash 2>&1
echo ""

echo "2. Checking LED Python scripts:"
ls -la led_toggle.py led_on.py hardware/led/led_toggle.py hardware/led/led_on.py 2>&1
echo ""

echo "3. Checking USB bash scripts:"
ls -la disable_usb.sh enable_usb.sh scripts/disable_usb.sh scripts/enable_usb.sh 2>&1
echo ""

echo "4. Testing path resolution from led_toggle.py location:"
if [ -f hardware/led/led_toggle.py ]; then
  python3 -c "
from pathlib import Path
script_dir = Path('/opt/scanner/hardware/led')
app_root = script_dir.parent.parent
print('App root:', app_root)
print('Disable script 1:', app_root / 'disable_usb.sh', 'exists:', (app_root / 'disable_usb.sh').exists())
print('Disable script 2:', app_root / 'scripts' / 'disable_usb.sh', 'exists:', (app_root / 'scripts' / 'disable_usb.sh').exists())
"
fi
echo ""

echo "5. Testing direct script execution:"
if [ -f disable_usb.sh ]; then
  echo "Testing disable_usb.sh:"
  bash disable_usb.sh 2>&1 | head -5
  echo "Exit code: $?"
fi
echo ""
EOF

echo "✅ Check complete!"

