from __future__ import annotations
import os
from pathlib import Path
import subprocess
import time
from flask import Flask, jsonify, render_template, request, send_from_directory

try:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ml_pipeline.inference import InvoiceCategorizer
    from ml_pipeline.utils.ocr_extract import extract_text_from_invoice
    from ml_pipeline.utils.receipt_parser import parse_receipt
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    InvoiceCategorizer = None
    extract_text_from_invoice = None
    parse_receipt = None

APP_ROOT = Path(__file__).resolve().parent
WORKDIR = Path(os.environ.get("SCANS_DIR", str(APP_ROOT / "scans")))
WORKDIR.mkdir(parents=True, exist_ok=True)
TOKEN = os.environ.get("PI_SCAN_TOKEN", "changeme")
MODEL_PATH = os.environ.get("INVOICE_MODEL_PATH", str(APP_ROOT / "ml_pipeline" / "checkpoints" / "best_model.pt"))
SERVER_HOST = os.environ.get("SYNC_SERVER_HOST", "10.29.0.1")
SERVER_USER = os.environ.get("SYNC_SERVER_USER", "pi")
SERVER_DIR = os.environ.get("SYNC_SERVER_DIR", "/opt/scanner/scans")
SYNC_ENABLED = os.environ.get("SYNC_ENABLED", "false").lower() == "true"

app = Flask(__name__, template_folder=str(APP_ROOT / "templates"), static_folder=str(APP_ROOT / "static"))
_categorizer = None

def require_auth(req) -> bool:
    token = req.headers.get("X-Auth") or req.args.get("token")
    return (TOKEN and token == TOKEN) or (TOKEN == "changeme" and not os.getenv("PI_SCAN_REQUIRE_AUTH"))

def get_categorizer():
    global _categorizer
    if not ML_AVAILABLE or _categorizer:
        return _categorizer
    model_path = Path(MODEL_PATH)
    if model_path.exists():
        _categorizer = InvoiceCategorizer(str(model_path))
    return _categorizer

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
    path = (request.get_json(force=True, silent=True) or {}).get("path")
    if not path:
        return jsonify({"ok": False, "error": "missing path"}), 400
    p = Path(path).expanduser()
    if p.is_absolute():
        try:
            p = p.resolve()
        except:
            pass
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
    subprocess.run(["/usr/bin/python3", str(APP_ROOT / "scripts" / "scan_once.py"), "--workdir", str(WORKDIR), "--basename", base, "--zoom", str(zoom)], check=True)
    result = {"ok": True, "saved": [f"{base}.jpg", f"{base}.pdf"], "workdir": str(WORKDIR)}
    if data.get("classify", True) and ML_AVAILABLE:
        classification = classify_invoice_file(f"{base}.jpg", f"{base}.pdf")
        if classification:
            result["classification"] = classification
    if (data.get("auto_sync", False) or os.environ.get("AUTO_SYNC", "false").lower() == "true") and SYNC_ENABLED:
        for filename in result["saved"]:
            file_path = WORKDIR / filename
            if file_path.exists():
                subprocess.run(["rsync", "-avz", "--remove-source-files", str(file_path), f"{SERVER_USER}@{SERVER_HOST}:{SERVER_DIR}/"], capture_output=True, timeout=30)
    return jsonify(result)

@app.post("/api/led/toggle")
def led_toggle():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    state_file = Path("/tmp/usb_led_state.txt")
    current_state = state_file.read_text().strip() if state_file.exists() else "on"
    script = APP_ROOT / "hardware" / "led" / ("led_toggle.py" if current_state == "on" else "led_on.py")
    result = subprocess.run(["sudo", "/usr/bin/python3", str(script)], capture_output=True, text=True)
    return jsonify({"ok": result.returncode == 0})

@app.get("/downloads/<path:filename>")
def downloads(filename: str):
    return send_from_directory(str(WORKDIR), filename, as_attachment=True)

@app.post("/api/classify")
def classify():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    if not ML_AVAILABLE:
        return jsonify({"ok": False, "error": "ML not available"}), 503
    filename = (request.get_json(force=True, silent=True) or {}).get("filename")
    if not filename:
        return jsonify({"ok": False, "error": "missing filename"}), 400
    base_name = Path(filename).stem
    jpg_path = WORKDIR / f"{base_name}.jpg"
    if not jpg_path.exists():
        for ext in [".jpg", ".jpeg", ".png"]:
            alt_path = WORKDIR / f"{base_name}{ext}"
            if alt_path.exists():
                jpg_path = alt_path
                break
    if not jpg_path.exists():
        return jsonify({"ok": False, "error": "file not found"}), 404
    pdf_path = WORKDIR / f"{base_name}.pdf"
    classification = classify_invoice_file(jpg_path.name, pdf_path.name if pdf_path.exists() else None)
    return jsonify({"ok": True, **classification}) if classification else jsonify({"ok": False, "error": "classification failed"}), 500

def classify_invoice_file(jpg_filename: str, pdf_filename: str = None) -> dict:
    categorizer = get_categorizer()
    if not categorizer:
        return None
    jpg_path = WORKDIR / jpg_filename
    pdf_path = WORKDIR / pdf_filename if pdf_filename else None
    text = extract_text_from_invoice(jpg_path, pdf_path) if extract_text_from_invoice else ""
    if categorizer.model_type == "image":
        category, probs = categorizer.predict_image(str(jpg_path), return_probs=True)
    elif categorizer.model_type == "hybrid":
        category, probs = categorizer.predict_hybrid(text, str(jpg_path), return_probs=True) if text else categorizer.predict_image(str(jpg_path), return_probs=True)
    else:
        if not text:
            return None
        category, probs = categorizer.predict_text(text, return_probs=True)
    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:3]
    receipt_data = parse_receipt(text) if text and parse_receipt else {}
    return {
        "category": category,
        "confidence": round(probs[category], 4),
        "top_predictions": [{"category": cat, "confidence": round(prob, 4)} for cat, prob in sorted_probs],
        "text_extracted": len(text) > 0,
        "text_length": len(text),
        "receipt_data": receipt_data
    }

@app.post("/api/sync")
def sync_to_server():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    if not SYNC_ENABLED:
        return jsonify({"ok": False, "error": "sync not enabled"}), 400
    files_to_sync = [f for f in WORKDIR.glob("*") if f.is_file() and f.suffix in ['.jpg', '.jpeg', '.png', '.pdf']]
    if not files_to_sync:
        return jsonify({"ok": True, "synced": 0})
    synced = []
    for file_path in files_to_sync:
        result = subprocess.run(["rsync", "-avz", "--remove-source-files", str(file_path), f"{SERVER_USER}@{SERVER_HOST}:{SERVER_DIR}/"], capture_output=True, timeout=30)
        if result.returncode == 0:
            synced.append(file_path.name)
    return jsonify({"ok": True, "synced": len(synced), "synced_files": synced})

@app.get("/api/sync/status")
def sync_status():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    files = [f.name for f in WORKDIR.glob("*") if f.is_file() and f.suffix in ['.jpg', '.jpeg', '.png', '.pdf']]
    return jsonify({"ok": True, "sync_enabled": SYNC_ENABLED, "server_host": SERVER_HOST, "files_ready": len(files)})

@app.get("/api/ml/status")
def ml_status():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    categorizer = get_categorizer()
    status = {"ok": True, "ml_available": ML_AVAILABLE, "model_path": MODEL_PATH, "model_exists": Path(MODEL_PATH).exists(), "model_loaded": categorizer is not None}
    if categorizer:
        status["categories"] = categorizer.categories
        status["model_type"] = categorizer.model_type
    return jsonify(status)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
