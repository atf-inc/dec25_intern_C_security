# backend/app/ml/phishing_model.py
from typing import List, Dict, Any
import json
import os
import logging
import re, math
from datetime import datetime
from app.ml.gemini_http import call_gemini_raw
from app.core.config import settings
import tldextract

logger = logging.getLogger(__name__)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER).lower()
HEURISTIC_THRESHOLD = int(os.getenv("HEURISTIC_THRESHOLD", settings.HEURISTIC_THRESHOLD))

URGENT_WORDS = [
    "verify", "immediately", "urgent", "click here", "password", "credential",
    "account locked", "action required", "verify your account", "confirm your identity"
]

def _dedupe_evidence(evidence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for item in evidence_list:
        try:
            key = json.dumps(item, sort_keys=True)
        except Exception:
            key = str(item)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out

def _domain_of(uri: str) -> str:
    try:
        parsed = tldextract.extract(uri or "")
        return ".".join(p for p in (parsed.domain, parsed.suffix) if p).lower()
    except Exception:
        return ""

def _url_entropy(url: str) -> float:
    if not url or "/" not in url:
        return 0.0
    path = url.split("/", 3)[-1]
    counts = {}
    for ch in path:
        counts[ch] = counts.get(ch, 0) + 1
    entropy = 0.0
    length = max(1, len(path))
    for v in counts.values():
        p = v / length
        entropy -= p * math.log2(p)
    return entropy

def _heuristic_signals(payload: Dict[str, Any]) -> Dict[str, Any]:
    reasons = []
    evidence = []
    score = 0
    text = (payload.get("raw_text") or "") or ""
    text_l = text.lower()
    if any(k in text_l for k in ["password", "passwd", "credentials", "account number", "verify your account"]):
        reasons.append("Contains credential-request keywords.")
        evidence.append({"type": "credential_request"})
        score += 35
    urgent_count = sum(1 for w in URGENT_WORDS if w in text_l)
    if urgent_count:
        reasons.append(f"Urgency language detected ({urgent_count} matches).")
        evidence.append({"type": "urgency", "count": urgent_count})
        score += min(20, 6 * urgent_count)
    visible = payload.get("visible_links") or []
    hidden = payload.get("hidden_links") or []
    for v in visible:
        anchor = (v.get("anchor_text") or "").strip()
        uri = (v.get("uri") or "").strip()
        if not uri:
            continue
        dom = _domain_of(uri)
        if anchor and "http" not in anchor and dom:
            anchor_low = anchor.lower()
            if dom.split(".")[0] not in anchor_low and anchor_low and len(anchor_low) > 1:
                reasons.append(f"Anchor text '{anchor}' does not match link domain '{dom}'.")
                evidence.append({"type": "link_mismatch", "anchor": anchor, "uri": uri})
                score += 25
        ent = _url_entropy(uri)
        if ent > 3.5:
            reasons.append(f"High URL path entropy for {uri}.")
            evidence.append({"type": "high_entropy_uri", "uri": uri, "entropy": ent})
            score += 10
    for h in hidden:
        uri = (h.get("uri") or "")
        if re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", uri):
            reasons.append("Hidden link points to raw IP address.")
            evidence.append({"type": "hidden_ip", "uri": uri})
            score += 15
    score = max(0, min(int(score), 100))
    return {"score": score, "reasons": reasons, "evidence": evidence}

def _llm_analyze(payload: Dict[str, Any]) -> Dict[str, Any]:
    if LLM_PROVIDER != "gemini":
        # mock augmentation
        heur = _heuristic_signals(payload)
        base = heur["score"]
        llm_score = max(0, min(100, base + (7 if base > 60 else -3)))
        label = "PHISHING" if llm_score >= 70 else ("SUSPICIOUS" if llm_score >= 40 else "SAFE")
        return {"label": label, "score": llm_score, "reasons": heur["reasons"] + ["LLM: mock augmentation"], "evidence": heur["evidence"], "model_meta": {"llm": "mock"}}

    # call Gemini via HTTP
    try:
        prompt = ("You are a security analyst. Return a JSON object exactly with keys: label (SAFE|SUSPICIOUS|PHISHING), "
                  "score (integer 0-100), reasons (list of short strings), evidence (list). Analyze this sanitized email JSON:\n"
                  + str(payload))
        res = call_gemini_raw(prompt, api_key=os.getenv("GEMINI_API_KEY"), model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), max_output_tokens=400, temperature=0.0)
        text = res.get("text", "")
        try:
            parsed = json.loads(text)
            return {
                "label": parsed.get("label"),
                "score": int(parsed.get("score", 50)),
                "reasons": parsed.get("reasons", []) or [],
                "evidence": parsed.get("evidence", []) or [],
                "model_meta": {"llm": "gemini-http", "latency": res.get("latency")}
            }
        except Exception:
            logger.exception("Gemini returned unparsable JSON, falling back.")
            # fallback to heuristic-based result
            heur = _heuristic_signals(payload)
            base = heur["score"]
            label = "PHISHING" if base >= 70 else ("SUSPICIOUS" if base >= 40 else "SAFE")
            return {"label": label, "score": base, "reasons": heur["reasons"], "evidence": heur["evidence"], "model_meta": {"llm": "fallback"}}
    except Exception as ex:
        logger.exception("Gemini call failed: %s", ex)
        heur = _heuristic_signals(payload)
        base = heur["score"]
        label = "PHISHING" if base >= 70 else ("SUSPICIOUS" if base >= 40 else "SAFE")
        return {"label": label, "score": base, "reasons": heur["reasons"], "evidence": heur["evidence"], "model_meta": {"llm": "error_fallback"}}

def analyze_email(payload: Dict[str, Any]) -> Dict[str, Any]:
    heur = _heuristic_signals(payload)
    # if heuristics below threshold, skip LLM
    if heur["score"] < HEURISTIC_THRESHOLD and LLM_PROVIDER == "gemini":
        # run mock LLM (or you could still run gemini if you prefer)
        merged = _llm_analyze(payload)  # for simplicity, call llm function which will fallback or mock
        heur_score = heur["score"]
        final_score = int(round(0.6 * merged.get("score", 50) + 0.4 * heur_score))
    else:
        merged = _llm_analyze(payload)
        final_score = int(round(0.6 * merged.get("score", 50) + 0.4 * heur["score"]))
    if final_score >= 70:
        label = "PHISHING"
    elif final_score >= 40:
        label = "SUSPICIOUS"
    else:
        label = "SAFE"
    reasons = list(dict.fromkeys((merged.get("reasons") or []) + heur.get("reasons", [])))
    evidence = _dedupe_evidence((merged.get("evidence") or []) + (heur.get("evidence") or []))

    return {
        "label": label,
        "score": final_score,
        "reasons": reasons,
        "evidence": evidence,
        "model_meta": merged.get("model_meta", {}),
        "timestamp": datetime.utcnow().isoformat()
    }
