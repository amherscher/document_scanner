"""
PyTorch model for invoice expense category classification.
Supports both text-based and image-based invoice classification.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer


class InvoiceTextClassifier(nn.Module):
    """
    Text-based invoice classifier using transformer architecture.
    Extracts text from invoices and classifies into expense categories.
    """
    def __init__(self, num_classes: int, model_name: str = "distilbert-base-uncased", 
                 hidden_dim: int = 256, dropout: float = 0.3):
        super(InvoiceTextClassifier, self).__init__()
        self.num_classes = num_classes
        self.transformer = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(self.transformer.config.hidden_size, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_classes)
        )
        
    def forward(self, input_ids, attention_mask):
        """Forward pass through the model."""
        outputs = self.transformer(input_ids=input_ids, attention_mask=attention_mask)
        # Use [CLS] token representation
        pooled_output = outputs.last_hidden_state[:, 0, :]
        logits = self.classifier(pooled_output)
        return logits


class InvoiceImageClassifier(nn.Module):
    """
    Image-based invoice classifier using CNN architecture.
    Classifies invoice images directly into expense categories.
    """
    def __init__(self, num_classes: int, input_channels: int = 3):
        super(InvoiceImageClassifier, self).__init__()
        self.num_classes = num_classes
        
        # Feature extraction layers
        self.features = nn.Sequential(
            # First block
            nn.Conv2d(input_channels, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            # Second block
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            # Third block
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            # Fourth block
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )
        
        # Adaptive pooling and classifier
        self.adaptive_pool = nn.AdaptiveAvgPool2d((4, 4))
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(512 * 4 * 4, 1024),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(1024, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, num_classes)
        )
        
    def forward(self, x):
        """Forward pass through the model."""
        x = self.features(x)
        x = self.adaptive_pool(x)
        x = self.classifier(x)
        return x


class HybridInvoiceClassifier(nn.Module):
    """
    Hybrid model combining both text and image features for classification.
    """
    def __init__(self, num_classes: int, text_model_name: str = "distilbert-base-uncased",
                 text_hidden_dim: int = 256, fusion_dim: int = 512, dropout: float = 0.3):
        super(HybridInvoiceClassifier, self).__init__()
        self.num_classes = num_classes
        
        # Text branch
        self.text_model = AutoModel.from_pretrained(text_model_name)
        self.text_proj = nn.Linear(self.text_model.config.hidden_size, text_hidden_dim)
        
        # Image branch
        self.image_model = InvoiceImageClassifier(num_classes=1)  # Dummy num_classes
        # Remove the final classifier from image model
        self.image_model.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(512 * 4 * 4, 1024),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(1024, text_hidden_dim)
        )
        
        # Fusion and classification
        self.fusion = nn.Sequential(
            nn.Linear(text_hidden_dim * 2, fusion_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(fusion_dim, fusion_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(fusion_dim // 2, num_classes)
        )
        
    def forward(self, text_input_ids, text_attention_mask, image):
        """Forward pass combining text and image features."""
        # Text features
        text_outputs = self.text_model(input_ids=text_input_ids, attention_mask=text_attention_mask)
        text_features = self.text_proj(text_outputs.last_hidden_state[:, 0, :])
        
        # Image features
        image_features = self.image_model.features(image)
        image_features = self.image_model.adaptive_pool(image_features)
        image_features = self.image_model.classifier(image_features)
        
        # Fuse features
        combined = torch.cat([text_features, image_features], dim=1)
        logits = self.fusion(combined)
        return logits

