# Pi Scanner - Invoice Categorization System

Raspberry Pi-based document scanner with ML-powered invoice categorization.

## Project Structure

```
pi/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/            # Web UI templates
│   └── index.html
├── static/               # Static web assets
├── scans/                # Scanned documents (created at runtime)
├── checkpoints/          # ML model checkpoints
│
├── docs/                 # All documentation
│   ├── README.md         # Main documentation
│   ├── INTEGRATION.md    # ML integration guide
│   ├── PI_DEPLOYMENT.md  # Deployment instructions
│   └── ...
│
├── hardware/             # Hardware control scripts
│   └── led/              # LED control
│       ├── led_on.py
│       └── led_toggle.py
│
├── scripts/              # Utility scripts
│   ├── scan_once.py      # Camera capture script
│   ├── deploy_to_pi.sh   # Deployment script
│   ├── disable_usb.sh
│   └── enable_usb.sh
│
├── config/               # Configuration files
│   └── pi-scan.service   # Systemd service file
│
└── ml_pipeline/          # ML pipeline code
    ├── train.py          # Training script
    ├── inference.py      # Inference module
    ├── models/           # Model architectures
    ├── data/             # Dataset handling
    └── utils/            # Utilities (OCR, parsing)
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Train model (optional):**
   ```bash
   cd ml_pipeline
   python train.py --data_path data/invoice_dataset.csv --model_type text
   ```

3. **Run scanner:**
   ```bash
   python app.py
   ```

4. **Deploy to Pi:**
   ```bash
   ./scripts/deploy_to_pi.sh
   ```

## Documentation

See `docs/` directory for detailed documentation:
- `README.md` - Main documentation
- `INTEGRATION.md` - ML pipeline integration
- `PI_DEPLOYMENT.md` - Raspberry Pi deployment
- `SCANNER_ML_SETUP.md` - Scanner setup guide

## Features

- Document scanning via web interface
- Automatic invoice categorization using ML
- Receipt data extraction (vendor, date, amounts, items)
- File synchronization to server
- LED control for scanner lighting

