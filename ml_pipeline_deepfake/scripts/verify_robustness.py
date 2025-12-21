"""
Verify Robustness of Deepfake Model v2.0
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import torch
import numpy as np
import librosa
from src.models import FusionDeepfakeDetector
from src.features import WavLMExtractor, WhisperExtractor, DSPExtractor

def main():
    print("Loading Extractors...")
    wavlm_ext = WavLMExtractor()
    whisper_ext = WhisperExtractor()
    dsp_ext = DSPExtractor()
    
    print("Loading Model v2.0...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = FusionDeepfakeDetector(dsp_dim=246) # Ensure dsp_dim matches new extractor
    
    model_path = 'ml_pipeline_deepfake/models/fusion_detector_v2.pth'
    if not os.path.exists(model_path):
        # Fallback to standard name if not versioned yet, or check arguments
        model_path = 'ml_pipeline_deepfake/models/fusion_detector.pth'
        
    print(f"Loading weights from {model_path}...")
    try:
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.to(device)
        model.eval()
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    # Test Files
    test_files = [
        "ml_pipeline_deepfake/data/real/wild_real_1.wav", # Real
        "ml_pipeline_deepfake/data/fake/wild_fake_1.wav", # Fake
        "ml_pipeline_deepfake/data/wavefake/generated_audio/ljspeech_melgan_large/LJ001-0001_gen.wav" # Fake (MelGAN)
    ]
    
    print("\nRunning Inference...")
    for fpath in test_files:
        if not os.path.exists(fpath):
            print(f"File not found: {fpath}")
            continue
            
        print(f"\nProcessing: {fpath}")
        wav, sr = librosa.load(fpath, sr=16000)
        
        # Extract
        w_emb = torch.tensor(wavlm_ext.extract(wav, sr)).unsqueeze(0).to(device)
        s_emb = torch.tensor(whisper_ext.extract(wav, sr)).unsqueeze(0).to(device)
        d_feat = torch.tensor(dsp_ext.extract(wav, sr)).unsqueeze(0).to(device)
        
        # Predict
        with torch.no_grad():
            outputs = model.predict_with_explanation(w_emb, s_emb, d_feat)
            
        conf = float(outputs['confidence'])
        label = "FAKE" if conf > 0.5 else "REAL"
        print(f"  -> Prediction: {label} (Confidence: {conf:.4f})")
        print(f"  -> Expert Scores: Acoustic={outputs['expert_scores']['acoustic']:.3f}, Semantic={outputs['expert_scores']['semantic']:.3f}, Signal={outputs['expert_scores']['signal']:.3f}")

if __name__ == "__main__":
    main()
