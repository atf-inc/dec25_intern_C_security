"""
Test the improved model and generate detailed accuracy report
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, 
    confusion_matrix, classification_report, roc_auc_score
)

from models.fusion_model import DeepfakeFusionModel
from features.wavlm_extractor import WavLMFeatureExtractor
from features.whisper_extractor import WhisperFeatureExtractor
from features.dsp_features import DSPFeatureExtractor

def test_model():
    """Test the improved model on all available data"""
    
    print("\n" + "="*60)
    print("TESTING IMPROVED MODEL")
    print("="*60)
    
    # Load cached features
    cache_path = "data/features_cache.npz"
    
    if not os.path.exists(cache_path):
        print("❌ No cached features found. Run training first.")
        return
    
    print(f"\n✓ Loading features from {cache_path}")
    data = np.load(cache_path)
    wavlm_features = data['wavlm']
    whisper_features = data['whisper']
    dsp_features = data['dsp']
    labels = data['labels']
    
    print(f"  Total samples: {len(labels)}")
    print(f"  Real samples: {np.sum(labels == 0)}")
    print(f"  Fake samples: {np.sum(labels == 1)}")
    
    # Load improved model
    model_path = "checkpoints/fusion_model_improved.pth"
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found at {model_path}")
        return
    
    print(f"\n✓ Loading model from {model_path}")
    model = DeepfakeFusionModel(hidden_dim=256, dropout=0.3)
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()
    
    # Convert to tensors
    wavlm_tensor = torch.FloatTensor(wavlm_features)
    whisper_tensor = torch.FloatTensor(whisper_features)
    dsp_tensor = torch.FloatTensor(dsp_features)
    
    # Run inference
    print("\n✓ Running inference on all samples...")
    with torch.no_grad():
        logits = model(wavlm_tensor, whisper_tensor, dsp_tensor)
        probs = torch.sigmoid(logits).numpy().flatten()
        preds = (probs > 0.5).astype(int)
    
    # Calculate metrics
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    # Overall accuracy
    accuracy = accuracy_score(labels, preds)
    print(f"\n🎯 OVERALL ACCURACY: {accuracy:.2%}")
    
    # Precision, Recall, F1
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average='binary', zero_division=0
    )
    
    print(f"\n📊 Detailed Metrics:")
    print(f"  Precision (Fake): {precision:.2%}")
    print(f"  Recall (Fake):    {recall:.2%}")
    print(f"  F1-Score:         {f1:.2%}")
    
    # AUC
    try:
        auc = roc_auc_score(labels, probs)
        print(f"  AUC-ROC:          {auc:.2%}")
    except:
        auc = 0.0
        print(f"  AUC-ROC:          N/A")
    
    # Confusion Matrix
    cm = confusion_matrix(labels, preds)
    print(f"\n📈 Confusion Matrix:")
    print(f"                Predicted")
    print(f"              Real    Fake")
    print(f"Actual Real    {cm[0,0]:3d}     {cm[0,1]:3d}")
    print(f"       Fake    {cm[1,0]:3d}     {cm[1,1]:3d}")
    
    # Per-class metrics
    print(f"\n📋 Per-Class Performance:")
    
    # Real detection
    real_correct = cm[0,0]
    real_total = cm[0,0] + cm[0,1]
    real_accuracy = real_correct / real_total if real_total > 0 else 0
    print(f"  Real Detection: {real_correct}/{real_total} ({real_accuracy:.2%})")
    
    # Fake detection
    fake_correct = cm[1,1]
    fake_total = cm[1,0] + cm[1,1]
    fake_accuracy = fake_correct / fake_total if fake_total > 0 else 0
    print(f"  Fake Detection: {fake_correct}/{fake_total} ({fake_accuracy:.2%})")
    
    # Classification Report
    print(f"\n📄 Full Classification Report:")
    print(classification_report(
        labels, preds, 
        target_names=['Real', 'Fake'],
        zero_division=0
    ))
    
    # Confidence analysis
    print(f"\n🔍 Confidence Analysis:")
    high_conf = np.sum((probs > 0.7) | (probs < 0.3))
    medium_conf = np.sum((probs >= 0.3) & (probs <= 0.7))
    print(f"  High confidence:   {high_conf}/{len(probs)} ({high_conf/len(probs):.2%})")
    print(f"  Medium confidence: {medium_conf}/{len(probs)} ({medium_conf/len(probs):.2%})")
    
    # Misclassified samples
    misclassified = np.where(preds != labels)[0]
    print(f"\n⚠️  Misclassified: {len(misclassified)}/{len(labels)} samples")
    
    if len(misclassified) > 0:
        print(f"\n  Breakdown:")
        false_positives = np.sum((preds == 1) & (labels == 0))
        false_negatives = np.sum((preds == 0) & (labels == 1))
        print(f"    False Positives (Real → Fake): {false_positives}")
        print(f"    False Negatives (Fake → Real): {false_negatives}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✅ Model tested on {len(labels)} samples")
    print(f"✅ Overall Accuracy: {accuracy:.2%}")
    print(f"✅ Precision: {precision:.2%} (When says FAKE, correct {precision:.2%} of time)")
    print(f"✅ Recall: {recall:.2%} (Catches {recall:.2%} of all fakes)")
    print(f"✅ F1-Score: {f1:.2%}")
    print(f"✅ AUC: {auc:.2%}")
    
    # Comparison with old model
    print(f"\n📊 Improvement from Old Model:")
    print(f"  Old Accuracy: 65%")
    print(f"  New Accuracy: {accuracy:.2%}")
    print(f"  Improvement:  +{(accuracy - 0.65)*100:.1f}%")
    
    print("\n" + "="*60)
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'auc': auc,
        'confusion_matrix': cm
    }

if __name__ == "__main__":
    results = test_model()
