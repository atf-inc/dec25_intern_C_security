# backend/app/api/v1/routes_upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.phishing import UploadPreview
from app.services.extraction_service import parse_eml_bytes, extract_links_from_pdf_bytes

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/eml", response_model=UploadPreview)
async def upload_eml(file: UploadFile = File(...)):
    import logging
    logger = logging.getLogger(__name__)
    
    # Log upload attempt
    logger.info(f"EML upload attempt: filename={file.filename}, content_type={file.content_type}")
    
    content = await file.read()
    
    # Check if file is empty
    if not content:
        raise HTTPException(status_code=422, detail="Empty EML file uploaded")
    
    # Log file info
    logger.info(f"EML file info: size={len(content)} bytes")
    logger.info(f"EML first 200 chars: {content[:200]}")
    
    try:
        parsed = parse_eml_bytes(content)
        logger.info(f"EML parsed successfully: subject='{parsed.get('subject', 'N/A')[:50]}...'")
    except Exception as e:
        logger.error(f"EML parsing failed: {str(e)}")
        logger.error(f"EML content preview: {content[:500]}")
        
        # Try a fallback approach for complex Gmail EML files
        try:
            # Fallback: Basic text extraction without full parsing
            content_str = content.decode('utf-8', errors='ignore')
            
            # Extract basic fields using simple regex
            import re
            subject_match = re.search(r'^Subject:\s*(.+)$', content_str, re.MULTILINE | re.IGNORECASE)
            from_match = re.search(r'^From:\s*(.+)$', content_str, re.MULTILINE | re.IGNORECASE)
            to_match = re.search(r'^To:\s*(.+)$', content_str, re.MULTILINE | re.IGNORECASE)
            date_match = re.search(r'^Date:\s*(.+)$', content_str, re.MULTILINE | re.IGNORECASE)
            
            # Extract email from From field if it contains name and email
            from_email = None
            from_name = None
            if from_match:
                from_text = from_match.group(1).strip()
                email_match = re.search(r'<([^>]+)>', from_text)
                if email_match:
                    from_email = email_match.group(1)
                    from_name = from_text.replace(f'<{from_email}>', '').strip().strip('"')
                else:
                    from_email = from_text
            
            # Find URLs in the content
            url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s<>"\']*'
            urls = re.findall(url_pattern, content_str, re.IGNORECASE)
            
            # Try to extract the main body (after headers)
            body_start = content_str.find('\n\n')
            if body_start > 0:
                raw_text = content_str[body_start:].strip()
            else:
                raw_text = content_str
            
            parsed = {
                "subject": subject_match.group(1).strip() if subject_match else "Unknown Subject",
                "from_name": from_name,
                "from_email": from_email or "unknown@example.com",
                "to": [to_match.group(1).strip()] if to_match else [],
                "date": date_match.group(1).strip() if date_match else None,
                "raw_text": raw_text,
                "visible_links": [],
                "hidden_links": [{"anchor_text": None, "uri": url, "page": None} for url in urls[:10]],  # Limit to 10 URLs
                "attachments": [],
                "parsing_method": "fallback_regex"
            }
            
            logger.info(f"EML fallback parsing successful: subject='{parsed.get('subject', 'N/A')[:50]}...'")
            
        except Exception as fallback_error:
            logger.error(f"EML fallback parsing also failed: {str(fallback_error)}")
            raise HTTPException(
                status_code=422, 
                detail=f"Failed to parse EML file. Original error: {str(e)}. Fallback error: {str(fallback_error)}. File size: {len(content)} bytes. Please ensure this is a valid .eml email file."
            )
    
    return UploadPreview(
        subject=parsed.get("subject"),
        from_name=parsed.get("from_name"),
        from_email=parsed.get("from_email"),
        to=parsed.get("to"),
        date=parsed.get("date"),
        raw_text=parsed.get("raw_text"),
        visible_links=parsed.get("visible_links"),
        hidden_links=parsed.get("hidden_links"),
        attachments=parsed.get("attachments")
    )

