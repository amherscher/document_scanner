from __future__ import annotations
import subprocess
import sys
from pathlib import Path




def main():
    script_dir = Path(__file__).resolve().parent
    result = subprocess.run(
        ["sudo", "bash", str(script_dir / "disable_usb.sh")],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        Path("/tmp/usb_led_state.txt").write_text("off")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
