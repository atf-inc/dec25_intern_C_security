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

