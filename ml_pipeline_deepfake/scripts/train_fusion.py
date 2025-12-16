"""
Training Script for Fusion Deepfake Detector

Trains the fusion classifier on pre-extracted features.

Usage:
    python scripts/train_fusion.py --features_dir features/ --epochs 20
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score, confusion_matrix

from src.models import FusionDeepfakeDetector


class FeatureDataset(Dataset):
    """Dataset for pre-extracted features."""
    
    def __init__(self, wavlm_features, whisper_features, dsp_features, labels):
        self.wavlm = torch.FloatTensor(wavlm_features)
        self.whisper = torch.FloatTensor(whisper_features)
        self.dsp = torch.FloatTensor(dsp_features)
        self.labels = torch.FloatTensor(labels)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return self.wavlm[idx], self.whisper[idx], self.dsp[idx], self.labels[idx]


def load_features(features_dir, split):
    """Load pre-extracted features for a split."""
    split_dir = os.path.join(features_dir, split)
    
    wavlm = np.load(os.path.join(split_dir, 'wavlm_features.npy'))
    whisper = np.load(os.path.join(split_dir, 'whisper_features.npy'))
    dsp = np.load(os.path.join(split_dir, 'dsp_features.npy'))
    labels = np.load(os.path.join(split_dir, 'labels.npy'))
    
    return wavlm, whisper, dsp, labels


def train_epoch(model, dataloader, criterion, optimizer, device):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []
    
    for wavlm, whisper, dsp, labels in dataloader:
        wavlm = wavlm.to(device)
        whisper = whisper.to(device)
        dsp = dsp.to(device)
        labels = labels.to(device).unsqueeze(1)
        
        # Forward
        optimizer.zero_grad()
        outputs = model(wavlm, whisper, dsp)
        loss = criterion(outputs, labels)
        
        # Backward
        loss.backward()
        optimizer.step()
        
        # Metrics
        total_loss += loss.item()
        preds = (outputs > 0.5).float()
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
    
    avg_loss = total_loss / len(dataloader)
    accuracy = accuracy_score(all_labels, all_preds)
    
    return avg_loss, accuracy


def evaluate(model, dataloader, criterion, device):
    """Evaluate on validation/test set."""
    model.eval()
    total_loss = 0
    all_preds = []
    all_probs = []
    all_labels = []
    
    with torch.no_grad():
        for wavlm, whisper, dsp, labels in dataloader:
            wavlm = wavlm.to(device)
            whisper = whisper.to(device)
            dsp = dsp.to(device)
            labels = labels.to(device).unsqueeze(1)
            
            outputs = model(wavlm, whisper, dsp)
            loss = criterion(outputs, labels)
            
            total_loss += loss.item()
            preds = (outputs > 0.5).float()
            
            all_preds.extend(preds.cpu().numpy())
            all_probs.extend(outputs.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    avg_loss = total_loss / len(dataloader)
    accuracy = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(all_labels, all_preds, average='binary', zero_division=0)
    
    try:
        auc = roc_auc_score(all_labels, all_probs)
    except:
        auc = 0.0
    
    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds)
    
    return avg_loss, accuracy, precision, recall, f1, auc, cm


def main():
    parser = argparse.ArgumentParser(description="Train Fusion Deepfake Detector")
    parser.add_argument('--features_dir', type=str, required=True, help='Directory with extracted features')
    parser.add_argument('--epochs', type=int, default=20, help='Number of epochs')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--output', type=str, default='models/fusion_detector.pth', help='Output model path')
    parser.add_argument('--cpu', action='store_true', help='Force CPU training')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("Fusion Deepfake Detector - Training")
    print("="*60)
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() and not args.cpu else 'cpu')
    print(f"Device: {device}")
    
    # Load features
    print("\nLoading features...")
    train_wavlm, train_whisper, train_dsp, train_labels = load_features(args.features_dir, 'train')
    dev_wavlm, dev_whisper, dev_dsp, dev_labels = load_features(args.features_dir, 'dev')
    
    print(f"Train samples: {len(train_labels)} ({sum(train_labels == 0)} real, {sum(train_labels == 1)} fake)")
    print(f"Dev samples: {len(dev_labels)} ({sum(dev_labels == 0)} real, {sum(dev_labels == 1)} fake)")
    
    # Create datasets
    train_dataset = FeatureDataset(train_wavlm, train_whisper, train_dsp, train_labels)
    dev_dataset = FeatureDataset(dev_wavlm, dev_whisper, dev_dsp, dev_labels)
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    dev_loader = DataLoader(dev_dataset, batch_size=args.batch_size, shuffle=False)
    
    # Initialize model
    print("\nInitializing model...")
    model = FusionDeepfakeDetector()
    model.to(device)
    print(f"Total parameters: {model.count_parameters():,}")
    
    # Loss and optimizer
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=3, verbose=True)
    
    # Training loop
    print(f"\n{'='*60}")
    print(f"Training for {args.epochs} epochs")
    print("="*60)
    
    best_val_acc = 0.0
    
    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch+1}/{args.epochs}")
        print("-" * 40)
        
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        print(f"Train - Loss: {train_loss:.4f} | Acc: {train_acc:.4f}")
        
        # Validate
        val_loss, val_acc, val_prec, val_rec, val_f1, val_auc, cm = evaluate(model, dev_loader, criterion, device)
        print(f"Val   - Loss: {val_loss:.4f} | Acc: {val_acc:.4f}")
        print(f"        Prec: {val_prec:.4f} | Rec: {val_rec:.4f} | F1: {val_f1:.4f} | AUC: {val_auc:.4f}")
        print(f"Confusion Matrix:\n{cm}")
        
        # Learning rate scheduling
        scheduler.step(val_acc)
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            os.makedirs(os.path.dirname(args.output), exist_ok=True)
            torch.save(model.state_dict(), args.output)
            print(f"✓ Best model saved to {args.output}")
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"Best validation accuracy: {best_val_acc:.4f}")
    print(f"Model saved to: {args.output}")
    print("\nNext step:")
    print("  Integrate model into backend/app/ml/deepfake_model.py")
    print("="*60)


if __name__ == '__main__':
    main()
