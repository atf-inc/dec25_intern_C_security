"""
Whisper Feature Extractor - Semantic Expert

Extracts 384-dimensional embeddings from audio using OpenAI's Whisper-Small encoder.
Captures semantic-acoustic relationship and prosody patterns.
"""

import torch
import numpy as np
from transformers import WhisperModel, WhisperProcessor
import logging

logger = logging.getLogger(__name__)


class WhisperExtractor:
    """
    Semantic Expert: Analyzes linguistic content vs. audio delivery.
    
    Detects:
    - Prosody mismatch (flat emotion during exciting sentence)
    - Unnatural pauses between words
    - Stress pattern errors
    - Intonation inconsistencies
    
    Key Insight: Modern deepfakes sound real but lack emotional coherence!
    
    Note: Whisper-Small encoder outputs 768-dim (not 384 as initially planned)
    """
    
    def __init__(self, model_name="openai/whisper-small", device=None):
        """
        Initialize Whisper extractor.
        
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
        
        logger.info(f"Initializing Whisper Extractor on {self.device}")
        
        # Lazy loading
        self.model = None
        self.processor = None
    
    def _ensure_loaded(self):
        """Load model if not already loaded."""
        if self.model is not None:
            return
        
        logger.info(f"Loading Whisper model: {self.model_name}")
        
        try:
            self.processor = WhisperProcessor.from_pretrained(self.model_name)
            
            # Load with optimizations
            if self.device.type == "cuda":
                self.model = WhisperModel.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16
                ).to(self.device)
            else:
                self.model = WhisperModel.from_pretrained(self.model_name).to(self.device)
            
            self.model.eval()
            logger.info("Whisper model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def extract(self, waveform, sample_rate=16000):
        """
        Extract Whisper encoder embeddings from audio.
        
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
            return_tensors="pt"
        )
        
        # Move to device
        input_features = inputs.input_features.to(self.device)
        
        # Extract features using encoder only (semantic features)
        with torch.no_grad():
            encoder_outputs = self.model.encoder(input_features)
            
            # Get last hidden state and mean pool over time
            last_hidden_state = encoder_outputs.last_hidden_state  # [batch, time, 384]
            embeddings = torch.mean(last_hidden_state, dim=1)  # [batch, 384]
        
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
    import numpy as np
    
    print("Testing Whisper Extractor...")
    
    # Generate test audio
    duration = 3.0
    sr = 16000
    t = np.linspace(0, duration, int(sr * duration))
    audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
    
    # Extract features
    extractor = WhisperExtractor()
    embeddings = extractor.extract(audio, sr)
    
    print(f"✅ Extraction successful!")
    print(f"   Embedding shape: {embeddings.shape}")
    print(f"   Embedding mean: {embeddings.mean():.4f}")
    print(f"   Embedding std: {embeddings.std():.4f}")
    print(f"   Model info: {extractor.get_info()}")
