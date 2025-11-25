# Invoice Expense Categorization ML Pipeline

A PyTorch-based machine learning pipeline for automatically categorizing invoices into expense categories.

## Features

- **Multiple Model Types:**
  - Text-based classification (using transformer models)
  - Image-based classification (using CNN)
  - Hybrid classification (combining text and image features)

- **Flexible Data Formats:**
  - CSV or JSON input
  - Support for text-only, image-only, or hybrid data

- **Complete Pipeline:**
  - Data preprocessing
  - Model training with validation
  - Inference for new invoices
  - Model checkpointing and evaluation

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install PyTorch (if not already installed):
```bash
# For CPU
pip install torch torchvision transformers

# For GPU (CUDA)
pip install torch torchvision transformers --index-url https://download.pytorch.org/whl/cu118
```

## Datasets

### Recommended Datasets

1. **FATURA Dataset**
   - 10,000 invoices with 50 distinct layouts
   - Paper: https://arxiv.org/abs/2311.11856
   - You'll need to manually label expense categories

2. **CloudScan Dataset**
   - Invoice analysis dataset
   - Paper: https://arxiv.org/abs/1708.07403

3. **Kaggle Datasets**
   - Search for "invoice", "receipt", or "expense" datasets
   - May require manual labeling for expense categories

4. **Your Own Data**
   - Collect invoices and label them with expense categories
   - Format as CSV with columns: `text`, `category`, `image_path` (optional)

### Preparing Your Dataset

1. **Create a sample dataset** (for testing):
```bash
python ml_pipeline/data/download_datasets.py --create_sample --sample_size 200
```

2. **Format your dataset** as CSV:
```csv
text,category,image_path
"Office supplies invoice...",Office Supplies,images/invoice1.jpg
"Hotel booking invoice...",Travel,images/invoice2.jpg
```

Required columns:
- `category`: The expense category (e.g., "Office Supplies", "Travel")
- `text`: Invoice text (for text/hybrid models)
- `image_path`: Path to invoice image (for image/hybrid models)

## Usage

### Training

Train a text-based model:
```bash
python ml_pipeline/train.py \
    --data_path data/sample_invoices.csv \
    --model_type text \
    --output_dir checkpoints \
    --epochs 10 \
    --batch_size 16
```

Train an image-based model:
```bash
python ml_pipeline/train.py \
    --data_path data/invoices.csv \
    --model_type image \
    --image_dir data/images \
    --output_dir checkpoints \
    --epochs 10 \
    --batch_size 8
```

Train a hybrid model:
```bash
python ml_pipeline/train.py \
    --data_path data/invoices.csv \
    --model_type hybrid \
    --image_dir data/images \
    --output_dir checkpoints \
    --epochs 10 \
    --batch_size 8
```

### Inference

Categorize from text:
```bash
python ml_pipeline/inference.py \
    --checkpoint checkpoints/best_model.pt \
    --text "Invoice for office supplies including pens and paper"
```

Categorize from image:
```bash
python ml_pipeline/inference.py \
    --checkpoint checkpoints/best_model.pt \
    --image path/to/invoice.jpg
```

Categorize with probabilities:
```bash
python ml_pipeline/inference.py \
    --checkpoint checkpoints/best_model.pt \
    --text "Hotel accommodation invoice" \
    --probs
```

### Using in Python Code

```python
from ml_pipeline.inference import InvoiceCategorizer

# Load model
categorizer = InvoiceCategorizer("checkpoints/best_model.pt")

# Predict from text
category = categorizer.predict_text("Invoice for software subscription")
print(f"Category: {category}")

# Predict from image
category = categorizer.predict_image("invoice.jpg")
print(f"Category: {category}")

# Get probabilities
category, probs = categorizer.predict_text("Invoice text...", return_probs=True)
print(f"Category: {category}")
print(f"Probabilities: {probs}")
```

## Expense Categories

Default categories (can be customized):
- Office Supplies
- Travel
- Meals & Entertainment
- Software & Subscriptions
- Hardware & Equipment
- Professional Services
- Utilities
- Marketing & Advertising
- Rent & Facilities
- Insurance
- Training & Education
- Transportation
- Legal & Compliance
- Other

## Model Architecture

### Text Model
- Base: DistilBERT (transformer)
- Classification head: 2-layer MLP with dropout
- Input: Tokenized invoice text (max 512 tokens)

### Image Model
- Architecture: Custom CNN (4 convolutional blocks)
- Input: 224x224 RGB images
- Classification head: 3-layer MLP with dropout

### Hybrid Model
- Combines text (DistilBERT) and image (CNN) features
- Fusion layer merges features before classification

## Integration with Flask App

You can integrate the ML pipeline with your existing Flask app:

```python
from ml_pipeline.inference import InvoiceCategorizer

# Load model once at startup
categorizer = InvoiceCategorizer("checkpoints/best_model.pt")

@app.post("/api/categorize")
def categorize_invoice():
    data = request.get_json()
    text = data.get("text")
    image_path = data.get("image_path")
    
    if text and image_path:
        category = categorizer.predict_hybrid(text, image_path)
    elif text:
        category = categorizer.predict_text(text)
    elif image_path:
        category = categorizer.predict_image(image_path)
    else:
        return jsonify({"error": "No input provided"}), 400
    
    return jsonify({"category": category})
```

## Tips

1. **Data Quality**: More labeled data = better performance. Aim for at least 50-100 samples per category.

2. **Text Extraction**: For image-based models, consider using OCR (like Tesseract) to extract text first, then use text or hybrid models.

3. **Fine-tuning**: Adjust learning rate, batch size, and epochs based on your dataset size and hardware.

4. **Validation**: Use a validation split to monitor overfitting. The training script automatically splits your data.

5. **Model Selection**:
   - Use **text** model if you have extracted invoice text
   - Use **image** model if you only have invoice images
   - Use **hybrid** model for best accuracy (if you have both)

## File Structure

```
ml_pipeline/
├── models/
│   └── invoice_classifier.py    # Model architectures
├── data/
│   ├── dataset.py               # Dataset classes
│   └── download_datasets.py     # Dataset preparation
├── train.py                     # Training script
├── inference.py                 # Inference script
└── README.md                    # This file
```

## License

This ML pipeline is part of the Pi Scanner project.

