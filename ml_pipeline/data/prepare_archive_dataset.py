"""
Script to prepare the archive (4) invoice dataset for training.
Processes JPG images and CSV metadata to create a training dataset.
"""
import argparse
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
from collections import Counter


# Category inference keywords
CATEGORY_KEYWORDS = {
    "Office Supplies": [
        "office", "supplies", "stationery", "paper", "pen", "printer", "ink", "cartridge",
        "folder", "binder", "stapler", "notebook", "desk", "chair"
    ],
    "Travel": [
        "hotel", "flight", "airline", "car rental", "taxi", "uber", "lyft", "lodging",
        "accommodation", "travel", "trip", "airport", "booking"
    ],
    "Meals & Entertainment": [
        "restaurant", "cafe", "dining", "food", "meal", "catering", "coffee", "lunch",
        "dinner", "entertainment", "bar", "pub", "grill"
    ],
    "Software & Subscriptions": [
        "software", "subscription", "saas", "cloud", "license", "app", "service",
        "platform", "subscription", "monthly", "annual", "renewal"
    ],
    "Hardware & Equipment": [
        "computer", "laptop", "desktop", "monitor", "keyboard", "mouse", "server",
        "equipment", "hardware", "device", "tablet", "phone"
    ],
    "Professional Services": [
        "consulting", "legal", "accounting", "audit", "advisory", "professional",
        "service", "attorney", "lawyer", "cpa", "consultant"
    ],
    "Utilities": [
        "electricity", "power", "gas", "water", "internet", "phone", "telephone",
        "utility", "utilities", "electric", "internet service"
    ],
    "Marketing & Advertising": [
        "marketing", "advertising", "ad", "campaign", "promotion", "social media",
        "seo", "ppc", "print", "brochure", "flyer"
    ],
    "Rent & Facilities": [
        "rent", "lease", "facility", "office space", "warehouse", "storage",
        "building", "property", "maintenance"
    ],
    "Insurance": [
        "insurance", "premium", "policy", "coverage", "liability", "health insurance"
    ],
    "Training & Education": [
        "training", "course", "education", "seminar", "workshop", "conference",
        "certification", "learning", "tuition"
    ],
    "Transportation": [
        "gas", "fuel", "parking", "toll", "transit", "bus", "train", "metro"
    ],
    "Legal & Compliance": [
        "legal", "compliance", "regulatory", "filing", "permit", "license fee"
    ]
}


def infer_category_from_text(text: str, items: List[Dict] = None) -> str:
    """
    Infer expense category from invoice text and items.
    
    Args:
        text: OCR text or invoice description
        items: List of invoice items with descriptions
        
    Returns:
        Inferred category name
    """
    if not text:
        text = ""
    
    # Combine all text
    all_text = text.lower()
    if items:
        for item in items:
            if isinstance(item, dict) and "description" in item:
                all_text += " " + str(item["description"]).lower()
    
    # Count matches for each category
    category_scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in all_text)
        if score > 0:
            category_scores[category] = score
    
    if category_scores:
        # Return category with highest score
        return max(category_scores.items(), key=lambda x: x[1])[0]
    
    return "Other"


def infer_category_from_seller(seller_name: str) -> Optional[str]:
    """Infer category from seller/vendor name."""
    if not seller_name:
        return None
    
    seller_lower = seller_name.lower()
    
    # Check for known vendor patterns
    if any(kw in seller_lower for kw in ["hotel", "inn", "lodge", "resort"]):
        return "Travel"
    if any(kw in seller_lower for kw in ["restaurant", "cafe", "dining", "grill"]):
        return "Meals & Entertainment"
    if any(kw in seller_lower for kw in ["office", "supply", "stationery"]):
        return "Office Supplies"
    if any(kw in seller_lower for kw in ["software", "tech", "cloud", "saas"]):
        return "Software & Subscriptions"
    if any(kw in seller_lower for kw in ["legal", "law", "attorney"]):
        return "Legal & Compliance"
    if any(kw in seller_lower for kw in ["consulting", "advisory", "services"]):
        return "Professional Services"
    
    return None


