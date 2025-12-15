
import time
import logging
from typing import Dict, Any
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
    """Service for analyzing voice files for deepfake detection."""
    
    def __init__(self):
        """Initialize the service with ML model."""
        logger.info("Initializing VoiceAnalysisService...")
        self.detector = DeepfakeDetector()
        self.model_version = "v1.0-wavlm-base-plus"
        logger.info("VoiceAnalysisService initialized successfully")
    
    
    async def analyze_voice(
        self, 
        file_bytes: bytes, 
        filename: str,
        db: Session = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze voice file for deepfake detection.
        
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
            if cached_result:
                logger.info(f"Cache hit for file hash: {file_hash}")
                return {
                    "cached": True,
                    **cached_result.to_dict()
                }
        
        # Step 3: Validate audio file
        is_valid, error_msg = validate_audio_file(file_bytes)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Step 4: Convert to WAV if needed
        if not filename.lower().endswith('.wav'):
            logger.info(f"Converting {filename} to WAV format")
            file_format = filename.split('.')[-1].lower()
            file_bytes = convert_to_wav(file_bytes, file_format)
        
        # Step 5: Load and preprocess audio
        waveform, sample_rate = load_and_preprocess_audio(file_bytes)
        duration = len(waveform) / sample_rate
        
        # Step 6: Run deepfake detection
        logger.info(f"Running deepfake detection on {filename}")
        prediction = self.detector.predict(waveform, sample_rate)
        
        # Step 7: Extract traditional features (for novelty/ensemble)
        traditional_features = extract_audio_features(waveform, sample_rate)
        
        # Step 8: Prepare result
        result = {
            "file_name": filename,
            "file_hash": file_hash,
            "file_size": len(file_bytes),
            "duration": duration,
            "is_deepfake": prediction['is_deepfake'],
            "confidence": prediction['confidence'],
            "risk_level": prediction['risk_level'],
            "raw_model_confidence": prediction.get('raw_confidence'),
            "artifact_score": prediction.get('artifact_score'),
            "artifacts": prediction.get('artifacts', {}),
            "traditional_features": traditional_features,
            "processing_time": time.time() - start_time,
            "model_version": self.model_version,
            "explanation": None,  # Will be filled by Gemini
            "highlights": self._generate_highlights(prediction),
            "cached": False
        }
        
        # Step 9: Save file to disk
        file_path = None
        if db is not None:
             try:
                import os
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

        # Step 10: Save to database if provided
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
                    raw_model_confidence=result.get('raw_model_confidence'),
                    artifact_score=result.get('artifact_score'),
                    artifacts=result['artifacts'],
                    explanation=result.get('explanation'),
                    highlights=result['highlights'],
                    processing_time=result['processing_time'],
                    model_version=self.model_version
                )
                result['id'] = voice_scan.id
            except Exception as e:
                logger.error(f"Failed to save scan to database: {e}")
        
        logger.info(f"Analysis complete: {filename} - Deepfake: {result['is_deepfake']} ({result['confidence']:.2f})")
        
        return result
    
    
    def _generate_highlights(self, prediction: Dict) -> list:
        """
        Generate key highlights from prediction.
        
        Args:
            prediction: Prediction dictionary from detector
        
        Returns:
            List of highlight strings
        """
        highlights = []
        
        confidence = prediction['confidence']
        artifacts = prediction.get('artifacts', {})
        
        # Confidence-based highlights
        if confidence > 0.8:
            highlights.append(f"Very high confidence ({confidence:.1%}) in deepfake detection")
        elif confidence > 0.6:
            highlights.append(f"High confidence ({confidence:.1%}) in deepfake detection")
        elif confidence > 0.4:
            highlights.append(f"Moderate confidence ({confidence:.1%}) - uncertain")
        else:
            highlights.append(f"Low confidence ({confidence:.1%}) - likely real")
        
        # Artifact-based highlights
        if artifacts:
            if artifacts.get('spectral_flatness', 0) > 0.5:
                highlights.append("Unusually flat frequency spectrum detected")
            
            if artifacts.get('high_freq_energy', 0) > 0.3:
                highlights.append("Suspicious high-frequency artifacts present")
            
            if artifacts.get('zcr_variance', 0) < 0.01:
                highlights.append("Unnaturally regular zero-crossing pattern")
            
            if artifacts.get('autocorr_peak', 0) > 500:
                highlights.append("Strong periodicity suggests synthetic generation")
        
        # Risk level highlight
        risk_level = prediction['risk_level']
        if risk_level == "high":
            highlights.append("⚠️ HIGH RISK: Strong indicators of AI generation")
        elif risk_level == "medium":
            highlights.append("⚡ MEDIUM RISK: Some suspicious characteristics")
        else:
            highlights.append("✓ LOW RISK: Appears to be genuine human voice")
        
        return highlights
    
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model details
        """
        return {
            "model_version": self.model_version,
            "base_model": "WavLM-Base-Plus",
            "framework": "PyTorch + Hugging Face Transformers",
            "device": str(self.detector.device),
            "trained": self.detector.is_trained
        }
