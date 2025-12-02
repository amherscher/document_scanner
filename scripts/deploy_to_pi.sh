#!/bin/bash
set -e

PI_USER=amherscher
PI_HOST=10.29.0.14
PI_DIR=/opt/scanner

# Use SSH connection sharing to avoid multiple password prompts
# This reuses a single SSH connection for all commands
SSH_OPTS="-o ControlMaster=auto -o ControlPath=~/.ssh/pi-deploy-%r@%h:%p -o ControlPersist=300"

echo "=========================================="
echo "Deploying Scanner to Raspberry Pi"
echo "=========================================="
echo "Target: ${PI_USER}@${PI_HOST}:${PI_DIR}"
echo ""
echo "💡 Tip: Run './scripts/setup_ssh_keys.sh' once to avoid password prompts"
echo ""

# Check if Pi is reachable
if ! ping -c 1 ${PI_HOST} &> /dev/null 2>&1; then
    echo "⚠️  Cannot ping ${PI_HOST} (this is OK, continuing anyway)"
fi

# Create directory on Pi
echo "📁 Creating directory on Pi..."
ssh $SSH_OPTS ${PI_USER}@${PI_HOST} "sudo mkdir -p ${PI_DIR}/{templates,static,scans} && sudo chown -R ${PI_USER}:${PI_USER} ${PI_DIR}" || {
    echo "❌ Cannot connect to Pi. Check:"
    echo "   - Pi is on same network"
    echo "   - SSH is enabled: sudo systemctl enable ssh"
    echo "   - Try IP address: PI_HOST=192.168.1.100 ./deploy_to_pi.sh"
    exit 1
}

# Sync files
echo "📤 Syncing files..."
# rsync only copies files that have changed (by size/modification time)
# Use --update to only copy if source is newer
# Use --ignore-times to always copy (force update)
FORCE_UPDATE=${FORCE_UPDATE:-false}
if [ "$FORCE_UPDATE" = "true" ]; then
    echo "⚠️  Force update mode: copying all files regardless of timestamps"
    RSYNC_FLAGS="--ignore-times"
else
    RSYNC_FLAGS="--update"
fi

rsync -avz --progress $RSYNC_FLAGS -e "ssh $SSH_OPTS" \
    --exclude 'venv/' \
    --exclude '*.pyc' \
    --exclude '__pycache__/' \
    --exclude 'checkpoints/' \
    --exclude 'ml_pipeline/' \
    --exclude '.git/' \
    --exclude 'archive*/' \
    --exclude '*.md' \
    --exclude 'docs/' \
    --exclude 'scripts/' \
    --exclude 'hardware/' \
    --exclude 'config/' \
    app.py \
    requirements.txt \
    templates/ \
    ${PI_USER}@${PI_HOST}:${PI_DIR}/

rsync -avz --progress $RSYNC_FLAGS -e "ssh $SSH_OPTS" \
    scripts/scan_once.py \
    ${PI_USER}@${PI_HOST}:${PI_DIR}/scan_once.py

rsync -avz --progress $RSYNC_FLAGS -e "ssh $SSH_OPTS" \
    hardware/led/led_on.py \
    ${PI_USER}@${PI_HOST}:${PI_DIR}/led_on.py

rsync -avz --progress $RSYNC_FLAGS -e "ssh $SSH_OPTS" \
    hardware/led/led_toggle.py \
    ${PI_USER}@${PI_HOST}:${PI_DIR}/led_toggle.py

rsync -avz --progress $RSYNC_FLAGS -e "ssh $SSH_OPTS" \
    config/pi-scan.service \
    ${PI_USER}@${PI_HOST}:${PI_DIR}/pi-scan.service

rsync -avz --progress $RSYNC_FLAGS -e "ssh $SSH_OPTS" \
    scripts/disable_usb.sh \
    ${PI_USER}@${PI_HOST}:${PI_DIR}/disable_usb.sh

rsync -avz --progress $RSYNC_FLAGS -e "ssh $SSH_OPTS" \
    scripts/enable_usb.sh \
    ${PI_USER}@${PI_HOST}:${PI_DIR}/enable_usb.sh

# Force update templates/index.html (always copy, even if timestamp matches)
echo "📄 Ensuring templates/index.html is updated..."
rsync -avz --ignore-times -e "ssh $SSH_OPTS" \
    templates/index.html \
    ${PI_USER}@${PI_HOST}:${PI_DIR}/templates/

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔄 Restarting service on Pi..."
ssh $SSH_OPTS ${PI_USER}@${PI_HOST} "sudo systemctl restart pi-scan" 2>/dev/null || echo "⚠️  Could not restart service (may not be installed yet)"

# Close SSH connection
ssh -O exit $SSH_OPTS ${PI_USER}@${PI_HOST} 2>/dev/null || true

echo ""
echo "Next steps on Pi:"
echo "  ssh ${PI_USER}@${PI_HOST}"
echo "  cd ${PI_DIR}"
echo "  # If first time:"
echo "  pip3 install -r requirements.txt"
echo "  sudo apt-get install -y python3-flask fswebcam img2pdf tesseract-ocr ocrmypdf imagemagick avahi-daemon"
echo "  sudo cp pi-scan.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable --now pi-scan"
echo ""
echo "  # To verify files updated:"
echo "  ls -lh ${PI_DIR}/templates/index.html"
echo "  sudo systemctl status pi-scan"
