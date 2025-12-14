"""
DSP Feature Extractor for Deepfake Voice Detection

Purpose:
    Extract signal-level features using classical DSP techniques.
    These features capture physical impossibilities and statistical anomalies
    that neural TTS/vocoders often produce.

What DSP Features Catch (Physical Impossibilities):
    
    1. PITCH VARIANCE:
       - Real humans: Natural pitch fluctuations (breathing, emotion, fatigue)
       - AI voices: Often too smooth/stable or unnaturally erratic
       - Physical impossibility: Perfect pitch stability is inhuman
    
    2. ENERGY VARIANCE:
       - Real humans: Dynamic energy (emphasis, breathing, natural decay)
       - AI voices: Overly consistent energy levels across utterances
       - Physical impossibility: Constant vocal energy without variation
    
    3. SILENCE RATIO / PAUSE DENSITY:
       - Real humans: Natural pauses, breathing gaps, micro-silences
       - AI voices: Either too few pauses or mechanically regular pauses
       - Physical impossibility: Speech without breathing or with robotic timing

Why This Complements WavLM + Whisper:
    - WavLM: Learns acoustic patterns (complex, black-box)
    - Whisper: Learns semantic patterns (complex, black-box)
    - DSP: Explicit, interpretable, physics-based rules
    
    DSP features provide:
    - Interpretability (we know WHY a sample is flagged)
    - Robustness (hard to fool simple statistical checks)
    - Complementarity (catches different artifact types)

Architecture:
    - Library: librosa (audio analysis)
    - Output: Small feature vector (6 dimensions)
    - CPU-only, fast computation
    - No ML models, pure signal processing

Usage:
    extractor = DSPFeatureExtractor()
    features = extractor.extract("path/to/audio.wav")
    # Returns: numpy array of shape (6,)
"""


import librosa
import numpy as np
import warnings

warnings.filterwarnings("ignore")


