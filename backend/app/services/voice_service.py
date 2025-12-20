
import time
import logging
import os
import tempfile
from typing import Dict, Any
import torch
import numpy as np

# Import your ML components
from ..ml.wavlm_extractor import WavLMFeatureExtractor
from ..ml.whisper_extractor import WhisperFeatureExtractor
from ..ml.dsp_features import DSPFeatureExtractor
from ..ml.fusion_model import DeepfakeFusionModel

from ..utils.audio_utils import (
    load_and_preprocess_audio,
    compute_audio_hash,
    validate_audio_file,
    convert_to_wav,
    extract_audio_features
)
from ..db.crud_voice import (
    create_voice_scan,
    get_voice_scan_by_hash
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class VoiceAnalysisService:
    """Service for analyzing voice files using multi-modal fusion deepfake detection."""
    
    def __init__(self):
    # <<<<<<< HEAD
    #     # """Initialize the service with ML model."""
    #     # logger.info("Initializing VoiceAnalysisService...")
    #     # self.detector = DeepfakeDetector()
    #     # self.model_version = "v2.1-fusion-generalization"
    #     # logger.info("VoiceAnalysisService initialized successfully")
    # =======
        """Initialize the service with your trained fusion model."""
        logger.info("Initializing VoiceAnalysisService with Fusion Model...")
        
        # Initialize feature extractors
        try:
            logger.info("Loading WavLM extractor...")
            self.wavlm_extractor = WavLMFeatureExtractor()
            logger.info("✅ WavLM extractor loaded")
            
            logger.info("Loading Whisper extractor...")
            self.whisper_extractor = WhisperFeatureExtractor()
            logger.info("✅ Whisper extractor loaded")
            
            logger.info("Loading DSP extractor...")
            self.dsp_extractor = DSPFeatureExtractor()
            logger.info("✅ DSP extractor loaded")
            
        except Exception as e:
            logger.error(f"Failed to load extractors: {e}")
            raise
        
        # Initialize fusion model
        try:
            logger.info("Loading Fusion Model...")
            self.model = DeepfakeFusionModel(
                wavlm_dim=768,
                whisper_dim=768,
                dsp_dim=6,
                hidden_dim=256,
                dropout=0.3
            )
            
            # Load trained checkpoint
            checkpoint_path = os.path.join("checkpoints", "fusion_model.pth")
            
            if os.path.exists(checkpoint_path):
                logger.info(f"Loading checkpoint from {checkpoint_path}")
                self.model.load_state_dict(
                    torch.load(checkpoint_path, map_location='cpu')
                )
                self.model.eval()
                logger.info("✅ Fusion model checkpoint loaded successfully!")
                self.model_loaded = True
            else:
                logger.warning(f"⚠️ Checkpoint not found at {checkpoint_path}")
                logger.warning("Model will use random weights (not recommended for production)")
                self.model_loaded = False
            
            self.device = torch.device('cpu')  # Use CPU for now
            self.model.to(self.device)
            
        except Exception as e:
            logger.error(f"Failed to load fusion model: {e}")
            raise
        
        self.model_version = "v1.0-fusion-wavlm-whisper-dsp"
        logger.info(f"✅ VoiceAnalysisService initialized successfully (version: {self.model_version})")
    # >>>>>>> origin/develop
    
    
    async def analyze_voice(
        self, 
        file_bytes: bytes, 
        filename: str,
        db: Session = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze voice file using multi-modal fusion approach.
        
        Args:
            file_bytes: Raw audio file bytes
            filename: Original filename
            db: Database session (optional, for caching)
            use_cache: Whether to check cache first
        
        Returns:
            Analysis result dictionary
        """
        start_time = time.time()
        
        # Step 1: Compute hash for caching
        file_hash = compute_audio_hash(file_bytes)
        
        # Step 2: Check cache if enabled
        # CRITICAL FIX: Only use cache if model version matches!
        if use_cache and db is not None:
            cached_result = get_voice_scan_by_hash(db, file_hash)
            if cached_result and cached_result.model_version == self.model_version:
                logger.info(f"Cache hit for file hash: {file_hash} (Version: {cached_result.model_version})")
                return {
                    "cached": True,
                    **cached_result.to_dict()
                }
        
        # Step 3: Validate audio file
        is_valid, error_msg = validate_audio_file(file_bytes)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Step 4: Save to temporary file for processing
        temp_path = None
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_path = temp_file.name
                
                # Convert to WAV if needed
                if not filename.lower().endswith('.wav'):
                    logger.info(f"Converting {filename} to WAV format")
                    file_format = filename.split('.')[-1].lower()
                    wav_bytes = convert_to_wav(file_bytes, file_format)
                    temp_file.write(wav_bytes)
                else:
                    temp_file.write(file_bytes)
            
            # Step 5: Extract features using your extractors
            logger.info(f"Extracting features from {filename}")
            
            try:
                wavlm_feat = self.wavlm_extractor.extract(temp_path)
                logger.info(f"✅ WavLM features extracted: {wavlm_feat.shape}")
            except Exception as e:
                logger.error(f"WavLM extraction failed: {e}")
                raise ValueError(f"Failed to extract WavLM features: {e}")
            
            try:
                whisper_feat = self.whisper_extractor.extract(temp_path)
                logger.info(f"✅ Whisper features extracted: {whisper_feat.shape}")
            except Exception as e:
                logger.error(f"Whisper extraction failed: {e}")
                raise ValueError(f"Failed to extract Whisper features: {e}")
            
            try:
                dsp_feat = self.dsp_extractor.extract(temp_path)
                logger.info(f"✅ DSP features extracted: {dsp_feat.shape}")
            except Exception as e:
                logger.error(f"DSP extraction failed: {e}")
                raise ValueError(f"Failed to extract DSP features: {e}")
            
            # Step 6: Convert to tensors
            wavlm_tensor = torch.FloatTensor(wavlm_feat).unsqueeze(0).to(self.device)
            whisper_tensor = torch.FloatTensor(whisper_feat).unsqueeze(0).to(self.device)
            dsp_tensor = torch.FloatTensor(dsp_feat).unsqueeze(0).to(self.device)
            
            # Step 7: Run fusion model inference
            logger.info("Running fusion model inference...")
            with torch.no_grad():
                logits = self.model(wavlm_tensor, whisper_tensor, dsp_tensor)
                prob_fake = torch.sigmoid(logits).item()
            
            logger.info(f"✅ Inference complete: prob_fake = {prob_fake:.4f}")
            
            # Step 8: Determine prediction
            is_deepfake = prob_fake > 0.5
            confidence = prob_fake if is_deepfake else (1 - prob_fake)
            risk_level = self._get_risk_level(prob_fake)
            
            # Step 9: Get audio duration
            waveform, sample_rate = load_and_preprocess_audio(file_bytes)
            duration = len(waveform) / sample_rate
            
            # Step 10: Prepare result
            result = {
                "file_name": filename,
                "file_hash": file_hash,
                "file_size": len(file_bytes),
                "duration": duration,
                "is_deepfake": bool(is_deepfake),
                "confidence": float(confidence),
                "probability_fake": float(prob_fake),
                "risk_level": risk_level,
                "dsp_features": {
                    "pitch_mean": float(dsp_feat[0]),
                    "pitch_std": float(dsp_feat[1]),
                    "pitch_range": float(dsp_feat[2]),
                    "energy_mean": float(dsp_feat[3]),
                    "energy_std": float(dsp_feat[4]),
                    "silence_ratio": float(dsp_feat[5])
                },
                "processing_time": time.time() - start_time,
                "model_version": self.model_version,
                "model_loaded": self.model_loaded,
                "explanation": None,  # Will be filled by Gemini
                "highlights": self._generate_highlights(prob_fake, dsp_feat, is_deepfake),
                "cached": False
            }
            
        finally:
            # Clean up temp file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
    # <<<<<<< HEAD
    #     # Step 5: Load and preprocess audio
    #     waveform, sample_rate = load_and_preprocess_audio(file_bytes)
    #     duration = len(waveform) / sample_rate
    #     
    #     # Step 6: Run deepfake detection
    #     logger.info(f"Running deepfake detection on {filename}")
    #     prediction = self.detector.predict(waveform, sample_rate)
    #     
    #     # Step 7: Extract traditional features (for novelty/ensemble)
    #     traditional_features = extract_audio_features(waveform, sample_rate)
    #     
    #     # Step 8: Prepare result
    #     result = {
    #         "file_name": filename,
    #         "file_hash": file_hash,
    #         "file_size": len(file_bytes),
    #         "duration": duration,
    #         "is_deepfake": prediction['is_deepfake'],
    #         "confidence": prediction['confidence'],
    #         "risk_level": prediction['risk_level'],
    #         "raw_model_confidence": prediction.get('raw_confidence'),
    #         "artifact_score": prediction.get('artifact_score'),
    #         "artifacts": prediction.get('artifacts', {}),
    #         "traditional_features": traditional_features,
    #         "processing_time": time.time() - start_time,
    #         "model_version": self.model_version,
    #         "explanation": prediction.get('explanation'),
    #         "highlights": self._generate_highlights(prediction),
    #         "cached": False
    #     }
    #     
    #     # Step 9: Save file to disk
    # =======
        # Step 11: Save file to disk
    # >>>>>>> origin/develop
        file_path = None
        if db is not None:
             try:
                # Create uploads directory if not exists
                upload_dir = "uploads/voice"
                os.makedirs(upload_dir, exist_ok=True)
                
                # Generate unique filename to avoid collisions
                import uuid
                safe_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join(upload_dir, safe_filename)
                
                # Write file
                with open(file_path, "wb") as f:
                    f.write(file_bytes)
                    
                logger.info(f"Saved audio file to {file_path}")
             except Exception as e:
                 logger.error(f"Failed to save audio file: {e}")

        # Step 12: Save to database if provided
        if db is not None:
            try:
                voice_scan = create_voice_scan(
                    db=db,
                    file_hash=file_hash,
                    file_name=filename,
                    file_path=file_path,
                    file_size=len(file_bytes),
                    duration=duration,
                    is_deepfake=result['is_deepfake'],
                    confidence=result['confidence'],
                    risk_level=result['risk_level'],
                    raw_model_confidence=result.get('probability_fake'),
                    artifact_score=None,
                    artifacts=result.get('dsp_features'),
                    explanation=result.get('explanation'),
                    highlights=result['highlights'],
                    processing_time=result['processing_time'],
                    model_version=self.model_version
                )
                result['id'] = voice_scan.id
            except Exception as e:
                logger.error(f"Failed to save scan to database: {e}")
        
        logger.info(f"Analysis complete: {filename} - Deepfake: {result['is_deepfake']} ({result['confidence']:.2%})")
        
        return result
    
    
    def _get_risk_level(self, prob_fake: float) -> str:
        """Determine risk level from probability."""
        if prob_fake > 0.7:
            return "high"
        elif prob_fake > 0.3:
            return "medium"
        else:
            return "low"
    
    
    def _generate_highlights(self, prob_fake: float, dsp_feat: np.ndarray, is_deepfake: bool) -> list:
        """
        Generate key highlights from prediction.
        
        Args:
            prob_fake: Probability of being fake
            dsp_feat: DSP features array
            is_deepfake: Whether classified as deepfake
        
        Returns:
            List of highlight strings
        """
        highlights = []
        
        # Confidence-based highlights
        confidence = prob_fake if is_deepfake else (1 - prob_fake)
        
        if confidence > 0.8:
            highlights.append(f"Very high confidence ({confidence:.1%}) in classification")
        elif confidence > 0.6:
            highlights.append(f"High confidence ({confidence:.1%}) in classification")
        elif confidence > 0.4:
            highlights.append(f"Moderate confidence ({confidence:.1%}) - uncertain")
        else:
            highlights.append(f"Low confidence ({confidence:.1%}) - borderline case")
        
    # <<<<<<< HEAD
    #     # Artifact-based highlights (Professional Forensic Analysis)
    #     if artifacts:
    #         # Signal Quality (Higher = Worse)
    #         if artifacts.get('signal_quality', 0) > 0.6:
    #             highlights.append("Detected significant digital signal anomalies indicative of synthesis")
    #         
    #         # Acoustic Consistency (Higher = Worse)
    #         if artifacts.get('acoustic_consistency', 0) > 0.6:
    #             highlights.append("Acoustic patterns exhibit inconsistencies typical of neural vocoders")
    #         
    #         # Semantic Coherence (Higher = Worse)
    #         if artifacts.get('semantic_coherence', 0) > 0.6:
    #             highlights.append(" phonetic or prosodic misalignment detected in speech structure")
    # =======
        # DSP feature analysis
        pitch_std = dsp_feat[1]
        energy_std = dsp_feat[4]
        silence_ratio = dsp_feat[5]
        
        if pitch_std < 500:
            highlights.append("⚠️ Unusually stable pitch (possible AI generation)")
        
        if energy_std < 0.05:
            highlights.append("⚠️ Very consistent energy levels (robotic pattern)")
        
        if silence_ratio < 0.1:
            highlights.append("⚠️ Very few pauses (unnatural speech pattern)")
        elif silence_ratio > 0.4:
            highlights.append("⚠️ Excessive silence (possible audio manipulation)")
    # >>>>>>> origin/develop
        
        # Risk level highlight
        if prob_fake > 0.7:
            highlights.append("🚨 HIGH RISK: Strong indicators of AI generation")
        elif prob_fake > 0.3:
            highlights.append("⚡ MEDIUM RISK: Some suspicious characteristics detected")
        else:
            highlights.append("✅ LOW RISK: Appears to be genuine human voice")
        
        return highlights
    
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model details
        """
        return {
            "model_version": self.model_version,
            "architecture": "Multi-Modal Fusion (WavLM + Whisper + DSP)",
            "wavlm_model": "microsoft/wavlm-base-plus",
            "whisper_model": "openai/whisper-small",
            "fusion_layers": "1542 → 256 → 128 → 1",
            "parameters": "428,801",
            "framework": "PyTorch + Hugging Face Transformers",
            "device": str(self.device),
            "checkpoint_loaded": self.model_loaded,
            "training_accuracy": "65%",
            "training_samples": "40 (ASVspoof 2021)"
        }
