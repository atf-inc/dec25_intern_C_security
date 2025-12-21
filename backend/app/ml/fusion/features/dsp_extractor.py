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
    Signal Expert: Advanced Signal Analysis.
    Extracts 246-dim vector: MFCCs (20), Deltas, Delta-Deltas, and their statistics + Spectral features.
    """
    
    def __init__(self):
        """Initialize DSP extractor."""
        logger.info("Initializing Advanced DSP Extractor")
        # No specific features list needed, implicitly defined by size
        self.input_dim = 246
    
    def extract(self, audio, sr=16000):
        """
        Extract advanced DSP features: MFCCs + Deltas + Statistics.
        Returns a rich feature vector (246-dim).
        """
        import librosa
        import numpy as np
        from scipy.stats import skew, kurtosis
        
        try:
            # Ensure float32
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

            # 1. MFCCs (20 coefficients)
            # Center=False to align frames better with short clips if needed, but default is fine
            mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=20)
            
            # 2. Deltas (First & Second Order)
            delta1 = librosa.feature.delta(mfcc)
            delta2 = librosa.feature.delta(mfcc, order=2)
            
            # 3. Compute Statistics (Mean, Std, Skew, Kurtosis) per coefficient across time
            # Shape: (n_mfcc, time) -> (n_mfcc * 4) features
            features = []
            
            # Helper to add stats
            def add_stats(matrix):
                features.extend(np.mean(matrix, axis=1))
                features.extend(np.std(matrix, axis=1))
                features.extend(skew(matrix, axis=1))
                features.extend(kurtosis(matrix, axis=1))
            
            add_stats(mfcc)   # 20 * 4 = 80
            add_stats(delta1) # 20 * 4 = 80
            add_stats(delta2) # 20 * 4 = 80
            
            # 4. Additional Robust Features (Mean, Std)
            
            # Zero Crossing Rate
            zcr = librosa.feature.zero_crossing_rate(audio)
            features.extend([np.mean(zcr), np.std(zcr)]) # +2
            
            # Spectral Centroid
            cent = librosa.feature.spectral_centroid(y=audio, sr=sr)
            features.extend([np.mean(cent), np.std(cent)]) # +2
            
            # Spectral Rolloff
            rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
            features.extend([np.mean(rolloff), np.std(rolloff)]) # +2
            
            # Total so far: 240 + 6 = 246 features
            
            return np.array(features, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"DSP Extraction Error: {e}")
            # Return zeros of expected size
            return np.zeros(self.input_dim, dtype=np.float32)

    def extract_batch(self, waveforms, sample_rate=16000):
        """Extract features for multiple audio samples."""
        all_features = []
        for waveform in waveforms:
            all_features.append(self.extract(waveform, sample_rate))
        return np.array(all_features)
    
    def get_info(self):
        return {
            'feature_dim': self.input_dim,
            'description': 'Advanced MFCC+Stat features (246-dim)'
        }

if __name__ == '__main__':
    # Test
    print("Testing DSP Extractor...")
    audio = np.random.normal(0, 1, 16000*3).astype(np.float32)
    extractor = DSPExtractor()
    feats = extractor.extract(audio)
    print(f"Feature shape: {feats.shape}")
    assert feats.shape[0] == 246, f"Expected 246, got {feats.shape[0]}"
    print("✅ Extraction successful!")
