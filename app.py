from __future__ import annotations
import os
from pathlib import Path
import subprocess
import time
from flask import Flask, jsonify, render_template, request, send_from_directory


APP_ROOT = Path(__file__).resolve().parent
WORKDIR = APP_ROOT / "scans"
TOKEN = os.environ.get("PI_SCAN_TOKEN", "changeme")


app = Flask(__name__, template_folder=str(APP_ROOT / "templates"), static_folder=str(APP_ROOT / "static"))


def require_auth(req) -> bool:
    token = req.headers.get("X-Auth") or req.args.get("token")
    return (TOKEN and token == TOKEN) or (TOKEN == "changeme" and not os.getenv("PI_SCAN_REQUIRE_AUTH"))


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
    
    data = request.get_json(force=True, silent=True) or {}
    zoom = max(0.2, min(2.0, float(data.get("zoom", 0.3))))
    
    ts = time.strftime("%Y%m%d_%H%M%S")
    base = f"scan_{ts}"
    subprocess.run(
        ["/usr/bin/python3", str(APP_ROOT / "scan_once.py"),
         "--workdir", str(WORKDIR),
         "--basename", base,
         "--zoom", str(zoom)
        ], check=True)
    return jsonify({"ok": True, "saved": [f"{base}.jpg", f"{base}.pdf"], "workdir": str(WORKDIR)})


@app.post("/api/led/toggle")
def led_toggle():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    
    state_file = Path("/tmp/usb_led_state.txt")
    current_state = state_file.read_text().strip() if state_file.exists() else "on"
    script = APP_ROOT / ("led_toggle.py" if current_state == "on" else "led_on.py")
    
    result = subprocess.run(
        ["sudo", "/usr/bin/python3", str(script)],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": result.stderr or result.stdout or "Unknown error"})


@app.get("/downloads/<path:filename>")
def downloads(filename: str):
    return send_from_directory(str(WORKDIR), filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)