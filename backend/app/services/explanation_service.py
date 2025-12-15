
import os
import logging
from typing import Dict, Any
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ExplanationService:
    """Service for generating human-readable explanations using Gemini API."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (or from environment)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            logger.warning("No Gemini API key provided. Explanations will be rule-based.")
            self.model = None
        else:
            try:
                genai.configure(api_key=self.api_key)
                # Use the old API - just set a flag that we have Gemini configured
                self.model = "configured"
                logger.info("Gemini client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.model = None
    
    
    async def generate_voice_explanation(
        self,
        analysis_result: Dict[str, Any],
        include_technical: bool = False
    ) -> str:
        """
        Generate human-readable explanation for voice analysis.
        
        Args:
            analysis_result: Result dictionary from voice analysis
            include_technical: Whether to include technical details
        
        Returns:
            Explanation string
        """

        if self.model is None:
            return self._generate_fallback_explanation(analysis_result)
        
        try:
            # Prepare prompt
            prompt = self._create_explanation_prompt(analysis_result, include_technical)
            
            # Call Gemini API using old API
            response = genai.generate_text(
                prompt=prompt,
                temperature=0.3,
                max_output_tokens=300,
            )
            
            explanation = response.result.strip() if response.result else ""
            logger.info("Generated explanation via Gemini API")
            
            return explanation
        
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._generate_fallback_explanation(analysis_result)
    
    
    def _create_explanation_prompt(
        self, 
        result: Dict[str, Any], 
        include_technical: bool
    ) -> str:
        """
        Create prompt for Gemini API.
        
        Args:
            result: Analysis result
            include_technical: Include technical details
        
        Returns:
            Prompt string
        """
        is_deepfake = result['is_deepfake']
        confidence = result['confidence']
        risk_level = result['risk_level']
        artifacts = result.get('artifacts', {})
        
        prompt = f"""You are an AI security expert explaining voice deepfake detection results to a non-technical user.

Analysis Results:
- Detection: {"AI-Generated Voice (Deepfake)" if is_deepfake else "Real Human Voice"}
- Confidence: {confidence:.1%}
- Risk Level: {risk_level.upper()}

Detected Artifacts:
- Spectral Flatness: {artifacts.get('spectral_flatness', 0):.3f}
- High-Frequency Energy: {artifacts.get('high_freq_energy', 0):.3f}
- Zero-Crossing Variance: {artifacts.get('zcr_variance', 0):.4f}
- Autocorrelation Peak: {artifacts.get('autocorr_peak', 0):.2f}

Task: Explain this analysis in 2-3 clear sentences for a general audience. Focus on:
1. What the system detected
2. Why it matters (security implications)
3. What the user should do next

