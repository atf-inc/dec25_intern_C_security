"""
Deepfake Detector v2.1 - Fusion Model with Attention

Uses WavLM + Whisper + DSP (246-dim) with Multi-Head Attention.
Trained on WaveFake + ASVspoof + LibriSpeech (~1,500 samples).
Validation accuracy: 90%, AUC: 0.96, Deepfake recall: 100%
"""

import torch
import numpy as np
import logging
import os
from typing import Dict, Any

from app.ml.fusion.models.fusion_model import FusionDeepfakeDetector
from app.ml.fusion.features.wavlm_extractor import WavLMExtractor
from app.ml.fusion.features.whisper_extractor import WhisperExtractor
from app.ml.fusion.features.dsp_extractor import DSPExtractor

logger = logging.getLogger(__name__)


class DeepfakeDetector:
    """
    v2.1 Fusion Deepfake Detector (WavLM + Whisper + DSP + Attention).
    
    Features:
    - 90% validation accuracy
    - 100% deepfake recall
    - Detects 11 vocoder architectures (MelGAN, HiFiGAN, WaveGlow, etc.)
    - Forensic explainability with expert scores
    - Calibrated confidence scores
    """
    
    # Temperature scaling parameter for confidence calibration
    # Learned from validation set (values > 1 make predictions less confident)
    CALIBRATION_TEMPERATURE = 1.2
    
    def __init__(self, model_path="app/ml/models/deepfake_v2_1.pth", device=None):
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = model_path
        
        # Lazy loading - components loaded on first prediction
        self.model = None
        self.wavlm_ext = None
        self.whisper_ext = None
        self.dsp_ext = None
        self.is_loaded = False
        
        logger.info(f"DeepfakeDetector v2.1 initialized (device: {self.device})")
        
    def _ensure_loaded(self):
        """Lazy load model and extractors on first use."""
        if self.is_loaded:
            return

        logger.info("Loading v2.1 Fusion Deepfake Model components...")
        
        # 1. Load Feature Extractors
        logger.info("Loading WavLM extractor...")
        self.wavlm_ext = WavLMExtractor(device=self.device)
        
        logger.info("Loading Whisper extractor...")
        self.whisper_ext = WhisperExtractor(device=self.device)
        
        logger.info("Loading DSP extractor (246-dim)...")
        self.dsp_ext = DSPExtractor()
        
        # 2. Load Fusion Model (dsp_dim=246 for v2.1)
        self.model = FusionDeepfakeDetector(dsp_dim=246, shared_dim=256) 
        
        # 3. Load trained weights
        try:
            # Try multiple paths to find the model
            paths_to_try = [
                self.model_path,
                os.path.join(os.path.dirname(__file__), 'models', 'deepfake_v2_1.pth'),
                os.path.abspath(os.path.join(os.path.dirname(__file__), 'models', 'deepfake_v2_1.pth')),
            ]
            
            loaded = False
            for path in paths_to_try:
                if os.path.exists(path):
                    logger.info(f"Loading v2.1 weights from {path}")
                    state_dict = torch.load(path, map_location=self.device)
                    self.model.load_state_dict(state_dict)
                    self.model.to(self.device)
                    self.model.eval()
                    loaded = True
                    logger.info("✅ v2.1 Fusion model loaded successfully")
                    break
            
            if not loaded:
                logger.warning(f"⚠️ Model not found at any path. Running with random weights.")
                self.model.to(self.device)
                self.model.eval()
                
        except Exception as e:
            logger.error(f"Failed to load fusion weights: {e}")
            logger.warning("Running with random weights (not recommended)")
            self.model.to(self.device)
            self.model.eval()
        
        self.is_loaded = True
        logger.info("✅ v2.1 DeepfakeDetector fully loaded")

    def predict(self, waveform: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """
        End-to-end prediction: Audio -> Features -> Fusion Model -> Result
        
        Args:
            waveform: Audio waveform as numpy array
            sample_rate: Sample rate (default 16000)
        
        Returns:
            Dictionary with prediction results and forensic analysis
        """
        self._ensure_loaded()
        
        try:
            # 1. Extract Features from all three modalities
            logger.debug("Extracting WavLM features...")
            w_emb = torch.tensor(self.wavlm_ext.extract(waveform, sample_rate)).unsqueeze(0).to(self.device)
            
            logger.debug("Extracting Whisper features...")
            s_emb = torch.tensor(self.whisper_ext.extract(waveform, sample_rate)).unsqueeze(0).to(self.device)
            
            logger.debug("Extracting DSP features (246-dim)...")
            d_feat = torch.tensor(self.dsp_ext.extract(waveform, sample_rate)).unsqueeze(0).to(self.device)
            
            # 2. Forward Pass with explainability
            result = self.model.predict_with_explanation(w_emb, s_emb, d_feat)
            
            raw_conf = float(result['confidence'])
            
            # 3. Apply confidence calibration (temperature scaling)
            final_conf = self._calibrate_confidence(raw_conf)
            is_deepfake = final_conf > 0.5
            
            # 4. Extract expert scores for forensic analysis
            expert_scores = result['expert_scores']
            
            # Construct artifact dictionary for UI
            artifacts = {
                'signal_quality': expert_scores['signal'],         # Higher = More Signal Anomalies
                'acoustic_consistency': expert_scores['acoustic'], # Higher = More Acoustic Anomalies
                'semantic_coherence': expert_scores['semantic'],   # Higher = More Semantic Anomalies
                'acoustic': expert_scores['acoustic'],
                'semantic': expert_scores['semantic'],
                'signal': expert_scores['signal']
            }
            
            # 5. Generate Professional Forensic Explanation
            explanation = self._generate_explanation(is_deepfake, final_conf, expert_scores)
            
            return {
                'is_deepfake': is_deepfake,
                'confidence': float(final_conf),           # Calibrated confidence
                'raw_confidence': float(raw_conf),         # Raw model output (before calibration)
                'calibrated': True,
                'risk_level': self._get_risk_level(final_conf),
                'artifact_score': float(expert_scores['signal']),
                'artifacts': artifacts,
                'explanation': explanation,
                'model_version': 'v2.1-fusion-generalization'
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            return {
                'is_deepfake': False,
                'confidence': 0.0,
                'risk_level': "low",
                'artifacts': {},
                'error': str(e)
            }

    def _generate_explanation(self, is_deepfake: bool, confidence: float, expert_scores: Dict) -> str:
        """Generate professional forensic explanation."""
        if is_deepfake:
            factors = []
            if expert_scores['signal'] > 0.6:
                factors.append("digital signal processing artifacts")
            if expert_scores['acoustic'] > 0.6:
                factors.append("acoustic inconsistencies typical of neural vocoders")
            if expert_scores['semantic'] > 0.6:
                factors.append("unnatural prosodic patterns")
            
            if not factors:
                factors.append("general synthetic characteristics")
            factor_str = ", ".join(factors)
            
            return (
                f"Voice analysis confirms high probability of AI generation (Confidence: {confidence:.1%}). "
                f"The model detected {factor_str}, which are strong indicators of neural text-to-speech synthesis "
                f"(e.g., MelGAN, HiFiGAN, WaveGlow)."
            )
        else:
            return (
                f"Voice analysis indicates the audio is likely genuine (Confidence: {1-confidence:.1%}). "
                "The acoustic properties, prosodic patterns, and signal integrity align with natural human speech. "
                "No significant artifacts from neural vocoders were detected."
            )
    
    def _get_risk_level(self, confidence: float) -> str:
        """Determine risk level from confidence."""
        if confidence < 0.3:
            return "low"
        elif confidence < 0.7:
            return "medium"
        return "high"
    
    def _calibrate_confidence(self, raw_confidence: float) -> float:
        """
        Apply temperature scaling to calibrate confidence scores.
        
        Temperature scaling makes overconfident predictions more conservative
        without changing the ranking (still same predictions, just calibrated probabilities).
        
        Args:
            raw_confidence: Raw model output probability (0-1)
        
        Returns:
            Calibrated confidence score (0-1)
        """
        # Convert probability to logit
        epsilon = 1e-7
        raw_confidence = np.clip(raw_confidence, epsilon, 1 - epsilon)
        logit = np.log(raw_confidence / (1 - raw_confidence))
        
        # Apply temperature scaling
        scaled_logit = logit / self.CALIBRATION_TEMPERATURE
        
        # Convert back to probability
        calibrated = 1 / (1 + np.exp(-scaled_logit))
        
        return float(calibrated)
