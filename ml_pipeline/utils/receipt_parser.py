import re
from typing import Dict, List, Optional

def extract_amounts(text: str) -> Dict[str, Optional[float]]:
    amounts = {'total': None, 'subtotal': None, 'tax': None, 'discount': None}
    patterns = {
        'total': [
            r'total[:\s]+[\$]?([\d,]+\.?\d*)',
            r'amount[:\s]+[\$]?([\d,]+\.?\d*)',
            r'[\$]([\d,]+\.?\d*)\s*(?:total|due|amount)',
            r'grand\s+total[:\s]+[\$]?([\d,]+\.?\d*)',
            r'balance[:\s]+due[:\s]+[\$]?([\d,]+\.?\d*)',
            r'balance[:\s]+[\$]?([\d,]+\.?\d*)',  # BALANCE: 10.53 (without "due")
            r'amount\s+due[:\s]+[\$]?([\d,]+\.?\d*)',
            r'[\$]([\d,]+\.\d{2})\s*(?:\n|$|total)',
        ],
        'subtotal': [r'subtotal[:\s]+[\$]?([\d,]+\.?\d*)', r'sub\s+total[:\s]+[\$]?([\d,]+\.?\d*)'],
        'tax': [r'tax[:\s]+[\$]?([\d,]+\.?\d*)', r'vat[:\s]+[\$]?([\d,]+\.?\d*)', r'sales\s+tax[:\s]+[\$]?([\d,]+\.?\d*)'],
        'discount': [r'discount[:\s]+[\$]?([\d,]+\.?\d*)', r'discount\s+amount[:\s]+[\$]?([\d,]+\.?\d*)']
    }
    text_lower = text.lower()
    # First, try to extract explicit subtotal / tax / discount / total using label-based patterns
    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    amounts[key] = float(match.group(1).replace(',', ''))
                    break
                except Exception:
                    continue

    # If total is still missing, find the largest dollar amount (simple fallback)
    if amounts['total'] is None:
        # Find all dollar amounts in the text
        # Pattern: $XX.XX or XX.XX (with optional commas)
        all_amounts = []
        for match in re.finditer(r'[\$]?\s*([\d,]+\.\d{2})', text):
            try:
                val = float(match.group(1).replace(',', ''))
                if 0.01 <= val <= 999999:  # Reasonable range
                    all_amounts.append(val)
            except Exception:
                continue
        
        # Also try patterns without .XX (like $50 or 50)
        for match in re.finditer(r'[\$]?\s*([\d,]+)(?:\.\d{0,2})?\s*(?:total|due|amount)', text, re.IGNORECASE):
            try:
                val = float(match.group(1).replace(',', ''))
                if 0.01 <= val <= 999999:
                    all_amounts.append(val)
            except Exception:
                continue
        
        # Use the largest amount found (usually the total)
        if all_amounts:
            amounts['total'] = max(all_amounts)
    
    # Calculate total from subtotal + tax if needed
    if amounts['total'] is None and amounts['subtotal']:
        amounts['total'] = amounts['subtotal']
        if amounts['tax']:
            amounts['total'] += amounts['tax']
    
    return amounts

def extract_date(text: str) -> Optional[str]:
    for pattern in [r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})']:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                groups = match.groups()
                if len(groups[0]) == 4:
                    year, month, day = groups
                else:
                    month, day, year = groups
                month, day, year = int(month), int(day), int(year)
                if year < 100:
                    year += 2000 if year < 50 else 1900
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return f"{year:04d}-{month:02d}-{day:02d}"
            except:
                continue
    return None

def clean_vendor_name(vendor_text: str) -> str:
    """Clean up OCR noise from vendor names"""
    if not vendor_text:
        return vendor_text
    
    words = vendor_text.split()
    if len(words) > 1:
        # Remove trailing words that are very short (likely OCR noise)
        # Keep the first 1-2 words (usually the business name) and skip trailing fragments
        cleaned_words = []
        for i, word in enumerate(words):
            # Keep first word always
            if i == 0:
                cleaned_words.append(word)
            # Keep second word if it's 3+ chars (likely part of name like "Kroger Co")
            elif i == 1 and len(word) >= 3:
                cleaned_words.append(word)
            # Skip trailing short words (1-2 chars) - these are usually OCR noise
            elif len(word) >= 3:
                # Only keep if it looks like a real word (has vowels or common patterns)
                if any(c.lower() in 'aeiou' for c in word) or len(word) >= 4:
                    cleaned_words.append(word)
        
        if cleaned_words:
            vendor_text = ' '.join(cleaned_words)
    
    return vendor_text.strip()

