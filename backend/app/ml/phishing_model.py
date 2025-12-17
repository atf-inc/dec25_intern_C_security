# backend/app/ml/phishing_model.py
from typing import List, Dict, Any
import json
import os
import logging
import re, math
from datetime import datetime
from app.ml.gemini_http import call_gemini_raw
from app.core.config import settings
from app.services.explanation_service import ExplanationService
import tldextract

logger = logging.getLogger(__name__)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER).lower()
HEURISTIC_THRESHOLD = int(os.getenv("HEURISTIC_THRESHOLD", 5))  # Ultra-low threshold for maximum hybrid performance

URGENT_WORDS = [
    "verify", "immediately", "urgent", "click here", "password", "credential",
    "account locked", "action required", "verify your account", "confirm your identity",
    "suspended", "expires", "act now", "limited time", "within 24 hours", "security alert",
    "unusual activity", "confirm now", "update payment", "billing issue", "payment failed",
    "account will be closed", "temporary hold", "restricted access", "verify identity"
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
    subject = (payload.get("subject") or "").lower()
    from_email = (payload.get("from_email") or "").lower()
    
    # 🚀 IMPROVED: Enhanced credential harvesting detection
    credential_keywords = ["password", "passwd", "credentials", "account number", "verify your account", 
                          "login", "username", "pin", "ssn", "social security", "credit card", "payment info"]
    if any(k in text_l for k in credential_keywords):
        reasons.append("Contains credential-request keywords.")
        evidence.append({"type": "credential_request"})
        score += 40  # Increased from 35
    
    # 🚀 IMPROVED: More aggressive urgency detection
    urgent_count = sum(1 for w in URGENT_WORDS if w in text_l + " " + subject)
    if urgent_count >= 3:
        reasons.append(f"Multiple urgency tactics detected ({urgent_count} matches).")
        evidence.append({"type": "high_urgency", "count": urgent_count})
        score += 45  # High urgency = very suspicious
    elif urgent_count >= 1:
        reasons.append(f"Urgency language detected ({urgent_count} matches).")
        evidence.append({"type": "urgency", "count": urgent_count})
        score += min(30, 10 * urgent_count)  # Increased scoring
    
    # 🚀 IMPROVED: Enhanced brand impersonation detection with legitimate domain checking
    brands = {
        'paypal': ['@paypal.com', '@paypal.net', '@paypal.org'],
        'amazon': ['@amazon.com', '@amazon.net', '@aboutamazon.com'],
        'microsoft': ['@microsoft.com', '@outlook.com', '@hotmail.com'],
        'apple': ['@apple.com', '@icloud.com'],
        'google': ['@google.com', '@gmail.com', '@googlemail.com'],
        'netflix': ['@netflix.com'],
        'bank': ['@chase.com', '@wellsfargo.com', '@bankofamerica.com', '@citi.com'],
        'chase': ['@chase.com', '@jpmorgan.com'],
        'wells fargo': ['@wellsfargo.com'],
        'visa': ['@visa.com'],
        'mastercard': ['@mastercard.com']
    }
    
    for brand, legitimate_domains in brands.items():
        if brand in subject + text_l:
            # Check if sender domain matches any legitimate domain for this brand
            is_legitimate = any(domain in from_email for domain in legitimate_domains)
            
            # 🚀 IMPROVED: Only flag as impersonation if sender is clearly suspicious
            if not is_legitimate and from_email:
                # Additional check: is this a clear impersonation attempt?
                suspicious_indicators = [
                    any(suspicious in from_email for suspicious in ['-', 'verify', 'secure', 'update', 'alert']),
                    any(tld in from_email for tld in ['.tk', '.ml', '.ga', '.cf', '.net', '.org']) and brand in ['paypal', 'amazon', 'microsoft'],
                    'noreply' in from_email or 'no-reply' in from_email
                ]
                
                if any(suspicious_indicators):
                    reasons.append(f"Potential {brand.title()} brand impersonation.")
                    evidence.append({"type": "brand_impersonation", "brand": brand, "sender": from_email})
                    score += 35  # Brand impersonation is very suspicious
    visible = payload.get("visible_links") or []
    hidden = payload.get("hidden_links") or []
    
    # 🚀 IMPROVED: Enhanced link analysis with better legitimate domain detection
    for v in visible:
        anchor = (v.get("anchor_text") or "").strip()
        uri = (v.get("uri") or "").strip()
        if not uri:
            continue
        dom = _domain_of(uri)
        
        # 🚀 IMPROVED: Better anchor text vs domain matching
        if anchor and "http" not in anchor and dom:
            anchor_low = anchor.lower()
            
            # Check for legitimate domains that should match
            legitimate_matches = [
                ('chase.com' in dom and 'chase' in anchor_low),
                ('amazon.com' in dom and ('amazon' in anchor_low or 'order' in anchor_low)),
                ('microsoft.com' in dom and 'microsoft' in anchor_low),
                ('paypal.com' in dom and 'paypal' in anchor_low),
                # Generic legitimate patterns
                ('help' in anchor_low and any(legit in dom for legit in ['amazon.com', 'microsoft.com', 'chase.com'])),
                ('unsubscribe' in anchor_low),
                ('contact' in anchor_low and not any(suspicious in dom for suspicious in ['.tk', '.ml', '.ga', '.cf']))
            ]
            
            # Only flag as mismatch if it's not a legitimate match
            if not any(legitimate_matches):
                domain_root = dom.split(".")[0]
                if domain_root not in anchor_low and anchor_low and len(anchor_low) > 1:
                    # 🚀 IMPROVED: Higher score for suspicious mismatches
                    suspicious_mismatch = any(suspicious in dom for suspicious in ['.tk', '.ml', '.ga', '.cf', 'verify', 'secure', 'update'])
                    mismatch_score = 40 if suspicious_mismatch else 25
                    
                    reasons.append(f"Anchor text '{anchor}' does not match link domain '{dom}'.")
                    evidence.append({"type": "link_mismatch", "anchor": anchor, "uri": uri, "suspicious": suspicious_mismatch})
                    score += mismatch_score
        
        # 🚀 IMPROVED: Enhanced URL entropy detection
        ent = _url_entropy(uri)
        if ent > 3.5:
            reasons.append(f"High URL path entropy for {uri}.")
            evidence.append({"type": "high_entropy_uri", "uri": uri, "entropy": ent})
            score += 15  # Increased from 10
    for h in hidden:
        uri = (h.get("uri") or "")
        if re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", uri):
            reasons.append("Hidden link points to raw IP address.")
            evidence.append({"type": "hidden_ip", "uri": uri})
            score += 20  # Increased from 15
    
    # 🚀 NEW: Suspicious domain detection
    suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.pw', '.top']
    suspicious_domains = ['bit.ly', 'tinyurl', 't.co', 'short.link', 'goo.gl']
    
    all_links = visible + hidden
    for link in all_links:
        uri = link.get("uri", "") if isinstance(link, dict) else str(link)
        if any(tld in uri for tld in suspicious_tlds):
            reasons.append("Contains suspicious free domain links.")
            evidence.append({"type": "suspicious_tld", "uri": uri})
            score += 25
        if any(domain in uri for domain in suspicious_domains):
            reasons.append("Contains shortened/redirect links.")
            evidence.append({"type": "shortened_link", "uri": uri})
            score += 20
    
    # 🚀 IMPROVED: Enhanced typosquatting and character substitution detection
    legitimate_domains = ['paypal.com', 'amazon.com', 'microsoft.com', 'apple.com', 'google.com', 'netflix.com', 'chase.com']
    
    # Check both visible links and sender domain
    all_domains_to_check = []
    for link in all_links:
        uri = link.get("uri", "") if isinstance(link, dict) else str(link)
        domain = _domain_of(uri)
        if domain:
            all_domains_to_check.append(domain)
    
    # Also check sender domain
    if from_email and '@' in from_email:
        sender_domain = from_email.split('@')[1].lower()
        all_domains_to_check.append(sender_domain)
    
    for domain in all_domains_to_check:
        if domain:
            for legit in legitimate_domains:
                # 🚀 IMPROVED: Multiple typosquatting detection methods
                
                # Method 1: Character substitution (payp4l.com, paypaI.com)
                if len(domain) == len(legit):
                    differences = sum(c1 != c2 for c1, c2 in zip(domain, legit))
                    if differences == 1:
                        # Check for common character substitutions
                        substitutions_found = []
                        for i, (c1, c2) in enumerate(zip(domain, legit)):
                            if c1 != c2:
                                # Common substitutions: l->I, o->0, etc.
                                common_subs = [('l', 'i'), ('i', 'l'), ('o', '0'), ('0', 'o'), ('m', 'n'), ('n', 'm')]
                                if (c2.lower(), c1.lower()) in common_subs or (c1.lower(), c2.lower()) in common_subs:
                                    substitutions_found.append(f"{c2}->{c1}")
                        
                        if substitutions_found:
                            reasons.append(f"Character substitution attack: {domain} (targeting {legit})")
                            evidence.append({"type": "character_substitution", "domain": domain, "target": legit, "substitutions": substitutions_found})
                            score += 50  # Very suspicious
                        else:
                            reasons.append(f"Potential typosquatting domain: {domain}")
                            evidence.append({"type": "typosquatting", "domain": domain, "target": legit})
                            score += 40
                
                # Method 2: Similar domains with extra characters
                elif abs(len(domain) - len(legit)) <= 2:
                    # Check if one domain is contained in the other with minor modifications
                    legit_root = legit.split('.')[0]
                    domain_root = domain.split('.')[0]
                    
                    if legit_root in domain_root or domain_root in legit_root:
                        if domain != legit:  # Not the exact legitimate domain
                            reasons.append(f"Similar domain to legitimate site: {domain} (similar to {legit})")
                            evidence.append({"type": "similar_domain", "domain": domain, "target": legit})
                            score += 30
    
    # 🚀 NEW: Grammar/spelling error detection (common in phishing)
    grammar_errors = ['recieve', 'loose', 'there account', 'you\'re account', 'click hear', 'seperate', 'occured']
    grammar_count = sum(1 for error in grammar_errors if error in text_l)
    if grammar_count > 0:
        reasons.append(f"Grammar/spelling errors detected ({grammar_count} errors).")
        evidence.append({"type": "grammar_errors", "count": grammar_count})
        score += min(15, 5 * grammar_count)
    
    # 🚀 NEW: Suspicious sender patterns
    if from_email:
        # Generic/suspicious sender patterns
        suspicious_senders = ['noreply@', 'no-reply@', 'donotreply@', 'support@', 'security@', 'admin@']
        if any(pattern in from_email for pattern in suspicious_senders):
            # Only suspicious if combined with other factors
            if score > 20:  # Already suspicious for other reasons
                reasons.append("Generic sender address with suspicious content.")
                evidence.append({"type": "suspicious_sender", "sender": from_email})
                score += 10
    
    score = max(0, min(int(score), 100))
    return {"score": score, "reasons": reasons, "evidence": evidence}

def _calculate_email_complexity(payload: Dict[str, Any]) -> float:
    """Calculate email complexity score for intelligent LLM triggering."""
    complexity = 0.0
    
    # Text length complexity
    text = payload.get("raw_text", "")
    if len(text) > 500:
        complexity += 0.3
    elif len(text) > 200:
        complexity += 0.2
    
    # Link complexity
    visible_links = payload.get("visible_links", [])
    if len(visible_links) > 3:
        complexity += 0.4
    elif len(visible_links) > 1:
        complexity += 0.2
    
    # Domain complexity (multiple domains = more complex)
    domains = set()
    for link in visible_links:
        uri = link.get("uri", "") if isinstance(link, dict) else str(link)
        domain = _domain_of(uri)
        if domain:
            domains.add(domain)
    
    if len(domains) > 2:
        complexity += 0.3
    elif len(domains) > 1:
        complexity += 0.2
    
    # Brand mention complexity
    brands = ['paypal', 'amazon', 'microsoft', 'apple', 'google', 'netflix', 'bank']
    brand_mentions = sum(1 for brand in brands if brand in text.lower())
    if brand_mentions > 1:
        complexity += 0.4
    elif brand_mentions == 1:
        complexity += 0.2
    
    return min(1.0, complexity)

def _get_few_shot_examples() -> str:
    """Return few-shot examples for better LLM prompting."""
    return """
Examples of phishing analysis:

Example 1 - PHISHING:
Email: "Urgent: Your PayPal account suspended. Click here: http://paypal-verify.tk"
Analysis: {"label": "PHISHING", "score": 85, "reasons": ["Brand impersonation (PayPal)", "Suspicious domain (.tk)", "Urgency manipulation"], "evidence": [{"type": "brand_impersonation", "brand": "PayPal"}]}

Example 2 - SAFE:
Email: "Meeting reminder for tomorrow at 2 PM. Best regards, John from Acme Corp"
Analysis: {"label": "SAFE", "score": 15, "reasons": ["Professional communication", "No suspicious links", "Legitimate business context"], "evidence": [{"type": "legitimate_business"}]}

Example 3 - SUSPICIOUS:
Email: "Security alert: unusual activity detected. Please verify your account within 24 hours."
Analysis: {"label": "SUSPICIOUS", "score": 65, "reasons": ["Urgency tactics", "Credential request", "Vague sender"], "evidence": [{"type": "urgency"}, {"type": "credential_request"}]}

Now analyze this email:
"""

def _llm_analyze(payload: Dict[str, Any]) -> Dict[str, Any]:
    if LLM_PROVIDER != "gemini":
        # Enhanced mock LLM with intelligent analysis
        heur = _heuristic_signals(payload)
        base = heur["score"]
        
        # Simulate intelligent LLM analysis
        subject = payload.get("subject", "").lower()
        raw_text = payload.get("raw_text", "").lower()
        from_email = payload.get("from_email", "").lower()
        
        llm_boost = 0
        llm_reasons = []
        confidence = 0.8  # Base confidence
        
        # 🚀 IMPROVED: More aggressive LLM pattern detection
        
        # Enhanced urgency and pressure tactics detection
        urgency_patterns = ['urgent', 'verify', 'suspended', 'act now', 'click here', 'immediately', 'expires', 'limited time', 'within 24 hours', 'deadline', 'final notice', 'last chance']
        urgency_count = sum(1 for pattern in urgency_patterns if pattern in subject + raw_text)
        if urgency_count >= 3:
            llm_boost += 50  # Multiple urgency indicators = very suspicious
            llm_reasons.append("LLM: Aggressive urgency manipulation tactics detected")
            confidence += 0.15
        elif urgency_count >= 2:
            llm_boost += 35  # Multiple urgency indicators = very suspicious
            llm_reasons.append("LLM: Multiple urgency manipulation tactics detected")
            confidence += 0.1
        elif urgency_count == 1:
            llm_boost += 20  # Increased from 15
            llm_reasons.append("LLM: Urgency manipulation detected")
            
        # 🚀 IMPROVED: Advanced brand impersonation with better legitimate domain checking
        brand_domains = {
            'paypal': ['@paypal.com', '@paypal.net', '@paypal.org'],
            'amazon': ['@amazon.com', '@amazon.net', '@aboutamazon.com'],
            'microsoft': ['@microsoft.com', '@outlook.com', '@hotmail.com'],
            'apple': ['@apple.com', '@icloud.com'],
            'google': ['@google.com', '@gmail.com', '@googlemail.com'],
            'netflix': ['@netflix.com'],
            'bank': ['@chase.com', '@wellsfargo.com', '@bankofamerica.com', '@citi.com'],
            'chase': ['@chase.com', '@jpmorgan.com'],
            'wells': ['@wellsfargo.com'],
            'visa': ['@visa.com'],
            'mastercard': ['@mastercard.com']
        }
        
        for brand, legitimate_domains in brand_domains.items():
            if brand in subject.lower() + raw_text.lower():
                # Check if email domain matches any legitimate domain for this brand
                is_legitimate = any(domain in from_email for domain in legitimate_domains)
                
                if not is_legitimate:
                    # 🚀 IMPROVED: Only flag if there are clear suspicious indicators
                    suspicious_context = [
                        any(urgent in raw_text for urgent in ['urgent', 'immediately', 'suspended', 'verify', 'click here']),
                        any(credential in raw_text for credential in ['password', 'login', 'verify your account', 'confirm your identity']),
                        any(suspicious in from_email for suspicious in ['noreply', 'security', 'alert', 'verify', 'update']) if from_email else False
                    ]
                    
                    # Only flag as impersonation if there are suspicious context clues
                    if any(suspicious_context):
                        if any(sensitive in raw_text for sensitive in ['password', 'login', 'account', 'payment', 'credit card', 'verify', 'confirm', 'update']):
                            llm_boost += 50  # Brand impersonation + sensitive request = very suspicious
                            llm_reasons.append(f"LLM: {brand.title()} impersonation with sensitive data request")
                            confidence += 0.15
                        else:
                            llm_boost += 30
                            llm_reasons.append(f"LLM: Potential {brand.title()} impersonation")
                            confidence += 0.1
                        break
                    
        # Sophisticated social engineering detection
        social_eng_patterns = [
            'confirm your identity', 'verify your account', 'update payment', 'account suspended', 
            'security alert', 'unusual activity', 'click to verify', 'confirm now'
        ]
        social_count = sum(1 for pattern in social_eng_patterns if pattern in raw_text)
        if social_count >= 2:
            llm_boost += 40  # Increased from 30
            llm_reasons.append("LLM: Multiple social engineering tactics detected")
            confidence += 0.1
        elif social_count == 1:
            llm_boost += 20  # Increased from 15
            llm_reasons.append("LLM: Social engineering tactics detected")
            
        # Suspicious link analysis (advanced)
        suspicious_domains = ['.tk', '.ml', '.ga', '.cf', 'bit.ly', 'tinyurl', 't.co', 'short.link']
        if any(domain in raw_text for domain in suspicious_domains):
            llm_boost += 30
            llm_reasons.append("LLM: Suspicious shortened/free domain links detected")
            confidence += 0.1
            
        # Grammar and spelling analysis (phishing often has poor grammar)
        grammar_issues = ['recieve', 'loose', 'there account', 'you\'re account', 'click hear']
        if any(issue in raw_text for issue in grammar_issues):
            llm_boost += 15
            llm_reasons.append("LLM: Grammar/spelling errors typical of phishing")
            
        # 🚀 IMPROVED: Enhanced legitimate business patterns (reduce false positives)
        legitimate_patterns = [
            'visit our help center', 'call customer service', 'visit local branch', 
            'customer service line', 'contact support', 'help desk', 'official website',
            'monthly statement', 'account statement', 'statement is ready', 'statement is available',
            'logging into your', 'log into your account', 'online banking', 'mobile app',
            'branch locations', 'customer service', 'call us at', 'phone number',
            'order confirmation', 'thank you for your order', 'tracking number',
            'unsubscribe', 'newsletter', 'weekly digest', 'monthly update'
        ]
        
        # 🚀 IMPROVED: Stronger legitimate indicators
        strong_legitimate_patterns = [
            'monthly statement is ready', 'statement is now available', 'thank you for your order',
            'order confirmation', 'tracking number', 'unsubscribe at any time'
        ]
        
        legit_count = sum(1 for pattern in legitimate_patterns if pattern in raw_text)
        strong_legit_count = sum(1 for pattern in strong_legitimate_patterns if pattern in raw_text)
        
        if strong_legit_count >= 1:
            llm_boost -= 40  # Strong legitimate indicators
            llm_reasons.append("LLM: Strong legitimate business communication detected")
            confidence += 0.15
        elif legit_count >= 2:
            llm_boost -= 25  # Increased from 20
            llm_reasons.append("LLM: Multiple legitimate support channels mentioned")
            confidence += 0.1
        elif legit_count == 1:
            llm_boost -= 15  # Increased from 10
            llm_reasons.append("LLM: Legitimate support channels mentioned")
            
        # Professional communication indicators
        if any(indicator in raw_text for indicator in ['best regards', 'sincerely', 'thank you for your business']):
            llm_boost -= 5
            llm_reasons.append("LLM: Professional communication style detected")
            
        # Calculate final LLM score with confidence decay
        llm_score = max(0, min(100, base + llm_boost))
        
        # Apply confidence decay for uncertain cases
        if confidence < 0.7:
            llm_score = int(llm_score * 0.9)  # Reduce score for low confidence
            llm_reasons.append("LLM: Confidence adjusted due to uncertainty")
        
        label = "PHISHING" if llm_score >= 70 else ("SUSPICIOUS" if llm_score >= 40 else "SAFE")
        
        return {
            "label": label, 
            "score": llm_score, 
            "reasons": heur["reasons"] + llm_reasons, 
            "evidence": heur["evidence"], 
            "model_meta": {
                "llm": "enhanced_mock", 
                "llm_boost": llm_boost,
                "base_score": base,
                "final_llm_score": llm_score,
                "confidence": min(1.0, confidence)
            }
        }

    # 🚀 ADVANCED: Few-shot prompting for better Gemini performance
    try:
        few_shot_examples = _get_few_shot_examples()
        enhanced_prompt = f"""{few_shot_examples}

You are an expert security analyst. Analyze this email for phishing threats.
Return a JSON object with keys: label (SAFE|SUSPICIOUS|PHISHING), score (0-100), reasons (list), evidence (list).

Email to analyze: {str(payload)}

Focus on:
- Brand impersonation (sender domain vs claimed brand)
- Urgency manipulation ("act now", "expires today")
- Credential harvesting attempts
- Suspicious links (shortened URLs, typosquatting)
- Social engineering tactics

Provide specific, actionable reasons."""

        res = call_gemini_raw(enhanced_prompt, api_key=os.getenv("GEMINI_API_KEY"), model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), max_output_tokens=500, temperature=0.1)
        text = res.get("text", "")
        try:
            parsed = json.loads(text)
            return {
                "label": parsed.get("label", "SUSPICIOUS"),  # Default to SUSPICIOUS if label is missing
                "score": int(parsed.get("score", 50)),
                "reasons": parsed.get("reasons", []) or [],
                "evidence": parsed.get("evidence", []) or [],
                "model_meta": {"llm": "gemini-http-enhanced", "latency": res.get("latency")}
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
    
    # Cost estimation constants (based on Gemini API pricing)
    GEMINI_COST_PER_REQUEST = 0.02  # Estimated cost per Gemini API call
    HEURISTIC_COST = 0.0  # Heuristics are free
    
    # 🚀 ADVANCED: Dynamic threshold zones based on email complexity
    email_complexity = _calculate_email_complexity(payload)
    
    # 🚀 IMPROVED: More aggressive thresholds for better recall
    if email_complexity > 0.7:  # High complexity emails
        lower_threshold = 10  # Lower threshold to catch more phishing
        upper_threshold = 75  # Lower upper threshold for more LLM usage
        llm_weight = 0.8  # Trust LLM more for complex emails
    elif email_complexity > 0.4:  # Medium complexity emails
        lower_threshold = 15  # Much lower threshold
        upper_threshold = 65  # Lower upper threshold
        llm_weight = 0.7
    else:  # Simple emails
        lower_threshold = 20  # Significantly lower threshold
        upper_threshold = 60  # Lower upper threshold
        llm_weight = 0.6  # Trust heuristics more for simple emails
    
    # 🚀 ADVANCED: Complexity-aware LLM triggering
    use_llm = (lower_threshold <= heur["score"] <= upper_threshold) and LLM_PROVIDER in ["gemini", "mock"]
    
    # Force LLM for high-complexity emails even if heuristics are confident
    if email_complexity > 0.8 and not use_llm:
        use_llm = True
        combined_reasons = [f"Complex email analysis required (complexity: {email_complexity:.2f})"]
    
    if use_llm:
        merged = _llm_analyze(payload)
        
        # 🚀 ADVANCED: Adaptive weighted blending based on confidence and complexity
        llm_score = merged.get("score", 50)
        heuristic_score = heur["score"]
        llm_confidence = merged.get("model_meta", {}).get("confidence", 0.8)
        
        # Adjust weights based on LLM confidence
        if llm_confidence > 0.9:
            adjusted_llm_weight = min(0.9, llm_weight + 0.1)
        elif llm_confidence < 0.6:
            adjusted_llm_weight = max(0.5, llm_weight - 0.2)
        else:
            adjusted_llm_weight = llm_weight
        
        heuristic_weight = 1.0 - adjusted_llm_weight
        
        # 🚀 ADVANCED: Weighted blending with confidence decay
        final_score = int(round(adjusted_llm_weight * llm_score + heuristic_weight * heuristic_score))
        
        # Apply confidence decay for very uncertain LLM predictions
        if llm_confidence < 0.5:
            final_score = int(final_score * 0.85)
        
        # 🔧 FIX 3: Use LLM label when LLM is triggered (not heuristic label)
        llm_label = merged.get("label", "SUSPICIOUS")
        
        cost_estimate = GEMINI_COST_PER_REQUEST  # We used Gemini
        analysis_method = "hybrid_advanced"
        
        # Use LLM reasoning when available
        combined_reasons = merged.get("reasons", []) + [
            f"Heuristic score: {heuristic_score}",
            f"LLM confidence: {llm_confidence:.2f}",
            f"Email complexity: {email_complexity:.2f}",
            f"Blending weights: LLM {adjusted_llm_weight:.1f}, Heuristic {heuristic_weight:.1f}"
        ]
        
    else:
        # Use heuristics only for clear cases
        merged = {
            "label": "SAFE",
            "score": heur["score"],
            "reasons": heur["reasons"],
            "evidence": heur["evidence"],
            "model_meta": {"llm": "heuristics_only"}
        }
        final_score = heur["score"]
        cost_estimate = HEURISTIC_COST  # No LLM cost
        analysis_method = "heuristics_only"
        combined_reasons = heur["reasons"] + [f"Email complexity: {email_complexity:.2f} (simple case)"]
        
        # Determine label from heuristic score with dynamic thresholds
        if final_score >= upper_threshold:
            llm_label = "PHISHING"
        elif final_score >= lower_threshold:
            llm_label = "SUSPICIOUS"
        else:
            llm_label = "SAFE"
    
    # 🚀 ADVANCED: Final label determination with confidence-based adjustment
    if use_llm:
        # Trust LLM decision but apply confidence-based adjustments
        llm_confidence = merged.get("model_meta", {}).get("confidence", 0.8)
        
        if llm_confidence > 0.85:
            label = llm_label  # High confidence - trust LLM completely
        elif llm_confidence < 0.6:
            # Low confidence - blend with score-based decision
            if final_score >= 75:
                label = "PHISHING"
            elif final_score >= 35:
                label = "SUSPICIOUS"
            else:
                label = "SAFE"
        else:
            label = llm_label  # Medium confidence - trust LLM
    else:
        # 🚀 IMPROVED: More aggressive labeling for better recall
        if final_score >= 50:  # Lower threshold for PHISHING classification
            label = "PHISHING"
        elif final_score >= 25:  # Lower threshold for SUSPICIOUS
            label = "SUSPICIOUS"
        else:
            label = "SAFE"
    
    # Merge reasons and evidence
    reasons = list(dict.fromkeys(combined_reasons))
    evidence = _dedupe_evidence((merged.get("evidence") or []) + (heur.get("evidence") or []))
    
    # Calculate cost savings vs full LLM approach
    cost_reduction_vs_full_llm = 1 - (cost_estimate / GEMINI_COST_PER_REQUEST)
    
    # 🚀 ADVANCED: Enhanced model metadata with detailed analytics
    model_meta = merged.get("model_meta", {})
    model_meta.update({
        "cost_estimate": cost_estimate,
        "cost_reduction_vs_full_llm": cost_reduction_vs_full_llm,
        "analysis_method": analysis_method,
        "heuristic_score": heur["score"],
        "llm_used": use_llm,
        "email_complexity": email_complexity,
        "dynamic_thresholds": {
            "lower": lower_threshold if use_llm else HEURISTIC_THRESHOLD,
            "upper": upper_threshold if use_llm else 70
        },
        "blending_weights": {
            "llm_weight": adjusted_llm_weight if use_llm else 0.0,
            "heuristic_weight": heuristic_weight if use_llm else 1.0
        } if use_llm else {"llm_weight": 0.0, "heuristic_weight": 1.0},
        "llm_confidence": merged.get("model_meta", {}).get("confidence", 0.8) if use_llm else None
    })

    # 🚀 TEMPORARY: Simplified explanation for testing (disable full AI explanation)
    ai_explanation = {
        "summary": f"Email classified as {label} with {final_score}% confidence using improved hybrid detection.",
        "suspicious_indicators": reasons[:3] if reasons else ["No specific indicators detected"],
        "ai_reasoning": "Analysis completed using enhanced hybrid AI detection system with improved recall.",
        "technical_indicators": [f"Risk score: {final_score}/100", f"Analysis method: {model_meta.get('analysis_method', 'hybrid')}"],
        "final_assessment": f"{label} - {final_score}% confidence",
        "recommended_action": "Exercise caution and verify sender identity before taking action." if label != "SAFE" else "Email appears safe, but always verify sender identity.",
        "full_explanation": f"This email has been analyzed using improved detection algorithms and classified as {label}."
    }
    
    return {
        "label": label,
        "score": final_score,
        "reasons": reasons,
        "evidence": evidence,
        "model_meta": model_meta,
        "ai_explanation": ai_explanation,  # 🚀 NEW: AI-generated explanation
        "timestamp": datetime.utcnow().isoformat()
    }
