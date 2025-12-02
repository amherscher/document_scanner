import argparse
import json
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms
from transformers import get_linear_schedule_with_warmup
from tqdm import tqdm
import numpy as np
from sklearn.metrics import accuracy_score, classification_report

from .models.invoice_classifier import InvoiceTextClassifier, InvoiceImageClassifier, HybridInvoiceClassifier
from .data.dataset import InvoiceTextDataset, InvoiceImageDataset, HybridInvoiceDataset

def train_epoch(model, dataloader, criterion, optimizer, device, scheduler=None):
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []
    pbar = tqdm(dataloader, desc="Training")
    for batch in pbar:
        if isinstance(model, InvoiceTextClassifier):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['label'].to(device)
            optimizer.zero_grad()
            outputs = model(input_ids, attention_mask)
            loss = criterion(outputs, labels)
        elif isinstance(model, InvoiceImageClassifier):
            images = batch['image'].to(device)
            labels = batch['label'].to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
        elif isinstance(model, HybridInvoiceClassifier):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            images = batch['image'].to(device)
            labels = batch['label'].to(device)
            optimizer.zero_grad()
            outputs = model(input_ids, attention_mask, images)
            loss = criterion(outputs, labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        if scheduler:
            scheduler.step()
        total_loss += loss.item()
        preds = torch.argmax(outputs, dim=1).cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(labels.cpu().numpy())
        pbar.set_postfix({'loss': loss.item(), 'acc': accuracy_score(all_labels, all_preds)})
    return total_loss / len(dataloader), accuracy_score(all_labels, all_preds)

def validate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Validating"):
            if isinstance(model, InvoiceTextClassifier):
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['label'].to(device)
                outputs = model(input_ids, attention_mask)
                loss = criterion(outputs, labels)
            elif isinstance(model, InvoiceImageClassifier):
                images = batch['image'].to(device)
                labels = batch['label'].to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
            elif isinstance(model, HybridInvoiceClassifier):
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                images = batch['image'].to(device)
                labels = batch['label'].to(device)
                outputs = model(input_ids, attention_mask, images)
                loss = criterion(outputs, labels)
            total_loss += loss.item()
            preds = torch.argmax(outputs, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())
    return total_loss / len(dataloader), accuracy_score(all_labels, all_preds), all_preds, all_labels

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", type=str, required=True)
    parser.add_argument("--model_type", type=str, choices=["text", "image", "hybrid"], default="text")
    parser.add_argument("--image_dir", type=str, default=None)
    parser.add_argument("--output_dir", type=str, default="./checkpoints")
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--learning_rate", type=float, default=2e-5)
    parser.add_argument("--weight_decay", type=float, default=0.01)
    parser.add_argument("--warmup_steps", type=int, default=100)
    parser.add_argument("--val_split", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", type=str, default="auto")
    args = parser.parse_args()
    
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu") if args.device == "auto" else torch.device(args.device)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.model_type == "text":
        dataset = InvoiceTextDataset(args.data_path)
    elif args.model_type == "image":
        image_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        dataset = InvoiceImageDataset(args.data_path, image_dir=args.image_dir, transform=image_transform)
    else:
        image_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        dataset = HybridInvoiceDataset(args.data_path, image_dir=args.image_dir, transform=image_transform)
    
    dataset_size = len(dataset)
    val_size = int(args.val_split * dataset_size)
    train_size = dataset_size - val_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size],
        generator=torch.Generator().manual_seed(args.seed)
    )
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    
    if args.model_type == "text":
        model = InvoiceTextClassifier(num_classes=dataset.num_classes)
    elif args.model_type == "image":
        model = InvoiceImageClassifier(num_classes=dataset.num_classes)
    else:
        model = HybridInvoiceClassifier(num_classes=dataset.num_classes)
    
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=args.warmup_steps, num_training_steps=len(train_loader) * args.epochs)
    
    best_val_acc = 0.0
    train_losses = []
    train_accs = []
    val_losses = []
    val_accs = []
    
    for epoch in range(args.epochs):
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device, scheduler)
        train_losses.append(train_loss)
        train_accs.append(train_acc)
        val_loss, val_acc, val_preds, val_labels = validate(model, val_loader, criterion, device)
        val_losses.append(val_loss)
        val_accs.append(val_acc)
        print(f"Epoch {epoch + 1}/{args.epochs} - Train: {train_loss:.4f}/{train_acc:.4f}, Val: {val_loss:.4f}/{val_acc:.4f}")
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            checkpoint = {
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
                'categories': dataset.categories,
                'label_to_idx': dataset.label_to_idx,
                'model_type': args.model_type,
            }
            torch.save(checkpoint, output_dir / "best_model.pt")
    
    checkpoint = {
        'epoch': args.epochs,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'val_acc': val_acc,
        'categories': dataset.categories,
        'label_to_idx': dataset.label_to_idx,
        'model_type': args.model_type,
    }
    torch.save(checkpoint, output_dir / "final_model.pt")
    
    with open(output_dir / "training_history.json", 'w') as f:
        json.dump({'train_losses': train_losses, 'train_accs': train_accs, 'val_losses': val_losses, 'val_accs': val_accs}, f, indent=2)
    
    if len(val_labels) > 0:
        val_labels = np.array(val_labels)
        val_preds = np.array(val_preds)
        unique_labels = np.unique(val_labels)
        if len(unique_labels) > 0:
            present_categories = [dataset.categories[i] for i in unique_labels if i < len(dataset.categories)]
            present_indices = [i for i in unique_labels if i < len(dataset.categories)]
            label_map = {old_idx: new_idx for new_idx, old_idx in enumerate(present_indices)}
            mapped_labels = np.array([label_map.get(int(l), 0) for l in val_labels])
            mapped_preds = np.array([label_map.get(int(p), 0) if int(p) in label_map else 0 for p in val_preds])
            print("\nClassification Report:")
            print(classification_report(mapped_labels, mapped_preds, target_names=present_categories, zero_division=0))
    
    print(f"\nBest validation accuracy: {best_val_acc:.4f}")

if __name__ == "__main__":
    main()
