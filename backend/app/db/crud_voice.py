
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.voice_scan import VoiceScan
from datetime import datetime

def create_voice_scan(
    db: Session,
    file_hash: str,
    file_name: str,
    file_size: int,
    duration: float,
    is_deepfake: bool,
    confidence: float,
    risk_level: str,
    file_path: str = None,
    raw_model_confidence: float = None,
    artifact_score: float = None,
    artifacts: dict = None,
    explanation: str = None,
    highlights: list = None,
    processing_time: float = None,
    model_version: str = "v1.0"
) -> VoiceScan:
    """
    Create a new voice scan record.
    
    Args:
        db: Database session
        file_hash: MD5 hash of audio file
        file_name: Original filename
        file_size: File size in bytes
        duration: Audio duration in seconds
        is_deepfake: Detection result
        confidence: Overall confidence score (0-1)
        risk_level: Risk classification (low/medium/high)
        file_path: Path to saved audio file
        raw_model_confidence: Raw model output
        artifact_score: Artifact detection score
        artifacts: Dictionary of artifact measurements
        explanation: LLM-generated explanation
        highlights: Key points list
        processing_time: Analysis duration in seconds
        model_version: Model version identifier
    
    Returns:
        VoiceScan: Created database record
    """
    voice_scan = VoiceScan(
        file_hash=file_hash,
        file_name=file_name,
        file_path=file_path,
        file_size=file_size,
        duration=duration,
        is_deepfake=is_deepfake,
        confidence=confidence,
        risk_level=risk_level,
        raw_model_confidence=raw_model_confidence,
        artifact_score=artifact_score,
        artifacts=artifacts,
        explanation=explanation,
        highlights=highlights,
        created_at=datetime.utcnow(),
        processing_time=processing_time,
        model_version=model_version
    )
    
    db.add(voice_scan)
    db.commit()
    db.refresh(voice_scan)
    
    return voice_scan


def get_voice_scan_by_hash(db: Session, file_hash: str) -> Optional[VoiceScan]:
    """
    Retrieve voice scan by file hash (for caching).
    
    Args:
        db: Database session
        file_hash: MD5 hash of audio file
    
    Returns:
        VoiceScan or None
    """
    return db.query(VoiceScan).filter(VoiceScan.file_hash == file_hash).first()


def get_voice_scan_by_id(db: Session, scan_id: int) -> Optional[VoiceScan]:
    """
    Retrieve voice scan by ID.
    
    Args:
        db: Database session
        scan_id: Scan ID
    
    Returns:
        VoiceScan or None
    """
    return db.query(VoiceScan).filter(VoiceScan.id == scan_id).first()


def get_all_voice_scans(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    order_by_recent: bool = True
) -> List[VoiceScan]:
    """
    Retrieve all voice scans with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum records to return
        order_by_recent: If True, order by created_at descending
    
    Returns:
        List of VoiceScan records
    """
    query = db.query(VoiceScan)
    
    if order_by_recent:
        query = query.order_by(VoiceScan.created_at.desc())
    
    return query.offset(skip).limit(limit).all()


def get_deepfake_scans(db: Session, skip: int = 0, limit: int = 100) -> List[VoiceScan]:
    """
    Retrieve only scans flagged as deepfakes.
    
    Args:
        db: Database session
        skip: Pagination offset
        limit: Max results
    
    Returns:
        List of deepfake VoiceScan records
    """
    return db.query(VoiceScan)\
        .filter(VoiceScan.is_deepfake == True)\
        .order_by(VoiceScan.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def get_high_risk_scans(db: Session, skip: int = 0, limit: int = 100) -> List[VoiceScan]:
    """
    Retrieve high-risk scans.
    
    Args:
        db: Database session
        skip: Pagination offset
        limit: Max results
    
    Returns:
        List of high-risk VoiceScan records
    """
    return db.query(VoiceScan)\
        .filter(VoiceScan.risk_level == "high")\
        .order_by(VoiceScan.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def delete_voice_scan(db: Session, scan_id: int) -> bool:
    """
    Delete a voice scan record.
    
    Args:
        db: Database session
        scan_id: Scan ID to delete
    
    Returns:
        True if deleted, False if not found
    """
    scan = db.query(VoiceScan).filter(VoiceScan.id == scan_id).first()
    
    if scan:
        db.delete(scan)
        db.commit()
        return True
    
    return False


def get_scan_statistics(db: Session) -> dict:
    """
    Get overall statistics about voice scans.
    
    Args:
        db: Database session
    
    Returns:
        Dictionary with statistics
    """
    total_scans = db.query(VoiceScan).count()
    deepfake_count = db.query(VoiceScan).filter(VoiceScan.is_deepfake == True).count()
    high_risk_count = db.query(VoiceScan).filter(VoiceScan.risk_level == "high").count()
    
    return {
        "total_scans": total_scans,
        "deepfake_count": deepfake_count,
        "real_count": total_scans - deepfake_count,
        "high_risk_count": high_risk_count,
        "deepfake_percentage": (deepfake_count / total_scans * 100) if total_scans > 0 else 0
    }
