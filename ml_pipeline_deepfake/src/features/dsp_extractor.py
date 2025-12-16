"""
DSP Feature Extractor - Signal Expert

Extracts 8-dimensional feature vector using traditional signal processing.
Detects impossible physics and mathematical anomalies.
"""

import numpy as np
import librosa
import logging

logger = logging.getLogger(__name__)


class DSPExtractor:
    """
    Signal Expert: Mathematical signal analysis.
    
    Detects:
    - Impossible physics (zero breath sounds)
    - Perfect pitch stability (too perfect = fake)
    - Spectral anomalies
    - Phase inconsistencies
    
    Features (8-dimensional):
    1. Spectral Flatness
    2. Autocorrelation Peak
    3. High-Frequency Energy
    4. Zero-Crossing Rate Variance
    5. Pitch Variance (F0)
    6. Formant Stability
    7. Mel-Spectrogram Variance
    8. Phase Coherence
    """
    
    def __init__(self):
        """Initialize DSP extractor."""
        logger.info("Initializing DSP Extractor")
        self.feature_names = [
            'spectral_flatness',
            'autocorr_peak',
            'high_freq_energy',
            'zcr_variance',
            'pitch_variance',
            'formant_stability',
            'mel_variance',
            'phase_coherence'
        ]
    
    def extract(self, waveform, sample_rate=16000):
        """
        Extract DSP features from audio.
        
        Args:
            waveform: Audio samples (numpy array)
            sample_rate: Sampling rate (default: 16000)
        
        Returns:
            features: 8-dimensional numpy array
        """
        features = {}
        
        # 1. Spectral Flatness
        # Measures how "noise-like" vs "tone-like" the signal is
        # Synthetic speech often has unusual spectral flatness
        spectral_flatness = librosa.feature.spectral_flatness(y=waveform)[0]
        features['spectral_flatness'] = float(np.mean(spectral_flatness))
        
        # 2. Autocorrelation Peak
        # Detects unnatural periodicity in synthetic speech
        autocorr = librosa.autocorrelate(waveform)
        if len(autocorr) > 1:
            end_idx = min(100, len(autocorr))
            slice_ = autocorr[1:end_idx]
            features['autocorr_peak'] = float(np.max(slice_)) if len(slice_) > 0 else 0.0
        else:
            features['autocorr_peak'] = 0.0
        
        # 3. High-Frequency Energy
        # Vocoders often have artifacts above 8kHz
        stft = librosa.stft(waveform)
        high_freq_start = len(stft) // 2
        high_freq_energy = np.mean(np.abs(stft[high_freq_start:, :]))
        features['high_freq_energy'] = float(high_freq_energy)
        
        # 4. Zero-Crossing Rate Variance
        # Synthetic speech is often too regular
        zcr = librosa.feature.zero_crossing_rate(waveform)[0]
        features['zcr_variance'] = float(np.var(zcr))
        
        # 5. Pitch Variance (F0)
        # Real speech has natural pitch variation
        # Synthetic speech can be too stable
        try:
            f0 = librosa.yin(waveform, fmin=50, fmax=400, sr=sample_rate)
            valid_f0 = f0[f0 > 0]
            if len(valid_f0) > 0:
                features['pitch_variance'] = float(np.var(valid_f0))
            else:
                features['pitch_variance'] = 0.0
        except:
            features['pitch_variance'] = 0.0
        
        # 6. Formant Stability
        # Measures stability of vocal tract resonances
        # Synthetic speech can have unnatural formant transitions
        mfccs = librosa.feature.mfcc(y=waveform, sr=sample_rate, n_mfcc=13)
        formant_mfccs = mfccs[1:4, :]  # First 3 MFCCs relate to formants
        features['formant_stability'] = float(np.std(formant_mfccs))
        
        # 7. Mel-Spectrogram Variance
        # Measures overall spectral variation
        # Synthetic speech can have unusual spectral dynamics
        mel_spec = librosa.feature.melspectrogram(y=waveform, sr=sample_rate)
        features['mel_variance'] = float(np.var(mel_spec))
        
        # 8. Phase Coherence
        # Measures phase consistency across time
        # Neural vocoders can have phase artifacts
        stft = librosa.stft(waveform)
        phase = np.angle(stft)
        if phase.shape[1] > 1:
            phase_diff = np.diff(phase, axis=1)
            features['phase_coherence'] = float(np.mean(np.abs(phase_diff)))
        else:
            features['phase_coherence'] = 0.0
        
        # Convert to numpy array in consistent order
        feature_vector = np.array([features[name] for name in self.feature_names])
        
        return feature_vector
    
    def extract_batch(self, waveforms, sample_rate=16000):
        """
        Extract features for multiple audio samples.
        
        Args:
            waveforms: List of audio samples
            sample_rate: Sampling rate
        
        Returns:
            features: numpy array of shape [batch_size, 8]
        """
        all_features = []
        
        for waveform in waveforms:
            features = self.extract(waveform, sample_rate)
            all_features.append(features)
        
        return np.array(all_features)
    
    def get_feature_names(self):
        """Get list of feature names."""
        return self.feature_names
    
    def get_info(self):
        """Get extractor information."""
        return {
            'feature_dim': 8,
            'feature_names': self.feature_names,
            'description': 'Traditional signal processing features'
        }


if __name__ == '__main__':
    # Test the extractor
    print("Testing DSP Extractor...")
    
    # Generate test audio
    duration = 3.0
    sr = 16000
    t = np.linspace(0, duration, int(sr * duration))
    audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
    
    # Extract features
    extractor = DSPExtractor()
    features = extractor.extract(audio, sr)
    
    print(f"✅ Extraction successful!")
    print(f"   Feature shape: {features.shape}")
    print(f"\n   Feature values:")
    for name, value in zip(extractor.get_feature_names(), features):
        print(f"   {name:20s}: {value:.6f}")
    print(f"\n   Extractor info: {extractor.get_info()}")
