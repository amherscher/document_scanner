from __future__ import annotations
import subprocess
import sys
from pathlib import Path


"""
Turn OFF Raspberry Pi's USB subsystem to turn off the built-in USB LED.

This script disables USB power on the Pi by calling disable_usb.sh
"""


def main():
    """Turn off USB to turn off LED."""
    script_dir = Path(__file__).resolve().parent
    disable_script = script_dir / "disable_usb.sh"
    
    if not disable_script.exists():
        print(f"Error: {disable_script} not found", file=sys.stderr)
        return 1
    
    print("Attempting to disable USB...", file=sys.stderr)
    
    result = subprocess.run(
        ["sudo", "bash", str(disable_script)],
        capture_output=True,
        text=True,
        check=False
    )
    
    # Print output to stderr so it shows in Flask logs
    if result.stdout:
        print(result.stdout.strip(), file=sys.stderr)
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    
    if result.returncode == 0:
        # Save state
        try:
            Path("/tmp/usb_led_state.txt").write_text("off")
            print("State saved: off", file=sys.stderr)
        except Exception as e:
            print(f"Failed to save state: {e}", file=sys.stderr)
        print("USB disabled successfully", file=sys.stderr)
        return 0
    else:
        print("Failed to disable USB", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
