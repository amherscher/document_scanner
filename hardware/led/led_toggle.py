from __future__ import annotations
import subprocess
import sys
from pathlib import Path




def main():
    script_dir = Path(__file__).resolve().parent
    if script_dir.name == "led":
        app_root = script_dir.parent.parent
    else:
        app_root = script_dir
    
    disable_script = app_root / "disable_usb.sh"
    if not disable_script.exists():
        disable_script = app_root / "scripts" / "disable_usb.sh"
    
    if not disable_script.exists():
        print(f"ERROR: disable_usb.sh not found at {disable_script}", file=sys.stderr)
        return 1
    
    cmd = ["sudo", "/bin/bash", str(disable_script)]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        Path("/tmp/usb_led_state.txt").write_text("off")
    else:
        print(f"ERROR: Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(f"ERROR: Exit code: {result.returncode}", file=sys.stderr)
        print(f"ERROR: stderr: {result.stderr}", file=sys.stderr)
        print(f"ERROR: stdout: {result.stdout}", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