class DSPFeatureExtractor:
    """
    Extracts 6-dim DSP features from audio using classical signal processing.
    """
    
    def __init__(self):
        """
        Initialize DSP feature extractor.
        No models to load - pure signal processing.
        """
        print("✓ DSP Feature Extractor initialized")
        print("✓ Output dimension: 6 (pitch + energy + silence features)")
    
    def load_audio(self, audio_path, sr=16000):
        """
        Load audio file.
        
        Args:
            audio_path (str): Path to audio file
            sr (int): Target sampling rate
        
        Returns:
            tuple: (waveform, sample_rate)
        """
        # Load audio with librosa (automatically resamples to sr)
        y, sr = librosa.load(audio_path, sr=sr, mono=True)
        return y, sr
    
    def extract_pitch_features(self, y, sr):
        """
        Extract pitch-related features.
        
        Catches: Unnatural pitch stability or erratic pitch in AI voices.
        
        Args:
            y (np.ndarray): Audio waveform
            sr (int): Sample rate
        
        Returns:
            dict: {
                'pitch_mean': float,
                'pitch_std': float,
                'pitch_range': float
            }
        """
        # Extract pitch using librosa's piptrack (pitch tracking)
        # Returns pitch estimates for each frame
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        
        # Get pitch values (filter out zeros/unvoiced frames)
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:  # Only voiced frames
                pitch_values.append(pitch)
        
        if len(pitch_values) > 0:
            pitch_values = np.array(pitch_values)
            pitch_mean = np.mean(pitch_values)
            pitch_std = np.std(pitch_values)  # Variance indicator
            pitch_range = np.max(pitch_values) - np.min(pitch_values)
        else:
            # Fallback if no pitch detected
            pitch_mean = 0.0
            pitch_std = 0.0
            pitch_range = 0.0
        
        return {
            'pitch_mean': pitch_mean,
            'pitch_std': pitch_std,      # LOW = too stable (AI-like)
            'pitch_range': pitch_range   # LOW = monotone (AI-like)
        }


    def extract_energy_features(self, y):
        """
        Extract energy-related features.
        
        Catches: Unnaturally consistent energy levels in AI voices.
        
        Args:
            y (np.ndarray): Audio waveform
        
        Returns:
            dict: {
                'energy_mean': float,
                'energy_std': float
            }
        """
        # Compute RMS energy per frame
        rms = librosa.feature.rms(y=y)[0]
        
        energy_mean = np.mean(rms)
        energy_std = np.std(rms)  # LOW = too consistent (AI-like)
        
        return {
            'energy_mean': energy_mean,
            'energy_std': energy_std     # LOW = robotic consistency
        }
    
    def extract_silence_features(self, y, sr, top_db=30):
        """
        Extract silence/pause-related features.
        
        Catches: Unnatural pause patterns (too few or too regular).
        
        Args:
            y (np.ndarray): Audio waveform
            sr (int): Sample rate
            top_db (int): Threshold for silence detection (dB below peak)
        
        Returns:
            dict: {
                'silence_ratio': float
            }
        """
        # Detect non-silent intervals
        intervals = librosa.effects.split(y, top_db=top_db)
        
        # Calculate total non-silent duration
        non_silent_duration = sum([end - start for start, end in intervals])
        total_duration = len(y)
        
        # Silence ratio = proportion of audio that is silent
        silence_ratio = 1.0 - (non_silent_duration / total_duration)
        
        return {
            'silence_ratio': silence_ratio  # Too LOW or Too HIGH = suspicious
        }
    
    def extract(self, audio_path):
        """
        Extract all DSP features from audio file.
        
        Args:
            audio_path (str): Path to audio file
        
        Returns:
            np.ndarray: Feature vector of shape (6,)
                [pitch_mean, pitch_std, pitch_range, 
                 energy_mean, energy_std, silence_ratio]
        """
        # Load audio
        y, sr = self.load_audio(audio_path)
        
        # Extract pitch features
        pitch_features = self.extract_pitch_features(y, sr)
        
        # Extract energy features
        energy_features = self.extract_energy_features(y)
        
        # Extract silence features
        silence_features = self.extract_silence_features(y, sr)
        
        # Combine into feature vector
        features = np.array([
            pitch_features['pitch_mean'],
            pitch_features['pitch_std'],
            pitch_features['pitch_range'],
            energy_features['energy_mean'],
            energy_features['energy_std'],
            silence_features['silence_ratio']
        ])
        
        return features
    
    def extract_with_labels(self, audio_path):
        """
        Extract features with human-readable labels (for debugging).
        
        Args:
            audio_path (str): Path to audio file
        
        Returns:
            dict: Feature dictionary with labels
        """
        features = self.extract(audio_path)
        
        return {
            'pitch_mean': features[0],
            'pitch_std': features[1],
            'pitch_range': features[2],
            'energy_mean': features[3],
            'energy_std': features[4],
            'silence_ratio': features[5]
        }
    
    def extract_batch(self, audio_paths):
        """
        Extract features from multiple audio files.
        
        Args:
            audio_paths (list): List of paths to audio files
        
        Returns:
            np.ndarray: Feature matrix of shape (num_files, 6)
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
    Test the DSP feature extractor on a sample audio file.
    """
    import os
    
    # Initialize extractor
    extractor = DSPFeatureExtractor()
    
    # Example: Extract features from a single file
    audio_path = "data/real/sample_001.wav"
    
    if os.path.exists(audio_path):
        print(f"\nExtracting DSP features from: {audio_path}")
        
        # Extract features
        features = extractor.extract(audio_path)
        print(f"\n✓ Feature extraction complete!")
        print(f"  Shape: {features.shape}")
        print(f"  Features: {features}")
        
        # Extract with labels (more readable)
        print(f"\n--- Feature Breakdown ---")
        labeled_features = extractor.extract_with_labels(audio_path)
        for name, value in labeled_features.items():
            print(f"  {name:20s}: {value:.4f}")
        
        # Interpretation hints
        print(f"\n--- Interpretation Hints ---")
        print(f"  Low pitch_std/pitch_range → Unnaturally stable pitch (AI-like)")
        print(f"  Low energy_std → Robotic energy consistency (AI-like)")
        print(f"  Extreme silence_ratio → Unnatural pause patterns")
        
    else:
        print(f"\n⚠ Audio file not found: {audio_path}")
        print("  Please provide a valid audio file path to test.")
    
    # Example: Batch processing
    # audio_files = ["data/real/sample_001.wav", "data/fake/sample_001.wav"]
    # features_matrix = extractor.extract_batch(audio_files)
    # print(f"Batch features shape: {features_matrix.shape}")  # (2, 6)
