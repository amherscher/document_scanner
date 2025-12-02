#!/usr/bin/env python3
"""Simple CLI tool to classify invoice files"""

import sys
from pathlib import Path
import argparse
import shutil

# Add project root to path (parent of scripts directory)
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    from ml_pipeline.inference import InvoiceCategorizer
    from ml_pipeline.utils.ocr_extract import extract_text_from_invoice, extract_text_with_details_from_invoice
    from ml_pipeline.utils.receipt_parser import parse_receipt
    from ml_pipeline.utils.expense_tracker import save_expense
    ML_AVAILABLE = True
except ImportError as e:
    print(f"Error: ML pipeline not available: {e}")
    print("Install dependencies: pip install -r requirements.txt")
    sys.exit(1)

def classify_file(jpg_path, pdf_path, categorizer, workdir):
    """Classify a single file"""
    print(f"\n📄 {jpg_path.name if jpg_path else pdf_path.name}")
    
    if not jpg_path and not pdf_path:
        print("  ⚠️  No file found")
        return None
    
    text = ""
    word_data = []
    if extract_text_from_invoice:
        # Use enhanced OCR with bounding box data for better vendor extraction
        effective_pdf = pdf_path if (pdf_path and pdf_path.exists()) else None
        if jpg_path or effective_pdf:
            # Try to get detailed OCR data (for better vendor extraction)
            if jpg_path and jpg_path.exists():
                text, word_data = extract_text_with_details_from_invoice(jpg_path, effective_pdf)
            else:
                # Fallback to simple extraction for PDF-only
                text = extract_text_from_invoice(effective_pdf, None)
    
    if not text and not jpg_path:
        print("  ⚠️  Cannot classify PDF without image")
        return None
    
    # Classify
    if categorizer.model_type == "image":
        if not jpg_path:
            print("  ⚠️  Image model requires image file")
            return None
        category, probs = categorizer.predict_image(str(jpg_path), return_probs=True)
    elif categorizer.model_type == "hybrid":
        if jpg_path:
            category, probs = categorizer.predict_hybrid(text, str(jpg_path), return_probs=True) if text else categorizer.predict_image(str(jpg_path), return_probs=True)
        else:
            print("  ⚠️  Hybrid model requires image file")
            return None
    else:
        if not text:
            print("  ⚠️  Text model requires extracted text")
            return None
        category, probs = categorizer.predict_text(text, return_probs=True)
    
    # Parse receipt (pass word_data for better vendor extraction)
    receipt_data = parse_receipt(text, word_data) if text and parse_receipt else {}
    
    # Display results
    confidence = probs[category]
    amount = receipt_data.get('amounts', {}).get('total')
    
    # Show category and amount prominently
    if amount:
        print(f"  ✓ Category: {category} | Amount: ${amount:.2f} ({confidence:.1%} confidence)")
    else:
        print(f"  ✓ Category: {category} ({confidence:.1%} confidence)")
        if not text:
            print(f"  ⚠️  Amount not found: No text extracted (install tesseract for OCR)")
        else:
            print(f"  ⚠️  Amount not found in extracted text ({len(text)} chars)")
    
    if receipt_data.get('vendor'):
        print(f"  ✓ Vendor: {receipt_data['vendor']}")
    if receipt_data.get('date'):
        print(f"  ✓ Date: {receipt_data['date']}")
    
    # Save to expense tracker
    if save_expense and jpg_path:
        save_expense(workdir, jpg_path.name, {
            "category": category,
            "confidence": confidence,
            "receipt_data": receipt_data
        }, receipt_data)
        print(f"  ✓ Saved to expenses.csv")
        
        # Move classified files to subdirectory to avoid reclassification
        classified_dir = workdir / "classified"
        classified_dir.mkdir(exist_ok=True)
        
        try:
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
            print(f"  ⚠️  Warning: Could not move files to classified/: {e}")
    
    return {
        "category": category,
        "confidence": confidence,
        "receipt_data": receipt_data
    }

