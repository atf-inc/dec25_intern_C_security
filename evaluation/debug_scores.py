#!/usr/bin/env python3
"""
Debug script to check heuristic scores for our samples.
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from app.ml.phishing_model import _heuristic_signals, analyze_email

def debug_scores():
    """Check heuristic scores for our balanced dataset."""
    
    # Load balanced dataset
    dataset_path = Path(__file__).parent / "evaluation/datasets/balanced_evaluation_dataset.json"
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    samples = data['samples']
    
    print("🔍 Debugging Heuristic Scores")
    print("=" * 60)
    
    for i, sample in enumerate(samples):
        payload = {
            "subject": sample.get('subject', ''),
            "from_email": sample.get('from_email', ''),
            "raw_text": sample.get('raw_text', ''),
            "visible_links": sample.get('visible_links', []),
            "hidden_links": sample.get('hidden_links', [])
        }
        
        # Get heuristic score
        heur_result = _heuristic_signals(payload)
        
        # Get full analysis
        full_result = analyze_email(payload)
        
        print(f"\n📧 Sample {i+1}: {sample['label'].upper()}")
        print(f"   Subject: {sample['subject'][:50]}...")
        print(f"   Heuristic Score: {heur_result['score']}")
        print(f"   Final Score: {full_result['score']}")
        print(f"   Final Label: {full_result['label']}")
        print(f"   LLM Used: {full_result.get('model_meta', {}).get('llm_used', False)}")
        print(f"   Analysis Method: {full_result.get('model_meta', {}).get('analysis_method', 'unknown')}")
        
        if heur_result['reasons']:
            print(f"   Reasons: {', '.join(heur_result['reasons'][:2])}")

if __name__ == "__main__":
    debug_scores()