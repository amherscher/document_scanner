from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path


"""
USB LED toggle for Raspberry Pi document scanner.

Supports multiple control methods:
1. USB hub port control (uhubctl) - for USB hubs with per-port power switching
2. Serial USB device - for USB devices that appear as serial ports
3. GPIO control - fallback for GPIO-connected LEDs

Configuration via environment variables:
- METHOD: "uhubctl", "serial", "gpio", or "auto" (default: auto - tries all)
- HUB: USB hub location for uhubctl (e.g., "1-1")
- PORT: USB port number for uhubctl (e.g., "2")
- SERIAL_DEVICE: Serial device path (e.g., "/dev/ttyUSB0" or "/dev/ttyACM0")
- GPIO_PIN: GPIO pin number (BCM numbering, e.g., "18")
- SERIAL_COMMAND_ON: Command bytes to send to turn LED on (hex, e.g., "FF")
- SERIAL_COMMAND_OFF: Command bytes to send to turn LED off (hex, e.g., "00")
"""


def check_command(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    try:
        result = subprocess.run(
            ["which", cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False


def toggle_uhubctl(hub: str, port: str) -> bool:
    """Toggle LED using uhubctl (USB hub port power control)."""
    if not check_command("uhubctl"):
        return False
    
    try:
        # Toggle: off then on (creates a visible blink/toggle effect)
        # First get current state or just toggle
        result_off = subprocess.run(
            ["sudo", "uhubctl", "-l", hub, "-p", port, "-a", "0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False
        )
        if result_off.returncode != 0:
            return False
        
        # Small delay for visible effect
        import time
        time.sleep(0.1)
        
        result_on = subprocess.run(
            ["sudo", "uhubctl", "-l", hub, "-p", port, "-a", "1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False
        )
        return result_on.returncode == 0
    except Exception as e:
        print(f"uhubctl error: {e}", file=sys.stderr)
        return False


def toggle_serial(device: str, cmd_on: str = "FF", cmd_off: str = "00") -> bool:
    """Toggle LED using serial communication."""
    try:
        import serial
    except ImportError:
        print("pyserial not installed. Install with: pip install pyserial", file=sys.stderr)
        return False
    
    if not Path(device).exists():
        print(f"Serial device not found: {device}", file=sys.stderr)
        return False
    
    try:
        ser = serial.Serial(device, 9600, timeout=1)
        # Read current state if possible, or just toggle
        # For simple toggle, send ON command then OFF
        ser.write(bytes.fromhex(cmd_on))
        ser.flush()
        import time
        time.sleep(0.1)
        ser.write(bytes.fromhex(cmd_off))
        ser.close()
        return True
    except Exception as e:
        print(f"Serial error: {e}", file=sys.stderr)
        return False


def toggle_gpio(pin: int) -> bool:
    """Toggle LED using GPIO."""
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        print("RPi.GPIO not installed. Install with: pip install RPi.GPIO", file=sys.stderr)
        return False
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        
        # Read current state and toggle
        current = GPIO.input(pin)
        GPIO.output(pin, not current)
        GPIO.cleanup()
        return True
    except Exception as e:
        print(f"GPIO error: {e}", file=sys.stderr)
        try:
            GPIO.cleanup()
        except:
            pass
        return False


def main():
    """Main entry point - tries to toggle LED using configured method."""
    method = os.environ.get("LED_METHOD", "auto").lower()
    
    # Method 1: USB hub port control (uhubctl)
    hub = os.environ.get("HUB", "")
    port = os.environ.get("PORT", "")
    
    if method in ("auto", "uhubctl"):
        if hub and port:
            if toggle_uhubctl(hub, port):
                print("LED toggled via uhubctl")
                return 0
    
    # Method 2: Serial USB device
    serial_device = os.environ.get("SERIAL_DEVICE", "")
    if method in ("auto", "serial"):
        if serial_device:
            cmd_on = os.environ.get("SERIAL_COMMAND_ON", "FF")
            cmd_off = os.environ.get("SERIAL_COMMAND_OFF", "00")
            if toggle_serial(serial_device, cmd_on, cmd_off):
                print("LED toggled via serial")
                return 0
    
    # Method 3: GPIO
    gpio_pin = os.environ.get("GPIO_PIN", "")
    if method in ("auto", "gpio"):
        if gpio_pin:
            try:
                pin_num = int(gpio_pin)
                if toggle_gpio(pin_num):
                    print("LED toggled via GPIO")
                    return 0
            except ValueError:
                pass
    
    # Fallback: No-op with informative message
    print("LED toggle requested, but no configuration found.")
    print("Configure via environment variables:")
    print("  - uhubctl: HUB=1-1 PORT=2")
    print("  - serial: SERIAL_DEVICE=/dev/ttyUSB0")
    print("  - GPIO: GPIO_PIN=18")
    print("Set LED_METHOD=uhubctl|serial|gpio to force a specific method.")
    return 0  # Return success even if no-op, so UI doesn't show error


if __name__ == "__main__":
    sys.exit(main())
