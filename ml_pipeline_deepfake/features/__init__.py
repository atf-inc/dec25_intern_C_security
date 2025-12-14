"""
Feature Extraction Module

Contains three expert feature extractors:
- WavLM: Acoustic features (768-dim)
- Whisper: Semantic/prosody features (768-dim)
- DSP: Signal processing features (6-dim)
"""

from .wavlm_extractor import WavLMFeatureExtractor
from .whisper_extractor import WhisperFeatureExtractor
from .dsp_features import DSPFeatureExtractor

__all__ = [
    'WavLMFeatureExtractor',
    'WhisperFeatureExtractor',
    'DSPFeatureExtractor'
]
