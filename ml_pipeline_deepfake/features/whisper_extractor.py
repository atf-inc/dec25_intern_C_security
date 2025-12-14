"""
Whisper-Small Feature Extractor for Deepfake Voice Detection

Purpose:
    Extract SEMANTIC and PROSODY features using OpenAI's Whisper-Small encoder.
    Unlike WavLM (acoustic), Whisper captures high-level linguistic patterns and
    speech timing that can reveal unnatural AI-generated speech patterns.

What Whisper Captures (Semantic/Prosody Artifacts):
    - Prosody mismatches (unnatural pitch contours, stress patterns)
    - Timing anomalies (pause durations, speech rate inconsistencies)
    - Linguistic coherence (semantic flow, contextual appropriateness)
    - Cross-modal alignment (how well audio matches expected speech patterns)
    - Attention patterns (where the model "focuses" can reveal synthesis artifacts)

Why This Complements WavLM:
    
    WavLM (Acoustic Expert):
    - Low-level: spectral, phase, waveform artifacts
    - Detects "how it sounds" (audio quality issues)
    - Catches vocoder/synthesis fingerprints
    
    Whisper (Semantic Expert):
    - High-level: meaning, prosody, timing
    - Detects "how it's spoken" (naturalness issues)
    - Catches unnatural speech patterns, rhythm anomalies
    
    FUSION BENEFIT:
    - WavLM: "This audio has spectral artifacts"
    - Whisper: "This speech has unnatural pauses and prosody"
    - Together: More robust detection across different deepfake types

Architecture:
    - Model: openai/whisper-small (244M parameters)
    - Encoder output: 768-dimensional embeddings
    - NO decoding (we don't need transcription)
    - CPU-compatible for MVP

Usage:
    extractor = WhisperFeatureExtractor()
    features = extractor.extract("path/to/audio.wav")
    # Returns: numpy array of shape (768,)
"""

import torch
import torchaudio
import numpy as np
from transformers import WhisperProcessor, WhisperModel
import warnings

warnings.filterwarnings("ignore")


