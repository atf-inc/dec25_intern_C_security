
import os
import logging
from typing import Dict, Any
try:
    import google.generativeai as genai
    from google.generativeai import types
    GENAI_AVAILABLE = True
except ImportError:
    print("⚠️ Google Generative AI not available, using mock responses")
    GENAI_AVAILABLE = False
    genai = None
    types = None

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
        
        if not GENAI_AVAILABLE:
            logger.warning("Google Generative AI not available. Using mock explanations.")
            self.client = None
        elif not self.api_key:
            logger.warning("No Gemini API key provided. Explanations will be rule-based.")
            self.client = None
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.client = None
    
    
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

        if self.client is None:
            return self._generate_fallback_explanation(analysis_result)
        
        try:
            # Prepare prompt
            prompt = self._create_explanation_prompt(analysis_result, include_technical)
            
            # Call Gemini API

            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,  # Low temperature for consistent explanations
                    max_output_tokens=300,
                    response_mime_type="text/plain"

                )
            )
            
            explanation = response.text.strip()
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
            summary += "\n⚠️ WARNING: High-risk deepfakes detected. Review flagged samples immediately."
        
        return summary
