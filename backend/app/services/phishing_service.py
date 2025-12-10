# app/services/phishing_service.py
import json
import uuid
from typing import Dict, List, Any
from app.schemas.phishing import AnalyzeRequest, AnalyzeResponse
from app.models.email_scan import EmailScan
from app.db.session import SessionLocal

class PhishingAnalysisService:
    """Service for analyzing emails for phishing indicators."""
    
    def __init__(self):
        self.phishing_keywords = [
            "urgent", "immediate", "verify", "suspend", "click here", 
            "act now", "limited time", "confirm", "update", "secure"
        ]
        self.suspicious_domains = [
            "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly"
        ]
    
    def analyze_email(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """Analyze email content for phishing indicators."""
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Calculate risk score
        score = self._calculate_risk_score(request)
        
        # Determine label based on score
        label = self._get_risk_label(score)
        
        # Generate reasons/explanations
        reasons = self._generate_reasons(request, score)
        
        # Save to database
        self._save_scan_result(request, score, label, reasons)
        
        return AnalyzeResponse(
            request_id=request_id,
            label=label,
            score=score,
            reasons=reasons,
            evidence=[],
            suggested_action=self._get_suggested_action(score),
            model_meta={"version": "1.0", "model": "rule-based"}
        )
    
    def _calculate_risk_score(self, request: AnalyzeRequest) -> int:
        """Calculate risk score based on various indicators."""
        score = 0
        
        # Check subject line
        if request.subject:
            score += self._analyze_subject(request.subject)
        
        # Check sender
        if request.from_email:
            score += self._analyze_sender(request.from_email)
        
        # Check content
        if request.raw_text:
            score += self._analyze_content(request.raw_text)
        
        # Check links
        if request.visible_links or request.hidden_links:
            score += self._analyze_links(request.visible_links or [], request.hidden_links or [])
        
        # Cap at 100
        return min(score, 100)
    
    def _analyze_subject(self, subject: str) -> int:
        """Analyze subject line for phishing indicators."""
        score = 0
        subject_lower = subject.lower()
        
        # Check for urgent language
        urgent_words = ["urgent", "immediate", "asap", "expires", "deadline"]
        for word in urgent_words:
            if word in subject_lower:
                score += 15
        
        # Check for verification requests
        verify_words = ["verify", "confirm", "update", "validate"]
        for word in verify_words:
            if word in subject_lower:
                score += 10
        
        # Check for excessive punctuation
        if subject.count("!") > 2 or subject.count("?") > 1:
            score += 5
        
        return min(score, 30)
    
    def _analyze_sender(self, sender_email: str) -> int:
        """Analyze sender email for suspicious patterns."""
        score = 0
        
        # Check for suspicious domains
        domain = sender_email.split("@")[-1].lower()
        
        # Common phishing domains
        suspicious_domains = [
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com"
        ]
        
        # If claiming to be from a company but using free email
        if any(company in sender_email.lower() for company in ["bank", "paypal", "amazon", "microsoft"]):
            if any(free_domain in domain for free_domain in suspicious_domains):
                score += 25
        
        # Check for domain spoofing attempts
        spoofing_indicators = ["payp4l", "g00gle", "micr0soft", "amaz0n"]
        for indicator in spoofing_indicators:
            if indicator in domain:
                score += 30
        
        return min(score, 35)
    
    def _analyze_content(self, content: str) -> int:
        """Analyze email content for phishing indicators."""
        score = 0
        content_lower = content.lower()
        
        # Check for phishing keywords
        keyword_count = 0
        for keyword in self.phishing_keywords:
            if keyword in content_lower:
                keyword_count += 1
        
        score += min(keyword_count * 3, 20)
        
        # Check for urgency tactics
        urgency_phrases = [
            "act now", "limited time", "expires soon", "immediate action",
            "account will be closed", "suspended", "verify immediately"
        ]
        
        for phrase in urgency_phrases:
            if phrase in content_lower:
                score += 8
        
        # Check for generic greetings
        if any(greeting in content_lower for greeting in ["dear customer", "dear user", "dear sir/madam"]):
            score += 5
        
        return min(score, 25)
    
    def _analyze_links(self, visible_links: List[Any], hidden_links: List[Any]) -> int:
        """Analyze links for suspicious patterns."""
        score = 0
        
        all_links = visible_links + hidden_links
        
        for link in all_links:
            # Handle both dict and LinkItem objects
            if hasattr(link, 'uri'):
                uri = link.uri or ""
            else:
                uri = link.get("uri", "") if isinstance(link, dict) else ""
            
            if not uri:
                continue
            
            # Check for URL shorteners
            for domain in self.suspicious_domains:
                if domain in uri:
                    score += 10
            
            # Check for suspicious TLDs
            suspicious_tlds = [".tk", ".ml", ".ga", ".cf"]
            for tld in suspicious_tlds:
                if tld in uri:
                    score += 15
            
            # Check for IP addresses instead of domains
            import re
            if re.match(r"https?://\d+\.\d+\.\d+\.\d+", uri):
                score += 20
        
        return min(score, 30)
    
    def _get_risk_label(self, score: int) -> str:
        """Convert risk score to label."""
        if score < 30:
            return "low"
        elif score < 70:
            return "medium"
        else:
            return "high"
    
    def _generate_reasons(self, request: AnalyzeRequest, score: int) -> List[str]:
        """Generate human-readable reasons for the risk assessment."""
        reasons = []
        
        if score < 30:
            reasons.append("Email appears legitimate with no major red flags detected")
            reasons.append("Sender domain and content seem trustworthy")
        elif score < 70:
            reasons.append("Some suspicious indicators detected")
            reasons.append("Exercise caution and verify sender authenticity")
            if request.subject and any(word in request.subject.lower() for word in ["urgent", "verify"]):
                reasons.append("Subject line contains urgency or verification language")
        else:
            reasons.append("Multiple phishing indicators detected")
            reasons.append("High risk of fraudulent activity")
            reasons.append("Do not click links or provide personal information")
            if request.visible_links or request.hidden_links:
                reasons.append("Contains suspicious links that may lead to malicious sites")
        
        return reasons
    
    def _get_suggested_action(self, score: int) -> str:
        """Get suggested action based on risk score."""
        if score < 30:
            return "Email appears safe to proceed"
        elif score < 70:
            return "Verify sender through alternative means before taking action"
        else:
            return "Delete email immediately and report as phishing"
    
    def _save_scan_result(self, request: AnalyzeRequest, score: int, label: str, reasons: List[str]):
        """Save scan result to database."""
        try:
            db = SessionLocal()
            
            scan = EmailScan(
                subject=request.subject,
                sender=request.from_email,
                label=label,
                score=score,
                reasons=json.dumps(reasons)
            )
            
            db.add(scan)
            db.commit()
            db.close()
        except Exception as e:
            print(f"Error saving scan result: {e}")

# Global service instance
phishing_service = PhishingAnalysisService()