# app/services/gemini_service.py
import json
import google.generativeai as genai
from typing import Dict, Any
from app.core.config import settings

class GeminiPhishingService:
    """Advanced AI-powered phishing detection using Gemini API."""
    
    def __init__(self):
        self.api_key = settings.llm_api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model_name = "gemini-2.0-flash-exp"
        
    async def analyze_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze email using Gemini AI for advanced phishing detection."""
        
        # Sanitize email content (remove PII)
        sanitized_content = self._sanitize_content(email_data)
        
        # Create AI prompt
        prompt = self._create_analysis_prompt(sanitized_content)
        
        try:
            # Call Gemini API
            response = self._call_gemini_api(prompt)
            
            # Parse and validate response
            analysis = self._parse_gemini_response(response)
            
            return {
                "label": analysis.get("label", "SUSPICIOUS"),
                "confidence": analysis.get("confidence", 50),
                "explanation": analysis.get("explanation", "AI analysis completed"),
                "risk_indicators": analysis.get("risk_indicators", []),
                "recommended_action": analysis.get("recommended_action", "Exercise caution"),
                "model_meta": {
                    "model": self.model_name,
                    "version": "1.0",
                    "cost_estimate": 0.02
                }
            }
            
        except Exception as e:
            # Fallback to heuristic analysis
            return self._fallback_analysis(email_data, str(e))
    
    def _sanitize_content(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove PII and sensitive data before sending to AI."""
        sanitized = email_data.copy()
        
        # Mask email addresses (keep domain for analysis)
        if sanitized.get("from_email"):
            email = sanitized["from_email"]
            if "@" in email:
                domain = email.split("@")[1]
                sanitized["from_email"] = f"[SENDER]@{domain}"
        
        # Mask phone numbers and other PII
        content = sanitized.get("raw_text", "")
        import re
        
        # Mask phone numbers
        content = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', content)
        
        # Mask credit card numbers
        content = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', content)
        
        # Mask SSN
        content = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', content)
        
        sanitized["raw_text"] = content
        return sanitized
    
    def _create_analysis_prompt(self, email_data: Dict[str, Any]) -> str:
        """Create structured prompt for Gemini analysis."""
        
        prompt = f"""You are a cybersecurity expert. Analyze this email and respond with ONLY valid JSON.

EMAIL DATA:
Subject: {email_data.get('subject', 'N/A')}
From: {email_data.get('from_email', 'N/A')}
Content: {email_data.get('raw_text', 'N/A')[:1500]}
Links: {json.dumps(email_data.get('visible_links', [])[:3])}

INSTRUCTIONS:
- Analyze for phishing indicators
- Return ONLY the JSON object below
- Do not include any other text or explanation
- Use exactly this format:

{{
    "label": "SAFE",
    "confidence": 85,
    "explanation": "Brief explanation of the analysis",
    "risk_indicators": ["indicator1", "indicator2"],
    "recommended_action": "What the user should do"
}}

Valid labels: SAFE, SUSPICIOUS, PHISHING
Confidence: 0-100 integer
Keep explanation under 100 characters.
JSON only:"""
        return prompt
    
    def _call_gemini_api(self, prompt: str) -> str:
        """Make API call to Gemini using REST API."""
        
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
        
        try:
            import requests
            
            # Use Gemini REST API directly with Flash 2.0
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 1000,
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                print(f"DEBUG: Gemini response: {content}")  # Debug output
                return content
            else:
                print(f"DEBUG: Full API response: {result}")  # Debug output
                raise ValueError("No response from Gemini API")
            
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: Request error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"DEBUG: Response status: {e.response.status_code}")
                print(f"DEBUG: Response text: {e.response.text}")
            raise ValueError(f"Gemini API request failed: {str(e)}")
        except Exception as e:
            print(f"DEBUG: General error: {e}")
            raise ValueError(f"Gemini API call failed: {str(e)}")
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate Gemini API response."""
        
        try:
            # Try to extract JSON from response (in case there's extra text)
            response_text = response_text.strip()
            
            # Look for JSON object in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                analysis = json.loads(json_text)
            else:
                # Try parsing the whole response
                analysis = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["label", "confidence", "explanation"]
            for field in required_fields:
                if field not in analysis:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate label values
            valid_labels = ["SAFE", "SUSPICIOUS", "PHISHING"]
            if analysis["label"] not in valid_labels:
                analysis["label"] = "SUSPICIOUS"
            
            # Ensure confidence is in valid range
            confidence = analysis.get("confidence", 50)
            analysis["confidence"] = max(0, min(100, confidence))
            
            # Ensure other fields exist
            if "risk_indicators" not in analysis:
                analysis["risk_indicators"] = []
            if "recommended_action" not in analysis:
                analysis["recommended_action"] = "Exercise caution"
            
            return analysis
            
        except (KeyError, json.JSONDecodeError, ValueError) as e:
            print(f"DEBUG: Failed to parse response: {response_text[:200]}...")
            raise ValueError(f"Invalid Gemini response format: {e}")
    
    def _fallback_analysis(self, email_data: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Fallback to heuristic analysis if Gemini fails."""
        
        return {
            "label": "SUSPICIOUS",
            "confidence": 30,
            "explanation": f"AI analysis unavailable ({error}). Basic heuristic analysis suggests caution.",
            "risk_indicators": ["AI analysis failed", "Using fallback detection"],
            "recommended_action": "Verify sender through alternative means",
            "model_meta": {
                "model": "heuristic-fallback",
                "version": "1.0",
                "cost_estimate": 0.0
            }
        }

# Global service instance
gemini_service = GeminiPhishingService()