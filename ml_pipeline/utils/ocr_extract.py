import subprocess
from pathlib import Path
from typing import Optional
import pytesseract
from PIL import Image

def have_command(cmd: str) -> bool:
    return subprocess.call(["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def extract_text_tesseract(image_path: Path) -> str:
    if not have_command("tesseract"):
        return ""
    try:
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        text = pytesseract.image_to_string(image, lang='eng', config=r'--oem 3 --psm 6')
        if len(text.strip()) < 50:
            text2 = pytesseract.image_to_string(image, lang='eng', config=r'--oem 3 --psm 11')
            if len(text2.strip()) > len(text.strip()):
                text = text2
        return text.strip()
    except:
        return ""

def extract_text_ocrmypdf(pdf_path: Path) -> Optional[str]:
    if not have_command("pdftotext"):
        return None
    try:
        result = subprocess.run(["pdftotext", str(pdf_path), "-"], capture_output=True, text=True, check=True, timeout=30)
        return result.stdout.strip() or None
    except:
        return None

def extract_text_from_invoice(image_path: Path, pdf_path: Optional[Path] = None) -> str:
    if pdf_path and pdf_path.exists():
        text = extract_text_ocrmypdf(pdf_path) or ""
    if not text and image_path.exists():
        text = extract_text_tesseract(image_path)
    return text if text else ""
