# backend/app/api/v1/routes_analyze.py
from fastapi import APIRouter, HTTPException, status
from app.schemas.phishing import AnalyzeRequest, AnalyzeResponse
from app.ml.phishing_model import analyze_email, retranslate_explanation
from uuid import uuid4
from app.db.session import SessionLocal
from app.models.email_scan import EmailScan
from pydantic import BaseModel
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze", tags=["analyze"])

@router.post("/", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    meta = req.meta or {}
    consent = meta.get("consent", False)
    if not consent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User consent required (meta.consent=true)")

    payload = req.dict()
    try:
        result = analyze_email(payload)
    except Exception as ex:
        logger.exception("analyze_email failed: %s", ex)
        raise HTTPException(status_code=500, detail="Analysis failed")

    db = SessionLocal()
    try:
        rec = EmailScan(
            subject=(req.subject or "")[:512],
            sender=(req.from_email or "")[:255],
            label=result.get("label"),
            score=int(result.get("score", 0)),
            reasons=";".join(result.get("reasons") or []),
            analysis_meta=str(result.get("model_meta", {}))
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
    except Exception:
        db.rollback()
        logger.exception("Failed to persist EmailScan")
    finally:
        db.close()

    # --- attach domain hints from meta.url_map (if frontend provided mapping) ---
    url_map = (req.meta or {}).get("url_map") or {}  # e.g. {"[LINK_1]": "https://youtube.com/...."}
    if url_map:
        logger.debug("url_map provided for request: keys=%s", list(url_map.keys()))
        # attach domain hint to evidence items that have placeholder URIs
        for ev in result.get("evidence", []):
            uri = ev.get("uri")
            if uri and uri in url_map:
                try:
                    full = url_map.get(uri)
                    # extract domain safely
                    if "://" in full:
                        domain = full.split("://", 1)[1].split("/", 1)[0]
                    else:
                        domain = full.split("/", 1)[0]
                    ev.setdefault("meta", {})["domain_hint"] = domain
                except Exception:
                    logger.debug("failed to parse domain for uri %s", uri)

    
    response = {
        "request_id": str(uuid4()),
        "label": result.get("label"),
        "score": int(result.get("score", 0)),
        "reasons": result.get("reasons") or [],
        "evidence": result.get("evidence") or [],
        "suggested_action": "Do not click links; verify the sender via official channels.",
        "suggested_reply": "I will confirm via official channels; please do not share credentials.",
        "ai_explanation": result.get("ai_explanation"),  # 🚀 NEW: Include AI explanation
        "model_meta": result.get("model_meta", {})
    }
    return response

# Re-translation request schema
class RetranslateRequest(BaseModel):
    original_result: Dict[str, Any]
    target_language: str
    meta: Dict[str, Any] = {}

@router.post("/retranslate", response_model=AnalyzeResponse)
def retranslate(req: RetranslateRequest):
    """Re-translate AI explanation to a different language without re-analyzing."""
    
    meta = req.meta or {}
    consent = meta.get("consent", False)
    if not consent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User consent required (meta.consent=true)")

    try:
        # Re-translate the explanation
        updated_result = retranslate_explanation(req.original_result, req.target_language)
        
        # Return the updated result with new explanation
        response = {
            "request_id": req.original_result.get("request_id", str(uuid4())),
            "label": updated_result.get("label"),
            "score": int(updated_result.get("score", 0)),
            "reasons": updated_result.get("reasons") or [],
            "evidence": updated_result.get("evidence") or [],
            "suggested_action": updated_result.get("suggested_action", ""),
            "suggested_reply": updated_result.get("suggested_reply", ""),
            "ai_explanation": updated_result.get("ai_explanation"),
            "model_meta": updated_result.get("model_meta", {})
        }
        return response
        
    except Exception as ex:
        logger.exception("Re-translation failed: %s", ex)
        raise HTTPException(status_code=500, detail="Re-translation failed")
