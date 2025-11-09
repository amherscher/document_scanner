from __future__ import annotations
from pathlib import Path
import subprocess
import argparse
import sys




def run(cmd: list[str], capture_output=False):
    subprocess.run(cmd, check=True, capture_output=capture_output, text=bool(capture_output))


def have(cmd: str) -> bool:
    return subprocess.call(["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


def capture_image_csi(jpg: Path, resolution: str, rotate: str, zoom: float = 1.0) -> bool:
    width, height = resolution.split("x")
    
    if have("rpicam-still"):
        cmd = ["rpicam-still", "-o", str(jpg), "--width", width, "--height", height, "--timeout", "1000", "--nopreview"]
        if rotate not in ("0", "auto"):
            cmd.extend(["--rotation", rotate])
        if zoom > 1.0:
            roi_size = 1.0 / zoom
            roi_x = (1.0 - roi_size) / 2.0
            roi_y = (1.0 - roi_size) / 2.0
            cmd.extend(["--roi", f"{roi_x},{roi_y},{roi_size},{roi_size}"])
        subprocess.run(cmd, check=True, capture_output=True)
        return jpg.exists()
    
    if have("libcamera-still"):
        cmd = ["libcamera-still", "-o", str(jpg), "--width", width, "--height", height, "--timeout", "1000", "--nopreview"]
        if rotate not in ("0", "auto"):
            cmd.extend(["--rotation", rotate])
        if zoom > 1.0:
            roi_size = 1.0 / zoom
            roi_x = (1.0 - roi_size) / 2.0
            roi_y = (1.0 - roi_size) / 2.0
            cmd.extend(["--roi", f"{roi_x},{roi_y},{roi_size},{roi_size}"])
        subprocess.run(cmd, check=True, capture_output=True)
        return jpg.exists()
    
    if have("raspistill"):
        cmd = ["raspistill", "-o", str(jpg), "-w", width, "-h", height, "-t", "1000", "-n"]
        if rotate not in ("0", "auto"):
            cmd.extend(["-rot", rotate])
        run(cmd)
        return True
    
    return False


def capture_image_usb(jpg: Path, resolution: str, device: str) -> bool:
    if not have("fswebcam"):
        return False
    run(["fswebcam", "--no-banner", "-r", resolution, "--device", device, "--save", str(jpg)])
    return True


parser = argparse.ArgumentParser()
parser.add_argument("--workdir", required=True)
parser.add_argument("--basename", required=True)
parser.add_argument("--device", default="/dev/video0")
parser.add_argument("--resolution", default="1920x1080")
parser.add_argument("--rotate", default="auto")
parser.add_argument("--camera-type", default="auto")
parser.add_argument("--zoom", type=float, default=0.3)
args = parser.parse_args()


workdir = Path(args.workdir)
workdir.mkdir(parents=True, exist_ok=True)
jpg = workdir / f"{args.basename}.jpg"
pdf = workdir / f"{args.basename}.pdf"


if args.camera_type in ("csi", "auto") and (have("rpicam-still") or have("libcamera-still") or have("raspistill")):
    captured = capture_image_csi(jpg, args.resolution, args.rotate, args.zoom)
    if not captured and args.camera_type == "auto":
        captured = capture_image_usb(jpg, args.resolution, args.device)
elif args.camera_type == "usb":
    captured = capture_image_usb(jpg, args.resolution, args.device)
else:
    captured = False

if not captured or not jpg.exists():
    raise Exception("Failed to capture image")


if args.rotate == "auto":
    try:
        run(["mogrify", "-auto-orient", str(jpg)])
    except Exception:
        pass


if have("ocrmypdf") and have("tesseract"):
    tmp_pdf = workdir / f"{args.basename}.img.pdf"
    try:
        run(["img2pdf", str(jpg), "-o", str(tmp_pdf)])
        run(["ocrmypdf", "--deskew", "--rotate-pages", "--optimize", "3", str(tmp_pdf), str(pdf)])
        tmp_pdf.unlink(missing_ok=True)
    except Exception:
        run(["img2pdf", str(jpg), "-o", str(pdf)])
else:
    run(["img2pdf", str(jpg), "-o", str(pdf)])
