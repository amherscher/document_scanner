# Raspberry Pi Deployment Guide

## What Files Go Where?

There are two deployment options. Choose based on your setup:

---

## Option 1: Pi as Scanner Only (Recommended)

**Pi handles scanning, Server handles ML classification**

### Files Needed on Raspberry Pi

```
/opt/scanner/
├── app.py                    # Flask web app (scanner only version)
├── scan_once.py              # Camera capture script
├── led_on.py                 # LED control (optional)
├── led_toggle.py             # LED control (optional)
├── pi-scan.service           # Systemd service file
├── requirements.txt          # Python dependencies (Flask only)
├── templates/
│   └── index.html            # Web UI
└── static/                   # Static files (if any)
```

**Minimal requirements.txt for Pi:**
```
Flask>=2.2
```

**System packages needed:**
```bash
sudo apt-get install -y python3-flask fswebcam img2pdf tesseract-ocr ocrmypdf imagemagick avahi-daemon
```

### Files Needed on Server (ML Classification)

```
/opt/scanner/  (or your server directory)
├── app.py                    # Flask app WITH ML integration
├── ml_pipeline/
│   ├── models/
│   │   └── invoice_classifier.py
│   ├── data/
│   │   └── dataset.py
│   ├── utils/
│   │   └── ocr_extract.py
│   ├── inference.py
│   └── __init__.py
├── checkpoints/
│   └── best_model.pt         # Your trained model
├── templates/
│   └── index.html            # Web UI with ML features
├── requirements.txt          # Full requirements with ML deps
└── scans/                    # Scanned files directory
```

**Full requirements.txt for Server:**
```
Flask>=2.2
torch>=2.0.0
torchvision>=0.15.0
transformers>=4.30.0
tokenizers>=0.13.0
pandas>=1.5.0
numpy>=1.24.0
Pillow>=9.5.0
scikit-learn>=1.3.0
pytesseract>=0.3.10
tqdm>=4.65.0
requests>=2.28.0
```

---

## Option 2: Everything on Pi

**Pi does both scanning AND ML classification**

### Files Needed on Raspberry Pi

```
/opt/scanner/
├── app.py                    # Flask app WITH ML integration
├── scan_once.py              # Camera capture script
├── led_on.py                 # LED control (optional)
├── led_toggle.py             # LED control (optional)
├── pi-scan.service           # Systemd service file
├── ml_pipeline/
│   ├── models/
│   │   └── invoice_classifier.py
│   ├── data/
│   │   └── dataset.py
│   ├── utils/
│   │   └── ocr_extract.py
│   ├── inference.py
│   └── __init__.py
├── checkpoints/
│   └── best_model.pt         # Your trained model
├── templates/
│   └── index.html            # Web UI
├── static/                   # Static files
├── requirements.txt          # Full requirements
└── scans/                    # Scanned files
```

**Note:** Pi may be slow for ML inference. Consider using a smaller model or CPU-optimized version.

---

## Quick Copy Scripts

### Copy Scanner Files to Pi (Option 1)

```bash
#!/bin/bash
# copy_scanner_to_pi.sh

PI_USER=pi
PI_HOST=pi-scan.local  # or IP address
PI_DIR=/opt/scanner

# Copy scanner files only
scp app.py scan_once.py led_*.py pi-scan.service requirements.txt \
    ${PI_USER}@${PI_HOST}:${PI_DIR}/

scp -r templates/ ${PI_USER}@${PI_HOST}:${PI_DIR}/

# On Pi, install dependencies
ssh ${PI_USER}@${PI_HOST} "cd ${PI_DIR} && pip3 install -r requirements.txt"
```

### Copy Everything to Pi (Option 2)

```bash
#!/bin/bash
# copy_all_to_pi.sh

PI_USER=pi
PI_HOST=pi-scan.local
PI_DIR=/opt/scanner

# Copy all files
scp app.py scan_once.py led_*.py pi-scan.service requirements.txt \
    ${PI_USER}@${PI_HOST}:${PI_DIR}/

scp -r ml_pipeline/ templates/ checkpoints/ ${PI_USER}@${PI_HOST}:${PI_DIR}/

# On Pi, install dependencies
ssh ${PI_USER}@${PI_HOST} "cd ${PI_DIR} && pip3 install -r requirements.txt"
```

