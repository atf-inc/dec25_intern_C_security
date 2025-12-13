#!/usr/bin/env python3
"""
Model Evaluation Script for Hybrid Phishing Detection System

Tests the performance of:
1. Heuristics-only baseline
2. Embedding classifier (placeholder)
3. Gemini LLM-only
4. Hybrid system (heuristics + LLM)

Generates precision, recall, F1, ROC-AUC metrics and cost analysis.

Usage:
    python evaluate_models.py --dataset combined_dataset.json
"""

import json
import asyncio
import time
from typing import List, Dict, Any, Tuple
from pathlib import Path
import argparse
import numpy as np
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score, confusion_matrix
import sys
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv(Path(__file__).parent.parent.parent / "backend" / ".env")

# Add backend to path for importing services
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

try:
    # Import the actual hybrid model we've been using
    from app.ml.phishing_model import analyze_email, _heuristic_signals
except ImportError as e:
    print(f"❌ Error importing phishing model: {e}")
    print("Make sure you're running from the project root and backend dependencies are installed")
    sys.exit(1)

class ModelEvaluator:
    """Evaluates different phishing detection models."""
    
    def __init__(self):
        self.results_dir = Path(__file__).parent.parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        
    def load_dataset(self, filepath: str) -> List[Dict[str, Any]]:
        """Load evaluation dataset."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        samples = data.get('samples', [])
        print(f"📊 Loaded {len(samples)} samples from {filepath}")
        return samples
    
    def convert_to_payload(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Convert sample to payload format for our model."""
        return {
            "subject": sample.get('subject', ''),
            "from_email": sample.get('from_email', ''),
            "raw_text": sample.get('raw_text', ''),
            "visible_links": sample.get('visible_links', []),
            "hidden_links": sample.get('hidden_links', [])
        }
    
    def evaluate_heuristics_only(self, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate heuristics-only baseline."""
        print("🔍 Evaluating heuristics-only model...")
        
        predictions = []
        true_labels = []
        scores = []
        costs = []
        latencies = []
        
        for sample in samples:
            start_time = time.time()
            
            payload = self.convert_to_payload(sample)
            result = _heuristic_signals(payload)
            
            latency = time.time() - start_time
            latencies.append(latency)
            
            # Convert to binary prediction (threshold at 50)
            prediction = 1 if result['score'] >= 50 else 0
            true_label = 1 if sample['label'] == 'phishing' else 0
            
            predictions.append(prediction)
            true_labels.append(true_label)
            scores.append(result['score'] / 100.0)  # Normalize to 0-1
            costs.append(0.0)  # Heuristics are free
        
        metrics = self._calculate_metrics(true_labels, predictions, scores)
        metrics.update({
            'total_cost': sum(costs),
            'avg_latency': np.mean(latencies),
            'model_name': 'Heuristics Only'
        })
        
        return metrics
    
    async def evaluate_gemini_only(self, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate Gemini LLM-only model."""
        print("🤖 Evaluating Gemini LLM-only model...")
        
        predictions = []
        true_labels = []
        scores = []
        costs = []
        latencies = []
        
        for i, sample in enumerate(samples):
            print(f"Processing sample {i+1}/{len(samples)}...", end='\\r')
            
            start_time = time.time()
            
            try:
                email_data = {
                    "subject": sample.get('subject', ''),
                    "from_email": sample.get('from_email', ''),
                    "raw_text": sample.get('raw_text', ''),
                    "visible_links": sample.get('visible_links', [])
                }
                
                result = await self.gemini_service.analyze_email(email_data)
                
                latency = time.time() - start_time
                latencies.append(latency)
                
                # Convert AI label to binary prediction
                ai_label = result.get('label', 'SUSPICIOUS')
                prediction = 1 if ai_label in ['SUSPICIOUS', 'PHISHING'] else 0
                confidence = result.get('confidence', 50) / 100.0
                
                true_label = 1 if sample['label'] == 'phishing' else 0
                
                predictions.append(prediction)
                true_labels.append(true_label)
                scores.append(confidence)
                costs.append(0.02)  # Estimated Gemini API cost
                
            except Exception as e:
                print(f"\\n⚠️ Error processing sample {i+1}: {e}")
                # Use fallback values
                predictions.append(0)
                true_labels.append(1 if sample['label'] == 'phishing' else 0)
                scores.append(0.5)
                costs.append(0.0)
                latencies.append(1.0)
        
        print("\\n")
        
        metrics = self._calculate_metrics(true_labels, predictions, scores)
        metrics.update({
            'total_cost': sum(costs),
            'avg_latency': np.mean(latencies),
            'model_name': 'Gemini LLM Only'
        })
        
        return metrics
    
    def evaluate_hybrid_system(self, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate hybrid system (heuristics + LLM)."""
        print("⚡ Evaluating hybrid system...")
        
        predictions = []
        true_labels = []
        scores = []
        costs = []
        latencies = []
        ai_usage_count = 0
        
        for i, sample in enumerate(samples):
            print(f"Processing sample {i+1}/{len(samples)}...", end='\r')
            
            start_time = time.time()
            
            try:
                payload = self.convert_to_payload(sample)
                result = analyze_email(payload)
                
                latency = time.time() - start_time
                latencies.append(latency)
                
                # Convert label to binary prediction
                prediction = 1 if result['label'] in ['SUSPICIOUS', 'PHISHING'] else 0
                true_label = 1 if sample['label'] == 'phishing' else 0
                
                predictions.append(prediction)
                true_labels.append(true_label)
                scores.append(result['score'] / 100.0)
                
                # Extract cost from metadata
                cost = result.get('model_meta', {}).get('cost_estimate', 0.0)
                costs.append(cost)
                
                # Track AI usage
                if result.get('model_meta', {}).get('llm_used', False):
                    ai_usage_count += 1
                
            except Exception as e:
                print(f"\n⚠️ Error processing sample {i+1}: {e}")
                # Use fallback values
                predictions.append(0)
                true_labels.append(1 if sample['label'] == 'phishing' else 0)
                scores.append(0.5)
                costs.append(0.0)
                latencies.append(1.0)
        
        print("\n")
        
        metrics = self._calculate_metrics(true_labels, predictions, scores)
        metrics.update({
            'total_cost': sum(costs),
            'avg_latency': np.mean(latencies),
            'ai_usage_rate': ai_usage_count / len(samples),
            'cost_reduction_vs_full_llm': 1 - (sum(costs) / (len(samples) * 0.02)),
            'model_name': 'Hybrid System'
        })
        
        return metrics
    
    def _calculate_metrics(self, true_labels: List[int], predictions: List[int], scores: List[float]) -> Dict[str, float]:
        """Calculate standard classification metrics."""
        
        # Basic metrics
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_labels, predictions, average='binary', zero_division=0
        )
        
        # ROC-AUC (handle edge case where all labels are the same)
        try:
            roc_auc = roc_auc_score(true_labels, scores)
        except ValueError:
            roc_auc = 0.5  # Random performance if all labels are same
        
        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(true_labels, predictions).ravel()
        
        return {
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'roc_auc': float(roc_auc),
            'true_positives': int(tp),
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'accuracy': float((tp + tn) / (tp + tn + fp + fn))
        }
    
    def save_results(self, all_results: Dict[str, Any], filename: str):
        """Save evaluation results to JSON."""
        filepath = self.results_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to {filepath}")

async def main():
    parser = argparse.ArgumentParser(description="Evaluate phishing detection models")
    parser.add_argument("--dataset", default="datasets/combined_dataset.json", 
                       help="Path to evaluation dataset")
    parser.add_argument("--quick", action="store_true", 
                       help="Quick evaluation (skip LLM-only test)")
    
    args = parser.parse_args()
    
    evaluator = ModelEvaluator()
    
    # Load dataset
    if args.dataset.startswith('evaluation/'):
        dataset_path = Path(args.dataset)
    else:
        dataset_path = Path(__file__).parent.parent / args.dataset
    if not dataset_path.exists():
        print(f"❌ Dataset not found: {dataset_path}")
        print("Run 'python collect_data.py' first to create the dataset")
        return
    
    samples = evaluator.load_dataset(dataset_path)
    
    if len(samples) == 0:
        print("❌ No samples found in dataset")
        return
    
    # Run evaluations
    results = {}
    
    # 1. Heuristics baseline
    results['heuristics'] = evaluator.evaluate_heuristics_only(samples)
    
    # 2. Hybrid system (our main approach)
    results['hybrid'] = evaluator.evaluate_hybrid_system(samples)
    
    # 3. Gemini-only (if not quick mode)
    if not args.quick:
        results['gemini_only'] = await evaluator.evaluate_gemini_only(samples)
    
    # Add metadata
    results['metadata'] = {
        'dataset_size': len(samples),
        'phishing_samples': sum(1 for s in samples if s['label'] == 'phishing'),
        'benign_samples': sum(1 for s in samples if s['label'] == 'benign'),
        'evaluation_date': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Save results
    evaluator.save_results(results, 'evaluation_results.json')
    
    # Print summary
    print("\\n" + "="*60)
    print("📊 EVALUATION SUMMARY")
    print("="*60)
    
    for model_name, metrics in results.items():
        if model_name == 'metadata':
            continue
            
        print(f"\\n🔹 {metrics['model_name']}")
        print(f"   Precision: {metrics['precision']:.3f}")
        print(f"   Recall:    {metrics['recall']:.3f}")
        print(f"   F1 Score:  {metrics['f1_score']:.3f}")
        print(f"   ROC-AUC:   {metrics['roc_auc']:.3f}")
        print(f"   Cost:      ${metrics['total_cost']:.4f}")
        print(f"   Latency:   {metrics['avg_latency']:.3f}s")
        
        if 'cost_reduction_vs_full_llm' in metrics:
            print(f"   Cost Reduction: {metrics['cost_reduction_vs_full_llm']:.1%}")
        if 'ai_usage_rate' in metrics:
            print(f"   AI Usage Rate: {metrics['ai_usage_rate']:.1%}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())