# Transferring Files to Raspberry Pi

## Quick Comparison

| Method | Best For | Speed | Setup Complexity |
|--------|----------|-------|------------------|
| **SCP/rsync** | One-time deployment | ⚡ Fast | ✅ Simple |
| **GitHub** | Version control, updates | 🐌 Slower | ⚠️ More steps |
| **USB Drive** | No network | ⚡ Fast | ✅ Simple |
| **Network Share** | Frequent access | ⚡ Fast | ⚠️ Medium |

## Recommended: SCP/rsync (Easiest for Deployment)

### Option 1: SCP (Simple Copy)

```bash
# From your server, copy files to Pi
scp -r app.py scan_once.py templates/ pi-scan.service \
    pi@pi-scan.local:/opt/scanner/

# Or if using IP address
scp -r app.py scan_once.py templates/ pi-scan.service \
    pi@192.168.1.100:/opt/scanner/
```

### Option 2: rsync (Better - Only Copies Changes)

```bash
# Sync files (only copies what changed)
rsync -avz --progress \
    app.py scan_once.py led_*.py pi-scan.service templates/ \
    pi@pi-scan.local:/opt/scanner/

# Exclude unnecessary files
rsync -avz --progress \
    --exclude 'venv/' \
    --exclude '*.pyc' \
    --exclude '__pycache__/' \
    --exclude 'checkpoints/' \
    --exclude 'ml_pipeline/' \
    . pi@pi-scan.local:/opt/scanner/
```

### Option 3: rsync Script (Most Convenient)

Create `deploy_to_pi.sh`:

```bash
#!/bin/bash
# deploy_to_pi.sh - Deploy scanner files to Raspberry Pi

PI_USER=pi
PI_HOST=pi-scan.local  # or use IP: 192.168.1.100
PI_DIR=/opt/scanner

echo "Deploying to ${PI_USER}@${PI_HOST}:${PI_DIR}"

# Sync essential files
rsync -avz --progress \
    --exclude 'venv/' \
    --exclude '*.pyc' \
    --exclude '__pycache__/' \
    --exclude 'checkpoints/' \
    --exclude 'ml_pipeline/' \
    --exclude '.git/' \
    --exclude 'archive*/' \
    app.py \
    scan_once.py \
    led_on.py \
    led_toggle.py \
    pi-scan.service \
    requirements.txt \
    templates/ \
    ${PI_USER}@${PI_HOST}:${PI_DIR}/

echo "Deployment complete!"
echo "SSH to Pi and run: sudo systemctl restart pi-scan"
```

Make it executable and run:
```bash
chmod +x deploy_to_pi.sh
./deploy_to_pi.sh
```

---

## GitHub Method (Good for Version Control)

### If You Want Version Control:

1. **On Server - Create/Update Repo:**
```bash
# Initialize git (if not already)
git init
git add app.py scan_once.py templates/ pi-scan.service requirements.txt
git commit -m "Scanner files for Pi deployment"

# Push to GitHub
git remote add origin https://github.com/yourusername/pi-scanner.git
git push -u origin main
```

2. **On Pi - Clone/Pull:**
```bash
# First time - clone
cd /opt/scanner
git clone https://github.com/yourusername/pi-scanner.git .

# Or update existing
cd /opt/scanner
git pull origin main
```

**Pros:**
- ✅ Version control
- ✅ Easy updates (just `git pull`)
- ✅ Backup in cloud
- ✅ Track changes

**Cons:**
- ⚠️ Requires GitHub account
- ⚠️ More steps for one-time deployment
- ⚠️ Need to commit/push first

---

## USB Drive Method (No Network Needed)

1. **Copy files to USB:**
```bash
# On server
cp -r app.py scan_once.py templates/ /media/usb/
```

2. **Plug USB into Pi and copy:**
```bash
# On Pi
sudo mount /dev/sda1 /mnt
cp -r /mnt/* /opt/scanner/
sudo umount /mnt
```

---

## Network Share Method (Same Network)

