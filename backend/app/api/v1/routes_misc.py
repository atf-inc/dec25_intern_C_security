# backend/app/api/v1/routes_misc.py
from fastapi import APIRouter, HTTPException
from app.db.session import SessionLocal
from app.models.email_scan import EmailScan
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

router = APIRouter(prefix="/misc", tags=["misc"])

class FeedbackPayload(BaseModel):
    request_id: str
    user_label: str
    notes: Optional[str] = None

@router.post("/feedback")
def feedback(payload: FeedbackPayload):
    # Save feedback as a simple log or attach to persisted EmailScan if mapping available.
    db: Session = SessionLocal()
    try:
        # naive approach: map by id if request_id equals numeric id (or do separate mapping)
        # For now we log feedback. In future, extend schema to include request_id mapping.
        print("Feedback received:", payload.dict())
        return {"status": "ok"}
    finally:
        db.close()

@router.get("/history/{scan_id}")
def history(scan_id: int):
    db = SessionLocal()
    try:
        rec = db.query(EmailScan).filter(EmailScan.id == scan_id).first()
        if not rec:
            raise HTTPException(status_code=404, detail="Not found")
        return {
            "id": rec.id,
            "subject": rec.subject,
            "sender": rec.sender,
            "label": rec.label,
            "score": rec.score,
            "reasons": rec.reasons,
            "analysis_meta": rec.analysis_meta,
            "created_at": rec.created_at.isoformat()
        }
    finally:
        db.close()
