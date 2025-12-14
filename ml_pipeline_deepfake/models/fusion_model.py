"""
Fusion Model for Deepfake Voice Detection

Purpose:
    Lightweight feedforward network that fuses features from three experts:
    1. WavLM (768-dim acoustic features)
    2. Whisper (768-dim semantic features)
    3. DSP (6-dim signal features)
    
    Total input: 768 + 768 + 6 = 1542 dimensions
    Output: Binary classification (0 = real, 1 = fake)

Architecture Philosophy:
    - LIGHTWEIGHT: Only the fusion head is trainable
    - WavLM and Whisper are FROZEN (no fine-tuning)
    - Simple MLP: 2-3 fully connected layers
    - Dropout for regularization (small dataset)
    - CPU-friendly for MVP

Training Strategy:
    - Loss: Binary Cross Entropy (BCE)
    - Optimizer: Adam
    - Epochs: 5-10 (MVP-scale)
    - Small batch size (CPU-friendly)

Usage:
    model = DeepfakeFusionModel()
    output = model(wavlm_features, whisper_features, dsp_features)
    # Returns: probability of being fake (0-1)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class DeepfakeFusionModel(nn.Module):
    """
    Lightweight fusion classifier for deepfake detection.
    
    Combines WavLM + Whisper + DSP features into a single prediction.
    """
    
    def __init__(
        self,
        wavlm_dim=768,
        whisper_dim=768,
        dsp_dim=6,
        hidden_dim=256,
        dropout=0.3
    ):
        """
        Initialize fusion model.
        
        Args:
            wavlm_dim (int): WavLM feature dimension (default: 768)
            whisper_dim (int): Whisper feature dimension (default: 768)
            dsp_dim (int): DSP feature dimension (default: 6)
            hidden_dim (int): Hidden layer dimension (default: 256)
            dropout (float): Dropout rate for regularization (default: 0.3)
        """
        super(DeepfakeFusionModel, self).__init__()
        
        # Input dimension: concatenation of all features
        self.input_dim = wavlm_dim + whisper_dim + dsp_dim  # 1542
        
        # Simple 3-layer MLP
        self.fc1 = nn.Linear(self.input_dim, hidden_dim)
        self.bn1 = nn.BatchNorm1d(hidden_dim)  # Batch normalization for stability
        self.dropout1 = nn.Dropout(dropout)
        
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.bn2 = nn.BatchNorm1d(hidden_dim // 2)
        self.dropout2 = nn.Dropout(dropout)
        
        self.fc3 = nn.Linear(hidden_dim // 2, 1)  # Binary output
        
        print(f"✓ Fusion Model initialized")
        print(f"  Input dim: {self.input_dim} (WavLM: {wavlm_dim}, Whisper: {whisper_dim}, DSP: {dsp_dim})")
        print(f"  Hidden dim: {hidden_dim}")
        print(f"  Dropout: {dropout}")
        print(f"  Total parameters: {self.count_parameters():,}")
    
    def forward(self, wavlm_features, whisper_features, dsp_features):
        """
        Forward pass through the fusion model.
        
        Args:
            wavlm_features (torch.Tensor): WavLM features (batch_size, 768)
            whisper_features (torch.Tensor): Whisper features (batch_size, 768)
            dsp_features (torch.Tensor): DSP features (batch_size, 6)
        
        Returns:
            torch.Tensor: Prediction logits (batch_size, 1)
        """
        # Concatenate all features
        x = torch.cat([wavlm_features, whisper_features, dsp_features], dim=1)
        
        # Layer 1
        x = self.fc1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.dropout1(x)
        
        # Layer 2
        x = self.fc2(x)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.dropout2(x)
        
        # Output layer (no activation, use BCEWithLogitsLoss)
        x = self.fc3(x)
        
        return x
    

