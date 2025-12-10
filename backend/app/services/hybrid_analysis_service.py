# app/services/hybrid_analysis_service.py
import json
import uuid
from typing import Dict, List, Any
from app.schemas.phishing import AnalyzeRequest, AnalyzeResponse
from app.services.phishing_service import PhishingAnalysisService
from app.services.gemini_service import GeminiPhishingService
from app.models.email_scan import EmailScan
from app.db.session import SessionLocal

class HybridPhishingService:
    """
    Hybrid phishing detection combining:
    1. Heuristic analysis (fast, free)
    2. Gemini AI analysis (accurate, cost-effective)
    
    Implements the 75% cost reduction strategy from technical document.
    """
    
    def __init__(self):
        self.heuristic_service = PhishingAnalysisService()
        self.gemini_service = GeminiPhishingService()
        
        # Thresholds for hybrid decision making
        self.safe_threshold = 25      # Below this = definitely safe
        self.danger_threshold = 75    # Above this = definitely phishing
        
    async def analyze_email(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """
        Hybrid analysis pipeline:
        1. Run fast heuristic analysis
        2. If unclear, use Gemini AI for final decision
        3. Return comprehensive results with cost tracking
        """
        
        request_id = str(uuid.uuid4())
        
        # Stage 1: Heuristic Analysis (Always run - it's free)
        heuristic_result = self.heuristic_service.analyze_email(request)
        heuristic_score = heuristic_result.score
        
        # Decision logic for AI usage
        use_ai = self._should_use_ai(heuristic_score)
        
        if use_ai:
            # Stage 2: AI Analysis for ambiguous cases
            try:
                ai_result = await self._analyze_with_ai(request)
                final_result = self._combine_results(heuristic_result, ai_result)
                cost_estimate = 0.02  # Gemini API cost
            except Exception as e:
                # Fallback to heuristic if AI fails
                final_result = heuristic_result
                final_result.reasons.append(f"AI analysis failed: {str(e)}")
                cost_estimate = 0.0
        else:
            # Use heuristic result directly
            final_result = heuristic_result
            cost_estimate = 0.0
        
        # Add analysis metadata
        final_result.model_meta = {
            "version": "2.0",
            "model": "hybrid",
            "heuristic_score": heuristic_score,
            "ai_used": use_ai,
            "cost_estimate": cost_estimate,
            "analysis_stages": self._get_analysis_stages(heuristic_score, use_ai)
        }
        
        # Save enhanced result to database
        self._save_enhanced_scan_result(request, final_result)
        
        return final_result
    
    def _should_use_ai(self, heuristic_score: int) -> bool:
        """
        Decide whether to use expensive AI analysis.
        
        Strategy:
        - Score < 25: Definitely safe, no AI needed
        - Score > 75: Definitely phishing, no AI needed  
        - Score 25-75: Ambiguous, use AI for better accuracy
        """
        return self.safe_threshold <= heuristic_score <= self.danger_threshold
    
    async def _analyze_with_ai(self, request: AnalyzeRequest) -> Dict[str, Any]:
        """Convert request to format expected by Gemini service."""
        
        email_data = {
            "subject": request.subject,
            "from_email": request.from_email,
            "raw_text": request.raw_text,
            "visible_links": [
                {"uri": link.uri, "anchor_text": link.anchor_text} 
                for link in (request.visible_links or [])
            ]
        }
        
        return await self.gemini_service.analyze_email(email_data)
    
    def _combine_results(self, heuristic_result: AnalyzeResponse, ai_result: Dict[str, Any]) -> AnalyzeResponse:
        """
        Intelligently combine heuristic and AI results.
        AI gets priority for final decision, but we keep heuristic insights.
        """
        
        # Map AI labels to our format
        label_mapping = {
            "SAFE": "low",
            "SUSPICIOUS": "medium", 
            "PHISHING": "high"
        }
        
        ai_label = ai_result.get("label", "SUSPICIOUS")
        final_label = label_mapping.get(ai_label, "medium")
        
        # Use AI confidence as score
        final_score = ai_result.get("confidence", 50)
        
        # Combine explanations
        combined_reasons = []
        
        # Add AI explanation first (most important)
        if ai_result.get("explanation"):
            combined_reasons.append(f"🤖 AI Analysis: {ai_result['explanation']}")
        
        # Add AI-specific risk indicators
        if ai_result.get("risk_indicators"):
            for indicator in ai_result["risk_indicators"]:
                combined_reasons.append(f"⚠️ {indicator}")
        
        # Add heuristic insights
        combined_reasons.append(f"📊 Heuristic Score: {heuristic_result.score}/100")
        
        # Keep some original heuristic reasons for context
        if heuristic_result.reasons:
            combined_reasons.extend(heuristic_result.reasons[:2])  # Top 2 reasons
        
        return AnalyzeResponse(
            request_id=heuristic_result.request_id,
            label=final_label,
            score=final_score,
            reasons=combined_reasons,
            evidence=heuristic_result.evidence,
            suggested_action=ai_result.get("recommended_action", heuristic_result.suggested_action),
            model_meta={}  # Will be set by caller
        )
    
    def _get_analysis_stages(self, heuristic_score: int, ai_used: bool) -> List[Dict[str, Any]]:
        """Return analysis pipeline stages for transparency."""
        
        stages = [
            {
                "stage": "heuristic",
                "score": heuristic_score,
                "cost": 0.0,
                "status": "completed"
            }
        ]
        
        if ai_used:
            stages.append({
                "stage": "gemini_ai",
                "cost": 0.02,
                "status": "completed"
            })
        else:
            stages.append({
                "stage": "gemini_ai", 
                "cost": 0.0,
                "status": "skipped",
                "reason": "heuristic_sufficient"
            })
        
        return stages
    
    def _save_enhanced_scan_result(self, request: AnalyzeRequest, result: AnalyzeResponse):
        """Save scan result with enhanced metadata."""
        
        try:
            db = SessionLocal()
            
            scan = EmailScan(
                subject=request.subject,
                sender=request.from_email,
                label=result.label,
                score=result.score,
                reasons=json.dumps(result.reasons),
                # Store additional metadata
                analysis_metadata=json.dumps(result.model_meta) if result.model_meta else None
            )
            
            db.add(scan)
            db.commit()
            db.close()
            
        except Exception as e:
            print(f"Error saving enhanced scan result: {e}")

# Global service instance
hybrid_service = HybridPhishingService()