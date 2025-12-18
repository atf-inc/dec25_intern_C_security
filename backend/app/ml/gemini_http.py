# backend/app/ml/gemini_http.py
import os
import requests
import json
import logging
from typing import Dict, Any, Optional
from time import time

logger = logging.getLogger(__name__)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_BASE = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta/models")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Developer API key
GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "20"))

def call_gemini_raw(
    prompt: str,
    api_key: Optional[str] = None,
    model: str = GEMINI_MODEL,
    max_output_tokens: int = 400,
    temperature: float = 0.0,
) -> Dict[str, Any]:
    api_key = api_key or GEMINI_API_KEY
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not configured")

    url = f"{GEMINI_API_BASE}/{model}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_output_tokens, "temperature": temperature}
    }
    start = time()
    try:
        resp = requests.post(url, headers=headers, params=params, json=body, timeout=GEMINI_TIMEOUT)
    except requests.RequestException as ex:
        logger.exception("Gemini HTTP request failed: %s", ex)
        raise RuntimeError(f"Gemini request failed: {ex}")
    latency = time() - start
    status = resp.status_code
    try:
        raw = resp.json()
    except ValueError:
        logger.warning("Gemini returned non-JSON response")
        raise RuntimeError("Gemini returned non-JSON response")

    # parse text output from a few likely shapes
    text_out = ""
    try:
        cands = raw.get("candidates") or raw.get("response", {}).get("candidates")
        if cands and isinstance(cands, list):
            first = cands[0]
            content = first.get("content") or first.get("message") or first.get("output")
            
            # Handle content as dict with parts (Gemini 2.0 format)
            if isinstance(content, dict) and "parts" in content:
                parts = content.get("parts", [])
                if parts and isinstance(parts, list):
                    for part in parts:
                        if isinstance(part, dict) and "text" in part:
                            text_out = part.get("text", "")
                            break
            # Handle content as list (legacy format)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        text_out = part.get("text", "")
                        break
                    elif isinstance(part, str):
                        text_out = part
                        break
            elif isinstance(content, str):
                text_out = content
            elif "text" in first:
                text_out = first.get("text", "")
        if not text_out:
            out = raw.get("output") or raw.get("outputs")
            if out and isinstance(out, list):
                first = out[0]
                content = first.get("content") if isinstance(first, dict) else None
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and "text" in part:
                            text_out = part["text"]
                            break
        if not text_out:
            text_out = json.dumps(raw)[:6000]
    except Exception as ex:
        logger.exception("Error parsing Gemini response: %s", ex)
        raise RuntimeError("Failed to parse Gemini response")

    return {"text": text_out, "raw_json": raw, "status": status, "latency": latency}
