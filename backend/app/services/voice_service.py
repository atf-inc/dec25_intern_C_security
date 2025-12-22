
import time
import logging
import os
import tempfile
from typing import Dict, Any, Optional, Tuple
import torch
import numpy as np
import librosa

# Import v2.1 DeepfakeDetector (uses FusionDeepfakeDetector with 246-dim DSP + Attention)
from ..ml.deepfake_model import DeepfakeDetector

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
    """Service for analyzing voice files using v2.1 Fusion Deepfake Detection."""
    
    # Audio quality thresholds
    MIN_DURATION_SECONDS = 0.5      # Minimum audio length
    MAX_DURATION_SECONDS = 300      # Maximum audio length (5 minutes)
    MIN_SNR_DB = 5                  # Minimum signal-to-noise ratio
    MIN_RMS_ENERGY = 0.001          # Minimum RMS energy (detect silence)
    
    def __init__(self):
        """Initialize the service with v2.1 DeepfakeDetector."""
        logger.info("Initializing VoiceAnalysisService with v2.1 Fusion Model...")
        
        try:
            self.detector = DeepfakeDetector()
            self.model_version = "v2.1-fusion-generalization"
            logger.info(f"✅ VoiceAnalysisService initialized successfully (version: {self.model_version})")
        except Exception as e:
            logger.error(f"Failed to initialize DeepfakeDetector: {e}")
            raise
        
    def _check_audio_quality(self, waveform: np.ndarray, sample_rate: int) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Check audio quality before analysis.
        
        Args:
            waveform: Audio waveform as numpy array
            sample_rate: Sample rate in Hz
        
        Returns:
            Tuple of (is_acceptable, warning_message, quality_metrics)
        """
        quality_metrics = {}
        warnings = []
        
        # 1. Check duration
        duration = len(waveform) / sample_rate
        quality_metrics['duration'] = duration
        
        if duration < self.MIN_DURATION_SECONDS:
            return False, f"Audio too short ({duration:.1f}s). Minimum is {self.MIN_DURATION_SECONDS}s.", quality_metrics
        
        if duration > self.MAX_DURATION_SECONDS:
            return False, f"Audio too long ({duration:.1f}s). Maximum is {self.MAX_DURATION_SECONDS}s.", quality_metrics
        
        # 2. Check RMS energy (detect silence/very quiet audio)
        rms = np.sqrt(np.mean(waveform ** 2))
        quality_metrics['rms_energy'] = float(rms)
        
        if rms < self.MIN_RMS_ENERGY:
            warnings.append("Very low audio energy detected (possibly silent or very quiet)")
        
        # 3. Estimate SNR (Signal-to-Noise Ratio)
        try:
            # Simple SNR estimation: ratio of signal power to noise floor
            # Use top 10% as signal, bottom 10% as noise
            sorted_power = np.sort(np.abs(waveform))
            signal_power = np.mean(sorted_power[int(len(sorted_power) * 0.9):] ** 2)
            noise_power = np.mean(sorted_power[:int(len(sorted_power) * 0.1)] ** 2) + 1e-10
            snr_db = 10 * np.log10(signal_power / noise_power)
            quality_metrics['snr_db'] = float(snr_db)
            
            if snr_db < self.MIN_SNR_DB:
                warnings.append(f"Low audio quality (SNR: {snr_db:.1f}dB). Results may be less reliable.")
        except Exception as e:
            logger.warning(f"Could not estimate SNR: {e}")
            quality_metrics['snr_db'] = None
        
        # 4. Check for clipping
        clipping_threshold = 0.99
        clipped_samples = np.sum(np.abs(waveform) > clipping_threshold)
        clipping_ratio = clipped_samples / len(waveform)
        quality_metrics['clipping_ratio'] = float(clipping_ratio)
        
        if clipping_ratio > 0.01:  # More than 1% clipped
            warnings.append("Audio clipping detected. This may affect accuracy.")
        
        # Compile warning message
        warning_msg = " | ".join(warnings) if warnings else None
        
        return True, warning_msg, quality_metrics
    
    
    async def analyze_voice(
        self, 
        file_bytes: bytes, 
        filename: str,
        db: Session = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze voice file using v2.1 multi-modal fusion approach.
        
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
            
            # Step 5: Load audio for duration calculation
            waveform, sample_rate = load_and_preprocess_audio(file_bytes)
            duration = len(waveform) / sample_rate
            
            # Step 6: Check audio quality
            is_acceptable, quality_warning, quality_metrics = self._check_audio_quality(waveform, sample_rate)
            
            if not is_acceptable:
                raise ValueError(quality_warning)
            
            # Step 7: Run v2.1 DeepfakeDetector
            logger.info(f"Running v2.1 deepfake detection on {filename}")
            prediction = self.detector.predict(waveform, sample_rate)
            
            # Step 8: Prepare result
            result = {
                "file_name": filename,
                "file_hash": file_hash,
                "file_size": len(file_bytes),
                "duration": duration,
                "is_deepfake": prediction['is_deepfake'],
                "confidence": prediction['confidence'],
                "probability_fake": prediction.get('raw_confidence', prediction['confidence']),
                "risk_level": prediction['risk_level'],
                "raw_model_confidence": prediction.get('raw_confidence'),
                "calibrated": prediction.get('calibrated', False),
                "artifact_score": prediction.get('artifact_score'),
                "artifacts": prediction.get('artifacts', {}),
                "dsp_features": prediction.get('artifacts', {}),  # For compatibility
                "quality_metrics": quality_metrics,
                "quality_warning": quality_warning,
                "processing_time": time.time() - start_time,
                "model_version": self.model_version,
                "model_loaded": True,
                "explanation": prediction.get('explanation'),
                "highlights": self._generate_highlights(prediction, quality_warning),
                "cached": False
            }
            
        finally:
            # Clean up temp file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
        # Step 8: Save file to disk
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

        # Step 9: Save to database if provided
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
                    artifact_score=result.get('artifact_score'),
                    artifacts=result.get('artifacts'),
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
    
    
    def _generate_highlights(self, prediction: Dict[str, Any], quality_warning: Optional[str] = None) -> list:
        """
        Generate key highlights from v2.1 prediction.
        
        Args:
            prediction: Prediction result from DeepfakeDetector
            quality_warning: Optional audio quality warning message
        
        Returns:
            List of highlight strings
        """
        highlights = []
        
        # Add quality warning first if present
        if quality_warning:
            highlights.append(f"⚠️ {quality_warning}")
        
        is_deepfake = prediction.get('is_deepfake', False)
        confidence = prediction.get('confidence', 0.5)
        artifacts = prediction.get('artifacts', {})
        
        # Confidence-based highlights
        if confidence > 0.8:
            highlights.append(f"Very high confidence ({confidence:.1%}) in classification")
        elif confidence > 0.6:
            highlights.append(f"High confidence ({confidence:.1%}) in classification")
        elif confidence > 0.4:
            highlights.append(f"Moderate confidence ({confidence:.1%}) - requires review")
        else:
            highlights.append(f"Low confidence ({confidence:.1%}) - borderline case")
        
        # Forensic artifact-based highlights (v2.1 expert scores)
        if artifacts:
            # Acoustic analysis
            acoustic_score = artifacts.get('acoustic', artifacts.get('acoustic_consistency', 0))
            if acoustic_score > 0.6:
                highlights.append("🔊 Acoustic patterns show synthesis artifacts typical of neural vocoders")
            
            # Semantic/prosodic analysis
            semantic_score = artifacts.get('semantic', artifacts.get('semantic_coherence', 0))
            if semantic_score > 0.6:
                highlights.append("🗣️ Prosodic/semantic inconsistencies detected in speech flow")
            
            # Signal/DSP analysis
            signal_score = artifacts.get('signal', artifacts.get('signal_quality', 0))
            if signal_score > 0.6:
                highlights.append("📊 Digital signal anomalies indicative of AI generation")
        
        # Risk level highlight
        risk_level = prediction.get('risk_level', 'unknown')
        if risk_level == 'high' or (is_deepfake and confidence > 0.7):
            highlights.append("🚨 HIGH RISK: Strong indicators of AI-generated voice")
        elif risk_level == 'medium' or (is_deepfake and confidence > 0.3):
            highlights.append("⚡ MEDIUM RISK: Suspicious characteristics detected")
        else:
            highlights.append("✅ LOW RISK: Appears to be genuine human voice")
        
        return highlights
    
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Get information about the v2.1 model.
        
        Returns:
            Dictionary with model details
        """
        return {
            "model_version": self.model_version,
            "architecture": "FusionDeepfakeDetector (WavLM + Whisper + DSP + Attention)",
            "wavlm_model": "microsoft/wavlm-base-plus",
            "whisper_model": "openai/whisper-small",
            "dsp_features": "246-dim forensic features (MFCCs, jitter, shimmer, spectral)",
            "attention": "Multi-Head Self-Attention (4 heads)",
            "fusion_layers": "768+768+246 → 256 → Attention → 512 → 256 → 1",
            "framework": "PyTorch + Hugging Face Transformers",
            "training_data": "~1,500 samples (WaveFake + ASVspoof + LibriSpeech)",
            "validation_accuracy": "90%",
            "validation_auc": "0.96",
            "recall_deepfake": "100%",
            "architectures_detected": "11/11 (MelGAN, HiFiGAN, WaveGlow, etc.)",
            "status": "Production / Forensic Grade"
        }
