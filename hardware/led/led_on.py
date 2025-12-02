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
    
    enable_script = app_root / "enable_usb.sh"
    if not enable_script.exists():
        enable_script = app_root / "scripts" / "enable_usb.sh"
    
    if not enable_script.exists():
        print(f"ERROR: enable_usb.sh not found at {enable_script}", file=sys.stderr)
        return 1
    
    cmd = ["sudo", "/bin/bash", str(enable_script)]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        Path("/tmp/usb_led_state.txt").write_text("on")
    else:
        print(f"ERROR: Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(f"ERROR: Exit code: {result.returncode}", file=sys.stderr)
        print(f"ERROR: stderr: {result.stderr}", file=sys.stderr)
        print(f"ERROR: stdout: {result.stdout}", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
