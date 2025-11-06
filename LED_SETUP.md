# USB LED Setup Guide

## Quick Setup (If running app.py directly)

1. **First, identify your USB LED device:**

   Run the diagnostic script:
   ```bash
   python3 detect_led.py
   ```

   Or manually check:
   ```bash
   # Check USB devices
   lsusb
   
   # Check USB hubs (if uhubctl is installed)
   sudo uhubctl
   
   # Check serial devices
   ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
   ```

2. **Set environment variables based on your LED type:**

   **Option A: USB Hub Port Control (uhubctl)**
   ```bash
   export HUB="1-1"    # Find from: sudo uhubctl
   export PORT="2"     # Port number where LED is connected
   ```

   **Option B: Serial USB Device**
   ```bash
   export SERIAL_DEVICE="/dev/ttyUSB0"  # or /dev/ttyACM0
   export SERIAL_COMMAND_ON="FF"        # Hex command to turn on
   export SERIAL_COMMAND_OFF="00"       # Hex command to turn off
   ```

   **Option C: GPIO Control**
   ```bash
   export GPIO_PIN="18"  # BCM pin number
   ```

3. **Test the LED toggle:**
   ```bash
   python3 led_toggle.py
   ```

4. **Run your Flask app with the environment variables:**
   ```bash
   # Make sure the variables are still set, then:
   python3 app.py
   ```

## Permanent Setup (Using systemd service)

1. **Edit the service file:**
   ```bash
   sudo nano /etc/systemd/system/pi-scan.service
   ```

2. **Uncomment and set the appropriate LED configuration lines:**
   
   For USB hub control:
   ```ini
   Environment="HUB=1-1"
   Environment="PORT=2"
   ```

   For serial device:
   ```ini
   Environment="SERIAL_DEVICE=/dev/ttyUSB0"
   Environment="SERIAL_COMMAND_ON=FF"
   Environment="SERIAL_COMMAND_OFF=00"
   ```

   For GPIO:
   ```ini
   Environment="GPIO_PIN=18"
   ```

3. **Reload and restart:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart pi-scan
   sudo systemctl status pi-scan
   ```

## Troubleshooting

- **"uhubctl not installed"**: `sudo apt-get install -y uhubctl`
- **"pyserial not installed"**: `pip install pyserial`
- **"RPi.GPIO not installed"**: `pip install RPi.GPIO`
- **Permission denied**: Make sure the user running the app has permissions to access USB devices (may need to add user to `dialout` group for serial devices)
- **"No configuration found"**: Run `detect_led.py` to identify your LED type

