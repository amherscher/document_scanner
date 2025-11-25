"""
Script to download and prepare invoice expense categorization datasets.
"""
import argparse
import json
import os
import pandas as pd
from pathlib import Path
import requests
import zipfile
from tqdm import tqdm


# Common expense categories for invoices
EXPENSE_CATEGORIES = [
    "Office Supplies",
    "Travel",
    "Meals & Entertainment",
    "Software & Subscriptions",
    "Hardware & Equipment",
    "Professional Services",
    "Utilities",
    "Marketing & Advertising",
    "Rent & Facilities",
    "Insurance",
    "Training & Education",
    "Transportation",
    "Legal & Compliance",
    "Other"
]


def download_file(url: str, output_path: Path, chunk_size: int = 8192):
    """Download a file with progress bar."""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(output_path, 'wb') as f, tqdm(
        desc=output_path.name,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))


def create_sample_dataset(output_path: Path, num_samples: int = 100):
    """
    Create a sample dataset structure for demonstration.
    In production, you would use real invoice datasets.
    """
    print(f"Creating sample dataset with {num_samples} samples...")
    
    # Sample invoice texts with categories
    sample_data = []
    
    invoice_templates = [
        ("Office Supplies", [
            "Invoice for office supplies including pens, paper, and notebooks",
            "Purchase of printer paper, ink cartridges, and folders",
            "Office stationery order: staplers, binders, and markers",
        ]),
        ("Travel", [
            "Hotel accommodation invoice for business trip",
            "Flight ticket purchase for conference attendance",
            "Car rental invoice for business travel",
        ]),
        ("Meals & Entertainment", [
            "Restaurant bill for client dinner meeting",
            "Catering services for company event",
            "Coffee and refreshments for team meeting",
        ]),
        ("Software & Subscriptions", [
            "Monthly subscription for cloud storage service",
            "Software license renewal for accounting software",
            "Annual subscription for project management tool",
        ]),
        ("Hardware & Equipment", [
            "Purchase of new laptop computer",
            "Office furniture: desk and chair",
            "Network equipment: router and switches",
        ]),
        ("Professional Services", [
            "Legal consultation services invoice",
            "Accounting services for quarterly review",
            "IT consulting services for system upgrade",
        ]),
        ("Utilities", [
            "Monthly electricity bill",
            "Internet and phone service invoice",
            "Water and sewer utility bill",
        ]),
        ("Marketing & Advertising", [
            "Social media advertising campaign invoice",
            "Print advertising in local newspaper",
            "Website design and development services",
        ]),
    ]
    
    import random
    for _ in range(num_samples):
        category, templates = random.choice(invoice_templates)
        text = random.choice(templates)
        sample_data.append({
            "text": text,
            "category": category,
            "amount": round(random.uniform(50, 5000), 2),
            "date": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        })
    
    # Save as CSV
    df = pd.DataFrame(sample_data)
    df.to_csv(output_path, index=False)
    print(f"Sample dataset saved to {output_path}")
    print(f"Categories: {df['category'].value_counts().to_dict()}")


def prepare_fatura_dataset_info(output_dir: Path):
    """
    Create information file for FATURA dataset.
    FATURA is a large invoice dataset with 10,000 invoices.
    Paper: https://arxiv.org/abs/2311.11856
    """
    info = {
        "name": "FATURA Dataset",
        "description": "Comprehensive invoice dataset with 10,000 invoices and 50 distinct layouts",
        "paper": "https://arxiv.org/abs/2311.11856",
        "download_instructions": [
            "1. Visit the paper link to find the dataset download page",
            "2. Download the dataset files",
            "3. Extract to a directory",
            "4. Organize images and annotations",
            "5. Create a CSV file mapping images to expense categories"
        ],
        "expected_structure": {
            "images/": "Directory containing invoice images",
            "annotations/": "Directory containing annotation files",
            "labels.csv": "CSV file with columns: image_path, category, text (optional)"
        },
        "note": "You may need to manually label expense categories based on invoice content"
    }
    
    info_path = output_dir / "fatura_dataset_info.json"
    with open(info_path, 'w') as f:
        json.dump(info, f, indent=2)
    print(f"FATURA dataset info saved to {info_path}")


def prepare_kaggle_datasets_info(output_dir: Path):
    """
    Create information about Kaggle datasets that might be useful.
    """
    datasets = [
        {
            "name": "Invoice Dataset",
            "description": "Search Kaggle for invoice-related datasets",
            "search_terms": ["invoice", "receipt", "expense", "document classification"],
            "url": "https://www.kaggle.com/datasets",
            "note": "You may need to create expense category labels manually"
        },
        {
            "name": "Receipt Dataset",
            "description": "Receipt and invoice datasets often overlap",
            "search_terms": ["receipt", "invoice", "OCR"],
            "url": "https://www.kaggle.com/datasets",
        }
    ]
    
    info_path = output_dir / "kaggle_datasets_info.json"
    with open(info_path, 'w') as f:
        json.dump(datasets, f, indent=2)
    print(f"Kaggle datasets info saved to {info_path}")


def main():
    parser = argparse.ArgumentParser(description="Download and prepare invoice datasets")
    parser.add_argument("--output_dir", type=str, default="./data", help="Output directory")
    parser.add_argument("--create_sample", action="store_true", help="Create a sample dataset")
    parser.add_argument("--sample_size", type=int, default=100, help="Number of samples in sample dataset")
    parser.add_argument("--download_fatura", action="store_true", help="Download FATURA dataset (if available)")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Invoice Expense Categorization Dataset Preparation")
    print("=" * 60)
    
    # Create sample dataset
    if args.create_sample:
        sample_path = output_dir / "sample_invoices.csv"
        create_sample_dataset(sample_path, args.sample_size)
    
    # Create dataset information files
    prepare_fatura_dataset_info(output_dir)
    prepare_kaggle_datasets_info(output_dir)
    
    # Create categories file
    categories_path = output_dir / "expense_categories.json"
    with open(categories_path, 'w') as f:
        json.dump(EXPENSE_CATEGORIES, f, indent=2)
    print(f"Expense categories saved to {categories_path}")
    
    print("\n" + "=" * 60)
    print("Dataset Preparation Complete!")
    print("\nNext steps:")
    print("1. Download real invoice datasets (FATURA, Kaggle, or your own)")
    print("2. Organize data into CSV format with 'category' column")
    print("3. For image models, ensure 'image_path' column points to images")
    print("4. For text models, ensure 'text' column contains invoice text")
    print("5. Run training script: python train.py --data_path <your_dataset.csv>")


if __name__ == "__main__":
    main()

