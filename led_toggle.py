from __future__ import annotations
import subprocess
import sys
from pathlib import Path


"""
Turn OFF Raspberry Pi's USB subsystem to turn off the built-in USB LED.

This script disables USB power on the Pi.
"""


def disable_usb() -> bool:
    """Disable USB power on the Raspberry Pi."""
    # Method 1: Use sysfs to suspend USB controller
    usb_paths = [
        Path("/sys/bus/usb/devices/usb1/power/control"),
        Path("/sys/bus/usb/devices/usb2/power/control"),
    ]
    
    for path in usb_paths:
        if path.exists():
            try:
                # Try writing directly first
                path.write_text("suspend")
                # Verify it worked
                if path.read_text().strip() in ["suspend", "auto"]:
                    print(f"USB disabled via {path}")
                    return True
            except PermissionError:
                # Try via echo through subprocess
                try:
                    result = subprocess.run(
                        ["sh", "-c", f"echo suspend | sudo tee {path}"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    if result.returncode == 0:
                        print(f"USB disabled via {path} (with sudo)")
                        return True
                except Exception:
                    pass
            except Exception as e:
                print(f"Error with {path}: {e}", file=sys.stderr)
    
    # Method 2: Use uhubctl to disable Pi's internal USB hub
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
            
            # Try common Pi USB hub locations
            for hub in ["1-1", "1-1.1", "1-1.2"]:
                for port in ["1", "2", "3", "4", "5"]:
                    result = subprocess.run(
                        ["sudo", "uhubctl", "-l", hub, "-p", port, "-a", "0"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False
                    )
                    if result.returncode == 0:
                        print(f"USB port {port} on hub {hub} disabled")
                        return True
                    elif result.stderr:
                        print(f"uhubctl hub {hub} port {port}: {result.stderr.strip()}", file=sys.stderr)
        except Exception as e:
            print(f"Error with uhubctl: {e}", file=sys.stderr)
    
    # Method 3: Unload USB modules (most aggressive)
    try:
        result = subprocess.run(
            ["sudo", "modprobe", "-r", "xhci_hcd"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print("USB disabled via xhci_hcd module removal")
            return True
        elif result.stderr:
            print(f"xhci_hcd removal: {result.stderr.strip()}", file=sys.stderr)
    except Exception as e:
        print(f"Error removing xhci_hcd: {e}", file=sys.stderr)
    
    try:
        result = subprocess.run(
            ["sudo", "modprobe", "-r", "ohci_hcd", "uhci_hcd"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print("USB disabled via OHCI/UHCI module removal")
            return True
        elif result.stderr:
            print(f"OHCI/UHCI removal: {result.stderr.strip()}", file=sys.stderr)
    except Exception as e:
        print(f"Error removing OHCI/UHCI: {e}", file=sys.stderr)
    
    return False


def main():
    """Turn off USB to turn off LED."""
    print("Attempting to disable USB...", file=sys.stderr)
    if disable_usb():
        # Save state
        try:
            Path("/tmp/usb_led_state.txt").write_text("off")
        except Exception:
            pass
        print("USB disabled successfully", file=sys.stderr)
        return 0
    else:
        print("Failed to disable USB. All methods failed.", file=sys.stderr)
        print("Tried: sysfs power control, uhubctl, and module removal", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
