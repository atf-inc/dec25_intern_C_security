"""
WavLM-Base-Plus Feature Extractor for Deepfake Voice Detection

Purpose:
    Extract acoustic features from audio using Microsoft's WavLM-Base-Plus model.
    WavLM is pre-trained on speech tasks and captures low-level acoustic artifacts
    that are useful for detecting AI-generated voices.

What WavLM Captures (Acoustic Artifacts):
    - Spectral inconsistencies (unnatural frequency patterns in AI voices)
    - Phase coherence issues (AI models sometimes produce phase artifacts)
    - Temporal dynamics (prosody, rhythm, natural speech variations)
    - Fine-grained acoustic textures (breathing, micro-pauses, vocal tract resonances)
    - Artifacts from vocoder/neural TTS synthesis

Architecture:
    - Model: microsoft/wavlm-base-plus (94M parameters)
    - Output: 768-dimensional feature vector per audio file
    - NO fine-tuning (frozen weights, feature extraction only)
    - CPU-compatible for MVP

Usage:
    extractor = WavLMFeatureExtractor()
    features = extractor.extract("path/to/audio.wav")
    # Returns: numpy array of shape (768,)
"""

import torch
import torchaudio
import numpy as np
from transformers import Wav2Vec2FeatureExtractor, WavLMModel
import warnings

warnings.filterwarnings("ignore")


class WavLMFeatureExtractor:
    """
    Extracts 768-dim acoustic features from audio using WavLM-Base-Plus.
    """
    
    def __init__(self, model_name="microsoft/wavlm-base-plus", device=None):
        """
        Initialize WavLM feature extractor.
        
        Args:
            model_name (str): HuggingFace model identifier
            device (str): 'cpu' or 'cuda' (defaults to CPU for MVP)
        """
        print(f"Loading WavLM model: {model_name}")
        
        # Set device (CPU by default for MVP)
        if device is None:
            self.device = torch.device("cpu")
        else:
            self.device = torch.device(device)
        
        # Load feature extractor (handles audio preprocessing)
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
        
        # Load WavLM model (frozen, no training)
        self.model = WavLMModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()  # Set to evaluation mode (no gradients)
        
        print(f"✓ WavLM loaded on {self.device}")
        print(f"✓ Output dimension: 768")
    
    def load_audio(self, audio_path, target_sr=16000):
        """
        Load and preprocess audio file.
        
        Args:
            audio_path (str): Path to .wav audio file
            target_sr (int): Target sampling rate (WavLM expects 16kHz)
        
        Returns:
            torch.Tensor: Audio waveform (1D tensor)
        """
        # Load audio using librosa (more reliable for various formats)
        import librosa
        waveform, sample_rate = librosa.load(audio_path, sr=target_sr, mono=True)
        
        # Convert to torch tensor
        waveform = torch.from_numpy(waveform).float()
        
        return waveform
    
    def extract(self, audio_path):
        """
        Extract 768-dim feature vector from audio file.
        
        Args:
            audio_path (str): Path to .wav audio file
        
        Returns:
            np.ndarray: Feature vector of shape (768,)
        """
        # Load and preprocess audio
        waveform = self.load_audio(audio_path)
        
        # Prepare input for WavLM (normalize and convert to model input format)
        inputs = self.feature_extractor(
            waveform.numpy(),
            sampling_rate=16000,
            return_tensors="pt",
            padding=True
        )
        
        # Move inputs to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Extract features (no gradient computation)
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Get hidden states from last layer
        # Shape: (batch_size, sequence_length, 768)
        hidden_states = outputs.last_hidden_state
        
        # Aggregate over time dimension using mean pooling
        # This gives us a single 768-dim vector representing the entire audio
        # Alternative: max pooling, attention-weighted pooling (mean is simplest for MVP)
        features = torch.mean(hidden_states, dim=1).squeeze()
        
        # Convert to numpy array
        features_np = features.cpu().numpy()
        
        return features_np
    
    def extract_batch(self, audio_paths):
        """
        Extract features from multiple audio files.
        
        Args:
            audio_paths (list): List of paths to .wav files
        
        Returns:
            np.ndarray: Feature matrix of shape (num_files, 768)
        """
        features_list = []
        
        for i, audio_path in enumerate(audio_paths):
            print(f"Processing {i+1}/{len(audio_paths)}: {audio_path}")
            features = self.extract(audio_path)
            features_list.append(features)
        
        # Stack into matrix
        features_matrix = np.vstack(features_list)
        
        return features_matrix


# ============================================================================
# Example Usage (for testing)
# ============================================================================

if __name__ == "__main__":
    """
    Test the WavLM feature extractor on a sample audio file.
    """
    import os
    
    # Initialize extractor
    extractor = WavLMFeatureExtractor()
    
    # Example: Extract features from a single file
    # Replace with your actual audio path
    audio_path = "data/real/sample_001.wav"
    
    if os.path.exists(audio_path):
        print(f"\nExtracting features from: {audio_path}")
        features = extractor.extract(audio_path)
        
        print(f"\n✓ Feature extraction complete!")
        print(f"  Shape: {features.shape}")
        print(f"  Mean: {features.mean():.4f}")
        print(f"  Std: {features.std():.4f}")
        print(f"  Min: {features.min():.4f}")
        print(f"  Max: {features.max():.4f}")
    else:
        print(f"\n⚠ Audio file not found: {audio_path}")
        print("  Please provide a valid audio file path to test.")
    
    # Example: Batch processing
    # audio_files = ["data/real/sample_001.wav", "data/real/sample_002.wav"]
    # features_matrix = extractor.extract_batch(audio_files)
    # print(f"Batch features shape: {features_matrix.shape}")  # (2, 768)
