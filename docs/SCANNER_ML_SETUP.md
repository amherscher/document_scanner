# Scanner + ML Integration - Quick Setup

## What Was Built

✅ **Complete integration** between Raspberry Pi scanner and ML invoice classification
✅ **Automatic classification** after scanning
✅ **OCR text extraction** from scanned invoices
✅ **Web UI** showing classification results
✅ **API endpoints** for classification

## Quick Start

### 1. Train a Model (On Server)

```bash
# Create sample dataset
python ml_pipeline/data/download_datasets.py --create_sample --sample_size 200

# Train model
python ml_pipeline/train.py \
    --data_path ml_pipeline/data/sample_invoices.csv \
    --model_type text \
    --epochs 10 \
    --output_dir ml_pipeline/checkpoints
```

### 2. Set Model Path

```bash
export INVOICE_MODEL_PATH=/home/data/Purdue/pi/ml_pipeline/checkpoints/best_model.pt
```

### 3. Install OCR (if needed)

```bash
sudo apt-get install -y tesseract-ocr
pip install pytesseract
```

### 4. Run Flask App

```bash
python app.py
```

### 5. Use It!

1. Open web interface: `http://your-server:5000`
2. Click "Scan" button
3. Invoice is scanned and automatically classified
4. Results appear showing expense category

## Features

- **Auto-classification**: Scans are automatically classified after capture
- **Manual classification**: Click "Classify" on any existing file
- **ML status indicator**: Shows if model is loaded and ready
- **Multiple model types**: Text, image, or hybrid models supported
- **OCR integration**: Automatically extracts text from scanned images
- **Confidence scores**: Shows prediction confidence and top alternatives

## File Structure

```
pi/
├── app.py                          # Flask app with ML integration
├── ml_pipeline/
│   ├── models/                     # PyTorch models
│   ├── data/                       # Dataset utilities
│   ├── utils/                      # OCR extraction
│   ├── train.py                    # Training script
│   └── inference.py                # Inference utilities
├── templates/
│   └── index.html                  # Web UI with classification display
└── scans/                          # Scanned invoices saved here
```

## API Endpoints

- `POST /api/scan` - Scan invoice (auto-classifies)
- `POST /api/classify` - Classify existing file
- `GET /api/ml/status` - Check ML model status

## Next Steps

1. **Train with your data**: Replace sample dataset with real invoices
2. **Fine-tune categories**: Adjust expense categories to your needs
3. **Deploy**: Set up as a service on your server
4. **Integrate**: Connect to accounting software or database

See `INTEGRATION.md` for detailed documentation.

