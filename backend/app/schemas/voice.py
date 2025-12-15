
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

class VoiceAnalysisRequest(BaseModel):
    """Request schema for voice analysis (file upload handled separately)."""
    include_explanation: bool = Field(
        default=True,
        description="Whether to generate LLM-based explanation"
    )
    use_cache: bool = Field(
        default=True,
        description="Whether to check cache for previous analysis"
    )


class ArtifactDetails(BaseModel):
    """Detailed artifact measurements."""
    spectral_flatness: float = Field(description="Measure of spectral flatness (0-1)")
    autocorr_peak: float = Field(description="Autocorrelation peak value")
    high_freq_energy: float = Field(description="High-frequency energy content")
    zcr_variance: float = Field(description="Zero-crossing rate variance")


class VoiceAnalysisResponse(BaseModel):
    """Response schema for voice analysis results."""
    
    # File information
    file_name: str = Field(description="Original filename")
    file_hash: str = Field(description="MD5 hash of file content")
    file_size: int = Field(description="File size in bytes")
    file_size: int = Field(description="File size in bytes")
    duration: float = Field(description="Audio duration in seconds")
    audio_url: Optional[str] = Field(default=None, description="URL to access audio file")
    
    # Detection results
    is_deepfake: bool = Field(description="Whether audio is detected as AI-generated")
    confidence: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Overall confidence score (0-1)"
    )
    risk_level: str = Field(
        description="Risk classification: low, medium, or high"
    )
    
    # Detailed scores (NOVELTY)
    raw_model_confidence: Optional[float] = Field(
        default=None,
        description="Raw model output before ensemble"
    )
    artifact_score: Optional[float] = Field(
        default=None,
        description="Artifact detection score"
    )
    artifacts: Optional[Dict] = Field(
        default=None,
        description="Detailed artifact measurements"
    )
    
    # Explanation
    explanation: Optional[str] = Field(
        default=None,
        description="Human-readable explanation of results"
    )
    highlights: Optional[List[str]] = Field(
        default=None,
        description="Key points from analysis"
    )
    
    # Metadata
    processing_time: float = Field(description="Analysis duration in seconds")
    model_version: str = Field(description="Model version used")
    cached: bool = Field(
        default=False,
        description="Whether result was retrieved from cache"
    )
    id: Optional[int] = Field(
        default=None,
        description="Database record ID"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of analysis"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_name": "voice_sample.wav",
                "file_hash": "a1b2c3d4e5f6",
                "file_size": 256000,
                "duration": 5.2,
                "is_deepfake": True,
                "confidence": 0.87,
                "risk_level": "high",
                "raw_model_confidence": 0.82,
                "artifact_score": 0.75,
                "artifacts": {
                    "spectral_flatness": 0.65,
                    "autocorr_peak": 520.3,
                    "high_freq_energy": 0.42,
                    "zcr_variance": 0.008
                },
                "explanation": "This audio exhibits multiple characteristics of AI-generated speech...",
                "highlights": [
                    "Very high confidence (87%) in deepfake detection",
                    "Suspicious high-frequency artifacts present",
                    "⚠️ HIGH RISK: Strong indicators of AI generation"
                ],
                "processing_time": 2.3,
                "model_version": "v1.0-wavlm-base-plus",
                "cached": False
            }
        }


class VoiceHistoryResponse(BaseModel):
    """Response schema for history endpoint."""
    total: int = Field(description="Total number of scans")
    scans: List[VoiceAnalysisResponse] = Field(description="List of scan results")


class VoiceStatistics(BaseModel):
    """Statistics about voice scans."""
    total_scans: int = Field(description="Total number of scans performed")
    deepfake_count: int = Field(description="Number of deepfakes detected")
    real_count: int = Field(description="Number of real voices detected")
    high_risk_count: int = Field(description="Number of high-risk detections")
    deepfake_percentage: float = Field(
        description="Percentage of scans that were deepfakes"
    )


class ModelInfo(BaseModel):
    """Information about the detection model."""
    model_version: str = Field(description="Current model version")
    base_model: str = Field(description="Base model architecture")
    framework: str = Field(description="ML framework used")
    device: str = Field(description="Device (CPU/GPU)")
    trained: bool = Field(description="Whether custom classifier is trained")
