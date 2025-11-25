# Archive Dataset Preparation

## Overview

The `archive (4)` directory contains **7,464 invoice images** organized in batch subdirectories. This script processes these images and prepares them for training.

## Quick Start

### Basic Processing (Fast - Uses CSV metadata only)

```bash
python ml_pipeline/data/prepare_archive_dataset.py \
    --archive_dir "ml_pipeline/data/archive (4)" \
    --output "ml_pipeline/data/invoice_dataset.csv"
```

This will:
- Process all 7,464 images
- Use OCR text from CSV files where available (489 invoices have CSV metadata)
- Infer categories from invoice content
- Create a training dataset CSV

### Full OCR Extraction (Slower - Extracts text from all images)

```bash
python ml_pipeline/data/prepare_archive_dataset.py \
    --archive_dir "ml_pipeline/data/archive (4)" \
    --output "ml_pipeline/data/invoice_dataset_full.csv" \
    --extract_ocr
```

This will:
- Extract OCR text from ALL images (requires pytesseract)
- Take longer but provides better categorization
- More accurate category inference

## Dataset Structure

The output CSV contains:
- `image_path`: Relative path to the image
- `category`: Inferred expense category
- `text`: OCR text from invoice
- `filename`: Original filename
- `seller_name`, `client_name`, `invoice_date`, `invoice_number`: If available from CSV

## Category Inference

Categories are inferred from:
1. **Seller/Vendor names** (e.g., "Hotel XYZ" → Travel)
2. **Invoice text content** (keywords matching)
3. **Item descriptions** (from JSON data)

If no match is found, category defaults to "Other".

## Current Status

After basic processing:
- **Total invoices**: 7,464
- **With CSV metadata**: 489
- **Category distribution**:
  - Other: ~6,710 (needs OCR extraction for better categorization)
  - Marketing & Advertising: ~234
  - Meals & Entertainment: ~174
  - Office Supplies: ~158
  - Hardware & Equipment: ~110
  - Others: smaller counts

## Improving Categorization

To get better categorization:

1. **Extract OCR from all images**:
   ```bash
   python ml_pipeline/data/prepare_archive_dataset.py \
       --archive_dir "ml_pipeline/data/archive (4)" \
       --output "ml_pipeline/data/invoice_dataset.csv" \
       --extract_ocr
   ```

2. **Manually review and correct** categories in the CSV

3. **Add more keywords** to `CATEGORY_KEYWORDS` in the script

## Training with the Dataset

Once the dataset is prepared:

```bash
# For text-based model (recommended)
python ml_pipeline/train.py \
    --data_path ml_pipeline/data/invoice_dataset.csv \
    --model_type text \
    --epochs 10 \
    --batch_size 16 \
    --output_dir ml_pipeline/checkpoints

# For image-based model
python ml_pipeline/train.py \
    --data_path ml_pipeline/data/invoice_dataset.csv \
    --model_type image \
    --image_dir ml_pipeline/data/archive\ \(4\) \
    --epochs 10 \
    --batch_size 8 \
    --output_dir ml_pipeline/checkpoints

# For hybrid model (best accuracy)
python ml_pipeline/train.py \
    --data_path ml_pipeline/data/invoice_dataset.csv \
    --model_type hybrid \
    --image_dir ml_pipeline/data/archive\ \(4\) \
    --epochs 10 \
    --batch_size 8 \
    --output_dir ml_pipeline/checkpoints
```

## Notes

- The script handles JSON parsing errors gracefully
- Images without metadata will still be included (with inferred categories)
- OCR extraction is optional but recommended for better results
- Processing 7,464 images with OCR may take 30-60 minutes depending on hardware

