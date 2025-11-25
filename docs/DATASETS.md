# Invoice Expense Categorization Datasets

This document provides information about datasets suitable for training invoice expense categorization models.

## Recommended Datasets

### 1. FATURA Dataset

**Description:** A comprehensive dataset with 10,000 invoice images across 50 distinct layouts.

**Paper:** [FATURA: A Large-Scale Invoice Dataset](https://arxiv.org/abs/2311.11856)

**Key Features:**
- 10,000 invoice images
- 50 different invoice layouts
- Suitable for both OCR and image classification tasks

**How to Use:**
1. Download the dataset from the paper's repository
2. Extract invoice images
3. Manually label each invoice with expense categories
4. Create a CSV file with columns: `image_path`, `category`, `text` (if you extract text via OCR)

**Note:** This dataset may not include expense category labels, so you'll need to label them manually based on invoice content.

### 2. CloudScan Dataset

**Description:** Dataset associated with the CloudScan system for invoice analysis.

**Paper:** [CloudScan: A System for Invoice Analysis](https://arxiv.org/abs/1708.07403)

**Key Features:**
- Invoice images with key field annotations
- Suitable for invoice understanding tasks

**How to Use:**
1. Access the dataset through the paper's repository
2. Extract invoice images and annotations
3. Map invoice content to expense categories
4. Format as CSV for training

### 3. Kaggle Datasets

**Search Terms:**
- "invoice"
- "receipt"
- "expense"
- "document classification"
- "invoice OCR"

**Popular Options:**
- Search Kaggle: https://www.kaggle.com/datasets
- Look for datasets with invoice images or text
- May require manual labeling for expense categories

### 4. Create Your Own Dataset

**Steps:**
1. Collect invoices from your organization
2. Extract text using OCR (Tesseract, EasyOCR, etc.)
3. Label each invoice with expense categories
4. Organize into CSV format

**CSV Format:**
```csv
text,category,image_path,amount,date
"Office supplies invoice...",Office Supplies,images/inv001.jpg,125.50,2024-01-15
"Hotel booking invoice...",Travel,images/inv002.jpg,450.00,2024-01-17
```

## Expense Categories

Common expense categories for invoices:

1. **Office Supplies** - Pens, paper, notebooks, printer supplies
2. **Travel** - Hotels, flights, car rentals, transportation
3. **Meals & Entertainment** - Restaurant bills, catering, client dinners
4. **Software & Subscriptions** - Cloud services, software licenses, SaaS
5. **Hardware & Equipment** - Computers, furniture, office equipment
6. **Professional Services** - Legal, accounting, consulting services
7. **Utilities** - Electricity, internet, phone, water
8. **Marketing & Advertising** - Ad campaigns, promotional materials
9. **Rent & Facilities** - Office rent, facility maintenance
10. **Insurance** - Business insurance, liability insurance
11. **Training & Education** - Courses, conferences, certifications
12. **Transportation** - Gas, parking, public transit
13. **Legal & Compliance** - Legal fees, compliance services
14. **Other** - Miscellaneous expenses

## Data Preparation Tips

### For Text Models:
- Extract text from invoices using OCR
- Clean and normalize text
- Ensure text column contains full invoice content
- Minimum 50-100 samples per category recommended

### For Image Models:
- Use high-quality invoice images (at least 224x224 pixels)
- Ensure consistent image format (JPG, PNG)
- Organize images in a single directory
- Reference images in CSV with relative or absolute paths

### For Hybrid Models:
- Provide both text and image for each invoice
- Text can be extracted from images using OCR
- Ensure image_path column points to valid images

## Sample Dataset Creation

Use the provided script to create a sample dataset for testing:

```bash
python ml_pipeline/data/download_datasets.py --create_sample --sample_size 200
```

This creates `data/sample_invoices.csv` with synthetic invoice data.

## Data Quality Guidelines

1. **Balance:** Try to have roughly equal samples per category (or at least 50+ per category)
2. **Diversity:** Include invoices from different vendors, formats, and time periods
3. **Accuracy:** Double-check category labels for consistency
4. **Completeness:** Ensure all required columns are present and non-null
5. **Validation:** Reserve 20% of data for validation/testing

## Legal Considerations

- Ensure you have permission to use invoice data
- Anonymize sensitive information if needed
- Comply with data privacy regulations (GDPR, etc.)
- Consider using synthetic or publicly available datasets for training

## Next Steps

1. Choose or create a dataset
2. Format data as CSV with required columns
3. Run training: `python ml_pipeline/train.py --data_path your_data.csv`
4. Evaluate model performance
5. Iterate and improve with more data

