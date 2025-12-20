"""
WavLM Feature Extractor - Acoustic Expert

Extracts 768-dimensional embeddings from audio using Microsoft's WavLM-Base-Plus.
Captures acoustic patterns, micro-glitches, and vocoder artifacts.
"""

import torch
import numpy as np
from transformers import WavLMModel, Wav2Vec2FeatureExtractor
import logging

logger = logging.getLogger(__name__)


class WavLMExtractor:
    """
    Acoustic Expert: Analyzes raw sound waves for deepfake artifacts.
    
    Detects:
    - Micro-glitches in waveform
    - Compression artifacts
    - Neural vocoder traces (phase errors, spectral anomalies)
    - Unnatural harmonics
    """
    
    def __init__(self, model_name="microsoft/wavlm-base-plus", device=None):
        """
        Initialize WavLM extractor.
        
        Args:
            model_name: Hugging Face model identifier
            device: torch device (cuda/cpu)
        """
        self.model_name = model_name
        
        # Auto-detect device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
        
        logger.info(f"Initializing WavLM Extractor on {self.device}")
        
        # Lazy loading
        self.model = None
        self.processor = None
    
    def _ensure_loaded(self):
        """Load model if not already loaded."""
        if self.model is not None:
            return
        
        logger.info(f"Loading WavLM model: {self.model_name}")
        
        try:
            self.processor = Wav2Vec2FeatureExtractor.from_pretrained(self.model_name)
            
            # Load with optimizations
            if self.device.type == "cuda":
                self.model = WavLMModel.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16
                ).to(self.device)
            else:
                self.model = WavLMModel.from_pretrained(self.model_name).to(self.device)
            
            self.model.eval()
            logger.info("WavLM model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load WavLM model: {e}")
            raise
    
    def extract(self, waveform, sample_rate=16000):
        """
        Extract WavLM embeddings from audio.
        
        Args:
            waveform: Audio samples (numpy array)
            sample_rate: Sampling rate (default: 16000)
        
        Returns:
            embeddings: 768-dimensional numpy array
        """
        self._ensure_loaded()
        
        # Preprocess audio
        inputs = self.processor(
            waveform,
            sampling_rate=sample_rate,
            return_tensors="pt",
            padding=True
        )
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Extract features
        with torch.no_grad():
            outputs = self.model(**inputs)
            
            # Get last hidden state and mean pool over time
            last_hidden_state = outputs.last_hidden_state  # [batch, time, 768]
            embeddings = torch.mean(last_hidden_state, dim=1)  # [batch, 768]
        
        # Convert to numpy
        embeddings_np = embeddings.cpu().numpy().squeeze()
        
        return embeddings_np
    
    def extract_batch(self, waveforms, sample_rate=16000):
        """
        Extract embeddings for multiple audio samples.
        
        Args:
            waveforms: List of audio samples
            sample_rate: Sampling rate
        
        Returns:
            embeddings: numpy array of shape [batch_size, 768]
        """
        self._ensure_loaded()
        
        all_embeddings = []
        
        for waveform in waveforms:
            emb = self.extract(waveform, sample_rate)
            all_embeddings.append(emb)
        
        return np.array(all_embeddings)
    
    def get_info(self):
        """Get model information."""
        return {
            'model_name': self.model_name,
            'embedding_dim': 768,
            'device': str(self.device),
            'loaded': self.model is not None
        }


if __name__ == '__main__':
    # Test the extractor
    import librosa
    
    print("Testing WavLM Extractor...")
    
    # Generate test audio
    duration = 3.0
    sr = 16000
    t = np.linspace(0, duration, int(sr * duration))
    audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
    
    # Extract features
    extractor = WavLMExtractor()
    embeddings = extractor.extract(audio, sr)
    
    print(f"✅ Extraction successful!")
    print(f"   Embedding shape: {embeddings.shape}")
    print(f"   Embedding mean: {embeddings.mean():.4f}")
    print(f"   Embedding std: {embeddings.std():.4f}")
    print(f"   Model info: {extractor.get_info()}")
