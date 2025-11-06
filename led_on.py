from __future__ import annotations
import subprocess
import sys
from pathlib import Path


"""
Turn ON Raspberry Pi's USB subsystem to turn on the built-in USB LED.

This script re-enables USB power on the Pi by calling enable_usb.sh
"""


def main():
    """Turn on USB to turn on LED."""
    script_dir = Path(__file__).resolve().parent
    enable_script = script_dir / "enable_usb.sh"
    
    if not enable_script.exists():
        print(f"Error: {enable_script} not found", file=sys.stderr)
        return 1
    
    print("Attempting to enable USB ports...", file=sys.stderr)
    
    result = subprocess.run(
        ["sudo", "bash", str(enable_script)],
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
            Path("/tmp/usb_led_state.txt").write_text("on")
            print("State saved: on", file=sys.stderr)
        except Exception as e:
            print(f"Failed to save state: {e}", file=sys.stderr)
        print("USB enabled successfully", file=sys.stderr)
        return 0
    else:
        print("Failed to enable USB", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
