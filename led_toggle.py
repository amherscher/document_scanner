from __future__ import annotations
import os
import subprocess
import sys
import re
from pathlib import Path


"""
USB LED toggle - Simply disable/enable USB port power to turn LED off/on.

Configuration via environment variables:
- HUB: USB hub location (e.g., "1-1") - find with: sudo uhubctl
- PORT: USB port number (e.g., "2") - find with: sudo uhubctl

Usage:
  export HUB="1-1"
  export PORT="2"
  python3 led_toggle.py
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


def get_usb_port_state(hub: str, port: str) -> bool | None:
    """Get current USB port power state. Returns True if on, False if off, None if error."""
    if not check_command("uhubctl"):
        return None
    
    try:
        result = subprocess.run(
            ["sudo", "uhubctl", "-l", hub],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            return None
        
        # Parse output to find port state
        # Look for line like: "Port 2: 0000 off  power"
        pattern = rf"Port {port}:\s+\d+\s+(on|off)"
        match = re.search(pattern, result.stdout)
        if match:
            return match.group(1) == "on"
        return None
    except Exception as e:
        print(f"Error reading port state: {e}", file=sys.stderr)
        return None


def set_usb_port_power(hub: str, port: str, state: bool) -> bool:
    """Set USB port power state. Returns True if successful."""
    if not check_command("uhubctl"):
        print("uhubctl not installed. Install with: sudo apt-get install -y uhubctl", file=sys.stderr)
        return False
    
    action = "1" if state else "0"
    state_str = "on" if state else "off"
    
    try:
        result = subprocess.run(
            ["sudo", "uhubctl", "-l", hub, "-p", port, "-a", action],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print(f"USB port {port} on hub {hub} turned {state_str}")
            return True
        else:
            print(f"Failed to turn {state_str} USB port: {result.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error setting port power: {e}", file=sys.stderr)
        return False


def toggle_usb_power(hub: str, port: str) -> bool:
    """Toggle USB port power: if on, turn off; if off, turn on."""
    current_state = get_usb_port_state(hub, port)
    
    if current_state is None:
        # If we can't read state, use a state file to track it
        state_file = Path("/tmp/usb_led_state.txt")
        try:
            if state_file.exists():
                saved_state = state_file.read_text().strip() == "on"
                new_state = not saved_state
            else:
                # Default: assume port is on, so turn it off
                new_state = False
        except Exception:
            # Fallback: just turn off (assuming it's on)
            new_state = False
        
        success = set_usb_port_power(hub, port, new_state)
        if success:
            # Save state
            try:
                state_file.write_text("on" if new_state else "off")
            except Exception:
                pass
        return success
    
    # Toggle: if on, turn off; if off, turn on
    new_state = not current_state
    success = set_usb_port_power(hub, port, new_state)
    
    # Save state for future reference
    if success:
        state_file = Path("/tmp/usb_led_state.txt")
        try:
            state_file.write_text("on" if new_state else "off")
        except Exception:
            pass
    
    return success


def main():
    """Main entry point - toggle USB port power."""
    hub = os.environ.get("HUB", "").strip()
    port = os.environ.get("PORT", "").strip()
    
    if not hub or not port:
        print("USB LED toggle requires HUB and PORT environment variables.", file=sys.stderr)
        print("", file=sys.stderr)
        print("To find your USB hub and port:", file=sys.stderr)
        print("  1. Run: sudo uhubctl", file=sys.stderr)
        print("  2. Find your LED device and note the hub location (e.g., '1-1') and port number", file=sys.stderr)
        print("  3. Set environment variables:", file=sys.stderr)
        print("     export HUB='1-1'", file=sys.stderr)
        print("     export PORT='2'", file=sys.stderr)
        print("  4. Run this script again", file=sys.stderr)
        return 1
    
    if toggle_usb_power(hub, port):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
