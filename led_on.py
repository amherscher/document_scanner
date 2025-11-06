from __future__ import annotations
import subprocess
import sys
from pathlib import Path


"""
Turn ON Raspberry Pi's USB subsystem to turn on the built-in USB LED.

This script re-enables USB power on the Pi.
"""


def enable_usb() -> bool:
    """Enable USB power on the Raspberry Pi."""
    # Method 1: Use sysfs to enable USB controller
    usb_paths = [
        Path("/sys/bus/usb/devices/usb1/power/control"),
        Path("/sys/bus/usb/devices/usb2/power/control"),
    ]
    
    for path in usb_paths:
        if path.exists():
            try:
                path.write_text("auto")
                print(f"USB enabled via {path}")
                return True
            except PermissionError:
                # Need root, try sudo approach
                pass
            except Exception as e:
                print(f"Error with {path}: {e}", file=sys.stderr)
    
    # Method 2: Use uhubctl to enable Pi's internal USB hub
    if subprocess.run(["which", "uhubctl"], capture_output=True).returncode == 0:
        try:
            # Try common Pi USB hub locations
            for hub in ["1-1", "1-1.1"]:
                for port in ["1", "2", "3", "4"]:
                    result = subprocess.run(
                        ["sudo", "uhubctl", "-l", hub, "-p", port, "-a", "1"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False
                    )
                    if result.returncode == 0:
                        print(f"USB port {port} on hub {hub} enabled")
                        return True
        except Exception as e:
            print(f"Error with uhubctl: {e}", file=sys.stderr)
    
    # Method 3: Reload USB modules
    try:
        result = subprocess.run(
            ["sudo", "modprobe", "xhci_hcd"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print("USB enabled via xhci_hcd module loading")
            return True
    except Exception:
        pass
    
    try:
        result = subprocess.run(
            ["sudo", "modprobe", "ohci_hcd", "uhci_hcd"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print("USB enabled via OHCI/UHCI module loading")
            return True
    except Exception:
        pass
    
    return False


def main():
    """Turn on USB to turn on LED."""
    if enable_usb():
        # Save state
        try:
            Path("/tmp/usb_led_state.txt").write_text("on")
        except Exception:
            pass
        return 0
    else:
        print("Failed to enable USB. Try running with sudo.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

