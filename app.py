from __future__ import annotations
import os
from pathlib import Path
import subprocess
import time

from flask import Flask, jsonify, render_template, request, send_from_directory
import sys


APP_ROOT = Path(__file__).resolve().parent
CONFIG = APP_ROOT / "config.ini"
WORKDIR = APP_ROOT / "scans"
TOKEN = os.environ.get("PI_SCAN_TOKEN", "changeme") # set in systemd unit


app = Flask(__name__, template_folder=str(APP_ROOT / "templates"), static_folder=str(APP_ROOT / "static"))


# --- helpers -----------------------------------------------------------------
def require_auth(req) -> bool:
    token = req.headers.get("X-Auth") or req.args.get("token")
    return (TOKEN and token == TOKEN) or (TOKEN == "changeme" and not os.getenv("PI_SCAN_REQUIRE_AUTH"))


# --- routes ------------------------------------------------------------------
@app.get("/")
def home():
    return render_template("index.html", token=(None if os.getenv("PI_SCAN_REQUIRE_AUTH") else TOKEN))


@app.get("/api/status")
def status():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    WORKDIR.mkdir(parents=True, exist_ok=True)
    files = sorted([p.name for p in WORKDIR.glob("*") if p.is_file()], reverse=True)[:20]
    return jsonify({"ok": True, "workdir": str(WORKDIR), "recent": files})


@app.post("/api/set_workdir")
def set_workdir():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    data = request.get_json(force=True, silent=True) or {}
    path = data.get("path")
    if not path:
        return jsonify({"ok": False, "error": "missing path"}), 400
    p = Path(path).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    global WORKDIR
    WORKDIR = p
    return jsonify({"ok": True, "workdir": str(WORKDIR)})


@app.post("/api/scan")
def scan():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    ts = time.strftime("%Y%m%d_%H%M%S")
    base = f"scan_{ts}"
    # Call the capture pipeline script
    try:
        subprocess.run(
        ["/usr/bin/python3", str(APP_ROOT / "scan_once.py"),
        "--workdir", str(WORKDIR),
            "--basename", base
            ], check=True)
        return jsonify({"ok": True, "saved": [f"{base}.jpg", f"{base}.pdf"], "workdir": str(WORKDIR)})
    except subprocess.CalledProcessError as e:
            return jsonify({"ok": False, "error": str(e)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.post("/api/led/toggle")
def led_toggle():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    try:
        # Check current state to determine which script to run
        state_file = Path("/tmp/usb_led_state.txt")
        
        current_state = "on"  # Default to on
        if state_file.exists():
            try:
                current_state = state_file.read_text().strip()
            except Exception:
                pass
        
        # Toggle: if on, turn off; if off, turn on
        if current_state == "on":
            script = APP_ROOT / "led_toggle.py"  # Turn off
        else:
            script = APP_ROOT / "led_on.py"     # Turn on
        
        env = os.environ.copy()
        result = subprocess.run(
            ["sudo", "/usr/bin/python3", str(script)],
            check=False,
            env=env,
            capture_output=True,
            text=True
        )
        
        # Log output for debugging
        output = result.stdout.strip() if result.stdout else ""
        error = result.stderr.strip() if result.stderr else ""
        
        # Print to console for debugging
        print(f"LED toggle script: {script.name}", file=sys.stderr)
        print(f"Return code: {result.returncode}", file=sys.stderr)
        if output:
            print(f"STDOUT: {output}", file=sys.stderr)
        if error:
            print(f"STDERR: {error}", file=sys.stderr)
        
        if result.returncode == 0:
            return jsonify({"ok": True, "message": output or "LED toggled", "stderr": error})
        else:
            error_msg = error or output or "Unknown error"
            print(f"LED toggle failed: {error_msg}", file=sys.stderr)
            return jsonify({"ok": False, "error": error_msg, "stdout": output, "stderr": error})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.get("/downloads/<path:filename>")
def downloads(filename: str):
# quick file server for saved scans
    return send_from_directory(str(WORKDIR), filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)