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
        # Optimized settings for text/document scanning
        cmd = [
            "rpicam-still", "-o", str(jpg),
            "--width", width, "--height", height,
            "--timeout", "2000",  # Longer timeout for autofocus
            "--nopreview",
            "--sharpness", "2.0",      # Increase sharpness for crisp text
            "--contrast", "1.3",       # Higher contrast for text clarity
            "--saturation", "0.8",     # Slightly desaturate for B&W documents
            "--exposure", "normal",    # Normal exposure (not too bright/dark)
            "--awb", "auto",           # Auto white balance
            "--autofocus-mode", "auto", # Autofocus for sharp text
        ]
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
        # Optimized settings for text/document scanning
        cmd = [
            "libcamera-still", "-o", str(jpg),
            "--width", width, "--height", height,
            "--timeout", "2000",  # Longer timeout for autofocus
            "--nopreview",
            "--sharpness", "2.0",      # Increase sharpness for crisp text
            "--contrast", "1.3",       # Higher contrast for text clarity
            "--saturation", "0.8",     # Slightly desaturate for B&W documents
            "--exposure", "normal",    # Normal exposure
            "--awb", "auto",           # Auto white balance
        ]
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
        # Optimized settings for text/document scanning (legacy camera)
        cmd = [
            "raspistill", "-o", str(jpg),
            "-w", width, "-h", height,
            "-t", "2000",  # Longer timeout
            "-n",  # No preview
            "-sh", "50",   # Sharpness (0-100, 50 is default, increase for text)
            "-co", "20",   # Contrast (0-100, increase for text clarity)
            "-sa", "-20",  # Saturation (reduce for B&W documents)
            "-ex", "auto", # Exposure mode
            "-awb", "auto", # Auto white balance
            "-ifx", "none", # No image effects
        ]
        if rotate not in ("0", "auto"):
            cmd.extend(["-rot", rotate])
        run(cmd)
        return True
    
    return False


def capture_image_usb(jpg: Path, resolution: str, device: str) -> bool:
    if not have("fswebcam"):
        return False
    # Optimized settings for text/document scanning with USB camera
    cmd = [
        "fswebcam",
        "--no-banner",
        "-r", resolution,
        "--device", device,
        "--set", "brightness=50%",      # Adjust if needed (0-100%)
        "--set", "contrast=60%",         # Higher contrast for text
        "--set", "sharpness=70%",        # Higher sharpness for crisp text
        "--set", "saturation=30%",      # Lower saturation for B&W documents
        "--set", "focus_auto=1",        # Autofocus if supported
        "--save", str(jpg)
    ]
    run(cmd)
    return True


parser = argparse.ArgumentParser()
parser.add_argument("--workdir", required=True)
parser.add_argument("--basename", required=True)
parser.add_argument("--device", default="/dev/video0")
parser.add_argument("--resolution", default="2592x1944")  # Higher resolution for better OCR
parser.add_argument("--rotate", default="auto")
parser.add_argument("--camera-type", default="auto")
parser.add_argument("--zoom", type=float, default=0.3)
args = parser.parse_args()


workdir = Path(args.workdir)
workdir.mkdir(parents=True, exist_ok=True)
jpg = workdir / f"{args.basename}.jpg"
# PDF generation removed - JPG is sufficient for OCR and classification
pdf = None  # Not generating PDFs anymore


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


# Post-process image for optimal text recognition
try:
    if args.rotate == "auto":
        run(["mogrify", "-auto-orient", str(jpg)])
    # Enhance image for OCR: increase contrast, sharpen, convert to grayscale if needed
    # This helps Tesseract recognize text better
    run(["mogrify", 
         "-normalize",           # Normalize brightness/contrast
         "-sharpen", "0x1.0",   # Sharpen for text edges
         "-contrast",            # Increase contrast
         str(jpg)])
except Exception:
    pass  # Continue even if ImageMagick fails


# PDF generation removed - JPG is better for OCR and classification
# PDFs were just image PDFs anyway and didn't help with OCR
# Uncomment below if you need PDFs for archival purposes:
# if have("img2pdf"):
#     run(["img2pdf", str(jpg), "-o", str(pdf)])
