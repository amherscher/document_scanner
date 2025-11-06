from __future__ import annotations
import os
from pathlib import Path
import subprocess
import time

from flask import Flask, jsonify, render_template, request, send_from_directory


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
        # Pass environment variables to the LED toggle script
        env = os.environ.copy()
        subprocess.run(
            ["/usr/bin/python3", str(APP_ROOT / "led_toggle.py")],
            check=True,
            env=env,
            capture_output=True,
            text=True
        )
        return jsonify({"ok": True})
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        return jsonify({"ok": False, "error": error_msg})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.get("/downloads/<path:filename>")
def downloads(filename: str):
# quick file server for saved scans
    return send_from_directory(str(WORKDIR), filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)