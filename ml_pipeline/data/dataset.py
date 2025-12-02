"""
Dataset classes for invoice expense categorization.
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import torch
from torch.utils.data import Dataset
from PIL import Image
import pandas as pd
from transformers import AutoTokenizer


class InvoiceTextDataset(Dataset):
    """Dataset for text-based invoice classification."""
    
    def __init__(self, data_path: str, labels_path: Optional[str] = None,
                 max_length: int = 512, model_name: str = "distilbert-base-uncased"):
        self.data_path = Path(data_path)
        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Load data
        if labels_path:
            self.df = pd.read_csv(labels_path)
        elif self.data_path.suffix == '.csv':
            self.df = pd.read_csv(self.data_path)
        elif self.data_path.suffix == '.json':
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            self.df = pd.DataFrame(data)
        else:
            raise ValueError(f"Unsupported file format: {self.data_path.suffix}")
        
        # Get unique categories and create label mapping
        if 'category' in self.df.columns:
            self.categories = sorted(self.df['category'].unique())
            self.label_to_idx = {cat: idx for idx, cat in enumerate(self.categories)}
            self.idx_to_label = {idx: cat for cat, idx in self.label_to_idx.items()}
        else:
            raise ValueError("'category' column not found in dataset")
        
        self.num_classes = len(self.categories)
        
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        
        # Get text (could be from 'text', 'description', 'content', etc.)
        text = ""
        for col in ['text', 'description', 'content', 'invoice_text', 'extracted_text']:
            if col in row and pd.notna(row[col]):
                text = str(row[col])
                break
        
        if not text:
            # Try to get text from other columns
            text = " ".join([str(row[col]) for col in row.index 
                           if col != 'category' and pd.notna(row[col])])
        
        # If still no text, use a placeholder (for image-only models this is OK)
        if not text or text.strip() == "":
            text = "invoice document"  # Minimal placeholder text
        
        # Tokenize
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        # Get label
        label = self.label_to_idx[row['category']]
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'label': torch.tensor(label, dtype=torch.long),
            'text': text
        }


class InvoiceImageDataset(Dataset):
    """Dataset for image-based invoice classification."""
    
    def __init__(self, data_path: str, labels_path: Optional[str] = None,
                 image_dir: Optional[str] = None, transform=None):
        self.data_path = Path(data_path)
        self.transform = transform
        
        # Load labels
        if labels_path:
            self.df = pd.read_csv(labels_path)
        elif self.data_path.suffix == '.csv':
            self.df = pd.read_csv(self.data_path)
        elif self.data_path.suffix == '.json':
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            self.df = pd.DataFrame(data)
        else:
            raise ValueError(f"Unsupported file format: {self.data_path.suffix}")
        
        # Set image directory
        if image_dir:
            self.image_dir = Path(image_dir)
        else:
            self.image_dir = self.data_path.parent / "images"
        
        # Get categories
        if 'category' in self.df.columns:
            self.categories = sorted(self.df['category'].unique())
            self.label_to_idx = {cat: idx for idx, cat in enumerate(self.categories)}
            self.idx_to_label = {idx: cat for cat, idx in self.label_to_idx.items()}
        else:
            raise ValueError("'category' column not found in dataset")
        
        self.num_classes = len(self.categories)
        
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        
        # Get image path
        image_path = None
        for col in ['image_path', 'image', 'file_path', 'path', 'filename']:
            if col in row and pd.notna(row[col]):
                image_path = Path(row[col])
                if not image_path.is_absolute():
                    image_path = self.image_dir / image_path
                break
        
        if not image_path or not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Load image
        image = Image.open(image_path).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
        
        # Get label
        label = self.label_to_idx[row['category']]
        
        return {
            'image': image,
            'label': torch.tensor(label, dtype=torch.long),
            'path': str(image_path)
        }


class HybridInvoiceDataset(Dataset):
    """Dataset for hybrid text+image invoice classification."""
    
    def __init__(self, data_path: str, labels_path: Optional[str] = None,
                 image_dir: Optional[str] = None, transform=None,
                 max_length: int = 512, model_name: str = "distilbert-base-uncased"):
        self.data_path = Path(data_path)
        self.transform = transform
        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Load data
        if labels_path:
            self.df = pd.read_csv(labels_path)
        elif self.data_path.suffix == '.csv':
            self.df = pd.read_csv(self.data_path)
        elif self.data_path.suffix == '.json':
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            self.df = pd.DataFrame(data)
        else:
            raise ValueError(f"Unsupported file format: {self.data_path.suffix}")
        
        # Set image directory
        if image_dir:
            self.image_dir = Path(image_dir)
        else:
            self.image_dir = self.data_path.parent / "images"
        
        # Get categories
        if 'category' in self.df.columns:
            self.categories = sorted(self.df['category'].unique())
            self.label_to_idx = {cat: idx for idx, cat in enumerate(self.categories)}
            self.idx_to_label = {idx: cat for cat, idx in self.label_to_idx.items()}
        else:
            raise ValueError("'category' column not found in dataset")
        
        self.num_classes = len(self.categories)
        
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        
        # Get text
        text = ""
        for col in ['text', 'description', 'content', 'invoice_text', 'extracted_text']:
            if col in row and pd.notna(row[col]):
                text = str(row[col])
                break
        
        if not text:
            text = " ".join([str(row[col]) for col in row.index 
                           if col not in ['category', 'image_path', 'image', 'file_path', 'path', 'filename'] 
                           and pd.notna(row[col])])
        
        # Tokenize text
        text_encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        # Get image
        image_path = None
        for col in ['image_path', 'image', 'file_path', 'path', 'filename']:
            if col in row and pd.notna(row[col]):
                image_path = Path(row[col])
                if not image_path.is_absolute():
                    image_path = self.image_dir / image_path
                break
        
        if image_path and image_path.exists():
            image = Image.open(image_path).convert('RGB')
            if self.transform:
                image = self.transform(image)
        else:
            # Create a blank image if not found
            image = Image.new('RGB', (224, 224), color='white')
            if self.transform:
                image = self.transform(image)
        
        # Get label
        label = self.label_to_idx[row['category']]
        
        return {
            'input_ids': text_encoding['input_ids'].flatten(),
            'attention_mask': text_encoding['attention_mask'].flatten(),
            'image': image,
            'label': torch.tensor(label, dtype=torch.long),
            'text': text,
            'path': str(image_path) if image_path else None
        }

