from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path


"""
Toggle Raspberry Pi's USB subsystem to control the built-in USB LED.

This script disables/enables the Pi's USB ports to turn the USB LED off/on.
"""


def find_pi_usb_controller() -> Path | None:
    """Find the Raspberry Pi's USB controller power control file."""
    # Common locations for USB controller power control
    usb_paths = [
        Path("/sys/bus/usb/devices/usb1/power/control"),
        Path("/sys/bus/usb/devices/usb2/power/control"),
    ]
    
    for path in usb_paths:
        if path.exists():
            return path
    
    return None


def get_usb_power_state() -> bool | None:
    """Get current USB power state. Returns True if on, None if can't determine."""
    controller = find_pi_usb_controller()
    if controller:
        try:
            state = controller.read_text().strip()
            return state == "on" or state == "auto"
        except Exception:
            pass
    
    # Try uhubctl on Pi's internal hub
    if subprocess.run(["which", "uhubctl"], capture_output=True).returncode == 0:
        try:
            result = subprocess.run(
                ["sudo", "uhubctl"],
                capture_output=True,
                text=True,
                check=False
            )
            # If we can list hubs, assume USB is on
            if result.returncode == 0 and "hub" in result.stdout.lower():
                return True
        except Exception:
            pass
    
    # Check state file as fallback
    state_file = Path("/tmp/usb_led_state.txt")
    if state_file.exists():
        try:
            return state_file.read_text().strip() == "on"
        except Exception:
            pass
    
    return None


def set_usb_power_state(state: bool) -> bool:
    """Set USB power state by disabling/enabling USB controller."""
    controller = find_pi_usb_controller()
    state_str = "on" if state else "off"
    
    if controller:
        try:
            # Write "on" or "auto" to enable, "suspend" to disable
            value = "auto" if state else "suspend"
            controller.write_text(value)
            print(f"USB controller set to {state_str} via sysfs")
            return True
        except PermissionError:
            print("Permission denied. Try running with sudo or ensure user has access.", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error setting USB power via sysfs: {e}", file=sys.stderr)
    
    # Fallback: Use uhubctl on Pi's internal USB hub
    if subprocess.run(["which", "uhubctl"], capture_output=True).returncode == 0:
        # Try to find Pi's internal hub (usually 1-1)
        try:
            result = subprocess.run(
                ["sudo", "uhubctl"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                # Look for hub 1-1 (Pi's internal hub) and try to control all ports
                # Or disable the hub itself
                action = "1" if state else "0"
                # Try hub 1-1, port 1 (common Pi internal hub configuration)
                ports = ["1", "2", "3", "4"]  # Try common port numbers
                success = False
                for port in ports:
                    result = subprocess.run(
                        ["sudo", "uhubctl", "-l", "1-1", "-p", port, "-a", action],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False
                    )
                    if result.returncode == 0:
                        success = True
                
                if success:
                    print(f"USB ports set to {state_str} via uhubctl")
                    return True
        except Exception as e:
            print(f"Error using uhubctl: {e}", file=sys.stderr)
    
    # Last resort: try disabling USB via modprobe (requires root)
    if not state:
        try:
            # Unload USB modules (this will disable USB entirely)
            subprocess.run(["sudo", "modprobe", "-r", "ohci_hcd", "uhci_hcd"], 
                          check=False, capture_output=True)
            subprocess.run(["sudo", "modprobe", "-r", "xhci_hcd"], 
                          check=False, capture_output=True)
            print("USB disabled via module removal")
            return True
        except Exception:
            pass
    else:
        try:
            # Reload USB modules
            subprocess.run(["sudo", "modprobe", "ohci_hcd", "uhci_hcd"], 
                          check=False, capture_output=True)
            subprocess.run(["sudo", "modprobe", "xhci_hcd"], 
                          check=False, capture_output=True)
            print("USB enabled via module loading")
            return True
        except Exception:
            pass
    
    return False


def toggle_usb_power() -> bool:
    """Toggle USB power: if on, turn off; if off, turn on."""
    current_state = get_usb_power_state()
    
    if current_state is None:
        # Can't determine state, use state file
        state_file = Path("/tmp/usb_led_state.txt")
        try:
            if state_file.exists():
                saved_state = state_file.read_text().strip() == "on"
                new_state = not saved_state
            else:
                # Default: assume USB is on, so turn it off
                new_state = False
        except Exception:
            new_state = False
    else:
        # Toggle based on current state
        new_state = not current_state
    
    success = set_usb_power_state(new_state)
    
    # Save state
    if success:
        state_file = Path("/tmp/usb_led_state.txt")
        try:
            state_file.write_text("on" if new_state else "off")
        except Exception:
            pass
    
    return success


def main():
    """Main entry point - toggle USB power to control Pi's LED."""
    if os.geteuid() != 0:
        print("Warning: This script may need root privileges to control USB power.", file=sys.stderr)
        print("If it fails, try running with: sudo python3 led_toggle.py", file=sys.stderr)
        print("", file=sys.stderr)
    
    if toggle_usb_power():
        print("USB LED toggled successfully")
        return 0
    else:
        print("Failed to toggle USB power. Check permissions and USB controller access.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
