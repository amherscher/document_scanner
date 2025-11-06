#!/usr/bin/env python3
"""
Diagnostic script to identify USB LED device and suggest configuration.
Run this on your Raspberry Pi to detect your USB LED.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=False):
    """Run a command and return output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout, result.returncode == 0
    except Exception as e:
        return str(e), False


def check_uhubctl():
    """Check for USB hubs and ports."""
    print("\n=== USB Hub Control (uhubctl) ===")
    stdout, exists = run_command(["which", "uhubctl"])
    if not exists:
        print("❌ uhubctl not installed. Install with: sudo apt-get install -y uhubctl")
        return []
    
    print("✓ uhubctl is installed")
    stdout, success = run_command(["sudo", "uhubctl"])
    if success:
        print("\nAvailable USB hubs and ports:")
        print(stdout)
        print("\n💡 To use uhubctl, set environment variables:")
        print("   HUB=<hub_location> (e.g., 1-1)")
        print("   PORT=<port_number> (e.g., 2)")
    else:
        print("⚠️  Could not list hubs (may need sudo)")
        print(stdout)
    
    return []


def check_serial_devices():
    """Check for serial USB devices."""
    print("\n=== Serial USB Devices ===")
    serial_devices = []
    for pattern in ["/dev/ttyUSB*", "/dev/ttyACM*", "/dev/ttyAMA*"]:
        for path in Path("/dev").glob(pattern.split("/")[-1]):
            if path.is_char_device():
                serial_devices.append(str(path))
    
    if serial_devices:
        print("✓ Found serial devices:")
        for dev in serial_devices:
            print(f"   {dev}")
        print("\n💡 To use serial control, set environment variables:")
        print("   SERIAL_DEVICE=/dev/ttyUSB0  # or /dev/ttyACM0")
        print("   SERIAL_COMMAND_ON=FF        # hex bytes to turn on")
        print("   SERIAL_COMMAND_OFF=00       # hex bytes to turn off")
    else:
        print("❌ No serial devices found in /dev/ttyUSB* or /dev/ttyACM*")
    
    return serial_devices


def check_usb_devices():
    """Check USB devices using lsusb."""
    print("\n=== USB Devices (lsusb) ===")
    stdout, success = run_command(["lsusb"])
    if success:
        print(stdout)
        print("\n💡 Look for your LED device in the list above.")
        print("   If it's a USB hub, you can use uhubctl to control it.")
    else:
        print("❌ Could not list USB devices")
    
    return success


def check_gpio():
    """Check GPIO availability."""
    print("\n=== GPIO Control ===")
    try:
        import RPi.GPIO as GPIO
        print("✓ RPi.GPIO is available")
        print("\n💡 To use GPIO, set environment variable:")
        print("   GPIO_PIN=18  # BCM pin number")
        return True
    except ImportError:
        print("❌ RPi.GPIO not installed. Install with: pip install RPi.GPIO")
        print("   Note: GPIO is typically for LEDs connected to GPIO pins, not USB.")
        return False


def main():
    print("=" * 60)
    print("USB LED Detection Script")
    print("=" * 60)
    
    check_usb_devices()
    check_uhubctl()
    serial_devs = check_serial_devices()
    check_gpio()
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    
    # Check if uhubctl works
    stdout, exists = run_command(["which", "uhubctl"])
    if exists:
        stdout, success = run_command(["sudo", "uhubctl"], check=False)
        if success and "port" in stdout.lower():
            print("\n1. USB Hub Control (RECOMMENDED if LED is on a USB hub):")
            print("   Run: sudo uhubctl")
            print("   Then set in your systemd service or environment:")
            print("   HUB=<hub> PORT=<port>")
    
    if serial_devs:
        print("\n2. Serial Device Control (if LED appears as serial device):")
        print(f"   Set: SERIAL_DEVICE={serial_devs[0]}")
        print("   You may need to install: pip install pyserial")
    
    print("\n3. After configuring, test with:")
    print("   python3 led_toggle.py")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

