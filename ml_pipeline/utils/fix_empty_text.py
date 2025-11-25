"""
Quick script to check and report issues with the dataset.
"""
import csv
from pathlib import Path
from collections import Counter


def analyze_dataset(csv_path: Path):
    """Analyze dataset and report issues."""
    print(f"Analyzing dataset: {csv_path}")
    
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    print(f"\nTotal rows: {len(rows)}")
    
    # Check for required columns
    if rows:
        required_cols = ['category', 'image_path']
        missing_cols = [col for col in required_cols if col not in rows[0]]
        if missing_cols:
            print(f"❌ Missing required columns: {missing_cols}")
        else:
            print(f"✓ Required columns present")
    
    # Check text column
    rows_with_text = sum(1 for row in rows if row.get('text', '').strip())
    rows_without_text = len(rows) - rows_with_text
    print(f"\nText column:")
    print(f"  Rows with text: {rows_with_text}")
    print(f"  Rows without text: {rows_without_text}")
    
    if rows_without_text > len(rows) * 0.5:
        print(f"\n⚠ WARNING: More than 50% of rows have no text!")
        print(f"  This will cause issues for text-based models.")
        print(f"  Solutions:")
        print(f"    1. Run prepare_archive_dataset.py with --extract_ocr")
        print(f"    2. Use --model_type image instead of text")
        print(f"    3. Filter dataset to only rows with text")
    
    # Check categories
    categories = Counter(row.get('category', '') for row in rows)
    print(f"\nCategories: {len(categories)} unique")
    for cat, count in categories.most_common(10):
        print(f"  {cat}: {count}")
    
    # Check image paths
    if rows:
        sample_path = rows[0].get('image_path', '')
        print(f"\nSample image_path: {sample_path}")
        print(f"  (Check if paths are correct relative to image_dir parameter)")
    
    # Check for empty categories
    empty_cats = sum(1 for row in rows if not row.get('category', '').strip())
    if empty_cats > 0:
        print(f"\n⚠ WARNING: {empty_cats} rows have no category!")
    
    print(f"\n✓ Analysis complete")


if __name__ == "__main__":
    import sys
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ml_pipeline/data/test_dataset.csv")
    analyze_dataset(csv_path)

