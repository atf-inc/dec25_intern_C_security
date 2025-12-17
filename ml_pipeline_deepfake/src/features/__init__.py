"""
Feature Extractors for Fusion Deepfake Detection

Three expert branches:
1. WavLM - Acoustic Expert (768-dim)
2. Whisper - Semantic Expert (768-dim)
3. DSP - Signal Expert (8-dim)

Total: 1544-dimensional feature vector
"""

from .wavlm_extractor import WavLMExtractor
from .whisper_extractor import WhisperExtractor
from .dsp_extractor import DSPExtractor

__all__ = ['WavLMExtractor', 'WhisperExtractor', 'DSPExtractor']
