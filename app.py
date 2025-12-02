from __future__ import annotations
import os
from pathlib import Path
import subprocess
import time
import shutil
from flask import Flask, jsonify, render_template, request, send_from_directory

try:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ml_pipeline.inference import InvoiceCategorizer
    from ml_pipeline.utils.ocr_extract import extract_text_from_invoice, extract_text_with_details_from_invoice
    from ml_pipeline.utils.receipt_parser import parse_receipt
    from ml_pipeline.utils.expense_tracker import save_expense, get_expenses, get_expense_summary
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    InvoiceCategorizer = None
    extract_text_from_invoice = None
    extract_text_with_details_from_invoice = None
    parse_receipt = None
    save_expense = None
    get_expenses = None
    get_expense_summary = None

APP_ROOT = Path(__file__).resolve().parent
WORKDIR = Path(os.environ.get("SCANS_DIR", str(APP_ROOT / "scans")))
WORKDIR.mkdir(parents=True, exist_ok=True)
TOKEN = os.environ.get("PI_SCAN_TOKEN", "changeme")
_default_model = str(APP_ROOT / "checkpoints" / "best_model.pt")
if not Path(_default_model).exists():
    _default_model = str(APP_ROOT / "ml_pipeline" / "checkpoints" / "best_model.pt")
MODEL_PATH = os.environ.get("INVOICE_MODEL_PATH", _default_model)
SERVER_HOST = os.environ.get("SYNC_SERVER_HOST", "10.29.0.1")
SERVER_USER = os.environ.get("SYNC_SERVER_USER", "amherscher")
SERVER_DIR = os.environ.get("SYNC_SERVER_DIR", "/home/data/Purdue/pi/scans")
SYNC_ENABLED = os.environ.get("SYNC_ENABLED", "false").lower() == "true"
if os.environ.get("DEBUG_SYNC"):
    print(f"DEBUG: SYNC_ENABLED env var = '{os.environ.get('SYNC_ENABLED', 'NOT SET')}'")
    print(f"DEBUG: SYNC_ENABLED parsed = {SYNC_ENABLED}")

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
    if ML_AVAILABLE and Path(MODEL_PATH).exists():
        return render_template("server.html", token=(None if os.getenv("PI_SCAN_REQUIRE_AUTH") else TOKEN))
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
    scan_script = APP_ROOT / "scan_once.py"
    if not scan_script.exists():
        scan_script = APP_ROOT / "scripts" / "scan_once.py"
    if not scan_script.exists():
        return jsonify({"ok": False, "error": f"scan_once.py not found in {APP_ROOT}"}), 500
    try:
        result_proc = subprocess.run(["/usr/bin/python3", str(scan_script), "--workdir", str(WORKDIR), "--basename", base, "--zoom", str(zoom)], capture_output=True, text=True, check=True, timeout=30)
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "Scan timeout"}), 500
    except subprocess.CalledProcessError as e:
        return jsonify({"ok": False, "error": f"Scan failed: {e.stderr[:200]}"}), 500
    result = {"ok": True, "saved": [f"{base}.jpg"], "workdir": str(WORKDIR)}  # PDF removed - JPG is better for OCR
    if data.get("classify", True) and ML_AVAILABLE:
        classification = classify_invoice_file(f"{base}.jpg", None)  # PDF not needed - JPG is better for OCR
        if classification:
            result["classification"] = classification
    if SYNC_ENABLED and (data.get("auto_sync", False) or os.environ.get("AUTO_SYNC", "false").lower() == "true"):
        subprocess.run(["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", f"{SERVER_USER}@{SERVER_HOST}", "mkdir", "-p", SERVER_DIR], capture_output=True, timeout=10)
        synced_files = []
        for filename in result["saved"]:
            file_path = WORKDIR / filename
            if file_path.exists():
                sync_result = subprocess.run(["rsync", "-avz", "--remove-source-files", str(file_path), f"{SERVER_USER}@{SERVER_HOST}:{SERVER_DIR}/"], capture_output=True, text=True, timeout=60)
                if sync_result.returncode == 0:
                    synced_files.append(filename)
        if synced_files:
            result["synced"] = synced_files
    return jsonify(result)

