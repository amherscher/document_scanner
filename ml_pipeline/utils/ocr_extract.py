import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import re

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# PIL-only receipt detection (no OpenCV needed)
def detect_and_crop_receipt_pil(image: Image.Image) -> Image.Image:
    """
    Detect receipt area using PIL only (no OpenCV).
    Finds the largest white/bright rectangular area.
    """
    try:
        # Convert to grayscale
        gray = image.convert('L')
        width, height = gray.size
        
        # Find the brightest region (white paper)
        # Sample points across the image to find paper boundaries
        threshold = 200  # White paper is typically > 200
        
        # Find top boundary (first row with mostly white pixels)
        top = 0
        for y in range(height):
            row = [gray.getpixel((x, y)) for x in range(0, width, 10)]  # Sample every 10px
            white_ratio = sum(1 for p in row if p > threshold) / len(row)
            if white_ratio > 0.3:  # 30% white pixels = likely paper
                top = max(0, y - 10)  # Add small padding
                break
        
        # Find bottom boundary
        bottom = height
        for y in range(height - 1, -1, -1):
            row = [gray.getpixel((x, y)) for x in range(0, width, 10)]
            white_ratio = sum(1 for p in row if p > threshold) / len(row)
            if white_ratio > 0.3:
                bottom = min(height, y + 10)
                break
        
        # Find left boundary
        left = 0
        for x in range(width):
            col = [gray.getpixel((x, y)) for y in range(0, height, 10)]
            white_ratio = sum(1 for p in col if p > threshold) / len(col)
            if white_ratio > 0.3:
                left = max(0, x - 10)
                break
        
        # Find right boundary
        right = width
        for x in range(width - 1, -1, -1):
            col = [gray.getpixel((x, y)) for y in range(0, height, 10)]
            white_ratio = sum(1 for p in col if p > threshold) / len(col)
            if white_ratio > 0.3:
                right = min(width, x + 10)
                break
        
        # Only crop if we found reasonable boundaries
        if (right - left) > width * 0.3 and (bottom - top) > height * 0.3:
            cropped = image.crop((left, top, right, bottom))
            
            # Enhance contrast for better OCR
            enhancer = ImageEnhance.Contrast(cropped)
            enhanced = enhancer.enhance(1.5)
            
            # Resize if too small
            w, h = enhanced.size
            if w < 1200 or h < 1200:
                scale = max(1200 / w, 1200 / h)
                scale = min(scale, 2.0)  # Don't scale more than 2x
                new_size = (int(w * scale), int(h * scale))
                enhanced = enhanced.resize(new_size, Image.LANCZOS)
            
            return enhanced
        
        return image  # No good crop found, return original
    except Exception:
        return image

