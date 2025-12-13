
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ...services.voice_service import VoiceAnalysisService
from ...services.explanation_service import ExplanationService
from ...schemas.voice import VoiceAnalysisResponse, VoiceAnalysisRequest
from ...db.session import get_db
from ...db.crud_voice import get_all_voice_scans, get_scan_statistics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

# Initialize services (singleton pattern)
voice_service = VoiceAnalysisService()
explanation_service = ExplanationService()

@router.post("/analyze", response_model=VoiceAnalysisResponse)
async def analyze_voice(
    file: UploadFile = File(...),
    include_explanation: bool = True,
    db: Session = Depends(get_db)
):
    """
    Analyze uploaded voice file for deepfake detection.
    
    Args:
        file: Audio file (WAV, MP3, M4A, FLAC supported)
        include_explanation: Whether to generate LLM explanation
        db: Database session
    
    Returns:
        VoiceAnalysisResponse with detection results
    """
    try:
        # Validate file type
        allowed_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
        file_ext = '.' + file.filename.split('.')[-1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file bytes
        file_bytes = await file.read()
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_bytes) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {max_size / (1024*1024):.0f}MB"
            )
            
        await file.seek(0)  # Reset file pointer after reading
        
        logger.info(f"Analyzing file: {file.filename} ({len(file_bytes)} bytes)")
        
        # Perform analysis
        result = await voice_service.analyze_voice(
            file_bytes=file_bytes,
            filename=file.filename,
            db=db,
            use_cache=True
        )
        
        # Generate explanation if requested and not cached
        if include_explanation and not result.get('cached', False):
            explanation = await explanation_service.generate_voice_explanation(result)
            result['explanation'] = explanation
            
            # Update database with explanation
            if 'id' in result and result['id']:
                from ...db.crud_voice import get_voice_scan_by_id
                scan = get_voice_scan_by_id(db, result['id'])
                if scan:
                    scan.explanation = explanation
                    db.commit()
        
        return VoiceAnalysisResponse(**result)
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during analysis")


@router.get("/history")
async def get_analysis_history(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get history of all voice analyses.
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum records to return
        db: Database session
    
    Returns:
        List of analysis results
    """
    try:
        scans = get_all_voice_scans(db, skip=skip, limit=limit)
        return {
            "total": len(scans),
            "scans": [scan.to_dict() for scan in scans]
        }
    
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")


@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get overall statistics about voice scans.
    
    Args:
        db: Database session
    
    Returns:
        Statistics dictionary
    """
    try:
        stats = get_scan_statistics(db)
        return stats
    
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


@router.get("/model-info")
async def get_model_info():
    """
    Get information about the loaded detection model.
    
    Returns:
        Model information dictionary
    """
    try:
        info = voice_service.get_model_info()
        return info
    
    except Exception as e:
        logger.error(f"Error fetching model info: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch model info")


@router.delete("/scan/{scan_id}")
async def delete_scan(scan_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific scan from history.
    
    Args:
        scan_id: ID of scan to delete
        db: Database session
    
    Returns:
        Success message
    """
    try:
        from ...db.crud_voice import delete_voice_scan
        
        success = delete_voice_scan(db, scan_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        return {"message": "Scan deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scan: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete scan")
