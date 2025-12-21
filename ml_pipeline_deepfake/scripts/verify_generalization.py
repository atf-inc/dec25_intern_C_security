
"""
Verify Generalization of Deepfake Model v2.1 (MelGAN Fix)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import torch
import librosa
import numpy as np
from src.models import FusionDeepfakeDetector
from src.features import WavLMExtractor, WhisperExtractor, DSPExtractor

def main():
    print("=== Deepfake Model v2.1 Generalization Test ===")
    
    # 1. Setup
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")
    
    # 2. Load Model
    model_path = 'ml_pipeline_deepfake/models/fusion_detector_v2_1.pth'
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return
        
    print(f"Loading v2.1 Model from {model_path}...")
    model = FusionDeepfakeDetector(dsp_dim=246)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    
    # 3. Load Extractors
    print("Loading Feature Extractors...")
    wavlm = WavLMExtractor(device=device)
    whisper = WhisperExtractor(device=device)
    dsp = DSPExtractor()
    
    # 4. Test Cases
    # We test the file that FAILED in v2.0
    test_cases = [
        # The MelGAN failure case
        ("ml_pipeline_deepfake/data/wavefake/generated_audio/ljspeech_melgan_large/LJ001-0001_gen.wav", "Fake (MelGAN)"),
        # A Real file (Control)
        ("ml_pipeline_deepfake/data/real/wild_real_1.wav", "Real (Noisy)"), 
        # Another architecture to check generalization
        ("ml_pipeline_deepfake/data/wavefake/generated_audio/ljspeech_hifiGAN/LJ001-0001_gen.wav", "Fake (HiFiGAN)")
    ]
    
    results = []
    
    print("\nStarting Inference...")
    print("-" * 60)
    print(f"{'File':<40} | {'Expected':<15} | {'Pred':<5} | {'Conf':<8} | {'Status'}")
    print("-" * 60)
    
    for fpath, label_str in test_cases:
        if not os.path.exists(fpath):
            print(f"File not found: {fpath}")
            continue
            
        # Process
        try:
            audio, sr = librosa.load(fpath, sr=16000)
            
            w_emb = torch.tensor(wavlm.extract(audio, sr)).unsqueeze(0).to(device)
            s_emb = torch.tensor(whisper.extract(audio, sr)).unsqueeze(0).to(device)
            d_feat = torch.tensor(dsp.extract(audio, sr)).unsqueeze(0).to(device)
            
            with torch.no_grad():
                out = model.predict_with_explanation(w_emb, s_emb, d_feat)
                
            conf = float(out['confidence'])
            pred = "FAKE" if conf > 0.5 else "REAL"
            expected = "FAKE" if "Fake" in label_str else "REAL"
            
            # Colors for terminal (ANSI)
            GREEN = "\033[92m"
            RED = "\033[91m"
            RESET = "\033[0m"
            
            status = f"{GREEN}PASS{RESET}" if pred == expected else f"{RED}FAIL{RESET}"
            
            short_name = os.path.basename(fpath)
            if "melgan" in fpath.lower(): short_name = "MelGAN_" + short_name
            if "hifigan" in fpath.lower(): short_name = "HiFiGAN_" + short_name
            
            print(f"{short_name:<40} | {label_str:<15} | {pred:<5} | {conf:.4f}   | {status}")
            
            results.append((short_name, pred == expected))
            
        except Exception as e:
            print(f"Error processing {fpath}: {e}")

    print("-" * 60)
    
    # Final Verdict
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nFinal Result: {passed}/{total} Tests Passed.")
    if passed == total:
        print("SUCCESS: Model v2.1 generalization verified.")
    else:
        print("WARNING: Generalization issues persist.")

if __name__ == "__main__":
    main()
