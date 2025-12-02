# Pi Scanner - System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│                    (Web Browser / Mobile)                        │
│                    http://pi-scan.local:5000                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP/REST API
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Raspberry Pi (Scanner)                        │
│                    IP: 10.29.0.14                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Flask Web Application (app.py)              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │   Scanner    │  │  LED Control │  │ File Sync    │  │   │
│  │  │   Endpoint   │  │   Endpoint   │  │  Endpoint    │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │   │
│  └─────────┼──────────────────┼──────────────────┼─────────┘   │
│            │                  │                  │              │
│  ┌─────────▼──────────┐  ┌────▼─────┐  ┌────────▼──────────┐  │
│  │  scan_once.py      │  │led_*.py  │  │   rsync           │  │
│  │  (Camera Capture)  │  │USB Ctrl  │  │   (File Transfer) │  │
│  └─────────┬──────────┘  └───────────┘  └────────┬──────────┘  │
│            │                                     │              │
│  ┌─────────▼──────────┐              ┌──────────▼──────────┐  │
│  │  Camera Hardware   │              │  USB Hub Control    │  │
│  │  (fswebcam/rpicam) │              │  (uhubctl)          │  │
│  └────────────────────┘              └─────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Local Storage (/opt/scanner/scans)        │  │
│  │  • Scanned images (.jpg)                               │  │
│  │  • PDF files (.pdf)                                    │  │
│  │  • Expense tracking (expenses.csv)                     │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ rsync (SSH)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Server (ML Processing)                       │
│                    IP: 10.29.0.1                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Flask Web Application (app.py)              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │  Classify    │  │  OCR Extract │  │  Receipt     │   │   │
│  │  │  Endpoint    │  │              │  │  Parser      │   │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │   │
│  └─────────┼──────────────────┼──────────────────┼─────────┘   │
│            │                  │                  │              │
│  ┌─────────▼──────────────────▼──────────────────▼──────────┐  │
│  │              ML Pipeline (ml_pipeline/)                   │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Invoice Classifier (PyTorch)                      │  │  │
│  │  │  • Text-based model                                │  │  │
│  │  │  • Image-based model                               │  │  │
│  │  │  • Hybrid model                                     │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  OCR Engine (Tesseract)                            │  │  │
│  │  │  • Text extraction from images/PDFs                │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Receipt Parser                                    │  │  │
│  │  │  • Vendor, Date, Amounts, Items extraction         │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Model Storage (checkpoints/best_model.pt)             │  │
│  │  • Trained PyTorch model (156MB)                       │  │
│  │  • 90.5% validation accuracy                           │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Centralized Storage (/home/data/Purdue/pi/scans)      │  │
│  │  • All scanned invoices                                 │  │
│  │  • Master expense spreadsheet                           │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Raspberry Pi Components

```
┌─────────────────────────────────────────┐
│         Raspberry Pi Stack              │
├─────────────────────────────────────────┤
│                                         │
│  Application Layer:                     │
│  • Flask Web Server (app.py)           │
│  • REST API Endpoints                   │
│  • Web UI (templates/index.html)        │
│                                         │
│  Hardware Control:                      │
│  • Camera Capture (scan_once.py)       │
│  • USB Hub Control (led_*.py)          │
│  • LED Toggle                           │
│                                         │
│  System Services:                       │
│  • systemd Service (pi-scan.service)    │
│  • Auto-start on boot                  │
│                                         │
│  Storage:                               │
│  • Local scans directory                │
│  • Temporary file storage               │
│                                         │
└─────────────────────────────────────────┘
```

### Server Components

```
┌─────────────────────────────────────────┐
│         Server Stack                     │
├─────────────────────────────────────────┤
│                                         │
│  Application Layer:                     │
│  • Flask Web Server (app.py)           │
│  • ML Classification API                │
│  • Expense Tracking                     │
│                                         │
│  ML Pipeline:                           │
│  • PyTorch Models                       │
│  • Transformers (BERT)                  │
│  • Image Processing (PIL)                │
│                                         │
│  Data Processing:                       │
│  • OCR (Tesseract)                      │
│  • Receipt Parsing (Regex)              │
│  • CSV Generation                       │
│                                         │
│  Storage:                               │
│  • Model Checkpoints                    │
│  • Centralized Scans                    │
│  • Master Expense Spreadsheet            │
│                                         │
└─────────────────────────────────────────┘
```

## Data Flow

### Scanning & Classification Flow

