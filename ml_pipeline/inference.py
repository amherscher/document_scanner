"""
Inference script for categorizing invoices into expense categories.
"""
import argparse
from pathlib import Path
import torch
from PIL import Image
from transformers import AutoTokenizer
from torchvision import transforms

from .models.invoice_classifier import InvoiceTextClassifier, InvoiceImageClassifier, HybridInvoiceClassifier


class InvoiceCategorizer:
    """Wrapper class for invoice categorization."""
    
    def __init__(self, checkpoint_path: str, device: str = "auto"):
        """Load model from checkpoint."""
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        
        self.model_type = checkpoint.get('model_type', 'text')
        self.categories = checkpoint['categories']
        self.label_to_idx = checkpoint['label_to_idx']
        self.idx_to_label = {idx: cat for cat, idx in self.label_to_idx.items()}
        self.num_classes = len(self.categories)
        
        # Create model
        if self.model_type == "text":
            self.model = InvoiceTextClassifier(num_classes=self.num_classes)
            self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        elif self.model_type == "image":
            self.model = InvoiceImageClassifier(num_classes=self.num_classes)
            self.image_transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        else:  # hybrid
            self.model = HybridInvoiceClassifier(num_classes=self.num_classes)
            self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
            self.image_transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        
        # Load weights
        self.model.load_state_dict(checkpoint['model_state_dict'])
        
        # Set device
        if device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        self.model = self.model.to(self.device)
        self.model.eval()
    
    def predict_text(self, text: str, return_probs: bool = False):
        """Predict category from text."""
        if self.model_type not in ["text", "hybrid"]:
            raise ValueError(f"Model type {self.model_type} does not support text input")
        
        # Tokenize
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=512,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # Predict
        with torch.no_grad():
            if self.model_type == "text":
                outputs = self.model(input_ids, attention_mask)
            else:  # hybrid - need dummy image
                dummy_image = torch.zeros(1, 3, 224, 224).to(self.device)
                outputs = self.model(input_ids, attention_mask, dummy_image)
        
        probs = torch.softmax(outputs, dim=1)
        pred_idx = torch.argmax(probs, dim=1).item()
        pred_category = self.idx_to_label[pred_idx]
        
        if return_probs:
            prob_dict = {self.idx_to_label[i]: probs[0][i].item() 
                        for i in range(self.num_classes)}
            return pred_category, prob_dict
        return pred_category
    
    def predict_image(self, image_path: str, return_probs: bool = False):
        """Predict category from image."""
        if self.model_type not in ["image", "hybrid"]:
            raise ValueError(f"Model type {self.model_type} does not support image input")
        
        # Load and transform image
        image = Image.open(image_path).convert('RGB')
        if hasattr(self, 'image_transform'):
            image = self.image_transform(image)
        else:
            # Default transform for image-only model
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            image = transform(image)
        
        image = image.unsqueeze(0).to(self.device)
        
        # Predict
        with torch.no_grad():
            if self.model_type == "image":
                outputs = self.model(image)
            else:  # hybrid - need dummy text
                dummy_input_ids = torch.zeros(1, 512, dtype=torch.long).to(self.device)
                dummy_attention_mask = torch.ones(1, 512, dtype=torch.long).to(self.device)
                outputs = self.model(dummy_input_ids, dummy_attention_mask, image)
        
        probs = torch.softmax(outputs, dim=1)
        pred_idx = torch.argmax(probs, dim=1).item()
        pred_category = self.idx_to_label[pred_idx]
        
        if return_probs:
            prob_dict = {self.idx_to_label[i]: probs[0][i].item() 
                        for i in range(self.num_classes)}
            return pred_category, prob_dict
        return pred_category
    
    def predict_hybrid(self, text: str, image_path: str, return_probs: bool = False):
        """Predict category from both text and image."""
        if self.model_type != "hybrid":
            raise ValueError(f"Model type {self.model_type} is not hybrid")
        
        # Tokenize text
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=512,
            return_tensors='pt'
        )
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # Load and transform image
        image = Image.open(image_path).convert('RGB')
        image = self.image_transform(image).unsqueeze(0).to(self.device)
        
        # Predict
        with torch.no_grad():
            outputs = self.model(input_ids, attention_mask, image)
        
        probs = torch.softmax(outputs, dim=1)
        pred_idx = torch.argmax(probs, dim=1).item()
        pred_category = self.idx_to_label[pred_idx]
        
        if return_probs:
            prob_dict = {self.idx_to_label[i]: probs[0][i].item() 
                        for i in range(self.num_classes)}
            return pred_category, prob_dict
        return pred_category


def main():
    parser = argparse.ArgumentParser(description="Categorize invoices into expense categories")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--text", type=str, default=None, help="Invoice text to classify")
    parser.add_argument("--image", type=str, default=None, help="Path to invoice image")
    parser.add_argument("--file", type=str, default=None, help="Path to text file containing invoice text")
    parser.add_argument("--probs", action="store_true", help="Return probability distribution")
    parser.add_argument("--device", type=str, default="auto", help="Device (auto, cpu, cuda)")
    
    args = parser.parse_args()
    
    # Load categorizer
    print(f"Loading model from {args.checkpoint}...")
    categorizer = InvoiceCategorizer(args.checkpoint, device=args.device)
    print(f"Model loaded. Categories: {categorizer.categories}")
    
    # Get text input
    text = args.text
    if args.file:
        with open(args.file, 'r') as f:
            text = f.read()
    
    # Predict
    if categorizer.model_type == "text":
        if not text:
            raise ValueError("Text input required for text model")
        result = categorizer.predict_text(text, return_probs=args.probs)
    elif categorizer.model_type == "image":
        if not args.image:
            raise ValueError("Image input required for image model")
        result = categorizer.predict_image(args.image, return_probs=args.probs)
    else:  # hybrid
        if text and args.image:
            result = categorizer.predict_hybrid(text, args.image, return_probs=args.probs)
        elif text:
            result = categorizer.predict_text(text, return_probs=args.probs)
        elif args.image:
            result = categorizer.predict_image(args.image, return_probs=args.probs)
        else:
            raise ValueError("Either text or image (or both) required for hybrid model")
    
    # Print results
    if args.probs:
        category, probs = result
        print(f"\nPredicted Category: {category}")
        print("\nProbability Distribution:")
        for cat, prob in sorted(probs.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {prob:.4f}")
    else:
        print(f"\nPredicted Category: {result}")


if __name__ == "__main__":
    main()

