from __future__ import annotations
from pathlib import Path
import subprocess
import argparse
import sys


"""
Captures one image from a camera (CSI or USB), writes JPEG and a single-page PDF.
If Tesseract + ocrmypdf are installed, creates a searchable PDF; otherwise makes a dumb
image-only PDF using img2pdf.

Supports:
- CSI cameras via libcamera-still (modern) or raspistill (legacy)
- USB cameras via fswebcam
"""


def run(cmd: list[str], capture_output=False):
    """Run a command and optionally capture output."""
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=capture_output,
            text=True if capture_output else False
        )
        return result
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to run command: {cmd}") from e
    except Exception as e:
        raise Exception(f"Failed to run command: {cmd}") from e


def have(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    try:
        return subprocess.call(
            ["which", cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ) == 0
    except Exception:
        return False


def capture_image_csi(jpg: Path, resolution: str, rotate: str) -> bool:
    """Capture image using CSI camera (libcamera-still or raspistill)."""
    # Try libcamera-still first (modern Pi OS - Bookworm)
    if have("libcamera-still"):
        width, height = resolution.split("x")
        cmd = [
            "libcamera-still",
            "-o", str(jpg),  # Use -o instead of --output
            "--width", width,
            "--height", height,
            "--timeout", "1000",  # 1 second timeout
            "--nopreview",
        ]
        
        # Handle rotation
        if rotate != "0" and rotate != "auto":
            # libcamera-still uses --rotation with degrees
            cmd.extend(["--rotation", rotate])
        
        try:
            print(f"Using libcamera-still for CSI camera...", file=sys.stderr)
            run(cmd)
            return True
        except Exception as e:
            print(f"libcamera-still failed: {e}", file=sys.stderr)
    
    # Fallback to raspistill (legacy Pi OS)
    if have("raspistill"):
        width, height = resolution.split("x")
        cmd = [
            "raspistill",
            "-o", str(jpg),
            "-w", width,
            "-h", height,
            "-t", "1000",  # 1 second timeout
            "-n",  # no preview
        ]
        
        # Handle rotation
        if rotate != "0" and rotate != "auto":
            # raspistill uses -rot for rotation
            cmd.extend(["-rot", rotate])
        
        try:
            run(cmd)
            return True
        except Exception as e:
            print(f"raspistill failed: {e}", file=sys.stderr)
    
    return False


def capture_image_usb(jpg: Path, resolution: str, device: str) -> bool:
    """Capture image using USB camera (fswebcam)."""
    if not have("fswebcam"):
        return False
    
    cmd = [
        "fswebcam",
        "--no-banner",
        "-r", resolution,
        "--device", device,
        "--save", str(jpg)
    ]
    
    try:
        run(cmd)
        return True
    except Exception as e:
        print(f"fswebcam failed: {e}", file=sys.stderr)
        return False


parser = argparse.ArgumentParser()
parser.add_argument("--workdir", required=True)
parser.add_argument("--basename", required=True)
parser.add_argument("--device", default="/dev/video0")
parser.add_argument("--resolution", default="1920x1080")
parser.add_argument("--rotate", default="auto")  # auto|0|90|180|270
parser.add_argument("--camera-type", default="auto")  # auto|csi|usb
args = parser.parse_args()


workdir = Path(args.workdir)
workdir.mkdir(parents=True, exist_ok=True)
jpg = workdir / f"{args.basename}.jpg"
pdf = workdir / f"{args.basename}.pdf"


# 1) Capture image
print(f"Capturing image to {jpg}...", file=sys.stderr)
captured = False

# For CSI camera (Pi Camera), try libcamera-still first (Bookworm)
if args.camera_type == "csi" or args.camera_type == "auto":
    # Try CSI camera first (this is the Pi Camera)
    captured = capture_image_csi(jpg, args.resolution, args.rotate)
    
    if not captured and args.camera_type == "auto":
        # If CSI failed and auto mode, try USB as fallback
        print("CSI camera failed, trying USB camera...", file=sys.stderr)
        captured = capture_image_usb(jpg, args.resolution, args.device)
elif args.camera_type == "usb":
    # Force USB camera
    captured = capture_image_usb(jpg, args.resolution, args.device)

if not captured:
    raise Exception("Failed to capture image. For CSI camera, ensure libcamera-still is installed: sudo apt-get install -y libcamera-apps")

if not jpg.exists():
    raise Exception(f"Image file was not created: {jpg}")


# 2) Optional rotation via ImageMagick (if auto-orient or manual rotation needed)
if args.rotate == "auto":
    try:
        run(["mogrify", "-auto-orient", str(jpg)])
    except Exception as e:
        print(f"Warning: Auto-orient failed: {e}", file=sys.stderr)
        pass  # Best effort only


# 3) Make PDF (prefer searchable if tools exist)
if have("ocrmypdf") and have("tesseract"):
    # Create a temp pdf from image, then make searchable
    tmp_pdf = workdir / f"{args.basename}.img.pdf"
    try:
        run(["img2pdf", str(jpg), "-o", str(tmp_pdf)])
        # Deskew + OCR layer
        run(["ocrmypdf", "--deskew", "--rotate-pages", "--optimize", "3", str(tmp_pdf), str(pdf)])
        tmp_pdf.unlink(missing_ok=True)
    except Exception as e:
        print(f"OCR failed, creating image-only PDF: {e}", file=sys.stderr)
        # Fallback to image-only PDF
        run(["img2pdf", str(jpg), "-o", str(pdf)])
else:
    # Image-only PDF
    run(["img2pdf", str(jpg), "-o", str(pdf)])


print(f"Saved: {jpg.name}, {pdf.name}")
