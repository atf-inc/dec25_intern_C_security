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

# 🚀 IMPROVED: Trusted domains to reduce false positives
TRUSTED_DOMAINS = [
    'github.com', 'gitlab.com', 'bitbucket.org',  # Code repositories
    'google.com', 'gmail.com', 'googlemail.com', 'calendar.google.com',  # Google services
    'microsoft.com', 'outlook.com', 'hotmail.com', 'live.com',  # Microsoft
    'apple.com', 'icloud.com',  # Apple
    'amazon.com', 'amazon.net', 'aboutamazon.com',  # Amazon
    'paypal.com', 'paypal.net', 'paypal.org',  # PayPal
    'netflix.com',  # Netflix
    'chase.com', 'jpmorgan.com',  # Chase
    'wellsfargo.com',  # Wells Fargo
    'bankofamerica.com',  # Bank of America
    'citi.com',  # Citi
    'visa.com', 'mastercard.com',  # Credit cards
    'linkedin.com',  # LinkedIn
    'facebook.com', 'meta.com',  # Meta/Facebook
    'twitter.com', 'x.com',  # Twitter/X
    'slack.com',  # Slack
    'zoom.us',  # Zoom
    'dropbox.com',  # Dropbox
    'atlassian.com', 'atlassian.net',  # Atlassian
    'salesforce.com',  # Salesforce
    'adobe.com',  # Adobe
]

# Business communication patterns that should NOT be flagged as phishing
LEGITIMATE_BUSINESS_PATTERNS = [
    # Calendar/Meeting patterns
    'google calendar', 'calendar invitation', 'meeting invitation', 'event invitation',
    'has invited you', 'join by phone', 'meeting id', 'dial-in number',
    'weekly from', 'daily from', 'monthly from', 'recurring meeting',
    'organizer', 'attendees', 'guests', 'location changed', 'event updated',
    
    # Internal business communication
    'team meeting', 'standup', 'retrospective', 'sprint planning',
    'quarterly review', 'performance review', 'one-on-one',
    'all hands', 'company meeting', 'department meeting',
    
    # Legitimate business actions
    'please review', 'for your approval', 'needs your attention',
    'quarterly report', 'monthly report', 'status update',
    'project update', 'milestone reached', 'deadline reminder'
]

