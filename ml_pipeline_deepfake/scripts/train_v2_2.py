"""
Training Script for Fusion Deepfake Detector v2.2

Improvements over v2.1:
1. Online data augmentation during training (more robust)
2. Mixup augmentation for better generalization
3. More aggressive regularization
4. Proper train/val split with stratification
5. Early stopping to prevent overfitting
6. Saves best model by F1 score (not just accuracy)

Usage:
    python scripts/train_v2_2.py --data_dir data/ --epochs 50 --augment
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
from sklearn.model_selection import train_test_split
from pathlib import Path
import librosa
from tqdm import tqdm
import random

from src.models import FusionDeepfakeDetector
from src.features import WavLMExtractor, WhisperExtractor, DSPExtractor
from src.utils.augmentation import AudioAugmentor


class AudioDataset(Dataset):
    """
    Dataset that loads raw audio and extracts features on-the-fly.
    Supports online augmentation for better generalization.
    """
    
    def __init__(self, file_paths, labels, extractors, augmentor=None, augment_prob=0.5):
        self.file_paths = file_paths
        self.labels = labels
        self.extractors = extractors
        self.augmentor = augmentor
        self.augment_prob = augment_prob
        self.sr = 16000
        
        # Cache for extracted features (avoid re-extracting during validation)
        self.cache = {}
        self.use_cache = (augmentor is None)  # Only cache if no augmentation
        
    def __len__(self):
        return len(self.file_paths)
    
    def __getitem__(self, idx):
        file_path = self.file_paths[idx]
        label = self.labels[idx]
        
        # Check cache first (for validation set)
        if self.use_cache and file_path in self.cache:
            return self.cache[file_path] + (label,)
        
        try:
            # Load audio
            waveform, sr = librosa.load(file_path, sr=self.sr)
            
            # Apply augmentation (training only)
            if self.augmentor is not None and random.random() < self.augment_prob:
                waveform = self.augmentor.apply_random_augmentation(waveform)
            
            # Extract features
            wavlm_emb = self.extractors['wavlm'].extract(waveform, sr)
            whisper_emb = self.extractors['whisper'].extract(waveform, sr)
            dsp_feat = self.extractors['dsp'].extract(waveform, sr)
            
            # Convert to tensors
            wavlm_t = torch.FloatTensor(wavlm_emb)
            whisper_t = torch.FloatTensor(whisper_emb)
            dsp_t = torch.FloatTensor(dsp_feat)
            
            # Cache if validation
            if self.use_cache:
                self.cache[file_path] = (wavlm_t, whisper_t, dsp_t)
            
            return wavlm_t, whisper_t, dsp_t, label
            
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            # Return zeros as fallback
            return (
                torch.zeros(768),
                torch.zeros(768),
                torch.zeros(246),
                label
            )


def collect_audio_files(data_dir):
    """Collect all audio files from data directory."""
    real_dir = os.path.join(data_dir, 'real')
    fake_dir = os.path.join(data_dir, 'fake')
    
    files = []
    labels = []
    
    # Real samples
    if os.path.exists(real_dir):
        for f in Path(real_dir).glob('**/*.wav'):
            files.append(str(f))
            labels.append(0)
    
    # Fake samples
    if os.path.exists(fake_dir):
        for f in Path(fake_dir).glob('**/*.wav'):
            files.append(str(f))
            labels.append(1)
    
    return files, labels


def mixup_data(x1, x2, x3, y, alpha=0.2):
    """Apply mixup augmentation to batch."""
    if alpha > 0:
        lam = np.random.beta(alpha, alpha)
    else:
        lam = 1
    
    batch_size = x1.size(0)
    index = torch.randperm(batch_size)
    
    mixed_x1 = lam * x1 + (1 - lam) * x1[index]
    mixed_x2 = lam * x2 + (1 - lam) * x2[index]
    mixed_x3 = lam * x3 + (1 - lam) * x3[index]
    
    y_a, y_b = y, y[index]
    
    return mixed_x1, mixed_x2, mixed_x3, y_a, y_b, lam


def mixup_criterion(criterion, pred, y_a, y_b, lam):
    """Mixup loss function."""
    return lam * criterion(pred, y_a) + (1 - lam) * criterion(pred, y_b)


def train_epoch(model, dataloader, criterion, optimizer, device, use_mixup=True, mixup_alpha=0.2):
    """Train for one epoch with optional mixup."""
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []
    
    for batch in dataloader:
        wavlm, whisper, dsp, labels = batch
        wavlm = wavlm.to(device)
        whisper = whisper.to(device)
        dsp = dsp.to(device)
        labels = labels.float().to(device).unsqueeze(1)
        
        optimizer.zero_grad()
        
        if use_mixup and random.random() < 0.5:
            # Apply mixup
            wavlm, whisper, dsp, labels_a, labels_b, lam = mixup_data(
                wavlm, whisper, dsp, labels, mixup_alpha
            )
            outputs = model(wavlm, whisper, dsp)
            loss = mixup_criterion(criterion, outputs, labels_a, labels_b, lam)
        else:
            # Normal forward
            outputs = model(wavlm, whisper, dsp)
            loss = criterion(outputs, labels)
        
        loss.backward()
        
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()
        
        total_loss += loss.item()
        
        # For metrics (use un-mixed labels)
        with torch.no_grad():
            probs = torch.sigmoid(outputs)
            preds = (probs > 0.5).float()
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy() if not use_mixup else batch[3].numpy().reshape(-1, 1))
    
    avg_loss = total_loss / len(dataloader)
    accuracy = accuracy_score(np.array(all_labels) > 0.5, np.array(all_preds) > 0.5)
    
    return avg_loss, accuracy


def evaluate(model, dataloader, criterion, device):
    """Evaluate on validation/test set."""
    model.eval()
    total_loss = 0
    all_preds = []
    all_probs = []
    all_labels = []
    
    with torch.no_grad():
        for batch in dataloader:
            wavlm, whisper, dsp, labels = batch
            wavlm = wavlm.to(device)
            whisper = whisper.to(device)
            dsp = dsp.to(device)
            labels = labels.float().to(device).unsqueeze(1)
            
            outputs = model(wavlm, whisper, dsp)
            loss = criterion(outputs, labels)
            
            total_loss += loss.item()
            
            probs = torch.sigmoid(outputs)
            preds = (probs > 0.5).float()
            
            all_preds.extend(preds.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    avg_loss = total_loss / len(dataloader)
    
    all_preds = np.array(all_preds).flatten()
    all_probs = np.array(all_probs).flatten()
    all_labels = np.array(all_labels).flatten()
    
    accuracy = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_labels, all_preds, average='binary', zero_division=0
    )
    
    try:
        auc = roc_auc_score(all_labels, all_probs)
    except:
        auc = 0.0
    
    cm = confusion_matrix(all_labels, all_preds)
    
    return avg_loss, accuracy, precision, recall, f1, auc, cm


def main():
    parser = argparse.ArgumentParser(description="Train Fusion Deepfake Detector v2.2")
    parser.add_argument('--data_dir', type=str, default='data', help='Data directory')
    parser.add_argument('--epochs', type=int, default=50, help='Number of epochs')
    parser.add_argument('--batch_size', type=int, default=8, help='Batch size (small due to large models)')
    parser.add_argument('--lr', type=float, default=0.0005, help='Learning rate')
    parser.add_argument('--output', type=str, default='models/deepfake_v2_2.pth', help='Output model path')
    parser.add_argument('--cpu', action='store_true', help='Force CPU training')
    parser.add_argument('--augment', action='store_true', help='Enable online augmentation')
    parser.add_argument('--mixup', action='store_true', help='Enable mixup augmentation')
    parser.add_argument('--val_split', type=float, default=0.2, help='Validation split ratio')
    parser.add_argument('--patience', type=int, default=10, help='Early stopping patience')
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("Fusion Deepfake Detector - Training v2.2 (Enhanced Generalization)")
    print("="*70)
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() and not args.cpu else 'cpu')
    print(f"Device: {device}")
    
    # Collect files
    print("\nCollecting audio files...")
    files, labels = collect_audio_files(args.data_dir)
    print(f"Found {len(files)} audio files ({sum(1 for l in labels if l == 0)} real, {sum(1 for l in labels if l == 1)} fake)")
    
    if len(files) < 10:
        print("ERROR: Not enough audio files! Need at least 10.")
        return
    
    # Split into train/val with stratification
    train_files, val_files, train_labels, val_labels = train_test_split(
        files, labels, test_size=args.val_split, stratify=labels, random_state=42
    )
    
    print(f"Train: {len(train_files)} samples")
    print(f"Val: {len(val_files)} samples")
    
    # Initialize extractors
    print("\nInitializing feature extractors...")
    extractors = {
        'wavlm': WavLMExtractor(device=device),
        'whisper': WhisperExtractor(device=device),
        'dsp': DSPExtractor()
    }
    print("✓ Extractors ready")
    
    # Initialize augmentor
    augmentor = AudioAugmentor() if args.augment else None
    if augmentor:
        print("✓ Data augmentation enabled (noise, reverb, codec, pitch)")
    
    # Create datasets
    train_dataset = AudioDataset(
        train_files, train_labels, extractors, 
        augmentor=augmentor, augment_prob=0.7
    )
    val_dataset = AudioDataset(
        val_files, val_labels, extractors, 
        augmentor=None  # No augmentation for validation
    )
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)
    
    # Initialize model
    print("\nInitializing model...")
    model = FusionDeepfakeDetector(dsp_dim=246)
    model.to(device)
    print(f"Total parameters: {model.count_parameters():,}")
    
    # Calculate class weights
    num_real = sum(1 for l in train_labels if l == 0)
    num_fake = sum(1 for l in train_labels if l == 1)
    pos_weight = torch.tensor([num_real / max(num_fake, 1)]).to(device)
    print(f"Class Weight (Pos Weight): {pos_weight.item():.2f}")
    
    # Loss and optimizer
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2)
    
    # Training loop
    print(f"\n{'='*70}")
    print(f"Training for {args.epochs} epochs (patience={args.patience})")
    print("="*70)
    
    best_f1 = 0.0
    best_acc = 0.0
    epochs_without_improvement = 0
    
    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch+1}/{args.epochs} (LR: {scheduler.get_last_lr()[0]:.6f})")
        print("-" * 50)
        
        # Train
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, device,
            use_mixup=args.mixup, mixup_alpha=0.2
        )
        print(f"Train - Loss: {train_loss:.4f} | Acc: {train_acc:.4f}")
        
        # Validate
        val_loss, val_acc, val_prec, val_rec, val_f1, val_auc, cm = evaluate(
            model, val_loader, criterion, device
        )
        print(f"Val   - Loss: {val_loss:.4f} | Acc: {val_acc:.4f}")
        print(f"        Prec: {val_prec:.4f} | Rec: {val_rec:.4f} | F1: {val_f1:.4f} | AUC: {val_auc:.4f}")
        print(f"Confusion Matrix:\n{cm}")
        
        # Learning rate scheduling
        scheduler.step()
        
        # Save best model by F1 score
        if val_f1 > best_f1:
            best_f1 = val_f1
            best_acc = val_acc
            epochs_without_improvement = 0
            
            os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else '.', exist_ok=True)
            torch.save(model.state_dict(), args.output)
            print(f"✓ Best model saved (F1: {best_f1:.4f})")
        else:
            epochs_without_improvement += 1
            
        # Early stopping
        if epochs_without_improvement >= args.patience:
            print(f"\nEarly stopping triggered after {epoch+1} epochs")
            break
    
    print("\n" + "="*70)
    print("TRAINING COMPLETE")
    print("="*70)
    print(f"Best validation F1: {best_f1:.4f}")
    print(f"Best validation accuracy: {best_acc:.4f}")
    print(f"Model saved to: {args.output}")
    print("\nNext steps:")
    print("  1. Copy model to backend: cp models/deepfake_v2_2.pth ../backend/app/ml/models/")
    print("  2. Update backend to use v2.2")
    print("="*70)


if __name__ == '__main__':
    main()

