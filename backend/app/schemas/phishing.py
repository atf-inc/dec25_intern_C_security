"""
Pydantic schemas for phishing detection endpoints.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from app.schemas.common import RiskLevel


class PhishingRequest(BaseModel):
    """Request schema for phishing email analysis."""
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject line")
    body: str = Field(..., min_length=1, description="Email body content")
    sender: str = Field(..., min_length=1, max_length=255, description="Email sender address")
    urls: Optional[List[str]] = Field(default=[], description="List of URLs found in the email")
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Urgent: Verify your account",
                "body": "Click here to verify your account or it will be suspended.",
                "sender": "noreply@suspicious-site.com",
                "urls": ["http://suspicious-site.com/verify"]
            }
        }


class PhishingResponse(BaseModel):
    """Response schema for phishing email analysis."""
    id: int = Field(..., description="Unique scan identifier")
    risk_score: int = Field(..., ge=0, le=100, description="Risk score from 0 to 100")
    risk_level: RiskLevel = Field(..., description="Risk level classification")
    explanation: str = Field(..., description="Human-readable explanation of the risk")
    highlights: List[str] = Field(..., description="List of specific concerns identified")
    created_at: datetime = Field(..., description="Timestamp of the scan")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "risk_score": 85,
                "risk_level": "high",
                "explanation": "This email shows multiple phishing indicators including urgency tactics and suspicious sender domain.",
                "highlights": [
                    "Urgent language detected",
                    "Suspicious sender domain",
                    "Contains suspicious URL"
                ],
                "created_at": "2024-12-09T10:30:00Z"
            }
        }
