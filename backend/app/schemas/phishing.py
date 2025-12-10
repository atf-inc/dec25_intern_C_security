# app/schemas/phishing.py
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Any

class LinkItem(BaseModel):
    anchor_text: Optional[str] = None
    uri: Optional[str] = None
    page: Optional[int] = None

class AttachmentItem(BaseModel):
    filename: str
    mimetype: Optional[str] = None
    size: Optional[int] = None

class UploadPreview(BaseModel):
    subject: Optional[str] = None
    from_name: Optional[str] = None
    from_email: Optional[str] = None
    to: Optional[List[str]] = None
    date: Optional[str] = None
    raw_text: Optional[str] = None
    visible_links: Optional[List[LinkItem]] = []
    hidden_links: Optional[List[LinkItem]] = []
    attachments: Optional[List[AttachmentItem]] = []

class AnalyzeRequest(BaseModel):
    subject: Optional[str] = None
    from_name: Optional[str] = None
    from_email: Optional[str] = None
    to: Optional[List[str]] = None
    raw_text: Optional[str] = None
    visible_links: Optional[List[LinkItem]] = []
    hidden_links: Optional[List[LinkItem]] = []
    attachments: Optional[List[AttachmentItem]] = []
    sanitization: Optional[List[Any]] = None
    meta: Optional[dict] = None

class AnalyzeResponse(BaseModel):
    request_id: str
    label: str
    score: int
    reasons: List[str]
    evidence: Optional[List[dict]] = []
    suggested_action: Optional[str] = None
    suggested_reply: Optional[str] = None
    model_meta: Optional[dict] = None