### On Server - Share Directory:
```bash
# Install Samba
sudo apt-get install samba

# Share directory
sudo nano /etc/samba/smb.conf
# Add:
[scanner]
path = /home/data/Purdue/pi
browsable = yes
writable = yes
valid users = youruser
```

### On Pi - Mount Share:
```bash
# Install cifs-utils
sudo apt-get install cifs-utils

# Mount
sudo mount -t cifs //server-ip/scanner /mnt/scanner -o username=youruser
cp -r /mnt/scanner/* /opt/scanner/
```

---

## Recommended Workflow

### For Initial Deployment:
**Use SCP or rsync** - Fastest and simplest

```bash
# Quick one-liner
rsync -avz app.py scan_once.py templates/ pi-scan.service \
    pi@pi-scan.local:/opt/scanner/
```

### For Ongoing Updates:
**Use GitHub** - Better for tracking changes

```bash
# On server: commit and push
git add .
git commit -m "Update scanner"
git push

# On Pi: pull updates
cd /opt/scanner && git pull
```

---

## Complete Deployment Script

Save as `deploy_to_pi.sh`:

```bash
#!/bin/bash
set -e

PI_USER=${PI_USER:-pi}
PI_HOST=${PI_HOST:-pi-scan.local}
PI_DIR=${PI_DIR:-/opt/scanner}

echo "=========================================="
echo "Deploying Scanner to Raspberry Pi"
echo "=========================================="
echo "Target: ${PI_USER}@${PI_HOST}:${PI_DIR}"
echo ""

# Check if Pi is reachable
if ! ping -c 1 ${PI_HOST} &> /dev/null; then
    echo "❌ Cannot reach ${PI_HOST}"
    echo "   Try using IP address: PI_HOST=192.168.1.100 ./deploy_to_pi.sh"
    exit 1
fi

# Create directory on Pi
echo "📁 Creating directory on Pi..."
ssh ${PI_USER}@${PI_HOST} "sudo mkdir -p ${PI_DIR}/{templates,static,scans} && sudo chown -R ${PI_USER}:${PI_USER} ${PI_DIR}"

# Sync files
echo "📤 Syncing files..."
rsync -avz --progress \
    --exclude 'venv/' \
    --exclude '*.pyc' \
    --exclude '__pycache__/' \
    --exclude 'checkpoints/' \
    --exclude 'ml_pipeline/' \
    --exclude '.git/' \
    --exclude 'archive*/' \
    --exclude '*.md' \
    app.py \
    scan_once.py \
    led_on.py \
    led_toggle.py \
    pi-scan.service \
    requirements.txt \
    templates/ \
    ${PI_USER}@${PI_HOST}:${PI_DIR}/

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps on Pi:"
echo "  1. Install dependencies:"
echo "     cd ${PI_DIR} && pip3 install -r requirements.txt"
echo ""
echo "  2. Install system packages:"
echo "     sudo apt-get install -y python3-flask fswebcam img2pdf tesseract-ocr ocrmypdf imagemagick avahi-daemon"
echo ""
echo "  3. Set up service:"
echo "     sudo cp ${PI_DIR}/pi-scan.service /etc/systemd/system/"
echo "     sudo systemctl daemon-reload"
echo "     sudo systemctl enable --now pi-scan"
echo ""
echo "  4. Test:"
echo "     curl http://pi-scan.local:5000/api/status"
```

Make executable:
```bash
chmod +x deploy_to_pi.sh
```

Run:
```bash
# Default (pi-scan.local)
./deploy_to_pi.sh

# Or with custom host
PI_HOST=192.168.1.100 ./deploy_to_pi.sh
```

---

## Quick Answer

**For one-time deployment:** Use **rsync** or **SCP** - it's faster and simpler.

**For ongoing updates:** Use **GitHub** - better for version control.

**Simplest command:**
```bash
rsync -avz app.py scan_once.py templates/ pi-scan.service \
    pi@pi-scan.local:/opt/scanner/
```

That's it! Much faster than GitHub for deployment. 🚀