@router.post("/pdf", response_model=UploadPreview)
async def upload_pdf(file: UploadFile = File(...)):
    import logging
    logger = logging.getLogger(__name__)
    
    # Log upload attempt
    logger.info(f"PDF upload attempt: filename={file.filename}, content_type={file.content_type}")
    
    content = await file.read()
    
    # Check if file is empty
    if not content:
        raise HTTPException(status_code=422, detail="Empty PDF file uploaded")
    
    # Log file info
    logger.info(f"PDF file info: size={len(content)} bytes, starts_with_pdf_header={content.startswith(b'%PDF')}")
    
    # More flexible PDF validation - some PDFs might not have exact content-type
    is_pdf_by_extension = file.filename and file.filename.lower().endswith('.pdf')
    is_pdf_by_header = content.startswith(b'%PDF')
    is_pdf_by_content_type = file.content_type and 'pdf' in file.content_type.lower()
    
    if not (is_pdf_by_extension or is_pdf_by_header or is_pdf_by_content_type):
        raise HTTPException(
            status_code=422, 
            detail=f"File does not appear to be a PDF. Content-type: {file.content_type}, Filename: {file.filename}, Has PDF header: {is_pdf_by_header}"
        )
    
    try:
        parsed_pdf = extract_links_from_pdf_bytes(content)
        logger.info(f"PDF parsed successfully with main parser")
    except Exception as e:
        logger.error(f"PDF main parsing failed: {str(e)}")
        
        # For Gmail PDFs and other complex PDFs, try multiple fallback approaches
        try:
            # Fallback 1: PyMuPDF (fitz) - most robust
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            text_parts = []
            urls = []
            
            for page_num, page in enumerate(doc):
                # Extract text
                page_text = page.get_text()
                text_parts.append(page_text)
                
                # Extract links
                links = page.get_links()
                for link in links:
                    if 'uri' in link:
                        urls.append(link['uri'])
            
            doc.close()
            
            # Find URLs in text as well using regex
            import re
            full_text = "\n\n".join(text_parts)
            url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s<>"\']*'
            text_urls = re.findall(url_pattern, full_text, re.IGNORECASE)
            
            # Combine and deduplicate URLs
            all_urls = list(set(urls + text_urls))
            
            parsed_pdf = {
                "raw_text": full_text,
                "visible_links": [{"anchor_text": None, "uri": url, "page": None} for url in all_urls[:20]],  # Limit to 20 URLs
                "parsing_method": "fallback_fitz"
            }
            
            logger.info(f"PDF fallback parsing successful with fitz: {len(text_parts)} pages, {len(all_urls)} URLs")
            
        except Exception as fitz_error:
            logger.error(f"PDF fitz fallback failed: {str(fitz_error)}")
            
            try:
                # Fallback 2: Basic text extraction only
                import fitz
                doc = fitz.open(stream=content, filetype="pdf")
                text_parts = []
                for page in doc:
                    text_parts.append(page.get_text())
                doc.close()
                
                parsed_pdf = {
                    "raw_text": "\n\n".join(text_parts),
                    "visible_links": [],
                    "parsing_method": "fallback_text_only"
                }
                
                logger.info(f"PDF basic text extraction successful: {len(text_parts)} pages")
                
            except Exception as basic_error:
                logger.error(f"PDF basic extraction failed: {str(basic_error)}")
                
                # Fallback 3: Return minimal info
                parsed_pdf = {
                    "raw_text": f"PDF file uploaded ({len(content)} bytes) but text extraction failed. Original error: {str(e)}",
                    "visible_links": [],
                    "parsing_method": "fallback_minimal"
                }
                
                logger.warning(f"PDF parsing completely failed, using minimal fallback")
    
    preview = UploadPreview(
        subject=f"PDF Email Document" if parsed_pdf.get("raw_text") else "PDF Upload",
        from_name=None,
        from_email="pdf-upload@system.local",  # Placeholder for PDF uploads
        to=[],
        date=None,
        raw_text=parsed_pdf.get("raw_text", ""),
        visible_links=parsed_pdf.get("visible_links", []),
        hidden_links=[],
        attachments=[]
    )
    return preview

@router.post("/manual", response_model=UploadPreview)
async def parse_manual(payload: UploadPreview):
    # simple pass-through: frontend sanitized & sends manual fields
    return payload