"""
Fusion Deepfake Detector Model

Multi-modal fusion combining:
- WavLM acoustic features (768-dim)
- Whisper semantic features (768-dim)  
- DSP signal features (8-dim)

Total input: 1544 dimensions
Output: Binary classification (Real vs Deepfake)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class FusionDeepfakeDetector(nn.Module):
    """
    Multi-modal fusion model for deepfake voice detection.
    
    Architecture:
        Input (1544) → FC(512) → ReLU → Dropout → BatchNorm →
        FC(256) → ReLU → Dropout → BatchNorm →
        FC(128) → ReLU → Dropout →
        FC(1) → Sigmoid
    """
    
    def __init__(self, wavlm_dim=768, whisper_dim=768, dsp_dim=8):
        super().__init__()
        
        total_dim = wavlm_dim + whisper_dim + dsp_dim  # 1544
        
        self.fusion = nn.Sequential(
            nn.Linear(total_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.BatchNorm1d(512),
            
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.BatchNorm1d(256),
            
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
        
        # Expert scoring layers (for explainability)
        self.acoustic_scorer = nn.Linear(wavlm_dim, 1)
        self.semantic_scorer = nn.Linear(whisper_dim, 1)
        self.signal_scorer = nn.Linear(dsp_dim, 1)
    
    def forward(self, wavlm_emb, whisper_emb, dsp_features):
        """
        Forward pass.
        
        Args:
            wavlm_emb: WavLM embeddings (batch, 768)
            whisper_emb: Whisper embeddings (batch, 768)
            dsp_features: DSP features (batch, 8)
        
        Returns:
            confidence: Probability of being deepfake (batch, 1)
        """
        # Concatenate all modalities
        x = torch.cat([wavlm_emb, whisper_emb, dsp_features], dim=1)
        
        # Fusion prediction
        confidence = self.fusion(x)
        
        return confidence
    
    def predict_with_explanation(self, wavlm_emb, whisper_emb, dsp_features):
        """
        Predict with explainability.
        
        Returns which expert contributed most to the decision.
        """
        # Set to eval mode to avoid BatchNorm issues with batch_size=1
        self.eval()
        
        with torch.no_grad():
            # Get fusion prediction
            confidence = self.forward(wavlm_emb, whisper_emb, dsp_features)
            
            # Get individual expert scores
            acoustic_score = torch.sigmoid(self.acoustic_scorer(wavlm_emb))
            semantic_score = torch.sigmoid(self.semantic_scorer(whisper_emb))
            signal_score = torch.sigmoid(self.signal_scorer(dsp_features))
        
        return {
            'confidence': confidence.item() if confidence.dim() == 0 else confidence.squeeze().tolist(),
            'expert_scores': {
                'acoustic': acoustic_score.item() if acoustic_score.dim() == 0 else acoustic_score.squeeze().tolist(),
                'semantic': semantic_score.item() if semantic_score.dim() == 0 else semantic_score.squeeze().tolist(),
                'signal': signal_score.item() if signal_score.dim() == 0 else signal_score.squeeze().tolist()
            }
        }
    
    def count_parameters(self):
        """Count trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


if __name__ == '__main__':
    # Test the model
    print("Testing Fusion Model...")
    
    batch_size = 4
    wavlm = torch.randn(batch_size, 768)
    whisper = torch.randn(batch_size, 768)
    dsp = torch.randn(batch_size, 8)
    
    model = FusionDeepfakeDetector()
    
    print(f"Total parameters: {model.count_parameters():,}")
    
    # Test forward pass
    output = model(wavlm, whisper, dsp)
    print(f"Output shape: {output.shape}")
    print(f"Output values: {output.squeeze()}")
    
    # Test explainability
    result = model.predict_with_explanation(wavlm[0:1], whisper[0:1], dsp[0:1])
    print(f"\nExplainability test:")
    print(f"Confidence: {result['confidence']:.4f}")
    print(f"Expert scores: {result['expert_scores']}")
