

### FILE: /opt/scanner/README.md
Setup on Raspberry Pi (USB webcam):


1) Install packages
sudo apt-get update
sudo apt-get install -y python3-flask fswebcam img2pdf tesseract-ocr ocrmypdf avahi-daemon
# optional for LED USB-port control
sudo apt-get install -y uhubctl imagemagick


2) Create app folder
sudo mkdir -p /opt/scanner/templates /opt/scanner/static /opt/scanner/scans
# copy files from this doc to matching paths
# ensure ownership
sudo chown -R pi:pi /opt/scanner


3) Enable service
sudo cp /opt/scanner/pi-scan.service /etc/systemd/system/pi-scan.service
sudo systemctl daemon-reload
sudo systemctl enable --now pi-scan


4) Browse from phone/iPad
http://pi-scan.local:5000 (mDNS via avahi-daemon)
# If you set PI_SCAN_REQUIRE_AUTH=1, requests need header X-Auth: <token>


5) Change save folder from the web page, or default is /opt/scanner/scans


Notes:
- First run creates JPG+PDF. If ocrmypdf is present, the PDF is searchable.
- LED toggle requires either a controllable USB hub (uhubctl) or replacing led_toggle.py
with your LED controller’s CLI.
- For HTTPS on LAN later, you can reverse-proxy via Caddy or nginx with a local cert.