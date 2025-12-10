# app/services/extraction_service.py
from email import message_from_bytes
from email.policy import default
import mailparser
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re
import fitz  # pymupdf

def extract_links_from_html(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a"):
        links.append({
            "anchor_text": a.get_text(strip=True),
            "uri": a.get("href")
        })
    return links

def parse_eml_bytes(raw_bytes: bytes) -> Dict:
    """Parse EML file bytes and extract email content and metadata."""
    msg = message_from_bytes(raw_bytes, policy=default)

    # --- Subject ---
    subject = msg.get("subject")

    # --- From ---
    from_name = None
    from_email = None
    if msg["from"]:
        # Format: Name <email@example.com>
        from_email = msg.get("from")
        if "<" in from_email and ">" in from_email:
            name_part, email_part = from_email.split("<", 1)
            from_name = name_part.strip().strip('"')
            from_email = email_part.replace(">", "").strip()

    # --- To (list) ---
    to_raw = msg.get_all("to", [])
    to_list = []
    for t in to_raw:
        # multiple addresses may be combined inside the header
        parts = [x.strip() for x in t.split(",")]
        to_list.extend(parts)

    # --- Extract plain text & HTML ---
    raw_text = ""
    html_text = ""

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    raw_text += payload.decode("utf-8", errors="ignore")
            elif ctype == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    html_text += payload.decode("utf-8", errors="ignore")
    else:
        # Single part message
        ctype = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload:
            content = payload.decode("utf-8", errors="ignore")
            if ctype == "text/plain":
                raw_text = content
            elif ctype == "text/html":
                html_text = content

    # If we only have HTML, extract text from it
    if not raw_text and html_text:
        soup = BeautifulSoup(html_text, "html.parser")
        raw_text = soup.get_text()

    # --- Extract links ---
    visible_links = []
    hidden_links = []
    
    if html_text:
        visible_links = extract_links_from_html(html_text)
    
    # Also look for URLs in plain text
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    text_urls = re.findall(url_pattern, raw_text)
    for url in text_urls:
        # Avoid duplicates
        if not any(link.get("uri") == url for link in visible_links):
            visible_links.append({
                "anchor_text": url,
                "uri": url
            })

    return {
        "subject": subject,
        "from_name": from_name,
        "from_email": from_email,
        "to": to_list,
        "date": msg.get("date"),
        "raw_text": raw_text,
        "visible_links": visible_links,
        "hidden_links": hidden_links,
        "attachments": []  # TODO: Extract attachment info if needed
    }

def extract_links_from_pdf_bytes(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Extract text and link annotations from PDF bytes.
    Returns dict with: raw_text, visible_links (anchor_text+uri), link_parsing_quality.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    visible_links: List[Dict[str, Any]] = []
    raw_text_parts: List[str] = []
    
    # For each page: gather link annotations and text spans (with bboxes)
    for pageno in range(len(doc)):
        page = doc[pageno]
        # Get page text as plain
        text = page.get_text("text")
        raw_text_parts.append(text)
        
        # Get annotation links
        links = page.get_links()  # list of dicts with 'uri' and 'from' bbox
        if not links:
            continue
            
        # get dict text spans with bbox
        text_dict = page.get_text("dict")
        spans = []
        for block in text_dict.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    spans.append({
                        "text": span.get("text", ""),
                        "bbox": span.get("bbox", []),
                    })
        
        # For each link annotation, try to find anchor text whose bbox intersects the link bbox
        for link in links:
            uri = link.get("uri") or link.get("url")
            if not uri:
                continue
            link_bbox = link.get("from")  # [x0, y0, x1, y1]
            anchor = None
            
            if link_bbox and spans:
                # find spans whose bbox intersects link bbox
                x0, y0, x1, y1 = link_bbox
                candidates = []
                for s in spans:
                    sb = s["bbox"]
                    if not sb or len(sb) < 4:
                        continue
                    sx0, sy0, sx1, sy1 = sb
                    # simple intersection test
                    horiz_overlap = not (sx1 < x0 or sx0 > x1)
                    vert_overlap = not (sy1 < y0 or sy0 > y1)
                    if horiz_overlap and vert_overlap:
                        candidates.append(s["text"].strip())
                if candidates:
                    # join nearby small spans
                    anchor = " ".join([c for c in candidates if c])
            
            # fallback: try to find visible/printed URL in page text close to uri
            if not anchor:
                # simple heuristic: match the display text if uri appears in text
                if uri in text:
                    anchor = uri
                else:
                    anchor = uri  # fallback to URI itself
            
            visible_links.append({
                "anchor_text": anchor,
                "uri": uri
            })
    
    doc.close()
    
    # Also extract URLs from plain text using regex
    full_text = "\n".join(raw_text_parts)
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    text_urls = re.findall(url_pattern, full_text)
    
    for url in text_urls:
        # Avoid duplicates
        if not any(link.get("uri") == url for link in visible_links):
            visible_links.append({
                "anchor_text": url,
                "uri": url
            })
    
    return {
        "raw_text": full_text,
        "visible_links": visible_links
    }