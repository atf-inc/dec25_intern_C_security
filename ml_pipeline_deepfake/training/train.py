"""
Training Script for Deepfake Fusion Classifier

Purpose:
    Train the lightweight fusion model on extracted features.
    This script ONLY trains the fusion head - WavLM and Whisper are frozen.

Workflow:
    1. Load pre-extracted features (WavLM + Whisper + DSP)
    2. Create train/validation split
    3. Train fusion model (5-10 epochs)
    4. Evaluate on validation set
    5. Save trained model

Training Configuration:
    - Loss: Binary Cross Entropy with Logits
    - Optimizer: Adam
    - Learning rate: 1e-3 (with optional decay)
    - Batch size: 8-16 (CPU-friendly)
    - Epochs: 5-10 (MVP-scale)

Usage:
    python train.py --data_dir data/ --epochs 10 --batch_size 8
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import os
import argparse
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.fusion_model import DeepfakeFusionModel, SimpleFusionModel
from features.wavlm_extractor import WavLMFeatureExtractor
from features.whisper_extractor import WhisperFeatureExtractor
from features.dsp_features import DSPFeatureExtractor


# ============================================================================
# Dataset Class
# ============================================================================

class DeepfakeDataset(Dataset):
    """
    Dataset for deepfake detection with pre-extracted features.
    """
    
    def __init__(self, wavlm_features, whisper_features, dsp_features, labels):
        """
        Args:
            wavlm_features (np.ndarray): WavLM features (N, 768)
            whisper_features (np.ndarray): Whisper features (N, 768)
            dsp_features (np.ndarray): DSP features (N, 6)
            labels (np.ndarray): Binary labels (N,) - 0=real, 1=fake
        """
        self.wavlm_features = torch.FloatTensor(wavlm_features)
        self.whisper_features = torch.FloatTensor(whisper_features)
        self.dsp_features = torch.FloatTensor(dsp_features)
        self.labels = torch.FloatTensor(labels)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return (
            self.wavlm_features[idx],
            self.whisper_features[idx],
            self.dsp_features[idx],
            self.labels[idx]
        )


# ============================================================================
# Feature Extraction Pipeline
# ============================================================================

def extract_features_from_directory(data_dir):
    """
    Extract features from all audio files in data/real and data/fake.
    
    Args:
        data_dir (str): Path to data directory containing real/ and fake/ folders
    
    Returns:
        tuple: (wavlm_features, whisper_features, dsp_features, labels, filenames)
    """
    print("\n=== Extracting Features ===")
    
    # Initialize extractors
    wavlm_extractor = WavLMFeatureExtractor()
    whisper_extractor = WhisperFeatureExtractor()
    dsp_extractor = DSPFeatureExtractor()
    
    # Collect audio files
    real_dir = os.path.join(data_dir, "real")
    fake_dir = os.path.join(data_dir, "fake")
    
    real_files = [os.path.join(real_dir, f) for f in os.listdir(real_dir) if f.endswith(('.wav', '.mp3', '.flac', '.m4a'))]
    fake_files = [os.path.join(fake_dir, f) for f in os.listdir(fake_dir) if f.endswith(('.wav', '.mp3', '.flac', '.m4a'))]
    
    all_files = real_files + fake_files
    labels = [0] * len(real_files) + [1] * len(fake_files)  # 0=real, 1=fake
    
    print(f"Found {len(real_files)} real samples")
    print(f"Found {len(fake_files)} fake samples")
    print(f"Total: {len(all_files)} samples")
    
    # Extract features
    wavlm_features = []
    whisper_features = []
    dsp_features = []
    
    for i, audio_file in enumerate(all_files):
        print(f"\nProcessing {i+1}/{len(all_files)}: {os.path.basename(audio_file)}")
        
        try:
            # Extract WavLM features
            wavlm_feat = wavlm_extractor.extract(audio_file)
            wavlm_features.append(wavlm_feat)
            
            # Extract Whisper features
            whisper_feat = whisper_extractor.extract(audio_file)
            whisper_features.append(whisper_feat)
            
            # Extract DSP features
            dsp_feat = dsp_extractor.extract(audio_file)
            dsp_features.append(dsp_feat)
            
        except Exception as e:
            print(f"  ⚠ Error processing {audio_file}: {e}")
            continue
    
    # Convert to numpy arrays
    wavlm_features = np.vstack(wavlm_features)
    whisper_features = np.vstack(whisper_features)
    dsp_features = np.vstack(dsp_features)
    labels = np.array(labels)
    
    print(f"\n✓ Feature extraction complete!")
    print(f"  WavLM shape: {wavlm_features.shape}")
    print(f"  Whisper shape: {whisper_features.shape}")
    print(f"  DSP shape: {dsp_features.shape}")
    
    return wavlm_features, whisper_features, dsp_features, labels, all_files



# ============================================================================
# Training Function
# ============================================================================

def train_epoch(model, dataloader, criterion, optimizer, device):
    """
    Train for one epoch.
    """
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []
    
    for wavlm_feat, whisper_feat, dsp_feat, labels in dataloader:
        # Move to device
        wavlm_feat = wavlm_feat.to(device)
        whisper_feat = whisper_feat.to(device)
        dsp_feat = dsp_feat.to(device)
        labels = labels.to(device).unsqueeze(1)  # (batch_size, 1)
        
        # Forward pass
        optimizer.zero_grad()
        outputs = model(wavlm_feat, whisper_feat, dsp_feat)
        loss = criterion(outputs, labels)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Track metrics
        total_loss += loss.item()
        preds = (torch.sigmoid(outputs) > 0.5).float()
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
    
    avg_loss = total_loss / len(dataloader)
    accuracy = accuracy_score(all_labels, all_preds)
    
    return avg_loss, accuracy


def evaluate(model, dataloader, criterion, device):
    """
    Evaluate on validation set.
    """
    model.eval()
    total_loss = 0
    all_preds = []
    all_probs = []
    all_labels = []
    
    with torch.no_grad():
        for wavlm_feat, whisper_feat, dsp_feat, labels in dataloader:
            wavlm_feat = wavlm_feat.to(device)
            whisper_feat = whisper_feat.to(device)
            dsp_feat = dsp_feat.to(device)
            labels = labels.to(device).unsqueeze(1)
            
            outputs = model(wavlm_feat, whisper_feat, dsp_feat)
            loss = criterion(outputs, labels)
            
            total_loss += loss.item()
            probs = torch.sigmoid(outputs)
            preds = (probs > 0.5).float()
            
            all_preds.extend(preds.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    avg_loss = total_loss / len(dataloader)
    accuracy = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(all_labels, all_preds, average='binary')
    
    try:
        auc = roc_auc_score(all_labels, all_probs)
    except:
        auc = 0.0
    
    return avg_loss, accuracy, precision, recall, f1, auc


# ============================================================================
# Main Training Script
# ============================================================================

def main(args):
    """
    Main training pipeline.
    """
    print("\n" + "="*60)
    print("Deepfake Voice Detection - Fusion Model Training")
    print("="*60)
    
    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    print(f"\nDevice: {device}")
    
    # Extract features (or load if cached)
    cache_path = os.path.join(args.data_dir, "features_cache.npz")
    
    if os.path.exists(cache_path) and not args.no_cache:
        print(f"\n✓ Loading cached features from {cache_path}")
        data = np.load(cache_path)
        wavlm_features = data['wavlm']
        whisper_features = data['whisper']
        dsp_features = data['dsp']
        labels = data['labels']
    else:
        wavlm_features, whisper_features, dsp_features, labels, _ = extract_features_from_directory(args.data_dir)
        
        # Cache features
        np.savez(cache_path, wavlm=wavlm_features, whisper=whisper_features, dsp=dsp_features, labels=labels)
        print(f"✓ Features cached to {cache_path}")
    
    # Train/validation split
    indices = np.arange(len(labels))
    train_idx, val_idx = train_test_split(indices, test_size=0.2, random_state=42, stratify=labels)
    
    train_dataset = DeepfakeDataset(
        wavlm_features[train_idx],
        whisper_features[train_idx],
        dsp_features[train_idx],
        labels[train_idx]
    )
    
    val_dataset = DeepfakeDataset(
        wavlm_features[val_idx],
        whisper_features[val_idx],
        dsp_features[val_idx],
        labels[val_idx]
    )
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    
    print(f"\nTrain samples: {len(train_dataset)}")
    print(f"Validation samples: {len(val_dataset)}")
    
    # Initialize model
    if args.simple:
        model = SimpleFusionModel(dropout=args.dropout)
    else:
        model = DeepfakeFusionModel(hidden_dim=args.hidden_dim, dropout=args.dropout)
    
    model.to(device)
    
    # Loss and optimizer
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    
    # Training loop
    print(f"\n=== Training for {args.epochs} epochs ===")
    best_val_acc = 0.0
    
    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch+1}/{args.epochs}")
        print("-" * 40)
        
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        print(f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f}")
        
        # Validate
        val_loss, val_acc, val_prec, val_rec, val_f1, val_auc = evaluate(model, val_loader, criterion, device)
        print(f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}")
        print(f"Precision: {val_prec:.4f} | Recall: {val_rec:.4f} | F1: {val_f1:.4f} | AUC: {val_auc:.4f}")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), args.save_path)
            print(f"✓ Model saved to {args.save_path}")
    
    print(f"\n=== Training Complete ===")
    print(f"Best validation accuracy: {best_val_acc:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Deepfake Fusion Classifier")
    
    # Data
    parser.add_argument("--data_dir", type=str, default="data", help="Path to data directory")
    parser.add_argument("--no_cache", action="store_true", help="Don't use cached features")
    
    # Model
    parser.add_argument("--simple", action="store_true", help="Use simple 2-layer model")
    parser.add_argument("--hidden_dim", type=int, default=256, help="Hidden layer dimension")
    parser.add_argument("--dropout", type=float, default=0.3, help="Dropout rate")
    
    # Training
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--cpu", action="store_true", help="Force CPU training")
    
    # Output
    parser.add_argument("--save_path", type=str, default="fusion_model.pth", help="Path to save model")
    
    args = parser.parse_args()
    main(args)

