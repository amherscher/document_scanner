import re
from typing import Dict, List, Optional

def extract_amounts(text: str) -> Dict[str, Optional[float]]:
    amounts = {'total': None, 'subtotal': None, 'tax': None, 'discount': None}
    patterns = {
        'total': [r'total[:\s]+[\$]?([\d,]+\.?\d*)', r'amount[:\s]+[\$]?([\d,]+\.?\d*)', r'[\$]([\d,]+\.?\d*)\s*(?:total|due)'],
        'subtotal': [r'subtotal[:\s]+[\$]?([\d,]+\.?\d*)'],
        'tax': [r'tax[:\s]+[\$]?([\d,]+\.?\d*)', r'vat[:\s]+[\$]?([\d,]+\.?\d*)'],
        'discount': [r'discount[:\s]+[\$]?([\d,]+\.?\d*)']
    }
    text_lower = text.lower()
    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                try:
                    amounts[key] = float(match.group(1).replace(',', ''))
                    break
                except:
                    continue
    if amounts['total'] is None:
        all_amounts = re.findall(r'[\$]?([\d,]+\.\d{2})', text)
        if all_amounts:
            try:
                amounts['total'] = max([float(a.replace(',', '')) for a in all_amounts])
            except:
                pass
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

def extract_vendor(text: str) -> Optional[str]:
    for line in text.split('\n')[:10]:
        line = line.strip()
        if not line or len(line) < 3 or len(line) > 50:
            continue
        skip_words = ['receipt', 'invoice', 'bill', 'thank', 'date', 'time']
        if any(word in line.lower() for word in skip_words):
            continue
        if re.search(r'[a-zA-Z]', line) and not re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line) and not re.search(r'[\$]\s*\d+\.\d{2}', line):
            return line
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

def parse_receipt(text: str) -> Dict:
    if not text or not text.strip():
        return {'amounts': {}, 'date': None, 'vendor': None, 'invoice_number': None, 'items': []}
    return {
        'amounts': extract_amounts(text),
        'date': extract_date(text),
        'vendor': extract_vendor(text),
        'invoice_number': extract_invoice_number(text),
        'items': extract_items(text)
    }
