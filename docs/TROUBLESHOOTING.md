# Troubleshooting Guide

## Nothing is Working - Quick Fixes

### 1. Check if app is running
```bash
# On Pi
sudo systemctl status pi-scan
# Or if running manually
ps aux | grep app.py
```

### 2. Check logs for errors
```bash
# On Pi
sudo journalctl -u pi-scan -n 50 --no-pager
# Or if running manually, check terminal output
```

### 3. Verify file structure on Pi
Files should be in `/opt/scanner/`:
- `app.py` ✓
- `scan_once.py` ✓ (in root, not scripts/)
- `led_toggle.py` ✓ (in root, not hardware/led/)
- `led_on.py` ✓ (in root, not hardware/led/)
- `disable_usb.sh` ✓
- `enable_usb.sh` ✓
- `templates/index.html` ✓

### 4. Common Issues

#### Scan not working
- **Check**: `scan_once.py` exists in `/opt/scanner/`
- **Check**: Camera is connected and accessible
- **Check**: `fswebcam` or `rpicam-still` is installed
- **Test**: Run manually: `python3 /opt/scanner/scan_once.py --workdir /opt/scanner/scans --basename test --zoom 0.3`

#### LED toggle not working
- **Check**: `led_toggle.py` and `led_on.py` exist in `/opt/scanner/`
- **Check**: `disable_usb.sh` and `enable_usb.sh` exist in `/opt/scanner/`
- **Check**: `uhubctl` is installed: `sudo apt-get install uhubctl`
- **Check**: User has sudo permissions (for LED control)
- **Test**: Run manually: `sudo python3 /opt/scanner/led_toggle.py`

#### ML Model not available
- **Check**: Model file exists (if using ML on Pi)
- **Check**: PyTorch is installed (if using ML on Pi)
- **Note**: If Pi is scanner-only, ML should run on server, not Pi
- **Check**: Environment variable `INVOICE_MODEL_PATH` is set correctly

### 5. Run Diagnostic Script
From server:
```bash
./scripts/test_pi_setup.sh
```

This will check:
- File structure
- Dependencies
- Service status
- Recent logs

### 6. Quick Fixes

#### Fix file paths
The deploy script should put files in root `/opt/scanner/`, not subdirectories.

#### Fix permissions
```bash
# On Pi
sudo chown -R pi:pi /opt/scanner
chmod +x /opt/scanner/*.py
chmod +x /opt/scanner/*.sh
```

#### Reinstall dependencies
```bash
# On Pi
sudo apt-get update
sudo apt-get install -y python3-flask fswebcam img2pdf tesseract-ocr uhubctl
pip3 install Flask
```

#### Restart service
```bash
# On Pi
sudo systemctl restart pi-scan
sudo systemctl status pi-scan
```

