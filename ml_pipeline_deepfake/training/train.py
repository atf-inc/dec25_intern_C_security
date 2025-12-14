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

