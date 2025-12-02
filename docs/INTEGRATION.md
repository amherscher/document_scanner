# Scanner + ML Pipeline Integration Guide

This guide explains how to use the Raspberry Pi scanner with the ML invoice classification pipeline.

## Architecture

```
Raspberry Pi (Scanner)          Server (Classification)
┌─────────────────┐             ┌──────────────────────┐
│  Camera         │             │  Flask App           │
│  Flask Web UI   │────────────▶│  ML Model            │
│  Scan Endpoint  │   HTTP      │  OCR Extraction      │
└─────────────────┘             │  Classification      │
                                └──────────────────────┘
```

## Setup

### 1. On the Server (Classification Machine)

#### Install Dependencies

```bash
# Install Python ML dependencies
pip install -r requirements.txt

# Install Tesseract OCR (if not already installed)
sudo apt-get install -y tesseract-ocr

# Install PyTorch (choose based on your system)
# For CPU:
pip install torch torchvision transformers

# For GPU (CUDA):
pip install torch torchvision transformers --index-url https://download.pytorch.org/whl/cu118
```

#### Train a Model

First, prepare your dataset and train a model:

```bash
# Create sample dataset for testing
python ml_pipeline/data/download_datasets.py --create_sample --sample_size 200

# Train a text-based model (recommended for invoices with OCR)
python ml_pipeline/train.py \
    --data_path ml_pipeline/data/sample_invoices.csv \
    --model_type text \
    --epochs 10 \
    --batch_size 16 \
    --output_dir ml_pipeline/checkpoints

# Or train a hybrid model (text + image) for best accuracy
python ml_pipeline/train.py \
    --data_path ml_pipeline/data/sample_invoices.csv \
    --model_type hybrid \
    --image_dir data/images \
    --epochs 10 \
    --batch_size 8 \
    --output_dir ml_pipeline/checkpoints
```

#### Configure Model Path

Set the environment variable to point to your trained model:

```bash
export INVOICE_MODEL_PATH=/path/to/ml_pipeline/checkpoints/best_model.pt
```

Or edit `app.py` to change the default path.

### 2. On the Raspberry Pi (Scanner)

The Pi only needs the Flask app and scanner scripts. The ML model runs on the server.

#### Option A: Run Scanner on Pi, ML on Server

1. **On the Pi:** Keep the scanner Flask app running
2. **On the Server:** Run the Flask app with ML pipeline enabled
3. **Configure:** Point the Pi's scan endpoint to the server, or run both and sync files

#### Option B: Run Everything on Server

If the server has access to the Pi's camera or receives scanned files:

1. Copy all files to the server
2. Run the Flask app on the server
3. The app will handle both scanning (if camera available) and classification

## Usage

### Scanning and Auto-Classification

1. **Open the web interface** on your device (phone, tablet, computer)
2. **Click "Scan"** - the invoice will be captured
3. **Classification happens automatically** - results appear below the scan button
4. **View results** showing:
   - Predicted expense category
   - Confidence score
   - Top 3 predictions
   - Whether text was extracted

### Manual Classification

1. **View recent files** in the web interface
2. **Click "Classify"** button next to any invoice file
3. **See classification results** for that specific file

### API Endpoints

#### Scan and Classify
```bash
POST /api/scan
{
  "zoom": 0.3,
  "classify": true
}

Response:
{
  "ok": true,
  "saved": ["scan_20240120_143022.jpg", "scan_20240120_143022.pdf"],
  "classification": {
    "category": "Office Supplies",
    "confidence": 0.9234,
    "top_predictions": [
      {"category": "Office Supplies", "confidence": 0.9234},
      {"category": "Hardware & Equipment", "confidence": 0.0456},
      {"category": "Other", "confidence": 0.0123}
    ],
    "text_extracted": true,
    "text_length": 1234
  }
}
```

#### Classify Existing File
```bash
POST /api/classify
{
  "filename": "scan_20240120_143022.jpg"
}

Response:
{
  "ok": true,
  "category": "Office Supplies",
  "confidence": 0.9234,
  "top_predictions": [...],
  "text_extracted": true,
  "text_length": 1234
}
```

#### Check ML Status
```bash
GET /api/ml/status

Response:
{
  "ok": true,
  "ml_available": true,
  "model_path": "/path/to/model.pt",
  "model_exists": true,
  "model_loaded": true,
  "categories": ["Office Supplies", "Travel", ...],
  "model_type": "text"
}
```

## Workflow

### Typical Workflow

1. **Place invoice** on scanner bed
2. **Click "Scan"** in web interface
3. **Wait for scan** (camera captures image)
4. **OCR extraction** happens automatically (extracts text from image)
5. **ML classification** runs automatically
6. **Results displayed** showing expense category
7. **File saved** to scans directory

### File Transfer (Pi → Server)

If scanner runs on Pi and ML on server, you can:

#### Option 1: Network Share
- Mount server directory on Pi
- Save scans directly to server
- Server processes files automatically

#### Option 2: Sync Script
```bash
# On Pi: Sync scans to server
rsync -av /opt/scanner/scans/ user@server:/path/to/scans/
```

#### Option 3: API Upload
- Modify scan endpoint to upload to server
- Server receives file and classifies immediately

## Model Types

### Text Model (Recommended)
- **Best for:** Invoices with clear text
- **Requires:** OCR text extraction
- **Pros:** Fast, accurate, smaller model
- **Use when:** You have good OCR results

### Image Model
- **Best for:** Visual invoice layouts
- **Requires:** Image files only
- **Pros:** No OCR needed
- **Use when:** OCR quality is poor

### Hybrid Model
- **Best for:** Maximum accuracy
- **Requires:** Both text and image
- **Pros:** Most accurate
- **Use when:** You want best results and have both

## Troubleshooting

### Model Not Loading
- Check model path: `export INVOICE_MODEL_PATH=/correct/path`
- Verify model file exists
- Check model was trained successfully
- Review error logs in Flask console

### OCR Not Working
- Install Tesseract: `sudo apt-get install tesseract-ocr`
- Check image quality (may need better lighting)
- Verify pytesseract is installed: `pip install pytesseract`

### Classification Errors
- Ensure model type matches (text/image/hybrid)
- Check input format matches training data
- Verify categories match between training and inference

### No Classification Results
- Check ML status endpoint: `/api/ml/status`
- Verify model is loaded
- Check Flask app logs for errors
- Ensure OCR extracted text (for text/hybrid models)

## Performance Tips

1. **Use text model** for faster inference
2. **Pre-process images** for better OCR
3. **Cache model** (already done - model loads once)
4. **Batch processing** for multiple invoices
5. **GPU acceleration** for faster inference (if available)

## Security Notes

- ML model runs on server (more secure than Pi)
- Classification happens server-side
- Scanned files stored locally or on server
- API requires authentication token

## Next Steps

1. Train model with your own invoice data
2. Fine-tune categories for your use case
3. Integrate with accounting software
4. Add batch processing for multiple invoices
5. Set up automated workflows