@app.post("/api/led/toggle")
def led_toggle():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    state_file = Path("/tmp/usb_led_state.txt")
    current_state = state_file.read_text().strip() if state_file.exists() else "on"
    
    if current_state == "on":
        script_name = "led_toggle.py"
        new_state = "off"
    else:
        script_name = "led_on.py"
        new_state = "on"
    
    script = APP_ROOT / script_name
    if not script.exists():
        script = APP_ROOT / "hardware" / "led" / script_name
    if not script.exists():
        return jsonify({"ok": False, "error": f"Script not found: {script_name}"})
    
    result = subprocess.run(["sudo", "/usr/bin/python3", str(script)], capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        error_msg = result.stderr.strip() if result.stderr else result.stdout.strip() if result.stdout else "LED toggle failed"
        full_error = f"Exit code: {result.returncode}. {error_msg}"
        if "password" in error_msg.lower() or "sudo" in error_msg.lower():
            full_error += " (Passwordless sudo may not be configured. Run ./scripts/setup_led_sudo.sh)"
        return jsonify({"ok": False, "error": full_error[:400], "stdout": result.stdout[:300], "stderr": result.stderr[:300], "script": str(script)})
    
    return jsonify({"ok": True, "state": new_state, "action": "turned off" if new_state == "off" else "turned on"})

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
    # PDF not needed - JPG is better for OCR
    classification = classify_invoice_file(jpg_path.name, None)  # Always use JPG for OCR
    return jsonify({"ok": True, **classification}) if classification else jsonify({"ok": False, "error": "classification failed"}), 500

def classify_invoice_file(jpg_filename: str, pdf_filename: str = None) -> dict:
    categorizer = get_categorizer()
    if not categorizer:
        return None
    jpg_path = WORKDIR / jpg_filename
    pdf_path = WORKDIR / pdf_filename if pdf_filename else None
    # Use enhanced OCR with bounding box data for better vendor extraction
    if extract_text_with_details_from_invoice and jpg_path.exists():
        text, word_data = extract_text_with_details_from_invoice(jpg_path, pdf_path) if extract_text_with_details_from_invoice else ("", [])
    else:
        text = extract_text_from_invoice(jpg_path, pdf_path) if extract_text_from_invoice else ""
        word_data = []
    if categorizer.model_type == "image":
        category, probs = categorizer.predict_image(str(jpg_path), return_probs=True)
    elif categorizer.model_type == "hybrid":
        category, probs = categorizer.predict_hybrid(text, str(jpg_path), return_probs=True) if text else categorizer.predict_image(str(jpg_path), return_probs=True)
    else:
        if not text:
            return None
        category, probs = categorizer.predict_text(text, return_probs=True)
    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:3]
    receipt_data = parse_receipt(text, word_data) if text and parse_receipt else {}
    classification_result = {
        "category": category,
        "confidence": round(probs[category], 4),
        "top_predictions": [{"category": cat, "confidence": round(prob, 4)} for cat, prob in sorted_probs],
        "text_extracted": len(text) > 0,
        "text_length": len(text),
        "receipt_data": receipt_data
    }
    
    if save_expense:
        save_expense(WORKDIR, jpg_filename, classification_result, receipt_data)
        
        # Move classified files to subdirectory to avoid reclassification
        classified_dir = WORKDIR / "classified"
        classified_dir.mkdir(exist_ok=True)
        
        try:
            # Move JPG
            if jpg_path.exists():
                dest_jpg = classified_dir / jpg_path.name
                shutil.move(str(jpg_path), str(dest_jpg))
            
            # Move PDF if it exists
            if pdf_path and pdf_path.exists():
                dest_pdf = classified_dir / pdf_path.name
                shutil.move(str(pdf_path), str(dest_pdf))
        except Exception as e:
            pass  # Silently fail - file might already be moved
    
    return classification_result

