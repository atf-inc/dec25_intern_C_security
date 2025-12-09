"""
Pydantic schemas for voice/deepfake detection endpoints.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.common import RiskLevel


class VoiceResponse(BaseModel):
    """Response schema for voice deepfake analysis."""
    id: int = Field(..., description="Unique scan identifier")
    deepfake_score: int = Field(..., ge=0, le=100, description="Deepfake likelihood score from 0 to 100")
    risk_level: RiskLevel = Field(..., description="Risk level classification")
    explanation: str = Field(..., description="Human-readable explanation of the analysis")
    created_at: datetime = Field(..., description="Timestamp of the scan")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "deepfake_score": 72,
                "risk_level": "high",
                "explanation": "Audio analysis detected synthetic voice patterns and unnatural prosody consistent with deepfake generation.",
                "created_at": "2024-12-09T10:30:00Z"
            }
        }
