#!/usr/bin/env python3
"""
Report Generator for Phishing Detection Evaluation

Generates comprehensive markdown reports from evaluation results.
Creates tables, charts, and analysis suitable for technical documentation.

Usage:
    python generate_report.py --results evaluation_results.json
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class ReportGenerator:
    """Generates evaluation reports in markdown format."""
    
    def __init__(self):
        self.results_dir = Path(__file__).parent.parent / "results"
        
    def load_results(self, filepath: str) -> Dict[str, Any]:
        """Load evaluation results."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive markdown report."""
        
        report = []
        
        # Header
        report.append("# ATF CyberX - Phishing Detection Evaluation Report")
        report.append("")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if 'metadata' in results:
            meta = results['metadata']
            report.append(f"**Dataset Size:** {meta.get('dataset_size', 'N/A')} samples")
            report.append(f"**Phishing Samples:** {meta.get('phishing_samples', 'N/A')}")
            report.append(f"**Benign Samples:** {meta.get('benign_samples', 'N/A')}")
        
        report.append("")
        report.append("---")
        report.append("")
        
        # Executive Summary
        report.append("## Executive Summary")
        report.append("")
        
        if 'hybrid' in results:
            hybrid = results['hybrid']
            report.append(f"Our hybrid AI system achieved **{hybrid['f1_score']:.1%} F1 score** with **{hybrid.get('cost_reduction_vs_full_llm', 0):.1%} cost reduction** compared to full LLM usage.")
            report.append("")
            
            if hybrid.get('ai_usage_rate'):
                report.append(f"The system used expensive AI analysis for only **{hybrid['ai_usage_rate']:.1%}** of emails, demonstrating effective cost optimization.")
                report.append("")
        
        # Performance Comparison Table
        report.append("## Performance Comparison")
        report.append("")
        report.append("| Model | Precision | Recall | F1 Score | ROC-AUC | Cost ($) | Latency (s) |")
        report.append("|-------|-----------|--------|----------|---------|----------|-------------|")
        
        model_order = ['heuristics', 'hybrid', 'gemini_only']
        for model_key in model_order:
            if model_key in results:
                metrics = results[model_key]
                name = metrics.get('model_name', model_key)
                precision = metrics.get('precision', 0)
                recall = metrics.get('recall', 0)
                f1 = metrics.get('f1_score', 0)
                roc_auc = metrics.get('roc_auc', 0)
                cost = metrics.get('total_cost', 0)
                latency = metrics.get('avg_latency', 0)
                
                report.append(f"| {name} | {precision:.3f} | {recall:.3f} | {f1:.3f} | {roc_auc:.3f} | ${cost:.4f} | {latency:.3f} |")
        
        report.append("")
        
        # Detailed Analysis
        report.append("## Detailed Analysis")
        report.append("")
        
        for model_key in model_order:
            if model_key in results:
                metrics = results[model_key]
                report.extend(self._generate_model_analysis(metrics))
        
        # Cost Analysis
        if 'hybrid' in results and 'gemini_only' in results:
            report.append("## Cost Analysis")
            report.append("")
            
            hybrid_cost = results['hybrid'].get('total_cost', 0)
            gemini_cost = results['gemini_only'].get('total_cost', 0)
            
            if gemini_cost > 0:
                savings = (gemini_cost - hybrid_cost) / gemini_cost
                report.append(f"**Cost Reduction:** {savings:.1%}")
                report.append(f"- Full LLM Cost: ${gemini_cost:.4f}")
                report.append(f"- Hybrid Cost: ${hybrid_cost:.4f}")
                report.append(f"- Savings: ${gemini_cost - hybrid_cost:.4f}")
                report.append("")
        
        # Technical Implementation
        report.append("## Technical Implementation")
        report.append("")
        report.append("### Hybrid Strategy")
        report.append("")
        report.append("Our hybrid system implements a 3-stage pipeline:")
        report.append("")
        report.append("1. **Heuristics (Free)** - Fast rule-based analysis")
        report.append("2. **Embeddings (Low Cost)** - Similarity-based detection")  
        report.append("3. **Gemini LLM (High Cost)** - Advanced AI analysis for ambiguous cases")
        report.append("")
        
        if 'hybrid' in results:
            ai_usage = results['hybrid'].get('ai_usage_rate', 0)
            report.append(f"The system automatically decides when to use expensive AI analysis, resulting in AI usage for only {ai_usage:.1%} of emails.")
            report.append("")
        
        # Confusion Matrices
        report.append("## Confusion Matrices")
        report.append("")
        
        for model_key in model_order:
            if model_key in results:
                metrics = results[model_key]
                report.extend(self._generate_confusion_matrix(metrics))
        
        # Recommendations
        report.append("## Recommendations")
        report.append("")
        report.append("### Production Deployment")
        report.append("")
        
        if 'hybrid' in results:
            hybrid = results['hybrid']
            f1 = hybrid.get('f1_score', 0)
            
            if f1 > 0.75:
                report.append("✅ **Ready for Production** - F1 score exceeds 75% threshold")
            else:
                report.append("⚠️ **Needs Improvement** - Consider additional training data or model tuning")
            
            report.append("")
        
        report.append("### Next Steps")
        report.append("")
        report.append("1. **Expand Dataset** - Collect more diverse phishing samples")
        report.append("2. **Fine-tune Thresholds** - Optimize decision boundaries for cost/accuracy trade-off")
        report.append("3. **A/B Testing** - Deploy alongside existing systems for comparison")
        report.append("4. **Monitoring** - Implement real-time performance tracking")
        report.append("")
        
        # Appendix
        report.append("## Appendix")
        report.append("")
        report.append("### Methodology")
        report.append("")
        report.append("- **Evaluation Dataset:** Balanced mix of phishing and benign emails")
        report.append("- **Metrics:** Standard classification metrics (Precision, Recall, F1, ROC-AUC)")
        report.append("- **Cost Calculation:** Based on Gemini API pricing estimates")
        report.append("- **Latency:** End-to-end processing time per email")
        report.append("")
        
        return "\\n".join(report)
    
    def _generate_model_analysis(self, metrics: Dict[str, Any]) -> list:
        """Generate detailed analysis for a single model."""
        analysis = []
        
        name = metrics.get('model_name', 'Unknown Model')
        analysis.append(f"### {name}")
        analysis.append("")
        
        # Performance summary
        precision = metrics.get('precision', 0)
        recall = metrics.get('recall', 0)
        f1 = metrics.get('f1_score', 0)
        
        analysis.append(f"**Performance Summary:**")
        analysis.append(f"- Precision: {precision:.1%} (of flagged emails, {precision:.1%} are actually phishing)")
        analysis.append(f"- Recall: {recall:.1%} (catches {recall:.1%} of all phishing emails)")
        analysis.append(f"- F1 Score: {f1:.1%} (balanced performance metric)")
        analysis.append("")
        
        # Strengths and weaknesses
        if precision > 0.8:
            analysis.append("**Strengths:** High precision - low false positive rate")
        elif precision < 0.6:
            analysis.append("**Weaknesses:** Low precision - many false positives")
        
        if recall > 0.8:
            analysis.append("**Strengths:** High recall - catches most phishing attempts")
        elif recall < 0.6:
            analysis.append("**Weaknesses:** Low recall - misses many phishing emails")
        
        analysis.append("")
        
        return analysis
    
    def _generate_confusion_matrix(self, metrics: Dict[str, Any]) -> list:
        """Generate confusion matrix display."""
        matrix = []
        
        name = metrics.get('model_name', 'Unknown')
        tp = metrics.get('true_positives', 0)
        tn = metrics.get('true_negatives', 0)
        fp = metrics.get('false_positives', 0)
        fn = metrics.get('false_negatives', 0)
        
        matrix.append(f"### {name} - Confusion Matrix")
        matrix.append("")
        matrix.append("```")
        matrix.append("                 Predicted")
        matrix.append("                Safe  Phishing")
        matrix.append(f"Actual Safe     {tn:4d}    {fp:4d}")
        matrix.append(f"       Phishing {fn:4d}    {tp:4d}")
        matrix.append("```")
        matrix.append("")
        
        return matrix
    
    def save_report(self, report: str, filename: str):
        """Save report to file."""
        filepath = self.results_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 Report saved to {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Generate evaluation report")
    parser.add_argument("--results", default="results/evaluation_results.json",
                       help="Path to evaluation results JSON")
    parser.add_argument("--output", default="evaluation_report.md",
                       help="Output report filename")
    
    args = parser.parse_args()
    
    generator = ReportGenerator()
    
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
    
    # Generate report
    report = generator.generate_markdown_report(results)
    
    # Save report
    generator.save_report(report, args.output)
    
    print("✅ Report generation complete!")

if __name__ == "__main__":
    main()