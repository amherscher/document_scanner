#!/usr/bin/env python3
"""Classify all scanned invoices in the scans directory"""

import sys
from pathlib import Path
import requests
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from ml_pipeline.inference import InvoiceCategorizer
    from ml_pipeline.utils.ocr_extract import extract_text_from_invoice, extract_text_with_details_from_invoice
    from ml_pipeline.utils.receipt_parser import parse_receipt
    from ml_pipeline.utils.expense_tracker import save_expense
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Error: ML pipeline not available. Install dependencies: pip install -r requirements.txt")
    sys.exit(1)

def classify_file(file_path: Path, categorizer, workdir: Path):
    """Classify a single file"""
    print(f"\nProcessing: {file_path.name}")
    
    # Find matching files (jpg/pdf pair)
    base_name = file_path.stem
    jpg_path = workdir / f"{base_name}.jpg"
    pdf_path = workdir / f"{base_name}.pdf"
    
    if not jpg_path.exists():
        for ext in [".jpg", ".jpeg", ".png"]:
            alt_path = workdir / f"{base_name}{ext}"
            if alt_path.exists():
                jpg_path = alt_path
                break
    
    if not jpg_path.exists():
        print(f"  ⚠️  No image file found for {file_path.name}")
        return None
    
    # Extract text with detailed OCR data for better vendor extraction
    if extract_text_with_details_from_invoice:
        text, word_data = extract_text_with_details_from_invoice(jpg_path, pdf_path if pdf_path.exists() else None)
    else:
        text = extract_text_from_invoice(jpg_path, pdf_path if pdf_path.exists() else None) if extract_text_from_invoice else ""
        word_data = []
    
    if not text:
        print(f"  ⚠️  No text extracted from {file_path.name}")
        return None
    
    # Classify
    if categorizer.model_type == "image":
        category, probs = categorizer.predict_image(str(jpg_path), return_probs=True)
    elif categorizer.model_type == "hybrid":
        category, probs = categorizer.predict_hybrid(text, str(jpg_path), return_probs=True) if text else categorizer.predict_image(str(jpg_path), return_probs=True)
    else:
        category, probs = categorizer.predict_text(text, return_probs=True)
    
    # Parse receipt (pass word_data for better vendor extraction)
    receipt_data = parse_receipt(text, word_data) if text and parse_receipt else {}
    
    classification = {
        "category": category,
        "confidence": round(probs[category], 4),
        "text_extracted": len(text) > 0,
        "text_length": len(text),
        "receipt_data": receipt_data
    }
    
    # Save to expense tracker
    if save_expense:
        save_expense(workdir, jpg_path.name, classification, receipt_data)
        print(f"  ✓ Classified as: {category} ({probs[category]:.1%} confidence)")
        if receipt_data.get('amounts', {}).get('total'):
            print(f"  ✓ Amount: ${receipt_data['amounts']['total']:.2f}")
        if receipt_data.get('vendor'):
            print(f"  ✓ Vendor: {receipt_data['vendor']}")
        
        # Move classified files to subdirectory to avoid reclassification
        classified_dir = workdir / "classified"
        classified_dir.mkdir(exist_ok=True)
        
        try:
            import shutil
            # Move JPG
            if jpg_path.exists():
                dest_jpg = classified_dir / jpg_path.name
                shutil.move(str(jpg_path), str(dest_jpg))
                print(f"  ✓ Moved to classified/{jpg_path.name}")
            
            # Move PDF if it exists
            if pdf_path and pdf_path.exists():
                dest_pdf = classified_dir / pdf_path.name
                shutil.move(str(pdf_path), str(dest_pdf))
        except Exception as e:
            print(f"  ⚠️  Warning: Could not move files: {e}")
    else:
        print(f"  ✓ Classified as: {category} ({probs[category]:.1%} confidence)")
    
    return classification

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Classify all scanned invoices")
    parser.add_argument("--scans_dir", default="scans", help="Directory containing scans")
    parser.add_argument("--model_path", default="checkpoints/best_model.pt", help="Path to model")
    args = parser.parse_args()
    
    scans_dir = Path(args.scans_dir)
    if not scans_dir.exists():
        print(f"Error: Scans directory not found: {scans_dir}")
        sys.exit(1)
    
    model_path = Path(args.model_path)
    if not model_path.exists():
        print(f"Error: Model not found: {model_path}")
        sys.exit(1)
    
    print(f"Loading model from: {model_path}")
    categorizer = InvoiceCategorizer(str(model_path))
    print(f"Model loaded: {categorizer.model_type} with {len(categorizer.categories)} categories")
    
    # Find all image files (skip files in classified/ subdirectory)
    classified_dir = scans_dir / "classified"
    image_files = [f for f in (list(scans_dir.glob("*.jpg")) + list(scans_dir.glob("*.jpeg")) + list(scans_dir.glob("*.png"))) 
                  if classified_dir not in f.parents]
    pdf_files = [f for f in list(scans_dir.glob("*.pdf")) 
                if classified_dir not in f.parents]
    
    # Process image files (skip if PDF exists with same name)
    files_to_process = []
    for img_file in image_files:
        base_name = img_file.stem
        pdf_file = scans_dir / f"{base_name}.pdf"
        if not pdf_file.exists():
            files_to_process.append(img_file)
    
    # Also process PDFs that don't have matching images
    for pdf_file in pdf_files:
        base_name = pdf_file.stem
        img_file = scans_dir / f"{base_name}.jpg"
        if not img_file.exists():
            files_to_process.append(pdf_file)
    
    if not files_to_process:
        print(f"No files to classify in {scans_dir}")
        return
    
    print(f"\nFound {len(files_to_process)} files to classify")
    
    classified = 0
    failed = 0
    
    for file_path in files_to_process:
        try:
            result = classify_file(file_path, categorizer, scans_dir)
            if result:
                classified += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1
    
    print(f"\n✅ Classification complete!")
    print(f"   Classified: {classified}")
    print(f"   Failed: {failed}")
    print(f"\nExpense spreadsheet: {scans_dir / 'expenses.csv'}")

if __name__ == "__main__":
    main()