def parse_json_data(json_str: str) -> Optional[Dict]:
    """Parse JSON data from CSV, handling escaped quotes and control characters."""
    if not json_str or json_str.strip() == "":
        return None
    
    try:
        # Clean up the JSON string
        json_str = json_str.strip()
        # Remove leading/trailing quotes if present
        if json_str.startswith('"') and json_str.endswith('"'):
            json_str = json_str[1:-1]
        # Unescape quotes
        json_str = json_str.replace('""', '"')
        
        # Remove control characters (except newlines and tabs)
        import re
        json_str = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
        
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Silently skip invalid JSON - we'll use OCR text instead
        return None
    except Exception as e:
        # Silently skip other errors
        return None


def process_csv_file(csv_path: Path) -> Dict[str, Dict]:
    """
    Process a CSV file and extract invoice data.
    
    Returns:
        Dictionary mapping filename to invoice data
    """
    invoices = {}
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                filename = row.get("File Name", "").strip()
                if not filename:
                    continue
                
                # Parse JSON data
                json_data = None
                if "Json Data" in row and row["Json Data"]:
                    json_data = parse_json_data(row["Json Data"])
                
                # Get OCR text
                ocr_text = row.get("OCRed Text", "").strip()
                
                invoices[filename] = {
                    "json_data": json_data,
                    "ocr_text": ocr_text,
                    "filename": filename
                }
    except Exception as e:
        print(f"Error processing CSV {csv_path}: {e}")
    
    return invoices


def find_all_images(archive_dir: Path) -> List[Path]:
    """Find all JPG images in the archive."""
    images = []
    for jpg_path in archive_dir.rglob("*.jpg"):
        if jpg_path.is_file():
            images.append(jpg_path)
    return sorted(images)


def find_all_csvs(archive_dir: Path) -> List[Path]:
    """Find all CSV files in the archive."""
    csvs = []
    for csv_path in archive_dir.rglob("*.csv"):
        if csv_path.is_file():
            csvs.append(csv_path)
    return sorted(csvs)


