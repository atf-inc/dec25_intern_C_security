#!/usr/bin/env python3
"""
Professional Report Generator for Phishing Detection Evaluation

Generates clean, professional markdown reports from evaluation results.
Creates properly formatted tables, charts, and analysis.

Usage:
    python professional_report_generator.py --results evaluation_results.json
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class ProfessionalReportGenerator:
    """Generates professional evaluation reports in markdown format."""
    
    def __init__(self):
        self.results_dir = Path(__file__).parent.parent / "results"
        
    def load_results(self, filepath: str) -> Dict[str, Any]:
        """Load evaluation results."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_professional_report(self, results: Dict[str, Any]) -> str:
        """Generate a clean, professional markdown report."""
        
        lines = []
        
        # Title and Header
        lines.append("# ATF CyberX - Phishing Detection Evaluation Report")
        lines.append("")
        lines.append("## Executive Summary")
        lines.append("")
        
        # Key metrics from hybrid system
        if 'hybrid' in results:
            hybrid = results['hybrid']
            f1_score = hybrid.get('f1_score', 0)
            cost_reduction = hybrid.get('cost_reduction_vs_full_llm', 0)
            ai_usage = hybrid.get('ai_usage_rate', 0)
            
            lines.append(f"🎯 **Performance Achievement**: {f1_score:.1%} F1 Score")
            lines.append(f"💰 **Cost Optimization**: {cost_reduction:.1%} reduction vs full LLM")
            lines.append(f"🤖 **Smart AI Usage**: {ai_usage:.1%} of emails analyzed with LLM")
            lines.append("")
            
            if f1_score > 0.75:
                lines.append("✅ **Status**: Ready for Production Deployment")
            else:
                lines.append("⚠️ **Status**: Requires Additional Optimization")
            lines.append("")
        
        # Dataset Information
        if 'metadata' in results:
            meta = results['metadata']
            lines.append("## Dataset Overview")
            lines.append("")
            lines.append(f"- **Total Samples**: {meta.get('dataset_size', 'N/A')}")
            lines.append(f"- **Phishing Emails**: {meta.get('phishing_samples', 'N/A')}")
            lines.append(f"- **Legitimate Emails**: {meta.get('benign_samples', 'N/A')}")
            lines.append(f"- **Evaluation Date**: {meta.get('evaluation_date', datetime.now().strftime('%Y-%m-%d'))}")
            lines.append("")
        
        # Performance Comparison
        lines.append("## Performance Comparison")
        lines.append("")
        
        # Create clean table
        lines.append("| Approach | Precision | Recall | F1 Score | Cost | Latency |")
        lines.append("|----------|-----------|--------|----------|------|---------|")
        
        model_order = ['heuristics', 'hybrid', 'gemini_only']
        for model_key in model_order:
            if model_key in results:
                metrics = results[model_key]
                name = metrics.get('model_name', model_key)
                precision = metrics.get('precision', 0)
                recall = metrics.get('recall', 0)
                f1 = metrics.get('f1_score', 0)
                cost = metrics.get('total_cost', 0)
                latency = metrics.get('avg_latency', 0)
                
                lines.append(f"| {name} | {precision:.1%} | {recall:.1%} | {f1:.1%} | ${cost:.3f} | {latency:.3f}s |")
        
        lines.append("")
        
        # Detailed Analysis
        lines.append("## Detailed Analysis")
        lines.append("")
        
        # Hybrid System Analysis
        if 'hybrid' in results:
            hybrid = results['hybrid']
            lines.append("### 🚀 Hybrid AI System")
            lines.append("")
            
            precision = hybrid.get('precision', 0)
            recall = hybrid.get('recall', 0)
            f1 = hybrid.get('f1_score', 0)
            
            lines.append("**Key Strengths:**")
            if precision > 0.9:
                lines.append(f"- 🎯 **Excellent Precision** ({precision:.1%}): Very few false alarms")
            elif precision > 0.8:
                lines.append(f"- ✅ **High Precision** ({precision:.1%}): Low false positive rate")
            
            if recall > 0.9:
                lines.append(f"- 🛡️ **Excellent Coverage** ({recall:.1%}): Catches almost all threats")
            elif recall > 0.8:
                lines.append(f"- ✅ **Good Coverage** ({recall:.1%}): Catches most threats")
            
            if f1 > 0.9:
                lines.append(f"- 🏆 **Outstanding Balance** ({f1:.1%}): Excellent overall performance")
            elif f1 > 0.8:
                lines.append(f"- ⭐ **Strong Balance** ({f1:.1%}): Good overall performance")
            
            lines.append("")
            
            # Cost Analysis
            cost = hybrid.get('total_cost', 0)
            ai_usage = hybrid.get('ai_usage_rate', 0)
            cost_reduction = hybrid.get('cost_reduction_vs_full_llm', 0)
            
            lines.append("**Cost Efficiency:**")
            lines.append(f"- 💰 **Total Cost**: ${cost:.4f} for {results.get('metadata', {}).get('dataset_size', 'N/A')} emails")
            lines.append(f"- 🤖 **AI Usage**: {ai_usage:.1%} of emails required LLM analysis")
            lines.append(f"- 📉 **Savings**: {cost_reduction:.1%} cost reduction vs full LLM approach")
            lines.append("")
        
        # Baseline Comparison
        if 'heuristics' in results:
            heuristics = results['heuristics']
            lines.append("### 📊 Heuristics Baseline")
            lines.append("")
            
            h_precision = heuristics.get('precision', 0)
            h_recall = heuristics.get('recall', 0)
            h_f1 = heuristics.get('f1_score', 0)
            
            lines.append(f"- **Precision**: {h_precision:.1%}")
            lines.append(f"- **Recall**: {h_recall:.1%}")
            lines.append(f"- **F1 Score**: {h_f1:.1%}")
            lines.append(f"- **Cost**: $0.0000 (free)")
            lines.append("")
            
            if h_recall < 0.5:
                lines.append("⚠️ **Limitation**: Low recall - misses many phishing attempts")
            if h_precision > 0.8:
                lines.append("✅ **Strength**: High precision - few false alarms")
            lines.append("")
        
        # Technical Implementation
        lines.append("## Technical Architecture")
        lines.append("")
        lines.append("### 🏗️ Hybrid Decision Pipeline")
        lines.append("")
        lines.append("```")
        lines.append("Email Input")
        lines.append("    ↓")
        lines.append("1. Heuristic Analysis (Free)")
        lines.append("   • Urgency keywords")
        lines.append("   • Link analysis")
        lines.append("   • Domain reputation")
        lines.append("    ↓")
        lines.append("2. Risk Assessment")
        lines.append("   • Score ≥ 30: Proceed to LLM")
        lines.append("   • Score < 30: Use heuristic result")
        lines.append("    ↓")
        lines.append("3. LLM Analysis (When Needed)")
        lines.append("   • Gemini AI evaluation")
        lines.append("   • Contextual understanding")
        lines.append("   • Final classification")
        lines.append("```")
        lines.append("")
        
        # Confusion Matrices
        lines.append("## Classification Results")
        lines.append("")
        
        for model_key in ['heuristics', 'hybrid']:
            if model_key in results:
                metrics = results[model_key]
                name = metrics.get('model_name', model_key)
                tp = metrics.get('true_positives', 0)
                tn = metrics.get('true_negatives', 0)
                fp = metrics.get('false_positives', 0)
                fn = metrics.get('false_negatives', 0)
                
                lines.append(f"### {name}")
                lines.append("")
                lines.append("```")
                lines.append("                Predicted")
                lines.append("              Safe  Phishing")
                lines.append(f"Actual Safe    {tn:3d}     {fp:3d}")
                lines.append(f"     Phishing  {fn:3d}     {tp:3d}")
                lines.append("```")
                lines.append("")
        
        # Business Impact
        lines.append("## Business Impact")
        lines.append("")
        
        if 'hybrid' in results:
            hybrid = results['hybrid']
            dataset_size = results.get('metadata', {}).get('dataset_size', 1000)
            
            # Calculate business metrics
            cost_per_1000 = (hybrid.get('total_cost', 0) / dataset_size) * 1000
            emails_per_day = 10000  # Assume 10k emails per day
            daily_cost = cost_per_1000 * (emails_per_day / 1000)
            monthly_cost = daily_cost * 30
            
            lines.append("### 💼 Operational Metrics")
            lines.append("")
            lines.append(f"- **Cost per 1,000 emails**: ${cost_per_1000:.2f}")
            lines.append(f"- **Estimated daily cost** (10k emails): ${daily_cost:.2f}")
            lines.append(f"- **Estimated monthly cost**: ${monthly_cost:.2f}")
            lines.append("")
            
            # Security metrics
            precision = hybrid.get('precision', 0)
            recall = hybrid.get('recall', 0)
            
            false_positive_rate = 1 - precision if precision > 0 else 0
            false_negative_rate = 1 - recall if recall > 0 else 0
            
            lines.append("### 🔒 Security Metrics")
            lines.append("")
            lines.append(f"- **False Positive Rate**: {false_positive_rate:.1%} (legitimate emails blocked)")
            lines.append(f"- **False Negative Rate**: {false_negative_rate:.1%} (phishing emails missed)")
            lines.append(f"- **Detection Accuracy**: {recall:.1%} of phishing attempts caught")
            lines.append("")
        
        # Recommendations
        lines.append("## Recommendations")
        lines.append("")
        
        if 'hybrid' in results:
            f1 = results['hybrid'].get('f1_score', 0)
            
            if f1 > 0.9:
                lines.append("### ✅ Production Deployment")
                lines.append("")
                lines.append("The system demonstrates excellent performance and is ready for production:")
                lines.append("")
                lines.append("1. **Deploy to staging environment** for final validation")
                lines.append("2. **Implement monitoring dashboards** for real-time metrics")
                lines.append("3. **Set up alerting** for performance degradation")
                lines.append("4. **Plan gradual rollout** to production traffic")
                
            elif f1 > 0.75:
                lines.append("### ⭐ Production Ready with Monitoring")
                lines.append("")
                lines.append("The system meets production thresholds with recommended monitoring:")
                lines.append("")
                lines.append("1. **Deploy with enhanced monitoring** to track edge cases")
                lines.append("2. **Implement feedback loops** for continuous improvement")
                lines.append("3. **Regular model retraining** with new threat data")
                
            else:
                lines.append("### ⚠️ Optimization Required")
                lines.append("")
                lines.append("Additional improvements needed before production deployment:")
                lines.append("")
                lines.append("1. **Expand training dataset** with more diverse samples")
                lines.append("2. **Fine-tune detection thresholds** for better balance")
                lines.append("3. **Enhance heuristic rules** for better initial filtering")
        
        lines.append("")
        
        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*Report generated by ATF CyberX Evaluation Framework*")
        lines.append(f"*Generated on: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*")
        
        return "\n".join(lines)
    
    def save_report(self, report: str, filename: str):
        """Save report to file."""
        filepath = self.results_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 Professional report saved to {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Generate professional evaluation report")
    parser.add_argument("--results", default="results/evaluation_results.json",
                       help="Path to evaluation results JSON")
    parser.add_argument("--output", default="professional_evaluation_report.md",
                       help="Output report filename")
    
    args = parser.parse_args()
    
    generator = ProfessionalReportGenerator()
    
    # Load results
    if args.results.startswith('evaluation/'):
        results_path = Path(args.results)
    else:
        results_path = Path(__file__).parent.parent / args.results
        
    if not results_path.exists():
        print(f"❌ Results file not found: {results_path}")
        print("Run 'python evaluate_models.py' first to generate results")
        return
    
    results = generator.load_results(results_path)
    
    # Generate professional report
    report = generator.generate_professional_report(results)
    
    # Save report
    generator.save_report(report, args.output)
    
    print("✅ Professional report generation complete!")

if __name__ == "__main__":
    main()