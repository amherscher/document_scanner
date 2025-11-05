from __future__ import annotations
import subprocess


"""
Best-effort USB LED toggle.
Option A: If your hub supports per-port power control, install uhubctl:
sudo apt-get install -y uhubctl
# set HUB and PORT envs in the systemd unit, e.g., HUB=1-1, PORT=2
Option B: Replace the command below with your USB LED controller CLI.
"""


import os
HUB = os.environ.get("HUB", "")
PORT = os.environ.get("PORT", "")


if HUB and PORT:
# Toggle cycle: off -> on or on -> off (two commands)
    try:
        subprocess.call(["uhubctl", "-l", HUB, "-p", PORT, "-a", "0"]) # off
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to turn off LED: {e}") from e
    except Exception as e:
        raise Exception(f"Failed to turn off LED: {e}") from e
    try:
        subprocess.call(["uhubctl", "-l", HUB, "-p", PORT, "-a", "1"]) # on
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to turn on LED: {e}") from e
    except Exception as e:
        raise Exception(f"Failed to turn on LED: {e}") from e
    except Exception as e:
        raise Exception(f"Failed to turn on LED: {e}") from e
else:
# Fallback: No-op; log to stdout so the UI shows success
    try:
        print("LED toggle requested (no hub control configured).")
    except Exception as e:
        raise Exception(f"Failed to print message: {e}") from e