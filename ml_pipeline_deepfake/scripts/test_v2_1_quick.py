"""
Quick Test for v2.1 Model

Tests the current v2.1 model on all available samples in data/ directory.
Provides a quick sanity check and baseline metrics.

Usage:
    python scripts/test_v2_1_quick.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import torch
import librosa
import numpy as np
from pathlib import Path
from tqdm import tqdm
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

from src.models import FusionDeepfakeDetector
from src.features import WavLMExtractor, WhisperExtractor, DSPExtractor


def main():
    print("\n" + "="*70)
    print("DEEPFAKE MODEL v2.1 - QUICK TEST")
    print("="*70)
    
    # Setup
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")
    
    # Model paths to try
    model_paths = [
        '../backend/app/ml/models/deepfake_v2_1.pth',
        'backend/app/ml/models/deepfake_v2_1.pth',
        'models/deepfake_v2_1.pth',
    ]
    
    model_path = None
    for p in model_paths:
        if os.path.exists(p):
            model_path = p
            break
    
    if model_path is None:
        print("ERROR: No model file found!")
        print("Tried:", model_paths)
        return
    
    print(f"Model: {model_path}")
    
    # Load model
    print("\nLoading model...")
    model = FusionDeepfakeDetector(dsp_dim=246)
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.to(device)
    model.eval()
    print("[OK] Model loaded")
    
    # Load extractors
    print("\nLoading extractors...")
    wavlm = WavLMExtractor(device=device)
    whisper = WhisperExtractor(device=device)
    dsp = DSPExtractor()
    print("[OK] Extractors ready")
    
    # Collect test files
    data_dir = 'data'
    real_dir = os.path.join(data_dir, 'real')
    fake_dir = os.path.join(data_dir, 'fake')
    
    files = []
    labels = []
    
    if os.path.exists(real_dir):
        for f in Path(real_dir).glob('*.wav'):
            files.append(str(f))
            labels.append(0)
    
    if os.path.exists(fake_dir):
        for f in Path(fake_dir).glob('*.wav'):
            files.append(str(f))
            labels.append(1)
    
    print(f"\nFound {len(files)} test files ({sum(1 for l in labels if l == 0)} real, {sum(1 for l in labels if l == 1)} fake)")
    
    if len(files) == 0:
        print("ERROR: No test files found!")
        return
    
    # Test
    print("\n" + "-"*70)
    predictions = []
    confidences = []
    
    for file_path, label in tqdm(zip(files, labels), total=len(files), desc="Testing"):
        try:
            # Load audio
            wav, sr = librosa.load(file_path, sr=16000)
            
            # Extract features
            w_emb = torch.tensor(wavlm.extract(wav, sr)).unsqueeze(0).to(device)
            s_emb = torch.tensor(whisper.extract(wav, sr)).unsqueeze(0).to(device)
            d_feat = torch.tensor(dsp.extract(wav, sr)).unsqueeze(0).to(device)
            
            # Predict
            with torch.no_grad():
                result = model.predict_with_explanation(w_emb, s_emb, d_feat)
            
            conf = float(result['confidence'])
            pred = 1 if conf > 0.5 else 0
            
            predictions.append(pred)
            confidences.append(conf)
            
        except Exception as e:
            print(f"\nError processing {file_path}: {e}")
            predictions.append(0)
            confidences.append(0.5)
    
    # Calculate metrics
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    accuracy = accuracy_score(labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average='binary', zero_division=0)
    cm = confusion_matrix(labels, predictions)
    
    print(f"\n[METRICS] Overall Metrics:")
    print(f"   Accuracy:  {accuracy:.2%}")
    print(f"   Precision: {precision:.2%}")
    print(f"   Recall:    {recall:.2%}")
    print(f"   F1 Score:  {f1:.2%}")
    
    print(f"\n[CONFUSION MATRIX]")
    print(f"                 Predicted")
    print(f"                 Real    Fake")
    print(f"   Actual Real   {cm[0,0]:4d}    {cm[0,1]:4d}")
    print(f"   Actual Fake   {cm[1,0]:4d}    {cm[1,1]:4d}")
    
    # Per-class analysis
    real_acc = cm[0,0] / (cm[0,0] + cm[0,1]) if (cm[0,0] + cm[0,1]) > 0 else 0
    fake_acc = cm[1,1] / (cm[1,0] + cm[1,1]) if (cm[1,0] + cm[1,1]) > 0 else 0
    
    print(f"\n[PER-CLASS] Accuracy:")
    print(f"   Real Detection Rate: {real_acc:.2%} ({cm[0,0]}/{cm[0,0]+cm[0,1]})")
    print(f"   Fake Detection Rate: {fake_acc:.2%} ({cm[1,1]}/{cm[1,0]+cm[1,1]})")
    
    # Confidence analysis
    real_confs = [confidences[i] for i in range(len(labels)) if labels[i] == 0]
    fake_confs = [confidences[i] for i in range(len(labels)) if labels[i] == 1]
    
    print(f"\n[CONFIDENCE] Distribution:")
    print(f"   Real samples: mean={np.mean(real_confs):.3f}, std={np.std(real_confs):.3f}")
    print(f"   Fake samples: mean={np.mean(fake_confs):.3f}, std={np.std(fake_confs):.3f}")
    
    print("\n" + "="*70)
    
    # Save results
    with open('test_v2_1_results.txt', 'w') as f:
        f.write(f"Deepfake Model v2.1 Test Results\n")
        f.write(f"================================\n\n")
        f.write(f"Test samples: {len(files)} ({sum(1 for l in labels if l == 0)} real, {sum(1 for l in labels if l == 1)} fake)\n\n")
        f.write(f"Accuracy:  {accuracy:.4f}\n")
        f.write(f"Precision: {precision:.4f}\n")
        f.write(f"Recall:    {recall:.4f}\n")
        f.write(f"F1 Score:  {f1:.4f}\n\n")
        f.write(f"Real Detection Rate: {real_acc:.4f}\n")
        f.write(f"Fake Detection Rate: {fake_acc:.4f}\n\n")
        f.write(f"Confusion Matrix:\n{cm}\n")
    
    print(f"[OK] Results saved to test_v2_1_results.txt")


if __name__ == '__main__':
    main()