def prepare_dataset(archive_dir: Path, output_csv: Path, extract_ocr: bool = False):
    """
    Prepare training dataset from archive.
    
    Args:
        archive_dir: Path to archive (4) directory
        output_csv: Output CSV path for training dataset
        extract_ocr: Whether to extract OCR from images (requires pytesseract)
    """
    print(f"Processing archive: {archive_dir}")
    
    # Find all images
    print("Finding images...")
    images = find_all_images(archive_dir)
    print(f"Found {len(images)} images")
    
    # Find all CSV files
    print("Finding CSV files...")
    csv_files = find_all_csvs(archive_dir)
    print(f"Found {len(csv_files)} CSV files")
    
    # Process CSV files
    all_invoice_data = {}
    for csv_file in csv_files:
        print(f"Processing CSV: {csv_file.name}")
        invoice_data = process_csv_file(csv_file)
        all_invoice_data.update(invoice_data)
        valid_count = sum(1 for v in invoice_data.values() if v.get("json_data") or v.get("ocr_text"))
        print(f"  Loaded {len(invoice_data)} invoices from CSV ({valid_count} with valid data)")
    
    print(f"Total invoices with metadata: {len(all_invoice_data)}")
    
    # Prepare dataset rows
    dataset_rows = []
    missing_metadata = 0
    missing_images = 0
    
    # Process images
    print("\nProcessing images and creating dataset...")
    for img_path in images:
        filename = img_path.name
        
        # Get invoice data from CSV if available
        invoice_data = all_invoice_data.get(filename, {})
        json_data = invoice_data.get("json_data")
        ocr_text = invoice_data.get("ocr_text", "")
        
        # If no OCR text in CSV and extract_ocr is True, extract from image
        if not ocr_text and extract_ocr:
            try:
                from ml_pipeline.utils.ocr_extract import extract_text_tesseract
                ocr_text = extract_text_tesseract(img_path)
            except Exception as e:
                print(f"  OCR extraction failed for {filename}: {e}")
        
        # Infer category
        category = None
        
        # Try to infer from seller name first
        if json_data and "invoice" in json_data:
            seller_name = json_data["invoice"].get("seller_name", "")
            category = infer_category_from_seller(seller_name)
        
        # If no category from seller, infer from text/items
        if not category:
            items = None
            if json_data and "items" in json_data:
                items = json_data["items"]
            category = infer_category_from_text(ocr_text, items)
        
        # Create dataset row
        # Use relative path from ml_pipeline/data/ directory
        try:
            # Try relative to archive_dir.parent (ml_pipeline/data/)
            rel_path = img_path.relative_to(archive_dir.parent)
        except ValueError:
            # Fallback: use relative to archive_dir
            rel_path = img_path.relative_to(archive_dir)
            # Prepend archive directory name
            rel_path = archive_dir.name / rel_path
        
        row = {
            "image_path": str(rel_path),
            "category": category,
            "text": ocr_text if ocr_text else "",  # Ensure non-empty string
            "filename": filename
        }
        
        # Add JSON fields if available
        if json_data and "invoice" in json_data:
            inv = json_data["invoice"]
            row["seller_name"] = inv.get("seller_name", "")
            row["client_name"] = inv.get("client_name", "")
            row["invoice_date"] = inv.get("invoice_date", "")
            row["invoice_number"] = inv.get("invoice_number", "")
        
        dataset_rows.append(row)
        
        if not json_data and not ocr_text:
            missing_metadata += 1
        if not img_path.exists():
            missing_images += 1
    
    # Count rows with/without text
    rows_with_text = sum(1 for row in dataset_rows if row.get("text", "").strip())
    rows_without_text = len(dataset_rows) - rows_with_text
    
    print(f"\nDataset preparation complete!")
    print(f"  Total rows: {len(dataset_rows)}")
    print(f"  Rows with text: {rows_with_text}")
    print(f"  Rows without text: {rows_without_text}")
    print(f"  Missing metadata: {missing_metadata}")
    print(f"  Missing images: {missing_images}")
    
    if rows_without_text > 0 and not extract_ocr:
        print(f"\n⚠ WARNING: {rows_without_text} rows have no text!")
        print(f"  For text/hybrid models, consider:")
        print(f"  1. Run with --extract_ocr flag to extract text from images")
        print(f"  2. Use image-only model (--model_type image)")
        print(f"  3. Filter dataset to only rows with text")
    
    # Count categories
    categories = Counter(row["category"] for row in dataset_rows)
    print(f"\nCategory distribution:")
    for cat, count in categories.most_common():
        print(f"  {cat}: {count}")
    
    # Write CSV
    if dataset_rows:
        fieldnames = ["image_path", "category", "text", "filename", 
                     "seller_name", "client_name", "invoice_date", "invoice_number"]
        
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(dataset_rows)
        
        print(f"\nDataset saved to: {output_csv}")
        print(f"  Rows: {len(dataset_rows)}")
    else:
        print("No data to save!")


def main():
    parser = argparse.ArgumentParser(description="Prepare archive dataset for training")
    parser.add_argument(
        "--archive_dir",
        type=str,
        default="ml_pipeline/data/archive (4)",
        help="Path to archive (4) directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="ml_pipeline/data/invoice_dataset.csv",
        help="Output CSV path"
    )
    parser.add_argument(
        "--extract_ocr",
        action="store_true",
        help="Extract OCR text from images (slower, requires pytesseract)"
    )
    
    args = parser.parse_args()
    
    archive_dir = Path(args.archive_dir)
    if not archive_dir.exists():
        # Try relative to current directory
        archive_dir = Path(__file__).parent / "archive (4)"
    
    if not archive_dir.exists():
        print(f"Error: Archive directory not found: {archive_dir}")
        return
    
    output_csv = Path(args.output)
    
    prepare_dataset(archive_dir, output_csv, args.extract_ocr)


if __name__ == "__main__":
    main()