```
1. User Action
   │
   ▼
2. Web UI → POST /api/scan
   │
   ▼
3. Pi: Capture Image
   │  • scan_once.py
   │  • Camera hardware
   │
   ▼
4. Save Locally
   │  • /opt/scanner/scans/scan_XXX.jpg
   │  • /opt/scanner/scans/scan_XXX.pdf
   │
   ▼
5. Auto-Classify (if ML available)
   │  • Extract text (OCR)
   │  • Classify category
   │  • Parse receipt data
   │
   ▼
6. Save to Expense Spreadsheet
   │  • expenses.csv
   │  • Category, Amount, Vendor, Date
   │
   ▼
7. Optional: Sync to Server
   │  • rsync via SSH
   │  • Transfer to server
   │  • Delete from Pi
   │
   ▼
8. Display Results
   │  • Category prediction
   │  • Confidence score
   │  • Receipt details
```

### File Synchronization Flow

```
Pi (Source)                    Server (Destination)
─────────────────              ────────────────────
/opt/scanner/scans/            /home/data/Purdue/pi/scans/
     │                                 │
     │  rsync -avz                     │
     │  --remove-source-files          │
     ├─────────────────────────────────►
     │                                 │
     │  Transfer files                 │
     │  • scan_XXX.jpg                 │
     │  • scan_XXX.pdf                 │
     │                                 │
     │  Delete from Pi                 │
     │  (after successful transfer)    │
     │                                 │
     └─────────────────────────────────┘
```

## Technology Stack

### Raspberry Pi
- **OS**: Raspberry Pi OS (Linux)
- **Web Framework**: Flask (Python)
- **Camera**: fswebcam / rpicam-still
- **Hardware Control**: uhubctl (USB hub control)
- **File Transfer**: rsync (SSH)
- **Service Management**: systemd

### Server
- **OS**: Linux
- **Web Framework**: Flask (Python)
- **ML Framework**: PyTorch
- **NLP**: Transformers (BERT)
- **OCR**: Tesseract
- **Image Processing**: PIL/Pillow
- **Data Processing**: pandas, numpy

## API Endpoints

```
┌─────────────────────────────────────────────────────────┐
│                    API Endpoints                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Scanner Operations:                                    │
│  POST   /api/scan          - Capture invoice           │
│  GET    /api/status        - Get recent files          │
│  POST   /api/set_workdir   - Change save directory     │
│                                                         │
│  LED Control:                                          │
│  POST   /api/led/toggle    - Toggle USB power          │
│                                                         │
│  ML Classification:                                     │
│  POST   /api/classify      - Classify existing file    │
│  GET    /api/ml/status     - ML model status           │
│                                                         │
│  File Sync:                                            │
│  POST   /api/sync          - Sync files to server       │
│  GET    /api/sync/status   - Sync configuration        │
│                                                         │
│  Expense Tracking:                                      │
│  GET    /api/expenses      - List expenses             │
│  GET    /api/expenses/summary - Expense totals         │
│  GET    /api/expenses/download - Download CSV          │
│                                                         │
│  File Access:                                          │
│  GET    /downloads/<file>   - Download scanned file     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
Development Server                    Production
───────────────────                   ───────────
                                      │
┌──────────────────┐                 │
│  Code Repository │                 │
│  (This machine)  │                 │
└────────┬─────────┘                 │
         │                           │
         │ deploy_to_pi.sh           │
         │ (rsync + SSH)             │
         │                           │
         ▼                           │
┌──────────────────┐                 │
│  Raspberry Pi    │                 │
│  10.29.0.14      │                 │
│  /opt/scanner/   │                 │
└────────┬─────────┘                 │
         │                           │
         │ File Sync (rsync)         │
         │                           │
         ▼                           │
┌──────────────────┐                 │
│  ML Server       │                 │
│  10.29.0.1       │                 │
│  /home/data/...  │                 │
└──────────────────┘                 │
```

## Key Features

1. **Document Scanning**
   - Camera-based capture
   - Automatic image processing
   - PDF generation

2. **ML Classification**
   - Invoice categorization
   - Multiple model types (text/image/hybrid)
   - Confidence scoring

3. **Data Extraction**
   - OCR text extraction
   - Receipt parsing (vendor, date, amounts)
   - Structured data output

4. **Expense Tracking**
   - Automatic CSV generation
   - Category-based summaries
   - Master spreadsheet

5. **File Management**
   - Local storage on Pi
   - Automatic sync to server
   - Centralized archive

6. **Hardware Control**
   - LED/USB power control
   - Camera management
   - System integration

## Security

- Token-based authentication
- SSH key authentication for file sync
- Service isolation (systemd)
- Network access control