@app.post("/api/sync")
def sync_to_server():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    if not SYNC_ENABLED:
        return jsonify({"ok": False, "error": "sync not enabled"}), 400
    
    test_ssh = subprocess.run(["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", f"{SERVER_USER}@{SERVER_HOST}", "test", "-d", SERVER_DIR], capture_output=True, timeout=10)
    if test_ssh.returncode != 0:
        subprocess.run(["ssh", "-o", "ConnectTimeout=5", f"{SERVER_USER}@{SERVER_HOST}", "mkdir", "-p", SERVER_DIR], capture_output=True, timeout=10)
    
    # Skip files in classified/ subdirectory (already processed)
    classified_dir = WORKDIR / "classified"
    files_to_sync = [f for f in WORKDIR.glob("*") if f.is_file() and f.suffix in ['.jpg', '.jpeg', '.png', '.pdf'] and classified_dir not in f.parents]
    if not files_to_sync:
        return jsonify({"ok": True, "synced": 0, "failed": 0})
    
    synced = []
    failed = []
    for file_path in files_to_sync:
        result = subprocess.run(["rsync", "-avz", "--remove-source-files", str(file_path), f"{SERVER_USER}@{SERVER_HOST}:{SERVER_DIR}/"], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            synced.append(file_path.name)
        else:
            failed.append({"file": file_path.name, "error": result.stderr[:200] if result.stderr else "unknown error"})
    
    return jsonify({"ok": True, "synced": len(synced), "synced_files": synced, "failed": len(failed), "failed_files": failed})

@app.get("/api/sync/status")
def sync_status():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    # Skip files in classified/ subdirectory
    classified_dir = WORKDIR / "classified"
    files = [f.name for f in WORKDIR.glob("*") if f.is_file() and f.suffix in ['.jpg', '.jpeg', '.png', '.pdf'] and classified_dir not in f.parents]
    ssh_test = subprocess.run(["ssh", "-o", "ConnectTimeout=3", "-o", "BatchMode=yes", f"{SERVER_USER}@{SERVER_HOST}", "echo", "ok"], capture_output=True, timeout=5)
    dir_test = subprocess.run(["ssh", "-o", "ConnectTimeout=3", "-o", "BatchMode=yes", f"{SERVER_USER}@{SERVER_HOST}", "test", "-d", SERVER_DIR], capture_output=True, timeout=5)
    env_sync = os.environ.get("SYNC_ENABLED", "NOT SET")
    return jsonify({
        "ok": True,
        "sync_enabled": SYNC_ENABLED,
        "sync_enabled_env": env_sync,
        "server_host": SERVER_HOST,
        "server_user": SERVER_USER,
        "server_dir": SERVER_DIR,
        "files_ready": len(files),
        "ssh_connected": ssh_test.returncode == 0,
        "server_dir_exists": dir_test.returncode == 0,
        "sync_target": f"{SERVER_USER}@{SERVER_HOST}:{SERVER_DIR}" if SYNC_ENABLED else "not configured"
    })

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

@app.get("/api/expenses")
def expenses():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    limit = request.args.get("limit", type=int)
    expenses_list = get_expenses(WORKDIR, limit) if get_expenses else []
    return jsonify({"ok": True, "expenses": expenses_list, "count": len(expenses_list)})

@app.get("/api/expenses/summary")
def expenses_summary():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    summary = get_expense_summary(WORKDIR) if get_expense_summary else {}
    return jsonify({"ok": True, **summary})

@app.get("/api/expenses/download")
def download_expenses():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    expense_file = WORKDIR / "expenses.csv"
    if not expense_file.exists():
        return jsonify({"ok": False, "error": "No expenses file found"}), 404
    return send_from_directory(str(WORKDIR), "expenses.csv", as_attachment=True)

@app.get("/api/files/list")
def list_files():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    files = []
    expenses = {}
    if get_expenses:
        try:
            expenses_list = get_expenses(WORKDIR)
            expenses = {e.get("filename"): e for e in expenses_list}
        except:
            pass
    # Skip files in classified/ subdirectory
    classified_dir = WORKDIR / "classified"
    for ext in [".jpg", ".jpeg", ".png", ".pdf"]:
        for file_path in WORKDIR.glob(f"*{ext}"):
            if classified_dir in file_path.parents:
                continue
            if file_path.suffix == ".pdf" and (WORKDIR / f"{file_path.stem}.jpg").exists():
                continue
            file_info = {
                "name": file_path.name,
                "size": f"{file_path.stat().st_size / 1024:.1f} KB",
                "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(file_path.stat().st_mtime))
            }
            exp = expenses.get(file_path.name)
            if exp:
                file_info["category"] = exp.get("category")
                file_info["confidence"] = exp.get("confidence", 0)
                file_info["amount"] = exp.get("amount")
            else:
                file_info["category"] = None
            files.append(file_info)
    files.sort(key=lambda x: x["modified"], reverse=True)
    return jsonify({"ok": True, "files": files})

@app.post("/api/classify/all")
def classify_all():
    if not require_auth(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    if not ML_AVAILABLE:
        return jsonify({"ok": False, "error": "ML not available"}), 503
    # Skip files in classified/ subdirectory
    classified_dir = WORKDIR / "classified"
    image_files = [f for f in (list(WORKDIR.glob("*.jpg")) + list(WORKDIR.glob("*.jpeg")) + list(WORKDIR.glob("*.png"))) 
                  if classified_dir not in f.parents]
    pdf_files = [f for f in list(WORKDIR.glob("*.pdf")) 
                if classified_dir not in f.parents]
    files_to_process = []
    for img_file in image_files:
        base_name = img_file.stem
        pdf_file = WORKDIR / f"{base_name}.pdf"
        files_to_process.append((img_file.name, pdf_file.name if pdf_file.exists() else None))
    for pdf_file in pdf_files:
        base_name = pdf_file.stem
        img_file = WORKDIR / f"{base_name}.jpg"
        if not img_file.exists():
            files_to_process.append((None, pdf_file.name))
    classified = 0
    failed = 0
    for jpg_name, pdf_name in files_to_process:
        try:
            result = classify_invoice_file(jpg_name, pdf_name)
            if result:
                classified += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
    return jsonify({"ok": True, "classified": classified, "failed": failed})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
