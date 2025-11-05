from __future__ import annotations
from pathlib import Path
import subprocess
import argparse
import sys


"""
Captures one image from a USB webcam using fswebcam, writes JPEG and a single-page PDF.
If Tesseract + ocrmypdf are installed, creates a searchable PDF; otherwise makes a dumb
image-only PDF using img2pdf.
"""


def run(cmd: list[str]):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to run command: {cmd}") from e
    except Exception as e:
        raise Exception(f"Failed to run command: {cmd}") from e


parser = argparse.ArgumentParser()
parser.add_argument("--workdir", required=True)
parser.add_argument("--basename", required=True)
parser.add_argument("--device", default="/dev/video0")
parser.add_argument("--resolution", default="1920x1080")
parser.add_argument("--rotate", default="auto") # auto|0|90|180|270
args = parser.parse_args()


workdir = Path(args.workdir)
workdir.mkdir(parents=True, exist_ok=True)
jpg = workdir / f"{args.basename}.jpg"
pdf = workdir / f"{args.basename}.pdf"


# 1) capture
# Install: sudo apt-get install -y fswebcam
run([
"fswebcam", "--no-banner", "-r", args.resolution, "--save", str(jpg)
])


# optional rotate via ImageMagick if auto or angle given
try:
    if args.rotate != "0":
        angle = "-auto-orient" if args.rotate == "auto" else str(int(args.rotate))
        if angle == "-auto-orient":
            run(["mogrify", "-auto-orient", str(jpg)])
        else:
            run(["mogrify", "-rotate", angle, str(jpg)])
except Exception:
        pass # make rotation best-effort only
if angle == "-auto-orient":
    run(["mogrify", "-auto-orient", str(jpg)])
else:
    run(["mogrify", "-rotate", angle, str(jpg)]) 
pass # make rotation best-effort only


# 2) make pdf (prefer searchable if tools exist)
def have(cmd):
    try:
        return subprocess.call(["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
    except Exception as e:
        return False


if have("ocrmypdf") and have("tesseract"):
# create a temp pdf from image, then make searchable
    tmp_pdf = workdir / f"{args.basename}.img.pdf"
run(["img2pdf", str(jpg), "-o", str(tmp_pdf)])
# deskew + OCR layer
run(["ocrmypdf", "--deskew", "--rotate-pages", "--optimize", "3", str(tmp_pdf), str(pdf)])
tmp_pdf.unlink(missing_ok=True)

try:
    if have("ocrmypdf") and have("tesseract"):
        tmp_pdf = workdir / f"{args.basename}.img.pdf"
        run(["img2pdf", str(jpg), "-o", str(tmp_pdf)])
        run(["ocrmypdf", "--deskew", "--rotate-pages", "--optimize", "3", str(tmp_pdf), str(pdf)])
        tmp_pdf.unlink(missing_ok=True)
except Exception as e:
    raise Exception(f"Failed to OCR PDF: {e}") from e
else:
# image-only
    try:
        run(["img2pdf", str(jpg), "-o", str(pdf)])
    except Exception as e:
        raise Exception(f"Failed to create PDF: {e}") from e


print(f"Saved: {jpg.name}, {pdf.name}")