def main():
    parser = argparse.ArgumentParser(description="Classify invoice files")
    parser.add_argument("--scans_dir", default="scans", help="Directory containing scans")
    parser.add_argument("--model", default="checkpoints/best_model.pt", help="Path to model")
    parser.add_argument("--file", help="Classify a specific file")
    parser.add_argument("--all", action="store_true", help="Classify all files")
    args = parser.parse_args()
    
    scans_dir = Path(args.scans_dir)
    if not scans_dir.exists():
        print(f"Error: Scans directory not found: {scans_dir}")
        sys.exit(1)
    
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"Error: Model not found: {model_path}")
        sys.exit(1)
    
    print(f"Loading model: {model_path}")
    categorizer = InvoiceCategorizer(str(model_path))
    print(f"Model: {categorizer.model_type} with {len(categorizer.categories)} categories\n")
    
    if args.file:
        # Classify single file
        file_path = scans_dir / args.file
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        
        base_name = file_path.stem
        jpg_path = scans_dir / f"{base_name}.jpg"
        pdf_path = scans_dir / f"{base_name}.pdf"
        
        if file_path.suffix == ".pdf":
            jpg_path = None
            pdf_path = file_path
        else:
            pdf_path = pdf_path if pdf_path.exists() else None
        
        if not jpg_path.exists() and not pdf_path:
            print(f"Error: No valid file found for {args.file}")
            sys.exit(1)
        
        classify_file(jpg_path if jpg_path.exists() else None, pdf_path, categorizer, scans_dir)
        
    elif args.all:
        # Classify all files (skip files in classified/ subdirectory)
        classified_dir = scans_dir / "classified"
        image_files = [f for f in (list(scans_dir.glob("*.jpg")) + list(scans_dir.glob("*.jpeg")) + list(scans_dir.glob("*.png"))) 
                      if classified_dir not in f.parents]
        pdf_files = [f for f in list(scans_dir.glob("*.pdf")) 
                    if classified_dir not in f.parents]
        
        files_to_process = []
        for img_file in image_files:
            base_name = img_file.stem
            pdf_file = scans_dir / f"{base_name}.pdf"
            files_to_process.append((img_file, pdf_file if pdf_file.exists() else None))
        
        for pdf_file in pdf_files:
            base_name = pdf_file.stem
            img_file = scans_dir / f"{base_name}.jpg"
            if not img_file.exists():
                files_to_process.append((None, pdf_file))
        
        if not files_to_process:
            print(f"No files to classify in {scans_dir}")
            return
        
        print(f"Found {len(files_to_process)} files to classify\n")
        
        classified = 0
        failed = 0
        
        for jpg_path, pdf_path in files_to_process:
            try:
                result = classify_file(jpg_path, pdf_path, categorizer, scans_dir)
                if result:
                    classified += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  ✗ Error: {e}")
                failed += 1
        
        print(f"\n✅ Complete!")
        print(f"   Classified: {classified}")
        print(f"   Failed: {failed}")
        print(f"\nExpense spreadsheet: {scans_dir / 'expenses.csv'}")
        
    else:
        # List files
        image_files = list(scans_dir.glob("*.jpg")) + list(scans_dir.glob("*.jpeg")) + list(scans_dir.glob("*.png"))
        pdf_files = list(scans_dir.glob("*.pdf"))
        
        all_files = []
        for img_file in image_files:
            all_files.append(img_file.name)
        for pdf_file in pdf_files:
            if not (scans_dir / f"{pdf_file.stem}.jpg").exists():
                all_files.append(pdf_file.name)
        
        if not all_files:
            print(f"No files found in {scans_dir}")
            return
        
        print(f"Files in {scans_dir}:")
        for f in sorted(all_files):
            print(f"  - {f}")
        print(f"\nTo classify all: python3 scripts/classify.py --all --scans_dir {scans_dir}")
        print(f"To classify one: python3 scripts/classify.py --file <filename> --scans_dir {scans_dir}")

if __name__ == "__main__":
    main()

