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


def capture_image_csi(jpg: Path, resolution: str, rotate: str, zoom: float = 1.0) -> bool:
    """Capture image using CSI camera (rpicam-still, libcamera-still, or raspistill).
    
    Args:
        zoom: 1.0 = full field of view, < 1.0 = zoomed out (more visible), > 1.0 = zoomed in
    """
    # Try rpicam-still first (newer Bookworm)
    if have("rpicam-still"):
        width, height = resolution.split("x")
        cmd = [
            "rpicam-still",
            "-o", str(jpg),
            "--width", width,
            "--height", height,
            "--timeout", "1000",
            "--nopreview",
        ]
        
        # Handle zoom using ROI (Region of Interest)
        # ROI format: x,y,width,height (normalized 0.0-1.0)
        # To zoom out, we need to use a larger ROI or adjust sensor mode
        if zoom < 1.0:
            # Zoom out: show more of the scene
            # Use a larger ROI centered (this is tricky with rpicam, so we'll use --mode instead)
            # Or we can just use a lower resolution mode which gives wider FOV
            pass  # We'll handle this with sensor mode selection
        
        # Handle rotation
        if rotate != "0" and rotate != "auto":
            # rpicam-still uses --rotation with degrees
            cmd.extend(["--rotation", rotate])
        
        # For zooming out, use full sensor (ROI = 1.0)
        # For zooming in, reduce ROI (smaller ROI = more zoom)
        # ROI format: x,y,width,height (all normalized 0.0-1.0)
        if zoom < 1.0:
            # Zoom out: use full sensor (ROI = 1.0, which is default, so don't set)
            # But we can also try using a lower resolution mode which inherently has wider FOV
            pass  # Full sensor is default
        elif zoom > 1.0:
            # Zoom in: reduce ROI
            roi_size = 1.0 / zoom  # If zoom=2.0, ROI=0.5 (zoom in 2x)
            roi_x = (1.0 - roi_size) / 2.0
            roi_y = (1.0 - roi_size) / 2.0
            cmd.extend(["--roi", f"{roi_x},{roi_y},{roi_size},{roi_size}"])
        
        try:
            print(f"Using rpicam-still for CSI camera...", file=sys.stderr)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            if jpg.exists():
                return True
            else:
                print(f"rpicam-still completed but file not created", file=sys.stderr)
                if result.stderr:
                    print(f"Error output: {result.stderr}", file=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(f"rpicam-still failed with return code {e.returncode}", file=sys.stderr)
            if e.stdout:
                print(f"stdout: {e.stdout}", file=sys.stderr)
            if e.stderr:
                print(f"stderr: {e.stderr}", file=sys.stderr)
        except Exception as e:
            print(f"rpicam-still failed: {e}", file=sys.stderr)
    
    # Fallback to libcamera-still (older Bookworm)
    if have("libcamera-still"):
        width, height = resolution.split("x")
        cmd = [
            "libcamera-still",
            "-o", str(jpg),
            "--width", width,
            "--height", height,
            "--timeout", "1000",
            "--nopreview",
        ]
        
        # Handle zoom with ROI (same logic as rpicam)
        if zoom > 1.0:
            roi_size = 1.0 / zoom
            roi_x = (1.0 - roi_size) / 2.0
            roi_y = (1.0 - roi_size) / 2.0
            cmd.extend(["--roi", f"{roi_x},{roi_y},{roi_size},{roi_size}"])
        
        # Handle rotation
        if rotate != "0" and rotate != "auto":
            cmd.extend(["--rotation", rotate])
        
        try:
            print(f"Using libcamera-still for CSI camera...", file=sys.stderr)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            if jpg.exists():
                return True
        except subprocess.CalledProcessError as e:
            print(f"libcamera-still failed: {e.stderr if e.stderr else e}", file=sys.stderr)
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
parser.add_argument("--zoom", type=float, default=0.7)  # 1.0 = normal, < 1.0 = zoom out (show more), > 1.0 = zoom in
args = parser.parse_args()


workdir = Path(args.workdir)
workdir.mkdir(parents=True, exist_ok=True)
jpg = workdir / f"{args.basename}.jpg"
pdf = workdir / f"{args.basename}.pdf"


# 1) Capture image
print(f"Capturing image to {jpg}...", file=sys.stderr)
captured = False

# For CSI camera (Pi Camera), try rpicam-still first (Bookworm)
if args.camera_type == "csi" or args.camera_type == "auto":
    # Check if camera tools are available
    if have("rpicam-still") or have("libcamera-still") or have("raspistill"):
        print("Attempting to use CSI camera...", file=sys.stderr)
        # Try CSI camera first (this is the Pi Camera)
        captured = capture_image_csi(jpg, args.resolution, args.rotate, args.zoom)
    else:
        print("No CSI camera tools found (rpicam-still, libcamera-still, or raspistill)", file=sys.stderr)
    
    if not captured and args.camera_type == "auto":
        # If CSI failed and auto mode, try USB as fallback
        print("CSI camera failed, trying USB camera...", file=sys.stderr)
        captured = capture_image_usb(jpg, args.resolution, args.device)
elif args.camera_type == "usb":
    # Force USB camera
    captured = capture_image_usb(jpg, args.resolution, args.device)

if not captured:
    raise Exception("Failed to capture image. For CSI camera, ensure rpicam-apps or libcamera-apps is installed: sudo apt-get install -y rpicam-apps")

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
