# app/api/v1/routes_phishing.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
from app.schemas.phishing import AnalyzeRequest, AnalyzeResponse, UploadPreview
from app.services.hybrid_analysis_service import hybrid_service
from app.services.extraction_service import parse_eml_bytes

router = APIRouter(prefix="/phishing", tags=["phishing"])

@router.post("/upload", response_model=UploadPreview)
async def upload_eml_preview(file: UploadFile = File(...)):
    """Upload EML file and get preview of extracted content."""
    
    if not file.filename.endswith('.eml'):
        raise HTTPException(status_code=400, detail="Only EML files are supported")
    
    try:
        # Read file content
        content = await file.read()
        
        # Parse EML content
        parsed_data = parse_eml_bytes(content)
        
        return UploadPreview(**parsed_data)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing EML file: {str(e)}")

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_email(request: AnalyzeRequest):
    """Analyze email content using hybrid AI + heuristic approach."""
    
    try:
        # Use hybrid analysis (heuristics + conditional AI)
        result = await hybrid_service.analyze_email(request)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing email: {str(e)}")

@router.post("/analyze-eml", response_model=AnalyzeResponse)
async def analyze_eml_file(file: UploadFile = File(...)):
    """Upload and analyze EML file using hybrid AI approach."""
    
    if not file.filename.endswith('.eml'):
        raise HTTPException(status_code=400, detail="Only EML files are supported")
    
    try:
        # Read and parse file
        content = await file.read()
        parsed_data = parse_eml_bytes(content)
        
        # Create analysis request
        request = AnalyzeRequest(**parsed_data)
        
        # Use hybrid analysis
        result = await hybrid_service.analyze_email(request)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing EML file: {str(e)}")