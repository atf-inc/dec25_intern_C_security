"""
Advanced Fusion Model with Attention

Architecture:
1. Feature Projections: Project each modality (WavLM, Whisper, DSP) to shared 256-dim space.
2. Cross-Modal Attention: Learn interactions between modalities.
3. Residual Fusion Head: Deep classifier with skip connections.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

class FusionDeepfakeDetector(nn.Module):
    def __init__(self, wavlm_dim=768, whisper_dim=768, dsp_dim=246, shared_dim=256):
        super().__init__()
        
        # 1. Feature Projection Layers (Project to shared latent space)
        self.wavlm_proj = nn.Sequential(
            nn.Linear(wavlm_dim, shared_dim),
            nn.ReLU(),
            nn.BatchNorm1d(shared_dim),
            nn.Dropout(0.3)
        )
        
        self.whisper_proj = nn.Sequential(
            nn.Linear(whisper_dim, shared_dim),
            nn.ReLU(),
            nn.BatchNorm1d(shared_dim),
            nn.Dropout(0.3)
        )
        
        self.dsp_proj = nn.Sequential(
            nn.Linear(dsp_dim, 64),  # Intermediate step for small input
            nn.ReLU(),
            nn.Linear(64, shared_dim),
            nn.ReLU(),
            nn.BatchNorm1d(shared_dim),
            nn.Dropout(0.1)
        )
        
        # 2. Attention Mechanism
        # Self-attention processing of the 3 modality vectors
        self.attention = nn.MultiheadAttention(embed_dim=shared_dim, num_heads=4, batch_first=True)
        
        # 3. Fusion Classifier
        # Input = 3 * shared_dim (concatenated attention output)
        fusion_input_dim = 3 * shared_dim
        
        self.classifier = nn.Sequential(
            nn.Linear(fusion_input_dim, 512),
            nn.ReLU(),
            nn.LayerNorm(512),
            nn.Dropout(0.4),
            
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.LayerNorm(256),
            nn.Dropout(0.3),
            
            nn.Linear(256, 1)  # Logits (BCEWithLogitsLoss expected)
        )
        
        # Expert Explainability Heads (Auxiliary tasks)
        self.acoustic_head = nn.Linear(shared_dim, 1)
        self.semantic_head = nn.Linear(shared_dim, 1)
        self.signal_head = nn.Linear(shared_dim, 1)

    def forward(self, wavlm_emb, whisper_emb, dsp_features):
        # 1. Project to shared space
        # [batch, 256]
        w_proj = self.wavlm_proj(wavlm_emb) 
        s_proj = self.whisper_proj(whisper_emb)
        d_proj = self.dsp_proj(dsp_features)
        
        # 2. Stack for Attention
        # [batch, 3, 256]
        stacked = torch.stack([w_proj, s_proj, d_proj], dim=1)
        
        # Apply Attention
        # attn_output: [batch, 3, 256]
        attn_output, _ = self.attention(stacked, stacked, stacked)
        
        # Residual connection (Add original projections)
        x = attn_output + stacked
        
        # 3. Flatten and Classify
        # [batch, 768]
        x_flat = x.reshape(x.size(0), -1)
        
        logits = self.classifier(x_flat)
        
        return logits

    def predict_with_explanation(self, wavlm_emb, whisper_emb, dsp_features):
        """
        Inference mode with explainability outputs.
        """
        self.eval()
        with torch.no_grad():
            # Projections
            w_proj = self.wavlm_proj(wavlm_emb)
            s_proj = self.whisper_proj(whisper_emb)
            d_proj = self.dsp_proj(dsp_features)
            
            # Attention
            stacked = torch.stack([w_proj, s_proj, d_proj], dim=1)
            attn_output, attn_weights = self.attention(stacked, stacked, stacked)
            
            # Classifier
            x = attn_output + stacked
            x_flat = x.reshape(x.size(0), -1)
            logits = self.classifier(x_flat)
            confidence = torch.sigmoid(logits)
            
            # Expert Scores (Auxiliary)
            acoustic_score = torch.sigmoid(self.acoustic_head(w_proj))
            semantic_score = torch.sigmoid(self.semantic_head(s_proj))
            signal_score = torch.sigmoid(self.signal_head(d_proj))
            
        return {
            'confidence': confidence.item() if confidence.dim() == 0 else confidence.cpu().numpy(),
            'expert_scores': {
                'acoustic': acoustic_score.item(),
                'semantic': semantic_score.item(),
                'signal': signal_score.item()
            },
            'attention_weights': attn_weights.cpu().numpy()
        }

    def count_parameters(self):
        """Count trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
