# backend/app/services/extraction_service.py
from typing import Dict, List, Any
from email import message_from_bytes
from email.policy import default
from bs4 import BeautifulSoup
import re
import fitz  # pymupdf

def extract_links_from_html(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html or "", "html.parser")
    links = []
    for a in soup.find_all("a"):
        links.append({"anchor_text": a.get_text(strip=True), "uri": a.get("href")})
    return links

def parse_eml_bytes(raw_bytes: bytes) -> Dict[str, Any]:
    msg = message_from_bytes(raw_bytes, policy=default)
    subject = msg.get("subject")
    from_name = None
    from_email = None
    if msg["from"]:
        fr = msg.get("from")
        if "<" in fr and ">" in fr:
            name_part, email_part = fr.split("<", 1)
            from_name = name_part.strip().strip('"')
            from_email = email_part.replace(">", "").strip()
        else:
            from_email = fr.strip()

    to_raw = msg.get_all("to", [])
    to_list = []
    for t in to_raw:
        parts = [x.strip() for x in t.split(",")]
        to_list.extend(parts)

    raw_text = ""
    html_text = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                try:
                    raw_text += part.get_content() or ""
                except Exception:
                    raw_text += (part.get_payload(decode=True) or b"").decode(errors="ignore")
            elif ctype == "text/html":
                try:
                    html_text += part.get_content() or ""
                except Exception:
                    html_text += (part.get_payload(decode=True) or b"").decode(errors="ignore")
    else:
        ctype = msg.get_content_type()
        if ctype == "text/plain":
            raw_text = msg.get_content() or ""
        elif ctype == "text/html":
            html_text = msg.get_content() or ""

    visible_links = extract_links_from_html(html_text)
    hidden_links = []
    for m in re.findall(r"(https?://[^\s'\"<>]+)", raw_text):
        hidden_links.append({"display_text": m, "uri": m})
    attachments = []
    for part in msg.iter_attachments():
        attachments.append({
            "filename": part.get_filename(),
            "mimetype": part.get_content_type(),
            "size": len(part.get_payload(decode=True) or b"")
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
        "attachments": attachments
    }

def extract_links_from_pdf_bytes(pdf_bytes: bytes) -> Dict[str, Any]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    visible_links = []
    raw_text_parts = []
    for pageno in range(len(doc)):
        page = doc[pageno]
        text = page.get_text("text")
        raw_text_parts.append(text)
        links = page.get_links()
        if not links:
            continue
        text_dict = page.get_text("dict")
        spans = []
        for block in text_dict.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    spans.append({"text": span.get("text", ""), "bbox": span.get("bbox", [])})
        for link in links:
            uri = link.get("uri") or link.get("url")
            if not uri:
                continue
            link_bbox = link.get("from")
            anchor = None
            if link_bbox and spans:
                x0, y0, x1, y1 = link_bbox
                candidates = []
                for s in spans:
                    sb = s.get("bbox") or []
                    if len(sb) < 4:
                        continue
                    sx0, sy0, sx1, sy1 = sb
                    horiz_overlap = not (sx1 < x0 or sx0 > x1)
                    vert_overlap = not (sy1 < y0 or sy0 > y1)
                    if horiz_overlap and vert_overlap:
                        candidates.append(s.get("text").strip())
                if candidates:
                    anchor = " ".join([c for c in candidates if c])
            if not anchor and uri in text:
                anchor = uri
            visible_links.append({"anchor_text": anchor, "uri": uri, "page": pageno+1})
    doc.close()
    raw_text = "\n\n".join(raw_text_parts)
    quality = "high" if visible_links else "low"
    return {"raw_text": raw_text, "visible_links": visible_links, "link_parsing_quality": quality}
