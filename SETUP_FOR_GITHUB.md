# Setup for GitHub

## Before Pushing to GitHub

This project contains some default configuration values that reference personal paths and usernames. These are safe to push as they are:
- Default values that users should override
- Environment variables that can be set per deployment
- Example configurations

## Configuration Values

The following values in `app.py` are defaults and should be overridden via environment variables:

- `PI_SCAN_TOKEN`: Default is "changeme" - **CHANGE THIS** in production
- `SYNC_SERVER_HOST`: Default is "10.29.0.1" - set via `SYNC_SERVER_HOST` env var
- `SYNC_SERVER_USER`: Default is "amherscher" - set via `SYNC_SERVER_USER` env var  
- `SYNC_SERVER_DIR`: Default is "/home/data/Purdue/pi/scans" - set via `SYNC_SERVER_DIR` env var

## Files Excluded from Git

The `.gitignore` file excludes:
- Virtual environments (`venv/`)
- Scanned images (`*.jpg`, `*.png`, `*.pdf`)
- CSV files (except `requirements.txt`)
- Model checkpoints (large `.pt` files)
- Cache files (`__pycache__/`)
- Log files

## Optional: Exclude Presentation Files

If you don't want to share your presentation, uncomment these lines in `.gitignore`:
```
# Pi_Scanner_Presentation.pptx
# PRESENTATION_SCRIPT_4MIN.md
```

## Recommended: Create .env.example

Create a `.env.example` file with template values:
```bash
PI_SCAN_TOKEN=your_secret_token_here
SYNC_SERVER_HOST=your.server.ip
SYNC_SERVER_USER=your_username
SYNC_SERVER_DIR=/path/to/scans
SYNC_ENABLED=false
INVOICE_MODEL_PATH=checkpoints/best_model.pt
```

Then users can copy it to `.env` and fill in their values.

