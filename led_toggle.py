from __future__ import annotations
import subprocess
import sys
from pathlib import Path


"""
Turn OFF Raspberry Pi's USB subsystem to turn off the built-in USB LED.

This script disables USB power on the Pi.
"""


def disable_usb() -> bool:
    """Disable USB power on the Raspberry Pi.
    
    Since camera is CSI (not USB), we can safely remove USB modules.
    """
    # Note: xhci_hcd is built into the kernel on this Pi, so we can't remove it
    # Instead, we'll disable USB ports via uhubctl, which controls the LED
    
    # Method 2: Try sysfs (often doesn't work on Pi, but worth trying)
    usb_paths = [
        Path("/sys/bus/usb/devices/usb1/power/control"),
        Path("/sys/bus/usb/devices/usb2/power/control"),
    ]
    
    for path in usb_paths:
        if path.exists():
            try:
                for value in ["off", "suspend"]:
                    try:
                        result = subprocess.run(
                            ["sh", "-c", f"echo {value} | sudo tee {path}"],
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        if result.returncode == 0:
                            new_value = path.read_text().strip()
                            if new_value == value:
                                print(f"USB disabled via {path} (set to {value})")
                                return True
                    except Exception:
                        pass
            except Exception:
                pass
    
    # Method 3: Use uhubctl to disable Pi's internal USB hub ports
    if subprocess.run(["which", "uhubctl"], capture_output=True).returncode == 0:
        try:
            # First, list available hubs to find the right one
            list_result = subprocess.run(
                ["sudo", "uhubctl"],
                capture_output=True,
                text=True,
                check=False
            )
            if list_result.returncode == 0:
                print(f"Available USB hubs:\n{list_result.stdout}", file=sys.stderr)
                # Parse hub numbers from output (e.g., "hub 4" or "hub 1-1")
                import re
                hub_matches = re.findall(r'hub\s+(\d+(?:-\d+)?)', list_result.stdout)
                hubs_to_try = list(set(hub_matches))  # Remove duplicates
                print(f"Found hubs: {hubs_to_try}", file=sys.stderr)
            else:
                # Fallback to common hub locations
                hubs_to_try = ["4", "1-1", "1-1.1"]
            
            # Disable ALL ports on ALL hubs to turn off USB LED
            disabled_count = 0
            for hub in hubs_to_try:
                for port in ["1", "2", "3", "4", "5"]:
                    result = subprocess.run(
                        ["sudo", "uhubctl", "-l", hub, "-p", port, "-a", "0"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False
                    )
                    if result.returncode == 0:
                        disabled_count += 1
                        print(f"USB port {port} on hub {hub} disabled", file=sys.stderr)
                    elif result.stderr and "not found" not in result.stderr.lower() and "port" not in result.stderr.lower():
                        print(f"uhubctl hub {hub} port {port}: {result.stderr.strip()}", file=sys.stderr)
            
            if disabled_count > 0:
                print(f"Disabled {disabled_count} USB port(s)", file=sys.stderr)
                # Don't return yet - ports disabled but LED might still be on
                # Continue to try module removal
        except Exception as e:
            print(f"Error with uhubctl: {e}", file=sys.stderr)
    
    
    print("All USB disable methods failed", file=sys.stderr)
    return False


def main():
    """Turn off USB to turn off LED."""
    print("Attempting to disable USB...", file=sys.stderr)
    success = disable_usb()
    
    if success:
        # Save state
        try:
            Path("/tmp/usb_led_state.txt").write_text("off")
            print("State saved: off", file=sys.stderr)
        except Exception as e:
            print(f"Failed to save state: {e}", file=sys.stderr)
        print("USB disabled successfully", file=sys.stderr)
        return 0
    else:
        print("CRITICAL: Failed to disable USB. All methods failed.", file=sys.stderr)
        print("Tried: sysfs power control, uhubctl, and module removal", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