"""
        
        if include_technical:
            prompt += "\nInclude brief technical details about the artifacts detected."
        else:
            prompt += "\nUse simple, non-technical language. Avoid jargon."
        
        prompt += "\n\nExplanation:"
        
        return prompt
    
    
    def _generate_fallback_explanation(self, result: Dict[str, Any]) -> str:
        """
        Generate rule-based explanation when Gemini is unavailable.
        
        Args:
            result: Analysis result
        
        Returns:
            Explanation string
        """
        is_deepfake = result['is_deepfake']
        confidence = result['confidence']
        risk_level = result['risk_level']
        
        if is_deepfake:
            if risk_level == "high":
                return (
                    f"This audio has been identified as AI-generated with {confidence:.0%} confidence. "
                    "The voice exhibits multiple characteristics typical of synthetic speech, including "
                    "unnatural frequency patterns and suspicious acoustic artifacts. "
                    "Recommendation: Do not trust this voice message. Verify the sender's identity through "
                    "an alternative communication channel before taking any action."
                )
            elif risk_level == "medium":
                return (
                    f"This audio shows signs of potential AI generation ({confidence:.0%} confidence). "
                    "Some acoustic characteristics suggest synthetic speech, but the detection is not conclusive. "
                    "Recommendation: Exercise caution. If the message requests sensitive information or actions, "
                    "verify the sender's identity before proceeding."
                )
            else:
                return (
                    f"This audio may be AI-generated, but confidence is low ({confidence:.0%}). "
                    "Some minor anomalies were detected, but they could also be caused by recording quality. "
                    "Recommendation: Use your judgment. If anything seems suspicious, verify independently."
                )
        else:
            if confidence > 0.7:
                return (
                    f"This audio appears to be genuine human speech ({confidence:.0%} confidence). "
                    "The voice characteristics, natural variations, and acoustic patterns are consistent "
                    "with authentic human vocalization. No significant deepfake indicators were detected."
                )
            else:
                return (
                    f"This audio is likely genuine, but analysis confidence is moderate ({confidence:.0%}). "
                    "The voice appears natural, though audio quality or recording conditions may affect certainty. "
                    "No clear deepfake indicators were found."
                )
    
    
    def generate_phishing_explanation(
        self,
        analysis_result: Dict[str, Any],
        email_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate human-readable explanation for phishing analysis.
        
        Args:
            analysis_result: Result from phishing detection
            email_content: Original email data
        
        Returns:
            Structured explanation dictionary
        """
        if self.model is None:
            return self._generate_fallback_phishing_explanation(analysis_result, email_content)
        
        try:
            # Create enhanced prompt for phishing explanation
            prompt = self._create_phishing_explanation_prompt(analysis_result, email_content)
            
            # Call Gemini API using old API
            response = genai.generate_text(
                prompt=prompt,
                temperature=0.2,  # Lower temperature for more consistent explanations
                max_output_tokens=800,
            )
            
            explanation_text = response.result.strip() if response.result else ""
            
            # Parse the structured response
            parsed_explanation = self._parse_phishing_explanation(explanation_text)
            
            logger.info("Generated phishing explanation via Gemini API")
            return parsed_explanation
        
        except Exception as e:
            logger.error(f"Gemini API error in phishing explanation: {e}")
            return self._generate_fallback_phishing_explanation(analysis_result, email_content)
    
    def _create_phishing_explanation_prompt(
        self, 
        result: Dict[str, Any], 
        email_content: Dict[str, Any]
    ) -> str:
        """Create enhanced prompt for phishing explanation."""
        
        # Extract key data
        label = result.get('label', 'UNKNOWN')
        score = result.get('score', 0)
        reasons = result.get('reasons', [])
        evidence = result.get('evidence', [])
        model_meta = result.get('model_meta', {})
        
        # Email content
        subject = email_content.get('subject', 'No subject')
        raw_text = email_content.get('raw_text', '')
        from_email = email_content.get('from_email', 'Unknown sender')
        visible_links = email_content.get('visible_links', [])
        
        prompt = f"""You are an AI cybersecurity analyst explaining phishing detection results to everyday users. 

EMAIL ANALYSIS RESULTS:
- Classification: {label}
- Risk Score: {score}/100
- Detected Patterns: {', '.join(reasons[:5])}
- Technical Evidence: {len(evidence)} indicators found
- Heuristic Score: {model_meta.get('heuristic_score', 'N/A')}
- LLM Confidence: {model_meta.get('llm_confidence', 'N/A')}
- Email Complexity: {model_meta.get('email_complexity', 'N/A')}

EMAIL CONTENT:
Subject: {subject}
From: {from_email}
Content Preview: {raw_text[:500]}...
Links Found: {len(visible_links)} links

TASK: Generate a human-friendly explanation with these EXACT sections:

## SUMMARY
Write 2-3 sentences explaining what this email is and why it might be risky.

## WHY THIS EMAIL LOOKS SUSPICIOUS
List 3-5 bullet points of specific suspicious behaviors found:
- Focus on user-understandable threats (hidden redirects, urgency tactics, impersonation)
- Avoid technical jargon
- Be specific about what was detected

## AI REASONING  
Explain the writing style, persuasion tactics, and manipulation patterns you detect.

## TECHNICAL INDICATORS
Convert technical findings to plain English:
- High entropy URLs → "Links appear intentionally obfuscated"
- Domain mismatch → "Displayed link differs from actual destination"  
- High complexity → "Template resembles mass phishing campaigns"

## FINAL ASSESSMENT
State: SAFE / SUSPICIOUS / PHISHING with brief justification.

## RECOMMENDED ACTION
Give clear, actionable advice:
- "Do not click any links"
- "Verify directly on the official website"
- "Delete this email immediately"

Format your response with clear section headers and make it sound like a professional cybersecurity expert talking to a regular person."""

        return prompt
    
    def _parse_phishing_explanation(self, explanation_text: str) -> Dict[str, Any]:
        """Parse structured explanation from Gemini response."""
        
        # Default structure
        parsed = {
            "summary": "",
            "suspicious_indicators": [],
            "ai_reasoning": "",
            "technical_indicators": [],
            "final_assessment": "",
            "recommended_action": "",
            "full_explanation": explanation_text
        }
        
        try:
            # Simple parsing - look for section headers
            sections = explanation_text.split('##')
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                    
                if section.upper().startswith('SUMMARY'):
                    parsed["summary"] = section.split('\n', 1)[1].strip() if '\n' in section else ""
                elif 'SUSPICIOUS' in section.upper():
                    # Extract bullet points
                    lines = section.split('\n')[1:]
                    parsed["suspicious_indicators"] = [
                        line.strip('- ').strip() for line in lines 
                        if line.strip() and line.strip().startswith('-')
                    ]
                elif 'REASONING' in section.upper():
                    parsed["ai_reasoning"] = section.split('\n', 1)[1].strip() if '\n' in section else ""
                elif 'TECHNICAL' in section.upper():
                    lines = section.split('\n')[1:]
                    parsed["technical_indicators"] = [
                        line.strip('- ').strip() for line in lines 
                        if line.strip() and line.strip().startswith('-')
                    ]
                elif 'ASSESSMENT' in section.upper():
                    parsed["final_assessment"] = section.split('\n', 1)[1].strip() if '\n' in section else ""
                elif 'ACTION' in section.upper() or 'RECOMMENDED' in section.upper():
                    parsed["recommended_action"] = section.split('\n', 1)[1].strip() if '\n' in section else ""
        
        except Exception as e:
            logger.warning(f"Failed to parse explanation structure: {e}")
            # Fallback - use full text as summary
            parsed["summary"] = explanation_text[:200] + "..." if len(explanation_text) > 200 else explanation_text
        
        return parsed
    
    def _generate_fallback_phishing_explanation(
        self, 
        result: Dict[str, Any], 
        email_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate enhanced human-readable explanation when Gemini is unavailable."""
        
        label = result.get('label', 'UNKNOWN')
        score = result.get('score', 0)
        reasons = result.get('reasons', [])
        evidence = result.get('evidence', [])
        
        # Extract email details for context
        subject = email_content.get('subject', 'No subject')
        from_email = email_content.get('from_email', 'Unknown sender')
        visible_links = email_content.get('visible_links', [])
        raw_text = email_content.get('raw_text', '')
        
        # Generate human-readable threat summary
        if label == "PHISHING" or score >= 70:
            summary = f"This email is a phishing attempt designed to steal your personal information. It uses deceptive tactics to appear legitimate while trying to trick you into revealing sensitive data."
            assessment = "🚨 PHISHING - Delete immediately"
            action = "Do not click any links or provide any information. Delete this email and report it as spam. If you're concerned about the claims made, contact the organization directly through their official website."
        elif label == "SUSPICIOUS" or score >= 40:
            summary = f"This email contains several warning signs that suggest it may be a phishing attempt or scam. While not definitively malicious, it exhibits patterns commonly used by cybercriminals."
            assessment = "⚠️ SUSPICIOUS - Exercise extreme caution"
            action = "Do not click any links or download attachments. Verify the sender's identity through a separate communication channel before taking any action. When in doubt, ignore the email."
        else:
            summary = f"This email appears to be legitimate with no significant red flags detected. However, always remain vigilant when dealing with unsolicited emails."
            assessment = "✅ SAFE - Appears legitimate"
            action = "While this email seems safe, continue to exercise standard email security practices. Verify any unexpected requests independently."
        
        # Generate human-readable suspicious indicators
        user_friendly_indicators = []
        
        # Analyze evidence for specific threats
        for ev in evidence:
            ev_type = ev.get('type', '')
            if ev_type == 'credential_request':
                user_friendly_indicators.append("🔑 Asks for passwords or login credentials - a classic phishing tactic")
            elif ev_type == 'urgency':
                count = ev.get('count', 1)
                user_friendly_indicators.append(f"⏰ Uses {count} urgency phrases to pressure you into quick action")
            elif ev_type == 'link_mismatch':
                anchor = ev.get('anchor', 'link text')
                user_friendly_indicators.append(f"🔗 Deceptive link: '{anchor}' leads to a different website than expected")
            elif ev_type == 'high_entropy_uri':
                user_friendly_indicators.append("🌐 Contains obfuscated URLs designed to hide the real destination")
            elif ev_type == 'hidden_ip':
                user_friendly_indicators.append("🖥️ Links directly to IP addresses instead of legitimate domain names")
        
        # Add context-based indicators
        if 'paypal' in subject.lower() and 'paypal' not in from_email.lower():
            user_friendly_indicators.append("🏢 Claims to be from PayPal but sender email doesn't match")
        
        if any(word in raw_text.lower() for word in ['suspended', 'locked', 'verify', 'confirm']):
            user_friendly_indicators.append("🚨 Uses account suspension threats to create fear and urgency")
        
        if len(visible_links) > 0:
            for link in visible_links:
                uri = link.get('uri', '')
                if '.tk' in uri or '.ml' in uri or '.ga' in uri:
                    user_friendly_indicators.append("🌍 Uses suspicious free domain extensions often favored by scammers")
                    break
        
        # Generate AI reasoning based on analysis
        reasoning_parts = []
        if score >= 70:
            reasoning_parts.append("This email exhibits multiple hallmarks of a sophisticated phishing campaign.")
            reasoning_parts.append("The combination of urgency tactics, credential requests, and deceptive links strongly indicates malicious intent.")
        elif score >= 40:
            reasoning_parts.append("Several concerning patterns suggest this could be a phishing attempt.")
            reasoning_parts.append("The sender is using psychological manipulation techniques commonly employed by cybercriminals.")
        else:
            reasoning_parts.append("The email structure and content appear consistent with legitimate business communications.")
            reasoning_parts.append("No significant deception indicators were detected in the message.")
        
        ai_reasoning = " ".join(reasoning_parts)
        
        # Generate simplified technical indicators
        tech_indicators = []
        if score >= 80:
            tech_indicators.append("🔴 High threat confidence - multiple attack vectors detected")
        elif score >= 60:
            tech_indicators.append("🟡 Medium threat confidence - several suspicious patterns found")
        elif score >= 30:
            tech_indicators.append("🟠 Low-medium threat confidence - some concerning elements present")
        else:
            tech_indicators.append("🟢 Low threat confidence - minimal risk indicators")
        
        # Add specific technical findings in plain English
        if any('entropy' in str(ev) for ev in evidence):
            tech_indicators.append("🔀 URL obfuscation detected - links are intentionally disguised")
        
        if any('mismatch' in str(ev) for ev in evidence):
            tech_indicators.append("🎭 Link deception detected - displayed text doesn't match actual destination")
        
        return {
            "summary": summary,
            "suspicious_indicators": user_friendly_indicators,
            "ai_reasoning": ai_reasoning,
            "technical_indicators": tech_indicators,
            "final_assessment": assessment,
            "recommended_action": action,
            "full_explanation": f"{summary} {action}"
        }

    async def generate_batch_summary(self, results: list) -> str:
        """
        Generate summary of multiple voice analyses.
        
        Args:
            results: List of analysis results
        
        Returns:
            Summary string
        """
        total = len(results)
        deepfakes = sum(1 for r in results if r['is_deepfake'])
        high_risk = sum(1 for r in results if r['risk_level'] == 'high')
        
        summary = f"Analyzed {total} voice samples:\n"
        summary += f"- {deepfakes} detected as AI-generated ({deepfakes/total:.0%})\n"
        summary += f"- {high_risk} flagged as high-risk ({high_risk/total:.0%})\n"
        summary += f"- {total - deepfakes} appear genuine\n"
        
        if high_risk > 0:
            summary += "\n ⚠️ WARNING: High-risk deepfakes detected. Review flagged samples immediately."
        
        return summary