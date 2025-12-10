# app/api/v1/routes_upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.phishing import UploadPreview
from app.services.extraction_service import parse_eml_bytes, extract_links_from_pdf_bytes

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/eml", response_model=UploadPreview)
async def upload_eml(file: UploadFile = File(...)):
    content = await file.read()
    try:
        parsed = parse_eml_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse EML: {str(e)}")
    return UploadPreview(
        subject=parsed.get("subject"),
        from_name=parsed.get("from_name"),
        from_email=parsed.get("from_email"),
        to=parsed.get("to"),
        date=parsed.get("date"),
        raw_text=parsed.get("raw_text"),
        visible_links=parsed.get("visible_links"),
        hidden_links=parsed.get("hidden_links"),
        attachments=parsed.get("attachments"),
    )

@router.post("/pdf", response_model=UploadPreview)
async def upload_pdf(file: UploadFile = File(...)):
    content = await file.read()
    try:
        parsed_pdf = extract_links_from_pdf_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse PDF: {str(e)}")
    # build UploadPreview with available info
    preview = UploadPreview(
        subject=None,
        from_name=None,
        from_email=None,
        to=[],
        date=None,
        raw_text=parsed_pdf.get("raw_text"),
        visible_links=parsed_pdf.get("visible_links"),
        hidden_links=[],
        attachments=[],
    )
    # include quality info via hidden field? our schema doesn't include it - we can rely on logs
    return preview