def extract_vendor(text: str, word_data: Optional[List[Dict]] = None) -> Optional[str]:
    """
    Extract vendor name by finding the largest/most prominent text in the top portion.
    Vendor names are typically the largest text at the top of receipts/invoices.
    
    If word_data (OCR bounding boxes) is provided, uses font size (bounding box area)
    to find the largest text block. Otherwise falls back to text-based heuristics.
    """
    # If we have OCR bounding box data, use it to find the largest text block
    if word_data:
        vendor = extract_vendor_from_ocr_data(text, word_data)
    else:
        # Fallback to text-based extraction
        vendor = extract_vendor_from_text(text)
    
    # Clean up OCR noise
    if vendor:
        vendor = clean_vendor_name(vendor)
    
    return vendor

def extract_vendor_from_ocr_data(text: str, word_data: List[Dict]) -> Optional[str]:
    """
    Extract vendor by finding the LARGEST text on the page.
    Simple approach: vendor names are almost always the biggest text.
    """
    if not word_data:
        return None
    
    # Group words by line (words with similar Y coordinates)
    lines = {}
    for word in word_data:
        if not word['text'].strip() or word['confidence'] < 10:
            continue
        y = word['top']
        # Group words within 20 pixels vertically
        line_key = (y // 20) * 20
        if line_key not in lines:
            lines[line_key] = []
        lines[line_key].append(word)
    
    # Only look at top 40% of document (vendor is always at top)
    sorted_lines = sorted(lines.items())
    top_portion = sorted_lines[:max(15, len(sorted_lines) * 2 // 5)]
    
    candidates = []
    for y_pos, words in top_portion:
        # Combine words on this line
        line_text = ' '.join(w['text'].strip() for w in words if w['text'].strip())
        line_text = line_text.strip()
        
        # Very basic filters - just skip obvious non-vendor text
        if not line_text or len(line_text) < 3:
            continue
        
        # Skip if it's just numbers or dates
        if re.match(r'^[\d\s\-\/\.]+$', line_text):
            continue
        
        # Skip if it's a dollar amount
        if re.search(r'[\$]\s*\d+\.\d{2}', line_text):
            continue
        
        # Skip if it looks like an address
        if re.search(r'\d+\s+(street|st|avenue|ave|road|rd|drive|dr|lane|ln|boulevard|blvd)', line_text, re.IGNORECASE):
            continue
        
        # Skip if it looks like a phone number
        if re.search(r'\d{3}[-.]?\d{3}[-.]?\d{4}', line_text):
            continue
        
        # Skip common receipt words
        line_lower = line_text.lower().strip()
        if line_lower in ['receipt', 'invoice', 'thank you', 'date', 'time', 'total', 'subtotal', 'tax', 'amount', 'fresh for everyone']:
            continue
        
        # Prefer shorter lines (1-3 words) - more likely to be vendor names
        word_count = len([w for w in line_text.split() if w.strip()])
        if word_count > 5:  # Skip very long lines (likely addresses or descriptions)
            continue
        
        # Calculate average font size (height) for this line
        avg_height = sum(w['height'] for w in words) / len(words) if words else 0
        
        # Store candidate with its size and word count
        candidates.append({
            'text': line_text,
            'height': avg_height,
            'word_count': word_count,
            'y_pos': y_pos
        })
    
    if not candidates:
        return None
    
    # Prefer shorter lines (1-3 words) with large font size
    short_candidates = [c for c in candidates if c['word_count'] <= 3]
    if short_candidates:
        # Among short candidates, pick the largest font size
        largest = max(short_candidates, key=lambda c: c['height'])
        return largest['text']
    
    # Fallback: pick the one with the largest font size
    largest = max(candidates, key=lambda c: c['height'])
    return largest['text']

def extract_vendor_from_text(text: str) -> Optional[str]:
    """
    Fallback vendor extraction: find the FIRST line that looks like a business name.
    Vendor names are typically the first prominent text line at the top.
    """
    lines = text.split('\n')
    # Look at first 10 lines (vendor is always at top)
    candidate_lines = lines[:10]
    
    for idx, raw_line in enumerate(candidate_lines):
        line = raw_line.strip()
        if not line:
            continue
        
        # Basic filters - require some text
        if len(line) < 3 or len(line) > 80:
            continue
        
        # Skip if it's just numbers or dates
        if re.match(r'^[\d\s\-\/\.]+$', line):
            continue
        
        # Skip if it's a dollar amount
        if re.search(r'[\$]\s*\d+\.\d{2}', line):
            continue
        
        # Skip if it looks like an address (has numbers and common address words)
        if re.search(r'\d+\s+(street|st|avenue|ave|road|rd|drive|dr|lane|ln|boulevard|blvd|way|circle|ct)', line, re.IGNORECASE):
            continue
        
        # Skip if it looks like a phone number
        if re.search(r'\d{3}[-.]?\d{3}[-.]?\d{4}', line):
            continue
        
        # Skip common receipt words
        line_lower = line.lower().strip()
        if line_lower in ['receipt', 'invoice', 'thank you', 'date', 'time', 'total', 'subtotal', 'tax', 'amount', 'fresh for everyone']:
            continue
        
        # Prefer shorter lines (1-3 words) as they're more likely to be vendor names
        words = line.split()
        if len(words) <= 3 and len(words) >= 1:
            # This looks like a business name - return it!
            return line
    
    # If no short business name found, fall back to longest line (but skip addresses)
    candidates = []
    for idx, raw_line in enumerate(candidate_lines):
        line = raw_line.strip()
        if not line or len(line) < 3 or len(line) > 100:
            continue
        if re.match(r'^[\d\s\-\/\.]+$', line):
            continue
        if re.search(r'[\$]\s*\d+\.\d{2}', line):
            continue
        if re.search(r'\d+\s+(street|st|avenue|ave|road|rd|drive|dr)', line, re.IGNORECASE):
            continue
        line_lower = line.lower().strip()
        if line_lower in ['receipt', 'invoice', 'thank you', 'date', 'time', 'total', 'subtotal', 'tax', 'amount']:
            continue
        candidates.append({'text': line, 'length': len(line)})
    
    if candidates:
        return max(candidates, key=lambda c: c['length'])['text']
    
    return None

def extract_invoice_number(text: str) -> Optional[str]:
    for pattern in [r'invoice[#:\s]+([A-Z0-9\-]+)', r'receipt[#:\s]+([A-Z0-9\-]+)', r'#[:\s]+([A-Z0-9\-]{4,})']:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def extract_items(text: str) -> List[Dict[str, str]]:
    items = []
    for line in text.split('\n'):
        line = line.strip()
        if not line or len(line) < 5:
            continue
        amount_match = re.search(r'[\$]?([\d,]+\.\d{2})', line)
        if amount_match:
            amount = amount_match.group(1).replace(',', '')
            description = line[:amount_match.start()].strip()
            if len(description) >= 3 and description.lower() not in ['total', 'subtotal', 'tax', 'discount']:
                items.append({'description': description, 'amount': amount})
    return items[:20]

def parse_receipt(text: str, word_data: Optional[List[Dict]] = None) -> Dict:
    """
    Parse receipt data from OCR text.
    word_data: Optional OCR bounding box data for better vendor extraction.
    """
    if not text or not text.strip():
        return {'amounts': {}, 'date': None, 'vendor': None, 'invoice_number': None, 'items': []}
    return {
        'amounts': extract_amounts(text),
        'date': extract_date(text),
        'vendor': extract_vendor(text, word_data),
        'invoice_number': extract_invoice_number(text),
        'items': extract_items(text)
    }
