from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from app.db.session import Base
from datetime import datetime

class VoiceScan(Base):
    """Database model for voice deepfake scan results."""
    
    __tablename__ = "voice_scans"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # File information
    file_hash = Column(String, unique=True, index=True, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer)  # in bytes
    duration = Column(Float)  # in seconds
    
    # Analysis results
    is_deepfake = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)  # 0-1 scale
    risk_level = Column(String, nullable=False)  # low, medium, high
    
    # Detailed scores
    raw_model_confidence = Column(Float)
    artifact_score = Column(Float)
    artifacts = Column(JSON)  # Store artifact details as JSON
    
    # Explanation
    explanation = Column(String)  # LLM-generated explanation
    highlights = Column(JSON)  # Key points from analysis
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_time = Column(Float)  # seconds
    model_version = Column(String)  # Track which model version was used
    
    def __repr__(self):
        return f"<VoiceScan(id={self.id}, is_deepfake={self.is_deepfake}, confidence={self.confidence})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "file_hash": self.file_hash,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "duration": self.duration,
            "is_deepfake": self.is_deepfake,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "raw_model_confidence": self.raw_model_confidence,
            "artifact_score": self.artifact_score,
            "artifacts": self.artifacts,
            "explanation": self.explanation,
            "highlights": self.highlights,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processing_time": self.processing_time,
            "model_version": self.model_version
        }