---

## Step-by-Step Deployment

### For Option 1 (Pi = Scanner, Server = ML)

#### On Raspberry Pi:

1. **Create directory:**
```bash
sudo mkdir -p /opt/scanner/{templates,static,scans}
sudo chown -R pi:pi /opt/scanner
```

2. **Copy scanner files:**
```bash
# Copy these files to /opt/scanner/
- app.py (scanner version - without ML imports)
- scan_once.py
- led_on.py
- led_toggle.py
- pi-scan.service
- templates/index.html
- requirements.txt (minimal)
```

3. **Install dependencies:**
```bash
sudo apt-get update
sudo apt-get install -y python3-flask fswebcam img2pdf tesseract-ocr ocrmypdf imagemagick avahi-daemon
pip3 install Flask
```

4. **Set up service:**
```bash
sudo cp /opt/scanner/pi-scan.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pi-scan
```

#### On Server:

1. **Copy ML files:**
```bash
# Copy these to server:
- app.py (with ML integration)
- ml_pipeline/ (entire directory)
- checkpoints/best_model.pt
- templates/index.html (with ML UI)
- requirements.txt (full version)
```

2. **Install ML dependencies:**
```bash
pip install -r requirements.txt
sudo apt-get install -y tesseract-ocr
```

3. **Set model path:**
```bash
export INVOICE_MODEL_PATH=/path/to/checkpoints/best_model.pt
```

4. **Run Flask app:**
```bash
python app.py
```

### For Option 2 (Everything on Pi)

1. **Copy all files to Pi:**
```bash
# Copy everything to /opt/scanner/
- app.py
- scan_once.py
- led_*.py
- ml_pipeline/
- checkpoints/
- templates/
- requirements.txt
```

2. **Install all dependencies:**
```bash
sudo apt-get update
sudo apt-get install -y python3-flask fswebcam img2pdf tesseract-ocr ocrmypdf imagemagick avahi-daemon
pip3 install -r requirements.txt
```

3. **Set up service:**
```bash
sudo cp /opt/scanner/pi-scan.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pi-scan
```

---

## File Checklist

### Essential Files (Both Options)

- [ ] `app.py` - Flask application
- [ ] `scan_once.py` - Camera capture
- [ ] `templates/index.html` - Web UI
- [ ] `pi-scan.service` - Systemd service
- [ ] `requirements.txt` - Dependencies

### For ML Classification (Server or Pi)

- [ ] `ml_pipeline/models/invoice_classifier.py`
- [ ] `ml_pipeline/data/dataset.py`
- [ ] `ml_pipeline/utils/ocr_extract.py`
- [ ] `ml_pipeline/inference.py`
- [ ] `checkpoints/best_model.pt` - Trained model

### Optional Files

- [ ] `led_on.py` - LED control
- [ ] `led_toggle.py` - LED control
- [ ] `enable_usb.sh` - USB control
- [ ] `disable_usb.sh` - USB control

---

## Verification

After deployment, verify:

1. **Pi scanner works:**
```bash
curl http://pi-scan.local:5000/api/status
```

2. **Server ML works:**
```bash
curl http://server:5000/api/ml/status
```

3. **Test scan:**
   - Open web interface
   - Click "Scan"
   - Verify image is captured
   - Check classification results (if ML enabled)

---

## Notes

- **Option 1 is recommended** - Pi is lightweight, server handles heavy ML
- **Model file size**: `best_model.pt` can be 100-500MB
- **Network**: Pi and server need network connectivity if using Option 1
- **Performance**: Pi may be slow for ML inference (Option 2)
- **Storage**: Ensure Pi has enough space for scans and model (if Option 2)

---

## Troubleshooting

### Pi can't connect to server
- Check network connectivity
- Verify server IP/port
- Check firewall settings

### Model not found
- Verify `best_model.pt` exists
- Check `INVOICE_MODEL_PATH` environment variable
- Check file permissions

### Slow classification
- Use Option 1 (server handles ML)
- Use smaller model
- Reduce image resolution

