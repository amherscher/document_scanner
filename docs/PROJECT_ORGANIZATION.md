# Project Organization

This document describes the organization of the Pi Scanner project files.

## Directory Structure

```
pi/
├── app.py                    # Main Flask web application (entry point)
├── README.md                 # Main project README
├── requirements.txt         # Python dependencies
├── ARCHITECTURE_DIAGRAM.txt # ASCII architecture diagram
├── .gitignore               # Git ignore rules
│
├── docs/                    # All documentation
│   ├── README.md            # ML pipeline documentation
│   ├── PI_SETUP_README.md   # Raspberry Pi setup instructions
│   ├── ARCHITECTURE.md      # Detailed system architecture
│   ├── INTEGRATION.md       # ML integration guide
│   ├── PI_DEPLOYMENT.md     # Deployment instructions
│   ├── SCANNER_ML_SETUP.md  # Scanner setup guide
│   ├── TROUBLESHOOTING.md   # Common issues and solutions
│   ├── SSH_SETUP_PI.md      # SSH setup for file sync
│   ├── QUICK_SYNC_FIX.md    # Quick sync troubleshooting
│   ├── TESTING_GUIDE.md     # Testing instructions
│   ├── DATASETS.md          # Dataset information
│   ├── SYNC_SETUP.md        # File sync setup
│   ├── TRANSFER_FILES.md    # File transfer guide
│   ├── DEPLOY_EXPLAINED.md  # Deployment explanation
│   ├── FIX_DEPLOY.md        # Deployment fixes
│   ├── CLEANUP_SUMMARY.md   # Cleanup documentation
│   ├── README_ARCHIVE.md    # Archived README
│   └── presentation/        # Presentation materials
│       ├── PRESENTATION_OUTLINE.md
│       ├── PRESENTATION_CHEATSHEET.md
│       └── PRESENTATION_SLIDES.md
│
├── scripts/                 # Utility scripts
│   ├── scan_once.py         # Camera capture script
│   ├── classify.py          # CLI classification tool
│   ├── classify_all_scans.py # Batch classification
│   ├── deploy_to_pi.sh      # Deployment script
│   ├── install_tesseract.sh # OCR installation
│   ├── setup_*.sh            # Various setup scripts
│   ├── fix_*.sh              # Fix/repair scripts
│   ├── test_*.sh             # Test scripts
│   ├── enable_*.sh / disable_*.sh # USB/LED control
│   └── manual_ssh_setup_pi.md # SSH setup guide
│
├── hardware/                # Hardware control
│   └── led/                 # LED control scripts
│       ├── led_on.py
│       └── led_toggle.py
│
├── config/                  # Configuration files
│   └── pi-scan.service      # Systemd service file
│
├── ml_pipeline/             # ML pipeline code
│   ├── train.py             # Model training script
│   ├── inference.py        # Inference module
│   ├── models/              # Model architectures
│   │   └── invoice_classifier.py
│   ├── data/                # Dataset handling
│   │   ├── dataset.py
│   │   ├── download_datasets.py
│   │   ├── prepare_archive_dataset.py
│   │   └── invoice_dataset.csv
│   └── utils/               # Utilities
│       ├── ocr_extract.py   # OCR text extraction
│       ├── receipt_parser.py # Receipt data parsing
│       ├── expense_tracker.py # Expense CSV generation
│       └── fix_empty_text.py # Text fixing utilities
│
├── checkpoints/             # ML model checkpoints
│   ├── best_model.pt        # Best model (156MB)
│   ├── final_model.pt       # Final trained model
│   └── training_history.json # Training metrics
│
├── templates/               # Web UI templates
│   ├── index.html           # Main scanner interface
│   └── server.html          # Server interface
│
├── static/                  # Static web assets (currently empty)
│
└── scans/                   # Scanned documents (runtime)
    ├── *.jpg                # Scanned images
    ├── *.pdf                # Generated PDFs
    └── expenses.csv         # Expense tracking spreadsheet
```

## File Organization Principles

### Documentation (`docs/`)
- All documentation files are centralized in `docs/`
- Setup/deployment guides are clearly named
- Presentation materials are in `docs/presentation/`
- Troubleshooting guides are easily accessible

### Scripts (`scripts/`)
- All utility scripts are in `scripts/`
- Classification tools are grouped together
- Setup/fix/test scripts are organized by purpose
- Shell scripts use `.sh` extension

### Code Organization
- **Root level**: Only main entry points (`app.py`, `README.md`)
- **ml_pipeline/**: All ML-related code
- **hardware/**: Hardware control code
- **config/**: Configuration files

### Runtime Data
- **scans/**: Generated at runtime, contains scanned documents
- **checkpoints/**: Model files (large, may be excluded from git)
- **venv/**: Virtual environment (excluded from git)

## Key Entry Points

1. **Web Application**: `python app.py`
2. **CLI Classification**: `python scripts/classify.py --all`
3. **Training**: `python ml_pipeline/train.py`
4. **Deployment**: `./scripts/deploy_to_pi.sh`

## Documentation Quick Reference

- **Getting Started**: `README.md` (root)
- **ML Pipeline**: `docs/README.md`
- **Pi Setup**: `docs/PI_SETUP_README.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`
- **Presentation**: `docs/presentation/`

## Notes

- The `venv/` directory is excluded from git (virtual environment)
- Large model files (`.pt`) may be excluded from git
- Scanned documents in `scans/` are runtime-generated
- `__pycache__/` directories are excluded from git

