
"""
Comprehensive Generalization Test for v2.1
Tests one sample from EVERY available generative architecture in WaveFake.
"""
import sys
import os
import glob
import random
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import torch
import librosa
import numpy as np
from src.models import FusionDeepfakeDetector
from src.features import WavLMExtractor, WhisperExtractor, DSPExtractor

def main():
    print("=== Deepfake Model v2.1: Cross-Architecture Verification ===")
    
    # Setup
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # Model was moved to backend during deployment
    model_path = 'backend/app/ml/models/deepfake_v2_1.pth'
    
    if not os.path.exists(model_path):
        print(f"Model not found: {model_path}")
        return

    # Load Model
    print(f"Loading Model: {model_path}")
    model = FusionDeepfakeDetector(dsp_dim=246)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    
    # Load Extractors
    print("Loading Extractors...")
    wavlm = WavLMExtractor(device=device)
    whisper = WhisperExtractor(device=device)
    dsp = DSPExtractor()
    
    # Discovery: Find all architectures
    wavefake_root = "ml_pipeline_deepfake/data/wavefake/generated_audio"
    if not os.path.exists(wavefake_root):
        print("WaveFake data not found.")
        return
        
    arch_dirs = [d for d in os.listdir(wavefake_root) if os.path.isdir(os.path.join(wavefake_root, d))]
    
    print(f"\nFound {len(arch_dirs)} Architectures to Test:")
    
    results = []
    
    print("-" * 100)
    print(f"{'Architecture':<40} | {'Prediction':<10} | {'Confidence':<10} | {'Status'}")
    print("-" * 100)
    
    # Colors
    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET = "\033[0m"

    for arch in arch_dirs:
        # Pick a random file from this architecture
        dir_path = os.path.join(wavefake_root, arch)
        files = glob.glob(os.path.join(dir_path, "*.wav"))
        
        if not files:
            continue
            
        test_file = random.choice(files)
        
        try:
            # Process
            wav, sr = librosa.load(test_file, sr=16000)
            
            w_emb = torch.tensor(wavlm.extract(wav, sr)).unsqueeze(0).to(device)
            s_emb = torch.tensor(whisper.extract(wav, sr)).unsqueeze(0).to(device)
            d_feat = torch.tensor(dsp.extract(wav, sr)).unsqueeze(0).to(device)
            
            with torch.no_grad():
                out = model.predict_with_explanation(w_emb, s_emb, d_feat)
            
            conf = float(out['confidence'])
            pred_label = "FAKE" if conf > 0.5 else "REAL"
            
            # Since these are all from WaveFake, Expected is always FAKE
            is_correct = (pred_label == "FAKE")
            status = f"{GREEN}PASS{RESET}" if is_correct else f"{RED}FAIL{RESET}"
            
            print(f"{arch[:40]:<40} | {pred_label:<10} | {conf:.4f}     | {status}")
            results.append(is_correct)
            
        except Exception as e:
            print(f"{arch:<40} | ERROR      | 0.0000     | {e}")
            results.append(False)

    # Also Test Real (Control)
    real_path = "ml_pipeline_deepfake/data/real/wild_real_1.wav"
    if os.path.exists(real_path):
        wav, sr = librosa.load(real_path, sr=16000)
        w_emb = torch.tensor(wavlm.extract(wav, sr)).unsqueeze(0).to(device)
        s_emb = torch.tensor(whisper.extract(wav, sr)).unsqueeze(0).to(device)
        d_feat = torch.tensor(dsp.extract(wav, sr)).unsqueeze(0).to(device)
        with torch.no_grad():
                out = model.predict_with_explanation(w_emb, s_emb, d_feat)
        conf = float(out['confidence'])
        pred_label = "FAKE" if conf > 0.5 else "REAL"
        is_correct = (pred_label == "REAL")
        status = f"{GREEN}PASS{RESET}" if is_correct else f"{RED}FAIL{RESET}"
        print("-" * 100)
        print(f"{'Control: Real Audio':<40} | {pred_label:<10} | {conf:.4f}     | {status}")
        results.append(is_correct)

    print("-" * 100)
    score = sum(results) / len(results) * 100
    print(f"\nOverall Generalization Score: {score:.1f}% ({sum(results)}/{len(results)})")

if __name__ == "__main__":
    main()
