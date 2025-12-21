"""
Custom exceptions for the CyberX Voice Deepfake Detection API.

These exceptions provide clear, specific error messages for different failure scenarios.
"""

from fastapi import HTTPException
from typing import Optional


class VoiceAnalysisException(HTTPException):
    """Base exception for voice analysis errors."""
    
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)


class AudioTooShortError(VoiceAnalysisException):
    """Raised when audio is shorter than the minimum required duration."""
    
    def __init__(self, duration: float, min_duration: float = 0.5):
        super().__init__(
            detail=f"Audio too short ({duration:.2f}s). Minimum duration is {min_duration}s.",
            status_code=400
        )


class AudioTooLongError(VoiceAnalysisException):
    """Raised when audio exceeds the maximum allowed duration."""
    
    def __init__(self, duration: float, max_duration: float = 300):
        super().__init__(
            detail=f"Audio too long ({duration:.1f}s). Maximum duration is {max_duration}s (5 minutes).",
            status_code=400
        )


class UnsupportedFormatError(VoiceAnalysisException):
    """Raised when the audio file format is not supported."""
    
    SUPPORTED_FORMATS = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
    
    def __init__(self, file_format: str):
        super().__init__(
            detail=f"Unsupported audio format: '{file_format}'. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}",
            status_code=400
        )


class FileTooLargeError(VoiceAnalysisException):
    """Raised when the file size exceeds the maximum allowed."""
    
    def __init__(self, file_size: int, max_size: int = 10 * 1024 * 1024):
        size_mb = file_size / (1024 * 1024)
        max_mb = max_size / (1024 * 1024)
        super().__init__(
            detail=f"File too large ({size_mb:.1f}MB). Maximum size is {max_mb:.0f}MB.",
            status_code=400
        )


class AudioQualityError(VoiceAnalysisException):
    """Raised when audio quality is too poor for reliable analysis."""
    
    def __init__(self, issue: str, snr_db: Optional[float] = None):
        detail = f"Audio quality too poor for reliable analysis: {issue}"
        if snr_db is not None:
            detail += f" (SNR: {snr_db:.1f}dB)"
        super().__init__(detail=detail, status_code=400)


class AudioProcessingError(VoiceAnalysisException):
    """Raised when audio cannot be processed (corrupt file, etc.)."""
    
    def __init__(self, reason: str = "Unknown error"):
        super().__init__(
            detail=f"Failed to process audio file: {reason}. The file may be corrupt or in an unsupported encoding.",
            status_code=400
        )


class ModelLoadError(VoiceAnalysisException):
    """Raised when the ML model fails to load."""
    
    def __init__(self, model_name: str = "DeepfakeDetector"):
        super().__init__(
            detail=f"Failed to load {model_name}. Please try again later or contact support.",
            status_code=503
        )


class PredictionError(VoiceAnalysisException):
    """Raised when the model fails to make a prediction."""
    
    def __init__(self, reason: str = "Unknown error"):
        super().__init__(
            detail=f"Model prediction failed: {reason}. Please try a different audio file.",
            status_code=500
        )


class ScanNotFoundError(VoiceAnalysisException):
    """Raised when a requested scan is not found."""
    
    def __init__(self, scan_id: int):
        super().__init__(
            detail=f"Scan with ID {scan_id} not found.",
            status_code=404
        )


class AudioFileNotFoundError(VoiceAnalysisException):
    """Raised when the audio file for a scan is missing."""
    
    def __init__(self, scan_id: int):
        super().__init__(
            detail=f"Audio file for scan {scan_id} not found. The file may have been deleted.",
            status_code=404
        )


class RateLimitError(VoiceAnalysisException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, limit: str = "20/minute"):
        super().__init__(
            detail=f"Rate limit exceeded. Maximum {limit} requests allowed. Please wait and try again.",
            status_code=429
        )