def have_command(cmd: str) -> bool:
    return subprocess.call(["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def detect_and_crop_receipt(image: Image.Image) -> Image.Image:
    """
    Detect the receipt/paper area in the image and crop to just that area.
    Finds the largest white/bright area (the paper) and crops to it.
    Uses OpenCV if available, otherwise falls back to PIL-only method.
    """
    if not CV2_AVAILABLE:
        # Use PIL-only method if OpenCV not available
        return detect_and_crop_receipt_pil(image)
    
    try:
        # Convert PIL to OpenCV format
        img_array = np.array(image.convert('RGB'))
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        original = img_cv.copy()
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Find white paper: threshold to get bright areas (white paper is typically > 200)
        # Try multiple thresholds to find the paper
        thresholds = [200, 180, 160]
        best_contour = None
        best_area = 0
        
        for thresh_val in thresholds:
            _, thresh = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
            
            # Apply morphological operations to clean up
            kernel = np.ones((3, 3), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Find largest contour
                largest = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest)
                # Paper should be at least 5% of image
                if area > img_cv.shape[0] * img_cv.shape[1] * 0.05 and area > best_area:
                    best_contour = largest
                    best_area = area
        
        if best_contour is None:
            return image  # No paper found, return original
        
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(best_contour)
        
        # Add small padding (2% on each side)
        padding_x = max(5, int(w * 0.02))
        padding_y = max(5, int(h * 0.02))
        x = max(0, x - padding_x)
        y = max(0, y - padding_y)
        w = min(img_cv.shape[1] - x, w + 2 * padding_x)
        h = min(img_cv.shape[0] - y, h + 2 * padding_y)
        
        # Crop the image
        cropped = original[y:y+h, x:x+w]
        
        # Enhance the cropped image for better OCR
        cropped_gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(cropped_gray)
        
        # Increase contrast more
        enhanced = cv2.convertScaleAbs(enhanced, alpha=1.2, beta=10)
        
        # Convert back to RGB for PIL
        enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
        cropped_pil = Image.fromarray(enhanced_rgb)
        
        # Resize if too small (Tesseract works better on larger images, but not too large)
        width, height = cropped_pil.size
        target_size = 2000  # Target size for better OCR
        if width < target_size or height < target_size:
            scale = min(target_size / width, target_size / height)
            # Don't scale up too much (max 2x)
            scale = min(scale, 2.0)
            new_width = int(width * scale)
            new_height = int(height * scale)
            cropped_pil = cropped_pil.resize((new_width, new_height), Image.LANCZOS)
        
        return cropped_pil
    except Exception as e:
        # If anything fails, return original image
        return image

def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Preprocess image to improve OCR accuracy:
    - Convert to grayscale
    - Enhance contrast
    - Sharpen
    - Apply thresholding for better text recognition
    """
    # Convert to grayscale if needed
    if image.mode != 'L':
        image = image.convert('L')
    
    # Resize if image is too small (Tesseract works better on larger images)
    width, height = image.size
    if width < 1000 or height < 1000:
        # Scale up to at least 1000px on the smaller dimension
        scale = max(1000 / width, 1000 / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = image.resize((new_width, new_height), Image.LANCZOS)
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)  # Increase contrast by 50%
    
    # Sharpen
    image = image.filter(ImageFilter.SHARPEN)
    
    # Convert to numpy for thresholding
    img_array = np.array(image)
    
    # Apply adaptive thresholding (makes text more distinct from background)
    # Simple threshold: values above 128 become 255 (white), below become 0 (black)
    threshold = 128
    img_array = np.where(img_array > threshold, 255, 0).astype(np.uint8)
    
    # Convert back to PIL Image
    image = Image.fromarray(img_array)
    
    return image

def extract_text_tesseract(image_path: Path) -> str:
    if not have_command("tesseract"):
        return ""
    
    # Try multiple OCR strategies and pick the best result
    results = []
    
    try:
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # First, try to detect and crop to just the receipt area
        # This removes background noise and improves OCR accuracy
        cropped_image = detect_and_crop_receipt(image)
        
        # Strategy 1: Cropped image with PSM 4 (single column) - BEST for receipts
        try:
            text1b = pytesseract.image_to_string(cropped_image, lang='eng', config=r'--oem 3 --psm 4').strip()
            if text1b and len(text1b) > 20:  # Need more text
                if has_reasonable_text_quality(text1b):
                    results.append(('cropped_psm4', text1b))
                # Even if quality check fails, if it has numbers/keywords, use it
                elif any(kw in text1b.lower() for kw in ['kroger', 'total', 'balance', 'tax']) or re.search(r'[\d,]+\.\d{2}', text1b):
                    results.append(('cropped_psm4_fallback', text1b))
        except:
            pass
        
        # Strategy 1a: Cropped image with PSM 6 (uniform block of text)
        try:
            text1 = pytesseract.image_to_string(cropped_image, lang='eng', config=r'--oem 3 --psm 6').strip()
            if text1 and len(text1) > 20:
                if has_reasonable_text_quality(text1):
                    results.append(('cropped_psm6', text1))
        except:
            pass
        
        # Strategy 2: Original image with PSM 6 (fallback if cropping didn't help)
        try:
            text2 = pytesseract.image_to_string(image, lang='eng', config=r'--oem 3 --psm 6').strip()
            if text2 and len(text2) > 10 and has_reasonable_text_quality(text2):
                results.append(('original_psm6', text2))
        except:
            pass
        
        # Strategy 3: Original image with PSM 4 (single column)
        try:
            text3 = pytesseract.image_to_string(image, lang='eng', config=r'--oem 3 --psm 4').strip()
            if text3 and len(text3) > 10 and has_reasonable_text_quality(text3):
                results.append(('original_psm4', text3))
        except:
            pass
        
        # Strategy 4: Light preprocessing on cropped image (just grayscale and contrast)
        try:
            gray = cropped_image.convert('L')
            # Resize if too small (but don't make it too large either)
            width, height = gray.size
            if width < 1000 or height < 1000:
                scale = max(1000 / width, 1000 / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                gray = gray.resize((new_width, new_height), Image.LANCZOS)
            enhancer = ImageEnhance.Contrast(gray)
            enhanced = enhancer.enhance(1.3)  # Light contrast boost
            text4 = pytesseract.image_to_string(enhanced, lang='eng', config=r'--oem 3 --psm 4').strip()
            if text4 and len(text4) > 10 and has_reasonable_text_quality(text4):
                results.append(('cropped_light_preprocess_psm4', text4))
        except:
            pass
        
        # Strategy 4: Aggressive preprocessing (only if others failed)
        if not results:
            try:
                preprocessed = preprocess_image_for_ocr(image.convert('L'))
                text4 = pytesseract.image_to_string(preprocessed, lang='eng', config=r'--oem 3 --psm 6').strip()
                if text4 and len(text4) > 10 and has_reasonable_text_quality(text4):
                    results.append(('aggressive_preprocess', text4))
            except:
                pass
        
        # Pick the best result (prioritize quality over length)
        if results:
            # Sort by quality (has receipt keywords) then length
            def score_result(x):
                text_lower = x[1].lower()
                quality_score = 0
                receipt_keywords = ['kroger', 'total', 'balance', 'tax', 'subtotal', 'amount', 'receipt', 'invoice']
                if any(keyword in text_lower for keyword in receipt_keywords):
                    quality_score = 1000  # Big boost for having receipt keywords
                return (quality_score, len(x[1]), count_letters(x[1]))
            
            results.sort(key=score_result, reverse=True)
            return results[0][1]
        
        # Fallback: return longest text even if quality is questionable
        # But prefer text with receipt keywords or numbers
        candidates = []
        if text1 and len(text1) > 10:
            candidates.append(text1)
        if text2 and len(text2) > 10:
            candidates.append(text2)
        if 'text2b' in locals() and text2b and len(text2b) > 10:
            candidates.append(text2b)
        if 'text2c' in locals() and text2c and len(text2c) > 10:
            candidates.append(text2c)
        if 'text3b' in locals() and text3b and len(text3b) > 10:
            candidates.append(text3b)
        
        if candidates:
            # Prefer candidate with receipt keywords or numbers (dollar amounts)
            import re
            for candidate in candidates:
                text_lower = candidate.lower()
                # Check for receipt keywords
                if any(kw in text_lower for kw in ['kroger', 'total', 'balance', 'tax', 'amount']):
                    return candidate
                # Check for dollar amounts (has numbers with .XX pattern)
                if re.search(r'[\d,]+\.\d{2}', candidate):
                    return candidate
            # If no keywords/numbers, return longest
            return max(candidates, key=len)
        
        return ""
    except Exception as e:
        # Final fallback
        try:
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return pytesseract.image_to_string(image, lang='eng', config=r'--oem 3 --psm 6').strip()
        except:
            return ""

def has_reasonable_text_quality(text: str) -> bool:
    """Check if text looks like real text, not OCR garbage"""
    if not text or len(text) < 10:
        return False
    
    # Count letters vs special characters
    letters = sum(1 for c in text if c.isalpha())
    digits = sum(1 for c in text if c.isdigit())
    spaces = sum(1 for c in text if c.isspace())
    special = len(text) - letters - digits - spaces
    
    # Real text should have mostly letters and spaces
    total_chars = len(text)
    letter_ratio = letters / total_chars if total_chars > 0 else 0
    
    # If less than 25% letters, it's probably garbage (lowered threshold)
    if letter_ratio < 0.25:
        return False
    
    # If too many special characters (>50%), it's probably garbage (raised threshold)
    special_ratio = special / total_chars if total_chars > 0 else 0
    if special_ratio > 0.5:
        return False
    
    # Should have some words (sequences of letters)
    words = [w for w in text.split() if any(c.isalpha() for c in w)]
    if len(words) < 2:  # Need at least a couple words (lowered threshold)
        return False
    
    # Check for common receipt words (Kroger, total, balance, tax, etc.)
    text_lower = text.lower()
    receipt_keywords = ['kroger', 'total', 'balance', 'tax', 'subtotal', 'amount', 'receipt', 'invoice', 'date', 'cashier']
    if any(keyword in text_lower for keyword in receipt_keywords):
        return True  # If it has receipt keywords, it's probably real text
    
    return True

def count_letters(text: str) -> int:
    """Count alphabetic characters in text"""
    return sum(1 for c in text if c.isalpha())

def extract_text_with_details(image_path: Path) -> Tuple[str, List[Dict]]:
    """
    Extract text with detailed OCR data (bounding boxes, confidence scores).
    Returns: (full_text, word_data_list)
    word_data_list contains: {'text': str, 'confidence': int, 'left': int, 'top': int, 'width': int, 'height': int}
    """
    if not have_command("tesseract"):
        return "", []
    
    # First get the best text using the improved extraction
    text = extract_text_tesseract(image_path)
    
    # Now get detailed data using the same strategy that worked
    word_data = []
    try:
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Try original image first (usually best)
        try:
            data = pytesseract.image_to_data(image, lang='eng', config=r'--oem 3 --psm 6', output_type=pytesseract.Output.DICT)
            extracted_text = pytesseract.image_to_string(image, lang='eng', config=r'--oem 3 --psm 6').strip()
            
            # Only use this if the text quality is reasonable
            if has_reasonable_text_quality(extracted_text) or not text:
                # Build word data list
                n_boxes = len(data['text'])
                for i in range(n_boxes):
                    conf = int(data['conf'][i])
                    word_text = data['text'][i].strip()
                    if conf > 0 and word_text:  # Only include words with confidence > 0 and non-empty text
                        word_data.append({
                            'text': word_text,
                            'confidence': conf,
                            'left': data['left'][i],
                            'top': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        })
        except:
            pass
        
        # If we didn't get good word data, try with light preprocessing
        if not word_data or len(word_data) < 10:
            try:
                gray = image.convert('L')
                enhancer = ImageEnhance.Contrast(gray)
                enhanced = enhancer.enhance(1.3)
                data = pytesseract.image_to_data(enhanced, lang='eng', config=r'--oem 3 --psm 6', output_type=pytesseract.Output.DICT)
                
                n_boxes = len(data['text'])
                for i in range(n_boxes):
                    conf = int(data['conf'][i])
                    word_text = data['text'][i].strip()
                    if conf > 0 and word_text:
                        word_data.append({
                            'text': word_text,
                            'confidence': conf,
                            'left': data['left'][i],
                            'top': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        })
            except:
                pass
        
        return text, word_data
    except:
        # Fallback
        try:
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            text = pytesseract.image_to_string(image, lang='eng', config=r'--oem 3 --psm 6').strip()
            return text, []
        except:
            return "", []

def extract_text_ocrmypdf(pdf_path: Path) -> Optional[str]:
    if not have_command("pdftotext"):
        return None
    try:
        result = subprocess.run(["pdftotext", str(pdf_path), "-"], capture_output=True, text=True, check=True, timeout=30)
        return result.stdout.strip() or None
    except:
        return None

def extract_text_from_invoice(image_path: Path, pdf_path: Optional[Path] = None) -> str:
    text = ""
    if pdf_path and pdf_path.exists():
        text = extract_text_ocrmypdf(pdf_path) or ""
    if not text and image_path.exists():
        text = extract_text_tesseract(image_path)
    return text if text else ""

def extract_text_with_details_from_invoice(image_path: Path, pdf_path: Optional[Path] = None) -> Tuple[str, List[Dict]]:
    """
    Extract text with detailed OCR data for better vendor extraction.
    Returns: (full_text, word_data_list)
    """
    text = ""
    word_data = []
    if pdf_path and pdf_path.exists():
        text = extract_text_ocrmypdf(pdf_path) or ""
        # PDF text doesn't have bounding boxes, so word_data will be empty
    if not text and image_path.exists():
        text, word_data = extract_text_with_details(image_path)
    return text if text else "", word_data
