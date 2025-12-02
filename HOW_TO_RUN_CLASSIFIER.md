# How to Run the Classifier

## Method 1: Command Line Tool (CLI)

### Classify a Single File
```bash
python3 scripts/classify.py --file scan_20251124_192338.jpg --scans_dir scans
```

### Classify All Files in Directory
```bash
python3 scripts/classify.py --all --scans_dir scans
```

### List Available Files (without classifying)
```bash
python3 scripts/classify.py --scans_dir scans
```

### Options:
- `--scans_dir`: Directory containing scans (default: `scans`)
- `--model`: Path to model file (default: `checkpoints/best_model.pt`)
- `--file`: Classify a specific file
- `--all`: Classify all files in the scans directory

### Example Output:
```
📄 scan_20251124_192338.jpg
  ✓ Category: Office Supplies | Amount: $7.24 (92.3% confidence)
  ✓ Vendor: Staples
  ✓ Date: 2025-11-24
  ✓ Saved to expenses.csv
```

---

## Method 2: Web API

### Using curl
```bash
# Classify a specific file
curl -X POST http://localhost:5000/api/classify \
  -H "Content-Type: application/json" \
  -H "X-Auth: changeme" \
  -d '{"filename": "scan_20251124_192338.jpg"}'
```

### Using Python requests
```python
import requests

response = requests.post(
    'http://localhost:5000/api/classify',
    json={'filename': 'scan_20251124_192338.jpg'},
    headers={'X-Auth': 'changeme'}
)
print(response.json())
```

### Response Format:
```json
{
  "ok": true,
  "category": "Office Supplies",
  "confidence": 0.9234,
  "top_predictions": [
    {"category": "Office Supplies", "confidence": 0.9234},
    {"category": "Hardware & Equipment", "confidence": 0.0456}
  ],
  "text_extracted": true,
  "text_length": 1234,
  "receipt_data": {
    "amounts": {"total": 7.24},
    "vendor": "Staples",
    "date": "2025-11-24"
  }
}
```

---

## Method 3: Batch Classification Script

### Classify All Scans
```bash
python3 scripts/classify_all_scans.py --scans_dir scans --model_path checkpoints/best_model.pt
```

This will:
- Process all image files in the scans directory
- Extract text using OCR
- Classify each invoice
- Parse receipt data
- Save results to expenses.csv

---

## Method 4: Shell Script (if available)

```bash
./scripts/classify_scans.sh
```

---

## Method 5: Web Interface

1. Start the Flask app:
   ```bash
   python3 app.py
   ```

2. Open browser: `http://localhost:5000`

3. Click "Classify" button next to any file in the file list

---

## Prerequisites

1. **Activate virtual environment (if using venv):**
   ```bash
   source venv/bin/activate
   # Or use venv's Python directly:
   ./venv/bin/python3 scripts/classify.py --all --scans_dir scans
   ```

2. **Model file must exist:**
   ```bash
   ls checkpoints/best_model.pt
   ```

3. **Tesseract OCR installed:**
   ```bash
   tesseract --version
   # If not installed:
   sudo apt-get install tesseract-ocr
   ```

4. **Python dependencies:**
   ```bash
   # If using venv:
   ./venv/bin/pip install -r requirements.txt
   # Or if venv is activated:
   pip install -r requirements.txt
   ```

---

## Troubleshooting

### "ML pipeline not available"
- Install dependencies: `pip install -r requirements.txt`
- Check that PyTorch and transformers are installed

### "Model not found"
- Verify model path: `ls checkpoints/best_model.pt`
- Use `--model` flag to specify correct path

### "No text extracted"
- Install Tesseract: `sudo apt-get install tesseract-ocr`
- Check image quality (may need better camera settings)

### "File not found"
- Verify file exists in scans directory
- Check file extension (.jpg, .jpeg, .png, .pdf)

---

## Quick Start Example

```bash
# 1. Make sure you have scans
ls scans/*.jpg

# 2. Classify all of them
python3 scripts/classify.py --all --scans_dir scans

# 3. Check results
cat scans/expenses.csv
```