class WhisperFeatureExtractor:
    """
    Extracts 768-dim semantic/prosody features from audio using Whisper-Small encoder.
    """
    
    def __init__(self, model_name="openai/whisper-small", device=None):
        """
        Initialize Whisper feature extractor.
        
        Args:
            model_name (str): HuggingFace model identifier
            device (str): 'cpu' or 'cuda' (defaults to CPU for MVP)
        """
        print(f"Loading Whisper model: {model_name}")
        
        # Set device (CPU by default for MVP)
        if device is None:
            self.device = torch.device("cpu")
        else:
            self.device = torch.device(device)
        
        # Load processor (handles audio preprocessing for Whisper)
        self.processor = WhisperProcessor.from_pretrained(model_name)
        
        # Load Whisper model (we only use the encoder, not decoder)
        self.model = WhisperModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()  # Frozen weights, no training
        
        print(f"✓ Whisper loaded on {self.device}")
        print(f"✓ Output dimension: 768 (encoder embeddings)")
    
    def load_audio(self, audio_path, target_sr=16000):
        """
        Load and preprocess audio file.
        
        Args:
            audio_path (str): Path to .wav audio file
            target_sr (int): Target sampling rate (Whisper expects 16kHz)
        
        Returns:
            np.ndarray: Audio waveform as numpy array
        """
        # Load audio using librosa (more reliable for various formats)
        import librosa
        waveform, sample_rate = librosa.load(audio_path, sr=target_sr, mono=True)
        
        return waveform
    
    def extract(self, audio_path):
        """
        Extract 768-dim semantic/prosody feature vector from audio file.
        
        Args:
            audio_path (str): Path to .wav audio file
        
        Returns:
            np.ndarray: Feature vector of shape (768,)
        """
        # Load and preprocess audio
        waveform = self.load_audio(audio_path)
        
        # Process audio into Whisper input format
        # The processor converts raw audio to log-mel spectrogram (80 mel bins)
        inputs = self.processor(
            waveform,
            sampling_rate=16000,
            return_tensors="pt"
        )
        
        # Move inputs to device
        input_features = inputs.input_features.to(self.device)
        
        # Extract encoder embeddings (no gradient computation)
        with torch.no_grad():
            # Get encoder outputs (we skip the decoder entirely)
            encoder_outputs = self.model.encoder(input_features)
        
        # encoder_outputs.last_hidden_state shape: (batch_size, sequence_length, 768)
        # sequence_length depends on audio duration (1500 frames for 30s audio)
        hidden_states = encoder_outputs.last_hidden_state
        
        # Aggregate over time dimension using mean pooling
        # This captures overall semantic/prosody patterns across the entire audio
        # Alternative strategies:
        #   - Max pooling: captures peak activations
        #   - Attention-weighted: learns importance (requires training)
        #   - First/last token: positional information
        features = torch.mean(hidden_states, dim=1).squeeze()
        
        # Convert to numpy array
        features_np = features.cpu().numpy()
        
        return features_np
    
    def extract_with_timing(self, audio_path):
        """
        Extract features WITH timing information (advanced).
        
        This method returns both:
        1. Aggregated 768-dim vector (like extract())
        2. Frame-level embeddings for temporal analysis
        
        Args:
            audio_path (str): Path to .wav audio file
        
        Returns:
            dict: {
                'aggregated': np.ndarray (768,),
                'frame_level': np.ndarray (num_frames, 768),
                'num_frames': int
            }
        """
        # Load and preprocess audio
        waveform = self.load_audio(audio_path)
        
        # Process audio
        inputs = self.processor(
            waveform,
            sampling_rate=16000,
            return_tensors="pt"
        )
        input_features = inputs.input_features.to(self.device)
        
        # Extract encoder embeddings
        with torch.no_grad():
            encoder_outputs = self.model.encoder(input_features)
        
        hidden_states = encoder_outputs.last_hidden_state  # (1, num_frames, 768)
        
        # Aggregated features (mean pooling)
        aggregated = torch.mean(hidden_states, dim=1).squeeze().cpu().numpy()
        
        # Frame-level features (for temporal analysis)
        frame_level = hidden_states.squeeze(0).cpu().numpy()  # (num_frames, 768)
        
        return {
            'aggregated': aggregated,
            'frame_level': frame_level,
            'num_frames': frame_level.shape[0]
        }
    
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
    Test the Whisper feature extractor on a sample audio file.
    """
    import os
    
    # Initialize extractor
    extractor = WhisperFeatureExtractor()
    
    # Example: Extract features from a single file
    audio_path = "data/real/sample_001.wav"
    
    if os.path.exists(audio_path):
        print(f"\nExtracting features from: {audio_path}")
        
        # Basic extraction
        features = extractor.extract(audio_path)
        print(f"\n✓ Feature extraction complete!")
        print(f"  Shape: {features.shape}")
        print(f"  Mean: {features.mean():.4f}")
        print(f"  Std: {features.std():.4f}")
        print(f"  Min: {features.min():.4f}")
        print(f"  Max: {features.max():.4f}")
        
        # Advanced: Extract with timing information
        print(f"\n--- Advanced: Timing Analysis ---")
        timing_features = extractor.extract_with_timing(audio_path)
        print(f"  Aggregated shape: {timing_features['aggregated'].shape}")
        print(f"  Frame-level shape: {timing_features['frame_level'].shape}")
        print(f"  Number of frames: {timing_features['num_frames']}")
        print(f"  (Each frame ≈ 20ms of audio)")
        
    else:
        print(f"\n⚠ Audio file not found: {audio_path}")
        print("  Please provide a valid audio file path to test.")
    
    # Example: Batch processing
    # audio_files = ["data/real/sample_001.wav", "data/fake/sample_001.wav"]
    # features_matrix = extractor.extract_batch(audio_files)
    # print(f"Batch features shape: {features_matrix.shape}")  # (2, 768)
