
import torch
import numpy as np
import logging
import os
from pathlib import Path
from typing import Dict, Any

from app.ml.fusion.models.fusion_model import FusionDeepfakeDetector
from app.ml.fusion.features.wavlm_extractor import WavLMExtractor
from app.ml.fusion.features.whisper_extractor import WhisperExtractor
from app.ml.fusion.features.dsp_extractor import DSPExtractor

logger = logging.getLogger(__name__)

class DeepfakeDetector:
    """
    Wrapper for the Fusion Deepfake Detector (WavLM + Whisper + DSP + Attention).
    """
    
    def __init__(self, model_path="app/ml/models/deepfake_v2_1.pth", device=None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = model_path
        
        # Lazy loading
        self.model = None
        self.wavlm_ext = None
        self.whisper_ext = None
        self.dsp_ext = None
        self.is_trained = False # Will be true after loading
        
    def _ensure_loaded(self):
        if self.model is not None:
            return

        logger.info("Loading Fusion Deepfake Model components (v2.0 - 246 dim DSP)...")
        
        # 1. Load Extractors
        self.wavlm_ext = WavLMExtractor(device=self.device)
        self.whisper_ext = WhisperExtractor(device=self.device)
        self.dsp_ext = DSPExtractor()
        
        # 2. Load Model
        # shared_dim=256 matches the training config
        self.model = FusionDeepfakeDetector(dsp_dim=246, shared_dim=256) 
        
        try:
            # Check absolute path first, then relative
            if os.path.exists(self.model_path):
                path = self.model_path
            else:
                # Fallback to absolute path relative to this file's directory
                # models/ is in the same directory as deepfake_model.py's parent? 
                # No, deepfake_model.py is in app/ml
                # models is in app/ml/models
                base_name = os.path.basename(self.model_path)
                path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'models', base_name))
            
            logger.info(f"Loading weights from {path}")
            state_dict = torch.load(path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
            self.is_trained = True
            logger.info("Fusion model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load fusion weights: {e}")
            logger.warning("Running in untrained mode (random weights)")
            self.model.to(self.device)
            self.is_trained = False

    def predict(self, waveform: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """
        End-to-end prediction: Audio -> Features -> Fusion Model -> Result
        """
        self._ensure_loaded()
        
        # 1. Extract Features
        try:
            # Features need to be tensors on device
            w_emb = torch.tensor(self.wavlm_ext.extract(waveform, sample_rate)).unsqueeze(0).to(self.device)
            s_emb = torch.tensor(self.whisper_ext.extract(waveform, sample_rate)).unsqueeze(0).to(self.device)
            d_feat = torch.tensor(self.dsp_ext.extract(waveform, sample_rate)).unsqueeze(0).to(self.device)
            
            # 2. Forward Pass
            # Use explainability method to get detailed scores
            result = self.model.predict_with_explanation(w_emb, s_emb, d_feat)
            
            final_conf = float(result['confidence'])
            is_deepfake = final_conf > 0.5
            
            # Map expert scores for UI
            expert_scores = result['expert_scores']
            
            # Construct artifact dictionary with clean keys for Frontend v2.1
            # We map 1.0 (Fake) -> 0.0 (Consistency) for user-friendly display if needed, 
            # but usually "Score" implies "Defect Score" in security contexts.
            # Let's keep it as "Anomaly Score" (Higher = More Fake/Anomaly).
            artifacts = {
                'signal_quality': expert_scores['signal'],       # Higher = More Signal Anomalies
                'acoustic_consistency': expert_scores['acoustic'], # Higher = More Acoustic Anomalies
                'semantic_coherence': expert_scores['semantic']    # Higher = More Semantic Anomalies
            }
            

            # Generate Professional Explanation
            if is_deepfake:
                factors = []
                if expert_scores['signal'] > 0.6: factors.append("digital signal processing artifacts")
                if expert_scores['acoustic'] > 0.6: factors.append("acoustic inconsistencies")
                if expert_scores['semantic'] > 0.6: factors.append("unnatural semantic patterns")
                
                if not factors: factors.append("general synthetic characteristics")
                factor_str = ", ".join(factors)
                
                explanation = (
                    f"Voice analysis confirms high probability of AI generation (Confidence: {final_conf:.1%}). "
                    f"The model detected {factor_str}, which are strong indicators of neural text-to-speech synthesis."
                )
            else:
                explanation = (
                    f"Voice analysis indicates the audio is likely genuine (Confidence: {final_conf:.1%}). "
                    "The acoustic properties and signal integrity align with natural human speech patterns."
                )

            # Construct response
            return {
                'is_deepfake': is_deepfake,
                'confidence': float(final_conf),
                'risk_level': self._get_risk_level(final_conf),
                'artifact_score': float(expert_scores['signal']), # Use DSP score as "Artifact Score"
                'artifacts': artifacts,
                'explanation': explanation
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            # Fallback
            return {
                'is_deepfake': False,
                'confidence': 0.0,
                'risk_level': "low",
                'error': str(e)
            }

    def _get_risk_level(self, confidence: float) -> str:
        if confidence < 0.3: return "low"
        if confidence < 0.7: return "medium"
        return "high"