def _check_legitimate_business_email(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if email is a legitimate business communication that should not be flagged.
    Returns dict with is_business, reason, confidence_boost, and evidence.
    
    NOTE: This function should be VERY restrictive to avoid bypassing the hybrid system.
    Only catch emails that are DEFINITELY legitimate business communications.
    """
    subject = payload.get("subject", "").lower()
    body = payload.get("raw_text", "").lower()
    from_email = payload.get("from_email", "").lower()
    combined_text = f"{subject} {body}"
    
    # Extract domain from sender
    sender_domain = ""
    if "@" in from_email:
        sender_domain = from_email.split("@")[1]
    
    # Check 1: Google Calendar invitations (VERY SPECIFIC)
    if any(pattern in combined_text for pattern in [
        "google calendar", "calendar invitation", "has invited you to", 
        "join by phone", "meeting id", "dial-in number"
    ]):
        # Additional validation for Google Calendar - MUST be from Google
        if ("google.com" in sender_domain and 
            ("calendar" in combined_text or "organizer" in combined_text)):
            return {
                "is_business": True,
                "reason": "Google Calendar meeting invitation",
                "confidence_boost": 25,
                "evidence": [{"type": "calendar_invitation", "details": "google_service"}]
            }
    
    # Check 2: Trusted domain senders (ONLY for very specific cases)
    # Only catch emails from trusted domains if they have VERY specific business patterns
    if sender_domain in ['github.com', 'gitlab.com', 'bitbucket.org']:
        # Only for code repository notifications
        if any(pattern in combined_text for pattern in [
            'pull request', 'merge request', 'commit', 'repository', 'issue opened', 'issue closed'
        ]):
            return {
                "is_business": True,
                "reason": f"Code repository notification from {sender_domain}",
                "confidence_boost": 20,
                "evidence": [{"type": "trusted_domain", "domain": sender_domain}]
            }
    
    # Check 3: Internal business communication patterns (MUCH MORE RESTRICTIVE)
    # Only catch emails with MULTIPLE very specific business patterns
    specific_business_patterns = [
        'google calendar', 'calendar invitation', 'meeting invitation',
        'pull request', 'merge request', 'code review',
        'sprint planning', 'retrospective', 'standup notes'
    ]
    
    business_pattern_count = sum(1 for pattern in specific_business_patterns 
                                if pattern in combined_text)
    
    if business_pattern_count >= 2:  # Need at least 2 VERY specific patterns
        return {
            "is_business": True,
            "reason": f"Multiple specific business communication patterns detected ({business_pattern_count})",
            "confidence_boost": 15,
            "evidence": [{"type": "business_patterns", "count": business_pattern_count}]
        }
    
    # REMOVED: Meeting indicators check (too broad)
    # REMOVED: Corporate email patterns check (too broad)
    
    return {"is_business": False}

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

def _is_legitimate_link_context(anchor_text: str, domain: str, from_email: str) -> bool:
    """Check if a link is in a legitimate context to reduce false positives"""
    if not anchor_text or not domain:
        return False
        
    anchor_lower = anchor_text.lower().strip()
    domain_lower = domain.lower()
    from_domain = from_email.split('@')[1].lower() if '@' in from_email else ''
    
    # Check if domain is trusted
    if any(trusted in domain_lower for trusted in TRUSTED_DOMAINS):
        # Additional check: sender domain should match or be related
        if from_domain:
            # Same domain or subdomain
            if from_domain == domain_lower or domain_lower.endswith('.' + from_domain) or from_domain.endswith('.' + domain_lower):
                return True
            
            # Known legitimate cross-domain patterns
            legitimate_cross_domain = [
                ('github.com' in from_domain and 'github.com' in domain_lower),
                ('google.com' in from_domain and 'google.com' in domain_lower),
                ('microsoft.com' in from_domain and any(ms in domain_lower for ms in ['microsoft.com', 'outlook.com', 'live.com'])),
            ]
            
            if any(legitimate_cross_domain):
                return True
    
    # Legitimate anchor patterns
    legitimate_patterns = [
        # Technical/development contexts
        ('view', ['github.com', 'gitlab.com', 'bitbucket.org']),
        ('review', ['github.com', 'gitlab.com', 'bitbucket.org']),
        ('merge', ['github.com', 'gitlab.com', 'bitbucket.org']),
        ('commit', ['github.com', 'gitlab.com', 'bitbucket.org']),
        ('pull request', ['github.com', 'gitlab.com', 'bitbucket.org']),
        ('pr', ['github.com', 'gitlab.com', 'bitbucket.org']),
        
        # Business contexts
        ('unsubscribe', ['*']),  # Unsubscribe is always legitimate
        ('manage preferences', ['*']),
        ('contact support', ['*']),
        ('help center', ['*']),
        ('customer service', ['*']),
        
        # Specific legitimate patterns
        ('view order', ['amazon.com']),
        ('track package', ['amazon.com', 'ups.com', 'fedex.com']),
        ('view statement', ['chase.com', 'wellsfargo.com', 'bankofamerica.com']),
        ('pay bill', ['chase.com', 'wellsfargo.com', 'bankofamerica.com']),
    ]
    
    # Check for legitimate anchor patterns
    for pattern, allowed_domains in legitimate_patterns:
        if pattern in anchor_lower:
            if '*' in allowed_domains or any(allowed in domain_lower for allowed in allowed_domains):
                return True
    
    return False

def _is_technical_urgency_context(text: str, subject: str) -> bool:
    """Check if urgency words are in a legitimate technical context"""
    text_lower = (text + ' ' + subject).lower()
    
    # Technical contexts where urgency words are legitimate
    technical_contexts = [
        'pull request', 'pr #', 'merge request', 'mr #',
        'commit', 'repository', 'repo',
        'implementation', 'feature', 'bug fix', 'hotfix',
        'deployment', 'release', 'version',
        'code review', 'review requested',
        'ci/cd', 'build', 'pipeline',
        'feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:',  # Conventional commits
    ]
    
    # If we find technical context, urgency words are likely legitimate
    return any(context in text_lower for context in technical_contexts)

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
    
    # 🚀 IMPROVED: Context-aware urgency detection
    urgent_count = sum(1 for w in URGENT_WORDS if w in text_l + " " + subject)
    
    # Check if urgency is in a legitimate technical context
    is_technical_context = _is_technical_urgency_context(text, subject)
    
    if urgent_count >= 3 and not is_technical_context:
        reasons.append(f"Multiple urgency tactics detected ({urgent_count} matches).")
        evidence.append({"type": "high_urgency", "count": urgent_count})
        score += 45  # High urgency = very suspicious
    elif urgent_count >= 1 and not is_technical_context:
        reasons.append(f"Urgency language detected ({urgent_count} matches).")
        evidence.append({"type": "urgency", "count": urgent_count})
        score += min(30, 10 * urgent_count)  # Increased scoring
    elif urgent_count >= 1 and is_technical_context:
        # Technical context - much lower penalty
        reasons.append(f"Technical urgency context detected ({urgent_count} matches).")
        evidence.append({"type": "technical_urgency", "count": urgent_count})
        score += max(5, urgent_count * 2)  # Much lower penalty for technical context
    
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
        
        # 🚀 IMPROVED: Context-aware anchor text vs domain matching
        if anchor and "http" not in anchor and dom:
            anchor_low = anchor.lower()
            
            # Check if this is a legitimate link context
            is_legitimate = _is_legitimate_link_context(anchor, dom, from_email)
            
            if not is_legitimate:
                # Check for basic domain matching
                domain_root = dom.split(".")[0]
                if domain_root not in anchor_low and anchor_low and len(anchor_low) > 1:
                    # 🚀 IMPROVED: Only flag if domain is suspicious or context is suspicious
                    suspicious_mismatch = any(suspicious in dom for suspicious in ['.tk', '.ml', '.ga', '.cf', 'verify', 'secure', 'update'])
                    
                    # Don't flag trusted domains with generic anchor text
                    if any(trusted in dom for trusted in TRUSTED_DOMAINS):
                        # Only flag trusted domains if anchor text is very suspicious
                        very_suspicious_anchor = any(sus in anchor_low for sus in ['click here', 'verify now', 'urgent', 'suspended'])
                        if very_suspicious_anchor:
                            mismatch_score = 20  # Lower score for trusted domains
                            reasons.append(f"Suspicious anchor text '{anchor}' on trusted domain '{dom}'.")
                            evidence.append({"type": "suspicious_anchor_trusted_domain", "anchor": anchor, "uri": uri})
                            score += mismatch_score
                    else:
                        # Non-trusted domain with mismatched anchor
                        mismatch_score = 40 if suspicious_mismatch else 25
                        reasons.append(f"Anchor text '{anchor}' does not match link domain '{dom}'.")
                        evidence.append({"type": "link_mismatch", "anchor": anchor, "uri": uri, "suspicious": suspicious_mismatch})
                        score += mismatch_score
        
        # 🚀 IMPROVED: Context-aware URL entropy detection
        ent = _url_entropy(uri)
        if ent > 3.5:
            # Don't penalize high entropy for trusted domains (they often have complex URLs)
            if any(trusted in dom for trusted in TRUSTED_DOMAINS):
                # Only flag if entropy is extremely high (> 4.5) for trusted domains
                if ent > 4.5:
                    reasons.append(f"Very high URL path entropy for trusted domain {uri}.")
                    evidence.append({"type": "high_entropy_trusted_uri", "uri": uri, "entropy": ent})
                    score += 5  # Much lower penalty for trusted domains
            else:
                reasons.append(f"High URL path entropy for {uri}.")
                evidence.append({"type": "high_entropy_uri", "uri": uri, "entropy": ent})
                score += 15  # Full penalty for untrusted domains
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
            
        # 🚀 FIXED: Contextual brand impersonation detection - NO false brand mentions
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
        
        # Only check for brands that are ACTUALLY mentioned in the email content
        email_content = subject + " " + raw_text
        actually_mentioned_brands = []
        
        for brand, legitimate_domains in brand_domains.items():
            # More precise brand detection - must be a clear mention
            brand_patterns = [
                f" {brand} ",  # Surrounded by spaces
                f"{brand}.",   # Followed by period
                f"{brand},",   # Followed by comma
                f"@{brand}",   # In email context
                f"{brand}.com", # Domain context
                f"from {brand}", # "from PayPal"
                f"{brand} account", # "PayPal account"
            ]
            
            if any(pattern in email_content.lower() for pattern in brand_patterns):
                actually_mentioned_brands.append((brand, legitimate_domains))
        
        # Only flag impersonation for brands that are ACTUALLY mentioned
        for brand, legitimate_domains in actually_mentioned_brands:
            # Check if email domain matches any legitimate domain for this brand
            is_legitimate = any(domain in from_email for domain in legitimate_domains)
            
            if not is_legitimate:
                # Only flag if there are clear suspicious indicators
                suspicious_context = [
                    any(urgent in raw_text for urgent in ['urgent', 'immediately', 'suspended', 'verify', 'click here']),
                    any(credential in raw_text for credential in ['password', 'login', 'verify your account', 'confirm your identity']),
                    any(suspicious in from_email for suspicious in ['noreply', 'security', 'alert', 'verify', 'update']) if from_email else False
                ]
                
                # Only flag as impersonation if there are suspicious context clues
                if any(suspicious_context):
                    if any(sensitive in raw_text for sensitive in ['password', 'login', 'account', 'payment', 'credit card', 'verify', 'confirm', 'update']):
                        llm_boost += 50  # Brand impersonation + sensitive request = very suspicious
                        llm_reasons.append(f"LLM: {brand.title()} impersonation with sensitive data request detected")
                        confidence += 0.15
                    else:
                        llm_boost += 30
                        llm_reasons.append(f"LLM: Potential {brand.title()} impersonation detected")
                        confidence += 0.1
                    break  # Only flag the first detected brand to avoid multiple flags
                    
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
            # 🚀 FIX: Handle Gemini responses wrapped in markdown code blocks
            json_text = text.strip()
            
            # Check if response is wrapped in markdown code blocks
            if json_text.startswith('```json') and json_text.endswith('```'):
                # Extract JSON from markdown
                json_start = json_text.find('```json') + 7
                json_end = json_text.rfind('```')
                json_text = json_text[json_start:json_end].strip()
            elif json_text.startswith('```') and json_text.endswith('```'):
                # Handle generic code blocks
                json_start = json_text.find('```') + 3
                json_end = json_text.rfind('```')
                json_text = json_text[json_start:json_end].strip()
            
            parsed = json.loads(json_text)
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
    # 🚀 DISABLED: Business pattern recognition (too aggressive for presentation)
    # Skip business email check - go straight to hybrid system for better accuracy
    
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
    
    # 🚀 FIXED: Always use LLM when available for better explanations
    # The hybrid system should use LLM for contextual explanations, not just uncertain cases
    use_llm = LLM_PROVIDER in ["gemini", "mock"]
    
    # Only skip LLM for very simple, clearly safe emails (score < 10)
    if heur["score"] < 10 and email_complexity < 0.3:
        use_llm = False
        combined_reasons = [f"Simple safe email (score: {heur['score']}, complexity: {email_complexity:.2f})"]
    
    # Always use LLM for suspicious/phishing emails to get contextual explanations
    if heur["score"] >= 25:  # Suspicious or higher
        use_llm = True
        combined_reasons = [f"Suspicious email requires AI analysis (score: {heur['score']})"]
    
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


    # 🚀 GEMINI-POWERED: Full AI explanation system
    ai_explanation = _generate_human_explanation(label, final_score, reasons, evidence, payload)
    
    return {
        "label": label,
        "score": final_score,
        "reasons": reasons,
        "evidence": evidence,
        "model_meta": model_meta,
        "ai_explanation": ai_explanation,  # 🚀 NEW: AI-generated explanation
        "timestamp": datetime.utcnow().isoformat()
    }

def _generate_gemini_reasoning(label: str, score: int, reasons: List[str], subject: str, from_email: str, raw_text: str, language: str = "en") -> str:
    """Generate AI reasoning using Gemini API for human-friendly explanations in specified language."""
    
    # Create language-specific prompts
    if language == "ja":
        explanation_prompt = f"""あなたは、技術的でないユーザーにメール分析結果を説明するサイバーセキュリティの専門家です。

メール分析結果:
- 分類: {label}
- 信頼度スコア: {score}%
- 件名: "{subject}"
- 送信者: {from_email}
- 検出された問題: {', '.join(reasons[:3])}

あなたの任務: このメールが{label}として分類された理由を2-3文で説明してください。会話的で、明確で、役に立つように説明してください。

ガイドライン:
- 簡単な言葉を使い、専門用語を避ける
- 発見された具体的な脅威や安全性の指標を説明する
- ユーザーがなぜ心配すべきか（または心配する必要がないか）に焦点を当てる
- 友人に話しかけるような親しみやすいセキュリティ専門家のように振る舞う
- 丁寧で専門的な日本語を使用する

例:
- フィッシングの場合: "このメールは、PayPalを装ってあなたを騙そうとしていますが、送信者のアドレスはPayPalの本物のドメインと一致しません。また、メッセージは偽の緊急性を作り出して、考える時間を与えずに悪意のあるリンクをクリックするよう圧力をかけています。"
- 安全な場合: "このメールは、Chaseの公式ドメインから送信され、専門的な言語を使用し、疑わしいリンクをクリックするよう圧力をかける代わりに正当な連絡方法を提供しているため、正当なものと思われます。"

あなたの説明:"""
    else:
        explanation_prompt = f"""You are a cybersecurity expert explaining email analysis results to a non-technical user. 

Email Analysis Results:
- Classification: {label}
- Confidence Score: {score}%
- Subject: "{subject}"
- From: {from_email}
- Detected Issues: {', '.join(reasons[:3])}

Your task: Explain in 2-3 sentences WHY this email was classified as {label}. Be conversational, clear, and helpful.

Guidelines:
- Use simple language, avoid technical jargon
- Explain the specific threats or safety indicators found
- Focus on WHY the user should be concerned (or not concerned)
- Be like a friendly security expert talking to a friend

Examples:
- For PHISHING: "This email is trying to trick you by pretending to be from PayPal, but the sender's address doesn't match PayPal's real domain. The message also creates fake urgency to pressure you into clicking malicious links before you have time to think."
- For SAFE: "This email appears legitimate because it comes from Chase's official domain, uses professional language, and provides legitimate contact methods instead of pressuring you to click suspicious links."

Your explanation:"""

    try:
        # Only call Gemini if we have an API key, otherwise use fallback
        if LLM_PROVIDER == "gemini" and os.getenv("GEMINI_API_KEY"):
            res = call_gemini_raw(
                explanation_prompt, 
                api_key=os.getenv("GEMINI_API_KEY"), 
                model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), 
                max_output_tokens=200, 
                temperature=0.3  # Slightly more creative for explanations
            )
            gemini_explanation = res.get("text", "").strip()
            
            # Validate the response is reasonable
            if gemini_explanation and len(gemini_explanation) > 20 and len(gemini_explanation) < 500:
                return gemini_explanation
        
        # Fallback to intelligent hardcoded explanations if Gemini fails
        return _generate_fallback_reasoning(label, score, reasons, subject, from_email, language)
        
    except Exception as ex:
        logger.warning(f"Gemini explanation failed: {ex}, using fallback")
        return _generate_fallback_reasoning(label, score, reasons, subject, from_email, language)

def _generate_fallback_reasoning(label: str, score: int, reasons: List[str], subject: str, from_email: str, language: str = "en") -> str:
    """Fallback reasoning when Gemini API is unavailable - CONTEXTUAL and NO hardcoded brands."""
    
    # Extract actual brands mentioned in reasons (not hardcoded)
    mentioned_brands = []
    reasons_text = " ".join(reasons).lower()
    
    # Only extract brands that are actually mentioned in the analysis reasons
    brand_keywords = ['paypal', 'amazon', 'microsoft', 'apple', 'google', 'netflix', 'chase', 'wells', 'bank']
    for brand in brand_keywords:
        if brand in reasons_text:
            mentioned_brands.append(brand.title())
    
    if language == "ja":
        # Japanese fallback reasoning - CONTEXTUAL
        if label == "PHISHING":
            if mentioned_brands:
                brands_text = "、".join(mentioned_brands)
                return f"このメールは{brands_text}を装って詐欺を行おうとしています。送信者のアドレス（{from_email}）は正当なドメインと一致せず、緊急性を装って個人情報を盗もうとする典型的なフィッシング攻撃です。"
            elif "urgency" in reasons_text and "credential" in reasons_text:
                return f"このメールは偽の緊急性を作り出し、パスワードや個人情報を要求する詐欺メールです。正当な企業がこのような方法で機密情報を求めることはありません。"
            elif "link" in reasons_text or "mismatch" in reasons_text:
                return f"このメールには欺瞞的なリンクが含まれており、表示されているテキストと実際のリンク先が異なります。これはフィッシング攻撃の典型的な手法です。"
            else:
                return f"複数の危険信号により、このメールはフィッシング攻撃と判定されました。疑わしい送信者、不審なリンク、心理的操作の手法が検出されています。"
        elif label == "SUSPICIOUS":
            return f"このメールには注意が必要な要素が含まれています。送信者の確認を行い、リンクをクリックする前に公式チャネルを通じて検証することをお勧めします。"
        else:  # SAFE
            return f"このメールは正当なビジネス通信の特徴を示しています。ただし、予期しないリクエストについては常に独立して確認することをお勧めします。"
    
    # English fallback reasoning - CONTEXTUAL (no hardcoded brands)
    if label == "PHISHING":
        if mentioned_brands:
            brands_text = " and ".join(mentioned_brands) if len(mentioned_brands) > 1 else mentioned_brands[0]
            return f"This email appears to be impersonating {brands_text}. The sender's address ({from_email}) doesn't match the legitimate domain, and the message uses typical phishing tactics to steal your personal information."
        elif "urgency" in reasons_text and "credential" in reasons_text:
            return f"This email creates false urgency to pressure you into revealing sensitive information like passwords or account details. Legitimate companies don't request credentials via email in this manner."
        elif "link" in reasons_text or "mismatch" in reasons_text:
            return f"This email contains deceptive links where the displayed text doesn't match the actual destination. This is a common phishing technique used to trick users into visiting malicious websites."
        else:
            return f"Multiple security indicators suggest this is a phishing attempt. The combination of suspicious sender patterns, deceptive content, and social engineering tactics are designed to compromise your security."
    elif label == "SUSPICIOUS":
        return f"This email contains some concerning elements that warrant caution. We recommend verifying the sender's identity through official channels before taking any action or clicking links."
    else:  # SAFE
        return f"This email appears to be legitimate business communication. However, always verify unexpected requests independently through official channels."

def _generate_human_explanation(label: str, score: int, reasons: List[str], evidence: List[Dict], payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate human-friendly AI explanation of the analysis."""
    
    # Extract key information
    subject = payload.get("subject", "")
    from_email = payload.get("from_email", "")
    raw_text = payload.get("raw_text", "")
    language = payload.get("language", "en")
    
    # Generate threat summary based on label and language
    if language == "ja":
        # Japanese threat summaries
        if label == "PHISHING":
            if score >= 80:
                summary = f"🚨 このメールはフィッシング攻撃の可能性が非常に高いです。AIが、サイバー犯罪者が個人情報や認証情報を盗むために一般的に使用する複数の危険信号を検出しました。"
            else:
                summary = f"⚠️ このメールはフィッシングの試みの強い兆候を示しています。これが正当なメッセージではないことを示唆する疑わしいパターンがいくつか検出されました。"
        elif label == "SUSPICIOUS":
            summary = f"⚠️ このメールには注意が必要な懸念される要素が含まれています。明確に悪意があるわけではありませんが、フィッシングの試みでよく見られるパターンを示しています。"
        else:  # SAFE
            summary = f"✅ このメールは正当なものと思われます。分析では重大な危険信号は見つからず、本物のビジネスコミュニケーションの特徴を示しています。"
    else:
        # English threat summaries (original)
        if label == "PHISHING":
            if score >= 80:
                summary = f"🚨 This email is highly likely a phishing attack. Our AI detected multiple red flags that are commonly used by cybercriminals to steal your personal information or credentials."
            else:
                summary = f"⚠️ This email shows strong signs of being a phishing attempt. Several suspicious patterns were detected that suggest this is not a legitimate message."
        elif label == "SUSPICIOUS":
            summary = f"⚠️ This email contains some concerning elements that warrant caution. While not definitively malicious, it exhibits patterns often seen in phishing attempts."
        else:  # SAFE
            summary = f"✅ This email appears to be legitimate. Our analysis found no significant red flags, and it shows characteristics of authentic business communication."
    
    # Generate Gemini-powered AI reasoning
    ai_reasoning = _generate_gemini_reasoning(label, score, reasons, subject, from_email, raw_text, language)
    
    # Generate human-readable suspicious indicators
    suspicious_indicators = []
    for reason in reasons[:5]:  # Top 5 reasons
        reason_lower = reason.lower()
        
        # Translate technical reasons to human language
        if "urgency" in reason_lower or "urgent" in reason_lower:
            suspicious_indicators.append("Creates artificial urgency to pressure you into acting quickly without thinking")
        elif "credential" in reason_lower or "password" in reason_lower:
            suspicious_indicators.append("Attempts to trick you into revealing sensitive login credentials or passwords")
        elif "brand impersonation" in reason_lower or "impersonation" in reason_lower:
            brand = reason.split("impersonation")[0].strip() if "impersonation" in reason else "a trusted company"
            suspicious_indicators.append(f"Pretends to be from {brand} but the sender's email address doesn't match their official domain")
        elif "character substitution" in reason_lower or "typosquatting" in reason_lower:
            suspicious_indicators.append("Uses a fake domain that looks similar to a legitimate one (like replacing 'l' with 'I' or 'o' with '0')")
        elif "link mismatch" in reason_lower or "anchor" in reason_lower:
            suspicious_indicators.append("The link text says one thing, but clicking it would take you to a completely different website")
        elif "suspicious domain" in reason_lower or "free domain" in reason_lower:
            suspicious_indicators.append("Uses a suspicious or free domain often associated with scam emails")
        elif "shortened" in reason_lower or "redirect" in reason_lower:
            suspicious_indicators.append("Contains shortened URLs that hide the real destination website")
        elif "grammar" in reason_lower or "spelling" in reason_lower:
            suspicious_indicators.append("Contains grammar or spelling errors typical of mass phishing campaigns")
        elif "sender" in reason_lower and "generic" in reason_lower:
            suspicious_indicators.append("Sent from a generic or suspicious email address that doesn't match the claimed sender")
        else:
            # Keep original if we can't translate it
            suspicious_indicators.append(reason)
    
    # Generate technical indicators in human-friendly format (language-specific)
    technical_indicators = []
    
    if language == "ja":
        # Japanese technical indicators
        technical_indicators.append(f"脅威の信頼度: {score}% ({_get_confidence_description(score, language)})")
        
        # Add evidence-based technical details in Japanese
        for ev in evidence[:3]:
            ev_type = ev.get("type", "")
            if ev_type == "urgency" or ev_type == "high_urgency":
                count = ev.get("count", 1)
                technical_indicators.append(f"{count}つの緊急性操作戦術を検出しました")
            elif ev_type == "brand_impersonation":
                brand = ev.get("brand", "unknown")
                technical_indicators.append(f"ブランドなりすましを検出: {brand.title()}")
            elif ev_type == "character_substitution":
                domain = ev.get("domain", "")
                target = ev.get("target", "")
                technical_indicators.append(f"偽ドメインを検出: {domain} ({target}を模倣)")
            elif ev_type == "link_mismatch":
                technical_indicators.append(f"欺瞞的リンク: '{ev.get('anchor', '')}'と表示されているが、異なるサイトにリンク")
    else:
        # English technical indicators (original)
        technical_indicators.append(f"Threat confidence: {score}% ({_get_confidence_description(score, language)})")
        
        # Add evidence-based technical details
        for ev in evidence[:3]:
            ev_type = ev.get("type", "")
            if ev_type == "urgency" or ev_type == "high_urgency":
                count = ev.get("count", 1)
                technical_indicators.append(f"Detected {count} urgency manipulation tactic{'s' if count > 1 else ''}")
            elif ev_type == "brand_impersonation":
                brand = ev.get("brand", "unknown")
                technical_indicators.append(f"Brand impersonation detected: {brand.title()}")
            elif ev_type == "character_substitution":
                domain = ev.get("domain", "")
                target = ev.get("target", "")
                technical_indicators.append(f"Fake domain detected: {domain} (mimicking {target})")
            elif ev_type == "link_mismatch":
                technical_indicators.append(f"Deceptive link: displays '{ev.get('anchor', '')}' but links to different site")
    
    # Final assessment (language-specific)
    if language == "ja":
        # Japanese final assessments
        if label == "PHISHING":
            final_assessment = f"高リスク - リンクをクリックしたり、情報を提供したりしないでください。これはフィッシング攻撃の可能性が非常に高いです。"
        elif label == "SUSPICIOUS":
            final_assessment = f"中リスク - 注意してください。続行する前に公式チャネルを通じて送信者を確認してください。"
        else:
            final_assessment = f"低リスク - メールは正当に見えますが、予期しないリクエストは常に独自に確認してください。"
    else:
        # English final assessments (original)
        if label == "PHISHING":
            final_assessment = f"HIGH RISK - Do not click any links or provide any information. This is very likely a phishing attack."
        elif label == "SUSPICIOUS":
            final_assessment = f"MEDIUM RISK - Exercise caution. Verify the sender through official channels before proceeding."
        else:
            final_assessment = f"LOW RISK - Email appears legitimate, but always verify unexpected requests independently."
    
    # Recommended action (language-specific)
    if language == "ja":
        # Japanese recommended actions
        if label == "PHISHING":
            recommended_action = "🛡️ このメールを直ちに削除してください。リンクをクリックしたり、添付ファイルをダウンロードしたりしないでください。アカウントが心配な場合は、（メールのリンクからではなく）企業の公式ウェブサイトに直接アクセスするか、公式カスタマーサービスに電話してください。"
        elif label == "SUSPICIOUS":
            recommended_action = "⚠️ まだリンクをクリックしないでください。このメッセージが正当であることを確認するために、（メールからではなく、ウェブサイトの電話番号から）公式チャネルを通じて送信者に連絡してから行動してください。"
        else:
            recommended_action = "✅ このメールは安全に見えますが、予期しないリクエストが含まれていたり、機密情報を求められたりする場合は、公式チャネルを通じて送信者に連絡して独自に確認してください。"
    else:
        # English recommended actions (original)
        if label == "PHISHING":
            recommended_action = "🛡️ Delete this email immediately. Do not click any links or download attachments. If you're concerned about your account, visit the company's official website directly (not through email links) or call their official customer service number."
        elif label == "SUSPICIOUS":
            recommended_action = "⚠️ Do not click any links yet. Contact the sender through official channels (phone number from their website, not from the email) to verify this message is legitimate before taking any action."
        else:
            recommended_action = "✅ This email appears safe, but if it contains unexpected requests or asks for sensitive information, verify independently by contacting the sender through official channels."
    
    # Create full explanation by combining all sections
    full_explanation = f"{summary}\n\n{ai_reasoning}\n\n{final_assessment}\n\n{recommended_action}"
    
    return {
        "summary": summary,
        "ai_reasoning": ai_reasoning,
        "suspicious_indicators": suspicious_indicators,
        "technical_indicators": technical_indicators,
        "final_assessment": final_assessment,
        "recommended_action": recommended_action,
        "full_explanation": full_explanation
    }

def _get_confidence_description(score: int, language: str = "en") -> str:
    """Get human-readable confidence description."""
    if language == "ja":
        # Japanese confidence descriptions
        if score >= 90:
            return "非常に高い信頼度"
        elif score >= 70:
            return "高い信頼度"
        elif score >= 50:
            return "中程度の信頼度"
        elif score >= 30:
            return "低い信頼度"
        else:
            return "非常に低い信頼度"
    else:
        # English confidence descriptions (original)
        if score >= 90:
            return "Very High Confidence"
        elif score >= 70:
            return "High Confidence"
        elif score >= 50:
            return "Medium Confidence"
        elif score >= 30:
            return "Low Confidence"
        else:
            return "Very Low Confidence"

def retranslate_explanation(original_result: Dict[str, Any], target_language: str) -> Dict[str, Any]:
    """
    Re-translate AI explanation and other dynamic content to a different language without re-analyzing the email.
    
    Args:
        original_result: The original analysis result
        target_language: Target language code (en, ja)
    
    Returns:
        Updated result with translated AI explanation and dynamic content
    """
    
    # Extract original analysis data
    label = original_result.get("label", "SAFE")
    score = original_result.get("score", 0)
    reasons = original_result.get("reasons", [])
    evidence = original_result.get("evidence", [])
    
    # Create a minimal payload for explanation generation
    payload = {
        "language": target_language,
        "subject": "Re-translation request",
        "raw_text": "Re-translation of existing analysis",
        "from_email": ""
    }
    
    # Generate new AI explanation in target language
    ai_explanation = _generate_human_explanation(label, score, reasons, evidence, payload)
    
    # Translate suggested actions based on language
    if target_language == "ja":
        suggested_action = "リンクをクリックしたり、情報を提供したりしないでください。公式チャネルを通じて送信者を確認してください。"
        suggested_reply = "公式チャネルを通じて確認いたします。認証情報は共有しないでください。"
    else:
        suggested_action = "Do not click links; verify the sender via official channels."
        suggested_reply = "I will confirm via official channels; please do not share credentials."
    
    # Return updated result with new explanation and translated content
    updated_result = original_result.copy()
    updated_result["ai_explanation"] = ai_explanation
    updated_result["suggested_action"] = suggested_action
    updated_result["suggested_reply"] = suggested_reply
    
    return updated_result