from __future__ import annotations
import subprocess
import sys
from pathlib import Path


"""
Turn ON Raspberry Pi's USB subsystem to turn on the built-in USB LED.

This script re-enables USB power on the Pi.
"""


def enable_usb() -> bool:
    """Enable USB power on the Raspberry Pi.
    
    Since xhci_hcd is builtin (can't modprobe), we use uhubctl to enable ports.
    """
    # Method 1: Use uhubctl to enable Pi's internal USB hub ports
    # This is the method that works since xhci_hcd is builtin
    if subprocess.run(["which", "uhubctl"], capture_output=True).returncode == 0:
        try:
            # List available hubs
            list_result = subprocess.run(
                ["sudo", "uhubctl"],
                capture_output=True,
                text=True,
                check=False
            )
            if list_result.returncode == 0:
                import re
                hub_matches = re.findall(r'hub\s+(\d+(?:-\d+)?)', list_result.stdout)
                hubs_to_try = list(set(hub_matches))
                print(f"Found hubs: {hubs_to_try}", file=sys.stderr)
            else:
                hubs_to_try = ["1", "2", "3", "4", "1-1"]
            
            # Enable all ports on all hubs
            enabled_count = 0
            for hub in hubs_to_try:
                for port in ["1", "2", "3", "4", "5"]:
                    result = subprocess.run(
                        ["sudo", "uhubctl", "-l", hub, "-p", port, "-a", "1"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False
                    )
                    if result.returncode == 0:
                        enabled_count += 1
                        print(f"USB port {port} on hub {hub} enabled", file=sys.stderr)
            
            if enabled_count > 0:
                print(f"Enabled {enabled_count} USB port(s) - LED should be on now")
                return True
        except Exception as e:
            print(f"Error with uhubctl: {e}", file=sys.stderr)
    
    # Method 2: Try sysfs to enable USB controller
    usb_paths = [
        Path("/sys/bus/usb/devices/usb1/power/control"),
        Path("/sys/bus/usb/devices/usb2/power/control"),
    ]
    
    for path in usb_paths:
        if path.exists():
            try:
                result = subprocess.run(
                    ["sh", "-c", f"echo auto | sudo tee {path}"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    new_value = path.read_text().strip()
                    if new_value == "auto":
                        print(f"USB enabled via {path}")
                        return True
            except Exception as e:
                print(f"Error with {path}: {e}", file=sys.stderr)
    
    # Note: xhci_hcd is builtin, so modprobe won't work
    # Don't try to modprobe - it's already there
    
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

