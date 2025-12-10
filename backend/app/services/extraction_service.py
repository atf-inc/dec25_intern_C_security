# app/services/extraction_service.py
from mailparser import MailParser
from typing import Dict, List
from bs4 import BeautifulSoup
import re

def extract_links_from_html(html: str):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a"):
        anchor = (a.get_text() or "").strip()
        uri = a.get("href")
        links.append({"anchor_text": anchor, "uri": uri})
    return links

def parse_eml_bytes(raw_bytes: bytes) -> Dict:
    mp = MailParser()
    mp.parse_from_bytes(raw_bytes)
    subject = mp.subject
    from_name, from_email = None, None
    if mp.from_:
        from_name = mp.from_[0].get("name")
        from_email = mp.from_[0].get("mail")
    to_list = [t.get("mail") for t in mp.to or [] if t.get("mail")]
    date = mp.date
    text = mp.body or ""
    html = mp.body or ""
    # attempt HTML extraction if html part exists
    if mp.html_attaches:
        # mailparser sets html in body sometimes; if not, fallback
        html = mp.html_attaches[0].get("content", "") if mp.html_attaches else mp.body
    visible_links = extract_links_from_html(html or "")
    # hidden links - attempt to find URIs inside text that are not anchor href
    hidden_links = []
    for match in re.findall(r"(https?://[^\s'\"]+)", text or ""):
        hidden_links.append({"display_text": match, "uri": match})
    attachments = []
    for att in mp.attachments or []:
        attachments.append({"filename": att.get("filename"), "mimetype": att.get("mail_content_type"), "size": len(att.get("payload") or b"")})
    return {
        "subject": subject,
        "from_name": from_name,
        "from_email": from_email,
        "to": to_list,
        "date": str(date),
        "raw_text": text,
        "visible_links": visible_links,
        "hidden_links": hidden_links,
        "attachments": attachments
    }
